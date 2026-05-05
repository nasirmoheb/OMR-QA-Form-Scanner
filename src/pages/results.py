"""Results page — summary table, raw data, trend analysis, and exports."""

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
from i18n import _
from models import FormResult, Survey
from persistence import PersistenceManager
from .base import BasePage, PageRouter

logger = logging.getLogger("omr_qa_scanner")


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

        IC.icon_button(
            header, "arrow_left", text="  " + _("back"),
            size=14, color=T._D_TEXT2, width=110, height=36,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.GHOST_TEXT, border_width=1, border_color=T.GHOST_BORDER,
            font=T.body(), command=lambda: self.go("dashboard"),
        ).pack(side="left")

        T.page_title(header, _("results")).pack(side="left", padx=16)

        # -- Survey meta card ----
        if self.survey:
            meta = T.card(self)
            meta.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))

            meta_inner = T.transparent(meta)
            meta_inner.pack(fill="x", padx=T.CARD_PADDING, pady=14)

            top_row = T.transparent(meta_inner)
            top_row.pack(fill="x")

            ctk.CTkLabel(
                top_row,
                image=IC.icon("book", size=16, color=T._D_TEXT1),
                text=f"  {self.survey.subject}",
                font=T.h3(), text_color=T.TEXT_PRIMARY, anchor="w",
                compound="left",
            ).pack(side="left")

            T.status_chip(top_row, self.survey.status).pack(side="left", padx=(12, 0))

            ctk.CTkLabel(
                meta_inner,
                image=IC.icon("user", size=12, color=T._D_TEXT2),
                text=f"  {self.survey.professor}   •   {self.survey.semester}   •   {self.survey.academic_year}",
                font=T.small(), text_color=T.TEXT_SECONDARY, anchor="w",
                compound="left",
            ).pack(anchor="w", pady=(6, 0))

            # KPI chips
            form_count = len(self.form_results)
            batch_score = (
                sum(fr.form_score for fr in self.form_results) / form_count
                if form_count > 0 else 0.0
            )
            kpi_row = T.transparent(meta_inner)
            kpi_row.pack(fill="x", pady=(10, 0))

            for label, value in [
                (_("forms_count", count=form_count), "forms"),
                (_("batch_score_label", score=batch_score), "score"),
            ]:
                chip = T.inner_card(kpi_row, corner_radius=T.RADIUS_SM)
                chip.pack(side="left", padx=(0, 10))
                ctk.CTkLabel(
                    chip,
                    text=label,
                    font=T.small(),
                    text_color=T.TEXT_SECONDARY,
                ).pack(padx=12, pady=6)

        # -- Tab switcher ----
        tab_card = T.card(self)
        tab_card.pack(fill="x", padx=T.PAGE_PADDING, pady=(12, 0))

        self.tab_var = tk.StringVar(value=_("summary_view"))
        seg = ctk.CTkSegmentedButton(
            tab_card,
            values=[_("summary_view"), _("raw_data_view"), _("trend_analysis")],
            command=self._on_tab,
            variable=self.tab_var,
            font=T.body(),
            height=38,
            corner_radius=T.RADIUS_MD,
            fg_color=T.SURFACE_RAISED,
            selected_color=T.ACCENT,
            selected_hover_color=T.ACCENT_HOVER,
            unselected_color=T.SURFACE_RAISED,
            unselected_hover_color=T.GHOST_HOVER,
        )
        seg.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # -- Content area ----
        self.content = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.content.pack(
            fill="both", expand=True,
            padx=T.PAGE_PADDING, pady=(12, 0),
        )

        # -- Export bar ----
        export_bar = T.card(self)
        export_bar.pack(fill="x", padx=T.PAGE_PADDING, pady=(12, T.PAGE_PADDING))

        export_inner = T.transparent(export_bar)
        export_inner.pack(fill="x", padx=T.CARD_PADDING, pady=12)

        T.section_title(export_inner, _("export_csv")).pack(side="left")

        IC.icon_button(
            export_inner, "download", text="  " + _("export_csv"),
            size=14, color="#FFFFFF", width=160,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF", font=T.font(13, "bold"),
            corner_radius=T.RADIUS_MD, command=self._on_csv,
        ).pack(side="right", padx=(8, 0))

        IC.icon_button(
            export_inner, "file_text", text="  " + _("export_pdf_report"),
            size=14, color=T._D_TEXT2, width=180,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.GHOST_TEXT, border_width=1, border_color=T.GHOST_BORDER,
            font=T.body(), corner_radius=T.RADIUS_MD, command=self._on_pdf,
        ).pack(side="right", padx=(8, 0))

        IC.icon_button(
            export_inner, "globe", text="  " + _("view_html_report"),
            size=14, color=T._D_TEXT2, width=180,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.GHOST_TEXT, border_width=1, border_color=T.GHOST_BORDER,
            font=T.body(), corner_radius=T.RADIUS_MD, command=self._on_html,
        ).pack(side="right")

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

    def _styled_tree(self, columns: tuple, col_names: tuple, widths: dict | None = None) -> ttk.Treeview:
        """Create a styled Treeview with alternating row colours."""
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Modern.Treeview",
            background="#FFFFFF",
            foreground="#0F172A",
            rowheight=32,
            fieldbackground="#FFFFFF",
            borderwidth=0,
            font=("Segoe UI", 11),
        )
        style.configure(
            "Modern.Treeview.Heading",
            background="#F1F5F9",
            foreground="#475569",
            font=("Segoe UI", 11, "bold"),
            borderwidth=0,
            relief="flat",
        )
        style.map("Modern.Treeview", background=[("selected", "#EFF6FF")])

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
        tree.tag_configure("odd",  background="#F8FAFC")
        tree.tag_configure("even", background="#FFFFFF")

        return tree

    def _show_summary(self) -> None:
        self._clear()

        if not self.form_results:
            T.muted_label(self.content, _("no_results")).pack(pady=40)
            return

        col_ids   = ("q_num", "q_text", "yes", "no", "somewhat", "invalid", "total", "pct")
        col_names = (
            _("question_num_short"), "Question",
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
        vsb.pack(side="right", fill="y")

    def _show_raw(self) -> None:
        self._clear()

        if not self.form_results:
            T.muted_label(self.content, _("no_results")).pack(pady=40)
            return

        q_cols    = tuple(f"Q{i}" for i in range(1, 15))
        col_ids   = ("form_id",) + q_cols + ("score", "valid")
        col_names = ("Form ID",) + q_cols + ("Score", "Valid")
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
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(self.content, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")

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
        col_names = (_("semester"), _("academic_year"), "Forms", "Score")
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
            messagebox.showinfo(_("export_success"), _("export_success"))
        except Exception as exc:
            logger.exception("CSV export failed")
            messagebox.showerror(_("export_error"), f"{_('export_error')}:\n{exc}")

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
            messagebox.showinfo(_("export_success"), _("export_success"))
        except Exception as exc:
            logger.exception("PDF export failed")
            messagebox.showerror(_("export_error"), f"{_('export_error')}:\n{exc}")

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
            messagebox.showerror(_("error_report"), f"{_('error_report')}:\n{exc}")
