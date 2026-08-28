from abc import ABC, abstractmethod

from qattack.core.result import AttackResult
from qattack.core.target import Target


class QuantumAttack(ABC):
    """
    Base interface for quantum attack simulations
    and security assessments.
    """

    name: str = "unknown"
    target_type: str = "unknown"

    @abstractmethod
    def validate(self, target: Target) -> None:
        """Validate whether the attack supports the target."""
        raise NotImplementedError

    @abstractmethod
    def run(self, target: Target) -> AttackResult:
        """Execute the authorized research experiment."""
        raise NotImplementedError