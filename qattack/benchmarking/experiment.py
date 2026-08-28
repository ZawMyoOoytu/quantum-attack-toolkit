from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from qattack.benchmarking.runner import BenchmarkRunner
from qattack.benchmarking.statistics import (
    BenchmarkStatistics,
    calculate_statistics,
)


@dataclass
class ExperimentResult:
    """
    Statistical result for one shot level.
    """

    shots: int
    trials: int
    statistics: BenchmarkStatistics

    def summary(self) -> dict:
        """
        Return a JSON-friendly experiment summary.
        """

        data = self.statistics.summary()

        data["shots"] = self.shots
        data["trials"] = self.trials

        return data


def run_experiment_matrix(
    attack_name: str,
    shot_levels: Iterable[int],
    trials: int,
) -> list[ExperimentResult]:
    """
    Execute a repeated benchmark for every shot level.

    Example:

        run_experiment_matrix(
            "shor-n15",
            [128, 256, 512, 1024],
            trials=10,
        )

    Each shot level gets its own BenchmarkRunner so that
    every trial uses the requested shot count.
    """

    if trials < 1:
        raise ValueError(
            "trials must be at least 1."
        )

    normalized_shots = list(
        shot_levels
    )

    if not normalized_shots:
        raise ValueError(
            "shot_levels must not be empty."
        )

    results: list[ExperimentResult] = []

    for shots in normalized_shots:

        if shots < 1:
            raise ValueError(
                "Each shot level must be at least 1."
            )

        runner = BenchmarkRunner(
            shots=shots
        )

        runs = runner.run_repeated(
            attack_name,
            trials=trials,
        )

        statistics = calculate_statistics(
            runs
        )

        results.append(
            ExperimentResult(
                shots=shots,
                trials=trials,
                statistics=statistics,
            )
        )

    return results