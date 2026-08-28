from qattack.benchmarking.runner import (
    BenchmarkRunner,
)

from qattack.benchmarking.statistics import (
    BenchmarkStatistics,
    calculate_statistics,
)


def test_calculate_statistics():

    runner = BenchmarkRunner(
        shots=128
    )

    results = runner.run_repeated(
        "shor-n15",
        trials=2,
    )

    stats = calculate_statistics(
        results
    )

    assert isinstance(
        stats,
        BenchmarkStatistics,
    )

    assert stats.trials == 2

    assert stats.shots == 128

    assert (
        stats.successful_trials
        + stats.failed_trials
        == 2
    )

    assert (
        0.0
        <= stats.success_rate
        <= 1.0
    )


def test_statistics_summary():

    runner = BenchmarkRunner(
        shots=128
    )

    results = runner.run_repeated(
        "shor-n15",
        trials=2,
    )

    stats = calculate_statistics(
        results
    )

    summary = stats.summary()

    assert isinstance(
        summary,
        dict,
    )

    assert summary["attack"] == "shor"

    assert summary["target"] == "RSA-Toy-15"

    assert summary["shots"] == 128

    assert summary["trials"] == 2

    assert "success_rate" in summary

    assert "mean_elapsed_seconds" in summary