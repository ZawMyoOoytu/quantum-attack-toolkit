
"""
Quantum Security Risk Engine.

Converts quantum-security assessment evidence into:

    - Quantum exposure score
    - Risk level
    - Risk factors
    - Security recommendations

This module is designed to sit after the quantum experiment and
measurement/evidence layers:

    Quantum Experiment
            |
            v
       Measurement
            |
            v
         Evidence
            |
            v
       Risk Engine
            |
            v
     Security Assessment
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RiskAssessment:
    """
    Result of a quantum-security risk assessment.

    score:
        Quantum exposure score from 0 to 100.

    level:
        LOW, MEDIUM, HIGH, or CRITICAL.

    attack_success:
        Whether the benchmark attack successfully recovered the
        expected order/factors.

    noise_sensitivity:
        Estimated sensitivity to the supplied noise condition.

    migration_priority:
        Recommended migration priority.
    """

    score: float
    level: str
    attack_success: bool
    noise_sensitivity: str
    migration_priority: str
    rationale: list[str]
    recommendations: list[str]

    def summary(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""

        return asdict(self)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _number(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    """Safely convert a value to boolean."""

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "verified",
            "success",
            "successful",
        }

    return bool(value)


def _normalize_evidence(
    evidence: Mapping[str, Any] | Any,
) -> dict[str, Any]:
    """
    Normalize flat or nested evidence.

    Supported structures include:

        {
            "attack": {...},
            "measurement": {...},
            "experiment": {...},
            "target": {...}
        }

    and already-flattened dictionaries.
    """

    if isinstance(evidence, Mapping):
        data = dict(evidence)

    elif hasattr(evidence, "summary"):
        summary = evidence.summary()

        if not isinstance(summary, Mapping):
            raise TypeError(
                "evidence.summary() must return a mapping."
            )

        data = dict(summary)

    elif hasattr(evidence, "__dataclass_fields__"):
        data = asdict(evidence)

    else:
        raise TypeError(
            "evidence must be a mapping, dataclass, "
            "or object exposing summary()."
        )

    target = data.get("target")
    experiment = data.get("experiment")
    measurement = data.get("measurement")
    attack = data.get("attack")

    if isinstance(target, Mapping):
        data.setdefault("target_name", target.get("name"))
        data.setdefault("target_type", target.get("type"))
        data.setdefault("target_size", target.get("size"))

    if isinstance(experiment, Mapping):
        data.setdefault(
            "noise_model",
            experiment.get("noise_model"),
        )

        data.setdefault(
            "noise_probability",
            experiment.get("noise_probability"),
        )

        data.setdefault(
            "shots",
            experiment.get("shots"),
        )

    if isinstance(measurement, Mapping):
        for key in (
            "dominant_state",
            "dominant_probability",
            "shannon_entropy_bits",
            "maximum_entropy_bits",
            "normalized_entropy",
            "unique_states",
            "probability_mass",
            "probability_mass_error",
        ):
            if key in measurement:
                data.setdefault(key, measurement[key])

    if isinstance(attack, Mapping):
        for key in (
            "recovered_order",
            "order_verified",
            "factors",
            "expected_order",
            "expected_factors",
            "method",
        ):
            if key in attack:
                data.setdefault(key, attack[key])

        data.setdefault(
            "attack_method",
            attack.get("method"),
        )

        data.setdefault(
            "noise_model",
            attack.get("noise_model"),
        )

        data.setdefault(
            "noise_probability",
            attack.get("noise_probability"),
        )

    return data


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

def risk_level(score: float) -> str:
    """
    Convert a 0-100 score into a risk category.

    0-24   LOW
    25-49  MEDIUM
    50-74  HIGH
    75-100 CRITICAL
    """

    score = max(0.0, min(100.0, score))

    if score >= 75:
        return "CRITICAL"

    if score >= 50:
        return "HIGH"

    if score >= 25:
        return "MEDIUM"

    return "LOW"


def migration_priority(level: str) -> str:
    """Return migration priority associated with a risk level."""

    priorities = {
        "LOW": "MONITOR",
        "MEDIUM": "PLAN",
        "HIGH": "PRIORITIZE",
        "CRITICAL": "URGENT",
    }

    return priorities.get(level, "MONITOR")


def _noise_sensitivity(
    noise_probability: float,
) -> str:
    """
    Classify the supplied noise condition.

    This is a benchmark interpretation, not a hardware-quality
    certification.
    """

    if noise_probability < 0.05:
        return "LOW"

    if noise_probability < 0.15:
        return "MODERATE"

    if noise_probability < 0.50:
        return "HIGH"

    return "VERY HIGH"


# ---------------------------------------------------------------------------
# Main assessment
# ---------------------------------------------------------------------------

def assess_quantum_risk(
    evidence: Mapping[str, Any] | Any,
) -> RiskAssessment:
    """
    Calculate a quantum-security exposure score.

    The score is intentionally an assessment heuristic rather than
    a cryptographic security proof.

    Scoring dimensions:

        Attack verification       0-40
        Noise exposure            0-25
        Measurement uncertainty   0-20
        Target cryptographic      0-15

    Maximum score = 100.
    """

    data = _normalize_evidence(evidence)

    score = 0.0
    rationale: list[str] = []
    recommendations: list[str] = []

    # ------------------------------------------------------------------
    # 1. Attack verification
    # ------------------------------------------------------------------

    attack_success = _bool(
        data.get("order_verified", False)
    )

    recovered_order = data.get("recovered_order")
    factors = data.get("factors")

    if attack_success:
        score += 40

        rationale.append(
            "Quantum period-finding benchmark successfully "
            "verified the recovered order."
        )

        if factors:
            rationale.append(
                f"Candidate factors were recovered: {factors}."
            )

    else:
        score += 10

        rationale.append(
            "Quantum attack result was not verified."
        )

    # ------------------------------------------------------------------
    # 2. Noise exposure
    # ------------------------------------------------------------------

    noise_probability = _number(
        data.get("noise_probability")
    )

    if noise_probability >= 0.50:
        noise_points = 25

    elif noise_probability >= 0.20:
        noise_points = 20

    elif noise_probability >= 0.10:
        noise_points = 15

    elif noise_probability >= 0.05:
        noise_points = 10

    else:
        noise_points = 0

    score += noise_points

    noise_level = _noise_sensitivity(
        noise_probability
    )

    rationale.append(
        f"Benchmark noise condition is classified as "
        f"{noise_level.lower()} sensitivity "
        f"(p={noise_probability:.4f})."
    )

    # ------------------------------------------------------------------
    # 3. Measurement uncertainty
    # ------------------------------------------------------------------

    normalized_entropy = _number(
        data.get("normalized_entropy")
    )

    dominant_probability = _number(
        data.get("dominant_probability")
    )

    if normalized_entropy >= 0.95:
        entropy_points = 20

    elif normalized_entropy >= 0.80:
        entropy_points = 15

    elif normalized_entropy >= 0.60:
        entropy_points = 10

    elif normalized_entropy > 0:
        entropy_points = 5

    else:
        entropy_points = 0

    score += entropy_points

    if normalized_entropy > 0:
        rationale.append(
            f"Measurement normalized entropy is "
            f"{normalized_entropy:.4f}."
        )

    if dominant_probability > 0:
        rationale.append(
            f"Dominant measurement probability is "
            f"{dominant_probability:.4f}."
        )

    # ------------------------------------------------------------------
    # 4. Target type / cryptographic exposure
    # ------------------------------------------------------------------

    target_type = str(
        data.get("target_type", "")
    ).lower()

    target_size = data.get("target_size")

    if target_type in {
        "rsa",
        "ecc",
        "ecdsa",
        "ecdh",
        "dh",
        "dsa",
    }:
        score += 15

        rationale.append(
            f"Target type '{target_type}' is based on "
            "cryptographic assumptions known to be relevant "
            "to future cryptographically relevant quantum computers."
        )

    elif target_type:
        score += 5

        rationale.append(
            f"Target type '{target_type}' requires "
            "additional cryptographic analysis."
        )

    else:
        score += 0

    score = max(
        0.0,
        min(100.0, score),
    )

    level = risk_level(score)

    priority = migration_priority(level)

    # ------------------------------------------------------------------
    # Recommendations
    # ------------------------------------------------------------------

    if attack_success:
        recommendations.append(
            "Treat the benchmark as evidence that the "
            "quantum attack workflow can recover the target's "
            "period under the tested conditions."
        )

    if target_type in {
        "rsa",
        "ecc",
        "ecdsa",
        "ecdh",
        "dh",
        "dsa",
    }:
        recommendations.append(
            "Inventory production systems that depend on "
            "quantum-vulnerable public-key cryptography."
        )

        recommendations.append(
            "Evaluate a migration path toward "
            "post-quantum cryptography."
        )

    if noise_probability >= 0.10:
        recommendations.append(
            "Repeat the experiment across multiple noise levels "
            "and hardware backends before drawing operational conclusions."
        )

    if normalized_entropy >= 0.90:
        recommendations.append(
            "Investigate measurement-distribution degradation "
            "because the observed distribution is highly dispersed."
        )

    recommendations.append(
        "Do not interpret this toy benchmark as a demonstration "
        "of practical RSA-2048 or ECC compromise."
    )

    return RiskAssessment(
        score=round(score, 4),
        level=level,
        attack_success=attack_success,
        noise_sensitivity=noise_level,
        migration_priority=priority,
        rationale=rationale,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Convenience aliases
# ---------------------------------------------------------------------------

def quantum_risk_score(
    evidence: Mapping[str, Any] | Any,
) -> float:
    """Return only the numeric quantum exposure score."""

    return assess_quantum_risk(evidence).score


def quantum_risk_level(
    evidence: Mapping[str, Any] | Any,
) -> str:
    """Return only the risk classification."""

    return assess_quantum_risk(evidence).level


__all__ = [
    "RiskAssessment",
    "assess_quantum_risk",
    "quantum_risk_score",
    "quantum_risk_level",
    "risk_level",
    "migration_priority",
]

