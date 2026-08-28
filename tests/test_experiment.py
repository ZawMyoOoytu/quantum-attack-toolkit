from qattack.benchmarking.experiment import (
    ExperimentResult,
    run_experiment_matrix,
)


def test_run_experiment_matrix():

    results = run_experiment_matrix(
        "shor-n15",
        [64],
        trials=2,
    )

    assert isinstance(
        results,
        list,
    )

    assert len(results) == 1

    result = results[0]

    assert isinstance(
        result,
        ExperimentResult,
    )

    assert result.shots == 64

    assert result.trials == 2

    assert result.statistics.trials == 2

    assert result.statistics.shots == 64


def test_experiment_summary():

    results = run_experiment_matrix(
        "shor-n15",
        [64],
        trials=2,
    )

    summary = results[0].summary()

    assert isinstance(
        summary,
        dict,
    )

    assert summary["attack"] == "shor"

    assert summary["target"] == "RSA-Toy-15"

    assert summary["shots"] == 64

    assert summary["trials"] == 2

    assert "success_rate" in summary

    assert "order_recovery_rate" in summary

    assert "factor_recovery_rate" in summary

    assert "mean_elapsed_seconds" in summary