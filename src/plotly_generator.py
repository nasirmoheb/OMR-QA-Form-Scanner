"""Plotly chart generation and HTML dashboard assembly."""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import Config, setup_logging

logger = setup_logging()


class PlotlyGenerator:
    """Static helpers for creating Plotly charts and dashboards."""

    # ------------------------------------------------------------------ #
    #  Stacked bar chart — per-question answer counts
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_stacked_bar_chart(df: pd.DataFrame, question_texts: list[str] | None = None) -> go.Figure:
        """Create a stacked bar chart of Yes/Somewhat/No/Invalid per question.

        Args:
            df: Results DataFrame.
            question_texts: Optional list of 14 question text strings to use
                as x-axis labels. Each label is truncated to 40 characters.
                Falls back to Q1..Q14 when ``None`` or length != 14.
        """
        question_cols = [f"Q{i}" for i in range(1, Config.ROW_COUNT + 1)]

        counts: dict[str, list[int]] = {
            "Yes": [],
            "Somewhat": [],
            "No": [],
            "Invalid": [],
        }

        for q in question_cols:
            for key in counts:
                counts[key].append(int((df[q] == key).sum()))

        # Determine x-axis labels
        if question_texts is not None and len(question_texts) == 14:
            x_labels = [t[:40] for t in question_texts]
        else:
            x_labels = question_cols

        fig = go.Figure()
        colors = {"Yes": "#2ecc71", "Somewhat": "#f1c40f", "No": "#e74c3c", "Invalid": "#95a5a6"}
        for key in ("Yes", "Somewhat", "No", "Invalid"):
            fig.add_trace(
                go.Bar(
                    name=key,
                    x=x_labels,
                    y=counts[key],
                    marker_color=colors[key],
                )
            )

        fig.update_layout(
            barmode="stack",
            title="Answer Distribution by Question",
            xaxis_title="Question",
            yaxis_title="Count",
            template="plotly_white",
            height=500,
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Pie chart — overall answer distribution
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_pie_chart(df: pd.DataFrame) -> go.Figure:
        """Create a pie chart of overall answer distribution."""
        question_cols = [f"Q{i}" for i in range(1, Config.ROW_COUNT + 1)]

        values: dict[str, int] = {"Yes": 0, "Somewhat": 0, "No": 0, "Invalid": 0}
        for q in question_cols:
            for val in df[q].fillna("Invalid"):
                if val in values:
                    values[val] += 1

        labels = list(values.keys())
        pie_values = list(values.values())
        colors = ["#2ecc71", "#f1c40f", "#e74c3c", "#95a5a6"]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=pie_values,
                    marker_colors=colors,
                    hole=0.4,
                    textinfo="label+percent",
                )
            ]
        )
        fig.update_layout(
            title="Overall Answer Distribution",
            template="plotly_white",
            height=400,
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Score display — large text indicator
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_score_display(score: float) -> go.Figure:
        """Create a large numeric score display."""
        fig = go.Figure()
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=round(score, 1),
                title={"text": "Overall Satisfaction Score"},
                domain={"x": [0, 1], "y": [0, 1]},
                number={"font": {"size": 72, "color": "#2c3e50"}},
            )
        )
        fig.update_layout(
            template="plotly_white",
            height=300,
            margin=dict(t=50, b=50, l=50, r=50),
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Dashboard assembly
    # ------------------------------------------------------------------ #

    @classmethod
    def generate_dashboard_html(
        cls, df: pd.DataFrame, batch_score: float, question_texts: list[str] | None = None
    ) -> str:
        """Combine all charts into a single HTML dashboard.

        Args:
            df: Results DataFrame.
            batch_score: Computed batch satisfaction score.
            question_texts: Optional list of 14 question text strings to use
                as chart labels in the stacked bar chart.

        Returns:
            Complete HTML string.
        """
        bar_fig = cls.create_stacked_bar_chart(df, question_texts=question_texts)
        pie_fig = cls.create_pie_chart(df)
        score_fig = cls.create_score_display(batch_score)

        # Convert each figure to a standalone HTML div
        bar_div = bar_fig.to_html(full_html=False, include_plotlyjs=False)
        pie_div = pie_fig.to_html(full_html=False, include_plotlyjs=False)
        score_div = score_fig.to_html(full_html=False, include_plotlyjs=False)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OMR QA Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 2em; background: #f8f9fa; }}
        h1 {{ color: #2c3e50; }}
        .card {{ background: white; border-radius: 8px; padding: 1em; margin-bottom: 1.5em;
                 box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <h1>OMR QA Form Scanner — Batch Report</h1>
    <div class="card">
        {score_div}
    </div>
    <div class="card">
        {bar_div}
    </div>
    <div class="card">
        {pie_div}
    </div>
</body>
</html>"""
        return html
