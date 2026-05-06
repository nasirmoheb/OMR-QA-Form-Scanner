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
from i18n import _, is_rtl, get_start, get_end, get_anchor, get_compound, rtl_text
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

    # RTL helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _start() -> str:
        return "right" if is_rtl() else "left"

    @staticmethod
    def _end() -> str:
        return "left" if is_rtl() else "right"

    @staticmethod
    def _anchor() -> str:
        return "e" if is_rtl() else "w"

    @staticmethod
    def _compound() -> str:
        return "right" if is_rtl() else "left"

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.configure(fg_color=T.PAGE_BG)

        # -- Header ----
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        # Title
        title_text = _("edit_evaluation_survey") if self.survey_id else _("create_new_evaluation_survey")
        ctk.CTkLabel(
            header, text=title_text, font=T.h1(), text_color=T.TEXT_PRIMARY
        ).pack(anchor=get_anchor())

        # Subtitle
        subtitle_text = _("survey_form_subtitle")
        ctk.CTkLabel(
            header, text=subtitle_text, font=T.small(), text_color=T.TEXT_SECONDARY, justify=self._start()
        ).pack(anchor=self._anchor(), pady=(4, 0))

        # -- Main Content (2 Columns) ----
        content_wrap = T.transparent(self)
        content_wrap.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        # Actions panel is always on the left; form fields always expand to the right.
        actions_col = T.transparent(content_wrap)
        actions_col.pack(side="left", fill="y", padx=(0, 16))

        form_col = ctk.CTkScrollableFrame(content_wrap, fg_color="transparent")
        form_col.pack(side="left", fill="both", expand=True)

        # -------------------------------------------------------------
        # LEFT COLUMN — Actions
        # -------------------------------------------------------------

        # -- Survey Actions Card ----
        action_card = T.card(actions_col)
        action_card.pack(fill="x", ipadx=10)

        action_header = T.transparent(action_card)
        action_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            action_header, text=_("survey_actions"),
            font=T.font(12, "bold"), text_color=T.TEXT_SECONDARY
        ).pack(anchor=self._anchor())

        action_body = T.transparent(action_card)
        action_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Save Survey
        ctk.CTkButton(
            action_body, text=_("save_survey") + "  " if is_rtl() else "  " + _("save_survey"),
            image=IC.icon("save", size=16, color="#000000"),
            height=44, corner_radius=T.RADIUS_MD, fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(14, "bold"), command=self._on_save,
            compound=self._compound(),
        ).pack(fill="x", pady=(0, 12))

        # Print Survey Form
        self.print_btn = ctk.CTkButton(
            action_body, text=_("print_form") + "  " if is_rtl() else "  " + _("print_form"),
            image=IC.icon("print_icon", size=16, color=T.TEXT_PRIMARY[1]),
            height=44, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_PRIMARY, font=T.font(13), border_width=1, border_color=T.CARD_BORDER,
            state="disabled" if not self.survey_id else "normal", command=self._on_print,
            compound=self._compound(),
        )
        self.print_btn.pack(fill="x", pady=(0, 16))

        # Discard Draft
        ctk.CTkButton(
            action_body, text=_("discard_draft") + "  " if is_rtl() else "  " + _("discard_draft"),
            image=IC.icon("trash", size=16, color=T.TEXT_SECONDARY[1]),
            height=36, corner_radius=T.RADIUS_MD, fg_color="transparent", hover_color=T.SURFACE_RAISED,
            text_color=T.TEXT_SECONDARY, font=T.font(13), command=lambda: self.go("dashboard"),
            compound=self._compound(),
        ).pack(fill="x")

        # -------------------------------------------------------------
        # RIGHT COLUMN — Form fields
        # -------------------------------------------------------------

        # -- Institution Details Card ----
        inst_card = T.card(form_col)
        inst_card.pack(fill="x", pady=(0, 16))

        inst_header = T.transparent(inst_card)
        inst_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            inst_header, text=_("university_branding") + "  " if is_rtl() else "  " + _("university_branding"),
            image=IC.icon("school", size=18, color=T.ACCENT[1]),
            font=T.h2(), text_color=T.TEXT_PRIMARY, compound=self._compound()
        ).pack(anchor=self._anchor())

        inst_grid = T.transparent(inst_card)
        inst_grid.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
        inst_grid.columnconfigure(0, weight=1)
        inst_grid.columnconfigure(1, weight=1)

        uni_name = self.persistence.get_setting("university_name", "Kabul University")
        self._field(inst_grid, _("university"), "university", row=0, col=0 if not is_rtl() else 1, default=uni_name)
        self._field(inst_grid, _("faculty"), "faculty", row=0, col=1 if not is_rtl() else 0)
        self._field(inst_grid, _("department"), "department", row=1, col=0, colspan=2)

        # -- Course Information Card ----
        course_card = T.card(form_col)
        course_card.pack(fill="x", pady=(0, 16))

        course_header = T.transparent(course_card)
        course_header.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))
        ctk.CTkLabel(
            course_header, text=_("course_information") + "  " if is_rtl() else "  " + _("course_information"),
            image=IC.icon("book", size=18, color=T.ACCENT[1]),
            font=T.h2(), text_color=T.TEXT_PRIMARY, compound=self._compound()
        ).pack(anchor=self._anchor())

        course_grid = T.transparent(course_card)
        course_grid.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)
        course_grid.columnconfigure(0, weight=1)
        course_grid.columnconfigure(1, weight=1)

        self._field(course_grid, _("subject"), "subject", row=0, col=0, colspan=2)
        self._field(course_grid, _("professor_name"), "professor", row=1, col=0, colspan=2)
        self._field(course_grid, _("semester"), "semester", row=2, col=0)
        self._field(course_grid, _("academic_year"), "academic_year", row=2, col=1)

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
        # Only add horizontal padding when two inputs share a row (colspan == 1).
        # Add 8px padding on each side so there's a 16px gap between the two fields.
        px = (0, 0)
        if colspan == 1:
            px = (4, 4)  # 4px on each side = 8px gap between fields
        
        wrap.grid(row=row, column=col, columnspan=colspan, padx=px, pady=8, sticky="ew")

        T.muted_label(wrap, label + " *").pack(anchor=self._anchor(), pady=(0, 4))

        entry = T.text_input(wrap, justify="right" if is_rtl() else "left")
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

        # Validate all required fields
        required_fields = {
            "faculty": _("faculty"),
            "department": _("department"),
            "subject": _("subject"),
            "professor": _("professor_name"),
            "semester": _("semester"),
            "academic_year": _("academic_year"),
        }
        
        missing_fields = []
        for key, label in required_fields.items():
            if not get(key):
                missing_fields.append(label)
        
        if missing_fields:
            fields_list = "\n• ".join(missing_fields)
            messagebox.showwarning(
                rtl_text(_("save_survey")),
                rtl_text(f"{_('required_fields_missing')}\n\n• {fields_list}")
            )
            return

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
            messagebox.showwarning(
                rtl_text(_("print_form")),
                rtl_text("Save the survey first.")
            )
            return
        survey = self.persistence.get_survey(self.survey_id)
        if not survey:
            messagebox.showerror(
                rtl_text(_("print_form")),
                rtl_text("Survey not found.")
            )
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
            messagebox.showerror(
                rtl_text(_("print_form")),
                rtl_text(f"Failed to generate PDF:\n{exc}")
            )
