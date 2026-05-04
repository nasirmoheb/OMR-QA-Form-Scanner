"""GUI layer: CustomTkinter desktop interface for the OMR scanner."""

from __future__ import annotations

import os
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

import customtkinter as ctk

from analytics_engine import AnalyticsEngine
from config import Config, setup_logging
from data_store import DataStore
from i18n import I18n, _
from models import Survey, FormResult
from pdf_generator import generate_prefilled_form, open_pdf
from persistence import PersistenceManager
from settings_page import SettingsFrame
from vision_processor import VisionProcessor

logger = setup_logging()


class PageRouter:
    """Manages navigation between different pages in the application."""

    def __init__(self, root: ctk.CTk, content_frame: ctk.CTkFrame) -> None:
        self.root = root
        self.content_frame = content_frame
        self.current_page: ctk.CTkFrame | None = None
        self.pages: dict[str, Callable[[], ctk.CTkFrame]] = {}

    def register_page(self, name: str, factory: Callable[[], ctk.CTkFrame]) -> None:
        """Register a page factory."""
        self.pages[name] = factory

    def navigate(self, page_name: str, **kwargs: Any) -> None:
        """Navigate to a registered page."""
        if self.current_page:
            self.current_page.pack_forget()
            self.current_page.destroy()

        if page_name in self.pages:
            kwargs["master"] = self.content_frame
            self.current_page = self.pages[page_name](**kwargs)
            self.current_page.pack(fill="both", expand=True)
        else:
            logger.error("Unknown page: %s", page_name)


class BasePage(ctk.CTkFrame):
    """Base class for all pages with common functionality."""

    def __init__(self, router: PageRouter, navigate_callback: Callable[[str, Any], None] | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.router = router
        self.navigate_callback = navigate_callback


class DashboardPage(BasePage):
    """Survey list table with search and filters."""

    def __init__(self, router: PageRouter, persistence: PersistenceManager, **kwargs: Any) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self._create_widgets()
        self._load_surveys()

    def _create_widgets(self) -> None:
        # Header with title and new button
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(16, 8), padx=20, fill="x")

        title = ctk.CTkLabel(
            header_frame,
            text=_("dashboard"),
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left")

        new_btn = ctk.CTkButton(
            header_frame,
            text="+ " + _("new_survey"),
            command=lambda: self.navigate_callback("survey_form") if self.navigate_callback else None,
            width=140,
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        new_btn.pack(side="right")

        # Search and filter bar
        filter_frame = ctk.CTkFrame(self, corner_radius=12)
        filter_frame.pack(padx=20, pady=(0, 10), fill="x")

        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text=_("search"),
            width=280,
            height=36,
            corner_radius=8,
        )
        self.search_entry.pack(side="left", padx=12, pady=12)
        self.search_entry.bind("<KeyRelease>", self._on_search)

        self.dept_filter = ctk.CTkOptionMenu(
            filter_frame,
            values=[_("all_departments")],
            command=self._on_filter_dept,
            width=180,
            height=36,
            corner_radius=8,
        )
        self.dept_filter.pack(side="right", padx=12, pady=12)

        # Survey list using scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.scrollable_frame.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        self.current_surveys: list[Survey] = []
        self.selected_survey_id: int | None = None
        self.survey_cards: list[ctk.CTkFrame] = []

    def _load_surveys(self) -> None:
        """Load surveys from database."""
        search = self.search_entry.get().strip() or None
        dept = self.dept_filter.get()
        if dept == _("all_departments"):
            dept = None

        self.current_surveys = self.persistence.list_surveys(
            search=search, department=dept
        )
        self._update_table()
        self._update_department_filter()

    def _update_table(self) -> None:
        """Update the scrollable frame with survey cards."""
        # Clear existing cards
        for card in self.survey_cards:
            card.destroy()
        self.survey_cards.clear()

        if not self.current_surveys:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=_("no_surveys"),
                font=ctk.CTkFont(size=14),
                text_color="gray",
            )
            empty_label.pack(pady=40)
            return

        # Create survey cards
        for survey in self.current_surveys:
            card = self._create_survey_card(survey)
            card.pack(fill="x", padx=10, pady=8)
            self.survey_cards.append(card)

    def _update_department_filter(self) -> None:
        """Update department filter dropdown with unique departments."""
        all_surveys = self.persistence.list_surveys()
        departments = sorted(set(s.department for s in all_surveys if s.department))
        values = [_("all_departments")] + departments
        self.dept_filter.configure(values=values)

    def _browse_folder(self, entry: ctk.CTkEntry) -> None:
        """Open folder dialog and populate the given entry."""
        folder = filedialog.askdirectory(title=_("select_folder"))
        if folder:
            entry.delete(0, "end")
            entry.insert(0, folder)

    def _create_survey_card(self, survey: Survey) -> ctk.CTkFrame:
        """Create a modern card widget for a survey."""
        card = ctk.CTkFrame(
            self.scrollable_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray95", "gray15"),
        )

        status_colors = {
            "Draft": ("#F59E0B", "#D97706"),
            "Processed": ("#3B82F6", "#2563EB"),
            "Analyzed": ("#10B981", "#059669"),
        }
        status_fg, status_hover = status_colors.get(survey.status, ("gray", "gray"))

        # --- Left content area ---
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=14, pady=14)

        subject_label = ctk.CTkLabel(
            content,
            text=survey.subject,
            font=ctk.CTkFont(size=17, weight="bold"),
        )
        subject_label.pack(anchor="w")

        prof_label = ctk.CTkLabel(
            content,
            text=f"{_('professor')}: {survey.professor}",
            font=ctk.CTkFont(size=13),
            text_color=("gray40", "gray60"),
        )
        prof_label.pack(anchor="w", pady=(2, 0))

        # Metadata chips row
        meta_frame = ctk.CTkFrame(content, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(10, 0))

        chip_bg = ("gray90", "gray25")
        chip_text = ("gray30", "gray70")
        for label, value in [
            (survey.semester, survey.semester),
            (survey.academic_year, survey.academic_year),
            (survey.department, survey.department),
        ]:
            if value:
                chip = ctk.CTkFrame(meta_frame, fg_color=chip_bg, corner_radius=6)
                chip.pack(side="left", padx=(0, 8))
                chip_label = ctk.CTkLabel(
                    chip,
                    text=value,
                    font=ctk.CTkFont(size=11),
                    text_color=chip_text,
                )
                chip_label.pack(padx=8, pady=3)

        # --- Right actions panel ---
        actions = ctk.CTkFrame(card, fg_color="transparent", width=130)
        actions.pack(side="right", padx=(0, 14), pady=14, fill="y")
        actions.pack_propagate(False)

        # Status badge
        status_badge = ctk.CTkFrame(actions, fg_color=status_fg, corner_radius=6)
        status_badge.pack(fill="x", pady=(0, 10))
        status_lbl = ctk.CTkLabel(
            status_badge,
            text=survey.status,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="white",
        )
        status_lbl.pack(pady=4)

        # Draft actions: folder + process + edit + delete
        if survey.status == "Draft":
            folder_entry = ctk.CTkEntry(
                actions,
                placeholder_text=_("select_folder"),
                height=26,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
            )
            folder_entry.pack(fill="x", pady=(0, 6))

            browse_row = ctk.CTkFrame(actions, fg_color="transparent")
            browse_row.pack(fill="x", pady=(0, 10))
            browse_btn = ctk.CTkButton(
                browse_row,
                text=_("browse"),
                height=24,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda e=folder_entry: self._browse_folder(e),
            )
            browse_btn.pack(side="right")

            proc_btn = ctk.CTkButton(
                actions,
                text=_("process"),
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda sid=survey.id, e=folder_entry: self._on_process(sid, e.get()),
            )
            proc_btn.pack(fill="x", pady=(0, 6))

            edit_btn = ctk.CTkButton(
                actions,
                text=_("edit_survey"),
                height=26,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=("gray85", "gray25"),
                hover_color=("gray75", "gray35"),
                text_color=("gray20", "gray90"),
                command=lambda sid=survey.id: self._on_edit(sid),
            )
            edit_btn.pack(fill="x", pady=(0, 6))

            del_btn = ctk.CTkButton(
                actions,
                text=_("delete"),
                height=26,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=("#E94560", "#C7364D"),
                hover_color=("#FF6B81", "#E94560"),
                command=lambda sid=survey.id: self._on_delete(sid),
            )
            del_btn.pack(fill="x")

        # Processed / Analyzed actions: results + delete
        elif survey.status in ("Processed", "Analyzed"):
            res_btn = ctk.CTkButton(
                actions,
                text=_("results"),
                height=28,
                corner_radius=6,
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda sid=survey.id: self._on_results(sid),
            )
            res_btn.pack(fill="x", pady=(0, 6))

            del_btn = ctk.CTkButton(
                actions,
                text=_("delete"),
                height=26,
                corner_radius=6,
                font=ctk.CTkFont(size=11),
                fg_color=("#E94560", "#C7364D"),
                hover_color=("#FF6B81", "#E94560"),
                command=lambda sid=survey.id: self._on_delete(sid),
            )
            del_btn.pack(fill="x")

        # Click to select
        card.configure(cursor="hand2")
        card.bind("<Button-1>", lambda e, sid=survey.id: self._select_survey(sid))

        return card

    def _select_survey(self, survey_id: int) -> None:
        """Select a survey by ID."""
        self.selected_survey_id = survey_id

        # Update card selection visuals
        for card in self.survey_cards:
            card.configure(border_color=("gray85", "gray25"))

        # Highlight selected card
        for i, survey in enumerate(self.current_surveys):
            if survey.id == survey_id and i < len(self.survey_cards):
                self.survey_cards[i].configure(border_color=("#4A90E2", "#357ABD"))
                break

        self._update_buttons()

    def _on_search(self, event: Any = None) -> None:
        """Handle search entry changes."""
        self._load_surveys()

    def _on_filter_dept(self, value: str) -> None:
        """Handle department filter changes."""
        self._load_surveys()

    def _update_buttons(self) -> None:
        """No bottom action bar; buttons live on each card."""
        pass

    def _on_edit(self, survey_id: int | None = None) -> None:
        """Navigate to edit survey page."""
        sid = survey_id or self.selected_survey_id
        if sid is None:
            return
        if self.navigate_callback:
            self.navigate_callback("survey_form", survey_id=sid)
        else:
            self.router.navigate("survey_form", survey_id=sid)

    def _on_process(self, survey_id: int | None = None, folder_path: str = "") -> None:
        """Navigate to process page with optional folder path."""
        sid = survey_id or self.selected_survey_id
        if sid is None:
            return
        if not folder_path or not Path(folder_path).exists():
            messagebox.showwarning(_("select_folder"), _("no_folder"))
            return
        if self.navigate_callback:
            self.navigate_callback("process", survey_id=sid, folder_path=folder_path)
        else:
            self.router.navigate("process", survey_id=sid, folder_path=folder_path)

    def _on_results(self, survey_id: int | None = None) -> None:
        """Navigate to results page."""
        sid = survey_id or self.selected_survey_id
        if sid is None:
            return
        if self.navigate_callback:
            self.navigate_callback("results", survey_id=sid)
        else:
            self.router.navigate("results", survey_id=sid)

    def _on_delete(self, survey_id: int | None = None) -> None:
        """Delete a survey with confirmation."""
        sid = survey_id or self.selected_survey_id
        if sid is None:
            return
        if messagebox.askyesno("Confirm", _("confirm_delete")):
            self.persistence.delete_survey(sid)
            if self.selected_survey_id == sid:
                self.selected_survey_id = None
            self._load_surveys()
            self._update_buttons()


class SurveyFormPage(BasePage):
    """Create or edit survey metadata."""

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
        self._create_widgets()
        if survey_id:
            self._load_survey()

    def _create_widgets(self) -> None:
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(16, 8), padx=20, fill="x")

        title = ctk.CTkLabel(
            header_frame,
            text=_("edit_survey") if self.survey_id else _("new_survey"),
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left")

        back_btn = ctk.CTkButton(
            header_frame,
            text=_("back"),
            command=lambda: self.navigate_callback("dashboard") if self.navigate_callback else self.router.navigate("dashboard"),
            width=100,
            height=36,
            corner_radius=8,
        )
        back_btn.pack(side="right")

        # Form frame with scrollable content
        form_container = ctk.CTkScrollableFrame(self, corner_radius=12)
        form_container.pack(padx=20, pady=(0, 16), fill="both", expand=True)

        # Form card
        form_frame = ctk.CTkFrame(form_container, corner_radius=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # University (read-only from settings)
        university_name = self.persistence.get_setting("university_name", "")
        self._create_field(form_frame, _("university"), university_name, row=0, readonly=True)

        # Editable fields
        self.faculty_entry = self._create_field(form_frame, _("faculty"), "", row=1)
        self.dept_entry = self._create_field(form_frame, _("department"), "", row=2)
        self.subject_entry = self._create_field(form_frame, _("subject"), "", row=3)
        self.professor_entry = self._create_field(form_frame, _("professor_name"), "", row=4)
        self.semester_entry = self._create_field(form_frame, _("semester"), "", row=5)
        self.year_entry = self._create_field(form_frame, _("academic_year"), "", row=6)

        # Action buttons
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(padx=20, pady=(0, 16), fill="x")

        save_btn = ctk.CTkButton(
            button_frame,
            text=_("save_survey"),
            command=self._on_save,
            width=140,
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        save_btn.pack(side="left", padx=5)

        self.print_btn = ctk.CTkButton(
            button_frame,
            text=_("print_form"),
            command=self._on_print,
            state="disabled" if not self.survey_id else "normal",
            width=140,
            height=40,
            corner_radius=8,
        )
        self.print_btn.pack(side="left", padx=5)

    def _create_field(
        self,
        parent: ctk.CTkFrame,
        label: str,
        default: str,
        row: int,
        readonly: bool = False,
    ) -> ctk.CTkEntry:
        """Create a labeled input field."""
        lbl = ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        lbl.grid(row=row, column=0, padx=16, pady=12, sticky="w")

        entry = ctk.CTkEntry(
            parent,
            width=350,
            height=38,
            corner_radius=8,
        )
        if default:
            entry.insert(0, default)
        if readonly:
            entry.configure(state="disabled")
        entry.grid(row=row, column=1, padx=16, pady=12, sticky="w")
        return entry

    def _load_survey(self) -> None:
        """Load existing survey data."""
        if self.survey_id:
            survey = self.persistence.get_survey(self.survey_id)
            if survey:
                self.faculty_entry.insert(0, survey.faculty)
                self.dept_entry.insert(0, survey.department)
                self.subject_entry.insert(0, survey.subject)
                self.professor_entry.insert(0, survey.professor)
                self.semester_entry.insert(0, survey.semester)
                self.year_entry.insert(0, survey.academic_year)

    def _on_save(self) -> None:
        """Save survey to database."""
        university_name = self.persistence.get_setting("university_name", "")
        survey = Survey(
            university=university_name,
            faculty=self.faculty_entry.get(),
            department=self.dept_entry.get(),
            subject=self.subject_entry.get(),
            professor=self.professor_entry.get(),
            semester=self.semester_entry.get(),
            academic_year=self.year_entry.get(),
            status="Draft",
        )

        if self.survey_id:
            survey.id = self.survey_id
            survey.updated_at = datetime.now().isoformat()
            self.persistence.update_survey(survey)
        else:
            saved = self.persistence.create_survey(survey)
            self.survey_id = saved.id
            # Enable print button now that the survey has a DB id
            if hasattr(self, "print_btn"):
                self.print_btn.configure(state="normal")

        if self.navigate_callback:
            self.navigate_callback("dashboard")
        else:
            self.router.navigate("dashboard")

    def _on_print(self) -> None:
        """Generate a prefilled PDF and open it with the system viewer."""
        if not self.survey_id:
            messagebox.showwarning(_("print_form"), "Please save the survey first.")
            return

        survey = self.persistence.get_survey(self.survey_id)
        if not survey:
            messagebox.showerror(_("print_form"), "Survey not found.")
            return

        try:
            import tempfile

            tmp_dir = Path(tempfile.mkdtemp())
            safe_name = (
                f"survey_{survey.id}_{survey.subject or 'form'}"
                .replace(" ", "_")
                .replace("/", "-")[:60]
            )
            output_path = tmp_dir / f"{safe_name}.pdf"

            generate_prefilled_form(
                survey,
                output_path,
                persistence=self.persistence,
            )
            open_pdf(output_path)
        except RuntimeError as exc:
            messagebox.showerror(_("print_form"), str(exc))
        except Exception as exc:
            logger.exception("PDF generation failed")
            messagebox.showerror(_("print_form"), f"Failed to generate PDF:\n{exc}")


class ProcessPage(BasePage):
    """Per-survey image upload and OMR processing."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        survey_id: int,
        folder_path: str = "",
        vision: VisionProcessor | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.survey_id = survey_id
        self.folder_path = folder_path
        self.vision = vision or VisionProcessor()

        self.image_files: list[Path] = []
        self.thumbnail_cards: dict[Path, ctk.CTkFrame] = {}
        self.is_scanning: bool = False

        self._create_widgets()

        # Auto-load images if a valid folder was provided
        if self.folder_path and Path(self.folder_path).exists():
            self._load_images_from_folder(Path(self.folder_path))

    def _create_widgets(self) -> None:
        """Build the ProcessPage layout."""
        # --- Header ---------------------------------------------------- #
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(16, 8), padx=20, fill="x")

        back_btn = ctk.CTkButton(
            header_frame,
            text=_("back"),
            command=lambda: (
                self.navigate_callback("dashboard")
                if self.navigate_callback
                else self.router.navigate("dashboard")
            ),
            width=100,
            height=36,
            corner_radius=8,
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            header_frame,
            text=_("process"),
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left", padx=16)

        # --- Survey metadata card -------------------------------------- #
        survey = None
        try:
            survey = self.persistence.get_survey(self.survey_id)
        except Exception:
            logger.warning("Could not load survey id=%s", self.survey_id)

        if survey:
            meta_frame = ctk.CTkFrame(self, corner_radius=12)
            meta_frame.pack(padx=20, pady=(0, 10), fill="x")
            meta_text = (
                f"{survey.subject} - {survey.professor} "
                f"({survey.semester}, {survey.academic_year})"
            )
            meta_label = ctk.CTkLabel(
                meta_frame,
                text=meta_text,
                font=ctk.CTkFont(size=15),
            )
            meta_label.pack(padx=16, pady=12)

        # --- Add Images row ------------------------------------------- #
        add_row = ctk.CTkFrame(self, fg_color="transparent")
        add_row.pack(padx=20, pady=(0, 8), fill="x")

        add_btn = ctk.CTkButton(
            add_row,
            text=_("add_images"),
            command=self._on_add_images,
            width=120,
            height=34,
            corner_radius=8,
        )
        add_btn.pack(side="left")

        folder_display = self.folder_path if self.folder_path else _("no_folder")
        self.folder_path_label = ctk.CTkLabel(
            add_row,
            text=folder_display,
            font=ctk.CTkFont(size=12),
            text_color=("gray40", "gray60"),
        )
        self.folder_path_label.pack(side="left", padx=12)

        # --- Thumbnail grid ------------------------------------------- #
        self.thumb_frame = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            height=200,
        )
        self.thumb_frame.pack(padx=20, pady=(0, 10), fill="x")

        # --- Progress -------------------------------------------------- #
        self.progress_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=13),
        )
        self.progress_label.pack(padx=20, pady=(0, 4), anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self, height=14, corner_radius=6)
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=20, pady=(0, 10), fill="x")

        # --- Start Scanning button ------------------------------------ #
        self.scan_btn = ctk.CTkButton(
            self,
            text=_("start_scanning"),
            command=self._on_start_scanning,
            state="disabled",
            height=40,
            corner_radius=8,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.scan_btn.pack(padx=20, pady=(0, 16), anchor="w")

    # ------------------------------------------------------------------ #
    #  Image management
    # ------------------------------------------------------------------ #

    def _on_add_images(self) -> None:
        """Open file dialog and add selected images."""
        files = filedialog.askopenfilenames(
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        for f in files:
            p = Path(f)
            if p not in self.image_files:
                self.image_files.append(p)
        self._refresh_thumbnails()
        if self.image_files:
            self.scan_btn.configure(state="normal")

    def _load_images_from_folder(self, folder: Path) -> None:
        """Scan a folder for supported image files and load them."""
        exts = {".jpg", ".jpeg", ".png"}
        found = sorted(
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in exts
        )
        self.image_files = found
        self._refresh_thumbnails()
        if self.image_files:
            self.scan_btn.configure(state="normal")

    def _refresh_thumbnails(self) -> None:
        """Rebuild the thumbnail grid from ``self.image_files``."""
        # Clear existing cards
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
        self.thumbnail_cards.clear()

        for path in self.image_files:
            card = ctk.CTkFrame(
                self.thumb_frame,
                width=100,
                height=80,
                corner_radius=8,
                border_width=1,
                border_color=("gray80", "gray30"),
            )
            card.pack(side="left", padx=4, pady=4)
            card.pack_propagate(False)

            # Filename label (truncated)
            name = path.name
            display_name = name if len(name) <= 12 else name[:12] + "..."
            name_lbl = ctk.CTkLabel(
                card,
                text=display_name,
                font=ctk.CTkFont(size=9),
                wraplength=90,
            )
            name_lbl.pack(pady=(6, 2))

            # Status badge
            status_lbl = ctk.CTkLabel(
                card,
                text=_("queued"),
                font=ctk.CTkFont(size=9),
                text_color="gray",
            )
            status_lbl.pack(pady=(0, 4))

            # Store reference to the status label inside the card
            card._status_label = status_lbl  # type: ignore[attr-defined]
            self.thumbnail_cards[path] = card

    def _update_thumbnail_status(self, path: Path, status: str) -> None:
        """Update the status badge on a thumbnail card."""
        card = self.thumbnail_cards.get(path)
        if card is None:
            return

        color_map = {
            "Queued": "gray",
            "Processing": "#3B82F6",
            "Success": "#10B981",
            "Warning": "#F59E0B",
            "Error": "#E94560",
        }
        color = color_map.get(status, "gray")

        # Map status to i18n key
        key_map = {
            "Queued": "queued",
            "Processing": "processing",
            "Success": "success",
            "Warning": "warning",
            "Error": "error",
        }
        label_text = _(key_map.get(status, status.lower()))

        lbl = getattr(card, "_status_label", None)
        if lbl:
            lbl.configure(text=label_text, text_color=color)

    # ------------------------------------------------------------------ #
    #  Scanning
    # ------------------------------------------------------------------ #

    def _on_start_scanning(self) -> None:
        """Start the scanning process in a background thread."""
        if self.is_scanning or not self.image_files:
            if not self.image_files:
                messagebox.showwarning(
                    _("start_scanning"), _("no_images_queued")
                )
            return
        self.is_scanning = True
        self.scan_btn.configure(state="disabled")
        t = threading.Thread(target=self._scan_worker, daemon=True)
        t.start()

    def _scan_worker(self) -> None:
        """Background worker: process each image and save results."""
        n = len(self.image_files)
        counts = {"success": 0, "warning": 0, "error": 0}

        for i, image_path in enumerate(self.image_files):
            # Update thumbnail to "Processing"
            self.after(
                0,
                lambda p=image_path: self._update_thumbnail_status(p, "Processing"),
            )
            # Update progress label
            label_text = _("scanning_image", current=i + 1, total=n)
            self.after(0, lambda t=label_text: self.progress_label.configure(text=t))
            # Update progress bar
            progress_val = (i + 1) / n
            self.after(0, lambda v=progress_val: self.progress_bar.set(v))

            try:
                result = self.vision.process_form(image_path)
            except Exception as exc:
                logger.exception("Error processing %s", image_path)
                result = {
                    "status": "error",
                    "form_confidence": 0.0,
                    "Form_ID": image_path.stem,
                    "Form_Score": 0.0,
                    "Valid": False,
                }
                for qi in range(1, 15):
                    result[f"Q{qi}"] = "Invalid"

            # Determine status
            if result.get("status") != "ok":
                status = "Error"
                counts["error"] += 1
            elif result.get("form_confidence", 0.0) < 0.5:
                status = "Warning"
                counts["warning"] += 1
            else:
                status = "Success"
                counts["success"] += 1

            # Save to DB
            try:
                form_result = self._result_to_form_result(result, image_path)
                self.persistence.create_form_result(form_result)
            except Exception:
                logger.exception("Failed to save form result for %s", image_path)

            # Update thumbnail
            self.after(
                0,
                lambda p=image_path, s=status: self._update_thumbnail_status(p, s),
            )

        # All done — update survey status to "Processed"
        try:
            survey = self.persistence.get_survey(self.survey_id)
            if survey:
                survey.status = "Processed"
                survey.updated_at = datetime.now().isoformat()
                self.persistence.update_survey(survey)
        except Exception:
            logger.exception("Failed to update survey status")

        # Final UI updates
        self.after(
            0,
            lambda: self.progress_label.configure(text=_("scan_complete")),
        )
        self.after(0, lambda: setattr(self, "is_scanning", False))
        self.after(0, lambda: self.scan_btn.configure(state="normal"))

        # Summary messagebox
        summary = (
            f"{_('scan_summary')}\n"
            f"{_('forms_success')}: {counts['success']}\n"
            f"{_('forms_warning')}: {counts['warning']}\n"
            f"{_('forms_error')}: {counts['error']}"
        )
        self.after(0, lambda: messagebox.showinfo(_("scan_complete"), summary))

    def _result_to_form_result(
        self, result: dict[str, Any], image_path: Path
    ) -> FormResult:
        """Convert a ``process_form`` result dict to a ``FormResult`` dataclass.

        Args:
            result: Dictionary returned by ``VisionProcessor.process_form``.
            image_path: Path to the source image.

        Returns:
            Populated ``FormResult`` instance (without ``id``).
        """
        return FormResult(
            survey_id=self.survey_id,
            form_id=result.get("Form_ID", image_path.stem),
            image_path=str(image_path),
            q1=result.get("Q1", ""),
            q2=result.get("Q2", ""),
            q3=result.get("Q3", ""),
            q4=result.get("Q4", ""),
            q5=result.get("Q5", ""),
            q6=result.get("Q6", ""),
            q7=result.get("Q7", ""),
            q8=result.get("Q8", ""),
            q9=result.get("Q9", ""),
            q10=result.get("Q10", ""),
            q11=result.get("Q11", ""),
            q12=result.get("Q12", ""),
            q13=result.get("Q13", ""),
            q14=result.get("Q14", ""),
            form_score=result.get("Form_Score", 0.0),
            valid=result.get("Valid", False),
            confidence=result.get("form_confidence", 0.0),
            manually_corrected=False,
        )


class ResultsPage(BasePage):
    """Results visualization and export — full Phase 5 implementation."""

    def __init__(
        self,
        router: PageRouter,
        persistence: PersistenceManager,
        survey_id: int,
        analytics: AnalyticsEngine | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the ResultsPage.

        Args:
            router: Application page router.
            persistence: Database persistence manager.
            survey_id: ID of the survey to display.
            analytics: Optional AnalyticsEngine instance; created if ``None``.
            **kwargs: Forwarded to ``BasePage``.
        """
        super().__init__(router, **kwargs)
        self.persistence = persistence
        self.survey_id = survey_id
        self.analytics = analytics or AnalyticsEngine()

        # Load data
        self.survey = self.persistence.get_survey(self.survey_id)
        self.form_results = self.persistence.get_form_results(self.survey_id)
        self.question_texts = self.persistence.get_setting("question_texts", None)

        # Auto-update status to "Analyzed" if it was "Processed"
        if self.survey and self.survey.status == "Processed":
            self.survey.status = "Analyzed"
            self.survey.updated_at = datetime.now().isoformat()
            self.persistence.update_survey(self.survey)
            logger.info(_("analyzed_status_set"))

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Build the full ResultsPage layout."""
        # --- Header ---------------------------------------------------- #
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(16, 8), padx=20, fill="x")

        back_btn = ctk.CTkButton(
            header_frame,
            text=_("back"),
            command=lambda: (
                self.navigate_callback("dashboard")
                if self.navigate_callback
                else self.router.navigate("dashboard")
            ),
            width=100,
            height=36,
            corner_radius=8,
        )
        back_btn.pack(side="left")

        title = ctk.CTkLabel(
            header_frame,
            text=_("results"),
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(side="left", padx=16)

        # --- Survey metadata card -------------------------------------- #
        if self.survey:
            meta_frame = ctk.CTkFrame(self, corner_radius=12)
            meta_frame.pack(padx=20, pady=(0, 10), fill="x")

            form_count = len(self.form_results)
            batch_score = (
                sum(fr.form_score for fr in self.form_results) / form_count
                if form_count > 0
                else 0.0
            )

            meta_top = ctk.CTkFrame(meta_frame, fg_color="transparent")
            meta_top.pack(fill="x", padx=16, pady=(12, 4))

            ctk.CTkLabel(
                meta_top,
                text=f"{self.survey.subject}  |  {self.survey.professor}  |  {self.survey.semester}",
                font=ctk.CTkFont(size=15, weight="bold"),
            ).pack(side="left")

            meta_bottom = ctk.CTkFrame(meta_frame, fg_color="transparent")
            meta_bottom.pack(fill="x", padx=16, pady=(0, 12))

            ctk.CTkLabel(
                meta_bottom,
                text=_("forms_count", count=form_count),
                font=ctk.CTkFont(size=13),
                text_color=("gray40", "gray60"),
            ).pack(side="left")

            ctk.CTkLabel(
                meta_bottom,
                text="   " + _("batch_score_label", score=batch_score),
                font=ctk.CTkFont(size=13),
                text_color=("gray40", "gray60"),
            ).pack(side="left")

        # --- Segmented tab button ------------------------------------- #
        self.tab_var = tk.StringVar(value=_("summary_view"))
        self.seg_btn = ctk.CTkSegmentedButton(
            self,
            values=[_("summary_view"), _("raw_data_view"), _("trend_analysis")],
            command=self._on_tab_change,
            variable=self.tab_var,
        )
        self.seg_btn.pack(padx=20, pady=(0, 8), fill="x")

        # --- Content area --------------------------------------------- #
        self.content_frame = ctk.CTkScrollableFrame(self, corner_radius=12)
        self.content_frame.pack(padx=20, pady=(0, 8), fill="both", expand=True)

        # --- Export buttons row --------------------------------------- #
        export_frame = ctk.CTkFrame(self, fg_color="transparent")
        export_frame.pack(padx=20, pady=(0, 16), fill="x")

        ctk.CTkButton(
            export_frame,
            text=_("export_csv"),
            command=self._on_export_csv,
            width=160,
            height=36,
            corner_radius=8,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            export_frame,
            text=_("export_pdf_report"),
            command=self._on_export_pdf,
            width=180,
            height=36,
            corner_radius=8,
        ).pack(side="left")

        # Show summary tab by default
        self._show_summary()

    # ------------------------------------------------------------------ #
    #  Tab helpers
    # ------------------------------------------------------------------ #

    def _clear_content(self) -> None:
        """Remove all widgets from the content frame."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _show_summary(self) -> None:
        """Build the summary table in the content frame."""
        self._clear_content()

        if not self.form_results:
            ctk.CTkLabel(
                self.content_frame,
                text=_("no_results"),
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        columns = (
            _("question_num_short"),
            _("question_text") if False else "Question",  # use plain "Question" as column id
            _("count_yes"),
            _("count_no"),
            _("count_somewhat"),
            _("count_invalid"),
            _("total_responses"),
            _("pct_distribution"),
        )
        col_ids = ("q_num", "q_text", "yes", "no", "somewhat", "invalid", "total", "pct")

        tree = ttk.Treeview(
            self.content_frame,
            columns=col_ids,
            show="headings",
            height=14,
        )
        for cid, cname in zip(col_ids, columns):
            tree.heading(cid, text=cname)
            tree.column(cid, width=80, anchor="center")
        tree.column("q_text", width=200, anchor="w")

        for i in range(14):
            q_num = i + 1
            q_text = (
                self.question_texts[i]
                if self.question_texts and len(self.question_texts) == 14
                else f"Q{q_num}"
            )
            count_yes = sum(1 for fr in self.form_results if fr.answers()[i] == "Yes")
            count_no = sum(1 for fr in self.form_results if fr.answers()[i] == "No")
            count_somewhat = sum(1 for fr in self.form_results if fr.answers()[i] == "Somewhat")
            count_invalid = sum(1 for fr in self.form_results if fr.answers()[i] == "Invalid")
            total = count_yes + count_no + count_somewhat + count_invalid
            pct = f"{(count_yes / total * 100):.1f}" if total > 0 else "0.0"
            tree.insert(
                "",
                "end",
                values=(q_num, q_text, count_yes, count_no, count_somewhat, count_invalid, total, pct),
            )

        tree.pack(fill="both", expand=True)

        # Scrollbar
        vsb = ttk.Scrollbar(self.content_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        # View HTML Report button
        ctk.CTkButton(
            self.content_frame,
            text=_("view_html_report"),
            command=self._on_view_html_report,
            width=180,
            height=36,
            corner_radius=8,
        ).pack(pady=(12, 4))

    def _show_raw_data(self) -> None:
        """Build the raw data table in the content frame."""
        self._clear_content()

        if not self.form_results:
            ctk.CTkLabel(
                self.content_frame,
                text=_("no_results"),
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        q_cols = tuple(f"Q{i}" for i in range(1, 15))
        col_ids = ("form_id",) + q_cols + ("score", "valid")
        col_names = ("Form ID",) + q_cols + ("Score", "Valid")

        tree = ttk.Treeview(
            self.content_frame,
            columns=col_ids,
            show="headings",
            height=min(len(self.form_results), 15),
        )
        for cid, cname in zip(col_ids, col_names):
            tree.heading(cid, text=cname)
            tree.column(cid, width=55, anchor="center")
        tree.column("form_id", width=120, anchor="w")

        for fr in self.form_results:
            row = (fr.form_id,) + tuple(fr.answers()) + (f"{fr.form_score:.1f}", str(fr.valid))
            tree.insert("", "end", values=row)

        tree.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(self.content_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

        hsb = ttk.Scrollbar(self.content_frame, orient="horizontal", command=tree.xview)
        tree.configure(xscrollcommand=hsb.set)
        hsb.pack(side="bottom", fill="x")

    def _show_trend(self) -> None:
        """Build the trend table in the content frame."""
        self._clear_content()

        if not self.survey:
            ctk.CTkLabel(
                self.content_frame,
                text=_("no_trend_data"),
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        trend_data = self.analytics.get_trend_data(self.survey, self.persistence)

        if len(trend_data) <= 1:
            ctk.CTkLabel(
                self.content_frame,
                text=_("no_trend_data"),
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).pack(pady=40)
            return

        col_ids = ("semester", "academic_year", "form_count", "batch_score")
        col_names = (_("semester"), _("academic_year"), "Forms", "Score")

        tree = ttk.Treeview(
            self.content_frame,
            columns=col_ids,
            show="headings",
            height=min(len(trend_data), 10),
        )
        for cid, cname in zip(col_ids, col_names):
            tree.heading(cid, text=cname)
            tree.column(cid, width=140, anchor="center")

        for entry in trend_data:
            tree.insert(
                "",
                "end",
                values=(
                    entry["semester"],
                    entry["academic_year"],
                    entry["form_count"],
                    f"{entry['batch_score']:.1f}%",
                ),
            )

        tree.pack(fill="both", expand=True)

    def _on_tab_change(self, value: str) -> None:
        """Switch content based on selected tab value."""
        if value == _("summary_view"):
            self._show_summary()
        elif value == _("raw_data_view"):
            self._show_raw_data()
        elif value == _("trend_analysis"):
            self._show_trend()

    # ------------------------------------------------------------------ #
    #  Export handlers
    # ------------------------------------------------------------------ #

    def _on_export_csv(self) -> None:
        """Open save dialog and export CSV."""
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

    def _on_export_pdf(self) -> None:
        """Open save dialog and export PDF report."""
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

    def _on_view_html_report(self) -> None:
        """Generate HTML report and open in default browser."""
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

            if rows:
                df = pd.DataFrame(rows)
            else:
                df = pd.DataFrame(
                    columns=["Form_ID"] + [f"Q{i}" for i in range(1, 15)] + ["Form_Score", "Valid"]
                )

            report_path = self.analytics.generate_report(
                df,
                question_texts=self.question_texts,
            )
            webbrowser.open(f"file:///{Path(report_path).resolve()}")
        except Exception as exc:
            logger.exception("HTML report generation failed")
            messagebox.showerror(_("error_report"), f"{_('error_report')}:\n{exc}")


class OMRGUI:
    """Main application window using CustomTkinter."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize the GUI.

        Args:
            config: Application configuration. Uses global defaults when
                ``None``.
        """
        self.config = config or Config()
        self.input_folder: Path | None = None
        self.image_files: list[Path] = []

        # Apply persisted preferences
        ctk.set_appearance_mode(self.config.APPEARANCE_MODE)
        I18n.set_language(self.config.LANGUAGE)

        # Core components
        self.persistence = PersistenceManager()
        self.vision = VisionProcessor(config=self.config)
        self.analytics = AnalyticsEngine(config=self.config)

        # --- Main window ------------------------------------------------ #
        self.root = ctk.CTk()
        self.root.title(_("app_title"))
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)

        self._create_widgets()

        # Re-translate when language changes
        I18n.register_listener(self._refresh_texts)

    # ------------------------------------------------------------------ #
    #  Widget creation
    # ------------------------------------------------------------------ #

    def _create_widgets(self) -> None:
        """Build all UI elements."""
        # Main container with sidebar and content
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = ctk.CTkFrame(
            main_container,
            width=250,
            corner_radius=0,
            fg_color=("gray95", "gray10"),
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App logo/title in sidebar
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(30, 20), padx=20, fill="x")

        app_title = ctk.CTkLabel(
            logo_frame,
            text="OMR Scanner",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        app_title.pack()

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊", _("dashboard")),
            ("survey_form", "➕", _("new_survey")),
            ("process", "📷", _("process")),
            ("results", "📈", _("results")),
            ("settings", "⚙️", _("settings")),
        ]

        for page_id, icon, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{icon}  {label}",
                font=ctk.CTkFont(size=14),
                height=45,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray20", "gray90"),
                hover_color=("gray85", "gray20"),
                anchor="w",
                command=lambda pid=page_id: self._navigate_to(pid),
            )
            btn.pack(padx=15, pady=(0, 8), fill="x")
            self.nav_buttons[page_id] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(expand=True)

        # User info / footer in sidebar
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(pady=(0, 20), padx=20, fill="x")

        footer_label = ctk.CTkLabel(
            footer_frame,
            text="v1.0",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        footer_label.pack()

        # Content area for page routing
        self.content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Setup page router
        self.router = PageRouter(self.root, self.content_frame)
        self.router.register_page(
            "dashboard",
            lambda **kwargs: DashboardPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate_to,
                **kwargs,
            ),
        )
        self.router.register_page(
            "survey_form",
            lambda **kwargs: SurveyFormPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate_to,
                **kwargs,
            ),
        )
        self.router.register_page(
            "process",
            lambda **kwargs: ProcessPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate_to,
                vision=self.vision,
                **kwargs,
            ),
        )
        self.router.register_page(
            "results",
            lambda **kwargs: ResultsPage(
                router=self.router,
                persistence=self.persistence,
                navigate_callback=self._navigate_to,
                analytics=self.analytics,
                **kwargs,
            ),
        )
        self.router.register_page(
            "settings",
            lambda master=None, **kwargs: SettingsFrame(
                master or self.content_frame,
                self.config,
                back_command=self.close_settings,
                persistence=self.persistence,
            ),
        )

        # Navigate to dashboard by default
        self._navigate_to("dashboard")

    # ------------------------------------------------------------------ #
    #  Navigation
    # ------------------------------------------------------------------ #

    def _navigate_to(self, page_id: str, **kwargs: Any) -> None:
        """Navigate to a page and update sidebar highlighting."""
        # Update sidebar button states
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=("#4A90E2", "#357ABD"),
                    text_color="white",
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray20", "gray90"),
                )

        # Navigate to the page
        if page_id == "survey_form":
            self.router.navigate("survey_form", **kwargs)
        elif page_id == "process":
            # Check if there's a selected survey
            if "survey_id" in kwargs:
                self.router.navigate("process", **kwargs)
            else:
                # Navigate to dashboard if no survey selected
                self._navigate_to("dashboard")
        elif page_id == "results":
            if "survey_id" in kwargs:
                self.router.navigate("results", **kwargs)
            else:
                self._navigate_to("dashboard")
        else:
            self.router.navigate(page_id, **kwargs)

    def open_settings(self) -> None:
        """Navigate to settings page."""
        self._navigate_to("settings")

    def close_settings(self) -> None:
        """Return to dashboard."""
        self._navigate_to("dashboard")

    def _refresh_texts(self) -> None:
        """Re-apply translations to all static widgets."""
        self.root.title(_("app_title"))
        # Refresh navigation buttons
        nav_items = [
            ("dashboard", "📊", _("dashboard")),
            ("survey_form", "➕", _("new_survey")),
            ("process", "📷", _("process")),
            ("results", "📈", _("results")),
            ("settings", "⚙️", _("settings")),
        ]
        for page_id, icon, label in nav_items:
            if page_id in self.nav_buttons:
                self.nav_buttons[page_id].configure(text=f"{icon}  {label}")
        # Refresh current page
        if self.router.current_page:
            self._navigate_to("dashboard")


    # ------------------------------------------------------------------ #
    #  Run
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Start the GUI main loop."""
        self.root.mainloop()
