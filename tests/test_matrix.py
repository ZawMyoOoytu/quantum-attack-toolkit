from qattack.benchmarking.matrix import (
    run_shot_matrix,
    matrix_to_dicts,
)


def test_run_shot_matrix():

    results = run_shot_matrix(
        [128, 256]
    )

    assert len(results) == 2

    assert results[0].shots == 128
    assert results[1].shots == 256


def test_matrix_results_have_metrics():

    results = run_shot_matrix(
        [128]
    )

    result = results[0]

    assert result.attack == "shor"
    assert result.target == "RSA-Toy-15"
    assert result.size == 15

    assert "N" in result.metrics
    assert "a" in result.metrics
    assert "candidate_orders" in result.metrics


def test_matrix_to_dicts():

    results = run_shot_matrix(
        [128]
    )

    data = matrix_to_dicts(
        results
    )

    assert isinstance(
        data,
        list
    )

    assert len(data) == 1

    assert data[0]["attack"] == "shor"
    assert data[0]["shots"] == 128