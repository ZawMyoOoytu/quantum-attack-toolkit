
"""
Agent Gateway for Quantum Security Assessment API.

This module provides an AI-agent-facing interface to the
Quantum Security Assessment Engine.

Architecture
------------

AI Agent / External Application
            |
            v
     POST /api/agent/assess
            |
            v
       Agent Gateway
            |
            v
 QuantumSecurityAssessment
            |
      +-----+-----+
      |           |
      v           v
 Measurement   Quantum Attack
 Analysis      Benchmark
      |           |
      +-----+-----+
            |
            v
     Security Evidence
            |
            v
      Structured JSON


Important
---------
The `/api/agent` URL prefix is intentionally NOT defined here.

It is registered centrally by `qattack/api/main.py` using:

    app.include_router(
        agent_router,
        prefix="/api/agent",
    )

This prevents accidental routes such as:

    /api/agent/api/agent/assess
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from qattack.analysis.evidence import evidence_from_result
from qattack.assessment import QuantumSecurityAssessment
from qattack.core.target import Target


# =====================================================================
# ROUTER
# =====================================================================

router = APIRouter(
    tags=["Agent Gateway"],
)


# =====================================================================
# REQUEST MODEL
# =====================================================================


class AgentAssessmentRequest(BaseModel):
    """
    Request sent by an AI agent to execute a quantum-security
    assessment.

    Example
    -------

    {
        "target_name": "RSA-Toy-15",
        "target_type": "rsa",
        "target_size": 15,
        "shots": 128,
        "noise_probability": 0.10
    }
    """

    target_name: str = Field(
        default="RSA-Toy-15",
        min_length=1,
        description="Human-readable target name.",
    )

    target_type: str = Field(
        default="rsa",
        min_length=1,
        description="Target type, for example rsa.",
    )

    target_size: int = Field(
        default=15,
        gt=0,
        description="Target size used by the benchmark.",
    )

    shots: int = Field(
        default=128,
        ge=1,
        le=100000,
        description="Number of measurement shots.",
    )

    noise_probability: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description=(
            "Depolarizing noise probability "
            "between 0.0 and 1.0."
        ),
    )


# =====================================================================
# HELPERS
# =====================================================================


def _json_safe(value: Any) -> Any:
    """
    Convert common Python objects into JSON-compatible values.

    Handles:

    - dict
    - list
    - tuple
    - set
    - NumPy-like scalar objects
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
            for item in sorted(value, key=str)
        ]

    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except Exception:
            pass

    return value


# =====================================================================
# CAPABILITIES
# =====================================================================


@router.get("/capabilities")
def agent_capabilities() -> dict[str, Any]:
    """
    Return capabilities available to an AI agent.

    This endpoint allows an agent/orchestrator to discover
    what this backend can execute.
    """

    return {
        "service": (
            "quantum-security-assessment-agent-gateway"
        ),
        "version": "0.1.0",
        "status": "available",

        "capabilities": [
            {
                "name": "quantum_security_assessment",
                "description": (
                    "Execute a quantum-security assessment "
                    "against a supported benchmark target."
                ),
            },
            {
                "name": "measurement_analysis",
                "description": (
                    "Analyze measurement distributions, "
                    "dominant states, entropy, and "
                    "probability mass."
                ),
            },
            {
                "name": "quantum_attack_benchmark",
                "description": (
                    "Execute the configured quantum attack "
                    "benchmark and evaluate recovered "
                    "orders and factors."
                ),
            },
            {
                "name": "security_evidence",
                "description": (
                    "Convert quantum assessment results "
                    "into structured security evidence."
                ),
            },
            {
                "name": "machine_readable_result",
                "description": (
                    "Return structured JSON suitable for "
                    "downstream AI-agent reasoning."
                ),
            },
        ],

        "supported_target_types": [
            "rsa",
        ],

        "supported_noise_models": [
            "depolarizing",
        ],

        "execution": {
            "mode": "synchronous",
            "persistent_storage": True,
            "reports": True,
        },

        "endpoints": {
            "capabilities": "/api/agent/capabilities",
            "assessment": "/api/agent/assess",
        },
    }


# =====================================================================
# AGENT ASSESSMENT
# =====================================================================


@router.post("/assess")
def agent_assess(
    request: AgentAssessmentRequest,
) -> dict[str, Any]:
    """
    Execute a quantum-security assessment requested by an AI agent.

    Processing pipeline
    -------------------

    1. Validate request.
    2. Create Target.
    3. Execute QuantumSecurityAssessment.
    4. Analyze measurement results.
    5. Generate security evidence.
    6. Extract decision signals.
    7. Return machine-readable response.

    Note
    ----
    This endpoint currently executes the existing assessment
    engine synchronously. Persistent storage and report generation
    remain available through the main assessment API.
    """

    try:
        # -------------------------------------------------------------
        # 1. Build target
        # -------------------------------------------------------------

        target = Target(
            target_type=request.target_type,
            name=request.target_name,
            size=request.target_size,
        )

        # -------------------------------------------------------------
        # 2. Create assessment engine
        # -------------------------------------------------------------

        assessor = QuantumSecurityAssessment()

        # -------------------------------------------------------------
        # 3. Execute quantum-security assessment
        # -------------------------------------------------------------

        result = assessor.run(
            target=target,
            shots=request.shots,
            noise_probability=request.noise_probability,
        )

        # -------------------------------------------------------------
        # 4. Generate security evidence
        # -------------------------------------------------------------

        evidence = evidence_from_result(result)

        # -------------------------------------------------------------
        # 5. Convert result into JSON-safe structures
        # -------------------------------------------------------------

        result_data = _json_safe(
            result.summary()
        )

        if hasattr(evidence, "summary"):
            evidence_data = _json_safe(
                evidence.summary()
            )
        else:
            evidence_data = _json_safe(
                evidence
            )

        # -------------------------------------------------------------
        # 6. Extract measurement information
        # -------------------------------------------------------------

        measurement = result_data.get(
            "measurement",
            {},
        )

        # -------------------------------------------------------------
        # 7. Extract attack information
        # -------------------------------------------------------------

        attack = result_data.get(
            "attack",
            {},
        )

        recovered_order = attack.get(
            "recovered_order"
        )

        order_verified = bool(
            attack.get(
                "order_verified",
                False,
            )
        )

        factors = attack.get(
            "factors",
            [],
        )

        expected_order = attack.get(
            "expected_order"
        )

        expected_factors = attack.get(
            "expected_factors",
            [],
        )

        # -------------------------------------------------------------
        # 8. Measurement signals
        # -------------------------------------------------------------

        dominant_state = measurement.get(
            "dominant_state"
        )

        dominant_probability = measurement.get(
            "dominant_probability"
        )

        shannon_entropy_bits = measurement.get(
            "shannon_entropy_bits"
        )

        normalized_entropy = measurement.get(
            "normalized_entropy"
        )

        probability_mass = measurement.get(
            "probability_mass"
        )

        probability_mass_error = measurement.get(
            "probability_mass_error"
        )

        # -------------------------------------------------------------
        # 9. Determine agent-facing assessment status
        # -------------------------------------------------------------

        if order_verified:
            assessment_status = "verified"
        else:
            assessment_status = "not_verified"

        # -------------------------------------------------------------
        # 10. Build structured agent response
        # -------------------------------------------------------------

        return {
            "status": "completed",

            "agent": {
                "gateway": "quantum-security-assessment",
                "execution_mode": "synchronous",
            },

            "assessment": {
                "target": {
                    "name": request.target_name,
                    "type": request.target_type,
                    "size": request.target_size,
                },

                "experiment": {
                    "shots": request.shots,
                    "noise_model": "depolarizing",
                    "noise_probability": (
                        request.noise_probability
                    ),
                },
            },

            "decision": {
                "assessment_status": assessment_status,

                "order": {
                    "recovered": recovered_order,
                    "verified": order_verified,
                    "expected": expected_order,
                },

                "factors": {
                    "recovered": factors,
                    "expected": expected_factors,
                },

                "measurement": {
                    "dominant_state": dominant_state,
                    "dominant_probability": (
                        dominant_probability
                    ),
                    "shannon_entropy_bits": (
                        shannon_entropy_bits
                    ),
                    "normalized_entropy": (
                        normalized_entropy
                    ),
                    "probability_mass": (
                        probability_mass
                    ),
                    "probability_mass_error": (
                        probability_mass_error
                    ),
                },
            },

            "result": result_data,

            "evidence": evidence_data,

            "agent_message": (
                "Quantum security assessment completed. "
                "Structured quantum-security evidence is "
                "available for downstream agent reasoning."
            ),
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "agent_assessment_failed",
                "message": str(exc),
            },
        ) from exc


# =====================================================================
# PUBLIC API
# =====================================================================


__all__ = [
    "router",
    "AgentAssessmentRequest",
    "agent_capabilities",
    "agent_assess",
]

