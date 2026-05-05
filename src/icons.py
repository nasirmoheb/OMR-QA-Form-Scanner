"""Lucide-style icon renderer using Pillow + CTkImage.

All icons are drawn as crisp RGBA bitmaps at the requested size.
No external DLLs, no SVG renderer required - pure Pillow ImageDraw.

Usage
-----
    from icons import icon, icon_label, icon_button

    img = icon("dashboard", size=20, color="#4A9EFF")   # CTkImage
    lbl = icon_label(parent, "search", size=16)          # CTkLabel with image
    btn = icon_button(parent, "plus", text="New", ...)   # CTkButton with image

Available names
---------------
    dashboard, plus, scan, chart, settings, back, save, print_icon,
    search, folder, trash, edit, check, warning, error, info,
    user, calendar, building, book, upload, download, file_text,
    arrow_left, arrow_right, refresh, eye, filter, sort, clock,
    bar_chart, pie_chart, trending_up, layers, cpu, globe
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _hex(color: str) -> tuple[int, int, int, int]:
    c = color.lstrip("#")
    if len(c) == 6:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return r, g, b, 255
    if len(c) == 8:
        r, g, b, a = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), int(c[6:8], 16)
        return r, g, b, a
    return 255, 255, 255, 255


def _lw(size: int) -> int:
    """Stroke width scaled to icon size."""
    return max(1, round(size / 12))


# ---------------------------------------------------------------------------
# Individual icon draw functions  (each receives img, draw, size, color_rgba)
# ---------------------------------------------------------------------------

DrawFn = Callable[[Image.Image, ImageDraw.ImageDraw, int, tuple], None]
_REGISTRY: dict[str, DrawFn] = {}


def _reg(name: str):
    def decorator(fn: DrawFn) -> DrawFn:
        _REGISTRY[name] = fn
        return fn
    return decorator


# -- Navigation ----

@_reg("dashboard")
def _dashboard(img, d, s, c):
    lw = _lw(s); p = s * 0.1
    # 2x2 grid of rounded squares
    half = s * 0.42; gap = s * 0.06
    for rx in (p, half + gap):
        for ry in (p, half + gap):
            d.rounded_rectangle([rx, ry, rx + half, ry + half], radius=s*0.08, outline=c, width=lw)


@_reg("plus")
def _plus(img, d, s, c):
    lw = _lw(s); m = s / 2; arm = s * 0.35
    d.line([(m, m - arm), (m, m + arm)], fill=c, width=lw)
    d.line([(m - arm, m), (m + arm, m)], fill=c, width=lw)


@_reg("scan")
def _scan(img, d, s, c):
    lw = _lw(s); p = s * 0.12; cr = s * 0.12
    # Corner brackets
    for x0, y0, x1, y1 in [(p, p, p+cr, p), (p, p, p, p+cr),
                             (s-p-cr, p, s-p, p), (s-p, p, s-p, p+cr),
                             (p, s-p-cr, p, s-p), (p, s-p, p+cr, s-p),
                             (s-p-cr, s-p, s-p, s-p), (s-p, s-p-cr, s-p, s-p)]:
        d.line([(x0, y0), (x1, y1)], fill=c, width=lw)
    # Horizontal scan line
    d.line([(p + cr, s/2), (s - p - cr, s/2)], fill=c, width=lw)


@_reg("chart")
def _chart(img, d, s, c):
    lw = _lw(s); p = s * 0.1
    # Three vertical bars
    bw = (s - 2*p) / 5
    heights = [0.6, 0.85, 0.45]
    for i, h in enumerate(heights):
        x0 = p + i * (bw + bw * 0.3)
        y0 = s - p - h * (s - 2*p)
        d.rounded_rectangle([x0, y0, x0 + bw, s - p], radius=lw, outline=c, width=lw)


@_reg("settings")
def _settings(img, d, s, c):
    lw = _lw(s); m = s / 2; r_outer = s * 0.38; r_inner = s * 0.18
    # Gear: outer circle with teeth
    teeth = 8
    for i in range(teeth):
        angle = math.radians(i * 360 / teeth)
        x1 = m + r_outer * math.cos(angle)
        y1 = m + r_outer * math.sin(angle)
        x2 = m + (r_outer + s*0.08) * math.cos(angle)
        y2 = m + (r_outer + s*0.08) * math.sin(angle)
        d.line([(x1, y1), (x2, y2)], fill=c, width=lw+1)
    d.ellipse([m - r_outer, m - r_outer, m + r_outer, m + r_outer], outline=c, width=lw)
    d.ellipse([m - r_inner, m - r_inner, m + r_inner, m + r_inner], outline=c, width=lw)


@_reg("back")
def _back(img, d, s, c):
    lw = _lw(s); m = s / 2; arm = s * 0.28
    # Left-pointing chevron
    d.line([(m + arm, m - arm), (m - arm, m), (m + arm, m + arm)], fill=c, width=lw)


@_reg("arrow_left")
def _arrow_left(img, d, s, c):
    lw = _lw(s); m = s / 2; arm = s * 0.3
    d.line([(m + arm, m - arm), (m - arm, m), (m + arm, m + arm)], fill=c, width=lw)
    d.line([(m - arm, m), (m + arm * 1.2, m)], fill=c, width=lw)


@_reg("arrow_right")
def _arrow_right(img, d, s, c):
    lw = _lw(s); m = s / 2; arm = s * 0.3
    d.line([(m - arm, m - arm), (m + arm, m), (m - arm, m + arm)], fill=c, width=lw)
    d.line([(m + arm, m), (m - arm * 1.2, m)], fill=c, width=lw)


# -- Actions ----

@_reg("save")
def _save(img, d, s, c):
    lw = _lw(s); p = s * 0.12
    # Floppy disk outline
    d.rounded_rectangle([p, p, s-p, s-p], radius=s*0.08, outline=c, width=lw)
    # Top notch
    d.rectangle([p + s*0.25, p, s - p - s*0.1, p + s*0.28], outline=c, width=lw)
    # Bottom data area
    d.rounded_rectangle([p + s*0.15, s*0.55, s-p-s*0.15, s-p-s*0.05], radius=s*0.04, outline=c, width=lw)


@_reg("print_icon")
def _print_icon(img, d, s, c):
    lw = _lw(s); p = s * 0.12
    # Paper tray
    d.rounded_rectangle([p, s*0.35, s-p, s*0.72], radius=s*0.06, outline=c, width=lw)
    # Paper top
    d.rectangle([p + s*0.18, p, s - p - s*0.18, s*0.38], outline=c, width=lw)
    # Paper output
    d.rectangle([p + s*0.18, s*0.62, s - p - s*0.18, s - p], outline=c, width=lw)
    # Dot
    d.ellipse([s*0.62, s*0.46, s*0.72, s*0.56], fill=c)


@_reg("trash")
def _trash(img, d, s, c):
    lw = _lw(s); p = s * 0.15
    # Bin body
    d.rounded_rectangle([p, s*0.28, s-p, s-p], radius=s*0.06, outline=c, width=lw)
    # Lid
    d.line([(p - s*0.05, s*0.25), (s - p + s*0.05, s*0.25)], fill=c, width=lw)
    # Handle
    d.rounded_rectangle([s*0.35, p, s*0.65, s*0.26], radius=s*0.04, outline=c, width=lw)
    # Lines inside
    for x in [s*0.35, s*0.5, s*0.65]:
        d.line([(x, s*0.38), (x, s - p - s*0.05)], fill=c, width=lw)


@_reg("edit")
def _edit(img, d, s, c):
    lw = _lw(s); p = s * 0.12
    # Pencil body
    angle = math.radians(45)
    tip_x, tip_y = p, s - p
    end_x = tip_x + (s - 2*p) * math.cos(angle)
    end_y = tip_y - (s - 2*p) * math.sin(angle)
    d.line([(tip_x + s*0.08, tip_y - s*0.08), (end_x, end_y)], fill=c, width=lw)
    # Eraser end
    d.ellipse([end_x - s*0.08, end_y - s*0.08, end_x + s*0.08, end_y + s*0.08], outline=c, width=lw)


@_reg("check")
def _check(img, d, s, c):
    lw = _lw(s) + 1; p = s * 0.15
    d.line([(p, s*0.5), (s*0.42, s - p), (s - p, p)], fill=c, width=lw)


@_reg("eye")
def _eye(img, d, s, c):
    lw = _lw(s); m = s / 2; p = s * 0.12
    # Eye outline
    d.arc([p, s*0.3, s-p, s*0.7], start=0, end=180, fill=c, width=lw)
    d.arc([p, s*0.3, s-p, s*0.7], start=180, end=360, fill=c, width=lw)
    # Pupil
    r = s * 0.1
    d.ellipse([m-r, m-r, m+r, m+r], outline=c, width=lw)


@_reg("refresh")
def _refresh(img, d, s, c):
    lw = _lw(s); m = s/2; r = s*0.35; p = s*0.12
    d.arc([m-r, m-r, m+r, m+r], start=40, end=320, fill=c, width=lw)
    # Arrow head
    ax = m + r * math.cos(math.radians(40))
    ay = m - r * math.sin(math.radians(40))
    d.line([(ax, ay), (ax + s*0.12, ay - s*0.12)], fill=c, width=lw)
    d.line([(ax, ay), (ax + s*0.14, ay + s*0.06)], fill=c, width=lw)


# -- Status ----

@_reg("warning")
def _warning(img, d, s, c):
    lw = _lw(s); p = s * 0.1; m = s / 2
    # Triangle
    d.polygon([(m, p), (s-p, s-p), (p, s-p)], outline=c, width=lw)
    # Exclamation
    d.line([(m, s*0.38), (m, s*0.62)], fill=c, width=lw)
    d.ellipse([m-lw, s*0.7, m+lw, s*0.7+lw*2], fill=c)


@_reg("error")
def _error(img, d, s, c):
    lw = _lw(s); p = s * 0.12
    d.ellipse([p, p, s-p, s-p], outline=c, width=lw)
    d.line([(p + s*0.15, p + s*0.15), (s - p - s*0.15, s - p - s*0.15)], fill=c, width=lw)
    d.line([(s - p - s*0.15, p + s*0.15), (p + s*0.15, s - p - s*0.15)], fill=c, width=lw)


@_reg("info")
def _info(img, d, s, c):
    lw = _lw(s); p = s * 0.12; m = s / 2
    d.ellipse([p, p, s-p, s-p], outline=c, width=lw)
    d.line([(m, s*0.45), (m, s*0.72)], fill=c, width=lw)
    d.ellipse([m-lw, s*0.28, m+lw, s*0.28+lw*2], fill=c)


@_reg("success")
def _success(img, d, s, c):
    lw = _lw(s); p = s * 0.12; m = s / 2
    d.ellipse([p, p, s-p, s-p], outline=c, width=lw)
    _check(img, d, s, c)


# -- Data / content ----

@_reg("search")
def _search(img, d, s, c):
    lw = _lw(s); r = s * 0.3; cx = s * 0.42; cy = s * 0.42
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=c, width=lw)
    d.line([(cx + r*0.7, cy + r*0.7), (s - s*0.12, s - s*0.12)], fill=c, width=lw+1)


@_reg("folder")
def _folder(img, d, s, c):
    lw = _lw(s); p = s * 0.1
    d.rounded_rectangle([p, s*0.3, s-p, s-p], radius=s*0.06, outline=c, width=lw)
    d.polygon([(p, s*0.32), (p, s*0.22), (s*0.42, s*0.22), (s*0.5, s*0.32)], outline=c, width=lw)


@_reg("upload")
def _upload(img, d, s, c):
    lw = _lw(s); m = s/2; p = s*0.15
    d.line([(m, s*0.62), (m, p)], fill=c, width=lw)
    d.line([(m - s*0.22, s*0.35), (m, p), (m + s*0.22, s*0.35)], fill=c, width=lw)
    d.line([(p, s*0.75), (p, s-p), (s-p, s-p), (s-p, s*0.75)], fill=c, width=lw)


@_reg("download")
def _download(img, d, s, c):
    lw = _lw(s); m = s/2; p = s*0.15
    d.line([(m, p), (m, s*0.62)], fill=c, width=lw)
    d.line([(m - s*0.22, s*0.45), (m, s*0.65), (m + s*0.22, s*0.45)], fill=c, width=lw)
    d.line([(p, s*0.75), (p, s-p), (s-p, s-p), (s-p, s*0.75)], fill=c, width=lw)


@_reg("file_text")
def _file_text(img, d, s, c):
    lw = _lw(s); p = s*0.12
    d.rounded_rectangle([p, p, s-p, s-p], radius=s*0.06, outline=c, width=lw)
    # Dog-ear
    fold = s * 0.28
    d.line([(s - p - fold, p), (s - p - fold, p + fold), (s - p, p + fold)], fill=c, width=lw)
    # Text lines
    for y in [s*0.52, s*0.64, s*0.76]:
        d.line([(p + s*0.15, y), (s - p - s*0.15, y)], fill=c, width=lw)


@_reg("user")
def _user(img, d, s, c):
    lw = _lw(s); m = s/2; p = s*0.12
    r_head = s * 0.2
    d.ellipse([m-r_head, p, m+r_head, p+r_head*2], outline=c, width=lw)
    d.arc([p, s*0.52, s-p, s-p+s*0.3], start=180, end=0, fill=c, width=lw)


@_reg("calendar")
def _calendar(img, d, s, c):
    lw = _lw(s); p = s*0.12
    d.rounded_rectangle([p, s*0.22, s-p, s-p], radius=s*0.06, outline=c, width=lw)
    d.line([(p, s*0.42), (s-p, s*0.42)], fill=c, width=lw)
    for x in [s*0.35, s*0.65]:
        d.line([(x, p), (x, s*0.32)], fill=c, width=lw)
    # Day dots
    for dx in [s*0.3, s*0.5, s*0.7]:
        for dy in [s*0.56, s*0.72]:
            r = lw
            d.ellipse([dx-r, dy-r, dx+r, dy+r], fill=c)


@_reg("building")
def _building(img, d, s, c):
    lw = _lw(s); p = s*0.12
    d.rectangle([p + s*0.1, p, s - p - s*0.1, s - p], outline=c, width=lw)
    # Windows
    for wx in [s*0.28, s*0.5, s*0.72]:
        for wy in [s*0.28, s*0.48]:
            r = s * 0.07
            d.rectangle([wx-r, wy-r, wx+r, wy+r], outline=c, width=lw)
    # Door
    d.rectangle([s*0.42, s*0.68, s*0.58, s-p], outline=c, width=lw)


@_reg("book")
def _book(img, d, s, c):
    lw = _lw(s); p = s*0.12; m = s/2
    d.rounded_rectangle([p, p, m - s*0.02, s-p], radius=s*0.04, outline=c, width=lw)
    d.rounded_rectangle([m + s*0.02, p, s-p, s-p], radius=s*0.04, outline=c, width=lw)
    d.line([(m, p + s*0.05), (m, s - p - s*0.05)], fill=c, width=lw)


@_reg("filter")
def _filter(img, d, s, c):
    lw = _lw(s); p = s*0.12
    d.line([(p, s*0.28), (s-p, s*0.28)], fill=c, width=lw)
    d.line([(p + s*0.15, s*0.5), (s - p - s*0.15, s*0.5)], fill=c, width=lw)
    d.line([(p + s*0.3, s*0.72), (s - p - s*0.3, s*0.72)], fill=c, width=lw)


@_reg("sort")
def _sort(img, d, s, c):
    lw = _lw(s); p = s*0.12
    d.line([(p, s*0.28), (s*0.72, s*0.28)], fill=c, width=lw)
    d.line([(p, s*0.5), (s*0.55, s*0.5)], fill=c, width=lw)
    d.line([(p, s*0.72), (s*0.38, s*0.72)], fill=c, width=lw)


@_reg("clock")
def _clock(img, d, s, c):
    lw = _lw(s); p = s*0.1; m = s/2
    d.ellipse([p, p, s-p, s-p], outline=c, width=lw)
    d.line([(m, m), (m, m - s*0.28)], fill=c, width=lw)
    d.line([(m, m), (m + s*0.2, m + s*0.1)], fill=c, width=lw)


@_reg("bar_chart")
def _bar_chart(img, d, s, c):
    lw = _lw(s); p = s*0.1
    d.line([(p, p), (p, s-p), (s-p, s-p)], fill=c, width=lw)
    bw = (s - 2*p) / 5
    for i, h in enumerate([0.5, 0.8, 0.35]):
        x0 = p + s*0.08 + i * (bw + bw*0.3)
        y0 = s - p - h * (s - 2*p)
        d.rounded_rectangle([x0, y0, x0+bw, s-p], radius=lw, outline=c, width=lw)


@_reg("pie_chart")
def _pie_chart(img, d, s, c):
    lw = _lw(s); p = s*0.1; m = s/2
    d.ellipse([p, p, s-p, s-p], outline=c, width=lw)
    d.line([(m, m), (m, p)], fill=c, width=lw)
    d.line([(m, m), (s-p, m)], fill=c, width=lw)


@_reg("trending_up")
def _trending_up(img, d, s, c):
    lw = _lw(s); p = s*0.15
    pts = [(p, s-p), (s*0.38, s*0.55), (s*0.62, s*0.68), (s-p, p)]
    d.line(pts, fill=c, width=lw)
    d.line([(s - p - s*0.22, p), (s-p, p), (s-p, p + s*0.22)], fill=c, width=lw)


@_reg("layers")
def _layers(img, d, s, c):
    lw = _lw(s); m = s/2; p = s*0.12
    for y_off in [-s*0.22, 0, s*0.22]:
        pts = [(p, m + y_off), (m, m + y_off - s*0.14), (s-p, m + y_off), (m, m + y_off + s*0.14)]
        d.polygon(pts, outline=c, width=lw)


@_reg("cpu")
def _cpu(img, d, s, c):
    lw = _lw(s); p = s*0.22
    d.rounded_rectangle([p, p, s-p, s-p], radius=s*0.06, outline=c, width=lw)
    inner = s*0.1
    d.rounded_rectangle([p+inner, p+inner, s-p-inner, s-p-inner], radius=s*0.03, outline=c, width=lw)
    for t in [s*0.35, s*0.5, s*0.65]:
        d.line([(t, p), (t, p - s*0.1)], fill=c, width=lw)
        d.line([(t, s-p), (t, s-p+s*0.1)], fill=c, width=lw)
        d.line([(p, t), (p - s*0.1, t)], fill=c, width=lw)
        d.line([(s-p, t), (s-p+s*0.1, t)], fill=c, width=lw)


@_reg("globe")
def _globe(img, d, s, c):
    lw = _lw(s); p = s*0.1; m = s/2
    d.ellipse([p, p, s-p, s-p], outline=c, width=lw)
    d.line([(p, m), (s-p, m)], fill=c, width=lw)
    d.arc([p + s*0.15, p, s - p - s*0.15, s-p], start=0, end=360, fill=c, width=lw)


# -- App-specific ----

@_reg("omr")
def _omr(img, d, s, c):
    """OMR scanner icon - form with checkboxes."""
    lw = _lw(s); p = s*0.12
    d.rounded_rectangle([p, p, s-p, s-p], radius=s*0.06, outline=c, width=lw)
    for i, y in enumerate([s*0.35, s*0.52, s*0.69]):
        bx = p + s*0.1; bs = s*0.12
        d.rectangle([bx, y - bs/2, bx+bs, y+bs/2], outline=c, width=lw)
        if i == 0:
            d.line([(bx+lw, y), (bx+bs/2, y+bs/2-lw), (bx+bs-lw, y-bs/2+lw)], fill=c, width=lw)
        d.line([(bx + bs + s*0.06, y), (s - p - s*0.1, y)], fill=c, width=lw)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=512)
def icon(
    name: str,
    size: int = 18,
    color: str = "#FFFFFF",
) -> ctk.CTkImage:
    """Return a cached CTkImage for the named Lucide-style icon.

    Parameters
    ----------
    name:   icon name (see module docstring for full list)
    size:   pixel size (same for width and height)
    color:  hex colour string, e.g. "#4A9EFF"
    """
    draw_fn = _REGISTRY.get(name)
    if draw_fn is None:
        # Fallback: filled circle
        img, d = _new(size)
        m = size / 2; r = size * 0.35
        d.ellipse([m-r, m-r, m+r, m+r], outline=_hex(color), width=_lw(size))
    else:
        img, d = _new(size)
        draw_fn(img, d, size, _hex(color))

    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))


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
    """A CTkButton with a Lucide icon on the left (or right)."""
    img = icon(name, size, color)
    return ctk.CTkButton(parent, image=img, text=text, compound=compound, **kw)

