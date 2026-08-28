"""
AI Agent Gateway for Quantum Security Assessment.

This module exposes machine-readable tools for AI agents.

Available agent tools
---------------------

GET  /api/agent/capabilities
POST /api/agent/assess
POST /api/agent/website-assess

The gateway supports two distinct workflows:

1. Quantum benchmark assessment

       Agent
         |
         v
       /assess
         |
         v
   QuantumSecurityAssessment

2. Authorized website quantum-security assessment

       Agent
         |
         v
   /website-assess
         |
         v
   Website Assessment
         |
         +--> TLS
         +--> Certificate
         +--> Crypto Inventory
         +--> Quantum Risk
         +--> Optional Toy Benchmark
         +--> Recommendations

Safety
------

Website assessment requires explicit authorization and an
authorized hostname allowlist.

The website workflow does NOT perform:

- authentication bypass
- credential brute force
- destructive testing
- data modification
- unbounded crawling
- real-world cryptographic breaking
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from qattack.analysis.evidence import (
    evidence_from_result,
)

from qattack.assessment import (
    QuantumSecurityAssessment,
)

from qattack.core.target import (
    Target,
)

from qattack.web.one_click import (
    run_one_click_assessment,
)


# =====================================================================
# ROUTER
# =====================================================================

router = APIRouter(
    tags=["Agent Gateway"],
)


# =====================================================================
# REQUEST MODELS
# =====================================================================


class AgentAssessmentRequest(BaseModel):
    """
    Request for the quantum benchmark assessment tool.
    """

    target_name: str = Field(
        default="RSA-Toy-15",
        min_length=1,
        description="Benchmark target name.",
    )

    target_type: str = Field(
        default="rsa",
        min_length=1,
        description="Benchmark target type.",
    )

    target_size: int = Field(
        default=15,
        gt=0,
        description="Benchmark target size.",
    )

    shots: int = Field(
        default=128,
        ge=1,
        le=100000,
        description="Quantum measurement shots.",
    )

    noise_probability: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description="Depolarizing noise probability.",
    )


class AgentWebsiteAssessmentRequest(BaseModel):
    """
    Request for the AI-agent website assessment tool.

    Example
    -------

    {
        "target_url": "https://zmo-frontend.vercel.app",
        "authorization_confirmed": true,
        "run_quantum_benchmark": true,
        "shots": 128,
        "noise_probability": 0.10
    }
    """

    target_url: str = Field(
        ...,
        min_length=8,
        max_length=2048,
        description=(
            "Authorized website URL."
        ),
        examples=[
            "https://zmo-frontend.vercel.app"
        ],
    )

    authorization_confirmed: bool = Field(
        default=False,
        description=(
            "Confirm authorization to assess "
            "the target website."
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
            "Maximum response bytes to inspect."
        ),
    )

    max_redirects: int = Field(
        default=3,
        ge=0,
        le=10,
        description=(
            "Maximum validated redirects."
        ),
    )

    run_quantum_benchmark: bool = Field(
        default=True,
        description=(
            "Run a separate research toy benchmark "
            "when supported cryptography is detected."
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
# HELPERS
# =====================================================================


def _json_safe(
    value: Any,
) -> Any:
    """
    Convert common Python objects into JSON-safe values.
    """

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
# CAPABILITIES
# =====================================================================


@router.get("/capabilities")
def agent_capabilities() -> dict[str, Any]:
    """
    Return machine-readable agent tool capabilities.
    """

    return {
        "service": (
            "quantum-security-assessment-agent-gateway"
        ),

        "version": "0.2.0",

        "status": "available",

        "tools": [
            {
                "name": "quantum_assess",

                "endpoint": (
                    "/api/agent/assess"
                ),

                "method": "POST",

                "description": (
                    "Run a quantum-security "
                    "research benchmark."
                ),
            },

            {
                "name": "website_quantum_assess",

                "endpoint": (
                    "/api/agent/website-assess"
                ),

                "method": "POST",

                "description": (
                    "Assess an authorized website's "
                    "observable security posture, TLS "
                    "certificate cryptography, quantum "
                    "risk, and optional toy benchmark."
                ),
            },
        ],

        "website_capabilities": [
            "https",
            "tls",
            "certificate",
            "certificate_public_key",
            "crypto_inventory",
            "quantum_risk_mapping",
            "security_headers",
            "cookies",
            "html_metadata",
            "toy_quantum_benchmark",
            "recommendations",
        ],

        "not_supported": [
            "authentication_bypass",
            "credential_bruteforce",
            "destructive_testing",
            "data_modification",
            "unbounded_crawling",
            "real_world_cryptographic_break",
        ],

        "agent_pattern": {
            "input": "target + security objective",
            "processing": (
                "assessment -> evidence -> decision"
            ),
            "output": (
                "machine-readable structured evidence"
            ),
        },
    }


# =====================================================================
# QUANTUM BENCHMARK TOOL
# =====================================================================


@router.post("/assess")
def agent_assess(
    request: AgentAssessmentRequest,
) -> dict[str, Any]:
    """
    Run the existing quantum-security benchmark.
    """

    try:

        target = Target(
            target_type=request.target_type,
            name=request.target_name,
            size=request.target_size,
        )

        assessor = (
            QuantumSecurityAssessment()
        )

        result = assessor.run(
            target=target,
            shots=request.shots,
            noise_probability=(
                request.noise_probability
            ),
        )

        evidence = (
            evidence_from_result(
                result
            )
        )

        result_data = _json_safe(
            result.summary()
        )

        if hasattr(
            evidence,
            "summary",
        ):
            evidence_data = _json_safe(
                evidence.summary()
            )
        else:
            evidence_data = _json_safe(
                evidence
            )

        attack = result_data.get(
            "attack",
            {},
        )

        measurement = result_data.get(
            "measurement",
            {},
        )

        return {
            "status": "completed",

            "tool": "quantum_assess",

            "assessment": {
                "target_name": (
                    request.target_name
                ),
                "target_type": (
                    request.target_type
                ),
                "target_size": (
                    request.target_size
                ),
                "shots": request.shots,
                "noise_probability": (
                    request.noise_probability
                ),
            },

            "decision": {
                "recovered_order": (
                    attack.get(
                        "recovered_order"
                    )
                ),
                "order_verified": bool(
                    attack.get(
                        "order_verified",
                        False,
                    )
                ),
                "factors": (
                    attack.get(
                        "factors",
                        [],
                    )
                ),
                "dominant_state": (
                    measurement.get(
                        "dominant_state"
                    )
                ),
                "normalized_entropy": (
                    measurement.get(
                        "normalized_entropy"
                    )
                ),
            },

            "result": result_data,

            "evidence": evidence_data,

            "agent_message": (
                "Quantum benchmark completed "
                "and structured evidence is ready "
                "for agent reasoning."
            ),
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "error": "agent_assessment_failed",
                "message": str(exc),
            },
        ) from exc


# =====================================================================
# WEBSITE QUANTUM ASSESSMENT TOOL
# =====================================================================


@router.post("/website-assess")
def agent_website_assess(
    request: AgentWebsiteAssessmentRequest,
) -> dict[str, Any]:
    """
    Perform one-click website quantum-security assessment.

    This endpoint is designed for AI-agent tool calling.

    Example agent request
    ---------------------

    {
        "target_url": "https://zmo-frontend.vercel.app",
        "authorization_confirmed": true,
        "run_quantum_benchmark": true
    }

    Output includes:

    - website security posture
    - TLS information
    - certificate information
    - public-key inventory
    - quantum risk
    - optional toy benchmark
    - recommendations
    - machine-readable decision
    """

    if not request.authorization_confirmed:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "authorization_required",
                "message": (
                    "The AI agent must explicitly "
                    "confirm authorization before "
                    "assessing the website."
                ),
            },
        )

    try:

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

        decision = result.get(
            "decision",
            {},
        )

        cryptography = result.get(
            "cryptography",
            {},
        )

        quantum_assessment = result.get(
            "quantum_assessment",
            {},
        )

        return {
            "status": "completed",

            "tool": "website_quantum_assess",

            "target": result.get(
                "target",
                {},
            ),

            "decision": decision,

            "cryptography": cryptography,

            "quantum_assessment": (
                quantum_assessment
            ),

            "recommendations": result.get(
                "recommendations",
                [],
            ),

            "website": result.get(
                "website",
                {},
            ),

            "warnings": result.get(
                "warnings",
                [],
            ),

            "errors": result.get(
                "errors",
                [],
            ),

            "scope": result.get(
                "scope",
                {},
            ),

            "evidence": result.get(
                "evidence",
                {},
            ),

            "agent_message": (
                "Authorized website quantum-security "
                "assessment completed. The result contains "
                "observable website evidence, cryptographic "
                "inventory, quantum-risk classification, "
                "and optional research benchmark data."
            ),
        }

    except HTTPException:
        raise

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_agent_request",
                "message": str(exc),
            },
        ) from exc

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "agent_website_assessment_failed"
                ),
                "message": str(exc),
            },
        ) from exc


# =====================================================================
# EXPORTS
# =====================================================================

__all__ = [
    "router",
    "AgentAssessmentRequest",
    "AgentWebsiteAssessmentRequest",
    "agent_capabilities",
    "agent_assess",
    "agent_website_assess",
]