"""Centralized design tokens and widget factories for the OMR Scanner UI.

Import this module everywhere instead of hard-coding colours, radii, or fonts.
All colour tuples are (light_mode_hex, dark_mode_hex) for CustomTkinter.
"""

from __future__ import annotations

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

# Brand / accent
ACCENT              = ("#2563EB", "#3B82F6")
ACCENT_HOVER        = ("#1D4ED8", "#2563EB")
ACCENT_SUBTLE       = ("#EFF6FF", "#1E3A5F")

# Sidebar (always dark regardless of app theme)
SIDEBAR_BG          = ("#1E293B", "#0F172A")
SIDEBAR_ACTIVE_BG   = ("#2563EB", "#2563EB")
SIDEBAR_HOVER_BG    = ("#334155", "#1E293B")
SIDEBAR_TEXT        = ("#94A3B8", "#64748B")
SIDEBAR_TEXT_ACTIVE = ("#FFFFFF", "#FFFFFF")
SIDEBAR_BORDER      = ("#334155", "#1E293B")

# Page surface
PAGE_BG             = ("#F1F5F9", "#0F172A")
SURFACE             = ("#FFFFFF", "#1E293B")
SURFACE_RAISED      = ("#F8FAFC", "#162032")
CARD_BORDER         = ("#E2E8F0", "#334155")

# Text
TEXT_PRIMARY        = ("#0F172A", "#F1F5F9")
TEXT_SECONDARY      = ("#475569", "#94A3B8")
TEXT_MUTED          = ("#94A3B8", "#475569")

# Status colours
STATUS_DRAFT        = ("#D97706", "#F59E0B")
STATUS_DRAFT_BG     = ("#FFFBEB", "#2D2006")
STATUS_PROCESSED    = ("#2563EB", "#60A5FA")
STATUS_PROCESSED_BG = ("#EFF6FF", "#0C1A3A")
STATUS_ANALYZED     = ("#059669", "#34D399")
STATUS_ANALYZED_BG  = ("#ECFDF5", "#052E1C")

# Semantic
SUCCESS             = ("#059669", "#34D399")
WARNING             = ("#D97706", "#FBBF24")
ERROR               = ("#DC2626", "#F87171")
INFO                = ("#2563EB", "#60A5FA")

# Danger button
DANGER              = ("#DC2626", "#EF4444")
DANGER_HOVER        = ("#B91C1C", "#DC2626")

# Ghost / outline button
GHOST_BG            = "transparent"
GHOST_HOVER         = ("#F1F5F9", "#1E293B")
GHOST_TEXT          = ("#475569", "#94A3B8")
GHOST_BORDER        = ("#CBD5E1", "#334155")

# Input
INPUT_BG            = ("#FFFFFF", "#1E293B")
INPUT_BORDER        = ("#CBD5E1", "#334155")
INPUT_BORDER_FOCUS  = ("#2563EB", "#3B82F6")

# Chip / tag
CHIP_BG             = ("#F1F5F9", "#1E293B")
CHIP_TEXT           = ("#475569", "#94A3B8")

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

RADIUS_XS   = 4
RADIUS_SM   = 6
RADIUS_MD   = 10
RADIUS_LG   = 14
RADIUS_XL   = 20

SIDEBAR_WIDTH   = 230
PAGE_PADDING    = 28
CARD_PADDING    = 20

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

def font(size: int = 13, weight: str = "normal", family: str | None = None) -> ctk.CTkFont:
    kw: dict = {"size": size, "weight": weight}
    if family:
        kw["family"] = family
    return ctk.CTkFont(**kw)

def h1()    -> ctk.CTkFont: return font(28, "bold")
def h2()    -> ctk.CTkFont: return font(22, "bold")
def h3()    -> ctk.CTkFont: return font(17, "bold")
def h4()    -> ctk.CTkFont: return font(14, "bold")
def body()  -> ctk.CTkFont: return font(13)
def small() -> ctk.CTkFont: return font(11)
def tiny()  -> ctk.CTkFont: return font(10)
def mono()  -> ctk.CTkFont: return font(11, family="Courier New")

# ---------------------------------------------------------------------------
# Widget factories
# ---------------------------------------------------------------------------

def page_frame(parent, **kw) -> ctk.CTkFrame:
    """Full-bleed page background."""
    defaults = dict(fg_color=PAGE_BG, corner_radius=0)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def card(parent, **kw) -> ctk.CTkFrame:
    """Elevated card with border."""
    defaults = dict(
        corner_radius=RADIUS_LG,
        fg_color=SURFACE,
        border_width=1,
        border_color=CARD_BORDER,
    )
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def inner_card(parent, **kw) -> ctk.CTkFrame:
    """Slightly raised inner card (for nested sections)."""
    defaults = dict(
        corner_radius=RADIUS_MD,
        fg_color=SURFACE_RAISED,
        border_width=1,
        border_color=CARD_BORDER,
    )
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def transparent(parent, **kw) -> ctk.CTkFrame:
    defaults = dict(fg_color="transparent")
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def divider(parent, **kw) -> ctk.CTkFrame:
    defaults = dict(height=1, fg_color=CARD_BORDER)
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


# --- Labels -----------------------------------------------------------------

def page_title(parent, text: str, **kw) -> ctk.CTkLabel:
    defaults = dict(text=text, font=h2(), text_color=TEXT_PRIMARY, anchor="w")
    defaults.update(kw)
    return ctk.CTkLabel(parent, **defaults)


def section_title(parent, text: str, **kw) -> ctk.CTkLabel:
    defaults = dict(text=text, font=h4(), text_color=TEXT_PRIMARY, anchor="w")
    defaults.update(kw)
    return ctk.CTkLabel(parent, **defaults)


def body_label(parent, text: str, **kw) -> ctk.CTkLabel:
    defaults = dict(text=text, font=body(), text_color=TEXT_PRIMARY)
    defaults.update(kw)
    return ctk.CTkLabel(parent, **defaults)


def muted_label(parent, text: str, **kw) -> ctk.CTkLabel:
    defaults = dict(text=text, font=small(), text_color=TEXT_SECONDARY)
    defaults.update(kw)
    return ctk.CTkLabel(parent, **defaults)


# --- Buttons ----------------------------------------------------------------

def primary_btn(parent, text: str, **kw) -> ctk.CTkButton:
    defaults = dict(
        text=text,
        font=font(13, "bold"),
        height=40,
        corner_radius=RADIUS_MD,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        text_color=("#FFFFFF", "#FFFFFF"),
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


def secondary_btn(parent, text: str, **kw) -> ctk.CTkButton:
    defaults = dict(
        text=text,
        font=body(),
        height=40,
        corner_radius=RADIUS_MD,
        fg_color=GHOST_BG,
        hover_color=GHOST_HOVER,
        text_color=GHOST_TEXT,
        border_width=1,
        border_color=GHOST_BORDER,
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


def danger_btn(parent, text: str, **kw) -> ctk.CTkButton:
    defaults = dict(
        text=text,
        font=body(),
        height=40,
        corner_radius=RADIUS_MD,
        fg_color=DANGER,
        hover_color=DANGER_HOVER,
        text_color=("#FFFFFF", "#FFFFFF"),
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


def icon_btn(parent, text: str, **kw) -> ctk.CTkButton:
    """Small square icon button."""
    defaults = dict(
        text=text,
        font=body(),
        width=36,
        height=36,
        corner_radius=RADIUS_SM,
        fg_color=GHOST_BG,
        hover_color=GHOST_HOVER,
        text_color=GHOST_TEXT,
    )
    defaults.update(kw)
    return ctk.CTkButton(parent, **defaults)


# --- Inputs -----------------------------------------------------------------

def text_input(parent, **kw) -> ctk.CTkEntry:
    defaults = dict(
        height=42,
        corner_radius=RADIUS_MD,
        fg_color=INPUT_BG,
        border_color=INPUT_BORDER,
        border_width=1,
        font=body(),
    )
    defaults.update(kw)
    return ctk.CTkEntry(parent, **defaults)


# --- Status chips -----------------------------------------------------------

_STATUS_COLORS = {
    "Draft":     (STATUS_DRAFT,     STATUS_DRAFT_BG),
    "Processed": (STATUS_PROCESSED, STATUS_PROCESSED_BG),
    "Analyzed":  (STATUS_ANALYZED,  STATUS_ANALYZED_BG),
}

_STATUS_ICONS = {
    "Draft":     "◐",
    "Processed": "◑",
    "Analyzed":  "●",
}


def status_chip(parent, status: str) -> ctk.CTkFrame:
    """Coloured pill showing survey status."""
    text_color, bg_color = _STATUS_COLORS.get(
        status, (TEXT_MUTED, CHIP_BG)
    )
    icon = _STATUS_ICONS.get(status, "○")
    chip = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=RADIUS_SM)
    ctk.CTkLabel(
        chip,
        text=f"{icon}  {status}",
        font=font(11, "bold"),
        text_color=text_color,
    ).pack(padx=10, pady=4)
    return chip


def tag_chip(parent, text: str, **kw) -> ctk.CTkFrame:
    """Neutral metadata tag chip."""
    chip = ctk.CTkFrame(parent, fg_color=CHIP_BG, corner_radius=RADIUS_SM, **kw)
    ctk.CTkLabel(chip, text=text, font=small(), text_color=CHIP_TEXT).pack(padx=8, pady=3)
    return chip


# --- Stat card (for dashboard summary row) ----------------------------------

def stat_card(parent, label: str, value: str, icon: str = "", color=None) -> ctk.CTkFrame:
    """A small KPI card showing a metric."""
    c = card(parent)
    inner = transparent(c)
    inner.pack(padx=CARD_PADDING, pady=CARD_PADDING, fill="both", expand=True)

    if icon:
        ctk.CTkLabel(inner, text=icon, font=font(22), text_color=color or ACCENT).pack(anchor="w")

    ctk.CTkLabel(
        inner,
        text=value,
        font=font(26, "bold"),
        text_color=color or TEXT_PRIMARY,
    ).pack(anchor="w", pady=(4, 0))

    ctk.CTkLabel(
        inner,
        text=label,
        font=small(),
        text_color=TEXT_SECONDARY,
    ).pack(anchor="w")

    return c
