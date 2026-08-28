
"""
Quantum Security Assessment API.

Persistent API layer for the Quantum Security Assessment Engine.

Endpoints
---------

GET  /
GET  /health

POST /api/assessment
GET  /api/assessment/{assessment_id}
GET  /api/assessment/{assessment_id}/report
GET  /api/assessments

GET  /api/agent/capabilities
POST /api/agent/assess


Architecture
------------

Client / AI Agent
        |
        +----------------------+
        |                      |
        v                      v
  Assessment API        Agent Gateway
        |                      |
        +----------+-----------+
                   |
                   v
     QuantumSecurityAssessment
                   |
        +----------+----------+
        |          |          |
        v          v          v
   Measurement   Quantum   Security
    Analysis     Attack     Evidence
                   |
                   v
             Reports
                   |
                   v
              SQLite


The Agent Gateway is registered here with:

    app.include_router(
        agent_router,
        prefix="/api/agent",
    )

The gateway itself does NOT define that prefix.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from qattack.analysis.evidence import evidence_from_result
from qattack.analysis.report import (
    render_html_report,
    save_all_reports,
)
from qattack.assessment import QuantumSecurityAssessment
from qattack.core.target import Target
from qattack.db.database import AssessmentStore

# Agent Gateway
from qattack.api.agent.gateway import (
    router as agent_router,
)


# =====================================================================
# APPLICATION
# =====================================================================

app = FastAPI(
    title="Quantum Security Assessment API",
    description=(
        "API-driven quantum-security assessment infrastructure "
        "for quantum attack benchmarks, measurement analysis, "
        "noise experiments, security evidence, persistent "
        "storage, machine-readable reports, and AI-agent "
        "integration."
    ),
    version="0.2.0",
)


# =====================================================================
# PERSISTENT STORAGE
# =====================================================================

RESULTS_DIR = (
    Path("results")
    / "api_assessments"
)

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

STORE = AssessmentStore()


# =====================================================================
# AGENT GATEWAY REGISTRATION
# =====================================================================

# IMPORTANT:
#
# gateway.py intentionally has no `/api/agent` prefix.
#
# This is the single place where the prefix is defined.
#
# Final routes:
#
#     /api/agent/capabilities
#     /api/agent/assess

app.include_router(
    agent_router,
    prefix="/api/agent",
    tags=["Agent Gateway"],
)


# =====================================================================
# REQUEST MODELS
# =====================================================================


class AssessmentRequest(BaseModel):
    """
    Request payload for a quantum security assessment.

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
# HELPER FUNCTIONS
# =====================================================================


def _utc_now() -> str:
    """
    Return the current UTC timestamp as ISO-8601.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


def _json_safe(value: Any) -> Any:
    """
    Convert common Python objects into JSON-compatible values.

    Handles:

    - dictionaries
    - lists
    - tuples
    - sets
    - pathlib.Path
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
            for item in sorted(
                value,
                key=str,
            )
        ]

    if isinstance(value, Path):
        return str(value)

    if hasattr(value, "item"):
        try:
            return _json_safe(
                value.item()
            )
        except Exception:
            pass

    return value


def _assessment_id() -> str:
    """
    Generate a unique assessment identifier.

    Example
    -------

    qa-4c1394d7e878
    """

    return (
        f"qa-{uuid.uuid4().hex[:12]}"
    )


def _get_record_or_404(
    assessment_id: str,
) -> dict[str, Any]:
    """
    Load an assessment from persistent storage.

    Raises
    ------

    HTTPException
        404 when the assessment does not exist.
    """

    record = STORE.get(
        assessment_id
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "assessment_not_found",
                "assessment_id": assessment_id,
            },
        )

    return record


def _build_report_prefix(
    target_name: str,
    noise_probability: float,
) -> str:
    """
    Build a filesystem-safe report prefix.

    Example
    -------

    RSA-Toy-15-noise-0.10
    """

    safe_name = (
        target_name
        .strip()
        .replace("\\", "_")
        .replace("/", "_")
        .replace(":", "_")
    )

    return (
        f"{safe_name}"
        f"-noise-{noise_probability:.2f}"
    )


# =====================================================================
# ROOT
# =====================================================================


@app.get("/")
def root() -> dict[str, Any]:
    """
    API information endpoint.
    """

    return {
        "service": (
            "Quantum Security Assessment API"
        ),
        "version": app.version,
        "status": "online",
        "storage": "sqlite",
        "assessment_count": STORE.count(),

        "endpoints": {
            "health": "/health",
            "docs": "/docs",

            "create_assessment": (
                "/api/assessment"
            ),

            "get_assessment": (
                "/api/assessment/{assessment_id}"
            ),

            "report": (
                "/api/assessment/"
                "{assessment_id}/report"
            ),

            "list_assessments": (
                "/api/assessments"
            ),

            "agent_capabilities": (
                "/api/agent/capabilities"
            ),

            "agent_assessment": (
                "/api/agent/assess"
            ),
        },
    }


# =====================================================================
# HEALTH
# =====================================================================


@app.get("/health")
def health() -> dict[str, Any]:
    """
    Health check endpoint.
    """

    return {
        "status": "ok",
        "service": (
            "quantum-security-assessment-api"
        ),
        "version": app.version,
        "storage": "sqlite",
        "assessment_count": STORE.count(),
        "agent_gateway": "available",
        "timestamp": _utc_now(),
    }


# =====================================================================
# CREATE ASSESSMENT
# =====================================================================


@app.post("/api/assessment")
def create_assessment(
    request: AssessmentRequest,
) -> dict[str, Any]:
    """
    Run and persist a quantum security assessment.

    Processing pipeline
    -------------------

    1. Create target.
    2. Run QuantumSecurityAssessment.
    3. Analyze measurement results.
    4. Generate security evidence.
    5. Generate JSON/TXT/HTML reports.
    6. Persist assessment in SQLite.
    7. Return machine-readable result.
    """

    assessment_id = _assessment_id()

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

        assessor = (
            QuantumSecurityAssessment()
        )

        # -------------------------------------------------------------
        # 3. Execute quantum-security experiment
        # -------------------------------------------------------------

        result = assessor.run(
            target=target,
            shots=request.shots,
            noise_probability=(
                request.noise_probability
            ),
        )

        # -------------------------------------------------------------
        # 4. Generate security evidence
        # -------------------------------------------------------------

        evidence = evidence_from_result(
            result
        )

        # -------------------------------------------------------------
        # 5. JSON-safe result
        # -------------------------------------------------------------

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

        # -------------------------------------------------------------
        # 6. Generate reports
        # -------------------------------------------------------------

        prefix = _build_report_prefix(
            request.target_name,
            request.noise_probability,
        )

        report_dir = (
            RESULTS_DIR
            / assessment_id
        )

        report_paths = save_all_reports(
            evidence,
            report_dir,
            prefix=prefix,
        )

        report_data = {
            key: str(path)
            for key, path
            in report_paths.items()
        }

        # -------------------------------------------------------------
        # 7. Build persistent record
        # -------------------------------------------------------------

        record = {
            "assessment_id": (
                assessment_id
            ),

            "created_at": _utc_now(),

            "status": "completed",

            "target": {
                "name": request.target_name,
                "type": request.target_type,
                "size": request.target_size,
            },

            "experiment": {
                "shots": request.shots,
                "noise_model": (
                    "depolarizing"
                ),
                "noise_probability": (
                    request.noise_probability
                ),
            },

            "result": result_data,

            "evidence": evidence_data,

            "reports": report_data,
        }

        # -------------------------------------------------------------
        # 8. Persist
        # -------------------------------------------------------------

        STORE.save(record)

        # -------------------------------------------------------------
        # 9. Return
        # -------------------------------------------------------------

        return record

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "assessment_failed",
                "message": str(exc),
                "assessment_id": (
                    assessment_id
                ),
            },
        ) from exc


# =====================================================================
# GET SINGLE ASSESSMENT
# =====================================================================


@app.get(
    "/api/assessment/{assessment_id}"
)
def get_assessment(
    assessment_id: str,
) -> dict[str, Any]:
    """
    Retrieve a persisted assessment.
    """

    return _get_record_or_404(
        assessment_id
    )


# =====================================================================
# HTML REPORT
# =====================================================================


@app.get(
    "/api/assessment/"
    "{assessment_id}/report",
    response_class=HTMLResponse,
)
def get_report(
    assessment_id: str,
) -> HTMLResponse:
    """
    Return the assessment as a standalone HTML report.
    """

    record = _get_record_or_404(
        assessment_id
    )

    evidence = record.get(
        "evidence",
        {},
    )

    try:
        html_report = (
            render_html_report(
                evidence
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": (
                    "report_generation_failed"
                ),
                "message": str(exc),
                "assessment_id": (
                    assessment_id
                ),
            },
        ) from exc

    return HTMLResponse(
        content=html_report,
        status_code=200,
    )


# =====================================================================
# LIST ASSESSMENTS
# =====================================================================


@app.get("/api/assessments")
def list_assessments() -> dict[str, Any]:
    """
    List persisted assessments.

    Returns lightweight metadata instead of
    complete result/evidence payloads.
    """

    items = STORE.list_all()

    assessments = []

    for record in items:
        assessments.append(
            {
                "assessment_id": (
                    record.get(
                        "assessment_id"
                    )
                ),

                "created_at": (
                    record.get(
                        "created_at"
                    )
                ),

                "status": (
                    record.get(
                        "status"
                    )
                ),

                "target": (
                    record.get(
                        "target"
                    )
                ),

                "experiment": (
                    record.get(
                        "experiment"
                    )
                ),
            }
        )

    return {
        "count": len(assessments),
        "assessments": assessments,
    }


# =====================================================================
# PUBLIC API
# =====================================================================


__all__ = [
    "app",
    "AssessmentRequest",
    "root",
    "health",
    "create_assessment",
    "get_assessment",
    "get_report",
    "list_assessments",
]

