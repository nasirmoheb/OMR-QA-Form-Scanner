"""SQLite persistence layer for surveys, form results, and app settings."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from models import FormResult, Survey

logger = logging.getLogger("omr_qa_scanner")

DEFAULT_DB_PATH: Path = Path(__file__).resolve().parent.parent / "data" / "omr.db"

_SURVEY_COLS = [
    "university", "faculty", "department", "subject",
    "professor", "semester", "academic_year", "status",
    "created_at", "updated_at",
]

_FORM_COLS = [
    "survey_id", "form_id", "image_path",
    "q1", "q2", "q3", "q4", "q5", "q6", "q7",
    "q8", "q9", "q10", "q11", "q12", "q13", "q14",
    "form_score", "valid", "confidence", "manually_corrected",
]


class PersistenceManager:
    """Manages all SQLite CRUD for surveys, form results, and settings."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------ #
    #  Connection helpers
    # ------------------------------------------------------------------ #

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS surveys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    university TEXT NOT NULL DEFAULT '',
                    faculty TEXT NOT NULL DEFAULT '',
                    department TEXT NOT NULL DEFAULT '',
                    subject TEXT NOT NULL DEFAULT '',
                    professor TEXT NOT NULL DEFAULT '',
                    semester TEXT NOT NULL DEFAULT '',
                    academic_year TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'Draft',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS form_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    form_id TEXT NOT NULL,
                    image_path TEXT NOT NULL DEFAULT '',
                    q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT,
                    q5 TEXT, q6 TEXT, q7 TEXT, q8 TEXT,
                    q9 TEXT, q10 TEXT, q11 TEXT, q12 TEXT,
                    q13 TEXT, q14 TEXT,
                    form_score REAL NOT NULL DEFAULT 0.0,
                    valid INTEGER NOT NULL DEFAULT 0,
                    confidence REAL NOT NULL DEFAULT 0.0,
                    manually_corrected INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (survey_id) REFERENCES surveys(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            conn.commit()
            logger.info("Database initialised: %s", self.db_path)

    # ------------------------------------------------------------------ #
    #  Survey CRUD
    # ------------------------------------------------------------------ #

    def create_survey(self, survey: Survey) -> Survey:
        """Insert a new survey and populate its ``id``."""
        placeholders = ",".join([f"?" for _ in _SURVEY_COLS])
        sql = f"INSERT INTO surveys ({','.join(_SURVEY_COLS)}) VALUES ({placeholders})"
        values = [getattr(survey, c) for c in _SURVEY_COLS]
        with self._connect() as conn:
            cur = conn.execute(sql, values)
            conn.commit()
            survey.id = cur.lastrowid
            logger.info("Created survey id=%s", survey.id)
        return survey

    def update_survey(self, survey: Survey) -> Survey:
        """Update an existing survey by id."""
        if survey.id is None:
            raise ValueError("Survey must have an id to update.")
        sets = ",".join([f"{c}=?" for c in _SURVEY_COLS])
        sql = f"UPDATE surveys SET {sets} WHERE id=?"
        values = [getattr(survey, c) for c in _SURVEY_COLS] + [survey.id]
        with self._connect() as conn:
            conn.execute(sql, values)
            conn.commit()
            logger.info("Updated survey id=%s", survey.id)
        return survey

    def get_survey(self, survey_id: int) -> Survey | None:
        """Retrieve a single survey by id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM surveys WHERE id=?", (survey_id,)
            ).fetchone()
        return Survey.from_row(tuple(row)) if row else None

    def list_surveys(
        self,
        status: str | None = None,
        search: str | None = None,
        department: str | None = None,
        order_by: str = "updated_at DESC",
    ) -> list[Survey]:
        """List surveys with optional filtering and ordering."""
        conditions: list[str] = []
        params: list[Any] = []
        if status:
            conditions.append("status = ?")
            params.append(status)
        if department:
            conditions.append("department = ?")
            params.append(department)
        if search:
            conditions.append("(subject LIKE ? OR professor LIKE ?)")
            like = f"%{search}%"
            params.extend([like, like])

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM surveys {where} ORDER BY {order_by}"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [Survey.from_row(tuple(r)) for r in rows]

    def delete_survey(self, survey_id: int) -> bool:
        """Delete a survey (cascades to form_results)."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM surveys WHERE id=?", (survey_id,))
            conn.commit()
            deleted = cur.rowcount > 0
            if deleted:
                logger.info("Deleted survey id=%s", survey_id)
            return deleted

    # ------------------------------------------------------------------ #
    #  FormResult CRUD
    # ------------------------------------------------------------------ #

    def create_form_result(self, result: FormResult) -> FormResult:
        """Insert a new form result and populate its ``id``."""
        placeholders = ",".join(["?" for _ in _FORM_COLS])
        sql = f"INSERT INTO form_results ({','.join(_FORM_COLS)}) VALUES ({placeholders})"
        values = []
        for c in _FORM_COLS:
            v = getattr(result, c)
            if c == "valid" or c == "manually_corrected":
                v = 1 if v else 0
            values.append(v)
        with self._connect() as conn:
            cur = conn.execute(sql, values)
            conn.commit()
            result.id = cur.lastrowid
        return result

    def get_form_results(self, survey_id: int) -> list[FormResult]:
        """Retrieve all form results for a given survey."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM form_results WHERE survey_id=?", (survey_id,)
            ).fetchall()
        return [FormResult.from_row(tuple(r)) for r in rows]

    def update_form_result(self, result: FormResult) -> FormResult:
        """Update an existing form result by id."""
        if result.id is None:
            raise ValueError("FormResult must have an id to update.")
        sets = ",".join([f"{c}=?" for c in _FORM_COLS])
        sql = f"UPDATE form_results SET {sets} WHERE id=?"
        values = []
        for c in _FORM_COLS:
            v = getattr(result, c)
            if c == "valid" or c == "manually_corrected":
                v = 1 if v else 0
            values.append(v)
        values.append(result.id)
        with self._connect() as conn:
            conn.execute(sql, values)
            conn.commit()
        return result

    def delete_form_results_for_survey(self, survey_id: int) -> int:
        """Delete all form results for a survey. Returns rowcount."""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM form_results WHERE survey_id=?", (survey_id,)
            )
            conn.commit()
            return cur.rowcount

    # ------------------------------------------------------------------ #
    #  AppSettings
    # ------------------------------------------------------------------ #

    def set_setting(self, key: str, value: Any) -> None:
        """Persist a setting value (JSON-serialised)."""
        json_value = json.dumps(value, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json_value),
            )
            conn.commit()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Retrieve a setting value (JSON-deserialised)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key=?", (key,)
            ).fetchone()
        if row is None:
            return default
        return json.loads(row[0])

    def get_all_settings(self) -> dict[str, Any]:
        """Return all settings as a dictionary."""
        with self._connect() as conn:
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}

    def delete_setting(self, key: str) -> bool:
        """Remove a setting by key."""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM app_settings WHERE key=?", (key,))
            conn.commit()
            return cur.rowcount > 0
