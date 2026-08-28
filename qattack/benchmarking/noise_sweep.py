from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, stdev
from typing import Iterable

from qattack.analysis.measurement import measurement_summary
from qattack.attacks.shor import ShorAttack
from qattack.core.target import Target
from qattack.quantum.noise import NoiseConfig


@dataclass
class NoiseSweepResult:
    """
    Aggregated statistical result for one noise level.

    The result separates:

    1. Benchmark-level cryptanalytic recovery
       - success_rate
       - order_recovery_rate
       - factor_recovery_rate

    2. Measurement-distribution quality
       - dominant probability
       - Shannon entropy
       - normalized entropy
       - number of unique states
    """

    model: str
    probability: float

    shots: int
    trials: int

    successful_trials: int
    failed_trials: int

    success_rate: float
    order_recovery_rate: float
    factor_recovery_rate: float

    mean_dominant_probability: float
    std_dominant_probability: float

    mean_entropy_bits: float
    std_entropy_bits: float

    mean_normalized_entropy: float
    std_normalized_entropy: float

    mean_unique_states: float
    std_unique_states: float

    def summary(self) -> dict:
        """
        Convert the result into a JSON-serializable dictionary.
        """

        return {
            "model": self.model,
            "probability": self.probability,

            "shots": self.shots,
            "trials": self.trials,

            "successful_trials": self.successful_trials,
            "failed_trials": self.failed_trials,

            "success_rate": self.success_rate,
            "order_recovery_rate": (
                self.order_recovery_rate
            ),
            "factor_recovery_rate": (
                self.factor_recovery_rate
            ),

            "mean_dominant_probability": (
                self.mean_dominant_probability
            ),
            "std_dominant_probability": (
                self.std_dominant_probability
            ),

            "mean_entropy_bits": (
                self.mean_entropy_bits
            ),
            "std_entropy_bits": (
                self.std_entropy_bits
            ),

            "mean_normalized_entropy": (
                self.mean_normalized_entropy
            ),
            "std_normalized_entropy": (
                self.std_normalized_entropy
            ),

            "mean_unique_states": (
                self.mean_unique_states
            ),
            "std_unique_states": (
                self.std_unique_states
            ),
        }


def _safe_stdev(values: list[float]) -> float:
    """
    Return sample standard deviation.

    For a single observation, return 0.0 rather than raising
    StatisticsError.
    """

    if len(values) <= 1:
        return 0.0

    return stdev(values)


def run_depolarizing_sweep(
    probabilities: Iterable[float],
    shots: int = 128,
    trials: int = 5,
) -> list[NoiseSweepResult]:
    """
    Run a statistical depolarizing-noise sweep for the
    N=15 Shor research benchmark.

    Parameters
    ----------
    probabilities:
        Iterable of depolarizing error probabilities.

        Every value must satisfy:

            0.0 <= p <= 1.0

    shots:
        Number of simulator shots per trial.

    trials:
        Number of repeated trials for each noise level.

    Returns
    -------
    list[NoiseSweepResult]
        One aggregated statistical result per probability.

    Notes
    -----
    This function intentionally separates:

        measurement degradation

    from:

        benchmark-level order/factor recovery.

    Therefore a noisy distribution may become nearly uniform
    while the current classical post-processing still recovers
    the toy N=15 factors.
    """

    # ---------------------------------------------------------
    # Validate global parameters
    # ---------------------------------------------------------

    if not isinstance(shots, int):
        raise TypeError(
            "shots must be an integer."
        )

    if shots <= 0:
        raise ValueError(
            "shots must be positive."
        )

    if not isinstance(trials, int):
        raise TypeError(
            "trials must be an integer."
        )

    if trials <= 0:
        raise ValueError(
            "trials must be positive."
        )

    probabilities = list(probabilities)

    # ---------------------------------------------------------
    # Validate probabilities
    # ---------------------------------------------------------

    for probability in probabilities:

        if not isinstance(
            probability,
            (int, float),
        ):
            raise TypeError(
                "Depolarizing probability must be numeric."
            )

        if not 0.0 <= float(probability) <= 1.0:
            raise ValueError(
                "Depolarizing probability must be "
                "between 0 and 1."
            )

    # ---------------------------------------------------------
    # Create benchmark objects once
    # ---------------------------------------------------------

    attack = ShorAttack()

    target = Target(
        target_type="rsa",
        name="RSA-Toy-15",
        size=15,
    )

    results: list[NoiseSweepResult] = []

    # ---------------------------------------------------------
    # Sweep noise levels
    # ---------------------------------------------------------

    for probability in probabilities:

        probability = float(probability)

        successful_trials = 0
        successful_orders = 0
        successful_factors = 0

        dominant_probabilities: list[float] = []
        entropy_values: list[float] = []
        normalized_entropy_values: list[float] = []
        unique_state_values: list[float] = []

        noise_config = NoiseConfig(
            model="depolarizing",
            depolarizing_probability=probability,
        )

        # -----------------------------------------------------
        # Repeated trials
        # -----------------------------------------------------

        for _ in range(trials):

            result = attack.run(
                target,
                shots=shots,
                noise_config=noise_config,
            )

            # -------------------------------------------------
            # Cryptanalytic recovery metrics
            # -------------------------------------------------

            if result.success:
                successful_trials += 1

            metrics = result.metrics

            if metrics.get(
                "order_verified",
                False,
            ):
                successful_orders += 1

            if metrics.get(
                "factors"
            ) is not None:
                successful_factors += 1

            # -------------------------------------------------
            # Measurement-distribution metrics
            # -------------------------------------------------

            counts = metrics.get(
                "counts",
                {},
            )

            summary = measurement_summary(
                counts
            )

            # measurement_summary({}) is supported and returns
            # an empty/zero-safe summary.

            dominant_probabilities.append(
                float(
                    summary.get(
                        "dominant_probability",
                        0.0,
                    )
                )
            )

            entropy_values.append(
                float(
                    summary.get(
                        "shannon_entropy_bits",
                        0.0,
                    )
                )
            )

            normalized_entropy_values.append(
                float(
                    summary.get(
                        "normalized_entropy",
                        0.0,
                    )
                )
            )

            unique_state_values.append(
                float(
                    summary.get(
                        "unique_states",
                        0,
                    )
                )
            )

        # -----------------------------------------------------
        # Aggregate statistics
        # -----------------------------------------------------

        results.append(
            NoiseSweepResult(
                model="depolarizing",
                probability=probability,

                shots=shots,
                trials=trials,

                successful_trials=(
                    successful_trials
                ),

                failed_trials=(
                    trials - successful_trials
                ),

                success_rate=(
                    successful_trials / trials
                ),

                order_recovery_rate=(
                    successful_orders / trials
                ),

                factor_recovery_rate=(
                    successful_factors / trials
                ),

                mean_dominant_probability=(
                    mean(
                        dominant_probabilities
                    )
                ),

                std_dominant_probability=(
                    _safe_stdev(
                        dominant_probabilities
                    )
                ),

                mean_entropy_bits=(
                    mean(
                        entropy_values
                    )
                ),

                std_entropy_bits=(
                    _safe_stdev(
                        entropy_values
                    )
                ),

                mean_normalized_entropy=(
                    mean(
                        normalized_entropy_values
                    )
                ),

                std_normalized_entropy=(
                    _safe_stdev(
                        normalized_entropy_values
                    )
                ),

                mean_unique_states=(
                    mean(
                        unique_state_values
                    )
                ),

                std_unique_states=(
                    _safe_stdev(
                        unique_state_values
                    )
                ),
            )
        )

    return results