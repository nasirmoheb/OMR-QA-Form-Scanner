"""Analytics layer: form and batch score calculations, advanced QA diagnostics."""

from __future__ import annotations

import collections
import csv
import math
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from config import Config, setup_logging
from data_store import DataStore
from models import DimensionScore, FormResult, QAAlert

logger = setup_logging()

# ---------------------------------------------------------------------------
# Simple NLP word lists (no external dependency required)
# ---------------------------------------------------------------------------
_POSITIVE_WORDS = {
    "good", "great", "excellent", "helpful", "clear", "best", "perfect",
    "amazing", "wonderful", "fantastic", "outstanding", "brilliant",
    "effective", "useful", "informative", "engaging", "motivated",
    "خوب", "عالی", "مفید", "واضح", "بهترین",
}
_NEGATIVE_WORDS = {
    "bad", "poor", "slow", "absent", "hard", "difficult", "boring",
    "unclear", "confusing", "late", "missing", "problem", "issue",
    "never", "worst", "terrible", "useless", "waste", "fail",
    "بد", "ضعیف", "غایب", "مشکل", "دیر",
}


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
            # Use writable reports directory instead of Program Files
            reports_dir = self.config.get_reports_dir()
            output_path = str(reports_dir / "report.html")

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
        persistence: Any | None = None,
    ) -> str:
        """Generate a printable PDF report using reportlab.

        Args:
            survey: ``Survey`` dataclass instance with metadata.
            form_results: List of ``FormResult`` objects.
            output_path: Destination file path for the PDF.
            question_texts: Optional list of 14 question text strings.
            persistence: Optional ``PersistenceManager`` for university branding fallback.

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

        # Resolve current university name using setting if available
        current_uni = "پوهنتون بدخشان"
        if persistence:
            current_uni = persistence.get_setting("university_name", Config.DEFAULT_UNIVERSITY_NAME)
        
        survey_uni = (getattr(survey, 'university', '') or "").strip()
        display_uni = survey_uni if (survey_uni and survey_uni != "پوهنتون بدخشان") else current_uni

        # --- Survey metadata card ---
        meta_lines = [
            f"<b>Subject:</b> {getattr(survey, 'subject', '')}",
            f"<b>Professor:</b> {getattr(survey, 'professor', '')}",
            f"<b>Semester:</b> {getattr(survey, 'semester', '')}",
            f"<b>Academic Year:</b> {getattr(survey, 'academic_year', '')}",
            f"<b>Date:</b> {getattr(survey, 'date', '')}",
            f"<b>University:</b> {display_uni}",
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

    # ------------------------------------------------------------------ #
    #  Phase 1 — Likert quantification & score matrix
    # ------------------------------------------------------------------ #

    _LIKERT_MAP = {"Yes": 3, "Somewhat": 2, "No": 1, "Invalid": 0}

    def quantify_likert(self, answers: list[str]) -> list[int]:
        """Map answer strings to Likert integers (Yes=3, Somewhat=2, No=1, Invalid=0).

        Args:
            answers: List of 14 answer strings.

        Returns:
            List of 14 integers.
        """
        return [self._LIKERT_MAP.get(a, 0) for a in answers]

    def build_score_matrix(self, form_results: list[FormResult]) -> pd.DataFrame:
        """Build a numeric Likert matrix from form results.

        Rows = valid forms, columns = Q1..Q14 (integer 0–3).
        Invalid forms (valid=False) are excluded.

        Args:
            form_results: List of FormResult objects.

        Returns:
            DataFrame with columns Q1..Q14 and integer Likert values.
        """
        rows = []
        for fr in form_results:
            if not fr.valid:
                continue
            likert = self.quantify_likert(fr.answers())
            row = {f"Q{i + 1}": v for i, v in enumerate(likert)}
            row["form_id"] = fr.form_id
            rows.append(row)

        if not rows:
            cols = ["form_id"] + [f"Q{i}" for i in range(1, 15)]
            return pd.DataFrame(columns=cols)

        df = pd.DataFrame(rows).set_index("form_id")
        return df

    def flag_invalid_forms(self, form_results: list[FormResult]) -> list[str]:
        """Return form_ids of forms marked invalid.

        Args:
            form_results: List of FormResult objects.

        Returns:
            List of form_id strings for invalid forms.
        """
        return [fr.form_id for fr in form_results if not fr.valid]

    # ------------------------------------------------------------------ #
    #  Phase 2 — Pedagogical dimension scores
    # ------------------------------------------------------------------ #

    def calculate_dimension_scores(
        self,
        score_matrix: pd.DataFrame,
        survey_id: int | None = None,
    ) -> list[DimensionScore]:
        """Compute mean and SD for each pedagogical dimension.

        Args:
            score_matrix: Numeric Likert DataFrame from build_score_matrix().
            survey_id: Optional survey id to embed in the returned objects.

        Returns:
            List of DimensionScore objects, one per dimension.
        """
        results: list[DimensionScore] = []
        for dim_name, q_indices in self.config.DIMENSION_MAP.items():
            cols = [f"Q{i}" for i in q_indices if f"Q{i}" in score_matrix.columns]
            if not cols or score_matrix.empty:
                results.append(
                    DimensionScore(
                        dimension_name=dim_name,
                        mean=0.0,
                        std_dev=0.0,
                        question_indices=q_indices,
                        survey_id=survey_id,
                    )
                )
                continue

            # Only include non-zero (answered) values
            values = score_matrix[cols].values.flatten()
            answered = values[values > 0]
            if len(answered) == 0:
                mean_val = 0.0
                std_val = 0.0
            else:
                mean_val = float(answered.mean())
                std_val = float(answered.std()) if len(answered) > 1 else 0.0

            results.append(
                DimensionScore(
                    dimension_name=dim_name,
                    mean=round(mean_val, 3),
                    std_dev=round(std_val, 3),
                    question_indices=q_indices,
                    survey_id=survey_id,
                )
            )
        return results

    # ------------------------------------------------------------------ #
    #  Phase 3a — Distribution & variance analysis
    # ------------------------------------------------------------------ #

    def calculate_question_stats(
        self, score_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute per-question descriptive statistics.

        Args:
            score_matrix: Numeric Likert DataFrame from build_score_matrix().

        Returns:
            DataFrame indexed by question (Q1..Q14) with columns:
            mean, median, std_dev, min, max, count_answered.
        """
        q_cols = [f"Q{i}" for i in range(1, 15) if f"Q{i}" in score_matrix.columns]
        records = []
        for col in q_cols:
            vals = score_matrix[col]
            answered = vals[vals > 0]
            records.append(
                {
                    "question": col,
                    "mean": round(float(answered.mean()), 3) if len(answered) else 0.0,
                    "median": float(answered.median()) if len(answered) else 0.0,
                    "std_dev": round(float(answered.std()), 3) if len(answered) > 1 else 0.0,
                    "min": int(answered.min()) if len(answered) else 0,
                    "max": int(answered.max()) if len(answered) else 0,
                    "count_answered": int(len(answered)),
                }
            )
        return pd.DataFrame(records).set_index("question") if records else pd.DataFrame()

    def detect_polarization(
        self,
        score_matrix: pd.DataFrame,
        threshold: float | None = None,
    ) -> list[int]:
        """Return 1-based question indices where SD exceeds the threshold.

        Args:
            score_matrix: Numeric Likert DataFrame.
            threshold: SD threshold (defaults to config.POLARIZATION_SD_THRESHOLD).

        Returns:
            List of 1-based question indices with high variance.
        """
        threshold = threshold or self.config.POLARIZATION_SD_THRESHOLD
        stats = self.calculate_question_stats(score_matrix)
        if stats.empty:
            return []
        polarized = []
        for i in range(1, 15):
            q = f"Q{i}"
            if q in stats.index and stats.loc[q, "std_dev"] >= threshold:
                polarized.append(i)
        return polarized

    # ------------------------------------------------------------------ #
    #  Phase 3b — Correlation matrix
    # ------------------------------------------------------------------ #

    def calculate_correlation_matrix(
        self, score_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute Pearson correlation between all question pairs.

        Args:
            score_matrix: Numeric Likert DataFrame.

        Returns:
            14×14 correlation DataFrame. Empty DataFrame if insufficient data.
        """
        q_cols = [f"Q{i}" for i in range(1, 15) if f"Q{i}" in score_matrix.columns]
        if score_matrix.empty or len(score_matrix) < 3:
            return pd.DataFrame()
        # Replace 0 (invalid) with NaN so they don't skew correlation
        clean = score_matrix[q_cols].replace(0, float("nan"))
        return clean.corr(method="pearson").round(3)

    def find_top_correlations(
        self,
        corr_matrix: pd.DataFrame,
        n: int = 5,
    ) -> list[dict]:
        """Return the top N strongest question-pair correlations.

        Args:
            corr_matrix: Output of calculate_correlation_matrix().
            n: Number of pairs to return.

        Returns:
            List of dicts with keys: q1, q2, correlation.
            Sorted by absolute correlation descending.
        """
        if corr_matrix.empty:
            return []
        pairs = []
        cols = list(corr_matrix.columns)
        for i, c1 in enumerate(cols):
            for c2 in cols[i + 1:]:
                val = corr_matrix.loc[c1, c2]
                if not math.isnan(val):
                    pairs.append({"q1": c1, "q2": c2, "correlation": round(val, 3)})
        pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)
        return pairs[:n]

    # ------------------------------------------------------------------ #
    #  Phase 3c — Z-score benchmarking
    # ------------------------------------------------------------------ #

    def calculate_z_scores(
        self,
        survey_id: int,
        persistence: Any,
    ) -> dict[str, float]:
        """Compute Z-scores for each dimension vs. the department average.

        Args:
            survey_id: The survey to benchmark.
            persistence: PersistenceManager instance.

        Returns:
            Dict mapping dimension_name → z_score.
            Empty dict if insufficient comparison data.
        """
        target_survey = persistence.get_survey(survey_id)
        if not target_survey:
            return {}

        target_scores = persistence.get_dimension_scores(survey_id)
        if not target_scores:
            return {}

        # Gather all dimension scores in the same department
        all_scores = persistence.get_all_dimension_scores(
            department=target_survey.department or None
        )

        # Group by dimension name
        dim_values: dict[str, list[float]] = collections.defaultdict(list)
        for ds in all_scores:
            if ds.mean > 0:
                dim_values[ds.dimension_name].append(ds.mean)

        z_scores: dict[str, float] = {}
        for ts in target_scores:
            vals = dim_values.get(ts.dimension_name, [])
            if len(vals) < 2:
                z_scores[ts.dimension_name] = 0.0
                continue
            mean_all = sum(vals) / len(vals)
            std_all = math.sqrt(sum((v - mean_all) ** 2 for v in vals) / len(vals))
            if std_all == 0:
                z_scores[ts.dimension_name] = 0.0
            else:
                z_scores[ts.dimension_name] = round((ts.mean - mean_all) / std_all, 3)

        return z_scores

    def get_percentile_rank(
        self,
        survey_id: int,
        persistence: Any,
    ) -> float:
        """Return the percentile rank (0–100) of this survey's batch score.

        Compares against all surveys in the same department.

        Args:
            survey_id: The survey to rank.
            persistence: PersistenceManager instance.

        Returns:
            Percentile rank as a float in [0, 100].
        """
        target_survey = persistence.get_survey(survey_id)
        if not target_survey:
            return 0.0

        target_results = persistence.get_form_results(survey_id)
        if not target_results:
            return 0.0

        target_score = (
            sum(fr.form_score for fr in target_results) / len(target_results)
        )

        dept = target_survey.department or None
        all_surveys = persistence.list_surveys(department=dept)
        all_scores = []
        for s in all_surveys:
            if s.id == survey_id:
                continue
            frs = persistence.get_form_results(s.id)
            if frs:
                all_scores.append(sum(fr.form_score for fr in frs) / len(frs))

        if not all_scores:
            return 100.0

        below = sum(1 for sc in all_scores if sc < target_score)
        return round(below / len(all_scores) * 100, 1)

    # ------------------------------------------------------------------ #
    #  Phase 4 — NLP comment analysis
    # ------------------------------------------------------------------ #

    def analyze_comments(
        self, form_results: list[FormResult]
    ) -> dict[str, Any]:
        """Extract keywords and sentiment from free-text comments.

        Uses a simple keyword-list approach — no external NLP library required.

        Args:
            form_results: List of FormResult objects.

        Returns:
            Dict with keys:
              - top_keywords: list of (word, count) tuples (top 15)
              - sentiment_counts: {"positive": int, "neutral": int, "negative": int}
              - negative_comments: list of comment strings classified as negative
              - total_comments: int
        """
        comments = [
            fr.comment.strip()
            for fr in form_results
            if fr.comment and fr.comment.strip()
        ]

        if not comments:
            return {
                "top_keywords": [],
                "sentiment_counts": {"positive": 0, "neutral": 0, "negative": 0},
                "negative_comments": [],
                "total_comments": 0,
            }

        # Tokenize: split on whitespace and punctuation, lowercase
        word_counter: collections.Counter = collections.Counter()
        for comment in comments:
            tokens = re.findall(r"[\w\u0600-\u06FF]+", comment.lower())
            # Filter very short tokens and common stop words
            stop = {"the", "a", "an", "is", "in", "of", "to", "and", "or",
                    "for", "it", "was", "are", "be", "has", "have", "this",
                    "that", "with", "not", "but", "on", "at", "by", "from"}
            word_counter.update(t for t in tokens if len(t) > 2 and t not in stop)

        top_keywords = word_counter.most_common(15)

        # Sentiment classification per comment
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        negative_comments: list[str] = []

        for comment in comments:
            tokens = set(re.findall(r"[\w\u0600-\u06FF]+", comment.lower()))
            pos_hits = len(tokens & _POSITIVE_WORDS)
            neg_hits = len(tokens & _NEGATIVE_WORDS)
            if neg_hits > pos_hits:
                sentiment_counts["negative"] += 1
                negative_comments.append(comment)
            elif pos_hits > neg_hits:
                sentiment_counts["positive"] += 1
            else:
                sentiment_counts["neutral"] += 1

        return {
            "top_keywords": top_keywords,
            "sentiment_counts": sentiment_counts,
            "negative_comments": negative_comments,
            "total_comments": len(comments),
        }

    # ------------------------------------------------------------------ #
    #  Phase 5 — Automated QA alerts
    # ------------------------------------------------------------------ #

    def run_qa_checks(
        self,
        survey_id: int,
        dimension_scores: list[DimensionScore],
        question_stats: pd.DataFrame,
        form_results: list[FormResult],
        persistence: Any | None = None,
    ) -> list[QAAlert]:
        """Run all QA threshold checks and return triggered alerts.

        Checks performed:
        1. Dimension mean below DIMENSION_ALERT_THRESHOLD
        2. Question SD above POLARIZATION_SD_THRESHOLD
        3. Q10 (Punctuality) > PUNCTUALITY_NO_THRESHOLD % "No" responses
        4. Batch score below BATCH_SCORE_ALERT_THRESHOLD

        Args:
            survey_id: The survey being checked.
            dimension_scores: Output of calculate_dimension_scores().
            question_stats: Output of calculate_question_stats().
            form_results: Raw FormResult list (for punctuality check).
            persistence: Optional PersistenceManager to persist alerts.

        Returns:
            List of QAAlert objects.
        """
        alerts: list[QAAlert] = []
        now = datetime.now().isoformat()

        # 1. Dimension threshold
        for ds in dimension_scores:
            if ds.mean > 0 and ds.mean < self.config.DIMENSION_ALERT_THRESHOLD:
                severity = "critical" if ds.mean < 1.8 else "warning"
                alerts.append(
                    QAAlert(
                        survey_id=survey_id,
                        alert_type="dimension_low",
                        dimension_name=ds.dimension_name,
                        value=ds.mean,
                        threshold=self.config.DIMENSION_ALERT_THRESHOLD,
                        message=(
                            f"Dimension '{ds.dimension_name}' scored {ds.mean:.2f} "
                            f"(threshold: {self.config.DIMENSION_ALERT_THRESHOLD}). "
                            "Schedule a classroom observation."
                        ),
                        severity=severity,
                        created_at=now,
                    )
                )

        # 2. Polarization (high SD)
        if not question_stats.empty:
            for i in range(1, 15):
                q = f"Q{i}"
                if q in question_stats.index:
                    sd = question_stats.loc[q, "std_dev"]
                    if sd >= self.config.POLARIZATION_SD_THRESHOLD:
                        alerts.append(
                            QAAlert(
                                survey_id=survey_id,
                                alert_type="polarization",
                                question_index=i,
                                value=sd,
                                threshold=self.config.POLARIZATION_SD_THRESHOLD,
                                message=(
                                    f"Q{i} shows high variance (SD={sd:.2f}). "
                                    "Students are polarized — possible comprehension gap."
                                ),
                                severity="warning",
                                created_at=now,
                            )
                        )

        # 3. Punctuality (Q10 "No" rate)
        pq = self.config.PUNCTUALITY_QUESTION
        valid_forms = [fr for fr in form_results if fr.valid]
        if valid_forms:
            no_count = sum(
                1 for fr in valid_forms if fr.answers()[pq - 1] == "No"
            )
            no_rate = no_count / len(valid_forms)
            if no_rate > self.config.PUNCTUALITY_NO_THRESHOLD:
                alerts.append(
                    QAAlert(
                        survey_id=survey_id,
                        alert_type="punctuality",
                        question_index=pq,
                        value=round(no_rate * 100, 1),
                        threshold=self.config.PUNCTUALITY_NO_THRESHOLD * 100,
                        message=(
                            f"Q{pq} (Punctuality): {no_rate * 100:.1f}% of students "
                            f"answered 'No' (threshold: "
                            f"{self.config.PUNCTUALITY_NO_THRESHOLD * 100:.0f}%). "
                            "Immediate follow-up required."
                        ),
                        severity="critical",
                        created_at=now,
                    )
                )

        # 4. Batch score
        if valid_forms:
            batch = sum(fr.form_score for fr in valid_forms) / len(valid_forms)
            if batch < self.config.BATCH_SCORE_ALERT_THRESHOLD:
                alerts.append(
                    QAAlert(
                        survey_id=survey_id,
                        alert_type="batch_low",
                        value=round(batch, 1),
                        threshold=self.config.BATCH_SCORE_ALERT_THRESHOLD,
                        message=(
                            f"Overall batch score {batch:.1f}% is below the "
                            f"acceptable threshold of "
                            f"{self.config.BATCH_SCORE_ALERT_THRESHOLD:.0f}%."
                        ),
                        severity="critical" if batch < 50 else "warning",
                        created_at=now,
                    )
                )

        if persistence and alerts:
            try:
                persistence.save_alerts(alerts)
            except Exception:
                logger.exception("Failed to persist QA alerts")

        logger.info(
            "QA checks for survey_id=%s: %d alert(s) triggered", survey_id, len(alerts)
        )
        return alerts

    # ------------------------------------------------------------------ #
    #  Convenience: run full advanced analytics pipeline
    # ------------------------------------------------------------------ #

    def run_advanced_analytics(
        self,
        survey_id: int,
        form_results: list[FormResult],
        persistence: Any | None = None,
    ) -> dict[str, Any]:
        """Run the complete advanced analytics pipeline for a survey.

        Builds the score matrix, computes dimension scores, question stats,
        correlation matrix, and QA alerts. Persists dimension scores and
        alerts if persistence is provided.

        Args:
            survey_id: The survey being analysed.
            form_results: List of FormResult objects.
            persistence: Optional PersistenceManager for persistence.

        Returns:
            Dict with keys: score_matrix, dimension_scores, question_stats,
            correlation_matrix, top_correlations, polarized_questions,
            alerts, comment_analysis, invalid_forms.
        """
        score_matrix = self.build_score_matrix(form_results)
        dimension_scores = self.calculate_dimension_scores(score_matrix, survey_id)
        question_stats = self.calculate_question_stats(score_matrix)
        corr_matrix = self.calculate_correlation_matrix(score_matrix)
        top_corr = self.find_top_correlations(corr_matrix)
        polarized = self.detect_polarization(score_matrix)
        alerts = self.run_qa_checks(
            survey_id, dimension_scores, question_stats, form_results, persistence
        )
        comment_analysis = self.analyze_comments(form_results)
        invalid_forms = self.flag_invalid_forms(form_results)

        if persistence and dimension_scores:
            try:
                persistence.save_dimension_scores(dimension_scores)
            except Exception:
                logger.exception("Failed to persist dimension scores")

        return {
            "score_matrix": score_matrix,
            "dimension_scores": dimension_scores,
            "question_stats": question_stats,
            "correlation_matrix": corr_matrix,
            "top_correlations": top_corr,
            "polarized_questions": polarized,
            "alerts": alerts,
            "comment_analysis": comment_analysis,
            "invalid_forms": invalid_forms,
        }
