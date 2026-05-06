"""Survey create / edit form page."""

from __future__ import annotations

import logging
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

import icons as IC
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

        # -- Header ----
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        # Title
        title_text = "Edit Evaluation Survey" if self.survey_id else "Create New Evaluation Survey"
        ctk.CTkLabel(
            header, text=title_text, font=T.h1(), text_color=T.TEXT_PRIMARY
        ).pack(anchor="w")

        # Subtitle
        subtitle_text = "Configure the metadata for the new optical mark recognition survey. This information will be printed on the\nheader of the physical forms."
        ctk.CTkLabel(
            header, text=subtitle_text, font=T.small(), text_color=T.TEXT_SECONDARY, justify="left"
        ).pack(anchor="w", pady=(4, 0))

        # -- Main Content (2 Columns) ----
        content_wrap = T.transparent(self)
        content_wrap.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        left_col = ctk.CTkScrollableFrame(content_wrap, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 16))

        right_col = T.transparent(content_wrap)
        right_col.pack(side="right", fill="y", padx=(16, 0))

        # -------------------------------------------------------------
        # LEFT COLUMN
        # -------------------------------------------------------------

        # -- Institution Details Card ----
        inst_card = T.card(left_col)
        inst_card.pack(fill="x", pady=(0, 16))

        inst_header = T.transparent(inst_card)
        inst_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            inst_header, text="  Institution Details", image=IC.icon("school", size=18, color=T.ACCENT[1]),
            font=T.h2(), text_color=T.TEXT_PRIMARY, compound="left"
        ).pack(anchor="w")

        inst_grid = T.transparent(inst_card)
        inst_grid.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
        inst_grid.columnconfigure(0, weight=1)
        inst_grid.columnconfigure(1, weight=1)

        uni_name = self.persistence.get_setting("university_name", "Kabul University")
        self._field(inst_grid, "University", "university", row=0, col=0, default=uni_name)
        self._field(inst_grid, "Faculty", "faculty", row=0, col=1)
        self._field(inst_grid, "Department", "department", row=1, col=0, colspan=2)

        # -- Course Information Card ----
        course_card = T.card(left_col)
        course_card.pack(fill="x", pady=(0, 16))

        course_header = T.transparent(course_card)
        course_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            course_header, text="  Course Information", image=IC.icon("book", size=18, color=T.ACCENT[1]),
            font=T.h2(), text_color=T.TEXT_PRIMARY, compound="left"
        ).pack(anchor="w")

        course_grid = T.transparent(course_card)
        course_grid.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
        course_grid.columnconfigure(0, weight=1)
        course_grid.columnconfigure(1, weight=1)

        self._field(course_grid, "Subject", "subject", row=0, col=0, colspan=2)
        self._field(course_grid, "Professor Name", "professor", row=1, col=0, colspan=2)
        self._field(course_grid, "Semester", "semester", row=2, col=0)
        self._field(course_grid, "Academic Year", "academic_year", row=2, col=1)

        # -------------------------------------------------------------
        # RIGHT COLUMN
        # -------------------------------------------------------------

        # -- Survey Actions Card ----
        action_card = T.card(right_col)
        action_card.pack(fill="x", ipadx=10)

        action_header = T.transparent(action_card)
        action_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            action_header, text="SURVEY ACTIONS",
            font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
        ).pack(anchor="w")

        action_body = T.transparent(action_card)
        action_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Save Survey
        ctk.CTkButton(
            action_body, text="  Save Survey", image=IC.icon("save", size=16, color="#000000"),
            height=44, corner_radius=T.RADIUS_MD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(14, "bold"), command=self._on_save,
        ).pack(fill="x", pady=(0, 12))

        # Print Survey Form
        self.print_btn = ctk.CTkButton(
            action_body, text="  Print Survey Form", image=IC.icon("print_icon", size=16, color=T.TEXT_PRIMARY[1]),
            height=44, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(13), border_width=1, border_color=T.CARD_BORDER,
            state="disabled" if not self.survey_id else "normal", command=self._on_print,
        )
        self.print_btn.pack(fill="x", pady=(0, 16))

        # Discard Draft
        ctk.CTkButton(
            action_body, text="  Discard Draft", image=IC.icon("trash", size=16, color=T.TEXT_SECONDARY[1]),
            height=36, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_SECONDARY, font=T.font(13), command=lambda: self.go("dashboard"),
        ).pack(fill="x")

    def _field(
        self,
        grid: ctk.CTkFrame,
        label: str,
        key: str,
        row: int,
        col: int,
        colspan: int = 1,
        default: str = "",
        readonly: bool = False,
    ) -> None:
        """Add a labelled entry to the grid."""
        wrap = T.transparent(grid)
        # Handle padding for columns correctly.
        # If it spans both columns, use regular padding
        # If it's col 0, padding right. If col 1, padding left.
        px = (0, 0)
        if colspan == 1:
            px = (0, 8) if col == 0 else (8, 0)
        
        wrap.grid(row=row, column=col, columnspan=colspan, padx=px, pady=8, sticky="ew")

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
