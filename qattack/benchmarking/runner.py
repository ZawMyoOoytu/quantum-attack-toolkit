from dataclasses import dataclass
from time import perf_counter
from typing import Any


from qattack.attacks.shor import ShorAttack
from qattack.core.target import Target


@dataclass
class BenchmarkRun:
    """
    Standardized result for a quantum attack benchmark.

    This object stores execution-level information together
    with the scientific metrics produced by the benchmark.
    """

    attack: str
    target: str
    target_type: str
    size: int

    success: bool

    logical_qubits: int
    circuit_depth: int
    gate_count: int
    shots: int

    success_probability: float

    elapsed_seconds: float

    metrics: dict[str, Any]
    notes: list[str]

    def summary(self) -> dict[str, Any]:
        """
        Return the benchmark result as a serializable dictionary.
        """

        return {
            "attack": self.attack,
            "target": self.target,
            "target_type": self.target_type,
            "size": self.size,
            "success": self.success,
            "logical_qubits": self.logical_qubits,
            "circuit_depth": self.circuit_depth,
            "gate_count": self.gate_count,
            "shots": self.shots,
            "success_probability": self.success_probability,
            "elapsed_seconds": self.elapsed_seconds,
            "metrics": self.metrics,
            "notes": self.notes,
        }


class BenchmarkRunner:
    """
    Execute standardized quantum attack benchmarks.

    Current supported benchmark:

        - Shor N=15

    The runner controls benchmark-level parameters such as
    measurement shots and repeated trials.
    """

    def __init__(
        self,
        shots: int = 1024,
    ) -> None:

        if not isinstance(shots, int):
            raise TypeError(
                "shots must be an integer."
            )

        if shots <= 0:
            raise ValueError(
                "shots must be greater than zero."
            )

        self.shots = shots

    # =========================================================
    # Shor N=15
    # =========================================================

    def run_shor_n15(
        self,
    ) -> BenchmarkRun:
        """
        Execute the local N=15 Shor research benchmark.
        """

        target = Target(
            target_type="rsa",
            name="RSA-Toy-15",
            size=15,
        )

        attack = ShorAttack()

        start = perf_counter()

        result = attack.run(
            target,
            shots=self.shots,
        )

        elapsed = (
            perf_counter()
            - start
        )

        return BenchmarkRun(
            attack=result.attack_name,
            target=target.name,
            target_type=target.target_type,
            size=target.size,

            success=result.success,

            logical_qubits=result.logical_qubits,
            circuit_depth=result.circuit_depth,
            gate_count=result.gate_count,

            shots=result.shots,

            success_probability=(
                result.success_probability
            ),

            elapsed_seconds=elapsed,

            metrics=result.metrics,
            notes=result.notes,
        )

    # =========================================================
    # Generic dispatcher
    # =========================================================

    def run(
        self,
        attack_name: str,
    ) -> BenchmarkRun:
        """
        Dispatch a supported benchmark.

        Supported aliases:

            shor
            shor-n15
            shor_n15
        """

        normalized = (
            attack_name
            .lower()
            .strip()
        )

        if normalized in {
            "shor",
            "shor-n15",
            "shor_n15",
        }:

            return self.run_shor_n15()

        raise ValueError(
            f"Unsupported benchmark: {attack_name}"
        )

    # =========================================================
    # Repeated benchmark execution
    # =========================================================

    def run_repeated(
        self,
        attack_name: str,
        trials: int = 3,
    ) -> list[BenchmarkRun]:
        """
        Execute the same benchmark multiple times.

        Parameters
        ----------
        attack_name:
            Benchmark identifier, for example:

                "shor"
                "shor-n15"
                "shor_n15"

        trials:
            Number of independent benchmark executions.

        Returns
        -------
        list[BenchmarkRun]
            One BenchmarkRun object per trial.

        Notes
        -----
        Each trial executes the benchmark independently.
        The configured shot count remains unchanged across
        all trials.
        """

        if not isinstance(trials, int):
            raise TypeError(
                "trials must be an integer."
            )

        if trials <= 0:
            raise ValueError(
                "trials must be greater than zero."
            )

        results: list[BenchmarkRun] = []

        for _ in range(trials):

            result = self.run(
                attack_name
            )

            results.append(
                result
            )

        return results