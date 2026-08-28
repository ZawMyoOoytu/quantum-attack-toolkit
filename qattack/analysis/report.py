
"""
Quantum Security Assessment Reporting.

Supports:
    - Mapping / dictionary evidence
    - dataclass evidence, including SecurityEvidence
    - objects exposing summary()

Outputs:
    - JSON
    - TXT
    - HTML

The reporting layer is intentionally independent from the attack engine.
It converts assessment evidence into stable, human-readable artifacts.
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# Internal normalization helpers
# ---------------------------------------------------------------------------

def _to_dict(evidence: Any) -> dict[str, Any]:
    """
    Normalize evidence into a dictionary.

    Supported inputs:
        1. Mapping / dictionary
        2. Dataclass, including SecurityEvidence
        3. Object exposing summary()

    Raises:
        TypeError: If the object cannot be converted to a mapping.
    """

    if isinstance(evidence, Mapping):
        return _make_json_compatible(dict(evidence))

    if is_dataclass(evidence):
        return _make_json_compatible(asdict(evidence))

    summary_method = getattr(evidence, "summary", None)

    if callable(summary_method):
        summary = summary_method()

        if isinstance(summary, Mapping):
            return _make_json_compatible(dict(summary))

        raise TypeError(
            "evidence.summary() must return a mapping."
        )

    raise TypeError(
        "evidence must be a mapping, dataclass, "
        "or object exposing summary()."
    )


def _make_json_compatible(value: Any) -> Any:
    """
    Convert common Python objects into JSON-compatible structures.

    Handles:
        - dictionaries
        - lists
        - tuples
        - sets
        - dataclasses
        - pathlib.Path
    """

    if is_dataclass(value):
        return _make_json_compatible(asdict(value))

    if isinstance(value, Mapping):
        return {
            str(key): _make_json_compatible(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _make_json_compatible(item)
            for item in value
        ]

    if isinstance(value, Path):
        return str(value)

    return value


def _flatten_evidence(data: Mapping[str, Any]) -> dict[str, Any]:
    """
    Flatten common nested SecurityEvidence structures.

    The assessment engine may produce evidence such as:

        {
            "target": {...},
            "experiment": {...},
            "measurement": {...},
            "attack": {...}
        }

    Reports are easier to consume when these values are available
    through stable top-level keys.

    Existing top-level values are preserved.
    """

    result: dict[str, Any] = dict(data)

    target = data.get("target")
    experiment = data.get("experiment")
    measurement = data.get("measurement")
    attack = data.get("attack")

    if isinstance(target, Mapping):
        result.setdefault("target_name", target.get("name"))
        result.setdefault("target_type", target.get("type"))
        result.setdefault("target_size", target.get("size"))

    if isinstance(experiment, Mapping):
        result.setdefault("shots", experiment.get("shots"))
        result.setdefault("noise_model", experiment.get("noise_model"))
        result.setdefault(
            "noise_probability",
            experiment.get("noise_probability"),
        )

    if isinstance(measurement, Mapping):
        for key in (
            "shots",
            "unique_states",
            "dominant_state",
            "dominant_probability",
            "shannon_entropy_bits",
            "maximum_entropy_bits",
            "normalized_entropy",
            "probability_mass",
            "probability_mass_error",
        ):
            if key in measurement:
                result.setdefault(key, measurement[key])

    if isinstance(attack, Mapping):
        result.setdefault(
            "recovered_order",
            attack.get("recovered_order"),
        )
        result.setdefault(
            "order_verified",
            attack.get("order_verified"),
        )
        result.setdefault(
            "factors",
            attack.get("factors"),
        )
        result.setdefault(
            "expected_order",
            attack.get("expected_order"),
        )
        result.setdefault(
            "expected_factors",
            attack.get("expected_factors"),
        )
        result.setdefault(
            "attack_method",
            attack.get("method"),
        )
        result.setdefault(
            "noise_model",
            attack.get("noise_model"),
        )
        result.setdefault(
            "noise_probability",
            attack.get("noise_probability"),
        )

    return result


def _report_data(evidence: Any) -> dict[str, Any]:
    """Normalize and flatten evidence for report generation."""

    return _flatten_evidence(_to_dict(evidence))


def _number(
    value: Any,
    default: float = 0.0,
) -> float:
    """Safely convert a value to float."""

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    """Safely convert a value to bool."""

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "verified",
        }

    return bool(value)


def _format_factors(factors: Any) -> str:
    """
    Format recovered factors for human-readable reports.
    """

    if factors is None:
        return "N/A"

    if isinstance(factors, (list, tuple, set)):
        values = list(factors)

        if not values:
            return "N/A"

        return " × ".join(str(value) for value in values)

    return str(factors)


# ---------------------------------------------------------------------------
# Text report
# ---------------------------------------------------------------------------

def render_text_report(evidence: Any) -> str:
    """
    Create a human-readable text report.
    """

    data = _report_data(evidence)

    factors = _format_factors(
        data.get("factors")
    )

    noise_probability = _number(
        data.get("noise_probability")
    )

    dominant_probability = _number(
        data.get("dominant_probability")
    )

    entropy = _number(
        data.get("shannon_entropy_bits")
    )

    maximum_entropy = _number(
        data.get("maximum_entropy_bits")
    )

    normalized_entropy = _number(
        data.get("normalized_entropy")
    )

    probability_mass = _number(
        data.get("probability_mass")
    )

    probability_mass_error = _number(
        data.get("probability_mass_error")
    )

    order_verified = _bool(
        data.get("order_verified", False)
    )

    return f"""
QUANTUM SECURITY ASSESSMENT
===========================

TARGET
------
Name:        {data.get("target_name", "N/A")}
Type:        {data.get("target_type", "N/A")}
Size:        {data.get("target_size", "N/A")}

EXPERIMENT
----------
Noise model:          {data.get("noise_model", "N/A")}
Shots:                {data.get("shots", "N/A")}
Noise probability:    {noise_probability:.4f}

QUANTUM RESULT
--------------
Recovered order:     {data.get("recovered_order", "N/A")}
Order verified:      {order_verified}
Recovered factors:   {factors}

MEASUREMENT ANALYSIS
--------------------
Dominant state:       {data.get("dominant_state", "N/A")}
Dominant probability: {dominant_probability:.6f}
Shannon entropy:      {entropy:.6f} bits
Maximum entropy:      {maximum_entropy:.6f} bits
Normalized entropy:   {normalized_entropy:.6f}

Probability mass:     {probability_mass:.6f}
Mass error:           {probability_mass_error:.6f}

METHOD
------
{data.get("attack_method", "N/A")}

EXPECTED RESULT
---------------
Expected order:       {data.get("expected_order", "N/A")}
Expected factors:     {_format_factors(data.get("expected_factors"))}

ASSESSMENT STATUS
-----------------
{"VERIFIED" if order_verified else "NOT VERIFIED"}
""".strip()


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------

def render_html_report(evidence: Any) -> str:
    """
    Create a standalone HTML report.
    """

    data = _report_data(evidence)

    def esc(value: Any) -> str:
        return html.escape(str(value))

    factors = _format_factors(
        data.get("factors")
    )

    expected_factors = _format_factors(
        data.get("expected_factors")
    )

    order_verified = _bool(
        data.get("order_verified", False)
    )

    status = (
        "VERIFIED"
        if order_verified
        else "NOT VERIFIED"
    )

    status_class = (
        "verified"
        if order_verified
        else "unverified"
    )

    normalized_entropy = _number(
        data.get("normalized_entropy")
    )

    dominant_probability = _number(
        data.get("dominant_probability")
    )

    entropy = _number(
        data.get("shannon_entropy_bits")
    )

    maximum_entropy = _number(
        data.get("maximum_entropy_bits")
    )

    probability_mass = _number(
        data.get("probability_mass")
    )

    probability_mass_error = _number(
        data.get("probability_mass_error")
    )

    noise_probability = _number(
        data.get("noise_probability")
    )

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>Quantum Security Assessment</title>

<style>

body {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    max-width: 1050px;

    margin: 40px auto;

    padding: 0 20px;

    line-height: 1.5;

    background: #fafafa;

    color: #222;
}}

h1 {{
    margin-bottom: 4px;
}}

h2 {{
    margin-top: 35px;
}}

.subtitle {{
    color: #666;

    margin-bottom: 30px;
}}

.grid {{
    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(220px, 1fr));

    gap: 16px;
}}

.card {{
    border: 1px solid #ddd;

    border-radius: 10px;

    padding: 18px;

    background: white;
}}

.label {{
    font-size: 13px;

    color: #666;
}}

.value {{
    font-size: 24px;

    font-weight: bold;

    margin-top: 5px;

    overflow-wrap: anywhere;
}}

.status {{
    font-weight: bold;
}}

.verified {{
    color: #176b2c;
}}

.unverified {{
    color: #9a1c1c;
}}

table {{
    width: 100%;

    border-collapse: collapse;

    margin-top: 15px;

    background: white;

    border: 1px solid #ddd;
}}

td {{
    border-bottom: 1px solid #eee;

    padding: 10px;
}}

td:first-child {{
    font-weight: bold;

    width: 40%;
}}

footer {{
    margin-top: 35px;

    color: #777;

    font-size: 13px;

    border-top: 1px solid #ddd;

    padding-top: 15px;
}}

</style>

</head>

<body>

<h1>Quantum Security Assessment</h1>

<div class="subtitle">
Experimental quantum-security evidence
</div>

<div class="grid">

<div class="card">

<div class="label">
Target
</div>

<div class="value">
{esc(data.get("target_name", "N/A"))}
</div>

</div>

<div class="card">

<div class="label">
Recovered Order
</div>

<div class="value">
{esc(data.get("recovered_order", "N/A"))}
</div>

</div>

<div class="card">

<div class="label">
Recovered Factors
</div>

<div class="value">
{esc(factors)}
</div>

</div>

<div class="card">

<div class="label">
Assessment Status
</div>

<div class="value status {status_class}">
{esc(status)}
</div>

</div>

</div>


<h2>Target</h2>

<table>

<tr>
<td>Name</td>
<td>{esc(data.get("target_name", "N/A"))}</td>
</tr>

<tr>
<td>Type</td>
<td>{esc(data.get("target_type", "N/A"))}</td>
</tr>

<tr>
<td>Size</td>
<td>{esc(data.get("target_size", "N/A"))}</td>
</tr>

</table>


<h2>Experiment</h2>

<table>

<tr>
<td>Shots</td>
<td>{esc(data.get("shots", "N/A"))}</td>
</tr>

<tr>
<td>Noise Model</td>
<td>{esc(data.get("noise_model", "N/A"))}</td>
</tr>

<tr>
<td>Noise Probability</td>
<td>{noise_probability:.4f}</td>
</tr>

</table>


<h2>Measurement Analysis</h2>

<table>

<tr>
<td>Dominant State</td>
<td>{esc(data.get("dominant_state", "N/A"))}</td>
</tr>

<tr>
<td>Dominant Probability</td>
<td>{dominant_probability:.6f}</td>
</tr>

<tr>
<td>Shannon Entropy</td>
<td>{entropy:.6f} bits</td>
</tr>

<tr>
<td>Maximum Entropy</td>
<td>{maximum_entropy:.6f} bits</td>
</tr>

<tr>
<td>Normalized Entropy</td>
<td>{normalized_entropy:.6f}</td>
</tr>

<tr>
<td>Probability Mass</td>
<td>{probability_mass:.6f}</td>
</tr>

<tr>
<td>Probability Mass Error</td>
<td>{probability_mass_error:.6f}</td>
</tr>

</table>


<h2>Quantum Result</h2>

<table>

<tr>
<td>Recovered Order</td>
<td>{esc(data.get("recovered_order", "N/A"))}</td>
</tr>

<tr>
<td>Order Verified</td>
<td>{esc(order_verified)}</td>
</tr>

<tr>
<td>Recovered Factors</td>
<td>{esc(factors)}</td>
</tr>

<tr>
<td>Expected Order</td>
<td>{esc(data.get("expected_order", "N/A"))}</td>
</tr>

<tr>
<td>Expected Factors</td>
<td>{esc(expected_factors)}</td>
</tr>

<tr>
<td>Method</td>
<td>{esc(data.get("attack_method", "N/A"))}</td>
</tr>

</table>


<footer>
Generated by Quantum Security Assessment Engine
</footer>

</body>

</html>
"""


# ---------------------------------------------------------------------------
# File writers
# ---------------------------------------------------------------------------

def save_json_report(
    evidence: Any,
    path: str | Path,
) -> Path:
    """
    Save normalized evidence as JSON.
    """

    data = _report_data(evidence)

    output = Path(path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output


def save_text_report(
    evidence: Any,
    path: str | Path,
) -> Path:
    """
    Save a human-readable TXT report.
    """

    output = Path(path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        render_text_report(evidence),
        encoding="utf-8",
    )

    return output


def save_html_report(
    evidence: Any,
    path: str | Path,
) -> Path:
    """
    Save a standalone HTML report.
    """

    output = Path(path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        render_html_report(evidence),
        encoding="utf-8",
    )

    return output


def save_all_reports(
    evidence: Any,
    output_dir: str | Path,
    prefix: str = "quantum_security_assessment",
) -> dict[str, Path]:
    """
    Save JSON, TXT and HTML reports.

    Parameters
    ----------
    evidence:
        SecurityEvidence, mapping, dataclass, or summary()-compatible object.

    output_dir:
        Directory where reports will be written.

    prefix:
        Base filename without extension.

    Returns
    -------
    dict[str, Path]
        Paths for JSON, TXT and HTML reports.
    """

    directory = Path(output_dir)

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return {
        "json": save_json_report(
            evidence,
            directory / f"{prefix}.json",
        ),

        "txt": save_text_report(
            evidence,
            directory / f"{prefix}.txt",
        ),

        "html": save_html_report(
            evidence,
            directory / f"{prefix}.html",
        ),
    }


__all__ = [
    "render_text_report",
    "render_html_report",
    "save_json_report",
    "save_text_report",
    "save_html_report",
    "save_all_reports",
]

