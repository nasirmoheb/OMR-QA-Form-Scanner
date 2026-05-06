"""Settings page - sidebar navigation with beautiful section panels."""


from __future__ import annotations

import json
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


def _tint(hex_color: str, factor: float = 0.15) -> str:
    """Blend hex_color toward the dark-navy page background (#141C2E).

    Returns a solid hex color suitable for Tkinter fg_color.
    factor=0.15 → very subtle tint; factor=0.35 → more visible.
    """
    bg = (20, 28, 46)   # #141C2E dark-navy
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except (ValueError, IndexError):
        return hex_color
    nr = int(r * factor + bg[0] * (1 - factor))
    ng = int(g * factor + bg[1] * (1 - factor))
    nb = int(b * factor + bg[2] * (1 - factor))
    return f"#{nr:02x}{ng:02x}{nb:02x}"


# ---------------------------------------------------------------------------
# Sidebar nav items: (section_id, icon_name, label_key, accent_hex)
# ---------------------------------------------------------------------------
_NAV_ITEMS = [
    ("general",    "globe",      "general",            T._D_BLUE),
    ("detection",  "eye",        "threshold",          T._D_GREEN),
    ("scoring",    "bar_chart",  "score_yes",          T._D_AMBER),
    ("questions",  "file_text",  "survey_questions",   "#38BDF8"),
    ("advanced",   "cpu",        "pdf_coords",         T._D_RED),
]

# Section subtitles shown in the content panel header — resolved at call time via _()
_SECTION_META_KEYS = {
    "general":   ("settings_section_general",   "settings_section_general_sub"),
    "detection": ("settings_section_detection", "settings_section_detection_sub"),
    "scoring":   ("settings_section_scoring",   "settings_section_scoring_sub"),
    "questions": ("settings_section_questions", "settings_section_questions_sub"),
    "advanced":  ("settings_section_advanced",  "settings_section_advanced_sub"),
}


class SettingsFrame(ctk.CTkFrame):
    """Beautiful settings page with sidebar navigation and section panels."""

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
        self._active_section: str = "general"
        self._nav_buttons: dict[str, ctk.CTkFrame] = {}
        self._panels: dict[str, ctk.CTkFrame] = {}

        self._build()
        self._load_values()
        self._switch_section("general")

    # ------------------------------------------------------------------
    # Top-level layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # ── Top header bar ────────────────────────────────────────────────
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

        IC.icon_button(
            header, "save", text="  " + _("save_all"),
            size=14, color="#000000", width=140, height=44,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#000000", font=T.font(13, "bold"),
            corner_radius=T.RADIUS_MD, command=self._save,
        ).pack(side=get_end())

        # ── Body: sidebar + content ───────────────────────────────────────
        body = T.transparent(self)
        body.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=16)

        # Left sidebar
        self._sidebar = ctk.CTkFrame(body, width=220, fg_color=T.SURFACE, corner_radius=T.RADIUS_LG)
        self._sidebar.pack(side=get_start(), fill="y", padx=(0, 16))
        self._sidebar.pack_propagate(False)

        self._nav_inner = T.transparent(self._sidebar)
        self._nav_inner.pack(fill="both", expand=True, padx=10, pady=16)

        # Nav section label
        ctk.CTkLabel(
            self._nav_inner,
            text=_("sections"),
            font=T.font(9, "bold"),
            text_color=T.TEXT_MUTED,
            anchor=get_anchor(),
        ).pack(anchor=get_anchor(), padx=8, pady=(0, 8))

        # Content area
        self._content_host = T.transparent(body)
        self._content_host.pack(side=get_start(), fill="both", expand=True)

        # Build nav items
        for section_id, icon_name, label_key, accent in _NAV_ITEMS:
            self._make_nav_item(section_id, icon_name, label_key, accent)

        # Spacer + version label at bottom of sidebar
        T.transparent(self._nav_inner).pack(fill="both", expand=True)
        ctk.CTkLabel(
            self._nav_inner,
            text="Tadris QA System",
            font=T.font(9),
            text_color=T.TEXT_MUTED,
            anchor=get_anchor(),
        ).pack(anchor=get_anchor(), padx=8, pady=(0, 4))

        # Build all panels
        self._panels["general"]   = self._build_general_panel(self._content_host)
        self._panels["detection"] = self._build_detection_panel(self._content_host)
        self._panels["scoring"]   = self._build_scoring_panel(self._content_host)
        self._panels["questions"] = self._build_questions_panel(self._content_host)
        self._panels["advanced"]  = self._build_advanced_panel(self._content_host)

        for panel in self._panels.values():
            panel.pack_forget()

    # ------------------------------------------------------------------
    # Sidebar navigation
    # ------------------------------------------------------------------

    def _make_nav_item(
        self, section_id: str, icon_name: str, label_key: str, accent: str
    ) -> None:
        """Create a sidebar nav row with icon, label, and active indicator."""
        row = ctk.CTkFrame(
            self._nav_inner,
            corner_radius=T.RADIUS_MD,
            fg_color="transparent",
            cursor="hand2",
            height=44,
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        # Active left-edge pill (hidden by default)
        pill = ctk.CTkFrame(row, width=3, corner_radius=2, fg_color=accent)
        pill.place(x=0, rely=0.15, relheight=0.7)
        pill.lower()  # hidden initially

        # Icon
        icon_lbl = ctk.CTkLabel(
            row,
            image=IC.icon(icon_name, size=16, color=T._D_TEXT3),
            text="",
            width=20,
        )
        icon_lbl.place(x=14, rely=0.5, anchor=get_anchor())

        # Label
        text_lbl = ctk.CTkLabel(
            row,
            text=_(_SECTION_META_KEYS.get(section_id, (section_id, ""))[0]),
            font=T.body(),
            text_color=T.TEXT_SECONDARY,
            anchor=get_anchor(),
        )
        text_lbl.place(x=42, rely=0.5, anchor=get_anchor())

        # Store references for active-state toggling
        self._nav_buttons[section_id] = {
            "row": row, "pill": pill,
            "icon_lbl": icon_lbl, "text_lbl": text_lbl,
            "icon_name": icon_name, "accent": accent,
        }

        def _click(sid=section_id):
            self._switch_section(sid)

        for w in (row, icon_lbl, text_lbl):
            w.bind("<Button-1>", lambda _e, s=section_id: _click(s))
            w.bind("<Enter>",    lambda _e, r=row: r.configure(fg_color=T.GHOST_HOVER))
            w.bind("<Leave>",    lambda _e, r=row, s=section_id:
                   r.configure(fg_color=T.ACCENT_SUBTLE if s == self._active_section else "transparent"))

    def _switch_section(self, section_id: str) -> None:
        """Show the selected panel and update sidebar active state."""
        prev = self._active_section
        self._active_section = section_id

        # Update nav button states
        for sid, widgets in self._nav_buttons.items():
            active = sid == section_id
            accent = widgets["accent"]
            row = widgets["row"]
            pill = widgets["pill"]
            icon_lbl = widgets["icon_lbl"]
            text_lbl = widgets["text_lbl"]
            icon_name = widgets["icon_name"]

            if active:
                row.configure(fg_color=T.ACCENT_SUBTLE)
                pill.lift()
                icon_lbl.configure(image=IC.icon(icon_name, size=16, color=accent))
                text_lbl.configure(text_color=T.TEXT_PRIMARY, font=T.font(13, "bold"))
            else:
                row.configure(fg_color="transparent")
                pill.lower()
                icon_lbl.configure(image=IC.icon(icon_name, size=16, color=T._D_TEXT3))
                text_lbl.configure(text_color=T.TEXT_SECONDARY, font=T.body())

        # Swap panels
        for sid, panel in self._panels.items():
            if sid == section_id:
                panel.pack(fill="both", expand=True)
            else:
                panel.pack_forget()

    # ------------------------------------------------------------------
    # Panel helpers
    # ------------------------------------------------------------------

    def _panel_scaffold(self, parent: Any, section_id: str) -> ctk.CTkScrollableFrame:
        """Create a scrollable panel with a section header."""
        outer = T.transparent(parent)

        # Panel header
        ph = ctk.CTkFrame(outer, fg_color=T.PAGE_BG, corner_radius=0, height=72)
        ph.pack(fill="x")
        ph.pack_propagate(False)

        ph_inner = T.transparent(ph)
        ph_inner.pack(fill="both", expand=True, padx=T.PAGE_PADDING)

        title_key, sub_key = _SECTION_META_KEYS.get(section_id, (section_id, ""))
        title_text    = _(title_key)
        subtitle_text = _(sub_key)
        # Find accent for this section
        accent = next((a for sid, _, _, a in _NAV_ITEMS if sid == section_id), T._D_ACCENT)
        icon_name = next((ic for sid, ic, _, _ in _NAV_ITEMS if sid == section_id), "settings")

        icon_badge = ctk.CTkFrame(
            ph_inner, width=40, height=40,
            corner_radius=T.RADIUS_MD,
            fg_color=_tint(accent, 0.18),
        )
        icon_badge.pack(side=get_start(), pady=16)
        icon_badge.pack_propagate(False)
        ctk.CTkLabel(
            icon_badge,
            image=IC.icon(icon_name, size=20, color=accent),
            text="",
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_col = T.transparent(ph_inner)
        title_col.pack(side=get_start(), padx=14)
        ctk.CTkLabel(
            title_col, text=title_text,
            font=T.h3(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor())
        ctk.CTkLabel(
            title_col, text=subtitle_text,
            font=T.small(), text_color=T.TEXT_MUTED, anchor=get_anchor(),
        ).pack(anchor=get_anchor())

        T.divider(outer).pack(fill="x")

        # Scrollable content
        scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=T.CARD_BORDER,
            scrollbar_button_hover_color=T.ACCENT,
        )
        scroll.pack(fill="both", expand=True, padx=T.PAGE_PADDING, pady=T.PAGE_PADDING)
        return outer, scroll

    def _field_card(
        self, parent: Any, title: str, subtitle: str = "", icon_name: str = ""
    ) -> ctk.CTkFrame:
        """A card with a title row and body area for fields."""
        card = T.card(parent)
        card.pack(fill="x", pady=(0, 16))

        # Card header
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

    def _field_row(
        self, parent: Any, label: str, key: str,
        hint: str = "", width: int = 120,
    ) -> ctk.CTkEntry:
        """A label + entry row inside a card body."""
        row = T.transparent(parent)
        row.pack(fill="x", padx=T.CARD_PADDING, pady=(12, 0))

        left = T.transparent(row)
        left.pack(side=get_start(), fill="x", expand=True)
        ctk.CTkLabel(left, text=label, font=T.body(), text_color=T.TEXT_PRIMARY, anchor=get_anchor()).pack(anchor=get_anchor())
        if hint:
            ctk.CTkLabel(left, text=hint, font=T.small(), text_color=T.TEXT_MUTED, anchor=get_anchor()).pack(anchor=get_anchor())

        entry = ctk.CTkEntry(
            row, width=width, height=38,
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
            font=T.body(),
            text_color=T.TEXT_PRIMARY,
            justify="center",
        )
        entry.pack(side=get_end())
        self._entries[key] = entry
        return entry

    def _save_btn(self, parent: Any, command: Any, text: str = "") -> None:
        """A right-aligned save button at the bottom of a card body."""
        row = T.transparent(parent)
        row.pack(fill="x", padx=T.CARD_PADDING, pady=(14, T.CARD_PADDING))
        IC.icon_button(
            row, "save", text="  " + (text or _("save")),
            size=13, color="#FFFFFF", height=36, width=140,
            fg_color=T.ACCENT, hover_color=T.ACCENT_HOVER,
            text_color="#FFFFFF", font=T.font(12, "bold"),
            corner_radius=T.RADIUS_MD, command=command,
        ).pack(side=get_end())

    # ------------------------------------------------------------------
    # Panel: General
    # ------------------------------------------------------------------

    def _build_general_panel(self, parent: Any) -> ctk.CTkFrame:
        outer, scroll = self._panel_scaffold(parent, "general")

        # ── Language card ─────────────────────────────────────────────────
        lang_card = self._field_card(
            scroll, _("language_card_title"), _("language_subtitle"), "globe"
        )
        lang_body = T.transparent(lang_card)
        lang_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        self._lang_code_map = I18n.languages()
        self._label_to_code = {v: k for k, v in self._lang_code_map.items()}
        current_label = self._lang_code_map.get(I18n.get_language(), "English")
        self.lang_var = ctk.StringVar(value=current_label)

        # Language option cards
        lang_row = T.transparent(lang_body)
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
            ctk.CTkLabel(
                opt, text=flag, font=T.font(18), text_color=T.TEXT_PRIMARY,
            ).place(relx=0.5, rely=0.3, anchor="center")
            ctk.CTkLabel(
                opt, text=label, font=T.font(10, "bold"), text_color=T.TEXT_PRIMARY,
            ).place(relx=0.5, rely=0.72, anchor="center")

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

        # ── Appearance card ───────────────────────────────────────────────
        appear_card = self._field_card(
            scroll, _("appearance_card_title"), _("appearance_subtitle"), "eye"
        )
        appear_body = T.transparent(appear_card)
        appear_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        self.appear_var = ctk.StringVar(value=ctk.get_appearance_mode())
        appear_row = T.transparent(appear_body)
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

            ctk.CTkLabel(
                opt,
                image=IC.icon(icon_n, size=22, color=color),
                text="",
            ).place(relx=0.5, rely=0.35, anchor="center")
            ctk.CTkLabel(
                opt, text=mode_label, font=T.font(11, "bold"), text_color=T.TEXT_PRIMARY,
            ).place(relx=0.5, rely=0.75, anchor="center")

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

        # ── Branding card ─────────────────────────────────────────────────
        brand_card = self._field_card(
            scroll, _("branding_card_title"), _("branding_subtitle"), "building"
        )
        brand_body = T.transparent(brand_card)
        brand_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        ctk.CTkLabel(
            brand_body, text=_("university_name"),
            font=T.body(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(0, 6))
        
        uni_default = (
            self._persistence.get_setting("university_name", "Kabul University")
            if self._persistence else "Kabul University"
        )
        self.uni_name_entry = ctk.CTkEntry(
            brand_body, height=42,
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
            brand_body, text=_("institution_logo"),
            font=T.body(), text_color=T.TEXT_PRIMARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(0, 4))

        logo_zone = ctk.CTkFrame(
            brand_body, corner_radius=T.RADIUS_LG,
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
            brand_body, "upload", text="  " + _("select_logo"),
            size=14, color=T._D_TEXT2, height=36, width=180,
            fg_color=T.GHOST_BG, hover_color=T.GHOST_HOVER,
            text_color=T.GHOST_TEXT, border_width=1, border_color=T.GHOST_BORDER,
            font=T.body(), corner_radius=T.RADIUS_MD,
            command=self._select_logo,
        ).pack(anchor=get_anchor())

        return outer

    # ------------------------------------------------------------------
    # Panel: Detection
    # ------------------------------------------------------------------

    def _build_detection_panel(self, parent: Any) -> ctk.CTkFrame:
        outer, scroll = self._panel_scaffold(parent, "detection")

        thresh_card = self._field_card(
            scroll, _("checkbox_detection"),
            _("detection_subtitle"), "eye"
        )
        self._field_row(
            thresh_card, _("detection_threshold"),
            "threshold", _("threshold_hint"), 120,
        )

        # Visual threshold guide
        guide = T.inner_card(thresh_card)
        guide.pack(fill="x", padx=T.CARD_PADDING, pady=(10, T.CARD_PADDING))
        g_inner = T.transparent(guide)
        g_inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(
            g_inner, text=_("threshold_guide"),
            font=T.small(), text_color=T.TEXT_SECONDARY, anchor=get_anchor(),
        ).pack(anchor=get_anchor())
        ctk.CTkLabel(
            g_inner,
            text=_("threshold_warning"),
            font=T.small(), text_color=T.TEXT_MUTED, anchor=get_anchor(), justify=get_start(),
        ).pack(anchor=get_anchor(), pady=(4, 0))

        # Form geometry card
        geom_card = self._field_card(
            scroll, _("form_geometry_card"),
            _("form_geometry_subtitle"), "layers"
        )
        for label, key, hint in [
            (_("form_width_label"),  "form_width",  _("pixels")),
            (_("form_height_label"), "form_height", _("pixels")),
            (_("row_count"),         "rows",        _("questions_per_form")),
            (_("column_count"),      "columns",     _("options_per_question")),
        ]:
            self._field_row(geom_card, label, key, hint)
        T.transparent(geom_card).pack(pady=8)  # bottom padding

        return outer

    # ------------------------------------------------------------------
    # Panel: Scoring
    # ------------------------------------------------------------------

    def _build_scoring_panel(self, parent: Any) -> ctk.CTkFrame:
        outer, scroll = self._panel_scaffold(parent, "scoring")

        score_card = self._field_card(
            scroll, _("likert_scale_weights"),
            _("scoring_subtitle"), "bar_chart"
        )

        # Visual score preview chips
        preview = T.transparent(score_card)
        preview.pack(fill="x", padx=T.CARD_PADDING, pady=(12, 0))

        _score_items = [
            (_("yes"),      "score_yes",      "#00C896", "3",   _("optimal_satisfaction")),
            (_("somewhat"), "score_somewhat", "#F5A623", "2",   _("partial_improvement")),
            (_("no"),       "score_no",       "#FF4D6A", "1",   _("critical_action")),
        ]
        for answer, key, color, default_val, desc in _score_items:
            chip_row = ctk.CTkFrame(
                preview, corner_radius=T.RADIUS_MD,
                fg_color=T.SURFACE_RAISED, height=64,
            )
            chip_row.pack(fill="x", pady=(0, 8))
            chip_row.pack_propagate(False)

            # Color dot
            dot = ctk.CTkFrame(chip_row, width=6, corner_radius=3, fg_color=color)
            dot.place(x=0, rely=0.1, relheight=0.8)

            inner = T.transparent(chip_row)
            inner.pack(fill="both", expand=True, padx=(16, 14))

            left = T.transparent(inner)
            left.pack(side=get_start(), fill="y")
            ctk.CTkLabel(
                left, text=answer, font=T.font(13, "bold"),
                text_color=color, anchor=get_anchor(),
            ).pack(anchor=get_anchor(), pady=(10, 0))
            ctk.CTkLabel(
                left, text=desc, font=T.small(),
                text_color=T.TEXT_MUTED, anchor=get_anchor(),
            ).pack(anchor=get_anchor())

            entry = ctk.CTkEntry(
                inner, width=80, height=36,
                corner_radius=T.RADIUS_MD,
                fg_color=T.INPUT_BG,
                border_color=color,
                border_width=2,
                font=T.font(15, "bold"),
                text_color=color,
                justify="center",
            )
            entry.pack(side=get_end(), pady=14)
            self._entries[key] = entry

        # Info note
        note = T.inner_card(score_card)
        note.pack(fill="x", padx=T.CARD_PADDING, pady=(4, T.CARD_PADDING))
        ctk.CTkLabel(
            note,
            text=_("likert_info"),
            font=T.small(), text_color=T.TEXT_MUTED,
            wraplength=560, justify=get_start(), anchor=get_anchor(),
        ).pack(padx=14, pady=10)

        return outer

    # ------------------------------------------------------------------
    # Panel: Branding
    # ------------------------------------------------------------------



    # ------------------------------------------------------------------
    # Panel: Questions
    # ------------------------------------------------------------------

    def _build_questions_panel(self, parent: Any) -> ctk.CTkFrame:
        outer, scroll = self._panel_scaffold(parent, "questions")

        q_card = self._field_card(
            scroll, _("survey_question_texts"),
            _("questions_subtitle"), "file_text"
        )
        q_body = T.transparent(q_card)
        q_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        from pdf_generator import _DARI_QUESTIONS
        defaults = list(_DARI_QUESTIONS)
        if self._persistence:
            stored = self._persistence.get_setting("question_texts")
            if isinstance(stored, list) and len(stored) == 14:
                defaults = stored

        # Column headers
        hdr = T.transparent(q_body)
        hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(hdr, text=_("question_num_short"), font=T.font(10, "bold"), text_color=T.TEXT_MUTED, width=36, anchor=get_anchor()).pack(side=get_start())
        ctk.CTkLabel(hdr, text=_("question_text_header"), font=T.font(10, "bold"), text_color=T.TEXT_MUTED, anchor=get_anchor()).pack(side=get_start(), padx=(8, 0))

        self._q_entries: list[ctk.CTkEntry] = []

        # Dimension color bands
        _DIM_COLORS_Q = {
            frozenset([1,2,3]):       "#4A9EFF",
            frozenset([4,5,9,12]):    "#00C896",
            frozenset([7,8,10,11]):   "#F5A623",
            frozenset([6,13,14]):     "#A78BFA",
        }
        _DIM_LABELS = {
            frozenset([1,2,3]):       "A",
            frozenset([4,5,9,12]):    "B",
            frozenset([7,8,10,11]):   "C",
            frozenset([6,13,14]):     "D",
        }

        def _dim_color(q_num: int) -> str:
            for qs, color in _DIM_COLORS_Q.items():
                if q_num in qs:
                    return color
            return T._D_TEXT3

        def _dim_label(q_num: int) -> str:
            for qs, lbl in _DIM_LABELS.items():
                if q_num in qs:
                    return lbl
            return ""

        for i in range(14):
            q_num = i + 1
            color = _dim_color(q_num)
            dim_lbl = _dim_label(q_num)

            row = ctk.CTkFrame(
                q_body, corner_radius=T.RADIUS_SM,
                fg_color=T.SURFACE_RAISED, height=46,
            )
            row.pack(fill="x", pady=(0, 4))
            row.pack_propagate(False)

            # Dimension color stripe
            stripe = ctk.CTkFrame(row, width=4, corner_radius=0, fg_color=color)
            stripe.pack(side=get_start(), fill="y")

            # Q number badge
            badge = ctk.CTkFrame(row, width=36, fg_color="transparent")
            badge.pack(side=get_start(), fill="y")
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge, text=f"Q{q_num:02d}",
                font=T.font(10, "bold"), text_color=color, anchor="center",
            ).place(relx=0.5, rely=0.5, anchor="center")

            # Dim badge
            if dim_lbl:
                dim_badge = ctk.CTkFrame(
                    row, width=20, height=20,
                    corner_radius=4,
                    fg_color=_tint(color, 0.25),
                )
                dim_badge.pack(side=get_start(), padx=(0, 6))
                dim_badge.pack_propagate(False)
                ctk.CTkLabel(
                    dim_badge, text=dim_lbl,
                    font=T.font(9, "bold"), text_color=color,
                ).place(relx=0.5, rely=0.5, anchor="center")

            entry = ctk.CTkEntry(
                row, height=34,
                corner_radius=T.RADIUS_SM,
                fg_color="transparent",
                border_width=0,
                font=T.body(),
                text_color=T.TEXT_PRIMARY,
            )
            entry.insert(0, defaults[i] if i < len(defaults) else "")
            entry.pack(side=get_start(), fill="x", expand=True, padx=(4, 8))
            self._q_entries.append(entry)

        # Dimension legend
        legend = T.inner_card(q_body)
        legend.pack(fill="x", pady=(12, 0))
        leg_inner = T.transparent(legend)
        leg_inner.pack(fill="x", padx=14, pady=10)
        ctk.CTkLabel(leg_inner, text=_("dimension_groups"), font=T.font(10, "bold"), text_color=T.TEXT_SECONDARY, anchor=get_anchor()).pack(anchor=get_anchor(), pady=(0, 6))
        leg_row = T.transparent(leg_inner)
        leg_row.pack(fill="x")
        for lbl, color, desc_key in [
            ("A", "#4A9EFF", "curriculum_resources"),
            ("B", "#00C896", "pedagogical_delivery"),
            ("C", "#F5A623", "classroom_management"),
            ("D", "#A78BFA", "modern_teaching"),
        ]:
            chip = ctk.CTkFrame(leg_row, corner_radius=T.RADIUS_SM, fg_color=_tint(color, 0.18))
            chip.pack(side=get_start(), padx=(0, 8))
            ctk.CTkLabel(chip, text=f"{lbl}  {_(desc_key)}", font=T.small(), text_color=color).pack(padx=10, pady=4)

        self._save_btn(q_card, self._save_questions, _("save_questions"))

        return outer

    # ------------------------------------------------------------------
    # Panel: Advanced
    # ------------------------------------------------------------------

    def _build_advanced_panel(self, parent: Any) -> ctk.CTkFrame:
        outer, scroll = self._panel_scaffold(parent, "advanced")

        coords_card = self._field_card(
            scroll, _("pdf_coords_card"),
            _("pdf_coords_subtitle"), "cpu"
        )
        coords_body = T.transparent(coords_card)
        coords_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        coords_default = "{}"
        if self._persistence:
            stored = self._persistence.get_setting("pdf_coords")
            if stored is not None:
                try:
                    coords_default = json.dumps(stored, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        self.pdf_coords_box = ctk.CTkTextbox(
            coords_body, height=200,
            font=T.mono(),
            corner_radius=T.RADIUS_MD,
            fg_color=T.INPUT_BG,
            border_color=T.INPUT_BORDER,
            border_width=1,
            text_color=T.TEXT_PRIMARY,
        )
        self.pdf_coords_box.pack(fill="x", pady=(0, 4))
        self.pdf_coords_box.insert("1.0", coords_default)

        ctk.CTkLabel(
            coords_body,
            text=_("pdf_coords_example"),
            font=T.small(), text_color=T.TEXT_MUTED, anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(0, 4))

        self._save_btn(coords_card, self._save_coords)

        # QA thresholds info card
        qa_card = self._field_card(
            scroll, _("qa_thresholds"),
            _("qa_thresholds_subtitle"), "warning"
        )
        qa_body = T.transparent(qa_card)
        qa_body.pack(fill="x", padx=T.CARD_PADDING, pady=T.CARD_PADDING)

        _thresholds = [
            (_("dimension_alert_threshold"), f"{self._config.DIMENSION_ALERT_THRESHOLD}", "#F5A623",
             _("dimension_alert_desc")),
            (_("polarization_threshold"), f"{self._config.POLARIZATION_SD_THRESHOLD}", "#FB7185",
             _("polarization_desc")),
            (_("batch_score_alert"), f"{self._config.BATCH_SCORE_ALERT_THRESHOLD}%", "#FF4D6A",
             _("batch_alert_desc")),
            (_("punctuality_threshold"), f"{int(self._config.PUNCTUALITY_NO_THRESHOLD * 100)}%", "#F5A623",
             _("punctuality_desc")),
        ]
        for label, value, color, desc in _thresholds:
            t_row = ctk.CTkFrame(qa_body, corner_radius=T.RADIUS_SM, fg_color=T.SURFACE_RAISED, height=52)
            t_row.pack(fill="x", pady=(0, 6))
            t_row.pack_propagate(False)

            dot = ctk.CTkFrame(t_row, width=4, corner_radius=0, fg_color=color)
            dot.pack(side=get_start(), fill="y")

            inner = T.transparent(t_row)
            inner.pack(fill="both", expand=True, padx=14)

            ctk.CTkLabel(inner, text=label, font=T.font(12, "bold"), text_color=T.TEXT_PRIMARY, anchor=get_anchor()).pack(anchor=get_anchor(), pady=(8, 0))
            ctk.CTkLabel(inner, text=desc, font=T.small(), text_color=T.TEXT_MUTED, anchor=get_anchor()).pack(anchor=get_anchor())

            ctk.CTkLabel(t_row, text=value, font=T.font(14, "bold"), text_color=color, width=60, anchor="center").pack(side=get_end(), padx=14)

        ctk.CTkLabel(
            qa_body,
            text=_("qa_config_note"),
            font=T.small(), text_color=T.TEXT_MUTED,
            wraplength=560, justify=get_start(), anchor=get_anchor(),
        ).pack(anchor=get_anchor(), pady=(8, 0))

        return outer

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

        self._config.FORM_WIDTH         = _int("form_width",     self._config.FORM_WIDTH)
        self._config.FORM_HEIGHT        = _int("form_height",    self._config.FORM_HEIGHT)
        self._config.ROW_COUNT          = _int("rows",           self._config.ROW_COUNT)
        self._config.COLUMN_COUNT       = _int("columns",        self._config.COLUMN_COUNT)
        self._config.CHECKBOX_THRESHOLD = _float("threshold",    self._config.CHECKBOX_THRESHOLD)
        self._config.SCORE_YES          = _int("score_yes",      self._config.SCORE_YES)
        self._config.SCORE_SOMEWHAT     = _int("score_somewhat", self._config.SCORE_SOMEWHAT)
        self._config.SCORE_NO           = _int("score_no",       self._config.SCORE_NO)

        ctk.set_appearance_mode(self.appear_var.get())

        selected_label = self.lang_var.get()
        new_lang = self._label_to_code.get(selected_label, selected_label)
        if new_lang != I18n.get_language():
            I18n.set_language(new_lang)

        if self._persistence:
            self._config.save_to_persistence(self._persistence)
            self._persistence.set_setting("university_name", self.uni_name_entry.get())
            if self._logo_path:
                self._persistence.set_setting("logo_path", self._logo_path)

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
            self.logo_lbl.configure(
                text="  " + os.path.basename(path),
                text_color=T.TEXT_PRIMARY,
                image=IC.icon("check", size=18, color="#00C896"),
            )

    def _save_branding(self) -> None:
        if not self._persistence:
            return
        self._persistence.set_setting("university_name", self.uni_name_entry.get())
        if self._logo_path:
            self._persistence.set_setting("logo_path", self._logo_path)
        messagebox.showinfo(rtl_text(_("university_branding")), rtl_text(_("branding_saved")))

    def _save_coords(self) -> None:
        if not self._persistence:
            return
        raw = self.pdf_coords_box.get("1.0", "end").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror(rtl_text(_("pdf_coords")), rtl_text(f"{_('invalid_json')}\n{exc}"))
            return
        self._persistence.set_setting("pdf_coords", parsed)
        messagebox.showinfo(rtl_text(_("pdf_coords")), rtl_text(_("settings_saved")))

    def _save_questions(self) -> None:
        if not self._persistence:
            return
        texts = [e.get() for e in self._q_entries]
        self._persistence.set_setting("question_texts", texts)
        messagebox.showinfo(rtl_text(_("survey_questions")), rtl_text(_("questions_saved")))
