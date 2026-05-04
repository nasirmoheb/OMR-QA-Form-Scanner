"""Dashboard page — survey list with search, filters, and stat cards."""

from __future__ import annotations

import logging
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

import theme as T
from i18n import _
from models import Survey
from persistence import PersistenceManager
from .base import BasePage, PageRouter

logger = logging.getLogger("omr_qa_scanner")


class DashboardPage(BasePage):
    """Main landing page: KPI row + searchable survey card list."""

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

        self._build()
        self._load_surveys()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # ── Top bar ────────────────────────────────────────────────────
        top = T.transparent(self)
        top.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        T.page_title(top, _("dashboard")).pack(side="left")

        T.primary_btn(
            top,
            f"＋  {_('new_survey')}",
            command=lambda: self.go("survey_form"),
            width=160,
        ).pack(side="right")

        # ── KPI stat row ───────────────────────────────────────────────
        self._stat_row = T.transparent(self)
        self._stat_row.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))
        # Populated in _load_surveys

        # ── Search / filter bar ────────────────────────────────────────
        bar = T.card(self)
        bar.pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))

        bar_inner = T.transparent(bar)
        bar_inner.pack(fill="x", padx=16, pady=12)

        # Search icon + entry
        search_wrap = T.transparent(bar_inner)
        search_wrap.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            search_wrap,
            text="🔍",
            font=T.body(),
            text_color=T.TEXT_MUTED,
        ).pack(side="left", padx=(0, 6))

        self.search_entry = ctk.CTkEntry(
            search_wrap,
            placeholder_text=_("search"),
            height=38,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
            font=T.body(),
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", lambda _e: self._load_surveys())

        # Department filter
        self.dept_filter = ctk.CTkOptionMenu(
            bar_inner,
            values=[_("all_departments")],
            command=lambda _v: self._load_surveys(),
            width=200,
            height=38,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            button_color=T.ACCENT,
            button_hover_color=T.ACCENT_HOVER,
            font=T.body(),
        )
        self.dept_filter.pack(side="right", padx=(12, 0))

        # ── Survey list ────────────────────────────────────────────────
        self.list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        self.list_frame.pack(
            fill="both", expand=True,
            padx=T.PAGE_PADDING, pady=(12, T.PAGE_PADDING),
        )

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_surveys(self) -> None:
        search = self.search_entry.get().strip() or None
        dept = self.dept_filter.get()
        if dept == _("all_departments"):
            dept = None

        self.current_surveys = self.persistence.list_surveys(
            search=search, department=dept
        )
        self._refresh_stats()
        self._refresh_list()
        self._refresh_dept_filter()

    def _refresh_stats(self) -> None:
        for w in self._stat_row.winfo_children():
            w.destroy()

        all_surveys = self.persistence.list_surveys()
        total   = len(all_surveys)
        draft   = sum(1 for s in all_surveys if s.status == "Draft")
        proc    = sum(1 for s in all_surveys if s.status == "Processed")
        analyzed = sum(1 for s in all_surveys if s.status == "Analyzed")

        stats = [
            (_("dashboard") + " Total", str(total),   "📋", T.ACCENT),
            ("Draft",                   str(draft),    "◐",  T.STATUS_DRAFT),
            ("Processed",               str(proc),     "◑",  T.STATUS_PROCESSED),
            ("Analyzed",                str(analyzed), "●",  T.STATUS_ANALYZED),
        ]

        for label, value, icon, color in stats:
            c = T.stat_card(self._stat_row, label, value, icon, color)
            c.pack(side="left", fill="x", expand=True, padx=(0, 12))

    def _refresh_list(self) -> None:
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.survey_cards.clear()

        if not self.current_surveys:
            empty = T.card(self.list_frame)
            empty.pack(fill="x", pady=8)
            ctk.CTkLabel(
                empty,
                text="📭  " + _("no_surveys"),
                font=T.body(),
                text_color=T.TEXT_MUTED,
            ).pack(pady=40)
            return

        for survey in self.current_surveys:
            c = self._make_card(survey)
            c.pack(fill="x", pady=(0, 10))
            self.survey_cards.append(c)

    def _refresh_dept_filter(self) -> None:
        all_surveys = self.persistence.list_surveys()
        depts = sorted({s.department for s in all_surveys if s.department})
        self.dept_filter.configure(values=[_("all_departments")] + depts)

    # ------------------------------------------------------------------
    # Survey card
    # ------------------------------------------------------------------

    def _make_card(self, survey: Survey) -> ctk.CTkFrame:
        card = T.card(self.list_frame)
        card.configure(cursor="hand2")

        inner = T.transparent(card)
        inner.pack(fill="both", expand=True, padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # ── Left: content ──────────────────────────────────────────────
        left = T.transparent(inner)
        left.pack(side="left", fill="both", expand=True)

        # Title row
        title_row = T.transparent(left)
        title_row.pack(fill="x")

        ctk.CTkLabel(
            title_row,
            text=survey.subject or "—",
            font=T.h3(),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left")

        T.status_chip(title_row, survey.status).pack(side="left", padx=(12, 0))

        # Professor
        T.muted_label(
            left,
            f"👤  {survey.professor}" if survey.professor else "",
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # Meta chips
        chips_row = T.transparent(left)
        chips_row.pack(fill="x", pady=(10, 0))

        for val in [survey.semester, survey.academic_year, survey.department, survey.faculty]:
            if val:
                T.tag_chip(chips_row, val).pack(side="left", padx=(0, 6))

        # ── Right: actions ─────────────────────────────────────────────
        right = T.transparent(inner)
        right.pack(side="right", fill="y", padx=(16, 0))

        if survey.status == "Draft":
            self._draft_actions(right, survey)
        else:
            self._done_actions(right, survey)

        # Click anywhere on card to select
        card.bind("<Button-1>", lambda _e, sid=survey.id: self._select(sid))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _e, sid=survey.id: self._select(sid))

        return card

    def _draft_actions(self, parent: ctk.CTkFrame, survey: Survey) -> None:
        """Folder picker + Process + Edit + Delete for Draft surveys."""
        folder_entry = ctk.CTkEntry(
            parent,
            placeholder_text=_("select_folder"),
            height=34,
            width=200,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
            font=T.small(),
        )
        folder_entry.pack(fill="x", pady=(0, 6))

        browse_row = T.transparent(parent)
        browse_row.pack(fill="x", pady=(0, 8))

        T.secondary_btn(
            browse_row,
            f"📁  {_('browse')}",
            height=32,
            font=T.small(),
            command=lambda e=folder_entry: self._browse(e),
        ).pack(side="right")

        T.primary_btn(
            parent,
            f"▶  {_('process')}",
            height=34,
            font=T.font(12, "bold"),
            command=lambda sid=survey.id, e=folder_entry: self._on_process(sid, e.get()),
        ).pack(fill="x", pady=(0, 6))

        T.secondary_btn(
            parent,
            f"✏  {_('edit_survey')}",
            height=32,
            font=T.small(),
            command=lambda sid=survey.id: self._on_edit(sid),
        ).pack(fill="x", pady=(0, 6))

        T.danger_btn(
            parent,
            f"🗑  {_('delete')}",
            height=32,
            font=T.small(),
            command=lambda sid=survey.id: self._on_delete(sid),
        ).pack(fill="x")

    def _done_actions(self, parent: ctk.CTkFrame, survey: Survey) -> None:
        """Results + Delete for Processed/Analyzed surveys."""
        T.primary_btn(
            parent,
            f"📊  {_('results')}",
            height=36,
            command=lambda sid=survey.id: self._on_results(sid),
        ).pack(fill="x", pady=(0, 8))

        T.danger_btn(
            parent,
            f"🗑  {_('delete')}",
            height=32,
            font=T.small(),
            command=lambda sid=survey.id: self._on_delete(sid),
        ).pack(fill="x")

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------

    def _browse(self, entry: ctk.CTkEntry) -> None:
        folder = filedialog.askdirectory(title=_("select_folder"))
        if folder:
            entry.delete(0, "end")
            entry.insert(0, folder)

    def _select(self, survey_id: int) -> None:
        self.selected_survey_id = survey_id
        for i, s in enumerate(self.current_surveys):
            if i < len(self.survey_cards):
                if s.id == survey_id:
                    self.survey_cards[i].configure(border_color=T.ACCENT)
                else:
                    self.survey_cards[i].configure(border_color=T.CARD_BORDER)

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
