"""Design tokens extracted from the Asan Hesab dark-navy palette.

Every colour is a (light_hex, dark_hex) tuple for CustomTkinter.
The dark values are the primary target; light values are reasonable
fallbacks if the user switches to light mode.

Palette reference (from screenshot):
  Page bg        #141C2E   deep navy
  Sidebar bg     #1A2035   slightly lighter navy
  Card bg        #1E2A42   card surface
  Card raised    #243352   hover / inner card
  Border         #2A3A5C   subtle divider
  Accent blue    #4A9EFF   active nav, primary buttons
  Accent hover   #2E7FE8
  Green          #00C896   positive / analyzed
  Amber          #F5A623   warning / draft
  Red            #FF4D6A   danger / negative
  Text primary   #E8EDF5
  Text secondary #8B9BB4
  Text muted     #4A5A7A
"""

from __future__ import annotations

import customtkinter as ctk

# ---------------------------------------------------------------------------
# Raw hex values (dark side of the palette)
# ---------------------------------------------------------------------------

_D_PAGE        = "#0F0F13"
_D_SIDEBAR     = "#0F0F13"
_D_CARD        = "#1A1A21"
_D_CARD_RAISED = "#22222A"
_D_BORDER      = "#2A2A35"
_D_BORDER_SUB  = "#1A1A21"

_D_ACCENT      = "#B49DF8"
_D_ACCENT_HOV  = "#A086EB"
_D_ACCENT_SUB  = "#1A1528"

_D_GREEN       = "#00D287"
_D_GREEN_BG    = "#0A281E"
_D_AMBER       = "#F5A623"
_D_AMBER_BG    = "#2A1A00"
_D_RED         = "#FF4D6A"
_D_RED_BG      = "#2A0A10"
_D_BLUE        = "#4A9EFF"
_D_BLUE_BG     = "#0D1E38"
_D_PURPLE      = "#B49DF8"
_D_PURPLE_BG   = "#1A1528"

_D_TEXT1       = "#FFFFFF"
_D_TEXT2       = "#A0A0AB"
_D_TEXT3       = "#6B6B78"

# Light-mode fallbacks (clean white/slate)
_L_PAGE        = "#F0F4FA"
_L_SIDEBAR     = "#1A2035"   # sidebar stays dark in both modes
_L_CARD        = "#FFFFFF"
_L_CARD_RAISED = "#F8FAFC"
_L_BORDER      = "#DDE3EE"

_L_ACCENT      = "#2563EB"
_L_ACCENT_HOV  = "#1D4ED8"
_L_ACCENT_SUB  = "#EFF6FF"

_L_GREEN       = "#059669"
_L_GREEN_BG    = "#ECFDF5"
_L_AMBER       = "#D97706"
_L_AMBER_BG    = "#FFFBEB"
_L_RED         = "#DC2626"
_L_RED_BG      = "#FEF2F2"
_L_BLUE        = "#2563EB"
_L_BLUE_BG     = "#EFF6FF"

_L_TEXT1       = "#0F172A"
_L_TEXT2       = "#475569"
_L_TEXT3       = "#94A3B8"

# ---------------------------------------------------------------------------
# Public colour tokens  (light, dark)
# ---------------------------------------------------------------------------

# -- Brand / accent ----
ACCENT              = (_L_ACCENT,     _D_ACCENT)
ACCENT_HOVER        = (_L_ACCENT_HOV, _D_ACCENT_HOV)
ACCENT_SUBTLE       = (_L_ACCENT_SUB, _D_ACCENT_SUB)

# -- Sidebar ----
SIDEBAR_BG          = (_L_SIDEBAR,    _D_SIDEBAR)
SIDEBAR_ACTIVE_BG   = (_L_CARD,       _D_CARD)        # row highlight
SIDEBAR_ACTIVE_PILL = (_L_ACCENT,     _D_ACCENT)      # left pill
SIDEBAR_HOVER_BG    = (_L_CARD,       _D_CARD)
SIDEBAR_TEXT        = (_L_TEXT2,      _D_TEXT2)
SIDEBAR_TEXT_ACTIVE = ("#FFFFFF",     "#FFFFFF")
SIDEBAR_BORDER      = (_L_BORDER,     _D_BORDER_SUB)

# -- Page / surface ----
PAGE_BG             = (_L_PAGE,        _D_PAGE)
SURFACE             = (_L_CARD,        _D_CARD)
SURFACE_RAISED      = (_L_CARD_RAISED, _D_CARD_RAISED)
SURFACE_OVERLAY     = (_L_CARD_RAISED, _D_CARD_RAISED)
CARD_BORDER         = (_L_BORDER,      _D_BORDER)

# -- Text ----
TEXT_PRIMARY        = (_L_TEXT1, _D_TEXT1)
TEXT_SECONDARY      = (_L_TEXT2, _D_TEXT2)
TEXT_MUTED          = (_L_TEXT3, _D_TEXT3)

# -- Status ----
STATUS_DRAFT            = (_L_AMBER,  _D_AMBER)
STATUS_DRAFT_BG         = (_L_AMBER_BG, _D_AMBER_BG)
STATUS_DRAFT_STRIPE     = (_L_AMBER,  _D_AMBER)

STATUS_PROCESSED        = (_L_ACCENT, _D_PURPLE)
STATUS_PROCESSED_BG     = (_L_ACCENT_SUB, _D_PURPLE_BG)
STATUS_PROCESSED_STRIPE = (_L_ACCENT, _D_PURPLE)

STATUS_ANALYZED         = (_L_GREEN,  _D_GREEN)
STATUS_ANALYZED_BG      = (_L_GREEN_BG, _D_GREEN_BG)
STATUS_ANALYZED_STRIPE  = (_L_GREEN,  _D_GREEN)

# -- Semantic ----
SUCCESS             = (_L_GREEN, _D_GREEN)
WARNING             = (_L_AMBER, _D_AMBER)
ERROR               = (_L_RED,   _D_RED)
INFO                = (_L_BLUE,  _D_BLUE)

# -- Danger ----
DANGER              = (_L_RED,    _D_RED)
DANGER_HOVER        = ("#B91C1C", "#E0304A")
DANGER_SUBTLE       = (_L_RED_BG, _D_RED_BG)

# -- Ghost / outline ----
GHOST_BG            = "transparent"
GHOST_HOVER         = (_L_CARD_RAISED, _D_CARD_RAISED)
GHOST_TEXT          = (_L_TEXT2,       _D_TEXT2)
GHOST_BORDER        = (_L_BORDER,      _D_BORDER)

# -- Input ----
INPUT_BG            = (_L_CARD,   _D_CARD_RAISED)
INPUT_BORDER        = (_L_BORDER, _D_BORDER)
INPUT_BORDER_FOCUS  = (_L_ACCENT, _D_ACCENT)

# -- Chip / tag ----
CHIP_BG             = (_L_CARD_RAISED, _D_CARD_RAISED)
CHIP_TEXT           = (_L_TEXT2,       _D_TEXT2)

# -- KPI card tints ----
KPI_TOTAL_BG        = (_L_BLUE_BG,  _D_BLUE_BG)
KPI_TOTAL_NUM       = (_L_BLUE,     _D_BLUE)
KPI_DRAFT_BG        = (_L_AMBER_BG, _D_AMBER_BG)
KPI_DRAFT_NUM       = (_L_AMBER,    _D_AMBER)
KPI_PROC_BG         = (_L_ACCENT_SUB, _D_PURPLE_BG)
KPI_PROC_NUM        = (_L_ACCENT,   _D_PURPLE)
KPI_ANA_BG          = (_L_GREEN_BG, _D_GREEN_BG)
KPI_ANA_NUM         = (_L_GREEN,    _D_GREEN)

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

RADIUS_XS   = 4
RADIUS_SM   = 8
RADIUS_MD   = 12
RADIUS_LG   = 16
RADIUS_XL   = 22

SIDEBAR_WIDTH   = 220
PAGE_PADDING    = 24
CARD_PADDING    = 20

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

def font(size: int = 13, weight: str = "normal", family: str | None = None) -> ctk.CTkFont:
    """Create a font with RTL support."""
    # Use Segoe UI for RTL languages (supports Arabic/Dari/Pashto well on Windows)
    # Fall back to system default if family is explicitly specified
    if family is None:
        from i18n import is_rtl
        if is_rtl():
            family = "Segoe UI"  # Excellent RTL support on Windows
    
    kw: dict = {"size": size, "weight": weight}
    if family:
        kw["family"] = family
    return ctk.CTkFont(**kw)

def h1()    -> ctk.CTkFont: return font(26, "bold")
def h2()    -> ctk.CTkFont: return font(20, "bold")
def h3()    -> ctk.CTkFont: return font(15, "bold")
def h4()    -> ctk.CTkFont: return font(13, "bold")
def body()  -> ctk.CTkFont: return font(13)
def small() -> ctk.CTkFont: return font(11)
def tiny()  -> ctk.CTkFont: return font(10)
def mono()  -> ctk.CTkFont: return font(11, family="Courier New")

# ---------------------------------------------------------------------------
# Widget factories
# ---------------------------------------------------------------------------

def card(parent, **kw) -> ctk.CTkFrame:
    """Standard card — matches the screenshot's #1E2A42 surface."""
    defaults = dict(
        corner_radius=RADIUS_LG,
        fg_color=SURFACE,
        border_width=0,          # borderless like the reference UI
    )
    defaults.update(kw)
    return ctk.CTkFrame(parent, **defaults)


def inner_card(parent, **kw) -> ctk.CTkFrame:
    """Slightly raised inner card."""
    defaults = dict(
        corner_radius=RADIUS_MD,
        fg_color=SURFACE_RAISED,
        border_width=0,
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


# -- Labels ----

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


# -- Buttons ----

def primary_btn(parent, text: str, **kw) -> ctk.CTkButton:
    defaults = dict(
        text=text,
        font=font(14, "bold"),
        height=44,
        corner_radius=RADIUS_MD,
        fg_color=ACCENT,
        hover_color=ACCENT_HOVER,
        text_color=("#000000", "#000000"), # Black text on light purple background
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


# -- Inputs ----

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


# -- Status chips ----

_STATUS_META = {
    "Draft":     (STATUS_DRAFT,     STATUS_DRAFT_BG,     "-"),
    "Processed": (STATUS_PROCESSED, STATUS_PROCESSED_BG, "-"),
    "Analyzed":  (STATUS_ANALYZED,  STATUS_ANALYZED_BG,  "-"),
}

_STATUS_STRIPE = {
    "Draft":     STATUS_DRAFT_STRIPE,
    "Processed": STATUS_PROCESSED_STRIPE,
    "Analyzed":  STATUS_ANALYZED_STRIPE,
}


def status_chip(parent, status: str) -> ctk.CTkFrame:
    text_color, bg_color, icon = _STATUS_META.get(
        status, (TEXT_MUTED, CHIP_BG, "-")
    )
    chip = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=RADIUS_SM)
    ctk.CTkLabel(
        chip,
        text=f"{icon}  {status}",
        font=font(11, "bold"),
        text_color=text_color,
    ).pack(padx=10, pady=4)
    return chip


def tag_chip(parent, text: str, **kw) -> ctk.CTkFrame:
    chip = ctk.CTkFrame(parent, fg_color=CHIP_BG, corner_radius=RADIUS_SM, **kw)
    ctk.CTkLabel(chip, text=text, font=small(), text_color=CHIP_TEXT).pack(padx=8, pady=3)
    return chip


def status_stripe_color(status: str) -> tuple:
    return _STATUS_STRIPE.get(status, TEXT_MUTED)


# -- KPI stat card ----

def stat_card(
    parent,
    label: str,
    value: str,
    icon_name: str = "",
    num_color=None,
    bg_color=None,
    is_active: bool = False,
) -> ctk.CTkFrame:
    """Tinted KPI card matching the new UI design."""
    import icons as IC  # local import to avoid circular at module load

    c = ctk.CTkFrame(
        parent,
        corner_radius=RADIUS_LG,
        fg_color=SURFACE, # All cards have surface background
        border_width=0,
    )
    
    # Active indicator stripe
    if is_active:
        stripe = ctk.CTkFrame(c, width=4, corner_radius=0, fg_color=num_color)
        stripe.pack(side="left", fill="y")
        stripe.pack_propagate(False)

    inner = transparent(c)
    inner.pack(padx=CARD_PADDING, pady=CARD_PADDING, fill="both", expand=True)

    top_row = transparent(inner)
    top_row.pack(fill="x")

    # Label (Top Left)
    ctk.CTkLabel(
        top_row,
        text=label,
        font=body(),
        text_color=TEXT_SECONDARY,
    ).pack(side="left", anchor="n")

    # Icon badge (Top Right)
    if icon_name:
        badge = ctk.CTkFrame(
            top_row, width=32, height=32,
            corner_radius=RADIUS_SM, fg_color=bg_color or ACCENT,
        )
        badge.pack(side="right", anchor="n")
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge,
            image=IC.icon(icon_name, size=16, color=num_color[1] if isinstance(num_color, tuple) else num_color),
            text="",
        ).place(relx=0.5, rely=0.5, anchor="center")

    # Big number (Bottom Left)
    ctk.CTkLabel(
        inner,
        text=value,
        font=font(30, "bold"),
        text_color=TEXT_PRIMARY,
    ).pack(anchor="w", pady=(8, 0))

    return c
