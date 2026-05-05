"""Tabler Icons wrapper for CustomTkinter.

Uses pytablericons library to load high-quality SVG icons from the Tabler Icons set.
Provides the same API as the previous custom icon implementation for compatibility.

Usage
-----
    from icons import icon, icon_label, icon_button

    img = icon("dashboard", size=20, color="#4A9EFF")   # CTkImage
    lbl = icon_label(parent, "search", size=16)          # CTkLabel with image
    btn = icon_button(parent, "plus", text="New", ...)   # CTkButton with image

Icon names
----------
Use any name from _ICON_MAP below, or pass a raw Tabler icon name directly
(e.g. "brand-github").  Tabler icon names are converted to OutlineIcon enum
members by uppercasing and replacing hyphens with underscores.
"""

from __future__ import annotations

import customtkinter as ctk
from pytablericons import TablerIcons, OutlineIcon
from PIL import Image

# ---------------------------------------------------------------------------
# PIL image cache (Tk-independent -- safe across multiple CTk() instances)
# ---------------------------------------------------------------------------
# We cache the rendered Pillow Image objects (keyed by name+size+color).
# CTkImage wrappers are created fresh each call because they hold a reference
# to the current Tk interpreter and become invalid when the root is destroyed.

_PIL_CACHE: dict[tuple, Image.Image] = {}

# ---------------------------------------------------------------------------
# Icon name mapping  (app-specific aliases -> Tabler icon names)
# ---------------------------------------------------------------------------
# Tabler icon names use lowercase-hyphenated format, which maps to
# OutlineIcon enum members as:  "layout-dashboard" -> OutlineIcon.LAYOUT_DASHBOARD
_ICON_MAP: dict[str, str] = {
    # Navigation
    "dashboard":   "layout-dashboard",
    "plus":        "plus",
    "scan":        "scan",
    "chart":       "chart-bar",
    "settings":    "settings",
    "back":        "chevron-left",
    "arrow_left":  "arrow-left",
    "arrow_right": "arrow-right",

    # Actions
    "save":        "device-floppy",
    "print_icon":  "printer",
    "trash":       "trash",
    "edit":        "edit",
    "check":       "check",
    "eye":         "eye",
    "refresh":     "refresh",

    # Status
    "warning":     "alert-triangle",
    "error":       "alert-circle",
    "info":        "info-circle",
    "success":     "circle-check",

    # Data / content
    "search":      "search",
    "folder":      "folder",
    "upload":      "upload",
    "download":    "download",
    "file_text":   "file-text",
    "user":        "user",
    "calendar":    "calendar",
    "building":    "building",
    "book":        "book",
    "filter":      "filter",
    "sort":        "sort-ascending",
    "clock":       "clock",
    "bar_chart":   "chart-bar",
    "pie_chart":   "chart-pie",
    "trending_up": "trending-up",
    "layers":      "layers-linked",
    "cpu":         "cpu",
    "globe":       "world",

    # App-specific
    "omr":         "checkbox",
}


def _tabler_name_to_enum(tabler_name: str) -> OutlineIcon | None:
    """Convert a Tabler icon name string to its OutlineIcon enum member.

    "layout-dashboard"  ->  OutlineIcon.LAYOUT_DASHBOARD
    Returns None if the name is not found in the enum.
    """
    enum_key = tabler_name.upper().replace("-", "_")
    return getattr(OutlineIcon, enum_key, None)


def _render_icon(name: str, size: int, color: str) -> Image.Image:
    """Resolve *name* to a Tabler icon and render it as a Pillow RGBA image."""
    # Resolve alias -> tabler name, or use the name directly
    tabler_name = _ICON_MAP.get(name, name)
    enum_member = _tabler_name_to_enum(tabler_name)

    if enum_member is not None:
        try:
            return TablerIcons.load(enum_member, size=size, color=color)
        except Exception:
            pass  # fall through to fallback

    # Fallback: simple circle outline so the UI never breaks
    return _fallback_icon(size, color)


def _fallback_icon(size: int, color: str) -> Image.Image:
    """Simple circle placeholder for unknown icon names."""
    from PIL import ImageDraw
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    hex_str = color.lstrip("#")
    try:
        r, g, b = int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16)
    except ValueError:
        r, g, b = 255, 255, 255
    m = size / 2
    rad = size * 0.35
    lw = max(1, round(size / 12))
    d.ellipse([m - rad, m - rad, m + rad, m + rad], outline=(r, g, b, 255), width=lw)
    return img


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def icon(
    name: str,
    size: int = 18,
    color: str = "#FFFFFF",
) -> ctk.CTkImage:
    """Return a CTkImage for the named icon.

    The underlying Pillow bitmap is cached by (name, size, color) so rendering
    only happens once per unique combination.  A fresh CTkImage wrapper is
    returned each call so it is always bound to the current Tk interpreter.

    Parameters
    ----------
    name:   icon alias (see _ICON_MAP) or any Tabler icon name, e.g. "brand-github"
    size:   pixel size (same for width and height)
    color:  hex colour string, e.g. "#4A9EFF"
    """
    cache_key = (name, size, color)
    pil_img = _PIL_CACHE.get(cache_key)

    if pil_img is None:
        pil_img = _render_icon(name, size, color)
        _PIL_CACHE[cache_key] = pil_img

    # Always create a fresh CTkImage wrapper (cheap, Tk-safe)
    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))


def icon_label(
    parent,
    name: str,
    size: int = 18,
    color: str = "#8B9BB4",
    **kw,
) -> ctk.CTkLabel:
    """A CTkLabel that shows only an icon image."""
    img = icon(name, size, color)
    return ctk.CTkLabel(parent, image=img, text="", **kw)


def icon_button(
    parent,
    name: str,
    text: str = "",
    size: int = 16,
    color: str = "#FFFFFF",
    compound: str = "left",
    **kw,
) -> ctk.CTkButton:
    """A CTkButton with a Tabler icon on the left (or right)."""
    img = icon(name, size, color)
    return ctk.CTkButton(parent, image=img, text=text, compound=compound, **kw)
