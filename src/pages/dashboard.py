"""Dashboard page - Asan Hesab dark-navy palette."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from i18n import _
from models import Survey
from persistence import PersistenceManager
from .base import BasePage, PageRouter

logger = logging.getLogger("omr_qa_scanner")

_SORT_OPTIONS = ["Newest first", "Oldest first", "Subject A->Z", "Subject Z->A"]


class DashboardPage(BasePage):
    """Main landing page - Asan Hesab dark-navy style."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.current_surveys: list[Survey] = []
        self.selected_survey_id: int | None = None
        self.survey_cards: list[ctk.CTkFrame] = []
        self._sort_mode = _SORT_OPTIONS[0]

        self._build()
        self._load_surveys()

    # ----
    # Skeleton
    # ----

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # 1 -- Greeting card
        self._build_greeting()

        # 2 -- KPI row (rebuilt on every data load)
        self._kpi_row = T.transparent(self)
        self._kpi_row.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))

        # 3 -- Toolbar
        self._build_toolbar()

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

    # -- Greeting card ----

    def _build_greeting(self) -> None:
        now  = datetime.now()
        hour = now.hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"

        # Full-width card matching the reference header card
        card = ctk.CTkFrame(
            self,
            corner_radius=T.RADIUS_LG,
            fg_color=T.SURFACE,
            border_width=0,
        )
        card.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        inner = T.transparent(card)
        inner.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Left: greeting text
        left = T.transparent(inner)
        left.pack(side="left", fill="y")

        ctk.CTkLabel(
            left,
            text=greeting,
            font=T.font(20, "bold"),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text="OMR QA Form Scanner",
            font=T.small(),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(3, 0))

        # Right: date + icon badge
        right = T.transparent(inner)
        right.pack(side="right", fill="y")

        date_col = T.transparent(right)
        date_col.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(date_col, text=now.strftime("%H:%M"),
                     font=T.font(22, "bold"), text_color=T.TEXT_PRIMARY).pack(anchor="e")
        ctk.CTkLabel(date_col, text=now.strftime("%A"),
                     font=T.tiny(), text_color=T.TEXT_SECONDARY).pack(anchor="e")
        ctk.CTkLabel(date_col, text=now.strftime("%d %b %Y"),
                     font=T.tiny(), text_color=T.TEXT_MUTED).pack(anchor="e")

        # Icon badge
        badge = ctk.CTkFrame(right, width=52, height=52,
                             corner_radius=T.RADIUS_MD, fg_color=T.ACCENT)
        badge.pack(side="left")
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge,
            image=IC.icon("omr", size=26, color="#FFFFFF"),
            text="",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # New Survey button
        IC.icon_button(
            inner,
            name="plus",
            text="  " + _("new_survey"),
            size=15,
            color="#FFFFFF",
            command=lambda: self.go("survey_form"),
            width=165, height=40,
            fg_color=T.ACCENT,
            hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=T.font(13, "bold"),
            corner_radius=T.RADIUS_MD,
        ).pack(side="right", padx=(0, 16))

    # -- Toolbar ----

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(
            self,
            corner_radius=T.RADIUS_LG,
            fg_color=T.SURFACE,
            border_width=0,
        )
        bar.pack(fill="x", padx=T.PAGE_PADDING, pady=(14, 0))

        inner = T.transparent(bar)
        inner.pack(fill="x", padx=16, pady=10)

        # Search
        search_wrap = T.transparent(inner)
        search_wrap.pack(side="left", fill="x", expand=True)

        # Search icon
        ctk.CTkLabel(
            search_wrap,
            image=IC.icon("search", size=16, color=T._D_TEXT3),
            text="",
        ).pack(side="left", padx=(0, 8))

        self.search_entry = ctk.CTkEntry(
            search_wrap,
            placeholder_text=_("search"),
            height=36,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
            font=T.body(),
            text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda _e: self._load_surveys())

        # Count label
        self._count_lbl = ctk.CTkLabel(
            inner,
            text="",
            font=T.small(),
            text_color=T.TEXT_MUTED,
        )
        self._count_lbl.pack(side="right", padx=(10, 0))

        # Department filter
        self.dept_filter = ctk.CTkOptionMenu(
            inner,
            values=[_("all_departments")],
            command=lambda _v: self._load_surveys(),
            width=180,
            height=36,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            button_color=T.INPUT_BORDER,
            button_hover_color=T.ACCENT,
            text_color=T.TEXT_PRIMARY,
            dropdown_fg_color=T.SURFACE_RAISED,
            dropdown_text_color=T.TEXT_PRIMARY,
            dropdown_hover_color=T.SURFACE_OVERLAY,
            font=T.body(),
        )
        self.dept_filter.pack(side="right", padx=(10, 0))

        # Sort
        self.sort_menu = ctk.CTkOptionMenu(
            inner,
            values=_SORT_OPTIONS,
            command=self._on_sort,
            width=150,
            height=36,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            button_color=T.INPUT_BORDER,
            button_hover_color=T.ACCENT,
            text_color=T.TEXT_PRIMARY,
            dropdown_fg_color=T.SURFACE_RAISED,
            dropdown_text_color=T.TEXT_PRIMARY,
            dropdown_hover_color=T.SURFACE_OVERLAY,
            font=T.body(),
        )
        self.sort_menu.set(_SORT_OPTIONS[0])
        self.sort_menu.pack(side="right", padx=(10, 0))

    # ----
    # Data
    # ----

    def _load_surveys(self) -> None:
        search = self.search_entry.get().strip() or None
        dept   = self.dept_filter.get()
        if dept == _("all_departments"):
            dept = None

        surveys = self.persistence.list_surveys(search=search, department=dept)
        surveys = self._apply_sort(surveys)
        self.current_surveys = surveys

        self._refresh_kpis()
        self._refresh_list()
        self._refresh_dept_filter()

        n = len(surveys)
        self._count_lbl.configure(text=f"{n} survey{'s' if n != 1 else ''}")

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
            ("Total Surveys", str(total),    "layers",      T.KPI_TOTAL_NUM, T.KPI_TOTAL_BG),
            ("Draft",         str(draft),    "clock",       T.KPI_DRAFT_NUM, T.KPI_DRAFT_BG),
            ("Processed",     str(proc),     "scan",        T.KPI_PROC_NUM,  T.KPI_PROC_BG),
            ("Analyzed",      str(analyzed), "trending_up", T.KPI_ANA_NUM,   T.KPI_ANA_BG),
        ]

        for label, value, icon_name, num_color, bg_color in kpis:
            c = T.stat_card(
                self._kpi_row,
                label=label, value=value,
                icon_name=icon_name, num_color=num_color, bg_color=bg_color,
            )
            c.pack(side="left", fill="x", expand=True, padx=(0, 12))

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

    def _refresh_dept_filter(self) -> None:
        all_s = self.persistence.list_surveys()
        depts = sorted({s.department for s in all_s if s.department})
        self.dept_filter.configure(values=[_("all_departments")] + depts)

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
            text="Create your first survey to get started.",
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
        stripe_color = T.status_stripe_color(survey.status)

        # Outer card - no border, just the surface colour
        outer = ctk.CTkFrame(
            self.list_frame,
            corner_radius=T.RADIUS_LG,
            fg_color=T.SURFACE,
            border_width=0,
            cursor="hand2",
        )

        # 5-px left status stripe
        stripe = ctk.CTkFrame(
            outer,
            width=5,
            corner_radius=0,
            fg_color=stripe_color,
        )
        stripe.pack(side="left", fill="y")
        stripe.pack_propagate(False)

        # Body
        body = T.transparent(outer)
        body.pack(side="left", fill="both", expand=True,
                  padx=(16, T.CARD_PADDING), pady=T.CARD_PADDING)

        # -- Left: info ----
        left = T.transparent(body)
        left.pack(side="left", fill="both", expand=True)

        # Row 1: subject + status chip
        r1 = T.transparent(left)
        r1.pack(fill="x")

        ctk.CTkLabel(
            r1,
            text=survey.subject or "-",
            font=T.font(14, "bold"),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        T.status_chip(r1, survey.status).pack(side="left", padx=(10, 0))

        # Row 2: professor
        if survey.professor:
            r2 = T.transparent(left)
            r2.pack(fill="x", pady=(5, 0))
            ctk.CTkLabel(
                r2,
                image=IC.icon("user", size=13, color=T._D_TEXT3),
                text=f"  {survey.professor}",
                font=T.small(), text_color=T.TEXT_SECONDARY, anchor="w",
                compound="left",
            ).pack(side="left")

        # Row 3: meta chips
        r3 = T.transparent(left)
        r3.pack(fill="x", pady=(10, 0))

        chip_defs = [
            (survey.semester,      "calendar"),
            (survey.academic_year, "clock"),
            (survey.department,    "building"),
            (survey.faculty,       "book"),
        ]
        for val, icon_name in chip_defs:
            if val:
                chip = ctk.CTkFrame(r3, fg_color=T.CHIP_BG, corner_radius=T.RADIUS_SM)
                chip.pack(side="left", padx=(0, 6))
                ctk.CTkLabel(
                    chip,
                    image=IC.icon(icon_name, size=11, color=T._D_TEXT2),
                    text=f"  {val}",
                    font=T.tiny(),
                    text_color=T.CHIP_TEXT,
                    compound="left",
                ).pack(padx=8, pady=3)

        # -- Right: actions ----
        right = T.transparent(body)
        right.pack(side="right", fill="y", padx=(12, 0))

        if survey.status == "Draft":
            self._draft_actions(right, survey)
        else:
            self._done_actions(right, survey)

        # -- Hover: lighten card bg ----
        def _enter(_e):
            outer.configure(fg_color=T.SURFACE_RAISED)

        def _leave(_e):
            outer.configure(fg_color=T.SURFACE)

        for w in [outer, stripe, body, left, r1]:
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            w.bind("<Button-1>", lambda _e, sid=survey.id: self._select(sid))

        return outer

    # ----
    # Action panels
    # ----

    def _draft_actions(self, parent: ctk.CTkFrame, survey: Survey) -> None:
        folder_entry = ctk.CTkEntry(
            parent, placeholder_text="Folder path...",
            height=32, width=200, corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG, border_color=T.INPUT_BORDER, border_width=1,
            font=T.small(), text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
        )
        folder_entry.pack(fill="x", pady=(0, 5))

        browse_row = T.transparent(parent)
        browse_row.pack(fill="x", pady=(0, 8))

        IC.icon_button(
            browse_row, "folder", text="  " + _("browse"),
            size=13, color=T._D_TEXT2,
            height=28, corner_radius=T.RADIUS_SM,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.TEXT_SECONDARY,
            border_width=1, border_color=T.GHOST_BORDER,
            font=T.tiny(),
            command=lambda e=folder_entry: self._browse(e),
        ).pack(side="right")

        IC.icon_button(
            parent, "scan", text="  " + _("process"),
            size=14, color="#FFFFFF",
            height=34, corner_radius=T.RADIUS_MD,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF", font=T.font(12, "bold"),
            command=lambda sid=survey.id, e=folder_entry: self._on_process(sid, e.get()),
        ).pack(fill="x", pady=(0, 5))

        btn_row = T.transparent(parent)
        btn_row.pack(fill="x")

        IC.icon_button(
            btn_row, "edit", text="",
            size=14, color=T._D_TEXT2,
            width=34, height=30, corner_radius=T.RADIUS_SM,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.TEXT_SECONDARY,
            border_width=1, border_color=T.GHOST_BORDER,
            command=lambda sid=survey.id: self._on_edit(sid),
        ).pack(side="left", padx=(0, 5))

        IC.icon_button(
            btn_row, "trash", text="",
            size=14, color=T._D_RED,
            width=34, height=30, corner_radius=T.RADIUS_SM,
            fg_color=T.DANGER_SUBTLE, hover_color=T.DANGER,
            text_color=T.DANGER,
            command=lambda sid=survey.id: self._on_delete(sid),
        ).pack(side="left")

    def _done_actions(self, parent: ctk.CTkFrame, survey: Survey) -> None:
        btn_color = T.STATUS_ANALYZED if survey.status == "Analyzed" else T.ACCENT
        btn_hover = T.SUCCESS if survey.status == "Analyzed" else T.ACCENT_HOVER
        icon_name = "trending_up" if survey.status == "Analyzed" else "bar_chart"

        IC.icon_button(
            parent, icon_name, text="  " + _("results"),
            size=15, color="#FFFFFF",
            height=36, corner_radius=T.RADIUS_MD,
            fg_color=btn_color, hover_color=btn_hover,
            text_color="#FFFFFF", font=T.font(12, "bold"),
            command=lambda sid=survey.id: self._on_results(sid),
        ).pack(fill="x", pady=(0, 8))

        IC.icon_button(
            parent, "trash", text="  " + _("delete"),
            size=12, color=T._D_RED,
            height=28, corner_radius=T.RADIUS_SM,
            fg_color=T.DANGER_SUBTLE, hover_color=T.DANGER,
            text_color=T.DANGER, font=T.small(),
            command=lambda sid=survey.id: self._on_delete(sid),
        ).pack(fill="x")

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

    def _on_process(self, survey_id: int, folder_path: str) -> None:
        if not folder_path or not Path(folder_path).exists():
            messagebox.showwarning(_("select_folder"), _("no_folder"))
            return
        self.go("process", survey_id=survey_id, folder_path=folder_path)

    def _on_results(self, survey_id: int) -> None:
        self.go("results", survey_id=survey_id)

    def _on_delete(self, survey_id: int) -> None:
        if messagebox.askyesno(_("delete"), _("confirm_delete")):
            self.persistence.delete_survey(survey_id)
            if self.selected_survey_id == survey_id:
                self.selected_survey_id = None
            self._load_surveys()
