"""
One-Click Website Quantum Security Assessment.

This module orchestrates the existing website and quantum-security
components into one end-to-end assessment pipeline.

Pipeline
--------
1. Validate authorized target.
2. Inspect website.
3. Inspect TLS and certificate.
4. Build cryptographic inventory.
5. Map cryptography to quantum risk.
6. Optionally run a separate toy quantum benchmark.
7. Produce a combined machine-readable assessment.

Important
---------
The real website is NEVER passed into the toy factorization
benchmark as its real key size.

For example:

    Real website certificate:
        RSA-2048

    Quantum benchmark:
        RSA-Toy-15

The benchmark demonstrates the relevant mathematical primitive;
it does not claim to break the real website.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from qattack.web.site_assessment import (
    WebsiteAssessment,
    assess_website,
)

from qattack.web.quantum_assessment import (
    build_website_quantum_assessment,
)


# =====================================================================
# VERSION
# =====================================================================

ASSESSMENT_VERSION = "0.3.0"


# =====================================================================
# HELPERS
# =====================================================================


def _utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(
        timezone.utc
    ).isoformat()


def _security_grade(
    assessment: WebsiteAssessment,
) -> str:
    """
    Produce a simple website hardening grade.

    This is a heuristic summary, not a standards certification.
    """

    if not assessment.https:
        return "critical"

    missing_count = (
        assessment.security_headers
        .get("_summary", {})
        .get("missing_count", 0)
    )

    if missing_count >= 4:
        return "needs_improvement"

    if missing_count >= 2:
        return "moderate"

    return "good"


def _build_recommendations(
    assessment: WebsiteAssessment,
) -> list[dict[str, Any]]:
    """
    Convert observed findings into prioritized recommendations.
    """

    recommendations: list[dict[str, Any]] = []

    missing_headers = (
        assessment.security_headers
        .get("_summary", {})
        .get("missing", [])
    )

    priority_map = {
        "CSP": "high",
        "X-Content-Type-Options": "medium",
        "X-Frame-Options": "medium",
        "Referrer-Policy": "medium",
        "Permissions-Policy": "low",
    }

    for header in missing_headers:
        recommendations.append(
            {
                "category": "web_hardening",
                "priority": priority_map.get(
                    header,
                    "medium",
                ),
                "finding": (
                    f"{header} is not observed "
                    "on the inspected response."
                ),
                "action": (
                    f"Review and configure {header} "
                    "according to application requirements."
                ),
            }
        )

    certificate = (
        assessment.tls
        .get("certificate", {})
    )

    public_key = (
        certificate.get("public_key")
    )

    if public_key:
        algorithm = public_key.get(
            "algorithm"
        )

        key_size = public_key.get(
            "key_size_bits"
        )

        if public_key.get(
            "quantum_vulnerable_class"
        ) is True:

            key_text = algorithm or "classical public-key"

            if key_size:
                key_text = (
                    f"{key_text}-{key_size}"
                )

            recommendations.append(
                {
                    "category": "quantum_readiness",
                    "priority": "high_future_risk",
                    "finding": (
                        f"Observed certificate public key "
                        f"{key_text} belongs to a classical "
                        "public-key cryptographic class that "
                        "is not post-quantum secure."
                    ),
                    "action": (
                        "Inventory all public-key cryptography "
                        "and evaluate a post-quantum migration "
                        "or hybrid transition strategy."
                    ),
                }
            )

    days_until_expiry = (
        certificate.get(
            "days_until_expiry"
        )
    )

    if days_until_expiry is not None:

        if days_until_expiry < 0:
            recommendations.append(
                {
                    "category": "certificate",
                    "priority": "critical",
                    "finding": (
                        "TLS certificate appears "
                        "to be expired."
                    ),
                    "action": (
                        "Renew and deploy a valid certificate."
                    ),
                }
            )

        elif days_until_expiry <= 30:
            recommendations.append(
                {
                    "category": "certificate",
                    "priority": "medium",
                    "finding": (
                        "TLS certificate expires "
                        "within 30 days."
                    ),
                    "action": (
                        "Verify automated certificate "
                        "renewal before expiry."
                    ),
                }
            )

    return recommendations


def _build_decision(
    assessment: WebsiteAssessment,
    quantum_assessment: dict[str, Any],
) -> dict[str, Any]:
    """
    Build an agent-friendly high-level decision.
    """

    website_grade = _security_grade(
        assessment
    )

    quantum_risk = (
        quantum_assessment
        .get("quantum_risk", {})
    )

    quantum_status = quantum_risk.get(
        "status"
    )

    benchmark = (
        quantum_assessment
        .get("toy_benchmark", {})
    )

    benchmark_result = (
        benchmark.get("result")
    )

    benchmark_verified = False

    if benchmark_result:

        attack = benchmark_result.get(
            "attack",
            {},
        )

        benchmark_verified = bool(
            attack.get(
                "order_verified",
                False,
            )
        )

    if not assessment.https:
        overall_status = "high_risk"
    elif quantum_status == "not_post_quantum_secure":
        overall_status = "quantum_migration_review"
    elif website_grade == "needs_improvement":
        overall_status = "web_hardening_required"
    else:
        overall_status = "review"

    return {
        "overall_status": overall_status,

        "website_security_grade": website_grade,

        "quantum_security_status": (
            quantum_status
        ),

        "quantum_migration_review": (
            quantum_status
            == "not_post_quantum_secure"
        ),

        "toy_quantum_benchmark": {
            "executed": bool(
                benchmark.get(
                    "executed",
                    False,
                )
            ),
            "verified": benchmark_verified,
            "represents_real_world_break": False,
        },

        "real_world_compromise": False,
    }


# =====================================================================
# ORCHESTRATOR
# =====================================================================


def run_one_click_assessment(
    target_url: str,
    *,
    authorization_confirmed: bool,
    timeout_seconds: int = 10,
    max_bytes: int = 1_000_000,
    max_redirects: int = 3,
    run_quantum_benchmark: bool = True,
    shots: int = 128,
    noise_probability: float = 0.10,
) -> dict[str, Any]:
    """
    Execute the complete website quantum-security pipeline.

    Parameters
    ----------
    target_url:
        Authorized website URL.

    authorization_confirmed:
        Explicit authorization confirmation.

    timeout_seconds:
        Network timeout.

    max_bytes:
        Maximum HTML response bytes inspected.

    max_redirects:
        Maximum validated redirects.

    run_quantum_benchmark:
        Whether to execute the separate toy benchmark.

    shots:
        Quantum benchmark measurement shots.

    noise_probability:
        Depolarizing noise probability.

    Returns
    -------
    dict
        Combined assessment result.
    """

    if not authorization_confirmed:
        raise ValueError(
            "Authorization must be explicitly confirmed."
        )

    # -------------------------------------------------------------
    # 1. Website inspection
    # -------------------------------------------------------------

    assessment = assess_website(
        target_url,
        timeout=timeout_seconds,
        max_bytes=max_bytes,
        max_redirects=max_redirects,
    )

    # -------------------------------------------------------------
    # 2. Quantum mapping + optional toy benchmark
    # -------------------------------------------------------------

    quantum_assessment = (
        build_website_quantum_assessment(
            crypto_inventory=(
                assessment.crypto_inventory
            ),
            quantum_risk=(
                assessment.quantum_risk
            ),
            run_benchmark=(
                run_quantum_benchmark
            ),
            shots=shots,
            noise_probability=(
                noise_probability
            ),
        )
    )

    # -------------------------------------------------------------
    # 3. Recommendations
    # -------------------------------------------------------------

    recommendations = (
        _build_recommendations(
            assessment
        )
    )

    # -------------------------------------------------------------
    # 4. High-level decision
    # -------------------------------------------------------------

    decision = _build_decision(
        assessment,
        quantum_assessment,
    )

    # -------------------------------------------------------------
    # 5. Final result
    # -------------------------------------------------------------

    return {
        "status": "completed",

        "assessment_version": (
            ASSESSMENT_VERSION
        ),

        "created_at": _utc_now(),

        "target": {
            "url": assessment.target_url,
            "final_url": assessment.final_url,
        },

        "website": {
            "status_code": assessment.status_code,
            "content_type": assessment.content_type,
            "content_length": assessment.content_length,
            "title": assessment.title,
            "https": assessment.https,
            "tls": assessment.tls,
            "security_headers": (
                assessment.security_headers
            ),
            "cookies": assessment.cookies,
            "page": assessment.page,
        },

        "cryptography": {
            "inventory": (
                assessment.crypto_inventory
            ),

            "quantum_risk": (
                assessment.quantum_risk
            ),
        },

        "quantum_assessment": (
            quantum_assessment
        ),

        "decision": decision,

        "recommendations": recommendations,

        "warnings": assessment.warnings,

        "errors": assessment.errors,

        "scope": {
            "authorized_target": True,
            "passive_website_assessment": True,
            "destructive_testing": False,
            "authentication_bypass": False,
            "credential_testing": False,
            "brute_force": False,
            "data_modification": False,
            "unbounded_crawling": False,
            "real_world_cryptographic_break": False,
        },

        "evidence": {
            "real_website_observation": {
                "certificate_crypto": (
                    assessment.crypto_inventory
                ),
                "quantum_risk": (
                    assessment.quantum_risk
                ),
            },

            "quantum_experiment": {
                "scope": (
                    "research-toy-benchmark"
                ),

                "real_world_break_demonstrated": (
                    False
                ),

                "result": (
                    quantum_assessment
                    .get("toy_benchmark", {})
                    .get("result")
                ),
            },
        },
    }


__all__ = [
    "ASSESSMENT_VERSION",
    "run_one_click_assessment",
]