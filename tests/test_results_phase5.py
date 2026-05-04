"""Tests for Phase 5 — Results Visualization & Export.

Covers:
- AnalyticsEngine.export_csv: file creation, columns, row count, counts, labels
- AnalyticsEngine.export_pdf_report: file creation, valid PDF, missing reportlab
- AnalyticsEngine.get_trend_data: current survey, matching surveys, exclusions, sorting

NOTE: customtkinter is NOT imported here — only analytics methods are tested.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure src/ is on the path when running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analytics_engine import AnalyticsEngine
from models import FormResult, Survey
from persistence import PersistenceManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_survey(
    subject: str = "Math",
    professor: str = "Dr. Ali",
    semester: str = "1",
    academic_year: str = "2024-2025",
    **kwargs,
) -> Survey:
    defaults = dict(
        university="Test University",
        faculty="Engineering",
        department="CS",
        subject=subject,
        professor=professor,
        semester=semester,
        academic_year=academic_year,
        status="Processed",
    )
    defaults.update(kwargs)
    return Survey(**defaults)


def _make_form_result(
    survey_id: int,
    form_id: str = "form_001",
    answers: list[str] | None = None,
    form_score: float = 75.0,
    valid: bool = True,
) -> FormResult:
    """Create a FormResult with specified or default answers."""
    if answers is None:
        answers = ["Yes"] * 14
    assert len(answers) == 14, "answers must have exactly 14 items"
    return FormResult(
        survey_id=survey_id,
        form_id=form_id,
        image_path="/tmp/test.jpg",
        q1=answers[0],
        q2=answers[1],
        q3=answers[2],
        q4=answers[3],
        q5=answers[4],
        q6=answers[5],
        q7=answers[6],
        q8=answers[7],
        q9=answers[8],
        q10=answers[9],
        q11=answers[10],
        q12=answers[11],
        q13=answers[12],
        q14=answers[13],
        form_score=form_score,
        valid=valid,
    )


@pytest.fixture
def persistence(tmp_path: Path) -> PersistenceManager:
    """Return a PersistenceManager backed by a temporary SQLite database."""
    db_path = tmp_path / "test_phase5.db"
    return PersistenceManager(db_path=db_path)


@pytest.fixture
def engine() -> AnalyticsEngine:
    """Return a fresh AnalyticsEngine."""
    return AnalyticsEngine()


# ---------------------------------------------------------------------------
# TestExportCsv
# ---------------------------------------------------------------------------


class TestExportCsv:
    """Tests for AnalyticsEngine.export_csv."""

    def _make_results(self, survey_id: int = 1) -> list[FormResult]:
        return [
            _make_form_result(survey_id, "f1", ["Yes"] * 14),
            _make_form_result(survey_id, "f2", ["No"] * 14),
            _make_form_result(survey_id, "f3", ["Somewhat"] * 14),
        ]

    def test_export_csv_creates_file(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """export_csv must create a file at the given path."""
        out = tmp_path / "results.csv"
        results = self._make_results()
        engine.export_csv(results, out)
        assert out.exists(), "CSV file was not created"
        assert out.stat().st_size > 0

    def test_export_csv_has_correct_columns(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """CSV header must contain all required column names."""
        out = tmp_path / "results.csv"
        results = self._make_results()
        engine.export_csv(results, out)

        with open(out, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or []

        expected = [
            "QuestionNumber",
            "QuestionText",
            "Count_Yes",
            "Count_No",
            "Count_Somewhat",
            "Count_Invalid",
            "TotalResponses",
        ]
        for col in expected:
            assert col in fieldnames, f"Missing column: {col}"

    def test_export_csv_has_14_rows(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """CSV must have exactly 14 data rows (one per question)."""
        out = tmp_path / "results.csv"
        results = self._make_results()
        engine.export_csv(results, out)

        with open(out, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        assert len(rows) == 14, f"Expected 14 rows, got {len(rows)}"

    def test_export_csv_counts_correctly(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """Counts in the CSV must match the actual answer distribution."""
        out = tmp_path / "results.csv"
        # 2 forms: first all Yes, second all No
        results = [
            _make_form_result(1, "f1", ["Yes"] * 14),
            _make_form_result(1, "f2", ["No"] * 14),
        ]
        engine.export_csv(results, out)

        with open(out, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        # Every question should have Count_Yes=1, Count_No=1, others=0
        for row in rows:
            assert int(row["Count_Yes"]) == 1, f"Q{row['QuestionNumber']}: expected Count_Yes=1"
            assert int(row["Count_No"]) == 1, f"Q{row['QuestionNumber']}: expected Count_No=1"
            assert int(row["Count_Somewhat"]) == 0
            assert int(row["Count_Invalid"]) == 0
            assert int(row["TotalResponses"]) == 2

    def test_export_csv_uses_question_texts(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """When question_texts is provided (len==14), QuestionText column uses them."""
        out = tmp_path / "results.csv"
        results = self._make_results()
        q_texts = [f"Custom Q{i + 1}" for i in range(14)]
        engine.export_csv(results, out, question_texts=q_texts)

        with open(out, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        for i, row in enumerate(rows):
            assert row["QuestionText"] == q_texts[i], (
                f"Row {i}: expected '{q_texts[i]}', got '{row['QuestionText']}'"
            )

    def test_export_csv_fallback_labels(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """When question_texts is None, QuestionText column uses Q1..Q14."""
        out = tmp_path / "results.csv"
        results = self._make_results()
        engine.export_csv(results, out, question_texts=None)

        with open(out, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)

        for i, row in enumerate(rows):
            expected = f"Q{i + 1}"
            assert row["QuestionText"] == expected, (
                f"Row {i}: expected '{expected}', got '{row['QuestionText']}'"
            )


# ---------------------------------------------------------------------------
# TestExportPdfReport
# ---------------------------------------------------------------------------


class TestExportPdfReport:
    """Tests for AnalyticsEngine.export_pdf_report."""

    def _make_survey_obj(self) -> Survey:
        return _make_survey()

    def _make_results(self, survey_id: int = 1) -> list[FormResult]:
        return [
            _make_form_result(survey_id, "f1", ["Yes"] * 14, form_score=90.0),
            _make_form_result(survey_id, "f2", ["No"] * 14, form_score=10.0),
        ]

    def test_export_pdf_creates_file(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """export_pdf_report must create a file at the given path."""
        out = tmp_path / "report.pdf"
        survey = self._make_survey_obj()
        results = self._make_results()
        engine.export_pdf_report(survey, results, out)
        assert out.exists(), "PDF file was not created"
        assert out.stat().st_size > 0

    def test_export_pdf_is_valid_pdf(self, engine: AnalyticsEngine, tmp_path: Path) -> None:
        """The generated file must start with the PDF magic bytes (%PDF)."""
        out = tmp_path / "report.pdf"
        survey = self._make_survey_obj()
        results = self._make_results()
        engine.export_pdf_report(survey, results, out)

        with open(out, "rb") as fh:
            magic = fh.read(4)
        assert magic == b"%PDF", f"File does not start with %PDF magic bytes: {magic!r}"

    def test_export_pdf_raises_without_reportlab(
        self, engine: AnalyticsEngine, tmp_path: Path
    ) -> None:
        """RuntimeError must be raised when reportlab is not available."""
        out = tmp_path / "report.pdf"
        survey = self._make_survey_obj()
        results = self._make_results()

        # Simulate reportlab being unavailable by patching the import
        import builtins
        real_import = builtins.__import__

        def mock_import(name: str, *args, **kwargs):
            if name.startswith("reportlab"):
                raise ImportError("No module named 'reportlab'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError, match="reportlab"):
                engine.export_pdf_report(survey, results, out)


# ---------------------------------------------------------------------------
# TestGetTrendData
# ---------------------------------------------------------------------------


class TestGetTrendData:
    """Tests for AnalyticsEngine.get_trend_data."""

    def _create_survey_with_results(
        self,
        persistence: PersistenceManager,
        subject: str = "Math",
        professor: str = "Dr. Ali",
        semester: str = "1",
        academic_year: str = "2024-2025",
        n_forms: int = 2,
    ) -> Survey:
        """Helper: create a survey and add form results to it."""
        survey = _make_survey(
            subject=subject,
            professor=professor,
            semester=semester,
            academic_year=academic_year,
        )
        survey = persistence.create_survey(survey)
        for i in range(n_forms):
            fr = _make_form_result(survey.id, f"form_{i:03d}", form_score=75.0)
            persistence.create_form_result(fr)
        return survey

    def test_get_trend_data_returns_current_survey(
        self, engine: AnalyticsEngine, persistence: PersistenceManager
    ) -> None:
        """get_trend_data must include the current survey in the results."""
        survey = self._create_survey_with_results(persistence)
        trend = engine.get_trend_data(survey, persistence)
        survey_ids = [d["survey_id"] for d in trend]
        assert survey.id in survey_ids, "Current survey not found in trend data"

    def test_get_trend_data_finds_matching_surveys(
        self, engine: AnalyticsEngine, persistence: PersistenceManager
    ) -> None:
        """get_trend_data must find surveys with the same subject and professor."""
        s1 = self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Ali", academic_year="2023-2024"
        )
        s2 = self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Ali", academic_year="2024-2025"
        )
        # Different subject — should NOT appear
        self._create_survey_with_results(
            persistence, subject="Physics", professor="Dr. Ali", academic_year="2024-2025"
        )
        # Different professor — should NOT appear
        self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Babar", academic_year="2024-2025"
        )

        trend = engine.get_trend_data(s1, persistence)
        survey_ids = {d["survey_id"] for d in trend}
        assert s1.id in survey_ids, "Survey 1 not found in trend data"
        assert s2.id in survey_ids, "Survey 2 not found in trend data"
        assert len(survey_ids) == 2, f"Expected 2 matching surveys, got {len(survey_ids)}"

    def test_get_trend_data_excludes_no_results(
        self, engine: AnalyticsEngine, persistence: PersistenceManager
    ) -> None:
        """get_trend_data must exclude surveys that have no form results."""
        # Survey with results
        s_with = self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Ali", n_forms=2
        )
        # Survey without results
        s_without = _make_survey(subject="Math", professor="Dr. Ali", academic_year="2022-2023")
        s_without = persistence.create_survey(s_without)

        trend = engine.get_trend_data(s_with, persistence)
        survey_ids = {d["survey_id"] for d in trend}
        assert s_with.id in survey_ids, "Survey with results should be included"
        assert s_without.id not in survey_ids, "Survey without results should be excluded"

    def test_get_trend_data_sorted_by_year(
        self, engine: AnalyticsEngine, persistence: PersistenceManager
    ) -> None:
        """get_trend_data results must be sorted by academic_year."""
        s_2025 = self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Ali", academic_year="2025-2026"
        )
        s_2023 = self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Ali", academic_year="2023-2024"
        )
        s_2024 = self._create_survey_with_results(
            persistence, subject="Math", professor="Dr. Ali", academic_year="2024-2025"
        )

        trend = engine.get_trend_data(s_2025, persistence)
        years = [d["academic_year"] for d in trend]
        assert years == sorted(years), f"Trend data not sorted by academic_year: {years}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
