from qattack.benchmarking.runner import BenchmarkRunner
from qattack.reporting.report import (
    benchmark_to_dict,
    benchmark_to_json,
    benchmark_summary_text,
    save_benchmark_json,
    save_benchmark_summary,
)


def test_benchmark_to_dict():

    runner = BenchmarkRunner(
        shots=256
    )

    result = runner.run_shor_n15()

    data = benchmark_to_dict(
        result
    )

    assert isinstance(
        data,
        dict
    )

    assert data["attack"] == "shor"
    assert data["target"] == "RSA-Toy-15"
    assert data["size"] == 15


def test_benchmark_to_json():

    runner = BenchmarkRunner(
        shots=256
    )

    result = runner.run_shor_n15()

    text = benchmark_to_json(
        result
    )

    assert isinstance(
        text,
        str
    )

    assert '"attack": "shor"' in text
    assert '"size": 15' in text
    assert '"success":' in text


def test_summary_text():

    runner = BenchmarkRunner(
        shots=256
    )

    result = runner.run_shor_n15()

    text = benchmark_summary_text(
        result
    )

    assert "Quantum Attack Toolkit Benchmark" in text
    assert "Attack:              shor" in text
    assert "Target:              RSA-Toy-15" in text
    assert "Logical qubits:" in text
    assert "Circuit depth:" in text


def test_save_benchmark_json(
    tmp_path,
):

    runner = BenchmarkRunner(
        shots=256
    )

    result = runner.run_shor_n15()

    output = (
        tmp_path
        / "benchmark.json"
    )

    saved = save_benchmark_json(
        result,
        output,
    )

    assert saved.exists()

    content = saved.read_text(
        encoding="utf-8"
    )

    assert '"attack": "shor"' in content


def test_save_benchmark_summary(
    tmp_path,
):

    runner = BenchmarkRunner(
        shots=256
    )

    result = runner.run_shor_n15()

    output = (
        tmp_path
        / "benchmark.txt"
    )

    saved = save_benchmark_summary(
        result,
        output,
    )

    assert saved.exists()

    content = saved.read_text(
        encoding="utf-8"
    )

    assert (
        "Quantum Attack Toolkit Benchmark"
        in content
    )