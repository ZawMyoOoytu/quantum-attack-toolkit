
"""
Experiment Report Generator.

Builds a research-grade report from quantum noise-sweep results.

Pipeline:

    Quantum experiment
          |
          v
    Measurement counts
          |
          v
    Statistical noise sweep
          |
          v
    Security assessment
          |
          v
    JSON / HTML research report

This module is intended for authorized quantum-security research,
benchmarking, simulation, and defensive analysis.
"""

from __future__ import annotations

import html
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ExperimentReport:
    """Complete experiment-level report."""

    title: str
    target_name: str
    target_type: str
    target_size: int | None
    algorithm: str
    noise_model: str

    shots: int
    trials: int

    records: list[dict[str, Any]]

    baseline_entropy_bits: float | None
    maximum_entropy_bits: float | None

    minimum_success_rate: float | None
    maximum_success_rate: float | None

    minimum_dominant_probability: float | None
    maximum_dominant_probability: float | None

    minimum_normalized_entropy: float | None
    maximum_normalized_entropy: float | None

    conclusion: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Numeric helpers
# ---------------------------------------------------------------------------

def _float_or_none(value: Any) -> float | None:
    """Safely convert a value to float."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _records(results: Iterable[Any]) -> list[dict[str, Any]]:
    """
    Normalize sweep results.

    Supports:
      - dataclass results with summary()
      - mappings
      - objects exposing __dict__
    """

    normalized: list[dict[str, Any]] = []

    for item in results:
        if hasattr(item, "summary") and callable(item.summary):
            data = item.summary()
        elif isinstance(item, Mapping):
            data = dict(item)
        elif hasattr(item, "__dict__"):
            data = dict(vars(item))
        else:
            raise TypeError(
                "Each result must be a mapping, dataclass-like object, "
                "or object exposing summary()."
            )

        normalized.append(dict(data))

    return normalized


# ---------------------------------------------------------------------------
# Report construction
# ---------------------------------------------------------------------------

def build_experiment_report(
    results: Iterable[Any],
    *,
    title: str = "Quantum Security Noise-Sweep Assessment",
    target_name: str = "RSA-Toy-15",
    target_type: str = "rsa",
    target_size: int | None = 15,
    algorithm: str = "Shor",
    noise_model: str = "depolarizing",
    shots: int | None = None,
    trials: int | None = None,
) -> ExperimentReport:
    """
    Build a complete experiment report from statistical sweep results.
    """

    records = _records(results)

    if not records:
        raise ValueError("results must contain at least one record.")

    if shots is None:
        shots = int(records[0].get("shots", 0))

    if trials is None:
        trials = int(records[0].get("trials", 0))

    entropy_values = [
        float(r["mean_entropy_bits"])
        for r in records
        if r.get("mean_entropy_bits") is not None
    ]

    normalized_entropy_values = [
        float(r["mean_normalized_entropy"])
        for r in records
        if r.get("mean_normalized_entropy") is not None
    ]

    success_values = [
        float(r["success_rate"])
        for r in records
        if r.get("success_rate") is not None
    ]

    dominant_values = [
        float(r["mean_dominant_probability"])
        for r in records
        if r.get("mean_dominant_probability") is not None
    ]

    baseline = records[0]

    baseline_entropy = _float_or_none(
        baseline.get("mean_entropy_bits")
    )

    maximum_entropy = None

    if baseline.get("mean_unique_states") is not None:
        import math

        states = max(1.0, float(baseline["mean_unique_states"]))
        maximum_entropy = math.log2(states)

    minimum_success = min(success_values) if success_values else None
    maximum_success = max(success_values) if success_values else None

    minimum_dominant = min(dominant_values) if dominant_values else None
    maximum_dominant = max(dominant_values) if dominant_values else None

    minimum_normalized = (
        min(normalized_entropy_values)
        if normalized_entropy_values
        else None
    )

    maximum_normalized = (
        max(normalized_entropy_values)
        if normalized_entropy_values
        else None
    )

    conclusion = _build_conclusion(
        records,
        minimum_success=minimum_success,
        maximum_success=maximum_success,
        minimum_dominant=minimum_dominant,
        maximum_dominant=maximum_dominant,
        minimum_normalized=minimum_normalized,
        maximum_normalized=maximum_normalized,
    )

    return ExperimentReport(
        title=title,
        target_name=target_name,
        target_type=target_type,
        target_size=target_size,
        algorithm=algorithm,
        noise_model=noise_model,
        shots=shots,
        trials=trials,
        records=records,
        baseline_entropy_bits=baseline_entropy,
        maximum_entropy_bits=maximum_entropy,
        minimum_success_rate=minimum_success,
        maximum_success_rate=maximum_success,
        minimum_dominant_probability=minimum_dominant,
        maximum_dominant_probability=maximum_dominant,
        minimum_normalized_entropy=minimum_normalized,
        maximum_normalized_entropy=maximum_normalized,
        conclusion=conclusion,
    )


def _build_conclusion(
    records: Sequence[Mapping[str, Any]],
    *,
    minimum_success: float | None,
    maximum_success: float | None,
    minimum_dominant: float | None,
    maximum_dominant: float | None,
    minimum_normalized: float | None,
    maximum_normalized: float | None,
) -> str:
    """
    Generate a conservative research conclusion.

    Important:
    Measurement degradation alone does not prove cryptographic
    failure or successful quantum attack.
    """

    if not records:
        return "No experiment records were available."

    baseline = records[0]

    baseline_entropy = _float_or_none(
        baseline.get("mean_entropy_bits")
    )

    final = records[-1]

    final_entropy = _float_or_none(
        final.get("mean_entropy_bits")
    )

    entropy_change = None

    if baseline_entropy is not None and final_entropy is not None:
        entropy_change = final_entropy - baseline_entropy

    if (
        minimum_success is not None
        and maximum_success is not None
        and minimum_success == maximum_success == 1.0
    ):
        recovery_statement = (
            "Recovery metrics remained at 100% across the tested sweep."
        )
    else:
        recovery_statement = (
            "Recovery metrics varied across the tested sweep."
        )

    if entropy_change is not None and entropy_change > 0.5:
        distribution_statement = (
            "The measurement distribution became substantially more "
            "dispersed as noise increased."
        )
    else:
        distribution_statement = (
            "The measured entropy change was limited across the tested range."
        )

    return (
        f"{distribution_statement} "
        f"{recovery_statement} "
        "These results characterize experimental measurement behavior; "
        "they should not by themselves be interpreted as proof of "
        "practical cryptographic compromise."
    )


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def save_json_report(
    report: ExperimentReport,
    path: str | Path,
) -> Path:
    """Save the experiment report as formatted JSON."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        json.dumps(
            report.to_dict(),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return output


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def _percent(value: Any) -> str:
    """Format a probability/rate as percentage."""
    number = _float_or_none(value)

    if number is None:
        return "N/A"

    return f"{number * 100:.2f}%"


def _number(value: Any, digits: int = 4) -> str:
    """Format numeric value."""
    number = _float_or_none(value)

    if number is None:
        return "N/A"

    return f"{number:.{digits}f}"


def render_html_report(report: ExperimentReport) -> str:
    """Render an experiment report as standalone HTML."""

    rows: list[str] = []

    for record in report.records:
        probability = record.get("probability")

        rows.append(
            "<tr>"
            f"<td>{html.escape(_number(probability, 2))}</td>"
            f"<td>{html.escape(_percent(record.get('success_rate')))}</td>"
            f"<td>{html.escape(_percent(record.get('order_recovery_rate')))}</td>"
            f"<td>{html.escape(_percent(record.get('factor_recovery_rate')))}</td>"
            f"<td>{html.escape(_number(record.get('mean_entropy_bits')))}</td>"
            f"<td>{html.escape(_number(record.get('mean_normalized_entropy')))}</td>"
            f"<td>{html.escape(_number(record.get('mean_dominant_probability')))}</td>"
            f"<td>{html.escape(_number(record.get('mean_unique_states'), 2))}</td>"
            "</tr>"
        )

    table_rows = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(report.title)}</title>

<style>
body {{
    font-family: Arial, sans-serif;
    margin: 40px;
    background: #f5f7fa;
    color: #202124;
}}

.container {{
    max-width: 1200px;
    margin: auto;
}}

.card {{
    background: white;
    padding: 24px;
    margin-bottom: 20px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,.08);
}}

h1 {{
    margin-top: 0;
}}

h2 {{
    margin-top: 0;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    background: white;
}}

th, td {{
    padding: 10px;
    border-bottom: 1px solid #ddd;
    text-align: right;
}}

th {{
    background: #f0f2f5;
}}

td:first-child,
th:first-child {{
    text-align: center;
}}

.metric {{
    display: inline-block;
    min-width: 180px;
    padding: 14px;
    margin: 5px;
    background: #f0f2f5;
    border-radius: 8px;
}}

.metric strong {{
    display: block;
    font-size: 20px;
}}

.note {{
    line-height: 1.6;
}}
</style>
</head>

<body>
<div class="container">

<div class="card">
<h1>{html.escape(report.title)}</h1>
<p>
<strong>Target:</strong>
{html.escape(report.target_name)}
</p>
<p>
<strong>Algorithm:</strong>
{html.escape(report.algorithm)}
&nbsp; | &nbsp;
<strong>Noise:</strong>
{html.escape(report.noise_model)}
</p>
</div>

<div class="card">
<h2>Experiment Configuration</h2>

<div class="metric">
Shots
<strong>{report.shots}</strong>
</div>

<div class="metric">
Trials
<strong>{report.trials}</strong>
</div>

<div class="metric">
Target Size
<strong>{report.target_size}</strong>
</div>

<div class="metric">
Records
<strong>{len(report.records)}</strong>
</div>
</div>

<div class="card">
<h2>Observed Range</h2>

<p>
<strong>Success rate:</strong>
{html.escape(_percent(report.minimum_success_rate))}
–
{html.escape(_percent(report.maximum_success_rate))}
</p>

<p>
<strong>Dominant probability:</strong>
{html.escape(_number(report.minimum_dominant_probability))}
–
{html.escape(_number(report.maximum_dominant_probability))}
</p>

<p>
<strong>Normalized entropy:</strong>
{html.escape(_number(report.minimum_normalized_entropy))}
–
{html.escape(_number(report.maximum_normalized_entropy))}
</p>

<p>
<strong>Baseline entropy:</strong>
{html.escape(_number(report.baseline_entropy_bits))}
</p>
</div>

<div class="card">
<h2>Statistical Noise Sweep</h2>

<table>
<thead>
<tr>
<th>Noise p</th>
<th>Success</th>
<th>Order</th>
<th>Factor</th>
<th>Entropy</th>
<th>Norm H</th>
<th>Dominant</th>
<th>States</th>
</tr>
</thead>

<tbody>
{table_rows}
</tbody>
</table>
</div>

<div class="card">
<h2>Research Conclusion</h2>
<p class="note">
{html.escape(report.conclusion)}
</p>
</div>

<div class="card">
<h2>Interpretation</h2>

<p class="note">
This report summarizes statistical measurement behavior from an
authorized quantum experiment. High entropy and a dispersed
measurement distribution indicate reduced concentration of the
observed output signal, but do not independently establish a
successful cryptographic attack.
</p>

<p class="note">
For hardware experiments, backend calibration, gate errors,
readout errors, coherence times, circuit depth, and repeated
experimental runs should be recorded for stronger conclusions.
</p>
</div>

</div>
</body>
</html>
"""


def save_html_report(
    report: ExperimentReport,
    path: str | Path,
) -> Path:
    """Save the experiment report as standalone HTML."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(
        render_html_report(report),
        encoding="utf-8",
    )

    return output


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------

def save_reports(
    results: Iterable[Any],
    *,
    json_path: str | Path,
    html_path: str | Path,
    **kwargs: Any,
) -> ExperimentReport:
    """
    Build and save both JSON and HTML reports.
    """

    report = build_experiment_report(
        results,
        **kwargs,
    )

    save_json_report(report, json_path)
    save_html_report(report, html_path)

    return report


__all__ = [
    "ExperimentReport",
    "build_experiment_report",
    "render_html_report",
    "save_json_report",
    "save_html_report",
    "save_reports",
]

