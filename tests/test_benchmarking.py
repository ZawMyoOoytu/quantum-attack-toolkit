from qiskit import QuantumCircuit

from qattack.benchmarking.metrics import (
    CircuitMetrics,
    calculate_success_probability,
    circuit_metrics,
)


def test_success_probability():
    result = calculate_success_probability(
        success_count=750,
        total_shots=1000,
    )

    assert result == 0.75


def test_circuit_metrics():

    circuit = QuantumCircuit(2)

    circuit.h(0)
    circuit.cx(0, 1)

    compiled = circuit

    metrics = circuit_metrics(
        circuit=circuit,
        compiled_circuit=compiled,
        shots=1000,
        success=True,
        success_probability=1.0,
    )

    assert metrics.logical_qubits == 2
    assert metrics.circuit_depth == 2
    assert metrics.gate_count == 2
    assert metrics.shots == 1000
    assert metrics.success is True
    assert metrics.success_probability == 1.0


def test_metrics_summary():

    metrics = CircuitMetrics(
        logical_qubits=8,
        circuit_depth=100,
        gate_count=200,
        shots=1024,
        success=True,
        success_probability=1.0,
    )

    result = metrics.summary()

    assert result["logical_qubits"] == 8
    assert result["circuit_depth"] == 100
    assert result["gate_count"] == 200
    assert result["shots"] == 1024
    assert result["success"] is True