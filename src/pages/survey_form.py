"""Survey create / edit form page."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

import theme as T
from i18n import _
from models import Survey
from persistence import PersistenceManager
from .base import BasePage, PageRouter

logger = logging.getLogger("omr_qa_scanner")


class SurveyFormPage(BasePage):
    """Two-column form for creating or editing a survey."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        survey_id: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.survey_id = survey_id
        self._entries: dict[str, ctk.CTkEntry] = {}

        self._build()
        if survey_id:
            self._load()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # ── Header ─────────────────────────────────────────────────────
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        T.secondary_btn(
            header,
            f"← {_('back')}",
            width=100,
            height=36,
            command=lambda: self.go("dashboard"),
        ).pack(side="left")

        T.page_title(
            header,
            _("edit_survey") if self.survey_id else _("new_survey"),
        ).pack(side="left", padx=16)

        # ── Scrollable body ────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        # ── Form card ──────────────────────────────────────────────────
        form_card = T.card(scroll)
        form_card.pack(fill="x", pady=(0, 16))

        T.section_title(form_card, "📋  " + _("new_survey")).pack(
            anchor="w", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0)
        )
        T.divider(form_card).pack(fill="x", padx=T.CARD_PADDING, pady=(12, 0))

        grid = T.transparent(form_card)
        grid.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        # University (read-only)
        uni_name = self.persistence.get_setting("university_name", "")
        self._field(grid, _("university"), "university", row=0, col=0, default=uni_name, readonly=True)

        # Editable fields — two columns
        fields = [
            (_("faculty"),        "faculty",        1, 0),
            (_("department"),     "department",     1, 1),
            (_("subject"),        "subject",        2, 0),
            (_("professor_name"), "professor",      2, 1),
            (_("semester"),       "semester",       3, 0),
            (_("academic_year"),  "academic_year",  3, 1),
        ]
        for label, key, row, col in fields:
            self._field(grid, label, key, row=row, col=col)

        # ── Action buttons ─────────────────────────────────────────────
        btn_row = T.transparent(scroll)
        btn_row.pack(fill="x", pady=(0, 16))

        T.primary_btn(
            btn_row,
            f"💾  {_('save_survey')}",
            command=self._on_save,
            width=180,
        ).pack(side="left", padx=(0, 10))

        self.print_btn = T.secondary_btn(
            btn_row,
            f"🖨  {_('print_form')}",
            command=self._on_print,
            width=180,
            state="disabled" if not self.survey_id else "normal",
        )
        self.print_btn.pack(side="left")

    def _field(
        self,
        grid: ctk.CTkFrame,
        label: str,
        key: str,
        row: int,
        col: int,
        default: str = "",
        readonly: bool = False,
    ) -> None:
        """Add a labelled entry to the grid."""
        wrap = T.transparent(grid)
        wrap.grid(row=row, column=col, padx=(0, 12) if col == 0 else (12, 0), pady=8, sticky="ew")

        T.muted_label(wrap, label).pack(anchor="w", pady=(0, 4))

        entry = T.text_input(wrap)
        if default:
            entry.insert(0, default)
        if readonly:
            entry.configure(
                state="disabled",
                fg_color=T.CHIP_BG,
                text_color=T.TEXT_MUTED,
            )
        entry.pack(fill="x")
        self._entries[key] = entry

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _load(self) -> None:
        survey = self.persistence.get_survey(self.survey_id)
        if not survey:
            return
        mapping = {
            "faculty":       survey.faculty,
            "department":    survey.department,
            "subject":       survey.subject,
            "professor":     survey.professor,
            "semester":      survey.semester,
            "academic_year": survey.academic_year,
        }
        for key, val in mapping.items():
            e = self._entries.get(key)
            if e and val:
                e.delete(0, "end")
                e.insert(0, val)

    def _on_save(self) -> None:
        def get(key: str) -> str:
            e = self._entries.get(key)
            return e.get().strip() if e else ""

        uni = self.persistence.get_setting("university_name", "")
        survey = Survey(
            university=uni,
            faculty=get("faculty"),
            department=get("department"),
            subject=get("subject"),
            professor=get("professor"),
            semester=get("semester"),
            academic_year=get("academic_year"),
            status="Draft",
        )

        if self.survey_id:
            survey.id = self.survey_id
            survey.updated_at = datetime.now().isoformat()
            self.persistence.update_survey(survey)
        else:
            saved = self.persistence.create_survey(survey)
            self.survey_id = saved.id
            self.print_btn.configure(state="normal")

        self.go("dashboard")

    def _on_print(self) -> None:
        if not self.survey_id:
            messagebox.showwarning(_("print_form"), "Save the survey first.")
            return
        survey = self.persistence.get_survey(self.survey_id)
        if not survey:
            messagebox.showerror(_("print_form"), "Survey not found.")
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
            messagebox.showerror(_("print_form"), str(exc))
        except Exception as exc:
            logger.exception("PDF generation failed")
            messagebox.showerror(_("print_form"), f"Failed to generate PDF:\n{exc}")
