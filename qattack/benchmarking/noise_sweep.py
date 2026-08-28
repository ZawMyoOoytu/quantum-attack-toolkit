from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from qattack.attacks.shor import ShorAttack
from qattack.core.target import Target
from qattack.quantum.noise import NoiseConfig


@dataclass
class NoiseSweepResult:
    model: str
    probability: float
    shots: int
    trials: int
    successful_trials: int
    failed_trials: int
    success_rate: float
    order_recovery_rate: float
    factor_recovery_rate: float

    def summary(self) -> dict:
        return {
            "model": self.model,
            "probability": self.probability,
            "shots": self.shots,
            "trials": self.trials,
            "successful_trials": self.successful_trials,
            "failed_trials": self.failed_trials,
            "success_rate": self.success_rate,
            "order_recovery_rate": self.order_recovery_rate,
            "factor_recovery_rate": self.factor_recovery_rate,
        }


def run_depolarizing_sweep(
    probabilities: Iterable[float],
    shots: int = 128,
    trials: int = 5,
) -> list[NoiseSweepResult]:
    """
    Run a depolarizing-noise sweep for the N=15 Shor benchmark.

    Parameters
    ----------
    probabilities:
        Depolarizing error probabilities to test.

    shots:
        Number of simulator shots per trial.

    trials:
        Number of repeated trials per noise level.

    Returns
    -------
    list[NoiseSweepResult]
        Aggregated benchmark results.
    """

    if shots <= 0:
        raise ValueError("shots must be positive.")

    if trials <= 0:
        raise ValueError("trials must be positive.")

    probabilities = list(probabilities)

    for probability in probabilities:
        if not 0.0 <= probability <= 1.0:
            raise ValueError(
                "Depolarizing probability must be between 0 and 1."
            )

    attack = ShorAttack()

    target = Target(
        target_type="rsa",
        name="RSA-Toy-15",
        size=15,
    )

    results: list[NoiseSweepResult] = []

    for probability in probabilities:

        successful_trials = 0
        successful_orders = 0
        successful_factors = 0

        noise_config = NoiseConfig(
            model="depolarizing",
            depolarizing_probability=probability,
        )

        for _ in range(trials):

            result = attack.run(
                target,
                shots=shots,
                noise_config=noise_config,
            )

            if result.success:
                successful_trials += 1

            metrics = result.metrics

            if metrics.get("order_verified", False):
                successful_orders += 1

            if metrics.get("factors") is not None:
                successful_factors += 1

        results.append(
            NoiseSweepResult(
                model="depolarizing",
                probability=probability,
                shots=shots,
                trials=trials,
                successful_trials=successful_trials,
                failed_trials=trials - successful_trials,
                success_rate=successful_trials / trials,
                order_recovery_rate=successful_orders / trials,
                factor_recovery_rate=successful_factors / trials,
            )
        )

    return results