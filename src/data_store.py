"""Data layer for storing and querying OMR form results."""

from typing import Any

import pandas as pd

from config import Config


class DataStore:
    """Class-level DataFrame backed store for form processing results."""

    _df: pd.DataFrame | None = None

    @classmethod
    def _ensure_initialized(cls) -> None:
        """Create the empty DataFrame if it does not yet exist."""
        if cls._df is None:
            question_cols = [f"Q{i}" for i in range(1, Config.ROW_COUNT + 1)]
            cls._df = pd.DataFrame(
                columns=["Form_ID", *question_cols, "Form_Score", "Valid"]
            )

    @classmethod
    def add_form_result(cls, result: dict[str, Any]) -> None:
        """Append a single form result to the store.

        Args:
            result: Dictionary containing at least Form_ID, Q1..Q14,
                    Form_Score and Valid keys.
        """
        cls._ensure_initialized()
        cls._df = pd.concat(
            [cls._df, pd.DataFrame([result])], ignore_index=True
        )

    @classmethod
    def get_results_dataframe(cls) -> pd.DataFrame:
        """Return the full results DataFrame.

        Returns:
            Copy of the internal DataFrame (may be empty).
        """
        cls._ensure_initialized()
        return cls._df.copy()

    @classmethod
    def get_valid_forms(cls) -> pd.DataFrame:
        """Return only rows marked as valid.

        Returns:
            Filtered DataFrame copy where ``Valid`` is True.
        """
        cls._ensure_initialized()
        return cls._df[cls._df["Valid"] == True].copy()

    @classmethod
    def get_batch_totals(cls) -> dict[str, Any]:
        """Calculate batch-level aggregate statistics.

        Returns:
            Dictionary with total_forms, valid_forms, invalid_forms,
            average_score and average_score_valid.
        """
        cls._ensure_initialized()
        total = len(cls._df)
        valid_df = cls._df[cls._df["Valid"] == True]
        valid = len(valid_df)
        invalid = total - valid

        avg_score = (
            cls._df["Form_Score"].mean() if total > 0 else 0.0
        )
        avg_score_valid = (
            valid_df["Form_Score"].mean() if valid > 0 else 0.0
        )

        return {
            "total_forms": total,
            "valid_forms": valid,
            "invalid_forms": invalid,
            "average_score": float(avg_score) if pd.notna(avg_score) else 0.0,
            "average_score_valid": (
                float(avg_score_valid) if pd.notna(avg_score_valid) else 0.0
            ),
        }

    @classmethod
    def reset(cls) -> None:
        """Clear all stored results (useful between batches)."""
        cls._df = None
        cls._ensure_initialized()
