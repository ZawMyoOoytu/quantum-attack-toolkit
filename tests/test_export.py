from pathlib import Path

from qattack.benchmarking.experiment import (
    run_experiment_matrix,
)

from qattack.benchmarking.export import (
    experiment_results_to_dicts,
    write_experiment_csv,
)


def test_experiment_results_to_dicts():

    results = run_experiment_matrix(
        "shor-n15",
        [64],
        trials=1,
    )

    rows = experiment_results_to_dicts(
        results
    )

    assert isinstance(
        rows,
        list,
    )

    assert len(rows) == 1

    assert rows[0]["attack"] == "shor"

    assert rows[0]["shots"] == 64

    assert rows[0]["trials"] == 1


def test_write_experiment_csv(
    tmp_path: Path,
):

    results = run_experiment_matrix(
        "shor-n15",
        [64],
        trials=1,
    )

    output = tmp_path / "experiment.csv"

    returned = write_experiment_csv(
        results,
        output,
    )

    assert returned == output

    assert output.exists()

    text = output.read_text(
        encoding="utf-8"
    )

    assert "attack" in text

    assert "shots" in text

    assert "success_rate" in text