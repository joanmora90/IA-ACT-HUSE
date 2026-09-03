from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from uuid import UUID

from .models import AssessmentResult, AssessmentState, ProjectMetadata


class AssessmentNotFoundError(KeyError):
    pass


class SQLiteAssessmentRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    id TEXT PRIMARY KEY,
                    metadata_json TEXT NOT NULL,
                    answers_json TEXT NOT NULL,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def create(self, metadata: ProjectMetadata) -> AssessmentState:
        state = AssessmentState(metadata=metadata)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO assessments
                (id, metadata_json, answers_json, result_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(state.id),
                    state.metadata.model_dump_json(),
                    json.dumps(state.answers),
                    None,
                    state.created_at.isoformat(),
                    state.updated_at.isoformat(),
                ),
            )
        return state

    def get(self, assessment_id: UUID) -> AssessmentState:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM assessments WHERE id = ?", (str(assessment_id),)
            ).fetchone()
        if row is None:
            raise AssessmentNotFoundError(str(assessment_id))
        return AssessmentState(
            id=UUID(row["id"]),
            metadata=ProjectMetadata.model_validate_json(row["metadata_json"]),
            answers=json.loads(row["answers_json"]),
            result=(
                AssessmentResult.model_validate_json(row["result_json"])
                if row["result_json"]
                else None
            ),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def save(self, state: AssessmentState) -> AssessmentState:
        state.updated_at = datetime.now(UTC)
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE assessments
                SET metadata_json = ?, answers_json = ?, result_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    state.metadata.model_dump_json(),
                    json.dumps(state.answers),
                    state.result.model_dump_json() if state.result else None,
                    state.updated_at.isoformat(),
                    str(state.id),
                ),
            )
        if cursor.rowcount == 0:
            raise AssessmentNotFoundError(str(state.id))
        return state
