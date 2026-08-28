"""
Benchmark metrics for quantum algorithm experiments.

This module measures circuit/resource characteristics only.

It does not perform:
    - credential extraction
    - key extraction
    - authentication bypass
    - third-party system access
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class CircuitMetrics:
    """
    Standardized quantum circuit resource metrics.
    """

    logical_qubits: int
    circuit_depth: int
    gate_count: int
    shots: int

    success: bool = False
    success_probability: float = 0.0

    def summary(self) -> dict[str, Any]:
        """
        Return metrics as a dictionary.
        """

        return asdict(self)


def calculate_success_probability(
    success_count: int,
    total_shots: int,
) -> float:
    """
    Calculate empirical success probability.

    Parameters
    ----------
    success_count:
        Number of successful measurements.

    total_shots:
        Total number of measurements.
    """

    if total_shots <= 0:
        raise ValueError(
            "total_shots must be greater than zero."
        )

    if success_count < 0:
        raise ValueError(
            "success_count cannot be negative."
        )

    if success_count > total_shots:
        raise ValueError(
            "success_count cannot exceed total_shots."
        )

    return success_count / total_shots


def circuit_metrics(
    circuit,
    compiled_circuit,
    shots: int,
    success: bool = False,
    success_probability: float = 0.0,
) -> CircuitMetrics:
    """
    Extract standardized resource metrics from a circuit.
    """

    if shots <= 0:
        raise ValueError(
            "shots must be greater than zero."
        )

    if not 0.0 <= success_probability <= 1.0:
        raise ValueError(
            "success_probability must be between "
            "0 and 1."
        )

    return CircuitMetrics(
        logical_qubits=circuit.num_qubits,
        circuit_depth=compiled_circuit.depth(),
        gate_count=len(compiled_circuit.data),
        shots=shots,
        success=success,
        success_probability=success_probability,
    )