from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qattack.quantum.modular import (
    modular_multiplication_by_2_mod_15,
)


WORK_QUBITS = [0, 1, 2, 3]


def prepare_basis_state(
    value: int,
) -> QuantumCircuit:
    """
    Prepare |value> on four qubits.

    Qubit 0 is the least-significant bit.
    """

    if not 0 <= value < 16:
        raise ValueError(
            "Value must be between 0 and 15."
        )

    qc = QuantumCircuit(4)

    for qubit in WORK_QUBITS:
        if (value >> qubit) & 1:
            qc.x(qubit)

    return qc


def run_and_measure(
    circuit: QuantumCircuit,
) -> int:
    """
    Execute a four-qubit circuit and return
    the most frequently measured basis state.
    """

    measured = QuantumCircuit(
        4,
        4,
    )

    measured.compose(
        circuit,
        inplace=True,
    )

    measured.measure(
        WORK_QUBITS,
        range(4),
    )

    simulator = AerSimulator()

    compiled = transpile(
        measured,
        simulator,
    )

    result = simulator.run(
        compiled,
        shots=256,
    ).result()

    counts = result.get_counts()

    bitstring = max(
        counts,
        key=counts.get,
    )

    return int(
        bitstring,
        2,
    )


def apply_modular_multiplication(
    value: int,
) -> int:
    """
    Apply the current N=15 modular-multiplication
    implementation to a computational basis state.
    """

    qc = prepare_basis_state(value)

    control = 4

    full = QuantumCircuit(5)

    full.compose(
        qc,
        qubits=WORK_QUBITS,
        inplace=True,
    )

    # Activate the controlled operation.
    full.x(control)

    modular_multiplication_by_2_mod_15(
        qc=full,
        control=control,
        work_qubits=WORK_QUBITS,
    )

    return run_full_and_measure(full)


def run_full_and_measure(
    circuit: QuantumCircuit,
) -> int:

    measured = QuantumCircuit(
        circuit.num_qubits,
        4,
    )

    measured.compose(
        circuit,
        inplace=True,
    )

    measured.measure(
        WORK_QUBITS,
        range(4),
    )

    simulator = AerSimulator()

    compiled = transpile(
        measured,
        simulator,
    )

    result = simulator.run(
        compiled,
        shots=256,
    ).result()

    counts = result.get_counts()

    bitstring = max(
        counts,
        key=counts.get,
    )

    # The classical register contains the four
    # work-qubit measurements.
    return int(
        bitstring,
        2,
    )


def test_modular_mapping_one():

    result = apply_modular_multiplication(1)

    assert result == 2


def test_modular_mapping_two():

    result = apply_modular_multiplication(2)

    assert result == 4


def test_modular_mapping_four():

    result = apply_modular_multiplication(4)

    assert result == 8


def test_modular_mapping_eight():

    result = apply_modular_multiplication(8)

    assert result == 1