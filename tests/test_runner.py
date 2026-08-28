from qattack.benchmarking.runner import (
    BenchmarkRunner,
)


def test_runner_creates_benchmark():

    runner = BenchmarkRunner(
        shots=1024
    )

    result = runner.run_shor_n15()

    assert result.attack == "shor"
    assert result.target == "RSA-Toy-15"
    assert result.size == 15


def test_runner_metrics_exist():

    runner = BenchmarkRunner()

    result = runner.run_shor_n15()

    assert result.logical_qubits > 0
    assert result.circuit_depth > 0
    assert result.gate_count > 0
    assert result.shots == 1024


def test_runner_summary():

    runner = BenchmarkRunner()

    result = runner.run_shor_n15()

    summary = result.summary()

    assert isinstance(summary, dict)

    assert summary["attack"] == "shor"
    assert summary["size"] == 15
    assert "elapsed_seconds" in summary
    assert "metrics" in summary