
"""
Quantum Risk Mapping for Website Cryptography.

Maps publicly observable cryptographic primitives into a
future-quantum security classification.

This is a threat-model classification layer.

It does NOT claim that the target is currently compromised.

Classification
--------------

post_quantum_candidate
    Primitive is designed as, or intended to be, post-quantum.

not_post_quantum_secure
    Primitive belongs to a classical public-key family that a
    sufficiently capable cryptographic quantum computer could
    attack using Shor-type algorithms.

unknown
    Primitive could not be confidently classified.

The output is intended for downstream AI-agent reasoning and
quantum experiment selection.
"""

from __future__ import annotations

from typing import Any


# =====================================================================
# ALGORITHM GROUPS
# =====================================================================


SHOR_FAMILIES = {
    "RSA": "integer_factorization",
    "DSA": "discrete_logarithm",
    "EC": "elliptic_curve_discrete_logarithm",
    "ECDSA": "elliptic_curve_discrete_logarithm",
    "ECDH": "elliptic_curve_discrete_logarithm",
    "Ed25519": "elliptic_curve_discrete_logarithm",
    "Ed448": "elliptic_curve_discrete_logarithm",
}


PQC_FAMILIES = {
    "ML-KEM": "module_lattice",
    "Kyber": "module_lattice",
    "ML-DSA": "module_lattice",
    "Dilithium": "module_lattice",
    "Falcon": "lattice",
    "SLH-DSA": "hash_based",
    "SPHINCS+": "hash_based",
}


# =====================================================================
# CORE MAPPER
# =====================================================================


def assess_quantum_risk(
    algorithm: str | None,
    key_size_bits: int | None = None,
    curve: str | None = None,
) -> dict[str, Any]:
    """
    Map a cryptographic primitive to a quantum-risk class.

    Parameters
    ----------
    algorithm:
        Normalized public-key algorithm name.

    key_size_bits:
        Public-key size when applicable.

    curve:
        Elliptic-curve name when applicable.

    Returns
    -------
    dict
        Machine-readable quantum-risk assessment.
    """

    if not algorithm:
        return {
            "status": "unknown",
            "quantum_algorithm": None,
            "risk_level": "unknown",
            "reason": (
                "No public-key algorithm was available "
                "from the inspected certificate."
            ),
            "migration_recommendation": (
                "Collect additional cryptographic metadata."
            ),
        }

    algorithm = algorithm.strip()

    if algorithm in SHOR_FAMILIES:
        family = SHOR_FAMILIES[
            algorithm
        ]

        # -------------------------------------------------------------
        # RSA-specific classification
        # -------------------------------------------------------------

        if algorithm == "RSA":
            if (
                key_size_bits is not None
                and key_size_bits < 2048
            ):
                risk_level = "high"
            else:
                risk_level = "high_future_risk"

            reason = (
                "RSA is a classical integer-factorization "
                "public-key primitive and is not designed "
                "to resist a sufficiently capable cryptographic "
                "quantum computer."
            )

        # -------------------------------------------------------------
        # EC / ECDSA / ECDH / EdDSA
        # -------------------------------------------------------------

        else:
            risk_level = "high_future_risk"

            reason = (
                f"{algorithm} belongs to the classical "
                "public-key family based on discrete-logarithm "
                "or elliptic-curve assumptions and is not "
                "post-quantum secure."
            )

        return {
            "status": "not_post_quantum_secure",

            "risk_level": risk_level,

            "quantum_algorithm": "Shor",

            "mathematical_family": family,

            "algorithm": algorithm,

            "key_size_bits": key_size_bits,

            "curve": curve,

            "reason": reason,

            "current_compromise": False,

            "migration_recommendation": (
                "Plan post-quantum cryptography migration "
                "and inventory other public-key usages."
            ),
        }

    if algorithm in PQC_FAMILIES:
        return {
            "status": "post_quantum_candidate",

            "risk_level": "lower_quantum_risk",

            "quantum_algorithm": None,

            "mathematical_family": PQC_FAMILIES[
                algorithm
            ],

            "algorithm": algorithm,

            "key_size_bits": key_size_bits,

            "curve": curve,

            "reason": (
                f"{algorithm} is classified in this "
                "assessment as a post-quantum cryptographic "
                "family."
            ),

            "current_compromise": False,

            "migration_recommendation": (
                "Validate implementation, parameter set, "
                "protocol support, and interoperability."
            ),
        }

    return {
        "status": "unknown",

        "risk_level": "unknown",

        "quantum_algorithm": None,

        "mathematical_family": None,

        "algorithm": algorithm,

        "key_size_bits": key_size_bits,

        "curve": curve,

        "reason": (
            "The observed public-key primitive is not "
            "recognized by the current classification table."
        ),

        "current_compromise": False,

        "migration_recommendation": (
            "Perform manual cryptographic review."
        ),
    }


# =====================================================================
# INVENTORY → RISK
# =====================================================================


def risk_from_inventory(
    inventory: dict[str, Any],
) -> dict[str, Any]:
    """
    Build quantum-risk information directly from a crypto inventory.
    """

    return assess_quantum_risk(
        algorithm=inventory.get(
            "algorithm"
        ),
        key_size_bits=inventory.get(
            "key_size_bits"
        ),
        curve=inventory.get(
            "curve"
        ),
    )


__all__ = [
    "SHOR_FAMILIES",
    "PQC_FAMILIES",
    "assess_quantum_risk",
    "risk_from_inventory",
]

