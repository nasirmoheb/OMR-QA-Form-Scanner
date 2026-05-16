"""Domain models for the Tadris QA System."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class Survey:
    """A single educational quality survey instance."""

    university: str = ""
    faculty: str = ""
    department: str = ""
    subject: str = ""
    professor: str = ""
    semester: str = ""
    academic_year: str = ""
    date: str = ""
    status: str = "Draft"
    id: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation excluding the internal id."""
        return {
            "university": self.university,
            "faculty": self.faculty,
            "department": self.department,
            "subject": self.subject,
            "professor": self.professor,
            "semester": self.semester,
            "academic_year": self.academic_year,
            "date": self.date,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: Any) -> Survey:
        """Construct from an sqlite3.Row or similar mapping object."""
        # Safer access in case migrations haven't run yet
        cols = row.keys() if hasattr(row, "keys") else []
        return cls(
            id=row["id"],
            university=row["university"],
            faculty=row["faculty"],
            department=row["department"],
            subject=row["subject"],
            professor=row["professor"],
            semester=row["semester"],
            academic_year=row["academic_year"],
            date=row["date"] if "date" in cols else "",
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class FormResult:
    """OMR recognition result for a single scanned form."""

    survey_id: int
    form_id: str
    image_path: str = ""
    q1: str = ""
    q2: str = ""
    q3: str = ""
    q4: str = ""
    q5: str = ""
    q6: str = ""
    q7: str = ""
    q8: str = ""
    q9: str = ""
    q10: str = ""
    q11: str = ""
    q12: str = ""
    q13: str = ""
    q14: str = ""
    form_score: float = 0.0
    valid: bool = False
    confidence: float = 0.0
    manually_corrected: bool = False
    comment: str = ""
    id: int | None = None

    def answers(self) -> list[str]:
        """Return answers Q1..Q14 as a list."""
        return [
            self.q1, self.q2, self.q3, self.q4,
            self.q5, self.q6, self.q7, self.q8,
            self.q9, self.q10, self.q11, self.q12,
            self.q13, self.q14,
        ]

    def to_dict(self) -> dict[str, Any]:
        """Return a dictionary representation."""
        return asdict(self)

    @classmethod
    def from_row(cls, row: Any) -> FormResult:
        """Construct from an sqlite3.Row or similar mapping object."""
        cols = row.keys() if hasattr(row, "keys") else []
        return cls(
            id=row["id"],
            survey_id=row["survey_id"],
            form_id=row["form_id"],
            image_path=row["image_path"],
            q1=row["q1"], q2=row["q2"], q3=row["q3"], q4=row["q4"],
            q5=row["q5"], q6=row["q6"], q7=row["q7"], q8=row["q8"],
            q9=row["q9"], q10=row["q10"], q11=row["q11"], q12=row["q12"],
            q13=row["q13"], q14=row["q14"],
            form_score=row["form_score"],
            valid=bool(row["valid"]),
            confidence=row["confidence"],
            manually_corrected=bool(row["manually_corrected"]),
            comment=row["comment"] if "comment" in cols else "",
        )


@dataclass
class DimensionScore:
    """Aggregated score for a single pedagogical dimension."""

    dimension_name: str
    mean: float
    std_dev: float
    question_indices: list  # 1-based question numbers
    survey_id: int | None = None
    id: int | None = None

    @property
    def status(self) -> str:
        """Return 'good', 'warning', or 'critical' based on mean."""
        if self.mean >= 2.5:
            return "good"
        if self.mean >= 2.2:
            return "warning"
        return "critical"

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension_name": self.dimension_name,
            "mean": self.mean,
            "std_dev": self.std_dev,
            "question_indices": self.question_indices,
            "survey_id": self.survey_id,
        }


@dataclass
class QAAlert:
    """A programmatic QA alert triggered by threshold violations."""

    survey_id: int
    alert_type: str          # "dimension_low", "polarization", "punctuality", "batch_low"
    dimension_name: str = ""
    question_index: int = 0  # 1-based, 0 means N/A
    value: float = 0.0
    threshold: float = 0.0
    message: str = ""
    severity: str = "warning"  # "warning" or "critical"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "survey_id": self.survey_id,
            "alert_type": self.alert_type,
            "dimension_name": self.dimension_name,
            "question_index": self.question_index,
            "value": self.value,
            "threshold": self.threshold,
            "message": self.message,
            "severity": self.severity,
            "created_at": self.created_at,
        }
