"""
Website Security Assessment API.

Provides a safe, authorized, passive website assessment endpoint
and exposes the complete one-click website-to-quantum-security
assessment pipeline.

Endpoints
---------
GET  /api/website/capabilities
POST /api/website/assessment

Current scope
-------------
- HTTPS
- TLS
- Certificate
- Public-key cryptography discovery
- Quantum-risk classification
- Optional toy quantum benchmark
- Security headers
- Cookies
- HTML metadata
- Machine-readable recommendations

Safety
------
This API does NOT perform:

- vulnerability exploitation
- authentication bypass
- credential brute forcing
- destructive testing
- data modification
- unbounded crawling
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from qattack.web.one_click import (
    run_one_click_assessment,
)


# =====================================================================
# ROUTER
# =====================================================================

router = APIRouter(
    prefix="/website",
    tags=["Website Security Assessment"],
)


# =====================================================================
# ALLOWLIST
# =====================================================================

DEFAULT_ALLOWED_HOSTS = {
    "zmo-frontend.vercel.app",
}


def _allowed_hosts() -> set[str]:
    """
    Read the authorized hostname allowlist.
    """

    configured = os.getenv(
        "WEBSITE_ASSESSMENT_ALLOWED_HOSTS"
    )

    if not configured:
        return DEFAULT_ALLOWED_HOSTS.copy()

    values = {
        item.strip().lower().rstrip(".")
        for item in configured.split(",")
        if item.strip()
    }

    return values or DEFAULT_ALLOWED_HOSTS.copy()


def _validate_allowed_host(
    target_url: str,
) -> None:
    """Ensure the target hostname is authorized."""

    parsed = urlparse(
        target_url
    )

    hostname = parsed.hostname

    if not hostname:
        raise ValueError(
            "Target URL has no hostname."
        )

    hostname = (
        hostname.lower()
        .rstrip(".")
    )

    if hostname not in _allowed_hosts():
        raise ValueError(
            "Target hostname is not in the authorized "
            "assessment allowlist."
        )


# =====================================================================
# REQUEST MODEL
# =====================================================================


class WebsiteAssessmentRequest(BaseModel):
    """
    One-click website quantum-security assessment request.
    """

    target_url: str = Field(
        ...,
        min_length=8,
        max_length=2048,
        description=(
            "Authorized website URL to assess."
        ),
        examples=[
            "https://zmo-frontend.vercel.app"
        ],
    )

    authorization_confirmed: bool = Field(
        default=False,
        description=(
            "Confirm that the requester is authorized "
            "to assess the target."
        ),
    )

    timeout_seconds: int = Field(
        default=10,
        ge=1,
        le=30,
        description=(
            "HTTP/TLS connection timeout."
        ),
    )

    max_bytes: int = Field(
        default=1_000_000,
        ge=10_000,
        le=5_000_000,
        description=(
            "Maximum HTML response bytes to inspect."
        ),
    )

    max_redirects: int = Field(
        default=3,
        ge=0,
        le=10,
        description=(
            "Maximum number of validated redirects."
        ),
    )

    run_quantum_benchmark: bool = Field(
        default=True,
        description=(
            "Run a separate research toy quantum benchmark "
            "when supported classical public-key cryptography "
            "is detected."
        ),
    )

    shots: int = Field(
        default=128,
        ge=1,
        le=100000,
        description=(
            "Measurement shots for the toy benchmark."
        ),
    )

    noise_probability: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description=(
            "Depolarizing noise probability."
        ),
    )


# =====================================================================
# WEBSITE ASSESSMENT
# =====================================================================


@router.post("/assessment")
def website_assessment(
    request: WebsiteAssessmentRequest,
) -> dict[str, Any]:
    """
    Run the complete one-click website assessment.

    Pipeline
    --------

    Website
       |
       +--> HTTP/TLS
       +--> Certificate
       +--> Crypto inventory
       +--> Quantum risk
       +--> Toy quantum benchmark
       +--> Recommendations
       |
       v
    Combined machine-readable assessment
    """

    if not request.authorization_confirmed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "authorization_required",
                "message": (
                    "Set authorization_confirmed=true "
                    "for an authorized target."
                ),
            },
        )

    try:

        _validate_allowed_host(
            request.target_url
        )

        result = run_one_click_assessment(
            request.target_url,
            authorization_confirmed=(
                request.authorization_confirmed
            ),
            timeout_seconds=(
                request.timeout_seconds
            ),
            max_bytes=(
                request.max_bytes
            ),
            max_redirects=(
                request.max_redirects
            ),
            run_quantum_benchmark=(
                request.run_quantum_benchmark
            ),
            shots=request.shots,
            noise_probability=(
                request.noise_probability
            ),
        )

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_target",
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "website_assessment_failed"
                ),
                "message": str(exc),
            },
        ) from exc


# =====================================================================
# CAPABILITIES
# =====================================================================


@router.get("/capabilities")
def website_capabilities() -> dict[str, Any]:
    """
    Describe website assessment capabilities.
    """

    return {
        "service": (
            "website-quantum-security-assessment"
        ),

        "version": "0.3.0",

        "mode": (
            "passive + quantum-risk-mapping"
        ),

        "authorized_targets_only": True,

        "pipeline": [
            "website_inspection",
            "tls_inspection",
            "certificate_inspection",
            "crypto_inventory",
            "quantum_risk_mapping",
            "optional_toy_quantum_benchmark",
            "recommendations",
            "machine_readable_decision",
        ],

        "checks": [
            "https",
            "http_status",
            "tls",
            "certificate",
            "certificate_public_key",
            "certificate_signature",
            "crypto_inventory",
            "quantum_risk_classification",
            "security_headers",
            "cookies",
            "page_title",
            "forms",
            "password_inputs",
            "scripts",
            "links",
        ],

        "not_supported": [
            "credential_bruteforce",
            "authentication_bypass",
            "destructive_testing",
            "data_modification",
            "unbounded_crawling",
            "real_world_cryptographic_break",
        ],

        "allowed_hosts": sorted(
            _allowed_hosts()
        ),
    }


__all__ = [
    "router",
    "WebsiteAssessmentRequest",
    "website_assessment",
    "website_capabilities",
]