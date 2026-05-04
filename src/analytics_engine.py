"""Analytics layer: form and batch score calculations."""

from __future__ import annotations

from typing import Any

import pandas as pd

from config import Config, setup_logging
from data_store import DataStore

logger = setup_logging()


class AnalyticsEngine:
    """Computes form scores, batch scores, and coordinates report generation."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize with configuration.

        Args:
            config: Application configuration. Uses global defaults when
                ``None``.
        """
        self.config = config or Config()

    # ------------------------------------------------------------------ #
    #  Form score
    # ------------------------------------------------------------------ #

    def calculate_form_score(self, answers: list[str]) -> float:
        """Compute the satisfaction score for a single form.

        Formula::

            ((Yes × 100) + (Somewhat × 50) + (No × 0)) / Total_Valid_Questions

        Args:
            answers: 14 answer strings (``"Yes"``, ``"Somewhat"``,
                ``"No"``, ``"Invalid"``).

        Returns:
            Score in ``[0.0, 100.0]``. Returns ``0.0`` when no answers are
            valid.
        """
        weights = {
            "Yes": self.config.SCORE_YES,
            "Somewhat": self.config.SCORE_SOMEWHAT,
            "No": self.config.SCORE_NO,
        }
        valid = [a for a in answers if a in weights]
        if not valid:
            return 0.0
        total = sum(weights[a] for a in valid)
        return total / len(valid)

    # ------------------------------------------------------------------ #
    #  Batch score
    # ------------------------------------------------------------------ #

    def calculate_batch_score(self, df: pd.DataFrame | None = None) -> float:
        """Compute the average form score across the batch.

        Invalid forms contribute ``0.0`` to the average.

        Args:
            df: Results DataFrame. When ``None`` the current DataStore
                contents are used.

        Returns:
            Batch score in ``[0.0, 100.0]``. Returns ``0.0`` for an empty
            batch.
        """
        if df is None:
            df = DataStore.get_results_dataframe()

        if df.empty:
            return 0.0

        # Include all rows; invalid forms already have Form_Score == 0.0
        scores = df["Form_Score"].fillna(0.0)
        return float(scores.mean())

    # ------------------------------------------------------------------ #
    #  Report generation (delegates to PlotlyGenerator)
    # ------------------------------------------------------------------ #

    def generate_report(
        self, df: pd.DataFrame | None = None, output_path: str | None = None,
        question_texts: list[str] | None = None,
    ) -> str:
        """Generate a Plotly HTML dashboard report.

        Args:
            df: Results DataFrame. Uses DataStore when ``None``.
            output_path: File path to write the HTML report. When ``None`` a
                temporary path is chosen.
            question_texts: Optional list of 14 question text strings to use
                as chart labels instead of Q1..Q14.

        Returns:
            Absolute path to the generated HTML file.
        """
        # Lazy import to avoid a hard dependency at module load time.
        from plotly_generator import PlotlyGenerator

        if df is None:
            df = DataStore.get_results_dataframe()

        batch_score = self.calculate_batch_score(df)
        logger.info("Batch score: %.2f", batch_score)

        html = PlotlyGenerator.generate_dashboard_html(df, batch_score, question_texts=question_texts)

        if output_path is None:
            output_path = str(
                self.config.PROJECT_ROOT / "assets" / "report.html"
            )

        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(html)

        logger.info("Report written to %s", output_path)
        return output_path
