from qattack.core.attack import QuantumAttack


class AttackRegistry:
    """
    Central registry for quantum attack modules.
    """

    def __init__(self) -> None:
        self._attacks: dict[str, QuantumAttack] = {}

    def register(self, attack: QuantumAttack) -> None:
        if attack.name in self._attacks:
            raise ValueError(
                f"Attack '{attack.name}' is already registered."
            )

        self._attacks[attack.name] = attack

    def get(self, name: str) -> QuantumAttack:
        try:
            return self._attacks[name]
        except KeyError:
            available = ", ".join(self._attacks.keys())
            raise ValueError(
                f"Unknown attack '{name}'. "
                f"Available attacks: {available}"
            )

    def list_attacks(self) -> list[str]:
        return sorted(self._attacks.keys())