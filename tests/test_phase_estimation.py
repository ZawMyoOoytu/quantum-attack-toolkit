from qattack.quantum.phase_estimation import (
    build_qpe_circuit,
    cycle_eigenstate,
    dominant_phase,
    run_qpe,
)


def test_cycle_eigenstate_is_normalized():

    state = cycle_eigenstate(
        eigen_index=1
    )

    norm = sum(
        abs(value) ** 2
        for value in state
    )

    assert abs(norm - 1.0) < 1e-12


def test_cycle_eigenstate_support():

    state = cycle_eigenstate(
        eigen_index=1
    )

    nonzero = [
        index
        for index, value in enumerate(state)
        if abs(value) > 1e-12
    ]

    assert nonzero == [
        1,
        2,
        4,
        8,
    ]


def test_qpe_circuit_size():

    qc = build_qpe_circuit(
        eigen_index=1
    )

    assert qc.num_qubits == 7


def test_qpe_phase_for_eigenvalue_one():

    counts = run_qpe(
        eigen_index=1,
        shots=1024,
    )

    phase = dominant_phase(
        counts
    )

    assert abs(
        phase - 0.25
    ) <= 0.125


def test_qpe_phase_for_eigenvalue_two():

    counts = run_qpe(
        eigen_index=2,
        shots=1024,
    )

    phase = dominant_phase(
        counts
    )

    assert abs(
        phase - 0.50
    ) <= 0.125