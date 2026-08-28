from qattack.benchmarking.runner import (
    BenchmarkRunner,
)
from qattack.benchmarking.statistics import (
    analyze_benchmark_runs,
)


def test_repeated_runner():

    runner = BenchmarkRunner(
        shots=128
    )

    results = runner.run_repeated(
        "shor-n15",
        trials=2,
    )

    assert len(results) == 2

    assert all(
        result.shots == 128
        for result in results
    )


def test_statistics():

    runner = BenchmarkRunner(
        shots=128
    )

    results = runner.run_repeated(
        "shor-n15",
        trials=2,
    )

    stats = analyze_benchmark_runs(
        results
    )

    assert stats.trials == 2

    assert stats.shots == 128

    assert 0.0 <= stats.success_rate <= 1.0

    assert (
        0.0
        <= stats.order_recovery_rate
        <= 1.0
    )

    assert (
        0.0
        <= stats.factor_recovery_rate
        <= 1.0
    )


def test_statistics_summary():

    runner = BenchmarkRunner(
        shots=128
    )

    results = runner.run_repeated(
        "shor-n15",
        trials=1,
    )

    stats = analyze_benchmark_runs(
        results
    )

    summary = stats.summary()

    assert isinstance(
        summary,
        dict,
    )

    assert summary["shots"] == 128

    assert summary["trials"] == 1

    assert (
        "success_rate"
        in summary
    )