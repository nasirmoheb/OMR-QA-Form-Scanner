"""Analytics layer: form and batch score calculations."""

from __future__ import annotations

import csv
import tempfile
from datetime import datetime
from pathlib import Path
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

    # ------------------------------------------------------------------ #
    #  CSV export
    # ------------------------------------------------------------------ #

    def export_csv(
        self,
        form_results: list,  # list[FormResult]
        output_path: str | Path,
        question_texts: list[str] | None = None,
    ) -> str:
        """Export a per-question summary table to a CSV file.

        Args:
            form_results: List of ``FormResult`` objects to summarise.
            output_path: Destination file path for the CSV.
            question_texts: Optional list of 14 question text strings.
                When provided and ``len == 14``, used as the QuestionText
                column; otherwise falls back to ``Q1``..``Q14``.

        Returns:
            The output path as a string.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        headers = [
            "QuestionNumber",
            "QuestionText",
            "Count_Yes",
            "Count_No",
            "Count_Somewhat",
            "Count_Invalid",
            "TotalResponses",
        ]

        rows = []
        for i in range(14):
            q_num = i + 1
            q_text = (
                question_texts[i]
                if question_texts is not None and len(question_texts) == 14
                else f"Q{q_num}"
            )
            count_yes = sum(1 for fr in form_results if fr.answers()[i] == "Yes")
            count_no = sum(1 for fr in form_results if fr.answers()[i] == "No")
            count_somewhat = sum(1 for fr in form_results if fr.answers()[i] == "Somewhat")
            count_invalid = sum(1 for fr in form_results if fr.answers()[i] == "Invalid")
            total = count_yes + count_no + count_somewhat + count_invalid
            rows.append([q_num, q_text, count_yes, count_no, count_somewhat, count_invalid, total])

        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(rows)

        logger.info("CSV exported to %s", output_path)
        return str(output_path)

    # ------------------------------------------------------------------ #
    #  PDF report export
    # ------------------------------------------------------------------ #

    def export_pdf_report(
        self,
        survey: Any,  # Survey dataclass
        form_results: list,  # list[FormResult]
        output_path: str | Path,
        question_texts: list[str] | None = None,
    ) -> str:
        """Generate a printable PDF report using reportlab.

        Args:
            survey: ``Survey`` dataclass instance with metadata.
            form_results: List of ``FormResult`` objects.
            output_path: Destination file path for the PDF.
            question_texts: Optional list of 14 question text strings.

        Returns:
            The output path as a string.

        Raises:
            RuntimeError: When reportlab is not installed.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import cm
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )
        except ImportError as exc:
            raise RuntimeError(
                "reportlab is required for PDF export. "
                "Install it with: pip install reportlab"
            ) from exc

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # --- Title ---
        title_style = styles["Heading1"]
        story.append(Paragraph("Survey Results Report", title_style))
        story.append(Spacer(1, 0.4 * cm))

        # --- Survey metadata card ---
        meta_lines = [
            f"<b>Subject:</b> {getattr(survey, 'subject', '')}",
            f"<b>Professor:</b> {getattr(survey, 'professor', '')}",
            f"<b>Semester:</b> {getattr(survey, 'semester', '')}",
            f"<b>Academic Year:</b> {getattr(survey, 'academic_year', '')}",
            f"<b>University:</b> {getattr(survey, 'university', '')}",
        ]
        for line in meta_lines:
            story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

        # --- Summary stats ---
        form_count = len(form_results)
        if form_count > 0:
            batch_score = sum(fr.form_score for fr in form_results) / form_count
        else:
            batch_score = 0.0

        story.append(Paragraph(f"<b>Forms Processed:</b> {form_count}", styles["Normal"]))
        story.append(Paragraph(f"<b>Batch Score:</b> {batch_score:.1f}%", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

        # --- Summary table ---
        table_data = [
            ["Q#", "Question Text", "Yes", "No", "Somewhat", "Invalid", "Total"],
        ]
        for i in range(14):
            q_num = i + 1
            q_text = (
                question_texts[i]
                if question_texts is not None and len(question_texts) == 14
                else f"Q{q_num}"
            )
            count_yes = sum(1 for fr in form_results if fr.answers()[i] == "Yes")
            count_no = sum(1 for fr in form_results if fr.answers()[i] == "No")
            count_somewhat = sum(1 for fr in form_results if fr.answers()[i] == "Somewhat")
            count_invalid = sum(1 for fr in form_results if fr.answers()[i] == "Invalid")
            total = count_yes + count_no + count_somewhat + count_invalid
            table_data.append([str(q_num), q_text, count_yes, count_no, count_somewhat, count_invalid, total])

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A90E2")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0F4FF")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 0.6 * cm))

        # --- Footer ---
        gen_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        story.append(Paragraph(f"Generated: {gen_date}", styles["Normal"]))

        doc.build(story)
        logger.info("PDF report exported to %s", output_path)
        return str(output_path)

    # ------------------------------------------------------------------ #
    #  Trend data
    # ------------------------------------------------------------------ #

    def get_trend_data(
        self,
        survey: Any,  # Survey dataclass
        persistence: Any,  # PersistenceManager
    ) -> list[dict]:
        """Find all surveys with the same subject and professor and return trend data.

        Args:
            survey: The current ``Survey`` dataclass instance.
            persistence: A ``PersistenceManager`` instance.

        Returns:
            List of dicts with keys: ``survey_id``, ``semester``,
            ``academic_year``, ``batch_score``, ``form_count``.
            Sorted by ``academic_year`` then ``semester``.
            Excludes surveys with no form results.
        """
        subject = (getattr(survey, "subject", "") or "").lower().strip()
        professor = (getattr(survey, "professor", "") or "").lower().strip()

        all_surveys = persistence.list_surveys()
        trend: list[dict] = []

        for s in all_surveys:
            s_subject = (getattr(s, "subject", "") or "").lower().strip()
            s_professor = (getattr(s, "professor", "") or "").lower().strip()
            if s_subject != subject or s_professor != professor:
                continue

            form_results = persistence.get_form_results(s.id)
            if not form_results:
                continue

            form_count = len(form_results)
            batch_score = (
                sum(fr.form_score for fr in form_results) / form_count
                if form_count > 0
                else 0.0
            )
            trend.append(
                {
                    "survey_id": s.id,
                    "semester": s.semester,
                    "academic_year": s.academic_year,
                    "batch_score": batch_score,
                    "form_count": form_count,
                }
            )

        trend.sort(key=lambda d: (d["academic_year"], d["semester"]))
        logger.info("Trend data: %d matching surveys found", len(trend))
        return trend
