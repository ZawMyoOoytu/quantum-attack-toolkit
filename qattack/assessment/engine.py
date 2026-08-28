
"""
Quantum Security Assessment Engine.

This module provides a high-level interface for running an authorized
quantum-security assessment against toy cryptographic targets.

The engine combines:

    Target
      -> Attack
      -> Noise
      -> Measurement Analysis
      -> Security Metrics

It is designed as an application layer above the lower-level qattack
components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qattack.analysis.measurement import measurement_summary
from qattack.attacks.shor import ShorAttack
from qattack.core.target import Target
from qattack.quantum.noise import NoiseConfig


@dataclass
class AssessmentResult:
    """Structured result returned by the assessment engine."""

    target_name: str
    target_type: str
    target_size: int

    shots: int
    noise_model: str
    noise_probability: float

    measurement: dict[str, Any]
    attack_metrics: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        """Return a JSON-serializable assessment summary."""

        return {
            "target": {
                "name": self.target_name,
                "type": self.target_type,
                "size": self.target_size,
            },
            "experiment": {
                "shots": self.shots,
                "noise_model": self.noise_model,
                "noise_probability": self.noise_probability,
            },
            "measurement": self.measurement,
            "attack": self.attack_metrics,
        }


class QuantumSecurityAssessment:
    """
    High-level quantum-security assessment interface.

    The class currently supports the Shor attack implementation used by
    the toolkit and is intentionally structured so additional attack
    engines and hardware backends can be added later.
    """

    def __init__(self) -> None:
        self.attack = ShorAttack()

    def run(
        self,
        *,
        target: Target,
        shots: int = 128,
        noise_model: str = "depolarizing",
        noise_probability: float = 0.0,
    ) -> AssessmentResult:
        """
        Execute one quantum-security assessment.

        Parameters
        ----------
        target:
            Authorized toy cryptographic target.

        shots:
            Number of measurement shots.

        noise_model:
            Quantum noise model.

        noise_probability:
            Probability parameter used by the selected noise model.

        Returns
        -------
        AssessmentResult
            Structured measurement and attack metrics.
        """

        if shots <= 0:
            raise ValueError("shots must be greater than zero.")

        if not 0.0 <= noise_probability <= 1.0:
            raise ValueError(
                "noise_probability must be between 0.0 and 1.0."
            )

        noise_config = NoiseConfig(
            model=noise_model,
            depolarizing_probability=noise_probability,
        )

        result = self.attack.run(
            target,
            shots=shots,
            noise_config=noise_config,
        )

        counts = result.metrics.get("counts", {})

        measurement = measurement_summary(counts)

        attack_metrics = {
            key: value
            for key, value in result.metrics.items()
            if key != "counts"
        }

        return AssessmentResult(
            target_name=target.name,
            target_type=target.target_type,
            target_size=target.size,
            shots=shots,
            noise_model=noise_model,
            noise_probability=noise_probability,
            measurement=measurement,
            attack_metrics=attack_metrics,
        )

