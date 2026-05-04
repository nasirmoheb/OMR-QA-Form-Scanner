"""Unit tests for the DataStore class."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd
import pytest

from data_store import DataStore


def sample_result(form_id: str = "form_001", valid: bool = True) -> dict:
    """Generate a minimal valid result dict for 14 questions."""
    base = {f"Q{i}": "Yes" for i in range(1, 15)}
    base.update({"Form_ID": form_id, "Form_Score": 100.0, "Valid": valid})
    return base


@pytest.fixture(autouse=True)
def reset_store():
    """Ensure each test starts with a clean DataStore."""
    DataStore.reset()
    yield


class TestDataStoreInitialization:
    def test_empty_dataframe_has_expected_columns(self):
        df = DataStore.get_results_dataframe()
        expected = ["Form_ID"] + [f"Q{i}" for i in range(1, 15)] + ["Form_Score", "Valid"]
        assert list(df.columns) == expected
        assert len(df) == 0

    def test_get_valid_forms_returns_empty_when_no_data(self):
        df = DataStore.get_valid_forms()
        assert len(df) == 0

    def test_batch_totals_empty(self):
        totals = DataStore.get_batch_totals()
        assert totals == {
            "total_forms": 0,
            "valid_forms": 0,
            "invalid_forms": 0,
            "average_score": 0.0,
            "average_score_valid": 0.0,
        }


class TestDataStoreAddAndRetrieve:
    def test_add_single_result(self):
        DataStore.add_form_result(sample_result("form_001"))
        df = DataStore.get_results_dataframe()
        assert len(df) == 1
        assert df.iloc[0]["Form_ID"] == "form_001"

    def test_add_multiple_results(self):
        for i in range(3):
            DataStore.add_form_result(sample_result(f"form_{i:03d}"))
        df = DataStore.get_results_dataframe()
        assert len(df) == 3

    def test_get_valid_forms_filters_correctly(self):
        DataStore.add_form_result(sample_result("valid_1", valid=True))
        DataStore.add_form_result(sample_result("invalid_1", valid=False))
        valid_df = DataStore.get_valid_forms()
        assert len(valid_df) == 1
        assert valid_df.iloc[0]["Form_ID"] == "valid_1"


class TestDataStoreBatchTotals:
    def test_totals_after_mixed_validity(self):
        DataStore.add_form_result(sample_result("v1", valid=True))
        DataStore.add_form_result(sample_result("v2", valid=True))
        DataStore.add_form_result(sample_result("i1", valid=False))
        totals = DataStore.get_batch_totals()
        assert totals["total_forms"] == 3
        assert totals["valid_forms"] == 2
        assert totals["invalid_forms"] == 1

    def test_average_scores(self):
        r1 = sample_result("v1", valid=True)
        r1["Form_Score"] = 80.0
        r2 = sample_result("v2", valid=True)
        r2["Form_Score"] = 100.0
        DataStore.add_form_result(r1)
        DataStore.add_form_result(r2)
        totals = DataStore.get_batch_totals()
        assert totals["average_score"] == pytest.approx(90.0)
        assert totals["average_score_valid"] == pytest.approx(90.0)

    def test_average_with_invalid_counts_as_zero(self):
        r1 = sample_result("v1", valid=True)
        r1["Form_Score"] = 100.0
        r2 = sample_result("i1", valid=False)
        r2["Form_Score"] = 0.0
        DataStore.add_form_result(r1)
        DataStore.add_form_result(r2)
        totals = DataStore.get_batch_totals()
        assert totals["average_score"] == pytest.approx(50.0)
        assert totals["average_score_valid"] == pytest.approx(100.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
