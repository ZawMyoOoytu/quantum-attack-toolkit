from dataclasses import dataclass, field
from typing import Any


@dataclass
class AttackResult:
    """
    Standard result returned by every quantum attack module.
    """

    attack_name: str
    target_type: str
    success: bool

    logical_qubits: int = 0
    circuit_depth: int = 0
    gate_count: int = 0
    shots: int = 0

    success_probability: float = 0.0

    metrics: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "attack": self.attack_name,
            "target": self.target_type,
            "success": self.success,
            "logical_qubits": self.logical_qubits,
            "circuit_depth": self.circuit_depth,
            "gate_count": self.gate_count,
            "shots": self.shots,
            "success_probability": self.success_probability,
            "metrics": self.metrics,
            "notes": self.notes,
        }