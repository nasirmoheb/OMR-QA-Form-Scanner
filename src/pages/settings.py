"""Settings page — branding, geometry, detection, scoring, questions."""

from __future__ import annotations

import json
import logging
import os
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

import theme as T
from config import Config
from i18n import I18n, _

logger = logging.getLogger("omr_qa_scanner")


class SettingsFrame(ctk.CTkFrame):
    """Card-based settings page, embeddable in the main window."""

    def __init__(
        self,
        master: Any,
        config: Config,
        back_command: Any = None,
        persistence: Any = None,
    ) -> None:
        super().__init__(master, fg_color=T.PAGE_BG)
        self._config = config
        self._back = back_command
        self._persistence = persistence
        self._logo_path: str = ""
        self._entries: dict[str, ctk.CTkEntry] = {}

        self._build()
        self._load_values()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # ── Header ─────────────────────────────────────────────────────
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        T.secondary_btn(
            header,
            f"← {_('back')}",
            width=100,
            height=36,
            command=self._on_back,
        ).pack(side="left")

        T.page_title(header, f"⚙️  {_('settings')}").pack(side="left", padx=16)

        # ── Scrollable body ────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        self._general_card(scroll)
        self._geometry_card(scroll)
        self._detection_card(scroll)
        self._scoring_card(scroll)
        self._branding_card(scroll)
        self._coords_card(scroll)
        self._questions_card(scroll)

        # ── Footer ─────────────────────────────────────────────────────
        footer = T.transparent(self)
        footer.pack(fill="x", padx=T.PAGE_PADDING, pady=(0, T.PAGE_PADDING))

        T.primary_btn(footer, f"💾  {_('save')}", command=self._save, width=140).pack(side="right", padx=(8, 0))
        T.secondary_btn(footer, _("close"), command=self._on_back, width=100).pack(side="right")

    # ------------------------------------------------------------------
    # Cards
    # ------------------------------------------------------------------

    def _section_card(self, parent: Any, title: str, icon: str = "") -> ctk.CTkFrame:
        c = T.card(parent)
        c.pack(fill="x", pady=(0, 14))
        T.section_title(c, f"{icon}  {title}" if icon else title).pack(
            anchor="w", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0)
        )
        T.divider(c).pack(fill="x", padx=T.CARD_PADDING, pady=(10, 0))
        return c

    def _row(self, parent: Any, label: str, key: str, width: int = 100) -> ctk.CTkEntry:
        row = T.transparent(parent)
        row.pack(fill="x", padx=T.CARD_PADDING, pady=8)
        T.body_label(row, label).pack(side="left")
        entry = T.text_input(row, width=width, height=36)
        entry.pack(side="right")
        self._entries[key] = entry
        return entry

    def _general_card(self, parent: Any) -> None:
        c = self._section_card(parent, _("general"), "🌐")
        body = T.transparent(c)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # Language
        T.muted_label(body, _("language")).pack(anchor="w", pady=(0, 6))
        self._lang_code_map = I18n.languages()
        self._label_to_code = {v: k for k, v in self._lang_code_map.items()}
        current_label = self._lang_code_map.get(I18n.get_language(), "English")
        self.lang_var = ctk.StringVar(value=current_label)
        self.lang_seg = ctk.CTkSegmentedButton(
            body,
            values=list(self._lang_code_map.values()),
            variable=self.lang_var,
            font=T.body(),
            height=38,
            corner_radius=T.RADIUS_MD,
            fg_color=T.SURFACE_RAISED,
            selected_color=T.ACCENT,
            selected_hover_color=T.ACCENT_HOVER,
        )
        self.lang_seg.pack(fill="x", pady=(0, 14))
        self.lang_seg.set(current_label)

        T.divider(body).pack(fill="x", pady=(0, 14))

        # Appearance
        T.muted_label(body, _("appearance")).pack(anchor="w", pady=(0, 6))
        self.appear_var = ctk.StringVar(value=ctk.get_appearance_mode())
        self.appear_seg = ctk.CTkSegmentedButton(
            body,
            values=["Light", "Dark", "System"],
            variable=self.appear_var,
            font=T.body(),
            height=38,
            corner_radius=T.RADIUS_MD,
            fg_color=T.SURFACE_RAISED,
            selected_color=T.ACCENT,
            selected_hover_color=T.ACCENT_HOVER,
        )
        self.appear_seg.pack(fill="x")

    def _geometry_card(self, parent: Any) -> None:
        c = self._section_card(parent, _("form_geometry"), "📐")
        for label, key in [
            (_("form_width"),  "form_width"),
            (_("form_height"), "form_height"),
            (_("rows"),        "rows"),
            (_("columns"),     "columns"),
        ]:
            self._row(c, label, key)

    def _detection_card(self, parent: Any) -> None:
        c = self._section_card(parent, _("threshold"), "🎯")
        self._row(c, _("threshold"), "threshold")

    def _scoring_card(self, parent: Any) -> None:
        c = self._section_card(parent, f"{_('score_yes')} / {_('score_somewhat')} / {_('score_no')}", "🏆")
        for label, key in [
            (_("score_yes"),      "score_yes"),
            (_("score_somewhat"), "score_somewhat"),
            (_("score_no"),       "score_no"),
        ]:
            self._row(c, label, key)

    def _branding_card(self, parent: Any) -> None:
        c = self._section_card(parent, _("university_branding"), "🏛")
        body = T.transparent(c)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        # University name
        T.muted_label(body, _("university_name")).pack(anchor="w", pady=(0, 4))
        uni_default = (
            self._persistence.get_setting("university_name", "")
            if self._persistence else ""
        )
        self.uni_name_entry = T.text_input(body, height=40)
        if uni_default:
            self.uni_name_entry.insert(0, uni_default)
        self.uni_name_entry.pack(fill="x", pady=(0, 12))

        T.divider(body).pack(fill="x", pady=(0, 12))

        # Logo
        logo_row = T.transparent(body)
        logo_row.pack(fill="x")
        T.muted_label(logo_row, _("logo_upload")).pack(side="left")

        T.secondary_btn(
            logo_row,
            f"📁  {_('select_logo')}",
            command=self._select_logo,
            height=34,
            width=160,
        ).pack(side="right")

        self.logo_lbl = T.muted_label(body, _("no_logo"))
        self.logo_lbl.pack(anchor="w", pady=(6, 12))

        if self._persistence:
            T.primary_btn(
                body,
                f"💾  {_('save')}",
                command=self._save_branding,
                height=36,
                width=120,
            ).pack(anchor="e")

    def _coords_card(self, parent: Any) -> None:
        c = self._section_card(parent, _("pdf_coords"), "📍")
        body = T.transparent(c)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        coords_default = "{}"
        if self._persistence:
            stored = self._persistence.get_setting("pdf_coords")
            if stored is not None:
                try:
                    coords_default = json.dumps(stored, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        self.pdf_coords_box = ctk.CTkTextbox(
            body,
            height=120,
            font=T.mono(),
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
        )
        self.pdf_coords_box.pack(fill="x", pady=(0, 10))
        self.pdf_coords_box.insert("1.0", coords_default)

        if self._persistence:
            T.primary_btn(
                body,
                f"💾  {_('save')}",
                command=self._save_coords,
                height=36,
                width=120,
            ).pack(anchor="e")

    def _questions_card(self, parent: Any) -> None:
        c = self._section_card(parent, _("survey_questions"), "❓")
        body = T.transparent(c)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        from pdf_generator import _DARI_QUESTIONS
        defaults = list(_DARI_QUESTIONS)
        if self._persistence:
            stored = self._persistence.get_setting("question_texts")
            if isinstance(stored, list) and len(stored) == 14:
                defaults = stored

        # Header
        hdr = T.transparent(body)
        hdr.pack(fill="x", pady=(0, 6))
        T.muted_label(hdr, _("question_num")).pack(side="left")
        T.muted_label(hdr, _("question_text")).pack(side="left", padx=(20, 0))

        q_scroll = ctk.CTkScrollableFrame(body, height=280, fg_color="transparent")
        q_scroll.pack(fill="x", pady=(0, 10))

        self._q_entries: list[ctk.CTkEntry] = []
        for i in range(14):
            row = T.transparent(q_scroll)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=f"Q{i + 1:02d}",
                font=T.font(11, "bold"),
                text_color=T.ACCENT,
                width=36,
                anchor="w",
            ).pack(side="left", padx=(0, 8))

            entry = T.text_input(row, height=36)
            entry.insert(0, defaults[i] if i < len(defaults) else "")
            entry.pack(side="left", fill="x", expand=True)
            self._q_entries.append(entry)

        if self._persistence:
            T.primary_btn(
                body,
                f"💾  {_('save_questions')}",
                command=self._save_questions,
                height=36,
                width=160,
            ).pack(anchor="e")

    # ------------------------------------------------------------------
    # Load / Save
    # ------------------------------------------------------------------

    def _load_values(self) -> None:
        mapping = {
            "form_width":     str(self._config.FORM_WIDTH),
            "form_height":    str(self._config.FORM_HEIGHT),
            "rows":           str(self._config.ROW_COUNT),
            "columns":        str(self._config.COLUMN_COUNT),
            "threshold":      str(self._config.CHECKBOX_THRESHOLD),
            "score_yes":      str(self._config.SCORE_YES),
            "score_somewhat": str(self._config.SCORE_SOMEWHAT),
            "score_no":       str(self._config.SCORE_NO),
        }
        for key, val in mapping.items():
            e = self._entries.get(key)
            if e:
                e.delete(0, "end")
                e.insert(0, val)

    def _save(self) -> None:
        def _int(key: str, default: int) -> int:
            try:
                return int(self._entries[key].get())
            except (ValueError, KeyError):
                return default

        def _float(key: str, default: float) -> float:
            try:
                return float(self._entries[key].get())
            except (ValueError, KeyError):
                return default

        self._config.FORM_WIDTH        = _int("form_width",     self._config.FORM_WIDTH)
        self._config.FORM_HEIGHT       = _int("form_height",    self._config.FORM_HEIGHT)
        self._config.ROW_COUNT         = _int("rows",           self._config.ROW_COUNT)
        self._config.COLUMN_COUNT      = _int("columns",        self._config.COLUMN_COUNT)
        self._config.CHECKBOX_THRESHOLD = _float("threshold",   self._config.CHECKBOX_THRESHOLD)
        self._config.SCORE_YES         = _int("score_yes",      self._config.SCORE_YES)
        self._config.SCORE_SOMEWHAT    = _int("score_somewhat", self._config.SCORE_SOMEWHAT)
        self._config.SCORE_NO          = _int("score_no",       self._config.SCORE_NO)

        ctk.set_appearance_mode(self.appear_var.get())

        selected_label = self.lang_var.get()
        new_lang = self._label_to_code.get(selected_label, selected_label)
        if new_lang != I18n.get_language():
            I18n.set_language(new_lang)

        self._on_back()

    def _on_back(self) -> None:
        if self._back:
            self._back()

    def _select_logo(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if path:
            self._logo_path = path
            self.logo_lbl.configure(text=os.path.basename(path), text_color=T.TEXT_PRIMARY)

    def _save_branding(self) -> None:
        if not self._persistence:
            return
        self._persistence.set_setting("university_name", self.uni_name_entry.get())
        if self._logo_path:
            self._persistence.set_setting("logo_path", self._logo_path)
        messagebox.showinfo(_("university_branding"), _("branding_saved"))

    def _save_coords(self) -> None:
        if not self._persistence:
            return
        raw = self.pdf_coords_box.get("1.0", "end").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror(_("pdf_coords"), f"Invalid JSON: {exc}")
            return
        self._persistence.set_setting("pdf_coords", parsed)
        messagebox.showinfo(_("pdf_coords"), _("settings_saved"))

    def _save_questions(self) -> None:
        if not self._persistence:
            return
        texts = [e.get() for e in self._q_entries]
        self._persistence.set_setting("question_texts", texts)
        messagebox.showinfo(_("survey_questions"), _("questions_saved"))
