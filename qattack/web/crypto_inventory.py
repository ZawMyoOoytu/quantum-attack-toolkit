
"""
Cryptographic Inventory for Website Security Assessment.

Converts publicly observable TLS certificate information into a
normalized cryptographic inventory.

This module does not perform exploitation.

It answers:

    What public-key primitive is visible in the TLS certificate?

Examples:

    RSA 2048
    RSA 3072
    EC P-256
    Ed25519
    Ed448

The output is intentionally machine-readable so it can be consumed
by a later quantum-risk mapper or experiment-selection layer.
"""

from __future__ import annotations

from typing import Any


# =====================================================================
# QUANTUM CLASSIFICATION CONSTANTS
# =====================================================================

SHOR_VULNERABLE_ALGORITHMS = {
    "RSA",
    "EC",
    "ECDSA",
    "ECDH",
    "DSA",
    "Ed25519",
    "Ed448",
}


POST_QUANTUM_ALGORITHMS = {
    "ML-KEM",
    "ML-DSA",
    "SLH-DSA",
    "Kyber",
    "Dilithium",
    "Falcon",
    "SPHINCS+",
}


# =====================================================================
# NORMALIZATION
# =====================================================================


def normalize_algorithm(
    algorithm: str | None,
) -> str | None:
    """
    Normalize common public-key algorithm names.
    """

    if algorithm is None:
        return None

    value = algorithm.strip()

    aliases = {
        "RSA": "RSA",
        "rsa": "RSA",

        "EC": "EC",
        "EllipticCurve": "EC",
        "ELLIPTIC CURVE": "EC",

        "ECDSA": "ECDSA",
        "ECDH": "ECDH",

        "DSA": "DSA",

        "Ed25519": "Ed25519",
        "ed25519": "Ed25519",

        "Ed448": "Ed448",
        "ed448": "Ed448",

        "ML-KEM": "ML-KEM",
        "ML-DSA": "ML-DSA",
        "SLH-DSA": "SLH-DSA",
    }

    return aliases.get(
        value,
        value,
    )


# =====================================================================
# INVENTORY BUILDER
# =====================================================================


def build_crypto_inventory(
    certificate: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Build a normalized cryptographic inventory from certificate data.

    Parameters
    ----------
    certificate:
        Certificate dictionary produced by the website assessment
        TLS inspection.

    Returns
    -------
    dict
        Normalized cryptographic inventory.
    """

    certificate = certificate or {}

    public_key = certificate.get(
        "public_key"
    )

    if not public_key:
        return {
            "available": False,
            "source": "tls_certificate",
            "algorithm": None,
            "key_size_bits": None,
            "curve": None,
            "signature_algorithm": certificate.get(
                "signature_algorithm"
            ),
            "quantum_relevance": "unknown",
        }

    algorithm = normalize_algorithm(
        public_key.get("algorithm")
    )

    key_size_bits = public_key.get(
        "key_size_bits"
    )

    curve = public_key.get(
        "curve"
    )

    if algorithm in POST_QUANTUM_ALGORITHMS:
        quantum_relevance = (
            "post_quantum_candidate"
        )

    elif algorithm in SHOR_VULNERABLE_ALGORITHMS:
        quantum_relevance = (
            "not_post_quantum_secure"
        )

    else:
        quantum_relevance = (
            "unknown"
        )

    return {
        "available": True,
        "source": "tls_certificate",

        "algorithm": algorithm,

        "key_size_bits": key_size_bits,

        "curve": curve,

        "signature_algorithm": certificate.get(
            "signature_algorithm"
        ),

        "quantum_relevance": quantum_relevance,
    }


# =====================================================================
# EXPORTS
# =====================================================================


__all__ = [
    "SHOR_VULNERABLE_ALGORITHMS",
    "POST_QUANTUM_ALGORITHMS",
    "normalize_algorithm",
    "build_crypto_inventory",
]

