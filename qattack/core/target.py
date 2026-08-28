from dataclasses import dataclass


@dataclass
class Target:
    """
    Represents an authorized research/benchmark target.

    The target contains metadata only.
    It does not contain credentials, private keys,
    or mechanisms for extracting secrets.
    """

    target_type: str
    name: str
    size: int

    def describe(self) -> str:
        return (
            f"Target(type={self.target_type}, "
            f"name={self.name}, size={self.size})"
        )