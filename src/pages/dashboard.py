"""Dashboard page - Asan Hesab dark-navy palette."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from i18n import _, is_rtl, I18n, rtl_text
from models import Survey
from persistence import PersistenceManager
from .base import BasePage, PageRouter

import webbrowser
from config import Config
import report_generator
logger = logging.getLogger("tadris_qa_system")

_SORT_OPTIONS = ["Newest first", "Oldest first", "Subject A->Z", "Subject Z->A"]


class DashboardPage(BasePage):
    """Main landing page - Asan Hesab dark-navy style."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        analytics: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.analytics = analytics
        self.current_surveys: list[Survey] = []
        self.selected_survey_id: int | None = None
        self.survey_cards: list[ctk.CTkFrame] = []
        self._sort_mode = _SORT_OPTIONS[0]

        self._build()
        self._load_surveys()
        I18n.register_listener(self._on_language_change)

    def destroy(self) -> None:
        I18n.unregister_listener(self._on_language_change)
        super().destroy()

    def _on_language_change(self) -> None:
        """Rebuild the entire page when the language (and thus direction) changes."""
        for w in self.winfo_children():
            w.destroy()
        self._build()
        self._load_surveys()

    # RTL helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _start() -> str:
        """The 'natural start' side for the current language."""
        return "right" if is_rtl() else "left"

    @staticmethod
    def _end() -> str:
        """The 'natural end' side for the current language."""
        return "left" if is_rtl() else "right"

    @staticmethod
    def _anchor() -> str:
        return "e" if is_rtl() else "w"

    @staticmethod
    def _compound() -> str:
        """Icon compound direction: icon leads text on the start side."""
        return "right" if is_rtl() else "left"

    @staticmethod
    def _pad_start(n: int) -> tuple:
        """Padding on the start side only."""
        return (0, n) if is_rtl() else (0, n)

    @staticmethod
    def _pad_after(n: int) -> tuple:
        """(before, after) padding where 'after' is toward the end."""
        return (n, 0) if is_rtl() else (0, n)

    # ----
    # Skeleton
    # ----

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # 1 -- Toolbar
        self._build_toolbar()

        # 2 -- KPI row (rebuilt on every data load)
        self._kpi_row = T.transparent(self)
        self._kpi_row.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        # 3 -- Recent Surveys header
        header_wrap = T.transparent(self)
        header_wrap.pack(fill="x", padx=T.PAGE_PADDING, pady=(24, 0))
        
        ctk.CTkLabel(
            header_wrap,
            text=_("recent_surveys"),
            font=T.h2(),
            text_color=T.TEXT_PRIMARY
        ).pack(side=self._start())
        
        ctk.CTkButton(
            header_wrap,
            text=_("view_all") + " ->",
            font=T.body(),
            text_color=T.ACCENT,
            fg_color="transparent",
            hover_color=T.SURFACE_RAISED,
            width=0
        ).pack(side=self._end())

        # 4 -- Scrollable survey list
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=T.CARD_BORDER,
            scrollbar_button_hover_color=T.ACCENT,
        )
        self.list_frame.pack(
            fill="both", expand=True,
            padx=T.PAGE_PADDING,
            pady=(14, T.PAGE_PADDING),
        )

    # -- Toolbar ----

    def _build_toolbar(self) -> None:
        bar = T.transparent(self)
        bar.pack(fill="x", padx=T.PAGE_PADDING, pady=(14, 0))

        S = self._start()   # "left" in LTR, "right" in RTL
        E = self._end()     # "right" in LTR, "left" in RTL

        # Title
        title_lbl = T.page_title(bar, text=_("dashboard"))
        title_lbl.pack(side=S)

        # Right container for search and icons
        right_wrap = T.transparent(bar)
        right_wrap.pack(side=E)

        # Search Entry
        search_wrap = ctk.CTkFrame(
            right_wrap, corner_radius=T.RADIUS_MD, fg_color=T.INPUT_BG, border_width=1, border_color=T.INPUT_BORDER
        )
        search_wrap.pack(side=E)
        
        ctk.CTkLabel(
            search_wrap,
            image=IC.icon("search", size=16, color=T._D_TEXT3),
            text="",
        ).pack(side=self._start(), padx=(10, 5))

        self.search_entry = ctk.CTkEntry(
            search_wrap,
            placeholder_text=_("search_surveys"),
            height=36, width=200,
            corner_radius=T.RADIUS_MD,
            fg_color="transparent",
            border_width=0,
            font=T.body(),
            text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
        )
        self.search_entry.pack(side=self._start(), fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda _e: self._load_surveys())

    # ----
    # Data
    # ----

    def _load_surveys(self) -> None:
        search = self.search_entry.get().strip() or None
        dept   = None

        surveys = self.persistence.list_surveys(search=search, department=dept)
        surveys = self._apply_sort(surveys)
        self.current_surveys = surveys

        self._refresh_kpis()
        self._refresh_list()

    def _apply_sort(self, surveys: list[Survey]) -> list[Survey]:
        m = self._sort_mode
        if m == "Newest first":
            return sorted(surveys, key=lambda s: s.created_at or "", reverse=True)
        if m == "Oldest first":
            return sorted(surveys, key=lambda s: s.created_at or "")
        if m == "Subject A->Z":
            return sorted(surveys, key=lambda s: (s.subject or "").lower())
        if m == "Subject Z->A":
            return sorted(surveys, key=lambda s: (s.subject or "").lower(), reverse=True)
        return surveys

    def _on_sort(self, value: str) -> None:
        self._sort_mode = value
        self._load_surveys()

    # -- KPI row ----

    def _refresh_kpis(self) -> None:
        for w in self._kpi_row.winfo_children():
            w.destroy()

        all_s    = self.persistence.list_surveys()
        total    = len(all_s)
        draft    = sum(1 for s in all_s if s.status == "Draft")
        proc     = sum(1 for s in all_s if s.status == "Processed")
        analyzed = sum(1 for s in all_s if s.status == "Analyzed")

        kpis = [
            (_("total_surveys"), str(total),    "folder",      T.KPI_TOTAL_NUM, T.KPI_TOTAL_BG, False),
            (_("draft"),         str(draft),    "clock",       T.KPI_DRAFT_NUM, T.KPI_DRAFT_BG, False),
            (_("processed"),     str(proc),     "scan",        T.KPI_PROC_NUM,  T.KPI_PROC_BG,  False),
            (_("analyzed"),      str(analyzed), "trending_up", T.KPI_ANA_NUM,   T.KPI_ANA_BG,   False),
        ]

        for label, value, icon_name, num_color, bg_color, is_active in kpis:
            c = T.stat_card(
                self._kpi_row,
                label=label, value=value,
                icon_name=icon_name, num_color=num_color, bg_color=bg_color,
                is_active=is_active
            )
            c.pack(side=self._start(), fill="x", expand=True, padx=(0, 12))

    # -- Survey list ----

    def _refresh_list(self) -> None:
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.survey_cards.clear()

        if not self.current_surveys:
            self._empty_state()
            return

        for survey in self.current_surveys:
            c = self._make_card(survey)
            c.pack(fill="x", pady=(0, 10))
            self.survey_cards.append(c)

    # Removed _refresh_dept_filter as we removed the department filter

    def _empty_state(self) -> None:
        wrap = ctk.CTkFrame(
            self.list_frame,
            corner_radius=T.RADIUS_LG,
            fg_color=T.SURFACE,
            border_width=0,
        )
        wrap.pack(fill="x", pady=8)

        inner = T.transparent(wrap)
        inner.pack(pady=52)

        ctk.CTkLabel(
            inner,
            image=IC.icon("file_text", size=48, color=T._D_TEXT3),
            text="",
        ).pack()

        ctk.CTkLabel(
            inner,
            text=_("no_surveys"),
            font=T.font(15, "bold"),
            text_color=T.TEXT_SECONDARY,
        ).pack(pady=(12, 4))

        ctk.CTkLabel(
            inner,
            text=_("create_first_survey"),
            font=T.small(),
            text_color=T.TEXT_MUTED,
        ).pack()

        IC.icon_button(
            inner,
            name="plus",
            text="  " + _("new_survey"),
            size=14,
            color="#FFFFFF",
            command=lambda: self.go("survey_form"),
            width=160, height=38,
            fg_color=T.ACCENT,
            hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=T.font(12, "bold"),
            corner_radius=T.RADIUS_MD,
        ).pack(pady=(20, 0))

    # ----
    # Survey card
    # ----

    def _make_card(self, survey: Survey) -> ctk.CTkFrame:
        status        = survey.status
        stripe_color  = T.status_stripe_color(status)
        status_meta   = {
            "Draft":     (T._D_AMBER,  T._D_AMBER_BG,  "clock"),
            "Processed": (T._D_BLUE,   T._D_BLUE_BG,   "scan"),
            "Analyzed":  (T._D_GREEN,  T._D_GREEN_BG,  "trending_up"),
        }
        accent_hex, accent_bg_hex, status_icon = status_meta.get(
            status, (T._D_TEXT2, T._D_CARD_RAISED, "info")
        )

        S = self._start()   # "left" LTR / "right" RTL
        E = self._end()     # "right" LTR / "left" RTL
        A = self._anchor()  # "w" LTR / "e" RTL
        C = self._compound()  # "left" LTR / "right" RTL

        # ── Outer card ──────────────────────────────────────────────────────
        outer = ctk.CTkFrame(
            self.list_frame,
            corner_radius=T.RADIUS_LG,
            fg_color=T.SURFACE,
            border_width=0,
            cursor="hand2",
        )

        # Main wrapper
        wrap = T.transparent(outer)
        wrap.pack(fill="both", expand=True, padx=T.CARD_PADDING, pady=16)

        # Left section: Document icon
        icon_box = ctk.CTkFrame(
            wrap, width=44, height=44, corner_radius=T.RADIUS_MD, fg_color=T.SURFACE_RAISED
        )
        icon_box.pack(side=S, padx=(24, 0) if is_rtl() else (0, 24))
        icon_box.pack_propagate(False)
        ctk.CTkLabel(
            icon_box, text="", image=IC.icon("file_text", size=20, color=T.TEXT_SECONDARY[1])
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Center section: Subject + Status (top), Meta (bottom)
        center = T.transparent(wrap)
        center.pack(side=S, fill="both", expand=True)

        top_row = T.transparent(center)
        top_row.pack(anchor=A, pady=(0, 4))

        # Subject
        ctk.CTkLabel(
            top_row,
            text=survey.subject or "—",
            font=T.font(16, "bold"),
            text_color=T.TEXT_PRIMARY,
        ).pack(side=S)

        # Status badge
        badge_frame = ctk.CTkFrame(
            top_row, fg_color=accent_bg_hex, corner_radius=T.RADIUS_SM,
        )
        badge_frame.pack(side=S, padx=(12, 0))
        ctk.CTkLabel(
            badge_frame,
            text=f"  {_(status.lower())}" if not is_rtl() else f"{_(status.lower())}  ",
            font=T.font(11, "bold"),
            text_color=accent_hex,
        ).pack(padx=8, pady=2)

        # Meta row
        meta_row = T.transparent(center)
        meta_row.pack(anchor=A)

        def _meta_chip(parent, icon_name: str, text: str) -> None:
            w = T.transparent(parent)
            w.pack(side=S, padx=(0, 16))
            ctk.CTkLabel(
                w, image=IC.icon(icon_name, size=14, color=T._D_TEXT3),
                text=f"  {text}" if not is_rtl() else f"{text}  ",
                font=T.small(), text_color=T.TEXT_SECONDARY, compound=C,
            ).pack(side=S)

        if survey.professor:
            _meta_chip(meta_row, "user", survey.professor)
        if survey.department:
            _meta_chip(meta_row, "building", survey.department)
        if survey.semester:
            _meta_chip(meta_row, "calendar", survey.semester)
        if survey.academic_year:
            _meta_chip(meta_row, "clock", survey.academic_year)
        if survey.faculty:
            _meta_chip(meta_row, "book", survey.faculty)

        # ── Action buttons (on the end side) ─────────────────────────────────
        actions = T.transparent(wrap)
        actions.pack(side=E)

        if status == "Draft":
            self._draft_actions(actions, survey)
        else:
            self._done_actions(actions, survey)

        # ── Hover effect ─────────────────────────────────────────────────────
        def _enter(_e):  outer.configure(fg_color=T.SURFACE_RAISED)
        def _leave(_e):  outer.configure(fg_color=T.SURFACE)

        for w in (outer, wrap, center, top_row, meta_row):
            w.bind("<Enter>",   _enter)
            w.bind("<Leave>",   _leave)
            w.bind("<Button-1>", lambda _e, sid=survey.id: self._select(sid))

        return outer

    # ----
    # Action panels
    # ----

    def _draft_actions(self, parent: ctk.CTkFrame, survey: Survey) -> None:
        # Print button
        IC.icon_button(
            parent, "printer", text="",
            size=16, color=T.TEXT_SECONDARY[1],
            width=38, height=38, corner_radius=T.RADIUS_SM,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            command=lambda sid=survey.id: self._on_print(sid),
        ).pack(side=self._start(), padx=self._pad_after(6))

        # Edit/Process buttons
        IC.icon_button(
            parent, "edit", text="",
            size=16, color=T.TEXT_SECONDARY[1],
            width=38, height=38, corner_radius=T.RADIUS_SM,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            command=lambda sid=survey.id: self._on_edit(sid),
        ).pack(side=self._start(), padx=self._pad_after(6))

        # Delete button
        IC.icon_button(
            parent, "trash", text="",
            size=16, color=T._D_RED,
            width=38, height=38, corner_radius=T.RADIUS_SM,
            fg_color="transparent", hover_color=T.DANGER_SUBTLE,
            command=lambda sid=survey.id: self._on_delete(sid),
        ).pack(side=self._start(), padx=self._pad_after(16))

        # Process button (primary)
        ctk.CTkButton(
            parent,
            text="  " + _("process"),
            image=IC.icon("cpu", size=16, color="#000000"),
            height=38, corner_radius=T.RADIUS_MD,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(13, "bold"),
            command=lambda sid=survey.id: self._on_process_click(sid),
        ).pack(side=self._start())

    def _done_actions(self, parent: ctk.CTkFrame, survey: Survey) -> None:
        btn_color = T.STATUS_ANALYZED[1] if survey.status == "Analyzed" else T.ACCENT[1]
        btn_hover = T.SUCCESS[1]        if survey.status == "Analyzed" else T.ACCENT_HOVER[1]
        icon_name = "trending_up"    if survey.status == "Analyzed" else "bar_chart"
        btn_text_color = "#000000"

        # Print button
        IC.icon_button(
            parent, "printer", text="",
            size=16, color=T.TEXT_SECONDARY[1],
            width=38, height=38, corner_radius=T.RADIUS_SM,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            command=lambda sid=survey.id: self._on_print(sid),
        ).pack(side=self._start(), padx=self._pad_after(6))

        # Reprocess button
        IC.icon_button(
            parent, "cpu", text="",
            size=16, color=T.TEXT_SECONDARY[1],
            width=38, height=38, corner_radius=T.RADIUS_SM,
            fg_color="transparent", hover_color=T.SURFACE_RAISED,
            command=lambda sid=survey.id: self._on_process_click(sid),
        ).pack(side=self._start(), padx=self._pad_after(6))

        # Delete button
        IC.icon_button(
            parent, "trash", text="",
            size=16, color=T._D_RED,
            width=38, height=38, corner_radius=T.RADIUS_SM,
            fg_color="transparent", hover_color=T.DANGER_SUBTLE,
            command=lambda sid=survey.id: self._on_delete(sid),
        ).pack(side=self._start(), padx=self._pad_after(16))

        # Results button (primary)
        ctk.CTkButton(
            parent,
            text="  " + _("results"),
            image=IC.icon(icon_name, size=16, color=btn_text_color),
            height=38, corner_radius=T.RADIUS_MD,
            fg_color=btn_color, hover_color=btn_hover,
            text_color=btn_text_color, font=T.font(13, "bold"),
            command=lambda sid=survey.id: self._on_results(sid),
        ).pack(side=self._start())

    # ----
    # Interaction
    # ----

    def _browse(self, entry: ctk.CTkEntry) -> None:
        folder = filedialog.askdirectory(title=_("select_folder"))
        if folder:
            entry.delete(0, "end")
            entry.insert(0, folder)

    def _select(self, survey_id: int) -> None:
        self.selected_survey_id = survey_id
        for i, s in enumerate(self.current_surveys):
            if i < len(self.survey_cards):
                # Selected card gets a subtle accent left-border highlight
                self.survey_cards[i].configure(
                    fg_color=T.ACCENT_SUBTLE if s.id == survey_id else T.SURFACE
                )

    def _on_edit(self, survey_id: int) -> None:
        self.go("survey_form", survey_id=survey_id)

    def _on_process_click(self, survey_id: int) -> None:
        """Open folder dialog immediately, then navigate to process page."""
        folder = filedialog.askdirectory(title=_("select_folder"))
        if not folder:
            return
        if not Path(folder).exists():
            messagebox.showwarning(rtl_text(_("select_folder")), rtl_text(_("no_folder")))
            return
        self.go("process", survey_id=survey_id, folder_path=folder)

    def _on_process(self, survey_id: int, folder_path: str) -> None:
        if not folder_path or not Path(folder_path).exists():
            messagebox.showwarning(rtl_text(_("select_folder")), rtl_text(_("no_folder")))
            return
        self.go("process", survey_id=survey_id, folder_path=folder_path)

    def _on_results(self, survey_id: int) -> None:
        """Directly open the Official Dari Report for analyzed/processed surveys."""
        survey = self.persistence.get_survey(survey_id)
        if not survey:
            messagebox.showerror(rtl_text(_("error")), rtl_text("Survey not found."))
            return

        try:
            results = self.persistence.get_form_results(survey_id)
            if not results:
                messagebox.showwarning(rtl_text(_("results")), rtl_text("No processed forms found for this survey."))
                return

            # Use writable reports directory instead of Program Files
            reports_dir = Config.get_reports_dir()
            report_path = str(reports_dir / "dari_qa_report.html")
            
            # Compute advanced analytics data
            advanced_data = self.analytics.run_advanced_analytics(
                survey_id,
                results,
                persistence=self.persistence,
            )
            
            report_generator.generate_dari_qa_report(survey, results, report_path, advanced_data=advanced_data)
            
            webbrowser.open(f"file:///{Path(report_path).resolve()}")
        except Exception as exc:
            logger.exception("Dari report generation failed")
            messagebox.showerror(rtl_text(_("error_report")), rtl_text(f"Failed to generate report:\n{exc}"))

    def _on_print(self, survey_id: int) -> None:
        survey = self.persistence.get_survey(survey_id)
        if not survey:
            messagebox.showerror(rtl_text(_("print_form")), rtl_text("Survey not found."))
            return
        try:
            from pdf_generator import generate_prefilled_form, open_pdf

            tmp = Path(tempfile.mkdtemp())
            name = (
                f"survey_{survey.id}_{survey.subject or 'form'}"
                .replace(" ", "_").replace("/", "-")[:60]
            )
            out = tmp / f"{name}.pdf"
            generate_prefilled_form(survey, out, persistence=self.persistence)
            open_pdf(out)
        except RuntimeError as exc:
            messagebox.showerror(rtl_text(_("print_form")), rtl_text(str(exc)))
        except Exception as exc:
            logger.exception("PDF generation failed")
            messagebox.showerror(rtl_text(_("print_form")), rtl_text(f"Failed to generate PDF:\n{exc}"))

    def _on_delete(self, survey_id: int) -> None:
        if messagebox.askyesno(rtl_text(_("delete")), rtl_text(_("confirm_delete"))):
            self.persistence.delete_survey(survey_id)
            if self.selected_survey_id == survey_id:
                self.selected_survey_id = None
            self._load_surveys()
