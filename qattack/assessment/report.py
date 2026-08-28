
"""
Quantum Security Assessment Reporting.

Converts AssessmentResult objects into:

    1. Human-readable text reports
    2. JSON-compatible dictionaries
    3. Simple security interpretations

This module intentionally keeps reporting separate from the attack
and measurement engines so that the assessment layer can later be
exposed through a CLI, REST API, dashboard, or agent platform.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qattack.assessment.engine import AssessmentResult


def _percentage(value: float) -> str:
    """Format a probability/rate as a percentage."""
    return f"{value * 100:.2f}%"


def _assessment_interpretation(result: AssessmentResult) -> str:
    """
    Generate a conservative interpretation of the benchmark.

    Important:
        This describes the toy benchmark result. It must not be
        interpreted as a real-world compromise of production RSA.
    """

    attack = result.attack_metrics

    order_verified = bool(attack.get("order_verified", False))
    factors = attack.get("factors")

    if order_verified and factors:
        return (
            "Toy benchmark successfully recovered the expected period "
            "and factors. This demonstrates that the implemented "
            "quantum attack pipeline is functioning for the selected "
            "small benchmark instance."
        )

    if order_verified:
        return (
            "The expected order was recovered for the selected toy "
            "benchmark, but factor recovery was not confirmed."
        )

    return (
        "The expected order was not verified in this benchmark run. "
        "Further trials or configuration changes may be required."
    )


def _limitations() -> list[str]:
    """Return standard limitations for the current benchmark."""
    return [
        (
            "The current RSA target is a small toy benchmark and does "
            "not represent a practical RSA-2048 or RSA-3072 compromise."
        ),
        (
            "The noise model is a simulation model and should not be "
            "treated as a direct measurement of a physical QPU."
        ),
        (
            "Measurement statistics depend on the selected number of "
            "shots and therefore contain sampling variation."
        ),
        (
            "Successful toy factor recovery does not imply practical "
            "cryptographic compromise of a production system."
        ),
    ]


def report_dict(result: AssessmentResult) -> dict[str, Any]:
    """
    Convert an AssessmentResult into a complete report dictionary.
    """

    measurement = result.measurement
    attack = result.attack_metrics

    order_verified = bool(attack.get("order_verified", False))
    factors = attack.get("factors")

    return {
        "report_version": "1.0",
        "target": {
            "name": result.target_name,
            "type": result.target_type,
            "size": result.target_size,
        },
        "experiment": {
            "shots": result.shots,
            "noise_model": result.noise_model,
            "noise_probability": result.noise_probability,
        },
        "measurement": {
            "shots": measurement.get("shots"),
            "unique_states": measurement.get("unique_states"),
            "dominant_state": measurement.get("dominant_state"),
            "dominant_probability": measurement.get(
                "dominant_probability"
            ),
            "shannon_entropy_bits": measurement.get(
                "shannon_entropy_bits"
            ),
            "maximum_entropy_bits": measurement.get(
                "maximum_entropy_bits"
            ),
            "normalized_entropy": measurement.get(
                "normalized_entropy"
            ),
            "probability_mass": measurement.get(
                "probability_mass"
            ),
            "probability_mass_error": measurement.get(
                "probability_mass_error"
            ),
        },
        "attack": {
            "method": attack.get("method"),
            "N": attack.get("N"),
            "a": attack.get("a"),
            "candidate_orders": attack.get("candidate_orders"),
            "recovered_order": attack.get("recovered_order"),
            "order_verified": order_verified,
            "factors": factors,
            "expected_order": attack.get("expected_order"),
            "expected_factors": attack.get("expected_factors"),
        },
        "assessment": {
            "status": (
                "BENCHMARK_SUCCESS"
                if order_verified and factors
                else "BENCHMARK_INCOMPLETE"
            ),
            "interpretation": _assessment_interpretation(result),
        },
        "limitations": _limitations(),
    }


def render_text_report(result: AssessmentResult) -> str:
    """
    Render an AssessmentResult as a human-readable text report.
    """

    measurement = result.measurement
    attack = result.attack_metrics

    status = (
        "BENCHMARK SUCCESS"
        if attack.get("order_verified") and attack.get("factors")
        else "BENCHMARK INCOMPLETE"
    )

    factors = attack.get("factors")
    if factors:
        factor_text = " × ".join(str(x) for x in factors)
    else:
        factor_text = "Not recovered"

    lines = [
        "=" * 64,
        "QUANTUM SECURITY ASSESSMENT",
        "=" * 64,
        "",
        "TARGET",
        "-" * 64,
        f"Name              : {result.target_name}",
        f"Type              : {result.target_type}",
        f"Size              : {result.target_size}",
        "",
        "QUANTUM EXPERIMENT",
        "-" * 64,
        f"Shots             : {result.shots}",
        f"Noise model       : {result.noise_model}",
        f"Noise probability : {result.noise_probability:.4f}",
        "",
        "MEASUREMENT ANALYSIS",
        "-" * 64,
        f"Unique states     : {measurement.get('unique_states', 0)}",
        (
            "Dominant state    : "
            f"{measurement.get('dominant_state', 'N/A')}"
        ),
        (
            "Dominant prob.    : "
            f"{_percentage(measurement.get('dominant_probability', 0.0))}"
        ),
        (
            "Shannon entropy   : "
            f"{measurement.get('shannon_entropy_bits', 0.0):.4f} bits"
        ),
        (
            "Maximum entropy   : "
            f"{measurement.get('maximum_entropy_bits', 0.0):.4f} bits"
        ),
        (
            "Normalized entropy: "
            f"{_percentage(measurement.get('normalized_entropy', 0.0))}"
        ),
        (
            "Probability mass  : "
            f"{measurement.get('probability_mass', 0.0):.6f}"
        ),
        "",
        "ATTACK ANALYSIS",
        "-" * 64,
        f"Method            : {attack.get('method', 'N/A')}",
        f"N                 : {attack.get('N', 'N/A')}",
        f"Base a            : {attack.get('a', 'N/A')}",
        (
            "Recovered order   : "
            f"{attack.get('recovered_order', 'N/A')}"
        ),
        (
            "Order verified    : "
            f"{attack.get('order_verified', False)}"
        ),
        f"Recovered factors : {factor_text}",
        (
            "Expected order    : "
            f"{attack.get('expected_order', 'N/A')}"
        ),
        (
            "Expected factors  : "
            f"{attack.get('expected_factors', 'N/A')}"
        ),
        "",
        "ASSESSMENT",
        "-" * 64,
        f"Status            : {status}",
        "",
        _assessment_interpretation(result),
        "",
        "LIMITATIONS",
        "-" * 64,
    ]

    for index, limitation in enumerate(_limitations(), start=1):
        lines.append(f"{index}. {limitation}")

    lines.extend(
        [
            "",
            "=" * 64,
            "End of assessment",
            "=" * 64,
        ]
    )

    return "\n".join(lines)


def save_json_report(
    result: AssessmentResult,
    path: str | Path,
) -> Path:
    """
    Save the assessment report as JSON.
    """

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report_dict(result),
            file,
            indent=2,
            ensure_ascii=False,
        )

    return output_path


def save_text_report(
    result: AssessmentResult,
    path: str | Path,
) -> Path:
    """
    Save the assessment report as plain text.
    """

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        render_text_report(result),
        encoding="utf-8",
    )

    return output_path


__all__ = [
    "report_dict",
    "render_text_report",
    "save_json_report",
    "save_text_report",
]

