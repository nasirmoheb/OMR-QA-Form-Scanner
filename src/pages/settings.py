"""Settings page — General settings only (language, appearance, branding)."""

from __future__ import annotations

import logging
import os
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

import icons as IC
import theme as T
from config import Config
from i18n import I18n, _, get_start, get_end, get_anchor, get_compound, rtl_text

logger = logging.getLogger("tadris_qa_system")


class SettingsFrame(ctk.CTkFrame):
    """Simplified settings page — General section only."""

    def __init__(
        self,
        master: Any,
        config: Config,
        back_command: Any = None,
        persistence: Any = None,
        router: Any = None,
    ) -> None:
        super().__init__(master, fg_color=T.PAGE_BG)
        self._config = config
        self._back = back_command
        self._persistence = persistence
        self._router = router
        self._logo_path: str = ""

        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # ── Header ────────────────────────────────────────────────────────
        header = T.transparent(self)
        header.pack(fill="x", padx=T.PAGE_PADDING, pady=(T.PAGE_PADDING, 0))

        title_col = T.transparent(header)
        title_col.pack(side=get_start())

        ctk.CTkLabel(
            title_col, text=_("settings"),
            font=T.h1(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor())

        ctk.CTkLabel(
            title_col, text=_("settings_subtitle"),
            font=T.small(), text_color=T.TEXT_SECONDARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(4, 0))

        # Save button
        IC.icon_button(
            header, "save", text="  " + _("save_all"),
            size=14, color="#000000", width=140, height=44,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(13, "bold"),
            corner_radius=T.RADIUS_MD, command=self._save,
        ).pack(side=get_end())

        T.divider(self).pack(fill="x", padx=T.PAGE_PADDING, pady=(16, 0))

        # ── Scrollable content ────────────────────────────────────────────
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=T.CARD_BORDER,
            scrollbar_button_hover_color=T.ACCENT,
        )
        scroll.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=T.PAGE_PADDING)

        self._build_language_card(scroll)
        self._build_appearance_card(scroll)
        self._build_branding_card(scroll)
        self._build_reset_card(scroll)

    # ------------------------------------------------------------------
    # Language card
    # ------------------------------------------------------------------

    def _build_language_card(self, parent: Any) -> None:
        card = self._card(parent, _("language_card_title"), _("language_subtitle"), "globe")
        body = T.transparent(card)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        self._lang_code_map = I18n.languages()
        self._label_to_code = {v: k for k, v in self._lang_code_map.items()}
        current_label = self._lang_code_map.get(I18n.get_language(), "English")
        self.lang_var = ctk.StringVar(value=current_label)

        lang_row = T.transparent(body)
        lang_row.pack(fill="x")
        self._lang_option_frames: dict[str, ctk.CTkFrame] = {}

        for code, label in self._lang_code_map.items():
            is_active = (label == current_label)
            opt = ctk.CTkFrame(
                lang_row,
                corner_radius=T.RADIUS_MD,
                fg_color=T.ACCENT_SUBTLE if is_active else T.SURFACE_RAISED,
                border_width=2,
                border_color=T.ACCENT if is_active else T.CARD_BORDER,
                cursor="hand2",
                width=140, height=56,
            )
            opt.pack(side=get_start(), padx=(0, 10))
            opt.pack_propagate(False)

            flag = {"en": "🇺🇸", "fa": "🇦🇫", "ps": "🇦🇫"}.get(code, "🌐")
            ctk.CTkLabel(opt, text=flag, font=T.font(18), text_color=T.TEXT_PRIMARY).place(relx=0.5, rely=0.3, anchor="center")
            ctk.CTkLabel(opt, text=label, font=T.font(10, "bold"), text_color=T.TEXT_PRIMARY).place(relx=0.5, rely=0.72, anchor="center")

            self._lang_option_frames[code] = opt

            def _select_lang(c=code, lbl=label):
                self.lang_var.set(lbl)
                for cc, fr in self._lang_option_frames.items():
                    active = cc == c
                    fr.configure(
                        fg_color=T.ACCENT_SUBTLE if active else T.SURFACE_RAISED,
                        border_color=T.ACCENT if active else T.CARD_BORDER,
                    )

            opt.bind("<Button-1>", lambda _e, c=code, lbl=label: _select_lang(c, lbl))

    # ------------------------------------------------------------------
    # Appearance card
    # ------------------------------------------------------------------

    def _build_appearance_card(self, parent: Any) -> None:
        card = self._card(parent, _("appearance_card_title"), _("appearance_subtitle"), "eye")
        body = T.transparent(card)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        self.appear_var = ctk.StringVar(value=ctk.get_appearance_mode())
        appear_row = T.transparent(body)
        appear_row.pack(fill="x")
        self._appear_frames: dict[str, ctk.CTkFrame] = {}

        _themes = [
            (_("light"),  "sun",   "#F5A623", "Light"),
            (_("dark"),   "moon",  "#4A9EFF", "Dark"),
            (_("system"), "cpu",   "#00C896", "System"),
        ]
        current_mode = ctk.get_appearance_mode()
        for mode_label, icon_n, color, mode_en in _themes:
            is_active = mode_en.lower() == current_mode.lower()
            opt = ctk.CTkFrame(
                appear_row,
                corner_radius=T.RADIUS_MD,
                fg_color=T.ACCENT_SUBTLE if is_active else T.SURFACE_RAISED,
                border_width=2,
                border_color=T.ACCENT if is_active else T.CARD_BORDER,
                cursor="hand2",
                width=110, height=72,
            )
            opt.pack(side=get_start(), padx=(0, 10))
            opt.pack_propagate(False)

            ctk.CTkLabel(opt, image=IC.icon(icon_n, size=22, color=color), text="").place(relx=0.5, rely=0.35, anchor="center")
            ctk.CTkLabel(opt, text=mode_label, font=T.font(11, "bold"), text_color=T.TEXT_PRIMARY).place(relx=0.5, rely=0.75, anchor="center")

            self._appear_frames[mode_en] = opt

            def _select_mode(m_en=mode_en):
                self.appear_var.set(m_en)
                for mm, fr in self._appear_frames.items():
                    active = mm == m_en
                    fr.configure(
                        fg_color=T.ACCENT_SUBTLE if active else T.SURFACE_RAISED,
                        border_color=T.ACCENT if active else T.CARD_BORDER,
                    )
                ctk.set_appearance_mode(m_en)

            opt.bind("<Button-1>", lambda _e, m_en=mode_en: _select_mode(m_en))

    # ------------------------------------------------------------------
    # Branding card
    # ------------------------------------------------------------------

    def _build_branding_card(self, parent: Any) -> None:
        card = self._card(parent, _("branding_card_title"), _("branding_subtitle"), "building")
        body = T.transparent(card)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        ctk.CTkLabel(
            body, text=_("university_name"),
            font=T.body(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(0, 6))

        uni_default = (
            self._persistence.get_setting("university_name", Config.DEFAULT_UNIVERSITY_NAME)
            if self._persistence else Config.DEFAULT_UNIVERSITY_NAME
        )
        self.uni_name_entry = ctk.CTkEntry(
            body, height=42,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
            font=T.body(),
            text_color=T.TEXT_PRIMARY,
            placeholder_text=_("university_name_placeholder"),
            placeholder_text_color=T.TEXT_MUTED,
        )
        if uni_default:
            self.uni_name_entry.insert(0, uni_default)
        self.uni_name_entry.pack(fill="x", pady=(0, 16))

        # Logo upload
        ctk.CTkLabel(
            body, text=_("institution_logo"),
            font=T.body(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(0, 4))

        logo_zone = ctk.CTkFrame(
            body, corner_radius=T.RADIUS_LG,
            fg_color=T.SURFACE_RAISED,
            border_width=2, border_color=T.CARD_BORDER,
            height=60,
        )
        logo_zone.pack(fill="x", pady=(0, 12))
        logo_zone.pack_propagate(False)

        self.logo_lbl = ctk.CTkLabel(
            logo_zone,
            image=IC.icon("upload", size=20, color=T._D_TEXT3),
            text="  " + _("no_logo"),
            font=T.body(), text_color=T.TEXT_MUTED,
            compound=get_compound(),
        )
        self.logo_lbl.place(relx=0.5, rely=0.5, anchor="center")

        IC.icon_button(
            body, "upload", text="  " + _("select_logo"),
            size=14, color=T._D_TEXT2, height=36, width=180,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.GHOST_TEXT, border_width=1, border_color=T.GHOST_BORDER,
            font=T.body(), corner_radius=T.RADIUS_MD,
            command=self._select_logo,
        ).pack(anchor=get_anchor())

    # ------------------------------------------------------------------
    # Reset card
    # ------------------------------------------------------------------

    def _build_reset_card(self, parent: Any) -> None:
        card = self._card(parent, _("reset_defaults"), _("reset_defaults_subtitle"), "refresh")
        body = T.transparent(card)
        body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        ctk.CTkLabel(
            body,
            text=_("reset_defaults_desc"),
            font=T.small(), text_color=T.TEXT_MUTED,
            wraplength=560, justify=get_start(), anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(0, 14))

        IC.icon_button(
            body, "refresh", text="  " + _("reset_defaults"),
            size=14, color="#FF4D6A", height=40, width=200,
            fg_color=T.SURFACE_RAISED, hover_color="#3A1A1F",
            text_color="#FF4D6A", border_width=1, border_color="#FF4D6A",
            font=T.font(13, "bold"), corner_radius=T.RADIUS_MD,
            command=self._reset_defaults,
        ).pack(anchor=get_anchor())

    # ------------------------------------------------------------------
    # Card helper
    # ------------------------------------------------------------------

    def _card(self, parent: Any, title: str, subtitle: str = "", icon_name: str = "") -> ctk.CTkFrame:
        card = T.card(parent)
        card.pack(fill="x", pady=(0, 16))

        ch = T.transparent(card)
        ch.pack(fill="x", padx=T.CARD_PADDING, pady=(T.CARD_PADDING, 0))

        if icon_name:
            ctk.CTkLabel(
                ch,
                image=IC.icon(icon_name, size=15, color=T._D_TEXT2),
                text=f"  {title}",
                font=T.h4(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
                compound=get_compound(),
            ).pack(side=get_start())
        else:
            ctk.CTkLabel(ch, text=title, font=T.h4(), text_color=T.TEXT_PRIMARY, anchor=get_anchor()).pack(side=get_start())

        if subtitle:
            ctk.CTkLabel(
                card, text=subtitle,
                font=T.small(), text_color=T.TEXT_MUTED, anchor=get_anchor(),
            ).pack(anchor=get_anchor(), padx=T.CARD_PADDING, pady=(2, 0))

        T.divider(card).pack(fill="x", padx=T.CARD_PADDING, pady=(10, 0))
        return card

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _save(self) -> None:
        # Language
        selected_label = self.lang_var.get()
        new_lang = self._label_to_code.get(selected_label, selected_label)
        if new_lang != I18n.get_language():
            I18n.set_language(new_lang)

        # Appearance
        ctk.set_appearance_mode(self.appear_var.get())

        # Persistence
        if self._persistence:
            self._persistence.set_setting("APPEARANCE_MODE", self.appear_var.get())
            self._persistence.set_setting("university_name", self.uni_name_entry.get())
            if self._logo_path:
                self._persistence.set_setting("logo_path", self._logo_path)
            self._config.save_to_persistence(self._persistence)

        # Invalidate the settings cache so next visit reflects saved values
        if self._router is not None:
            self._router.invalidate("settings")

        self._on_back()

    def _select_logo(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg")]
        )
        if path:
            self._logo_path = path
            self.logo_lbl.configure(
                text="  " + os.path.basename(path),
                text_color=T.TEXT_PRIMARY,
                image=IC.icon("check", size=18, color="#00C896"),
            )

    def _reset_defaults(self) -> None:
        confirmed = messagebox.askyesno(
            rtl_text(_("reset_defaults")),
            rtl_text(_("reset_confirm")),
        )
        if not confirmed:
            return

        # Reset config to defaults
        defaults = Config()
        self._config.CHECKBOX_THRESHOLD = defaults.CHECKBOX_THRESHOLD
        self._config.SCORE_YES          = defaults.SCORE_YES
        self._config.SCORE_SOMEWHAT     = defaults.SCORE_SOMEWHAT
        self._config.SCORE_NO           = defaults.SCORE_NO
        self._config.FORM_WIDTH         = defaults.FORM_WIDTH
        self._config.FORM_HEIGHT        = defaults.FORM_HEIGHT
        self._config.ROW_COUNT          = defaults.ROW_COUNT
        self._config.COLUMN_COUNT       = defaults.COLUMN_COUNT
        self._config.APPEARANCE_MODE    = defaults.APPEARANCE_MODE
        self._config.LANGUAGE           = defaults.LANGUAGE

        # Reset appearance
        ctk.set_appearance_mode(defaults.APPEARANCE_MODE)
        self.appear_var.set(defaults.APPEARANCE_MODE)
        for mm, fr in self._appear_frames.items():
            active = mm == defaults.APPEARANCE_MODE
            fr.configure(
                fg_color=T.ACCENT_SUBTLE if active else T.SURFACE_RAISED,
                border_color=T.ACCENT if active else T.CARD_BORDER,
            )

        # Reset language to Dari (fa)
        I18n.set_language(defaults.LANGUAGE)
        default_lang_label = self._lang_code_map.get(defaults.LANGUAGE, "Dari")
        self.lang_var.set(default_lang_label)
        for cc, fr in self._lang_option_frames.items():
            active = cc == defaults.LANGUAGE
            fr.configure(
                fg_color=T.ACCENT_SUBTLE if active else T.SURFACE_RAISED,
                border_color=T.ACCENT if active else T.CARD_BORDER,
            )

        # Reset university name
        self.uni_name_entry.delete(0, "end")
        self.uni_name_entry.insert(0, defaults.DEFAULT_UNIVERSITY_NAME)

        # Persist reset values
        if self._persistence:
            self._config.save_to_persistence(self._persistence)
            self._persistence.set_setting("university_name", defaults.DEFAULT_UNIVERSITY_NAME)
            self._persistence.set_setting("logo_path", "")
            self._persistence.set_setting("question_texts", [])
            self._persistence.set_setting("pdf_coords", {})

        messagebox.showinfo(rtl_text(_("reset_defaults")), rtl_text(_("reset_done")))

        # Invalidate cache so next visit rebuilds with reset values
        if self._router is not None:
            self._router.invalidate("settings")

        self._on_back()

    def _on_back(self) -> None:
        if self._back:
            self._back()
