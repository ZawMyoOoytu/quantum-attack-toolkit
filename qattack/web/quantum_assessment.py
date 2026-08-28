
"""
Website-to-Quantum Security Assessment.

Bridges passive website cryptographic discovery with the existing
QuantumSecurityAssessment research engine.

Important design principle
--------------------------

A real website certificate key such as RSA-2048 is NOT passed
directly into the toy quantum factorization benchmark as N=2048.

Instead:

    REAL WEBSITE
        |
        v
    CRYPTO DISCOVERY
        |
        v
    QUANTUM RISK CLASSIFICATION
        |
        +--> REAL-WORLD POST-QUANTUM FINDING
        |
        +--> OPTIONAL TOY QUANTUM BENCHMARK
                |
                v
        EXISTING QUANTUM ENGINE

This keeps empirical website evidence separate from toy
quantum-computing demonstrations.
"""

from __future__ import annotations

from typing import Any

from qattack.assessment import QuantumSecurityAssessment
from qattack.core.target import Target


# =====================================================================
# SUPPORTED MAPPINGS
# =====================================================================

QUANTUM_BENCHMARK_BY_ALGORITHM = {
    "RSA": {
        "benchmark": "quantum-period-finding-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "integer factorization"
        ),
    },
    "EC": {
        "benchmark": "discrete-logarithm-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "elliptic-curve discrete logarithm"
        ),
    },
    "ECDSA": {
        "benchmark": "discrete-logarithm-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "elliptic-curve discrete logarithm"
        ),
    },
    "ECDH": {
        "benchmark": "discrete-logarithm-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "elliptic-curve discrete logarithm"
        ),
    },
    "DSA": {
        "benchmark": "discrete-logarithm-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "discrete logarithm"
        ),
    },
    "Ed25519": {
        "benchmark": "discrete-logarithm-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "elliptic-curve discrete logarithm"
        ),
    },
    "Ed448": {
        "benchmark": "discrete-logarithm-benchmark",
        "quantum_algorithm": "Shor",
        "mathematical_problem": (
            "elliptic-curve discrete logarithm"
        ),
    },
}


# =====================================================================
# SAFE BENCHMARK DEFAULT
# =====================================================================

DEFAULT_TOY_BENCHMARK_SIZE = 15

DEFAULT_TOY_SHOTS = 128

DEFAULT_TOY_NOISE_PROBABILITY = 0.10


# =====================================================================
# HELPERS
# =====================================================================


def _json_safe(value: Any) -> Any:
    """Convert common Python objects into JSON-safe structures."""

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(value, set):
        return [
            _json_safe(item)
            for item in sorted(
                value,
                key=str,
            )
        ]

    if hasattr(value, "item"):
        try:
            return _json_safe(
                value.item()
            )
        except Exception:
            pass

    return value


# =====================================================================
# MAP CRYPTO INVENTORY
# =====================================================================


def map_crypto_to_quantum(
    crypto_inventory: dict[str, Any],
) -> dict[str, Any]:
    """
    Map detected public-key cryptography to a quantum threat model.

    This function does not perform an attack against the website.
    """

    algorithm = crypto_inventory.get(
        "algorithm"
    )

    key_size_bits = crypto_inventory.get(
        "key_size_bits"
    )

    curve = crypto_inventory.get(
        "curve"
    )

    if not algorithm:
        return {
            "status": "unknown",
            "algorithm": None,
            "key_size_bits": key_size_bits,
            "curve": curve,
            "quantum_algorithm": None,
            "benchmark": None,
            "real_world_break_demonstrated": False,
            "recommendation": (
                "No supported public-key primitive was "
                "identified from the inspected certificate."
            ),
        }

    mapping = (
        QUANTUM_BENCHMARK_BY_ALGORITHM.get(
            algorithm
        )
    )

    if mapping is None:
        return {
            "status": "unknown",
            "algorithm": algorithm,
            "key_size_bits": key_size_bits,
            "curve": curve,
            "quantum_algorithm": None,
            "benchmark": None,
            "real_world_break_demonstrated": False,
            "recommendation": (
                "Perform additional cryptographic inventory "
                "before selecting a quantum benchmark."
            ),
        }

    return {
        "status": "quantum_vulnerable_class",
        "algorithm": algorithm,
        "key_size_bits": key_size_bits,
        "curve": curve,
        "quantum_algorithm": mapping[
            "quantum_algorithm"
        ],
        "benchmark": mapping[
            "benchmark"
        ],
        "mathematical_problem": mapping[
            "mathematical_problem"
        ],
        "real_world_break_demonstrated": False,
        "recommendation": (
            "Review post-quantum migration requirements "
            "for this public-key primitive."
        ),
    }


# =====================================================================
# OPTIONAL TOY BENCHMARK
# =====================================================================


def run_toy_quantum_benchmark(
    *,
    target_type: str,
    shots: int = DEFAULT_TOY_SHOTS,
    noise_probability: float = (
        DEFAULT_TOY_NOISE_PROBABILITY
    ),
    toy_size: int = DEFAULT_TOY_BENCHMARK_SIZE,
) -> dict[str, Any]:
    """
    Run the existing quantum research benchmark on a toy target.

    The toy target is intentionally independent of the real website
    key size.
    """

    target = Target(
        target_type=target_type,
        name=f"{target_type.upper()}-Toy-{toy_size}",
        size=toy_size,
    )

    assessor = (
        QuantumSecurityAssessment()
    )

    result = assessor.run(
        target=target,
        shots=shots,
        noise_probability=noise_probability,
    )

    return _json_safe(
        result.summary()
    )


# =====================================================================
# END-TO-END WEBSITE QUANTUM ASSESSMENT
# =====================================================================


def build_website_quantum_assessment(
    *,
    crypto_inventory: dict[str, Any],
    quantum_risk: dict[str, Any],
    run_benchmark: bool = True,
    shots: int = DEFAULT_TOY_SHOTS,
    noise_probability: float = (
        DEFAULT_TOY_NOISE_PROBABILITY
    ),
) -> dict[str, Any]:
    """
    Combine real website crypto evidence with quantum-risk mapping.

    Optionally runs a separate toy quantum benchmark.

    The benchmark result is clearly labeled as a research
    demonstration and is never presented as a break of the
    real website certificate.
    """

    mapping = map_crypto_to_quantum(
        crypto_inventory
    )

    benchmark_result = None

    if (
        run_benchmark
        and mapping["status"]
        == "quantum_vulnerable_class"
    ):
        algorithm = mapping.get(
            "algorithm"
        )

        benchmark_target_type = (
            "rsa"
            if algorithm == "RSA"
            else None
        )

        if benchmark_target_type is not None:
            benchmark_result = (
                run_toy_quantum_benchmark(
                    target_type=benchmark_target_type,
                    shots=shots,
                    noise_probability=(
                        noise_probability
                    ),
                )
            )

    return {
        "status": "completed",

        "crypto_inventory": _json_safe(
            crypto_inventory
        ),

        "quantum_risk": _json_safe(
            quantum_risk
        ),

        "quantum_mapping": mapping,

        "toy_benchmark": {
            "executed": (
                benchmark_result is not None
            ),
            "scope": (
                "research-toy-benchmark"
            ),
            "real_world_break_demonstrated": False,
            "result": benchmark_result,
        },

        "interpretation": {
            "real_world_target_assessed": True,
            "real_world_cryptographic_break": False,
            "quantum_migration_review": (
                mapping["status"]
                == "quantum_vulnerable_class"
            ),
        },
    }


__all__ = [
    "QUANTUM_BENCHMARK_BY_ALGORITHM",
    "DEFAULT_TOY_BENCHMARK_SIZE",
    "DEFAULT_TOY_SHOTS",
    "DEFAULT_TOY_NOISE_PROBABILITY",
    "map_crypto_to_quantum",
    "run_toy_quantum_benchmark",
    "build_website_quantum_assessment",
]

