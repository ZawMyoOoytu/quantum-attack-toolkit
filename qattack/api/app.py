
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import json
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from qattack.assessment import QuantumSecurityAssessment
from qattack.core.target import Target


# ============================================================
# Application
# ============================================================

app = FastAPI(
    title="Quantum Attack Toolkit",
    description=(
        "Quantum security assessment and benchmarking API "
        "for controlled research experiments."
    ),
    version="0.3.0",
)


# ============================================================
# Storage
# ============================================================

RESULTS_DIR = Path("results") / "assessments"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Request Models
# ============================================================

class AssessmentRequest(BaseModel):
    target_type: str = Field(
        ...,
        min_length=1,
        description="Target type, e.g. rsa",
    )

    name: str = Field(
        ...,
        min_length=1,
        description="Target name",
    )

    size: int = Field(
        ...,
        gt=1,
        description="Target size",
    )

    shots: int = Field(
        default=128,
        ge=1,
        le=100000,
        description="Number of measurement shots",
    )

    noise_probability: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Depolarizing noise probability",
    )


class BenchmarkRequest(BaseModel):
    target_type: str = Field(
        ...,
        min_length=1,
    )

    name: str = Field(
        ...,
        min_length=1,
    )

    size: int = Field(
        ...,
        gt=1,
    )

    shots: int = Field(
        default=128,
        ge=1,
        le=100000,
    )

    trials: int = Field(
        default=10,
        ge=1,
        le=1000,
    )

    noise_probabilities: list[float] = Field(
        default=[0.0, 0.05, 0.10, 0.20, 0.30, 0.50, 0.70, 1.0],
        min_length=1,
    )


# ============================================================
# Response Models
# ============================================================

class AssessmentResponse(BaseModel):
    assessment_id: str
    status: str
    created_at: str
    result: dict[str, Any]


class BenchmarkResponse(BaseModel):
    benchmark_id: str
    status: str
    created_at: str
    result: dict[str, Any]


# ============================================================
# Utility Functions
# ============================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def result_path(
    result_id: str,
    prefix: str,
) -> Path:
    return RESULTS_DIR / f"{prefix}_{result_id}.json"


def save_json(
    path: Path,
    payload: dict[str, Any],
) -> None:

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_json(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Result not found.",
        )

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail="Stored result is corrupted.",
        ) from exc


def validate_noise_probabilities(
    probabilities: list[float],
) -> None:

    for probability in probabilities:

        if not 0.0 <= probability <= 1.0:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Every noise probability must be "
                    "between 0.0 and 1.0."
                ),
            )


# ============================================================
# Health
# ============================================================

@app.get("/health")
def health() -> dict[str, Any]:

    return {
        "status": "ok",
        "service": "quantum-attack-toolkit",
        "version": app.version,
        "timestamp": utc_now(),
    }


# ============================================================
# Service Information
# ============================================================

@app.get("/")
def root() -> dict[str, Any]:

    return {
        "service": "Quantum Attack Toolkit",
        "version": app.version,
        "purpose": (
            "Controlled quantum-security assessment "
            "and benchmarking."
        ),
        "endpoints": {
            "health": "/health",
            "assessment": "/assess",
            "benchmark": "/benchmark",
            "docs": "/docs",
        },
    }


# ============================================================
# Single Assessment
# ============================================================

@app.post(
    "/assess",
    response_model=AssessmentResponse,
)
def run_assessment(
    request: AssessmentRequest,
) -> AssessmentResponse:

    assessment_id = str(uuid.uuid4())
    created_at = utc_now()

    try:

        target = Target(
            target_type=request.target_type,
            name=request.name,
            size=request.size,
        )

        engine = QuantumSecurityAssessment()

        result = engine.run(
            target=target,
            shots=request.shots,
            noise_probability=request.noise_probability,
        )

        summary = result.summary()

        payload = {
            "assessment_id": assessment_id,
            "status": "completed",
            "created_at": created_at,
            "request": request.model_dump(),
            "result": summary,
        }

        save_json(
            result_path(
                assessment_id,
                "assessment",
            ),
            payload,
        )

        return AssessmentResponse(
            assessment_id=assessment_id,
            status="completed",
            created_at=created_at,
            result=summary,
        )

    except Exception as exc:

        payload = {
            "assessment_id": assessment_id,
            "status": "failed",
            "created_at": created_at,
            "request": request.model_dump(),
            "error": str(exc),
        }

        save_json(
            result_path(
                assessment_id,
                "assessment",
            ),
            payload,
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# Retrieve Assessment
# ============================================================

@app.get(
    "/assess/{assessment_id}",
)
def get_assessment(
    assessment_id: str,
) -> dict[str, Any]:

    return load_json(
        result_path(
            assessment_id,
            "assessment",
        )
    )


# ============================================================
# Statistical Benchmark
# ============================================================

@app.post(
    "/benchmark",
    response_model=BenchmarkResponse,
)
def run_benchmark(
    request: BenchmarkRequest,
) -> BenchmarkResponse:

    benchmark_id = str(uuid.uuid4())
    created_at = utc_now()

    validate_noise_probabilities(
        request.noise_probabilities
    )

    try:

        from qattack.benchmarking.noise_sweep import (
            run_depolarizing_sweep,
        )

        results = run_depolarizing_sweep(
            request.noise_probabilities,
            shots=request.shots,
            trials=request.trials,
        )

        summaries = [
            item.summary()
            for item in results
        ]

        payload = {
            "benchmark_id": benchmark_id,
            "status": "completed",
            "created_at": created_at,
            "request": request.model_dump(),
            "result": {
                "model": "depolarizing",
                "records": summaries,
            },
        }

        save_json(
            result_path(
                benchmark_id,
                "benchmark",
            ),
            payload,
        )

        return BenchmarkResponse(
            benchmark_id=benchmark_id,
            status="completed",
            created_at=created_at,
            result=payload["result"],
        )

    except Exception as exc:

        payload = {
            "benchmark_id": benchmark_id,
            "status": "failed",
            "created_at": created_at,
            "request": request.model_dump(),
            "error": str(exc),
        }

        save_json(
            result_path(
                benchmark_id,
                "benchmark",
            ),
            payload,
        )

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc


# ============================================================
# Retrieve Benchmark
# ============================================================

@app.get(
    "/benchmark/{benchmark_id}",
)
def get_benchmark(
    benchmark_id: str,
) -> dict[str, Any]:

    return load_json(
        result_path(
            benchmark_id,
            "benchmark",
        )
    )

