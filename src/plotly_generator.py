"""Plotly chart generation and HTML dashboard assembly."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import Config, setup_logging

logger = setup_logging()

# Colour palette shared across all charts
_COLORS = {
    "Yes":      "#2ecc71",
    "Somewhat": "#f1c40f",
    "No":       "#e74c3c",
    "Invalid":  "#95a5a6",
    "good":     "#00C896",
    "warning":  "#F5A623",
    "critical": "#FF4D6A",
    "neutral":  "#4A9EFF",
    "positive": "#2ecc71",
    "negative": "#e74c3c",
}

_DIM_COLORS = ["#4A9EFF", "#00C896", "#F5A623", "#FF4D6A"]


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
    #  Diverging stacked bar chart — Likert scale best-practice view
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_diverging_bar_chart(
        df: pd.DataFrame,
        question_labels: list[str] | None = None,
    ) -> go.Figure:
        """Create a diverging stacked bar chart for Likert responses.

        No responses extend left (negative), Yes responses extend right
        (positive), Somewhat is split evenly around the centre axis.

        Args:
            df: Results DataFrame with Q1..Q14 columns containing
                'Yes', 'Somewhat', 'No', 'Invalid' strings.
            question_labels: Optional list of 14 label strings.

        Returns:
            Plotly Figure.
        """
        question_cols = [f"Q{i}" for i in range(1, Config.ROW_COUNT + 1)]
        if question_labels and len(question_labels) == 14:
            x_labels = [f"Q{i+1}: {t[:35]}" for i, t in enumerate(question_labels)]
        else:
            x_labels = question_cols

        yes_pct, sw_pct, no_pct = [], [], []
        for q in question_cols:
            total = len(df)
            if total == 0:
                yes_pct.append(0.0)
                sw_pct.append(0.0)
                no_pct.append(0.0)
                continue
            yes_pct.append((df[q] == "Yes").sum() / total * 100)
            sw_pct.append((df[q] == "Somewhat").sum() / total * 100)
            no_pct.append((df[q] == "No").sum() / total * 100)

        sw_left  = [v / 2 for v in sw_pct]
        sw_right = [v / 2 for v in sw_pct]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="No",
            x=[-v for v in no_pct],
            y=x_labels,
            orientation="h",
            marker_color=_COLORS["No"],
            hovertemplate="%{customdata:.1f}%<extra>No</extra>",
            customdata=no_pct,
        ))
        fig.add_trace(go.Bar(
            name="Somewhat (−)",
            x=[-v for v in sw_left],
            y=x_labels,
            orientation="h",
            marker_color=_COLORS["Somewhat"],
            showlegend=False,
            hovertemplate="%{customdata:.1f}%<extra>Somewhat</extra>",
            customdata=sw_pct,
        ))
        fig.add_trace(go.Bar(
            name="Somewhat",
            x=sw_right,
            y=x_labels,
            orientation="h",
            marker_color=_COLORS["Somewhat"],
            hovertemplate="%{customdata:.1f}%<extra>Somewhat</extra>",
            customdata=sw_pct,
        ))
        fig.add_trace(go.Bar(
            name="Yes",
            x=yes_pct,
            y=x_labels,
            orientation="h",
            marker_color=_COLORS["Yes"],
            hovertemplate="%{x:.1f}%<extra>Yes</extra>",
        ))

        fig.update_layout(
            barmode="relative",
            title="Likert Response Distribution (Diverging)",
            xaxis=dict(
                title="← No  |  Yes →",
                ticksuffix="%",
                zeroline=True,
                zerolinecolor="#888",
                zerolinewidth=2,
            ),
            yaxis=dict(autorange="reversed"),
            template="plotly_white",
            height=max(400, 35 * 14),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Radar chart — pedagogical dimensions
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_radar_chart(
        dimension_scores: list,
        title: str = "Pedagogical Dimension Scores",
        dept_avg: list | None = None,
    ) -> go.Figure:
        """Create a radar/spider chart for the 4 pedagogical dimensions.

        Args:
            dimension_scores: List of DimensionScore objects for this survey.
            title: Chart title.
            dept_avg: Optional list of DimensionScore objects representing
                      the department average (adds a second trace).

        Returns:
            Plotly Figure.
        """
        if not dimension_scores:
            fig = go.Figure()
            fig.update_layout(title=title, template="plotly_white", height=400)
            return fig

        categories = [ds.dimension_name for ds in dimension_scores]
        values = [ds.mean for ds in dimension_scores]
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself",
            name="This Survey",
            line_color=_COLORS["neutral"],
            fillcolor="rgba(74,158,255,0.2)",
            hovertemplate="%{theta}: %{r:.2f}<extra></extra>",
        ))

        if dept_avg:
            avg_values = [ds.mean for ds in dept_avg]
            avg_closed = avg_values + [avg_values[0]]
            fig.add_trace(go.Scatterpolar(
                r=avg_closed,
                theta=categories_closed,
                fill="toself",
                name="Dept. Average",
                line_color=_COLORS["warning"],
                fillcolor="rgba(245,166,35,0.15)",
                line_dash="dash",
                hovertemplate="%{theta}: %{r:.2f}<extra>Dept. Avg</extra>",
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 3],
                    tickvals=[1, 2, 3],
                    ticktext=["No (1)", "Somewhat (2)", "Yes (3)"],
                    gridcolor="#ddd",
                ),
                angularaxis=dict(gridcolor="#ddd"),
            ),
            title=title,
            template="plotly_white",
            height=450,
            showlegend=True,
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Correlation heatmap
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_correlation_heatmap(
        corr_matrix: pd.DataFrame,
        question_labels: list[str] | None = None,
    ) -> go.Figure:
        """Create an annotated Pearson correlation heatmap.

        Args:
            corr_matrix: 14×14 correlation DataFrame.
            question_labels: Optional list of 14 label strings.

        Returns:
            Plotly Figure.
        """
        if corr_matrix.empty:
            fig = go.Figure()
            fig.update_layout(
                title="Correlation Matrix (insufficient data)",
                template="plotly_white",
                height=400,
            )
            return fig

        cols = list(corr_matrix.columns)
        labels = [f"Q{i+1}" for i in range(len(cols))]

        z = corr_matrix.values.tolist()
        z_clean = [
            [0.0 if (isinstance(v, float) and math.isnan(v)) else v for v in row]
            for row in z
        ]

        fig = go.Figure(go.Heatmap(
            z=z_clean,
            x=labels,
            y=labels,
            colorscale="RdBu",
            zmid=0,
            zmin=-1,
            zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in z_clean],
            texttemplate="%{text}",
            textfont={"size": 9},
            hovertemplate="Q%{x} × Q%{y}: %{z:.3f}<extra></extra>",
            colorbar=dict(title="Pearson r"),
        ))

        fig.update_layout(
            title="Question Correlation Matrix (Pearson)",
            template="plotly_white",
            height=520,
            xaxis=dict(side="bottom"),
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Box plots — per-question variance
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_box_plots(
        score_matrix: pd.DataFrame,
        question_labels: list[str] | None = None,
    ) -> go.Figure:
        """Create box plots showing Likert score distribution per question.

        Args:
            score_matrix: Numeric Likert DataFrame from build_score_matrix().
            question_labels: Optional list of 14 label strings.

        Returns:
            Plotly Figure.
        """
        if score_matrix.empty:
            fig = go.Figure()
            fig.update_layout(
                title="Score Distribution (no data)",
                template="plotly_white",
                height=400,
            )
            return fig

        q_cols = [f"Q{i}" for i in range(1, 15) if f"Q{i}" in score_matrix.columns]
        fig = go.Figure()

        for i, col in enumerate(q_cols):
            vals = score_matrix[col]
            answered = vals[vals > 0].tolist()
            label = (
                f"Q{i+1}: {question_labels[i][:25]}"
                if question_labels and len(question_labels) == 14
                else col
            )
            fig.add_trace(go.Box(
                y=answered,
                name=label,
                marker_color=_DIM_COLORS[i % len(_DIM_COLORS)],
                boxmean="sd",
                hovertemplate=f"{label}<br>Value: %{{y}}<extra></extra>",
            ))

        fig.update_layout(
            title="Score Distribution per Question (Likert 1–3)",
            yaxis=dict(
                title="Likert Score",
                tickvals=[1, 2, 3],
                ticktext=["No (1)", "Somewhat (2)", "Yes (3)"],
                range=[0.5, 3.5],
            ),
            xaxis=dict(tickangle=-45),
            template="plotly_white",
            height=480,
            showlegend=False,
        )
        return fig

    # ------------------------------------------------------------------ #
    #  Dimension KPI bar chart
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_dimension_bar_chart(
        dimension_scores: list,
    ) -> go.Figure:
        """Create a horizontal bar chart of dimension scores with threshold line.

        Args:
            dimension_scores: List of DimensionScore objects.

        Returns:
            Plotly Figure.
        """
        if not dimension_scores:
            fig = go.Figure()
            fig.update_layout(title="Dimension Scores", template="plotly_white", height=300)
            return fig

        names = [ds.dimension_name for ds in dimension_scores]
        means = [ds.mean for ds in dimension_scores]
        colors = [_COLORS.get(ds.status, _COLORS["neutral"]) for ds in dimension_scores]
        errors = [ds.std_dev for ds in dimension_scores]

        fig = go.Figure(go.Bar(
            x=means,
            y=names,
            orientation="h",
            marker_color=colors,
            error_x=dict(type="data", array=errors, visible=True),
            hovertemplate="%{y}: %{x:.2f} ± %{error_x.array:.2f}<extra></extra>",
        ))

        threshold = Config.DIMENSION_ALERT_THRESHOLD
        fig.add_vline(
            x=threshold,
            line_dash="dash",
            line_color="#FF4D6A",
            annotation_text=f"Alert threshold ({threshold})",
            annotation_position="top right",
        )

        fig.update_layout(
            title="Pedagogical Dimension Scores (Likert 1–3)",
            xaxis=dict(
                title="Mean Likert Score",
                range=[0, 3.2],
                tickvals=[1, 2, 3],
                ticktext=["No (1)", "Somewhat (2)", "Yes (3)"],
            ),
            yaxis=dict(autorange="reversed"),
            template="plotly_white",
            height=320,
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
        cls,
        df: pd.DataFrame,
        batch_score: float,
        question_texts: list[str] | None = None,
        mode: str = "basic",
        advanced_data: dict | None = None,
    ) -> str:
        """Combine all charts into a single HTML dashboard.

        Args:
            df: Results DataFrame.
            batch_score: Computed batch satisfaction score.
            question_texts: Optional list of 14 question text strings.
            mode: "basic" (original 3-chart report) or "advanced"
                  (full QA analytics report).
            advanced_data: Dict returned by AnalyticsEngine.run_advanced_analytics().
                           Required when mode="advanced".

        Returns:
            Complete HTML string.
        """
        if mode == "advanced" and advanced_data:
            return cls._generate_advanced_html(
                df, batch_score, question_texts, advanced_data
            )
        return cls._generate_basic_html(df, batch_score, question_texts)

    @classmethod
    def _generate_basic_html(
        cls,
        df: pd.DataFrame,
        batch_score: float,
        question_texts: list[str] | None = None,
    ) -> str:
        bar_fig   = cls.create_stacked_bar_chart(df, question_texts=question_texts)
        pie_fig   = cls.create_pie_chart(df)
        score_fig = cls.create_score_display(batch_score)

        bar_div   = bar_fig.to_html(full_html=False, include_plotlyjs=False)
        pie_div   = pie_fig.to_html(full_html=False, include_plotlyjs=False)
        score_div = score_fig.to_html(full_html=False, include_plotlyjs=False)

        return f"""<!DOCTYPE html>
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
    <div class="card">{score_div}</div>
    <div class="card">{bar_div}</div>
    <div class="card">{pie_div}</div>
</body>
</html>"""

    @classmethod
    def _generate_advanced_html(
        cls,
        df: pd.DataFrame,
        batch_score: float,
        question_texts: list[str] | None,
        advanced_data: dict,
    ) -> str:
        """Generate the full advanced QA analytics HTML report."""
        dimension_scores  = advanced_data.get("dimension_scores", [])
        score_matrix      = advanced_data.get("score_matrix")
        corr_matrix       = advanced_data.get("correlation_matrix")
        alerts            = advanced_data.get("alerts", [])
        comment_analysis  = advanced_data.get("comment_analysis", {})
        top_correlations  = advanced_data.get("top_correlations", [])
        polarized         = advanced_data.get("polarized_questions", [])

        # Build all figures
        score_fig    = cls.create_score_display(batch_score)
        radar_fig    = cls.create_radar_chart(dimension_scores)
        dim_bar_fig  = cls.create_dimension_bar_chart(dimension_scores)
        div_bar_fig  = cls.create_diverging_bar_chart(df, question_labels=question_texts)
        bar_fig      = cls.create_stacked_bar_chart(df, question_texts=question_texts)
        pie_fig      = cls.create_pie_chart(df)

        corr_fig = (
            cls.create_correlation_heatmap(corr_matrix, question_labels=question_texts)
            if corr_matrix is not None and not corr_matrix.empty
            else None
        )
        box_fig = (
            cls.create_box_plots(score_matrix, question_labels=question_texts)
            if score_matrix is not None and not score_matrix.empty
            else None
        )

        def _div(fig):
            return fig.to_html(full_html=False, include_plotlyjs=False) if fig else ""

        # Alert HTML
        alert_html = ""
        if alerts:
            rows = ""
            for a in alerts:
                icon = "🔴" if a.severity == "critical" else "🟡"
                rows += f"<tr><td>{icon}</td><td>{a.alert_type.replace('_',' ').title()}</td><td>{a.message}</td></tr>"
            alert_html = f"""
            <div class="card alert-card">
                <h2>⚠️ QA Alerts ({len(alerts)})</h2>
                <table class="alert-table">
                    <thead><tr><th></th><th>Type</th><th>Message</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>"""
        else:
            alert_html = '<div class="card"><h2>✅ No QA Alerts</h2><p>All dimensions are within acceptable thresholds.</p></div>'

        # Comment analysis HTML
        comment_html = ""
        if comment_analysis.get("total_comments", 0) > 0:
            sc = comment_analysis["sentiment_counts"]
            kw = comment_analysis["top_keywords"]
            kw_html = " ".join(
                f'<span class="kw-chip">{w} <b>({c})</b></span>'
                for w, c in kw[:10]
            )
            comment_html = f"""
            <div class="card">
                <h2>💬 Comment Analysis ({comment_analysis['total_comments']} comments)</h2>
                <div class="sentiment-row">
                    <span class="sent-pos">✅ Positive: {sc['positive']}</span>
                    <span class="sent-neu">➖ Neutral: {sc['neutral']}</span>
                    <span class="sent-neg">❌ Negative: {sc['negative']}</span>
                </div>
                <h3>Top Keywords</h3>
                <div class="kw-cloud">{kw_html}</div>
            </div>"""

        # Top correlations HTML
        corr_insight_html = ""
        if top_correlations:
            rows = "".join(
                f"<tr><td>{p['q1']}</td><td>{p['q2']}</td>"
                f"<td style='color:{'#2ecc71' if p['correlation']>0 else '#e74c3c'}'>"
                f"{p['correlation']:+.3f}</td></tr>"
                for p in top_correlations[:5]
            )
            corr_insight_html = f"""
            <div class="card">
                <h2>🔗 Top Question Correlations</h2>
                <table class="corr-table">
                    <thead><tr><th>Q1</th><th>Q2</th><th>Pearson r</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>"""

        # Polarization HTML
        polar_html = ""
        if polarized:
            qs = ", ".join(f"Q{i}" for i in polarized)
            polar_html = f"""
            <div class="card warn-card">
                <h2>📊 Polarized Questions</h2>
                <p>The following questions show high variance (SD ≥ {Config.POLARIZATION_SD_THRESHOLD}),
                indicating a split classroom: <strong>{qs}</strong></p>
            </div>"""

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>OMR QA Advanced Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; background: #f0f4fa; color: #0f172a; }}
        .header {{ background: #1A2035; color: white; padding: 1.5em 2em; }}
        .header h1 {{ margin: 0; font-size: 1.6em; }}
        .header p {{ margin: 0.3em 0 0; color: #8B9BB4; font-size: 0.9em; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 1.5em 2em; }}
        .card {{ background: white; border-radius: 12px; padding: 1.2em 1.5em;
                 margin-bottom: 1.5em; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        .card h2 {{ margin-top: 0; font-size: 1.1em; color: #1A2035; }}
        .card h3 {{ font-size: 0.95em; color: #475569; }}
        .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5em; }}
        .alert-card {{ border-left: 4px solid #FF4D6A; }}
        .warn-card  {{ border-left: 4px solid #F5A623; }}
        .alert-table, .corr-table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        .alert-table th, .alert-table td,
        .corr-table th, .corr-table td {{
            padding: 0.5em 0.8em; border-bottom: 1px solid #e2e8f0; text-align: left;
        }}
        .alert-table th, .corr-table th {{ background: #f8fafc; font-weight: 600; }}
        .sentiment-row {{ display: flex; gap: 2em; margin: 0.8em 0; font-size: 0.95em; }}
        .sent-pos {{ color: #059669; font-weight: 600; }}
        .sent-neu {{ color: #475569; font-weight: 600; }}
        .sent-neg {{ color: #DC2626; font-weight: 600; }}
        .kw-cloud {{ display: flex; flex-wrap: wrap; gap: 0.5em; margin-top: 0.5em; }}
        .kw-chip {{ background: #EFF6FF; color: #1D4ED8; padding: 0.3em 0.7em;
                    border-radius: 20px; font-size: 0.85em; }}
        @media (max-width: 900px) {{ .two-col {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>OMR QA Advanced Analytics Report</h1>
        <p>Comprehensive pedagogical quality assessment</p>
    </div>
    <div class="container">
        <div class="card">{_div(score_fig)}</div>
        {alert_html}
        {polar_html}
        <div class="two-col">
            <div class="card">{_div(radar_fig)}</div>
            <div class="card">{_div(dim_bar_fig)}</div>
        </div>
        <div class="card">{_div(div_bar_fig)}</div>
        <div class="card">{_div(bar_fig)}</div>
        {f'<div class="card">{_div(box_fig)}</div>' if box_fig else ''}
        {f'<div class="card">{_div(corr_fig)}</div>' if corr_fig else ''}
        {corr_insight_html}
        <div class="card">{_div(pie_fig)}</div>
        {comment_html}
    </div>
</body>
</html>"""
