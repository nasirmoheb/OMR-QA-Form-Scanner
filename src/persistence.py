"""SQLite persistence layer for surveys, form results, and app settings."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from models import DimensionScore, FormResult, QAAlert, Survey

logger = logging.getLogger("tadris_qa_system")


def _get_default_db_path() -> Path:
    """Get the default database path in the user's AppData directory.
    
    On Windows: %LOCALAPPDATA%\Tadris_QA\data\omr.db
    On Linux/Mac: ~/.local/share/Tadris_QA/data/omr.db
    
    Falls back to the application directory if running in development mode.
    """
    # Check if we're running from a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running as compiled executable - use AppData
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('LOCALAPPDATA')
            if app_data:
                return Path(app_data) / "Tadris_QA" / "data" / "omr.db"
        else:  # Linux/Mac
            home = Path.home()
            return home / ".local" / "share" / "Tadris_QA" / "data" / "omr.db"
    
    # Development mode - use local data directory
    return Path(__file__).resolve().parent.parent / "data" / "omr.db"


DEFAULT_DB_PATH: Path = _get_default_db_path()

_SURVEY_COLS = [
    "university", "faculty", "department", "subject",
    "professor", "semester", "academic_year", "status",
    "created_at", "updated_at",
]

_FORM_COLS = [
    "survey_id", "form_id", "image_path",
    "q1", "q2", "q3", "q4", "q5", "q6", "q7",
    "q8", "q9", "q10", "q11", "q12", "q13", "q14",
    "form_score", "valid", "confidence", "manually_corrected", "comment",
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
                    comment TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (survey_id) REFERENCES surveys(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dimension_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    dimension_name TEXT NOT NULL,
                    mean REAL NOT NULL DEFAULT 0.0,
                    std_dev REAL NOT NULL DEFAULT 0.0,
                    question_indices TEXT NOT NULL DEFAULT '[]',
                    FOREIGN KEY (survey_id) REFERENCES surveys(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS qa_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    survey_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    dimension_name TEXT NOT NULL DEFAULT '',
                    question_index INTEGER NOT NULL DEFAULT 0,
                    value REAL NOT NULL DEFAULT 0.0,
                    threshold REAL NOT NULL DEFAULT 0.0,
                    message TEXT NOT NULL DEFAULT '',
                    severity TEXT NOT NULL DEFAULT 'warning',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (survey_id) REFERENCES surveys(id)
                        ON DELETE CASCADE
                );
                """
            )
            # Safe migrations for existing databases
            self._migrate(conn)
            conn.commit()
            logger.info("Database initialised: %s", self.db_path)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        """Apply safe ALTER TABLE migrations for schema evolution."""
        migrations = [
            ("form_results", "comment", "TEXT NOT NULL DEFAULT ''"),
        ]
        for table, column, col_def in migrations:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
                logger.info("Migration: added %s.%s", table, column)
            except sqlite3.OperationalError:
                pass  # Column already exists

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

    # ------------------------------------------------------------------ #
    #  DimensionScore CRUD
    # ------------------------------------------------------------------ #

    def save_dimension_scores(self, scores: list[DimensionScore]) -> None:
        """Upsert dimension scores for a survey (replaces existing)."""
        if not scores:
            return
        survey_id = scores[0].survey_id
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM dimension_scores WHERE survey_id=?", (survey_id,)
            )
            for ds in scores:
                conn.execute(
                    """INSERT INTO dimension_scores
                       (survey_id, dimension_name, mean, std_dev, question_indices)
                       VALUES (?, ?, ?, ?, ?)""",
                    (
                        ds.survey_id,
                        ds.dimension_name,
                        ds.mean,
                        ds.std_dev,
                        json.dumps(ds.question_indices),
                    ),
                )
            conn.commit()
        logger.info("Saved %d dimension scores for survey_id=%s", len(scores), survey_id)

    def get_dimension_scores(self, survey_id: int) -> list[DimensionScore]:
        """Retrieve dimension scores for a survey."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, survey_id, dimension_name, mean, std_dev, question_indices "
                "FROM dimension_scores WHERE survey_id=?",
                (survey_id,),
            ).fetchall()
        result = []
        for row in rows:
            result.append(
                DimensionScore(
                    id=row[0],
                    survey_id=row[1],
                    dimension_name=row[2],
                    mean=row[3],
                    std_dev=row[4],
                    question_indices=json.loads(row[5]),
                )
            )
        return result

    def get_all_dimension_scores(
        self, department: str | None = None
    ) -> list[DimensionScore]:
        """Retrieve dimension scores across all surveys, optionally filtered by department."""
        if department:
            sql = """
                SELECT ds.id, ds.survey_id, ds.dimension_name, ds.mean, ds.std_dev,
                       ds.question_indices
                FROM dimension_scores ds
                JOIN surveys s ON s.id = ds.survey_id
                WHERE s.department = ?
            """
            params: list[Any] = [department]
        else:
            sql = """
                SELECT id, survey_id, dimension_name, mean, std_dev, question_indices
                FROM dimension_scores
            """
            params = []
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            DimensionScore(
                id=row[0],
                survey_id=row[1],
                dimension_name=row[2],
                mean=row[3],
                std_dev=row[4],
                question_indices=json.loads(row[5]),
            )
            for row in rows
        ]

    # ------------------------------------------------------------------ #
    #  QAAlert CRUD
    # ------------------------------------------------------------------ #

    def save_alerts(self, alerts: list[QAAlert]) -> None:
        """Replace all alerts for a survey with the provided list."""
        if not alerts:
            return
        survey_id = alerts[0].survey_id
        with self._connect() as conn:
            conn.execute("DELETE FROM qa_alerts WHERE survey_id=?", (survey_id,))
            for a in alerts:
                conn.execute(
                    """INSERT INTO qa_alerts
                       (survey_id, alert_type, dimension_name, question_index,
                        value, threshold, message, severity, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        a.survey_id, a.alert_type, a.dimension_name,
                        a.question_index, a.value, a.threshold,
                        a.message, a.severity, a.created_at,
                    ),
                )
            conn.commit()
        logger.info("Saved %d QA alerts for survey_id=%s", len(alerts), survey_id)

    def get_alerts(self, survey_id: int) -> list[QAAlert]:
        """Retrieve all QA alerts for a survey."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT id, survey_id, alert_type, dimension_name, question_index,
                          value, threshold, message, severity, created_at
                   FROM qa_alerts WHERE survey_id=?
                   ORDER BY severity DESC, created_at""",
                (survey_id,),
            ).fetchall()
        return [
            QAAlert(
                id=row[0],
                survey_id=row[1],
                alert_type=row[2],
                dimension_name=row[3],
                question_index=row[4],
                value=row[5],
                threshold=row[6],
                message=row[7],
                severity=row[8],
                created_at=row[9],
            )
            for row in rows
        ]
