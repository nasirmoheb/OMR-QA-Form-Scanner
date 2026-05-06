"""Results page — summary table, raw data, trend analysis, advanced analytics, and exports."""

from __future__ import annotations

import logging
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from analytics_engine import AnalyticsEngine
from i18n import _, get_start, get_end, get_anchor, get_compound, is_rtl, rtl_text
from models import FormResult, Survey
from persistence import PersistenceManager
from .base import BasePage, PageRouter

logger = logging.getLogger("tadris_qa_system")

# Tab identifiers (not translated — used as internal keys)
_TAB_SUMMARY  = "summary_view"
_TAB_RAW      = "raw_data_view"
_TAB_TREND    = "trend_analysis"
_TAB_ADVANCED = "advanced_analytics"


class ResultsPage(BasePage):
    """Survey results: summary, raw data, trend, and export."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        survey_id: int,
        analytics: AnalyticsEngine | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.survey_id = survey_id
        self.analytics = analytics or AnalyticsEngine()

        self.survey: Survey | None = self.persistence.get_survey(survey_id)
        self.form_results: list[FormResult] = self.persistence.get_form_results(survey_id)
        self.question_texts: list[str] | None = self.persistence.get_setting("question_texts", None)

        # Advanced analytics cache (computed lazily on first tab visit)
        self._advanced_data: dict | None = None

        # Auto-advance status
        if self.survey and self.survey.status == "Processed":
            self.survey.status = "Analyzed"
            self.survey.updated_at = datetime.now().isoformat()
            self.persistence.update_survey(self.survey)

        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # -- Header ----
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        # Title
        ctk.CTkLabel(
            header, text=_("survey_results_analytics"), font=T.h1(), text_color=T.TEXT_PRIMARY
        ).pack(anchor=get_anchor())

        # Subtitle
        ctk.CTkLabel(
            header, text=_("survey_results_subtitle"),
            font=T.small(), text_color=T.TEXT_SECONDARY, justify=get_start()
        ).pack(anchor=get_anchor(), pady=(4, 0))

        # -- Main Content (2 Columns Layout) ----
        content_wrap = T.transparent(self)
        content_wrap.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        left_col = T.transparent(content_wrap)
        left_col.pack(side=get_start(), fill="both", expand=True, padx=(0, 16) if not is_rtl() else (16, 0))

        right_col = T.transparent(content_wrap)
        right_col.pack(side=get_end(), fill="y", padx=(16, 0) if not is_rtl() else (0, 16))

        # -------------------------------------------------------------
        # LEFT COLUMN: Tabs and Tables
        # -------------------------------------------------------------
        
        # -- Tab switcher ----
        tab_card = T.card(left_col)
        tab_card.pack(fill="x", pady=(0, 16))

        self.tab_var = tk.StringVar(value=_("summary_view"))
        seg = ctk.CTkSegmentedButton(
            tab_card,
            values=[
                _("summary_view"),
                _("raw_data_view"),
                _("trend_analysis"),
                _("advanced_analytics"),
            ],
            command=self._on_tab,
            variable=self.tab_var,
            font=T.body(),
            height=40,
            corner_radius=T.RADIUS_MD,
            fg_color=T.SURFACE_RAISED,
            selected_color=T.ACCENT,
            selected_hover_color=T.ACCENT_HOVER,
            unselected_color=T.SURFACE_RAISED,
            unselected_hover_color=T.GHOST_HOVER,
            text_color="#FFFFFF",
        )
        seg.pack(fill="x", padx=8, pady=8)

        # -- Content area ----
        self.content = ctk.CTkScrollableFrame(
            left_col, fg_color="transparent", corner_radius=0
        )
        self.content.pack(fill="both", expand=True)

        # -------------------------------------------------------------
        # RIGHT COLUMN: Actions and Meta
        # -------------------------------------------------------------
        
        # -- Survey Meta Details ----
        if self.survey:
            meta_card = T.card(right_col)
            meta_card.pack(fill="x", pady=(0, 16), ipadx=10)
            
            meta_inner = T.transparent(meta_card)
            meta_inner.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
            
            ctk.CTkLabel(
                meta_inner, text=_("survey_summary"),
                font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
            ).pack(anchor=get_anchor(), pady=(0, 12))

            ctk.CTkLabel(
                meta_inner, image=IC.icon("book", size=15, color=T.ACCENT[1]),
                text=f"  {self.survey.subject}", font=T.h4(), text_color=T.TEXT_PRIMARY,
                anchor=get_anchor(), compound=get_compound()
            ).pack(anchor=get_anchor())

            ctk.CTkLabel(
                meta_inner, text=f"{self.survey.professor}\n{self.survey.semester} • {self.survey.academic_year}",
                font=T.small(), text_color=T.TEXT_SECONDARY, anchor=get_anchor(), justify=get_start()
            ).pack(anchor=get_anchor(), pady=(8, 0))

            T.status_chip(meta_inner, self.survey.status).pack(anchor=get_anchor(), pady=(12, 0))

            # KPIs
            form_count = len(self.form_results)
            batch_score = (
                sum(fr.form_score for fr in self.form_results) / form_count
                if form_count > 0 else 0.0
            )
            
            T.divider(meta_inner).pack(fill="x", pady=16)
            
            # Simple KPI display
            def _kpi_row(label, value, icon):
                r = T.transparent(meta_inner)
                r.pack(fill="x", pady=2)
                ctk.CTkLabel(r, text=label, font=T.tiny(), text_color=T.TEXT_MUTED).pack(side=get_start())
                ctk.CTkLabel(r, text=value, font=T.font(12, "bold"), text_color=T.TEXT_PRIMARY).pack(side=get_end())

            _kpi_row(_("total_forms"), str(form_count), "file_text")
            _kpi_row(_("avg_score"), f"{batch_score:.1f}%", "trending_up")

        # -- Export Card ----
        export_card = T.card(right_col)
        export_card.pack(fill="x", ipadx=10)

        export_header = T.transparent(export_card)
        export_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            export_header, text=_("export_reports"),
            font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
        ).pack(anchor=get_anchor())

        export_body = T.transparent(export_card)
        export_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # HTML Dashboard
        ctk.CTkButton(
            export_body, text="  " + _("html_dashboard"), image=IC.icon("globe", size=16, color="#000000"),
            height=44, corner_radius=T.RADIUS_MD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(13, "bold"), command=self._on_html,
        ).pack(fill="x", pady=(0, 12))

        # Advanced HTML
        IC.icon_button(
            export_body, "trending_up", text="  " + _("advanced_analytics"),
            size=16, color=T.TEXT_PRIMARY[1], height=40,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(12),
            border_width=1, border_color=T.CARD_BORDER,
            command=self._on_advanced_html,
        ).pack(fill="x", pady=(0, 12))

        # PDF Report
        IC.icon_button(
            export_body, "file_text", text="  " + _("pdf_summary"),
            size=16, color=T.TEXT_PRIMARY[1], height=40,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(12),
            border_width=1, border_color=T.CARD_BORDER,
            command=self._on_pdf,
        ).pack(fill="x", pady=(0, 12))

        # Official Dari Report
        IC.icon_button(
            export_body, "globe", text="  " + _("official_dari_report"),
            size=16, color=T.TEXT_PRIMARY[1], height=40,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(12),
            border_width=1, border_color=T.CARD_BORDER,
            command=self._on_dari_report,
        ).pack(fill="x", pady=(0, 12))

        # CSV Data
        IC.icon_button(
            export_body, "download", text="  " + _("csv_raw_data"),
            size=16, color=T.TEXT_PRIMARY[1], height=40,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(12),
            border_width=1, border_color=T.CARD_BORDER,
            command=self._on_csv,
        ).pack(fill="x", pady=(0, 12))

        # Back Button
        ctk.CTkButton(
            export_body, text="  " + _("back_to_home"), image=IC.icon("arrow_left", size=16, color=T.TEXT_SECONDARY[1]),
            height=36, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_SECONDARY, font=T.font(13), command=lambda: self.go("dashboard"),
        ).pack(fill="x", pady=(20, 0))

        # Content area removed from here, already packed in left_col above.
        pass

        # Show default tab
        self._show_summary()

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    def _clear(self) -> None:
        for w in self.content.winfo_children():
            w.destroy()

    def _on_tab(self, value: str) -> None:
        if value == _("summary_view"):
            self._show_summary()
        elif value == _("raw_data_view"):
            self._show_raw()
        elif value == _("trend_analysis"):
            self._show_trend()
        elif value == _("advanced_analytics"):
            self._show_advanced()

    def _styled_tree(self, columns: tuple, col_names: tuple, widths: dict | None = None) -> ttk.Treeview:
        """Create a styled Treeview with alternating row colours."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Modern.Treeview",
            background=T.SURFACE[1],
            foreground=T.TEXT_PRIMARY[1],
            rowheight=36,
            fieldbackground=T.SURFACE[1],
            borderwidth=0,
            font=T.font(11),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background=T.SURFACE_RAISED[1],
            foreground=T.TEXT_SECONDARY[1],
            font=T.font(11, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map("Modern.Treeview", background=[("selected", T.ACCENT_SUBTLE[1])])

        tree = ttk.Treeview(
            self.content,
            columns=columns,
            show="headings",
            style="Modern.Treeview",
        )
        for cid, cname in zip(columns, col_names):
            tree.heading(cid, text=cname)
            w = (widths or {}).get(cid, 80)
            tree.column(cid, width=w, anchor="center")

        # Alternating row tags
        tree.tag_configure("odd",  background=T.SURFACE_RAISED[1])
        tree.tag_configure("even", background=T.SURFACE[1])

        return tree

    def _show_summary(self) -> None:
        self._clear()

        if not self.form_results:
            T.muted_label(self.content, _("no_results")).pack(pady=40)
            return

        col_ids   = ("q_num", "q_text", "yes", "no", "somewhat", "invalid", "total", "pct")
        col_names = (
            _("question_num_short"), _("question"),
            _("count_yes"), _("count_no"), _("count_somewhat"),
            _("count_invalid"), _("total_responses"), _("pct_distribution"),
        )
        widths = {"q_num": 40, "q_text": 220, "yes": 60, "no": 60,
                  "somewhat": 80, "invalid": 70, "total": 60, "pct": 60}

        tree = self._styled_tree(col_ids, col_names, widths)

        for i in range(14):
            q_num = i + 1
            q_text = (
                self.question_texts[i]
                if self.question_texts and len(self.question_texts) == 14
                else f"Q{q_num}"
            )
            yes  = sum(1 for fr in self.form_results if fr.answers()[i] == "Yes")
            no   = sum(1 for fr in self.form_results if fr.answers()[i] == "No")
            sw   = sum(1 for fr in self.form_results if fr.answers()[i] == "Somewhat")
            inv  = sum(1 for fr in self.form_results if fr.answers()[i] == "Invalid")
            tot  = yes + no + sw + inv
            pct  = f"{yes / tot * 100:.1f}" if tot > 0 else "0.0"
            tag  = "odd" if i % 2 else "even"
            tree.insert("", "end", values=(q_num, q_text, yes, no, sw, inv, tot, pct), tags=(tag,))

        tree.pack(fill="both", expand=True, pady=(0, 8))
        vsb = ttk.Scrollbar(self.content, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=get_end(), fill="y")

    def _show_raw(self) -> None:
        self._clear()

        if not self.form_results:
            T.muted_label(self.content, _("no_results")).pack(pady=40)
            return

        q_cols    = tuple(f"Q{i}" for i in range(1, 15))
        col_ids   = ("form_id",) + q_cols + ("score", "valid")
        col_names = (_("form_id"),) + q_cols + (_("score"), _("valid"))
        widths    = {c: 52 for c in col_ids}
        widths["form_id"] = 130
        widths["score"]   = 60

        tree = self._styled_tree(col_ids, col_names, widths)

        for idx, fr in enumerate(self.form_results):
            row = (fr.form_id,) + tuple(fr.answers()) + (f"{fr.form_score:.1f}", str(fr.valid))
            tag = "odd" if idx % 2 else "even"
            tree.insert("", "end", values=row, tags=(tag,))

        tree.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(self.content, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side=get_end(), fill="y")
        hsb = ttk.Scrollbar(self.content, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")

    # ------------------------------------------------------------------
    # Advanced Analytics tab
    # ------------------------------------------------------------------

    def _get_advanced_data(self) -> dict:
        """Compute (or return cached) advanced analytics results."""
        if self._advanced_data is None:
            self._advanced_data = self.analytics.run_advanced_analytics(
                self.survey_id,
                self.form_results,
                persistence=self.persistence,
            )
        return self._advanced_data

    def _show_advanced(self) -> None:
        self._clear()

        if not self.form_results:
            T.muted_label(self.content, _("no_results")).pack(pady=40)
            return

        # Loading indicator while computing
        loading_lbl = T.muted_label(self.content, _("computing_analytics"))
        loading_lbl.pack(pady=20)
        self.content.update()

        try:
            data = self._get_advanced_data()
        except Exception as exc:
            logger.exception("Advanced analytics failed")
            loading_lbl.destroy()
            T.muted_label(self.content, f"Analytics error: {exc}").pack(pady=20)
            return

        loading_lbl.destroy()

        dimension_scores = data.get("dimension_scores", [])
        question_stats   = data.get("question_stats")
        alerts           = data.get("alerts", [])
        comment_analysis = data.get("comment_analysis", {})
        polarized        = data.get("polarized_questions", [])
        top_corr         = data.get("top_correlations", [])
        invalid_forms    = data.get("invalid_forms", [])

        # ── Section: Dimension KPI cards ──────────────────────────────────
        T.section_title(self.content, _("pedagogical_dimensions")).pack(
            anchor=get_anchor(), pady=(0, 8)
        )
        dim_row = T.transparent(self.content)
        dim_row.pack(fill="x", pady=(0, 16))

        _STATUS_COLORS = {
            "good":     (T.KPI_ANA_NUM,   T.KPI_ANA_BG),
            "warning":  (T.KPI_DRAFT_NUM, T.KPI_DRAFT_BG),
            "critical": (T.DANGER,        T.DANGER_SUBTLE),
        }
        for ds in dimension_scores:
            num_color, bg_color = _STATUS_COLORS.get(ds.status, (T.KPI_TOTAL_NUM, T.KPI_TOTAL_BG))
            card = T.stat_card(
                dim_row,
                label=ds.dimension_name,
                value=f"{ds.mean:.2f}",
                icon_name="trending_up",
                num_color=num_color,
                bg_color=bg_color,
            )
            card.pack(side=get_start(), fill="x", expand=True, padx=(0, 10))

        # ── Section: QA Alerts ────────────────────────────────────────────
        T.section_title(self.content, f"{_('qa_alerts')} ({len(alerts)})").pack(
            anchor=get_anchor(), pady=(8, 6)
        )
        if not alerts:
            ok_card = T.card(self.content)
            ok_card.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                ok_card,
                text=_("all_dimensions_ok"),
                font=T.body(),
                text_color=T.SUCCESS,
            ).pack(padx=T.CARD_PADDING, pady=12)
        else:
            for alert in alerts:
                a_card = T.card(self.content)
                a_card.pack(fill="x", pady=(0, 6))
                inner = T.transparent(a_card)
                inner.pack(fill="x", padx=T.CARD_PADDING, pady=10)

                icon_name = "alert_triangle" if alert.severity == "critical" else "info"
                color = T.DANGER if alert.severity == "critical" else T.WARNING

                ctk.CTkLabel(
                    inner,
                    image=IC.icon(icon_name, size=16, color=color[1] if isinstance(color, tuple) else color),
                    text=f"  {alert.message}",
                    font=T.body(),
                    text_color=color,
                    anchor=get_anchor(),
                    compound=get_compound(),
                    wraplength=900,
                ).pack(anchor=get_anchor())

        # ── Section: Polarized questions ──────────────────────────────────
        if polarized:
            T.section_title(self.content, _("polarized_questions")).pack(
                anchor=get_anchor(), pady=(8, 6)
            )
            p_card = T.card(self.content)
            p_card.pack(fill="x", pady=(0, 12))
            qs_text = ", ".join(f"Q{i}" for i in polarized)
            ctk.CTkLabel(
                p_card,
                text=f"⚠️  {qs_text} — {_('polarized_questions')}",
                font=T.body(),
                text_color=T.WARNING,
                anchor=get_anchor(),
                wraplength=900,
            ).pack(padx=T.CARD_PADDING, pady=12)

        # ── Section: Per-question stats table ─────────────────────────────
        if question_stats is not None and not question_stats.empty:
            T.section_title(self.content, _("per_question_stats")).pack(
                anchor=get_anchor(), pady=(8, 6)
            )
            col_ids   = ("q", "mean", "median", "std_dev", "min", "max", "count")
            col_names = (_("question"), _("mean"), _("median"), _("std_dev"), _("min"), _("max"), _("answered"))
            widths    = {"q": 70, "mean": 70, "median": 70, "std_dev": 70,
                         "min": 50, "max": 50, "count": 80}
            tree = self._styled_tree(col_ids, col_names, widths)
            for idx, (q_idx, row) in enumerate(question_stats.iterrows()):
                q_num = int(q_idx[1:]) if q_idx.startswith("Q") else idx + 1
                q_label = (
                    self.question_texts[q_num - 1][:40]
                    if self.question_texts and len(self.question_texts) >= q_num
                    else q_idx
                )
                tag = "odd" if idx % 2 else "even"
                tree.insert("", "end", values=(
                    q_label,
                    f"{row['mean']:.2f}",
                    f"{row['median']:.1f}",
                    f"{row['std_dev']:.2f}",
                    int(row["min"]),
                    int(row["max"]),
                    int(row["count_answered"]),
                ), tags=(tag,))
            tree.pack(fill="both", expand=True, pady=(0, 12))

        # ── Section: Top correlations ─────────────────────────────────────
        if top_corr:
            T.section_title(self.content, _("top_correlations")).pack(
                anchor=get_anchor(), pady=(8, 6)
            )
            corr_card = T.card(self.content)
            corr_card.pack(fill="x", pady=(0, 12))
            inner = T.transparent(corr_card)
            inner.pack(fill="x", padx=T.CARD_PADDING, pady=10)
            for p in top_corr[:5]:
                color = T.SUCCESS if p["correlation"] > 0 else T.DANGER
                ctk.CTkLabel(
                    inner,
                    text=f"{p['q1']} ↔ {p['q2']}:  r = {p['correlation']:+.3f}",
                    font=T.body(),
                    text_color=color,
                    anchor=get_anchor(),
                ).pack(anchor=get_anchor(), pady=2)

        # ── Section: Invalid forms ────────────────────────────────────────
        if invalid_forms:
            T.section_title(self.content, f"{_('invalid_forms')} ({len(invalid_forms)})").pack(
                anchor=get_anchor(), pady=(8, 6)
            )
            inv_card = T.card(self.content)
            inv_card.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                inv_card,
                text="  " + ", ".join(str(f) for f in invalid_forms[:20])
                     + ("…" if len(invalid_forms) > 20 else ""),
                font=T.small(),
                text_color=T.TEXT_SECONDARY,
                anchor=get_anchor(),
                wraplength=900,
            ).pack(padx=T.CARD_PADDING, pady=10)

        # ── Section: Comment analysis ─────────────────────────────────────
        total_comments = comment_analysis.get("total_comments", 0)
        if total_comments > 0:
            T.section_title(
                self.content, f"{_('comment_analysis')} ({total_comments})"
            ).pack(anchor=get_anchor(), pady=(8, 6))

            sc = comment_analysis["sentiment_counts"]
            kw = comment_analysis["top_keywords"]

            c_card = T.card(self.content)
            c_card.pack(fill="x", pady=(0, 12))
            c_inner = T.transparent(c_card)
            c_inner.pack(fill="x", padx=T.CARD_PADDING, pady=12)

            sent_row = T.transparent(c_inner)
            sent_row.pack(fill="x", pady=(0, 8))
            for label, count, color in [
                (_("positive"), sc["positive"], T.SUCCESS),
                (_("neutral"),  sc["neutral"],  T.TEXT_SECONDARY),
                (_("negative"), sc["negative"], T.DANGER),
            ]:
                chip = T.inner_card(sent_row, corner_radius=T.RADIUS_SM)
                chip.pack(side=get_start(), padx=(0, 10))
                ctk.CTkLabel(
                    chip,
                    text=f"{label}: {count}",
                    font=T.body(),
                    text_color=color,
                ).pack(padx=14, pady=8)

            if kw:
                T.muted_label(c_inner, _("top_keywords")).pack(anchor=get_anchor(), pady=(4, 4))
                kw_row = T.transparent(c_inner)
                kw_row.pack(fill="x")
                for word, count in kw[:12]:
                    chip = T.inner_card(kw_row, corner_radius=20)
                    chip.pack(side=get_start(), padx=(0, 6), pady=2)
                    ctk.CTkLabel(
                        chip,
                        text=f"{word}  ({count})",
                        font=T.small(),
                        text_color=T.ACCENT,
                    ).pack(padx=10, pady=4)

    def _show_trend(self) -> None:
        self._clear()

        if not self.survey:
            T.muted_label(self.content, _("no_trend_data")).pack(pady=40)
            return

        trend = self.analytics.get_trend_data(self.survey, self.persistence)
        if len(trend) <= 1:
            T.muted_label(self.content, _("no_trend_data")).pack(pady=40)
            return

        col_ids   = ("semester", "academic_year", "form_count", "batch_score")
        col_names = (_("semester"), _("academic_year"), _("forms"), _("score"))
        widths    = {"semester": 160, "academic_year": 160, "form_count": 100, "batch_score": 120}

        tree = self._styled_tree(col_ids, col_names, widths)
        for idx, entry in enumerate(trend):
            tag = "odd" if idx % 2 else "even"
            tree.insert("", "end", values=(
                entry["semester"], entry["academic_year"],
                entry["form_count"], f"{entry['batch_score']:.1f}%",
            ), tags=(tag,))

        tree.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------

    def _on_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title=_("export_csv"),
        )
        if not path:
            return
        try:
            self.analytics.export_csv(self.form_results, path, self.question_texts)
            messagebox.showinfo(rtl_text(_("export_success")), rtl_text(_("export_success")))
        except Exception as exc:
            logger.exception("CSV export failed")
            messagebox.showerror(rtl_text(_("export_error")), rtl_text(f"{_('export_error')}:\n{exc}"))

    def _on_dari_report(self) -> None:
        try:
            from config import Config
            import report_generator
            
            report_path = str(Config.PROJECT_ROOT / "assets" / "dari_qa_report.html")
            advanced_data = self._get_advanced_data()
            report_generator.generate_dari_qa_report(self.survey, self.form_results, report_path, advanced_data=advanced_data)
            
            webbrowser.open(f"file:///{Path(report_path).resolve()}")
        except Exception as exc:
            logger.exception("Dari report generation failed")
            messagebox.showerror(rtl_text(_("error_report")), rtl_text(f"{_('error_report')}:\n{exc}"))

    def _on_pdf(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title=_("export_pdf_report"),
        )
        if not path:
            return
        try:
            self.analytics.export_pdf_report(
                self.survey, self.form_results, path, self.question_texts
            )
            messagebox.showinfo(rtl_text(_("export_success")), rtl_text(_("export_success")))
        except Exception as exc:
            logger.exception("PDF export failed")
            messagebox.showerror(rtl_text(_("export_error")), rtl_text(f"{_('export_error')}:\n{exc}"))

    def _on_html(self) -> None:
        try:
            import pandas as pd

            rows = []
            for fr in self.form_results:
                row: dict[str, Any] = {
                    "Form_ID": fr.form_id,
                    "Form_Score": fr.form_score,
                    "Valid": fr.valid,
                }
                for i, ans in enumerate(fr.answers(), start=1):
                    row[f"Q{i}"] = ans
                rows.append(row)

            df = pd.DataFrame(rows) if rows else pd.DataFrame(
                columns=["Form_ID"] + [f"Q{i}" for i in range(1, 15)] + ["Form_Score", "Valid"]
            )
            report_path = self.analytics.generate_report(df, question_texts=self.question_texts)
            webbrowser.open(f"file:///{Path(report_path).resolve()}")
        except Exception as exc:
            logger.exception("HTML report failed")
            messagebox.showerror(rtl_text(_("error_report")), rtl_text(f"{_('error_report')}:\n{exc}"))

    def _on_advanced_html(self) -> None:
        """Generate and open the advanced QA analytics HTML report."""
        try:
            import pandas as pd
            from plotly_generator import PlotlyGenerator

            rows = []
            for fr in self.form_results:
                row: dict[str, Any] = {
                    "Form_ID": fr.form_id,
                    "Form_Score": fr.form_score,
                    "Valid": fr.valid,
                }
                for i, ans in enumerate(fr.answers(), start=1):
                    row[f"Q{i}"] = ans
                rows.append(row)

            df = pd.DataFrame(rows) if rows else pd.DataFrame(
                columns=["Form_ID"] + [f"Q{i}" for i in range(1, 15)] + ["Form_Score", "Valid"]
            )

            form_count = len(self.form_results)
            batch_score = (
                sum(fr.form_score for fr in self.form_results) / form_count
                if form_count > 0 else 0.0
            )

            advanced_data = self._get_advanced_data()

            html = PlotlyGenerator.generate_dashboard_html(
                df,
                batch_score,
                question_texts=self.question_texts,
                mode="advanced",
                advanced_data=advanced_data,
            )

            from config import Config
            report_path = str(Config.PROJECT_ROOT / "assets" / "report_advanced.html")
            with open(report_path, "w", encoding="utf-8") as fh:
                fh.write(html)

            webbrowser.open(f"file:///{Path(report_path).resolve()}")
        except Exception as exc:
            logger.exception("Advanced HTML report failed")
            messagebox.showerror(rtl_text(_("error_report")), rtl_text(f"{_('error_report')}:\n{exc}"))
