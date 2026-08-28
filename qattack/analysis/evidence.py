
"""
Quantum Security Assessment Evidence

Converts a QuantumSecurityAssessment result into a
machine-readable security evidence record.

This module does not perform attacks itself.
It organizes experimental observations for analysis,
reporting, reproducibility, and downstream automation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class SecurityEvidence:
    """Structured evidence produced by a quantum security assessment."""

    target_name: str
    target_type: str
    target_size: int

    shots: int
    noise_model: str
    noise_probability: float

    recovered_order: int | None
    order_verified: bool

    factors: tuple[int, int] | None

    dominant_state: str | None
    dominant_probability: float

    shannon_entropy_bits: float
    maximum_entropy_bits: float
    normalized_entropy: float

    probability_mass: float
    probability_mass_error: float

    attack_method: str

    def summary(self) -> dict[str, Any]:
        """Return JSON-compatible evidence."""

        return asdict(self)

    def save_json(self, path: str | Path) -> Path:
        """Save evidence as formatted JSON."""

        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)

        output.write_text(
            json.dumps(
                self.summary(),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output


def evidence_from_result(result: Any) -> SecurityEvidence:
    """
    Convert QuantumSecurityAssessment result into SecurityEvidence.

    The function accepts either an object exposing ``summary()``
    or a mapping containing the same information.
    """

    if hasattr(result, "summary"):
        data = result.summary()
    elif isinstance(result, Mapping):
        data = dict(result)
    else:
        raise TypeError(
            "result must provide summary() or be a mapping."
        )

    target = data.get("target", {})
    experiment = data.get("experiment", {})
    measurement = data.get("measurement", {})
    attack = data.get("attack", {})

    factors = attack.get("factors")

    if factors is not None:
        factors = tuple(factors)

    return SecurityEvidence(
        target_name=str(target.get("name", "unknown")),
        target_type=str(target.get("type", "unknown")),
        target_size=int(target.get("size", 0)),

        shots=int(experiment.get("shots", measurement.get("shots", 0))),
        noise_model=str(
            experiment.get(
                "noise_model",
                attack.get("noise_model", "unknown"),
            )
        ),
        noise_probability=float(
            experiment.get(
                "noise_probability",
                attack.get("noise_probability", 0.0),
            )
        ),

        recovered_order=attack.get("recovered_order"),
        order_verified=bool(attack.get("order_verified", False)),

        factors=factors,

        dominant_state=measurement.get("dominant_state"),
        dominant_probability=float(
            measurement.get("dominant_probability", 0.0)
        ),

        shannon_entropy_bits=float(
            measurement.get("shannon_entropy_bits", 0.0)
        ),
        maximum_entropy_bits=float(
            measurement.get("maximum_entropy_bits", 0.0)
        ),
        normalized_entropy=float(
            measurement.get("normalized_entropy", 0.0)
        ),

        probability_mass=float(
            measurement.get("probability_mass", 0.0)
        ),
        probability_mass_error=float(
            measurement.get("probability_mass_error", 0.0)
        ),

        attack_method=str(
            attack.get(
                "method",
                "quantum-security-assessment",
            )
        ),
    )


def save_evidence(
    result: Any,
    path: str | Path,
) -> Path:
    """Convert an assessment result and save it as JSON evidence."""

    evidence = evidence_from_result(result)
    return evidence.save_json(path)


__all__ = [
    "SecurityEvidence",
    "evidence_from_result",
    "save_evidence",
]

