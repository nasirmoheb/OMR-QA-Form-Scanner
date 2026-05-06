"""Unit tests for AnalyticsEngine and PlotlyGenerator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import pytest

from analytics_engine import AnalyticsEngine
from config import Config
from data_store import DataStore
from plotly_generator import PlotlyGenerator


# ------------------------------------------------------------------ #
#  Fixtures
# ------------------------------------------------------------------ #


@pytest.fixture(autouse=True)
def reset_store():
    DataStore.reset()
    yield


@pytest.fixture
def sample_dataframe() -> pd.DataFrame:
    """Return a small DataFrame with known answers."""
    rows = [
        {
            "Form_ID": "form_001",
            **{f"Q{i}": "Yes" for i in range(1, 15)},
            "Form_Score": 100.0,
            "Valid": True,
        },
        {
            "Form_ID": "form_002",
            **{f"Q{i}": "No" for i in range(1, 15)},
            "Form_Score": 0.0,
            "Valid": True,
        },
        {
            "Form_ID": "form_003",
            **{f"Q{i}": "Invalid" for i in range(1, 15)},
            "Form_Score": 0.0,
            "Valid": False,
        },
    ]
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ #
#  AnalyticsEngine — form score
# ------------------------------------------------------------------ #


class TestCalculateFormScore:
    def test_all_yes(self):
        engine = AnalyticsEngine()
        score = engine.calculate_form_score(["Yes"] * 14)
        assert score == 100.0

    def test_all_no(self):
        engine = AnalyticsEngine()
        score = engine.calculate_form_score(["No"] * 14)
        assert score == 0.0

    def test_all_somewhat(self):
        engine = AnalyticsEngine()
        score = engine.calculate_form_score(["Somewhat"] * 14)
        assert score == 50.0

    def test_mixed(self):
        engine = AnalyticsEngine()
        answers = ["Yes", "Somewhat", "No", "Invalid"] * 3 + ["Yes", "Somewhat"]
        score = engine.calculate_form_score(answers)
        # 3*(100+50+0) + 100 + 50 = 600 over 11 valid
        assert score == pytest.approx(600 / 11, abs=0.01)

    def test_all_invalid(self):
        engine = AnalyticsEngine()
        score = engine.calculate_form_score(["Invalid"] * 14)
        assert score == 0.0

    def test_empty_list(self):
        engine = AnalyticsEngine()
        score = engine.calculate_form_score([])
        assert score == 0.0


# ------------------------------------------------------------------ #
#  AnalyticsEngine — batch score
# ------------------------------------------------------------------ #


class TestCalculateBatchScore:
    def test_empty_batch(self):
        engine = AnalyticsEngine()
        assert engine.calculate_batch_score() == 0.0

    def test_all_valid(self, sample_dataframe):
        engine = AnalyticsEngine()
        valid_df = sample_dataframe[sample_dataframe["Valid"] == True]
        score = engine.calculate_batch_score(valid_df)
        # (100 + 0) / 2 = 50
        assert score == 50.0

    def test_with_invalid_counted_as_zero(self, sample_dataframe):
        engine = AnalyticsEngine()
        score = engine.calculate_batch_score(sample_dataframe)
        # (100 + 0 + 0) / 3 = 33.33...
        assert score == pytest.approx(100 / 3, abs=0.01)

    def test_uses_datastore_when_none(self):
        engine = AnalyticsEngine()
        DataStore.add_form_result(
            {
                "Form_ID": "f1",
                **{f"Q{i}": "Yes" for i in range(1, 15)},
                "Form_Score": 100.0,
                "Valid": True,
            }
        )
        DataStore.add_form_result(
            {
                "Form_ID": "f2",
                **{f"Q{i}": "No" for i in range(1, 15)},
                "Form_Score": 0.0,
                "Valid": True,
            }
        )
        assert engine.calculate_batch_score() == 50.0


# ------------------------------------------------------------------ #
#  AnalyticsEngine — report generation
# ------------------------------------------------------------------ #


class TestGenerateReport:
    def test_generates_html_file(self, tmp_path, sample_dataframe):
        engine = AnalyticsEngine()
        out = tmp_path / "report.html"
        path = engine.generate_report(sample_dataframe, output_path=str(out))
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "Tadris QA Report" in content
        assert "Overall Satisfaction Score" in content
        assert "plotly" in content


# ------------------------------------------------------------------ #
#  PlotlyGenerator — charts
# ------------------------------------------------------------------ #


class TestPlotlyGenerator:
    def test_stacked_bar_returns_figure(self, sample_dataframe):
        fig = PlotlyGenerator.create_stacked_bar_chart(sample_dataframe)
        assert fig is not None
        assert len(fig.data) == 4  # Yes, Somewhat, No, Invalid

    def test_pie_chart_returns_figure(self, sample_dataframe):
        fig = PlotlyGenerator.create_pie_chart(sample_dataframe)
        assert fig is not None
        assert len(fig.data) == 1
        assert fig.data[0].type == "pie"

    def test_score_display_returns_figure(self):
        fig = PlotlyGenerator.create_score_display(73.5)
        assert fig is not None
        assert fig.data[0].type == "indicator"

    def test_dashboard_html_contains_all_sections(self, sample_dataframe):
        html = PlotlyGenerator.generate_dashboard_html(sample_dataframe, 73.5)
        assert "Tadris QA Report" in html
        assert "Overall Satisfaction Score" in html
        assert "Answer Distribution by Question" in html
        assert "Overall Answer Distribution" in html
        assert "<script src=\"https://cdn.plot.ly/plotly-latest.min.js\"></script>" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
