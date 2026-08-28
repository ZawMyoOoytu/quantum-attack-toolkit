from typing import Any

from qattack.benchmarking.runner import (
    BenchmarkRunner,
    BenchmarkRun,
)


def run_shot_matrix(
    shot_values: list[int],
) -> list[BenchmarkRun]:
    """
    Run the N=15 Shor benchmark for multiple shot counts.

    Example
    -------
    run_shot_matrix([128, 256, 512, 1024])
    """

    if not shot_values:
        return []

    results = []

    for shots in shot_values:

        if shots <= 0:
            raise ValueError(
                "All shot values must be positive."
            )

        runner = BenchmarkRunner(
            shots=shots
        )

        result = runner.run_shor_n15()

        results.append(result)

    return results


def matrix_to_dicts(
    results: list[BenchmarkRun],
) -> list[dict[str, Any]]:
    """
    Convert benchmark matrix results into
    serializable dictionaries.
    """

    return [
        result.summary()
        for result in results
    ]