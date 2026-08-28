from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from qattack.quantum.modular import (
    modular_multiplication_by_2_mod_15,
)


WORK_QUBITS = [0, 1, 2, 3]
CONTROL = 4


def prepare_basis_state(value: int) -> QuantumCircuit:
    """
    Prepare |value> on four work qubits.
    """

    if not 0 <= value < 16:
        raise ValueError(
            "value must be between 0 and 15"
        )

    qc = QuantumCircuit(5)

    for qubit in WORK_QUBITS:
        if (value >> qubit) & 1:
            qc.x(qubit)

    # Enable the controlled modular operation.
    qc.x(CONTROL)

    return qc


def apply_u(qc: QuantumCircuit) -> None:
    """
    Apply the controlled N=15 modular
    multiplication operation.

    Because CONTROL is prepared in |1>,
    the controlled operation acts on the
    work register.
    """

    modular_multiplication_by_2_mod_15(
        qc=qc,
        control=CONTROL,
        work_qubits=WORK_QUBITS,
    )


def measure_work_register(
    qc: QuantumCircuit,
) -> int:
    """
    Measure the four work qubits and return
    the dominant computational-basis value.
    """

    measured = QuantumCircuit(
        5,
        4,
    )

    measured.compose(
        qc,
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


def apply_u_power(
    initial_value: int,
    power: int,
) -> int:
    """
    Apply U repeatedly to |initial_value>.

    Returns the measured work-register value.
    """

    qc = prepare_basis_state(
        initial_value
    )

    for _ in range(power):
        apply_u(qc)

    return measure_work_register(qc)


def test_u_one_maps_1_to_2():
    result = apply_u_power(
        initial_value=1,
        power=1,
    )

    assert result == 2


def test_u_two_maps_1_to_4():
    result = apply_u_power(
        initial_value=1,
        power=2,
    )

    assert result == 4


def test_u_three_maps_1_to_8():
    result = apply_u_power(
        initial_value=1,
        power=3,
    )

    assert result == 8


def test_u_four_returns_to_1():
    result = apply_u_power(
        initial_value=1,
        power=4,
    )

    assert result == 1


def test_u_four_maps_2_back_to_2():
    result = apply_u_power(
        initial_value=2,
        power=4,
    )

    assert result == 2


def test_u_four_maps_4_back_to_4():
    result = apply_u_power(
        initial_value=4,
        power=4,
    )

    assert result == 4


def test_u_four_maps_8_back_to_8():
    result = apply_u_power(
        initial_value=8,
        power=4,
    )

    assert result == 8