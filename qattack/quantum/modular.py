"""
Toy modular arithmetic benchmark for N=15.

This module provides a reversible quantum permutation for

    |y> -> |2y mod 15>

on a 4-qubit work register.

It is designed for:

    - quantum-algorithm research
    - Shor's algorithm education
    - QPE/order-finding experiments
    - local Qiskit/Aer benchmarking
    - automated unit testing

IMPORTANT
---------
This is an N=15 toy benchmark.

It does not access:

    - real RSA keys
    - credentials
    - passwords
    - private keys
    - third-party systems

The implementation is intentionally limited to the
small N=15 research problem.
"""

from __future__ import annotations

import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate


# ---------------------------------------------------------------------
# Benchmark configuration
# ---------------------------------------------------------------------

MODULUS = 15
MULTIPLIER = 2
NUM_WORK_QUBITS = 4

# For a = 2 modulo N = 15,

#     2^4 mod 15 = 1

# therefore the multiplicative order is

#     r = 4

MULTIPLICATIVE_ORDER = 4


# ---------------------------------------------------------------------
# Classical reference implementation
# ---------------------------------------------------------------------

def classical_modular_map(
    value: int,
) -> int:
    """
    Compute the classical reference permutation

        f(y) = 2y mod 15

    for the 4-qubit computational basis.

    Valid inputs are 0..15.

    The state |15> is preserved because 15 is outside
    the modular domain {0,...,14} and is used as the
    unused basis state in this toy permutation.
    """

    if not isinstance(
        value,
        int,
    ):
        raise TypeError(
            "value must be an integer."
        )

    if not 0 <= value < 16:
        raise ValueError(
            "value must be in the range 0..15."
        )

    if value == 15:
        return 15

    return (
        MULTIPLIER * value
    ) % MODULUS


# ---------------------------------------------------------------------
# Public reference mapping
# ---------------------------------------------------------------------

def expected_mapping(
    value: int,
) -> int:
    """
    Public reference mapping used by tests.
    """

    return classical_modular_map(
        value
    )


# ---------------------------------------------------------------------
# Permutation matrix
# ---------------------------------------------------------------------

def modular_permutation_matrix() -> np.ndarray:
    """
    Construct the 16 x 16 permutation matrix implementing

        |y> -> |2y mod 15>

    on four work qubits.

    Mapping:

        0  -> 0
        1  -> 2
        2  -> 4
        3  -> 6
        4  -> 8
        5  -> 10
        6  -> 12
        7  -> 14
        8  -> 1
        9  -> 3
        10 -> 5
        11 -> 7
        12 -> 9
        13 -> 11
        14 -> 13
        15 -> 15

    The mapping is a permutation and therefore produces
    a unitary matrix.
    """

    dimension = (
        2 ** NUM_WORK_QUBITS
    )

    matrix = np.zeros(
        (
            dimension,
            dimension,
        ),
        dtype=complex,
    )

    for value in range(
        dimension
    ):

        mapped = classical_modular_map(
            value
        )

        matrix[
            mapped,
            value,
        ] = 1.0

    return matrix


# ---------------------------------------------------------------------
# Unitary validation
# ---------------------------------------------------------------------

def is_unitary(
    matrix: np.ndarray,
    atol: float = 1e-10,
) -> bool:
    """
    Check whether a matrix is unitary.

    A matrix U is unitary when

        U†U = I
    """

    matrix = np.asarray(
        matrix,
        dtype=complex,
    )

    if matrix.ndim != 2:
        return False

    if matrix.shape[0] != matrix.shape[1]:
        return False

    identity = np.eye(
        matrix.shape[0],
        dtype=complex,
    )

    return np.allclose(
        matrix.conj().T @ matrix,
        identity,
        atol=atol,
    )


# ---------------------------------------------------------------------
# Basic controlled modular multiplication
# ---------------------------------------------------------------------

def modular_multiplication_by_2_mod_15(
    qc: QuantumCircuit,
    control: int,
    work_qubits: list[int],
) -> QuantumCircuit:
    """
    Append the controlled modular multiplication

        |y> -> |2y mod 15>

    to an existing quantum circuit.

    The operation is activated when the control qubit
    is |1>.
    """

    if not isinstance(
        qc,
        QuantumCircuit,
    ):
        raise TypeError(
            "qc must be a Qiskit QuantumCircuit."
        )

    if len(work_qubits) != NUM_WORK_QUBITS:
        raise ValueError(
            "N=15 benchmark requires exactly "
            "four work qubits."
        )

    if control in work_qubits:
        raise ValueError(
            "Control qubit must be different "
            "from work qubits."
        )

    if len(set(work_qubits)) != len(work_qubits):
        raise ValueError(
            "work_qubits must contain unique indices."
        )

    all_indices = [
        control,
        *work_qubits,
    ]

    if any(
        index < 0
        or index >= qc.num_qubits
        for index in all_indices
    ):
        raise ValueError(
            "Qubit index is outside the circuit."
        )

    matrix = modular_permutation_matrix()

    if not is_unitary(matrix):
        raise ValueError(
            "Modular permutation matrix "
            "must be unitary."
        )

    base_gate = UnitaryGate(
        matrix,
        label="2y mod 15",
    )

    controlled_gate = base_gate.control(
        num_ctrl_qubits=1,
        label="C(2y mod 15)",
    )

    qc.append(
        controlled_gate,
        [
            control,
            *work_qubits,
        ],
    )

    return qc


# ---------------------------------------------------------------------
# Controlled modular exponentiation
# ---------------------------------------------------------------------

def controlled_modular_power_2(
    qc: QuantumCircuit,
    control: int,
    work_qubits: list[int],
    exponent_power: int | None = None,
    power: int | None = None,
) -> QuantumCircuit:
    """
    Append the controlled modular power required by QPE.

    The base modular operator is

        U|y> = |2y mod 15>.

    QPE requires

        controlled-U^(2^j)

    for counting-register index j.

    Therefore:

        exponent_power = 0
            -> U^(2^0) = U

        exponent_power = 1
            -> U^(2^1) = U^2

        exponent_power = 2
            -> U^(2^2) = U^4 = I

        exponent_power = 3
            -> U^(2^3) = U^8 = I

    because the order of 2 modulo 15 is 4.

    The parameter name ``exponent_power`` therefore means
    the QPE exponent index j, NOT the direct exponent k.

    ``power`` is retained as a backward-compatible alias.
    """

    # -------------------------------------------------------------
    # Resolve compatibility aliases
    # -------------------------------------------------------------

    if (
        exponent_power is not None
        and power is not None
    ):

        if exponent_power != power:
            raise ValueError(
                "exponent_power and power specify "
                "different values."
            )

    if exponent_power is None:

        exponent_power = power

    if exponent_power is None:

        exponent_power = 0

    # -------------------------------------------------------------
    # Validate exponent index
    # -------------------------------------------------------------

    if not isinstance(
        exponent_power,
        int,
    ):
        raise TypeError(
            "exponent_power must be an integer."
        )

    if exponent_power < 0:
        raise ValueError(
            "exponent_power must be non-negative."
        )

    # -------------------------------------------------------------
    # Validate work register
    # -------------------------------------------------------------

    if len(work_qubits) != NUM_WORK_QUBITS:
        raise ValueError(
            "N=15 benchmark requires exactly "
            "four work qubits."
        )

    if control in work_qubits:
        raise ValueError(
            "Control qubit must be different "
            "from work qubits."
        )

    if len(set(work_qubits)) != len(work_qubits):
        raise ValueError(
            "work_qubits must contain unique indices."
        )

    all_indices = [
        control,
        *work_qubits,
    ]

    if any(
        index < 0
        or index >= qc.num_qubits
        for index in all_indices
    ):
        raise ValueError(
            "Qubit index is outside the circuit."
        )

    # -------------------------------------------------------------
    # QPE requires U^(2^j)
    # -------------------------------------------------------------

    qpe_exponent = (
        2 ** exponent_power
    )

    # -------------------------------------------------------------
    # Since U has order 4:
    #
    #     U^k = U^(k mod 4)
    #
    # Therefore the actual number of U applications
    # can be reduced modulo 4.
    # -------------------------------------------------------------

    effective_power = (
        qpe_exponent
        % MULTIPLICATIVE_ORDER
    )

    # -------------------------------------------------------------
    # U^0 = I
    #
    # For j >= 2 in this N=15 benchmark:
    #
    #     U^4 = I
    #     U^8 = I
    #
    # so nothing needs to be appended.
    # -------------------------------------------------------------

    if effective_power == 0:

        return qc

    # -------------------------------------------------------------
    # Append controlled-U repeatedly.
    #
    # effective_power:
    #
    #     1 -> U
    #     2 -> U^2
    #     3 -> U^3
    # -------------------------------------------------------------

    for _ in range(
        effective_power
    ):

        modular_multiplication_by_2_mod_15(
            qc=qc,
            control=control,
            work_qubits=work_qubits,
        )

    return qc


# ---------------------------------------------------------------------
# Direct-power compatibility helper
# ---------------------------------------------------------------------

def controlled_modular_power_direct(
    qc: QuantumCircuit,
    control: int,
    work_qubits: list[int],
    exponent: int,
) -> QuantumCircuit:
    """
    Apply controlled-U^exponent directly.

    This helper is intentionally separate from
    ``controlled_modular_power_2``.

    ``controlled_modular_power_2`` is QPE-oriented and
    interprets its exponent as the QPE index j.

    This function interprets ``exponent`` literally.
    """

    if not isinstance(
        exponent,
        int,
    ):
        raise TypeError(
            "exponent must be an integer."
        )

    if exponent < 0:
        raise ValueError(
            "exponent must be non-negative."
        )

    effective_power = (
        exponent
        % MULTIPLICATIVE_ORDER
    )

    if effective_power == 0:
        return qc

    for _ in range(
        effective_power
    ):

        modular_multiplication_by_2_mod_15(
            qc=qc,
            control=control,
            work_qubits=work_qubits,
        )

    return qc


# ---------------------------------------------------------------------
# Convenience circuit builder
# ---------------------------------------------------------------------

def build_controlled_modular_circuit(
    exponent_power: int,
) -> QuantumCircuit:
    """
    Build a standalone QPE-style controlled modular-power circuit.

    Layout:

        q0      : control
        q1..q4  : work register

    Total qubits = 5.

    ``exponent_power`` follows the QPE convention:

        0 -> controlled-U
        1 -> controlled-U^2
        2 -> controlled-U^4
        3 -> controlled-U^8
    """

    circuit = QuantumCircuit(
        1 + NUM_WORK_QUBITS
    )

    controlled_modular_power_2(
        qc=circuit,
        control=0,
        work_qubits=[
            1,
            2,
            3,
            4,
        ],
        exponent_power=exponent_power,
    )

    return circuit


# ---------------------------------------------------------------------
# Classical periodicity helper
# ---------------------------------------------------------------------

def modular_power_map(
    exponent: int,
    value: int,
) -> int:
    """
    Classical reference for

        2^exponent * value mod 15.

    This function interprets ``exponent`` literally.

    Examples:

        modular_power_map(0, 1) -> 1
        modular_power_map(1, 1) -> 2
        modular_power_map(2, 1) -> 4
        modular_power_map(3, 1) -> 8
        modular_power_map(4, 1) -> 1
    """

    if not isinstance(
        exponent,
        int,
    ):
        raise TypeError(
            "exponent must be an integer."
        )

    if exponent < 0:
        raise ValueError(
            "exponent must be non-negative."
        )

    if not isinstance(
        value,
        int,
    ):
        raise TypeError(
            "value must be an integer."
        )

    if not 0 <= value < 16:
        raise ValueError(
            "value must be in the range 0..15."
        )

    if value == 15:
        return 15

    multiplier = pow(
        MULTIPLIER,
        exponent,
        MODULUS,
    )

    return (
        multiplier * value
    ) % MODULUS