
"""
Persistent storage for Quantum Security Assessments.

Uses SQLite by default so the API works immediately without requiring
a running PostgreSQL server.

The storage interface is intentionally small and can later be backed
by PostgreSQL without changing the API contract.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path("results") / "api_assessments" / "assessments.db"


class AssessmentStore:
    """SQLite-backed persistent assessment store."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target_json TEXT NOT NULL,
                    experiment_json TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    reports_json TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def save(self, record: dict[str, Any]) -> None:
        """Persist an assessment record."""

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO assessments (
                    assessment_id,
                    created_at,
                    status,
                    target_json,
                    experiment_json,
                    result_json,
                    evidence_json,
                    reports_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["assessment_id"],
                    record["created_at"],
                    record["status"],
                    json.dumps(
                        record["target"],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        record["experiment"],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        record["result"],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        record["evidence"],
                        ensure_ascii=False,
                    ),
                    json.dumps(
                        record["reports"],
                        ensure_ascii=False,
                    ),
                ),
            )

            connection.commit()

    def get(
        self,
        assessment_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve one assessment."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    assessment_id,
                    created_at,
                    status,
                    target_json,
                    experiment_json,
                    result_json,
                    evidence_json,
                    reports_json
                FROM assessments
                WHERE assessment_id = ?
                """,
                (assessment_id,),
            ).fetchone()

        if row is None:
            return None

        return {
            "assessment_id": row["assessment_id"],
            "created_at": row["created_at"],
            "status": row["status"],
            "target": json.loads(row["target_json"]),
            "experiment": json.loads(row["experiment_json"]),
            "result": json.loads(row["result_json"]),
            "evidence": json.loads(row["evidence_json"]),
            "reports": json.loads(row["reports_json"]),
        }

    def list_all(self) -> list[dict[str, Any]]:
        """Return all assessments, newest first."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    assessment_id,
                    created_at,
                    status,
                    target_json,
                    experiment_json
                FROM assessments
                ORDER BY created_at DESC
                """
            ).fetchall()

        return [
            {
                "assessment_id": row["assessment_id"],
                "created_at": row["created_at"],
                "status": row["status"],
                "target": json.loads(row["target_json"]),
                "experiment": json.loads(row["experiment_json"]),
            }
            for row in rows
        ]

    def count(self) -> int:
        """Return the number of stored assessments."""

        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM assessments"
            ).fetchone()

        return int(row["count"])


__all__ = [
    "AssessmentStore",
    "DEFAULT_DB_PATH",
]

