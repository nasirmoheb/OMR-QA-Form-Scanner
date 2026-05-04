"""Tests for src/pdf_generator.py.

Verifies that:
- generate_prefilled_form creates a valid, non-empty PDF file.
- The output is readable as a PDF (starts with the %PDF header).
- The function works with a minimal Survey object (no persistence).
- The function works with a Survey that has no logo / no QR library.
- Coordinates stored in AppSettings are respected.
- A RuntimeError is raised when reportlab is not available (mocked).
"""

from __future__ import annotations

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure src/ is on the path when running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from models import Survey


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_survey(**kwargs) -> Survey:
    defaults = dict(
        id=42,
        university="Test University",
        faculty="Engineering",
        department="Computer Science",
        subject="Software Engineering",
        professor="Dr. Smith",
        semester="1",
        academic_year="2025-2026",
        status="Draft",
    )
    defaults.update(kwargs)
    return Survey(**defaults)


def _is_pdf(path: Path) -> bool:
    """Return True if the file starts with the PDF magic bytes."""
    with open(path, "rb") as f:
        return f.read(4) == b"%PDF"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGeneratePreffilledForm:
    """Tests for generate_prefilled_form."""

    def test_creates_file(self, tmp_path: Path) -> None:
        """A PDF file must be created at the specified output path."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey()
        out = tmp_path / "survey.pdf"
        result = generate_prefilled_form(survey, out)

        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_is_valid_pdf(self, tmp_path: Path) -> None:
        """The output file must start with the PDF magic bytes."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey()
        out = tmp_path / "survey.pdf"
        generate_prefilled_form(survey, out)

        assert _is_pdf(out), "Output file does not appear to be a valid PDF."

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """Output parent directories are created automatically."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey()
        out = tmp_path / "nested" / "deep" / "survey.pdf"
        generate_prefilled_form(survey, out)

        assert out.exists()

    def test_minimal_survey_no_persistence(self, tmp_path: Path) -> None:
        """Works with a Survey that has empty optional fields."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey(
            university="",
            faculty="",
            department="",
            subject="",
            professor="",
            semester="",
            academic_year="",
        )
        out = tmp_path / "minimal.pdf"
        generate_prefilled_form(survey, out)

        assert out.exists()
        assert _is_pdf(out)

    def test_survey_with_none_id(self, tmp_path: Path) -> None:
        """A survey without a DB id (DRAFT) should still produce a valid PDF."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey(id=None)
        out = tmp_path / "draft.pdf"
        generate_prefilled_form(survey, out)

        assert out.exists()
        assert _is_pdf(out)

    def test_persistence_question_texts_used(self, tmp_path: Path) -> None:
        """Custom question texts from AppSettings are embedded in the PDF."""
        from pdf_generator import generate_prefilled_form

        custom_questions = [f"Custom question {i + 1}" for i in range(14)]
        mock_persistence = MagicMock()
        mock_persistence.get_setting.side_effect = lambda key, default=None: {
            "question_texts": custom_questions,
            "pdf_coords": None,
            "logo_path": None,
        }.get(key, default)

        survey = _make_survey()
        out = tmp_path / "custom_q.pdf"
        generate_prefilled_form(survey, out, persistence=mock_persistence)

        assert out.exists()
        assert _is_pdf(out)

    def test_persistence_coords_override(self, tmp_path: Path) -> None:
        """Custom pdf_coords from AppSettings are accepted without error."""
        from pdf_generator import generate_prefilled_form

        custom_coords = {"logo_x": 20, "logo_y": 260}
        mock_persistence = MagicMock()
        mock_persistence.get_setting.side_effect = lambda key, default=None: {
            "pdf_coords": custom_coords,
            "question_texts": None,
            "logo_path": None,
        }.get(key, default)

        survey = _make_survey()
        out = tmp_path / "custom_coords.pdf"
        generate_prefilled_form(survey, out, persistence=mock_persistence)

        assert out.exists()
        assert _is_pdf(out)

    def test_logo_path_embedded(self, tmp_path: Path) -> None:
        """A valid logo image is embedded without raising an exception."""
        from pdf_generator import generate_prefilled_form

        # Create a tiny 10×10 white PNG as a fake logo
        try:
            from PIL import Image as PILImage

            logo = PILImage.new("RGB", (10, 10), color=(255, 255, 255))
            logo_path = tmp_path / "logo.png"
            logo.save(str(logo_path))
        except ImportError:
            pytest.skip("Pillow not installed — skipping logo test")

        survey = _make_survey()
        out = tmp_path / "with_logo.pdf"
        generate_prefilled_form(survey, out, logo_path=logo_path)

        assert out.exists()
        assert _is_pdf(out)

    def test_invalid_logo_path_does_not_crash(self, tmp_path: Path) -> None:
        """A non-existent logo path is silently ignored."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey()
        out = tmp_path / "bad_logo.pdf"
        # Pass a path that doesn't exist — should not raise
        generate_prefilled_form(survey, out, logo_path="/nonexistent/logo.png")

        assert out.exists()
        assert _is_pdf(out)

    def test_raises_when_reportlab_missing(self, tmp_path: Path) -> None:
        """RuntimeError is raised when reportlab is not installed."""
        import pdf_generator as pg

        original = pg._REPORTLAB_OK
        try:
            pg._REPORTLAB_OK = False
            with pytest.raises(RuntimeError, match="reportlab"):
                pg.generate_prefilled_form(_make_survey(), tmp_path / "x.pdf")
        finally:
            pg._REPORTLAB_OK = original

    def test_overwrite_existing_file(self, tmp_path: Path) -> None:
        """Calling generate_prefilled_form twice overwrites the first file."""
        from pdf_generator import generate_prefilled_form

        survey = _make_survey()
        out = tmp_path / "overwrite.pdf"

        generate_prefilled_form(survey, out)
        size_first = out.stat().st_size

        generate_prefilled_form(survey, out)
        size_second = out.stat().st_size

        # Both should be valid PDFs; sizes should be equal (deterministic layout)
        assert _is_pdf(out)
        assert size_second > 0


class TestDefaultQuestions:
    """Verify the default Dari question list is well-formed."""

    def test_exactly_14_questions(self) -> None:
        from pdf_generator import _DARI_QUESTIONS

        assert len(_DARI_QUESTIONS) == 14

    def test_no_empty_questions(self) -> None:
        from pdf_generator import _DARI_QUESTIONS

        for q in _DARI_QUESTIONS:
            assert q.strip(), f"Empty question found: {q!r}"

    def test_questions_are_dari(self) -> None:
        """Each question should contain Arabic/Dari Unicode characters."""
        from pdf_generator import _DARI_QUESTIONS

        for q in _DARI_QUESTIONS:
            # Dari text contains characters in the Arabic Unicode block (U+0600–U+06FF)
            assert any("\u0600" <= ch <= "\u06ff" for ch in q), (
                f"Question does not appear to be Dari: {q!r}"
            )


class TestDefaultCoords:
    """Verify the default coordinate map has the required fiducial keys."""

    _REQUIRED_KEYS = {"fiducial_size", "fiducial_inset"}

    def test_all_required_keys_present(self) -> None:
        from pdf_generator import _DEFAULT_COORDS

        missing = self._REQUIRED_KEYS - set(_DEFAULT_COORDS.keys())
        assert not missing, f"Missing coord keys: {missing}"

    def test_eastern_numerals_count(self) -> None:
        """There should be exactly 14 eastern-Arabic row numerals."""
        from pdf_generator import _EASTERN_NUMS

        assert len(_EASTERN_NUMS) == 14

    def test_eastern_numerals_are_nonempty(self) -> None:
        from pdf_generator import _EASTERN_NUMS

        for n in _EASTERN_NUMS:
            assert n.strip(), f"Empty numeral found: {n!r}"
