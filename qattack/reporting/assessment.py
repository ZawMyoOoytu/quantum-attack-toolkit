
"""
Quantum Security Assessment Reporting.

Converts quantum measurement counts and execution metadata into a
structured security-assessment report.

This module is intentionally focused on authorized research,
benchmarking, simulation, and defensive quantum-security analysis.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from qattack.analysis.measurement import measurement_summary


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SecurityAssessment:
    """Structured result of a quantum experiment assessment."""

    target_name: str
    target_type: str
    target_size: Optional[int]

    algorithm: str
    noise_model: str
    noise_probability: Optional[float]

    shots: int

    success_rate: Optional[float]
    order_recovery_rate: Optional[float]
    factor_recovery_rate: Optional[float]

    dominant_state: Optional[str]
    dominant_probability: float

    shannon_entropy_bits: float
    maximum_entropy_bits: float
    normalized_entropy: float

    unique_states: int

    probability_mass: float
    probability_mass_error: float

    assessment_level: str
    confidence: str

    findings: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Return the assessment as a JSON-compatible dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value: Any) -> Optional[float]:
    """Convert a value to float when possible."""
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _classify_entropy(normalized_entropy: float) -> str:
    """
    Classify measurement uncertainty.

    The thresholds are heuristic indicators, not cryptographic guarantees.
    """
    if normalized_entropy < 0.35:
        return "LOW"

    if normalized_entropy < 0.70:
        return "MODERATE"

    if normalized_entropy < 0.90:
        return "HIGH"

    return "VERY_HIGH"


def _build_findings(
    *,
    dominant_probability: float,
    normalized_entropy: float,
    unique_states: int,
    probability_mass_error: float,
    success_rate: Optional[float],
    order_recovery_rate: Optional[float],
    factor_recovery_rate: Optional[float],
) -> list[str]:
    """Generate human-readable assessment findings."""

    findings: list[str] = []

    if dominant_probability >= 0.25:
        findings.append(
            "A relatively concentrated measurement outcome was observed."
        )
    else:
        findings.append(
            "The measurement distribution is relatively dispersed."
        )

    if normalized_entropy >= 0.90:
        findings.append(
            "Measurement entropy is close to the observed maximum, "
            "indicating a highly dispersed outcome distribution."
        )
    elif normalized_entropy >= 0.70:
        findings.append(
            "Measurement entropy is high relative to the observed state space."
        )
    else:
        findings.append(
            "Measurement entropy remains comparatively concentrated."
        )

    if unique_states >= 16:
        findings.append(
            "A broad set of measurement states was observed."
        )
    elif unique_states <= 4:
        findings.append(
            "Only a small number of measurement states dominated the sample."
        )

    if probability_mass_error > 1e-9:
        findings.append(
            "Probability-mass validation detected a numerical inconsistency."
        )
    else:
        findings.append(
            "Measurement probabilities passed probability-mass validation."
        )

    if success_rate is not None:
        findings.append(
            f"Experiment-level success rate: {success_rate:.2%}."
        )

    if order_recovery_rate is not None:
        findings.append(
            f"Order-recovery rate: {order_recovery_rate:.2%}."
        )

    if factor_recovery_rate is not None:
        findings.append(
            f"Factor-recovery rate: {factor_recovery_rate:.2%}."
        )

    return findings


def _build_recommendations(
    *,
    normalized_entropy: float,
    dominant_probability: float,
    success_rate: Optional[float],
) -> list[str]:
    """Generate research-oriented recommendations."""

    recommendations: list[str] = []

    if normalized_entropy >= 0.90:
        recommendations.append(
            "Increase shots and repeat trials before drawing conclusions "
            "from individual measurement distributions."
        )

    if dominant_probability < 0.15:
        recommendations.append(
            "Inspect whether noise, sampling variance, or circuit depth "
            "is dispersing the expected measurement signal."
        )

    if success_rate is not None and success_rate < 0.80:
        recommendations.append(
            "Investigate circuit quality, noise sensitivity, and "
            "algorithm-level recovery before treating the experiment "
            "as operationally reliable."
        )

    recommendations.append(
        "Compare the noisy result with an ideal or lower-noise baseline."
    )

    recommendations.append(
        "For hardware experiments, record backend calibration and "
        "execution metadata alongside the measurement results."
    )

    recommendations.append(
        "Use multiple independent trials and confidence intervals "
        "for research-grade conclusions."
    )

    return recommendations


# ---------------------------------------------------------------------------
# Main assessment function
# ---------------------------------------------------------------------------

def assess_measurements(
    counts: Mapping[str, int],
    *,
    target_name: str = "unknown",
    target_type: str = "unknown",
    target_size: Optional[int] = None,
    algorithm: str = "unknown",
    noise_model: str = "none",
    noise_probability: Optional[float] = None,
    success_rate: Optional[float] = None,
    order_recovery_rate: Optional[float] = None,
    factor_recovery_rate: Optional[float] = None,
) -> SecurityAssessment:
    """
    Convert raw measurement counts into a security assessment.

    Parameters
    ----------
    counts:
        Measurement-count dictionary, e.g. {"00": 75, "11": 25}.

    target_name:
        Name of the authorized research target.

    target_type:
        Target category, e.g. "rsa".

    target_size:
        Toy target size, e.g. 15.

    algorithm:
        Quantum algorithm used for the experiment.

    noise_model:
        Noise model used by the experiment.

    noise_probability:
        Noise probability when applicable.

    success_rate:
        Optional experiment-level success rate.

    order_recovery_rate:
        Optional order-recovery rate.

    factor_recovery_rate:
        Optional factor-recovery rate.

    Returns
    -------
    SecurityAssessment
        Structured assessment result.
    """

    summary = measurement_summary(counts)

    normalized_entropy = float(summary["normalized_entropy"])
    dominant_probability = float(summary["dominant_probability"])
    unique_states = int(summary["unique_states"])
    probability_mass_error = float(summary["probability_mass_error"])

    assessment_level = _classify_entropy(normalized_entropy)

    # Confidence here refers to the quality of the observed distribution,
    # not the cryptographic validity of the experiment.
    if summary["shots"] >= 1000:
        confidence = "HIGH"
    elif summary["shots"] >= 100:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    findings = _build_findings(
        dominant_probability=dominant_probability,
        normalized_entropy=normalized_entropy,
        unique_states=unique_states,
        probability_mass_error=probability_mass_error,
        success_rate=success_rate,
        order_recovery_rate=order_recovery_rate,
        factor_recovery_rate=factor_recovery_rate,
    )

    recommendations = _build_recommendations(
        normalized_entropy=normalized_entropy,
        dominant_probability=dominant_probability,
        success_rate=success_rate,
    )

    return SecurityAssessment(
        target_name=target_name,
        target_type=target_type,
        target_size=target_size,
        algorithm=algorithm,
        noise_model=noise_model,
        noise_probability=_safe_float(noise_probability),
        shots=int(summary["shots"]),
        success_rate=_safe_float(success_rate),
        order_recovery_rate=_safe_float(order_recovery_rate),
        factor_recovery_rate=_safe_float(factor_recovery_rate),
        dominant_state=summary.get("dominant_state"),
        dominant_probability=dominant_probability,
        shannon_entropy_bits=float(summary["shannon_entropy_bits"]),
        maximum_entropy_bits=float(summary["maximum_entropy_bits"]),
        normalized_entropy=normalized_entropy,
        unique_states=unique_states,
        probability_mass=float(summary["probability_mass"]),
        probability_mass_error=probability_mass_error,
        assessment_level=assessment_level,
        confidence=confidence,
        findings=findings,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_text_report(assessment: SecurityAssessment) -> str:
    """
    Format an assessment as a human-readable text report.
    """

    lines = [
        "=" * 72,
        "QUANTUM SECURITY ASSESSMENT",
        "=" * 72,
        "",
        "TARGET",
        f"  Name              : {assessment.target_name}",
        f"  Type              : {assessment.target_type}",
        f"  Size              : {assessment.target_size}",
        "",
        "EXPERIMENT",
        f"  Algorithm         : {assessment.algorithm}",
        f"  Noise model       : {assessment.noise_model}",
        f"  Noise probability : {assessment.noise_probability}",
        f"  Shots             : {assessment.shots}",
        "",
        "MEASUREMENT",
        f"  Dominant state    : {assessment.dominant_state}",
        f"  Dominant P        : {assessment.dominant_probability:.6f}",
        f"  Unique states     : {assessment.unique_states}",
        f"  Shannon entropy   : {assessment.shannon_entropy_bits:.6f} bits",
        f"  Maximum entropy   : {assessment.maximum_entropy_bits:.6f} bits",
        f"  Normalized entropy: {assessment.normalized_entropy:.6f}",
        f"  Probability mass  : {assessment.probability_mass:.6f}",
        "",
        "RECOVERY",
        f"  Success rate      : {assessment.success_rate}",
        f"  Order recovery    : {assessment.order_recovery_rate}",
        f"  Factor recovery   : {assessment.factor_recovery_rate}",
        "",
        "ASSESSMENT",
        f"  Level             : {assessment.assessment_level}",
        f"  Confidence        : {assessment.confidence}",
        "",
        "FINDINGS",
    ]

    for finding in assessment.findings:
        lines.append(f"  - {finding}")

    lines.extend(
        [
            "",
            "RECOMMENDATIONS",
        ]
    )

    for recommendation in assessment.recommendations:
        lines.append(f"  - {recommendation}")

    lines.extend(
        [
            "",
            f"Generated at: {assessment.generated_at}",
            "=" * 72,
        ]
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------

def assessment_summary(
    counts: Mapping[str, int],
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Return a JSON-compatible assessment dictionary.

    This is the simplest API for downstream services such as a REST API,
    dashboard, reporting pipeline, or agent platform.
    """

    return assess_measurements(counts, **kwargs).to_dict()


__all__ = [
    "SecurityAssessment",
    "assess_measurements",
    "assessment_summary",
    "format_text_report",
]

