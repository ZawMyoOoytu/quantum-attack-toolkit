from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from qattack.benchmarking.experiment import (
    ExperimentResult,
)


def experiment_results_to_dicts(
    results: Iterable[ExperimentResult],
) -> list[dict]:
    """
    Convert experiment results into flat dictionaries.
    """

    rows = []

    for result in results:

        summary = result.summary()

        rows.append(
            {
                "attack": summary["attack"],
                "target": summary["target"],
                "target_type": summary["target_type"],
                "size": summary["size"],
                "shots": summary["shots"],
                "trials": summary["trials"],
                "successful_trials": summary[
                    "successful_trials"
                ],
                "failed_trials": summary[
                    "failed_trials"
                ],
                "success_rate": summary[
                    "success_rate"
                ],
                "order_recovery_rate": summary[
                    "order_recovery_rate"
                ],
                "factor_recovery_rate": summary[
                    "factor_recovery_rate"
                ],
                "mean_elapsed_seconds": summary[
                    "mean_elapsed_seconds"
                ],
            }
        )

    return rows


def write_experiment_csv(
    results: Iterable[ExperimentResult],
    path: str | Path,
) -> Path:
    """
    Write experiment results to CSV.
    """

    rows = experiment_results_to_dicts(
        results
    )

    output_path = Path(path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not rows:
        raise ValueError(
            "Cannot write an empty experiment result."
        )

    fieldnames = list(
        rows[0].keys()
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            rows
        )

    return output_path