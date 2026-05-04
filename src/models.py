"""Domain models for the OMR QA Form Scanner."""

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
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> Survey:
        """Construct from an sqlite3 row tuple.

        Expected column order:
        id, university, faculty, department, subject, professor,
        semester, academic_year, status, created_at, updated_at
        """
        return cls(
            id=row[0],
            university=row[1],
            faculty=row[2],
            department=row[3],
            subject=row[4],
            professor=row[5],
            semester=row[6],
            academic_year=row[7],
            status=row[8],
            created_at=row[9],
            updated_at=row[10],
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
    def from_row(cls, row: tuple) -> FormResult:
        """Construct from an sqlite3 row tuple.

        Expected column order:
        id, survey_id, form_id, image_path,
        q1..q14, form_score, valid, confidence, manually_corrected
        """
        return cls(
            id=row[0],
            survey_id=row[1],
            form_id=row[2],
            image_path=row[3],
            q1=row[4], q2=row[5], q3=row[6], q4=row[7],
            q5=row[8], q6=row[9], q7=row[10], q8=row[11],
            q9=row[12], q10=row[13], q11=row[14], q12=row[15],
            q13=row[16], q14=row[17],
            form_score=row[18],
            valid=bool(row[19]),
            confidence=row[20],
            manually_corrected=bool(row[21]),
        )
