"""Tests for Phase 3 — App Settings: Branding & Questions.

Covers:
- Config.QUESTION_TEXTS defaults to empty list
- Config.from_persistence loads question_texts when stored
- Config.from_persistence ignores question_texts if not exactly 14 items
- PlotlyGenerator.create_stacked_bar_chart uses question_texts labels when provided
- PlotlyGenerator.create_stacked_bar_chart falls back to Q1..Q14 when question_texts is None
- PlotlyGenerator.generate_dashboard_html accepts question_texts parameter without error

NOTE: customtkinter is NOT imported here — only Config and PlotlyGenerator are tested.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

# Ensure src/ is on the path when running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config import Config
from plotly_generator import PlotlyGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_persistence(settings: dict) -> MagicMock:
    """Return a MagicMock that behaves like PersistenceManager for settings."""
    mock = MagicMock()
    mock.get_all_settings.return_value = settings
    mock.get_setting.side_effect = lambda key, default=None: settings.get(key, default)
    return mock


def _make_results_df(n_rows: int = 5) -> pd.DataFrame:
    """Create a minimal results DataFrame with Q1..Q14 columns."""
    answers = ["Yes", "Somewhat", "No", "Invalid"]
    data: dict[str, list] = {}
    for i in range(1, 15):
        col = f"Q{i}"
        data[col] = [answers[j % len(answers)] for j in range(n_rows)]
    data["Form_Score"] = [75.0] * n_rows
    return pd.DataFrame(data)


# ---------------------------------------------------------------------------
# Config.QUESTION_TEXTS
# ---------------------------------------------------------------------------

class TestConfigQuestionTexts:
    """Tests for the QUESTION_TEXTS attribute on Config."""

    def test_default_is_empty_list(self) -> None:
        """Config.QUESTION_TEXTS should default to an empty list."""
        cfg = Config()
        assert cfg.QUESTION_TEXTS == []

    def test_class_attribute_is_empty_list(self) -> None:
        """The class-level default should be an empty list."""
        assert Config.QUESTION_TEXTS == []

    def test_from_persistence_loads_14_questions(self) -> None:
        """from_persistence should load question_texts when exactly 14 items are stored."""
        questions = [f"Question {i + 1}" for i in range(14)]
        mock = _make_mock_persistence({"question_texts": questions})
        cfg = Config.from_persistence(mock)
        assert cfg.QUESTION_TEXTS == questions

    def test_from_persistence_ignores_wrong_length_short(self) -> None:
        """from_persistence should ignore question_texts with fewer than 14 items."""
        questions = [f"Q{i}" for i in range(10)]  # only 10
        mock = _make_mock_persistence({"question_texts": questions})
        cfg = Config.from_persistence(mock)
        assert cfg.QUESTION_TEXTS == []

    def test_from_persistence_ignores_wrong_length_long(self) -> None:
        """from_persistence should ignore question_texts with more than 14 items."""
        questions = [f"Q{i}" for i in range(20)]  # 20 items
        mock = _make_mock_persistence({"question_texts": questions})
        cfg = Config.from_persistence(mock)
        assert cfg.QUESTION_TEXTS == []

    def test_from_persistence_ignores_non_list(self) -> None:
        """from_persistence should ignore question_texts that is not a list."""
        mock = _make_mock_persistence({"question_texts": "not a list"})
        cfg = Config.from_persistence(mock)
        assert cfg.QUESTION_TEXTS == []

    def test_from_persistence_ignores_missing(self) -> None:
        """from_persistence should leave QUESTION_TEXTS as [] when key is absent."""
        mock = _make_mock_persistence({})
        cfg = Config.from_persistence(mock)
        assert cfg.QUESTION_TEXTS == []

    def test_save_to_persistence_stores_question_texts(self) -> None:
        """save_to_persistence should call set_setting for question_texts when non-empty."""
        questions = [f"Question {i + 1}" for i in range(14)]
        cfg = Config()
        cfg.QUESTION_TEXTS = questions

        mock = MagicMock()
        cfg.save_to_persistence(mock)

        mock.set_setting.assert_any_call("question_texts", questions)

    def test_save_to_persistence_skips_empty_question_texts(self) -> None:
        """save_to_persistence should NOT call set_setting for question_texts when empty."""
        cfg = Config()
        assert cfg.QUESTION_TEXTS == []

        mock = MagicMock()
        cfg.save_to_persistence(mock)

        # Verify question_texts was never set
        called_keys = [call.args[0] for call in mock.set_setting.call_args_list]
        assert "question_texts" not in called_keys


# ---------------------------------------------------------------------------
# PlotlyGenerator — stacked bar chart labels
# ---------------------------------------------------------------------------

class TestPlotlyGeneratorQuestionTexts:
    """Tests for question_texts label support in PlotlyGenerator."""

    def test_create_stacked_bar_chart_uses_question_texts_labels(self) -> None:
        """create_stacked_bar_chart should use question_texts as x-axis labels."""
        df = _make_results_df()
        labels = [f"Custom Question {i + 1}" for i in range(14)]
        fig = PlotlyGenerator.create_stacked_bar_chart(df, question_texts=labels)

        # All traces should use the custom labels as x values
        for trace in fig.data:
            assert list(trace.x) == labels, (
                f"Expected custom labels but got: {list(trace.x)}"
            )

    def test_create_stacked_bar_chart_truncates_labels_to_40_chars(self) -> None:
        """Labels longer than 40 characters should be truncated."""
        df = _make_results_df()
        long_label = "A" * 60
        labels = [long_label] * 14
        fig = PlotlyGenerator.create_stacked_bar_chart(df, question_texts=labels)

        for trace in fig.data:
            for x_val in trace.x:
                assert len(x_val) <= 40, f"Label not truncated: {x_val!r}"

    def test_create_stacked_bar_chart_falls_back_to_q_labels_when_none(self) -> None:
        """create_stacked_bar_chart should use Q1..Q14 when question_texts is None."""
        df = _make_results_df()
        fig = PlotlyGenerator.create_stacked_bar_chart(df, question_texts=None)

        expected = [f"Q{i}" for i in range(1, 15)]
        for trace in fig.data:
            assert list(trace.x) == expected, (
                f"Expected Q1..Q14 labels but got: {list(trace.x)}"
            )

    def test_create_stacked_bar_chart_falls_back_when_wrong_length(self) -> None:
        """create_stacked_bar_chart should fall back to Q1..Q14 when len != 14."""
        df = _make_results_df()
        short_labels = ["Label A", "Label B"]  # only 2
        fig = PlotlyGenerator.create_stacked_bar_chart(df, question_texts=short_labels)

        expected = [f"Q{i}" for i in range(1, 15)]
        for trace in fig.data:
            assert list(trace.x) == expected

    def test_create_stacked_bar_chart_no_question_texts_arg(self) -> None:
        """create_stacked_bar_chart should work without the question_texts argument."""
        df = _make_results_df()
        fig = PlotlyGenerator.create_stacked_bar_chart(df)

        expected = [f"Q{i}" for i in range(1, 15)]
        for trace in fig.data:
            assert list(trace.x) == expected

    def test_generate_dashboard_html_accepts_question_texts(self) -> None:
        """generate_dashboard_html should accept question_texts without error."""
        df = _make_results_df()
        labels = [f"Survey Q{i + 1}" for i in range(14)]
        html = PlotlyGenerator.generate_dashboard_html(df, 75.0, question_texts=labels)

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert len(html) > 100

    def test_generate_dashboard_html_without_question_texts(self) -> None:
        """generate_dashboard_html should work without question_texts (default None)."""
        df = _make_results_df()
        html = PlotlyGenerator.generate_dashboard_html(df, 80.0)

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_generate_dashboard_html_question_texts_none_explicit(self) -> None:
        """generate_dashboard_html should work with question_texts=None explicitly."""
        df = _make_results_df()
        html = PlotlyGenerator.generate_dashboard_html(df, 60.0, question_texts=None)

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
