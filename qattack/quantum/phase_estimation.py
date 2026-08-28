"""
Quantum Phase Estimation benchmark for the N=15 toy
modular multiplication unitary.

This module is intended for educational and research
benchmarking only.

It does not access real cryptographic keys, credentials,
or third-party systems.
"""

from __future__ import annotations

import numpy as np

from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator

from qattack.quantum.modular import (
    modular_permutation_matrix,
)


MODULUS = 15
MULTIPLIER = 2

NUM_WORK_QUBITS = 4
NUM_PHASE_QUBITS = 3

WORK_QUBITS = list(
    range(NUM_PHASE_QUBITS, NUM_PHASE_QUBITS + NUM_WORK_QUBITS)
)

PHASE_QUBITS = list(
    range(NUM_PHASE_QUBITS)
)


def cycle_eigenstate(
    eigen_index: int,
) -> np.ndarray:
    """
    Construct an eigenstate of the N=15 modular
    multiplication permutation restricted to the
    cycle

        1 -> 2 -> 4 -> 8 -> 1

    Eigenstates are

        |psi_k> =
            1/2 sum_j exp(-2*pi*i*k*j/4)
            |cycle_j>

    for k = 0,1,2,3.

    The corresponding eigenvalue is

        exp(2*pi*i*k/4).
    """

    if eigen_index not in range(4):
        raise ValueError(
            "eigen_index must be 0, 1, 2, or 3"
        )

    state = np.zeros(
        16,
        dtype=complex,
    )

    cycle = [1, 2, 4, 8]

    for j, value in enumerate(cycle):

        amplitude = np.exp(
            -2j
            * np.pi
            * eigen_index
            * j
            / 4
        ) / 2

        state[value] = amplitude

    return state


def prepare_cycle_eigenstate(
    qc: QuantumCircuit,
    work_qubits: list[int],
    eigen_index: int,
) -> None:
    """
    Prepare the cycle eigenstate on the four work qubits.
    """

    state = cycle_eigenstate(
        eigen_index
    )

    qc.initialize(
        state,
        work_qubits,
    )


def append_controlled_power(
    qc: QuantumCircuit,
    control: int,
    work_qubits: list[int],
    power: int,
) -> None:
    """
    Append controlled-U^power.

    U is the N=15 permutation

        |y> -> |2y mod 15>.

    Repeating controlled-U 'power' times gives
    controlled-U^power.
    """

    if power < 1:
        raise ValueError(
            "power must be >= 1"
        )

    for _ in range(power):

        from qattack.quantum.modular import (
            modular_multiplication_by_2_mod_15,
        )

        modular_multiplication_by_2_mod_15(
            qc=qc,
            control=control,
            work_qubits=work_qubits,
        )


def inverse_qft(
    qc: QuantumCircuit,
    qubits: list[int],
) -> None:
    """
    Apply an explicit inverse Quantum Fourier Transform.
    """

    n = len(qubits)

    # Swap qubit order.
    for i in range(n // 2):
        qc.swap(
            qubits[i],
            qubits[n - i - 1],
        )

    # Inverse QFT.
    for j in range(n):

        for m in range(j):

            angle = -np.pi / (
                2 ** (j - m)
            )

            qc.cp(
                angle,
                qubits[m],
                qubits[j],
            )

        qc.h(
            qubits[j]
        )


def build_qpe_circuit(
    eigen_index: int = 1,
) -> QuantumCircuit:
    """
    Build a complete QPE circuit.

    For eigen_index=1 the expected phase is

        1/4 = 0.25

    using three phase-estimation qubits.
    """

    total_qubits = (
        NUM_PHASE_QUBITS
        + NUM_WORK_QUBITS
    )

    qc = QuantumCircuit(
        total_qubits,
        NUM_PHASE_QUBITS,
    )

    # Prepare eigenstate of U.
    prepare_cycle_eigenstate(
        qc,
        WORK_QUBITS,
        eigen_index,
    )

    # Phase register in uniform superposition.
    for qubit in PHASE_QUBITS:
        qc.h(qubit)

    # Controlled-U^(2^j).
    for j, control in enumerate(
        PHASE_QUBITS
    ):

        power = 2 ** j

        append_controlled_power(
            qc=qc,
            control=control,
            work_qubits=WORK_QUBITS,
            power=power,
        )

    # Inverse QFT.
    inverse_qft(
        qc,
        PHASE_QUBITS,
    )

    # Measurement.
    qc.measure(
        PHASE_QUBITS,
        range(NUM_PHASE_QUBITS),
    )

    return qc


def run_qpe(
    eigen_index: int = 1,
    shots: int = 1024,
) -> dict[str, int]:
    """
    Execute QPE using Qiskit Aer.
    """

    qc = build_qpe_circuit(
        eigen_index
    )

    simulator = AerSimulator()

    compiled = transpile(
        qc,
        simulator,
    )

    result = simulator.run(
        compiled,
        shots=shots,
    ).result()

    return result.get_counts()


def dominant_phase(
    counts: dict[str, int],
) -> float:
    """
    Convert the most frequent QPE measurement
    into a phase in [0,1).
    """

    bitstring = max(
        counts,
        key=counts.get,
    )

    integer = int(
        bitstring,
        2,
    )

    return integer / (
        2 ** NUM_PHASE_QUBITS
    )