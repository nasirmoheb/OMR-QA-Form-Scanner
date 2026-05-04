"""Modern settings window for the OMR QA Form Scanner."""

from __future__ import annotations

import logging
from typing import Any

import customtkinter as ctk

from config import Config
from i18n import I18n, _

logger = logging.getLogger("omr_qa_scanner")


class SettingsFrame(ctk.CTkFrame):
    """A modern, card-based settings frame for embedding in the main window."""

    def __init__(self, master: Any, config: Config, back_command: Any = None) -> None:
        super().__init__(master, fg_color="transparent")
        self._config = config
        self._back_command = back_command

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
