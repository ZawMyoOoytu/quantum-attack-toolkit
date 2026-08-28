
"""
IBM Quantum Runtime adapter.

This module provides a thin adapter around an IBM Quantum Runtime
backend. It converts real-QPU measurement results into the same
counts-based representation used by the local simulator.

The adapter deliberately keeps authentication and backend execution
separate from the security-analysis layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class QPUResult:
    """Normalized result returned by a real quantum backend."""

    backend_name: str
    shots: int
    counts: dict[str, int]
    job_id: str | None = None

    def summary(self) -> dict[str, Any]:
        """Return a JSON-compatible summary."""

        return {
            "backend": self.backend_name,
            "shots": self.shots,
            "counts": dict(self.counts),
            "job_id": self.job_id,
        }


class IBMQuantumAdapter:
    """
    Thin IBM Quantum Runtime adapter.

    The class does not implement an attack algorithm. It executes an
    already-built Qiskit circuit and normalizes the resulting counts.
    """

    def __init__(
        self,
        backend_name: str,
        *,
        channel: str = "ibm_quantum_platform",
    ) -> None:
        self.backend_name = backend_name
        self.channel = channel

    def _load_runtime(self):
        """Import IBM Runtime lazily."""

        try:
            from qiskit_ibm_runtime import (
                QiskitRuntimeService,
                SamplerV2,
            )
        except ImportError as exc:
            raise RuntimeError(
                "qiskit-ibm-runtime is required for real-QPU execution."
            ) from exc

        return QiskitRuntimeService, SamplerV2

    def connect(
        self,
        *,
        token: str | None = None,
    ):
        """
        Connect to IBM Quantum.

        If token is omitted, the adapter expects an existing IBM
        Quantum saved account.
        """

        QiskitRuntimeService, _ = self._load_runtime()

        if token:
            return QiskitRuntimeService(
                channel=self.channel,
                token=token,
            )

        return QiskitRuntimeService()

    @staticmethod
    def _extract_counts(
        pub_result: Any,
    ) -> dict[str, int]:
        """
        Extract counts from a SamplerV2 PUB result.

        Supports the common Qiskit Runtime measurement-container
        representation while keeping the adapter defensive.
        """

        data = getattr(pub_result, "data", None)

        if data is None:
            raise RuntimeError(
                "QPU result does not contain a data container."
            )

        # Common case: classical register named "c".
        register = getattr(data, "c", None)

        if register is None:
            # Fall back to the first data attribute that provides
            # get_counts().
            for name in dir(data):
                if name.startswith("_"):
                    continue

                candidate = getattr(data, name, None)

                if hasattr(candidate, "get_counts"):
                    register = candidate
                    break

        if register is None or not hasattr(register, "get_counts"):
            raise RuntimeError(
                "Unable to locate measurement counts in QPU result."
            )

        raw_counts = register.get_counts()

        return {
            str(state): int(count)
            for state, count in raw_counts.items()
        }

    def run(
        self,
        circuit: Any,
        *,
        shots: int = 1024,
        token: str | None = None,
    ) -> QPUResult:
        """
        Execute a Qiskit circuit on the configured IBM backend.

        Parameters
        ----------
        circuit:
            Qiskit QuantumCircuit containing measurements.

        shots:
            Number of measurement shots.

        token:
            Optional IBM Quantum API token. Prefer a saved account
            rather than passing tokens directly in source code.
        """

        if shots <= 0:
            raise ValueError("shots must be positive.")

        service = self.connect(token=token)

        backend = service.backend(self.backend_name)

        _, SamplerV2 = self._load_runtime()

        sampler = SamplerV2(mode=backend)

        job = sampler.run(
            [circuit],
            shots=shots,
        )

        result = job.result()

        if not result:
            raise RuntimeError("IBM Quantum returned an empty result.")

        pub_result = result[0]

        counts = self._extract_counts(pub_result)

        observed_shots = sum(counts.values())

        return QPUResult(
            backend_name=self.backend_name,
            shots=observed_shots,
            counts=counts,
            job_id=getattr(job, "job_id", lambda: None)(),
        )


__all__ = [
    "QPUResult",
    "IBMQuantumAdapter",
]

