"""Modern settings window for the OMR QA Form Scanner."""

from __future__ import annotations

import json
import logging
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from config import Config
from i18n import I18n, _

logger = logging.getLogger("omr_qa_scanner")


class SettingsFrame(ctk.CTkFrame):
    """A modern, card-based settings frame for embedding in the main window."""

    def __init__(
        self,
        master: Any,
        config: Config,
        back_command: Any = None,
        persistence: Any = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._back_command = back_command
        self._persistence = persistence
        self._logo_path: str = ""

        # Colours for the modern look (light, dark)
        self.card_colour = ("#F9F9F9", "#2B2B2B")

        self._build_ui()
        self._load_values()

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(padx=20, pady=20, fill="both", expand=True)

        # --- General card ------------------------------------------------- #
        general_card = self._card(container, _("general"))
        general_card.pack(pady=(0, 16), fill="x")

        # Language
        lang_row = ctk.CTkFrame(general_card, fg_color="transparent")
        lang_row.pack(padx=16, pady=(12, 6), fill="x")
        ctk.CTkLabel(
            lang_row,
            text=_("language"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w")

        self._lang_code_map = I18n.languages()
        self._label_to_code = {label: code for code, label in self._lang_code_map.items()}
        current_label = self._lang_code_map.get(I18n.get_language(), "English")
        self.lang_var = ctk.StringVar(value=current_label)
        self.lang_seg = ctk.CTkSegmentedButton(
            lang_row,
            values=list(self._lang_code_map.values()),
            variable=self.lang_var,
            command=self._on_lang_preview,
            font=ctk.CTkFont(size=12),
        )
        self.lang_seg.pack(pady=(8, 4), fill="x")
        self.lang_seg.set(current_label)

        # Appearance
        appear_row = ctk.CTkFrame(general_card, fg_color="transparent")
        appear_row.pack(padx=16, pady=(6, 12), fill="x")
        ctk.CTkLabel(
            appear_row,
            text=_("appearance"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w")

        self.appear_var = ctk.StringVar(value=ctk.get_appearance_mode())
        self.appear_seg = ctk.CTkSegmentedButton(
            appear_row,
            values=["Light", "Dark", "System"],
            variable=self.appear_var,
            font=ctk.CTkFont(size=12),
        )
        self.appear_seg.pack(pady=(8, 4), fill="x")

        # --- Form geometry card ------------------------------------------- #
        geo_card = self._card(container, _("form_geometry"))
        geo_card.pack(pady=(0, 16), fill="x")

        self._numeric_row(geo_card, _("form_width"), "form_width")
        self._numeric_row(geo_card, _("form_height"), "form_height")
        self._numeric_row(geo_card, _("rows"), "rows")
        self._numeric_row(geo_card, _("columns"), "columns")

        # --- Detection card ----------------------------------------------- #
        detect_card = self._card(container, _("threshold"))
        detect_card.pack(pady=(0, 16), fill="x")

        self._float_row(detect_card, _("threshold"), "threshold")

        # --- Scoring card ------------------------------------------------- #
        score_card = self._card(container, f"{_('score_yes')} / {_('score_somewhat')} / {_('score_no')}")
        score_card.pack(pady=(0, 16), fill="x")

        self._numeric_row(score_card, _("score_yes"), "score_yes")
        self._numeric_row(score_card, _("score_somewhat"), "score_somewhat")
        self._numeric_row(score_card, _("score_no"), "score_no")

        # --- University Branding card ------------------------------------- #
        branding_card = self._card(container, _("university_branding"))
        branding_card.pack(pady=(0, 16), fill="x")

        # University name row
        uni_row = ctk.CTkFrame(branding_card, fg_color="transparent")
        uni_row.pack(padx=16, pady=(8, 4), fill="x")
        ctk.CTkLabel(
            uni_row,
            text=_("university_name"),
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        uni_default = (
            self._persistence.get_setting("university_name", "")
            if self._persistence is not None
            else ""
        )
        self.uni_name_entry = ctk.CTkEntry(uni_row, width=300, font=ctk.CTkFont(size=12))
        if uni_default:
            self.uni_name_entry.insert(0, uni_default)
        self.uni_name_entry.pack(side="right")

        # Logo upload row
        logo_row = ctk.CTkFrame(branding_card, fg_color="transparent")
        logo_row.pack(padx=16, pady=(4, 4), fill="x")
        ctk.CTkLabel(
            logo_row,
            text=_("logo_upload"),
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        ctk.CTkButton(
            logo_row,
            text=_("select_logo"),
            command=self._select_logo,
            width=160,
            font=ctk.CTkFont(size=12),
        ).pack(side="right")

        # Logo preview row
        preview_row = ctk.CTkFrame(branding_card, fg_color="transparent")
        preview_row.pack(padx=16, pady=(4, 4), fill="x")
        ctk.CTkLabel(
            preview_row,
            text=_("logo_preview"),
            font=ctk.CTkFont(size=12),
        ).pack(side="left")
        self.logo_preview_label = ctk.CTkLabel(
            preview_row,
            text=_("no_logo"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self.logo_preview_label.pack(side="right")

        # Branding save button
        if self._persistence is not None:
            branding_save_row = ctk.CTkFrame(branding_card, fg_color="transparent")
            branding_save_row.pack(padx=16, pady=(4, 12), fill="x")
            ctk.CTkButton(
                branding_save_row,
                text=_("save"),
                command=self._save_branding,
                width=100,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right")

        # --- PDF Template Coordinates card -------------------------------- #
        coords_card = self._card(container, _("pdf_coords"))
        coords_card.pack(pady=(0, 16), fill="x")

        coords_default = ""
        if self._persistence is not None:
            stored_coords = self._persistence.get_setting("pdf_coords")
            if stored_coords is not None:
                try:
                    coords_default = json.dumps(stored_coords, ensure_ascii=False, indent=2)
                except Exception:
                    coords_default = "{}"

        self.pdf_coords_textbox = ctk.CTkTextbox(
            coords_card,
            height=120,
            font=ctk.CTkFont(size=11, family="Courier"),
        )
        self.pdf_coords_textbox.pack(padx=16, pady=(8, 4), fill="x")
        if coords_default:
            self.pdf_coords_textbox.insert("1.0", coords_default)
        else:
            self.pdf_coords_textbox.insert("1.0", "{}")

        if self._persistence is not None:
            coords_save_row = ctk.CTkFrame(coords_card, fg_color="transparent")
            coords_save_row.pack(padx=16, pady=(4, 12), fill="x")
            ctk.CTkButton(
                coords_save_row,
                text=_("save"),
                command=self._save_pdf_coords,
                width=100,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right")

        # --- Survey Questions card ---------------------------------------- #
        questions_card = self._card(container, _("survey_questions"))
        questions_card.pack(pady=(0, 16), fill="x")

        # Load default questions
        from pdf_generator import _DARI_QUESTIONS
        default_questions = list(_DARI_QUESTIONS)
        if self._persistence is not None:
            stored_q = self._persistence.get_setting("question_texts")
            if isinstance(stored_q, list) and len(stored_q) == 14:
                default_questions = stored_q

        # Scrollable frame for 14 question rows
        q_scroll = ctk.CTkScrollableFrame(questions_card, height=300)
        q_scroll.pack(padx=16, pady=(8, 4), fill="x")

        # Header row
        header_row = ctk.CTkFrame(q_scroll, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            header_row,
            text=_("question_num"),
            font=ctk.CTkFont(size=11, weight="bold"),
            width=30,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            header_row,
            text=_("question_text"),
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left")

        self._question_entries: list[ctk.CTkEntry] = []
        for i in range(14):
            row = ctk.CTkFrame(q_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(
                row,
                text=f"Q{i + 1}",
                font=ctk.CTkFont(size=11),
                width=30,
                anchor="w",
            ).pack(side="left", padx=(0, 8))
            entry = ctk.CTkEntry(row, width=400, font=ctk.CTkFont(size=11))
            entry.insert(0, default_questions[i] if i < len(default_questions) else "")
            entry.pack(side="left")
            self._question_entries.append(entry)

        if self._persistence is not None:
            q_save_row = ctk.CTkFrame(questions_card, fg_color="transparent")
            q_save_row.pack(padx=16, pady=(4, 12), fill="x")
            ctk.CTkButton(
                q_save_row,
                text=_("save_questions"),
                command=self._save_questions,
                width=140,
                font=ctk.CTkFont(size=12, weight="bold"),
            ).pack(side="right")

        # --- Footer buttons ----------------------------------------------- #
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(padx=20, pady=(0, 20), fill="x")

        self.save_btn = ctk.CTkButton(
            footer,
            text=_("save"),
            command=self._save,
            width=120,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.save_btn.pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            footer,
            text=_("close"),
            command=self._on_back,
            width=100,
            fg_color="transparent",
            hover_color=("#E5E5E5", "#404040"),
        ).pack(side="right")

    def _card(self, parent: Any, title: str) -> ctk.CTkFrame:
        """Create a rounded card frame with a title."""
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=self.card_colour)
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#1A1A1A", "#EAEAEA"),
        ).pack(anchor="w", padx=16, pady=(12, 0))
        return card

    def _numeric_row(self, parent: Any, label: str, attr_name: str) -> None:
        """Add a labelled integer entry row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(padx=16, pady=8, fill="x")
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12)).pack(side="left")
        entry = ctk.CTkEntry(row, width=80, justify="right", font=ctk.CTkFont(size=12))
        entry.pack(side="right")
        setattr(self, f"{attr_name}_entry", entry)

    def _float_row(self, parent: Any, label: str, attr_name: str) -> None:
        """Add a labelled float entry row."""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(padx=16, pady=8, fill="x")
        ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12)).pack(side="left")
        entry = ctk.CTkEntry(row, width=80, justify="right", font=ctk.CTkFont(size=12))
        entry.pack(side="right")
        setattr(self, f"{attr_name}_entry", entry)

    # ------------------------------------------------------------------ #
    #  Data loading & saving
    # ------------------------------------------------------------------ #

    def _load_values(self) -> None:
        self.form_width_entry.insert(0, str(self._config.FORM_WIDTH))
        self.form_height_entry.insert(0, str(self._config.FORM_HEIGHT))
        self.rows_entry.insert(0, str(self._config.ROW_COUNT))
        self.columns_entry.insert(0, str(self._config.COLUMN_COUNT))
        self.threshold_entry.insert(0, str(self._config.CHECKBOX_THRESHOLD))
        self.score_yes_entry.insert(0, str(self._config.SCORE_YES))
        self.score_somewhat_entry.insert(0, str(self._config.SCORE_SOMEWHAT))
        self.score_no_entry.insert(0, str(self._config.SCORE_NO))

    def _save(self) -> None:
        try:
            self._config.FORM_WIDTH = int(self.form_width_entry.get())
            self._config.FORM_HEIGHT = int(self.form_height_entry.get())
            self._config.ROW_COUNT = int(self.rows_entry.get())
            self._config.COLUMN_COUNT = int(self.columns_entry.get())
            self._config.CHECKBOX_THRESHOLD = float(self.threshold_entry.get())
            self._config.SCORE_YES = int(self.score_yes_entry.get())
            self._config.SCORE_SOMEWHAT = int(self.score_somewhat_entry.get())
            self._config.SCORE_NO = int(self.score_no_entry.get())
        except ValueError as exc:
            logger.error("Invalid setting value: %s", exc)
            return

        # Appearance
        ctk.set_appearance_mode(self.appear_var.get())

        # Language (convert label back to code)
        selected_label = self.lang_var.get()
        new_lang = self._label_to_code.get(selected_label, selected_label)
        if new_lang != I18n.get_language():
            I18n.set_language(new_lang)

        self._on_back()

    def _on_back(self) -> None:
        """Return to the main view via the callback."""
        if self._back_command:
            self._back_command()

    def _on_lang_preview(self, value: str) -> None:
        """Optional: update some labels immediately when user clicks a language."""
        # We keep it minimal; actual switch happens on Save.
        pass

    # ------------------------------------------------------------------ #
    #  Branding helpers
    # ------------------------------------------------------------------ #

    def _select_logo(self) -> None:
        """Open a file dialog to select a logo image."""
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if path:
            self._logo_path = path
            import os
            self.logo_preview_label.configure(text=os.path.basename(path))

    def _save_branding(self) -> None:
        """Save university name and logo path to persistence."""
        if self._persistence is None:
            return
        uni_name = self.uni_name_entry.get()
        self._persistence.set_setting("university_name", uni_name)
        if self._logo_path:
            self._persistence.set_setting("logo_path", self._logo_path)
        messagebox.showinfo(_("university_branding"), _("branding_saved"))

    # ------------------------------------------------------------------ #
    #  PDF coords helpers
    # ------------------------------------------------------------------ #

    def _save_pdf_coords(self) -> None:
        """Parse and save PDF template coordinates to persistence."""
        if self._persistence is None:
            return
        raw = self.pdf_coords_textbox.get("1.0", "end").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror(_("pdf_coords"), f"Invalid JSON: {exc}")
            return
        self._persistence.set_setting("pdf_coords", parsed)
        messagebox.showinfo(_("pdf_coords"), _("settings_saved"))

    # ------------------------------------------------------------------ #
    #  Survey questions helpers
    # ------------------------------------------------------------------ #

    def _save_questions(self) -> None:
        """Read all 14 question entries and save to persistence."""
        if self._persistence is None:
            return
        texts = [entry.get() for entry in self._question_entries]
        self._persistence.set_setting("question_texts", texts)
        messagebox.showinfo(_("survey_questions"), _("questions_saved"))
