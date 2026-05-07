"""PDF form generation — reproduces the Afghan MoHE QA survey form exactly.

Matches the official HTML form:
  - RTL Dari text throughout (arabic-reshaper + python-bidi + Tahoma font)
  - Ministry header: وزارت تحصیلات عالی / معینیت علمی / ریاست تضمین کیفیت
  - Two logo placeholders (university + QA)
  - Metadata row: پوهنحی / دیپارتمنت / اسم استاد / مضمون / سمستر
  - Instructions paragraph
  - 14-row OMR table with timing marks and square bubbles
  - Columns: timing | # | question | بلی | نخیر | نسبتاً | پیشنهادات
  - Comments section
  - Footer note + approval text
  - Four fiducial corner markers for OMR alignment
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger("tadris_qa_system")

# ---------------------------------------------------------------------------
# Optional heavy imports
# ---------------------------------------------------------------------------
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.utils import ImageReader

    _REPORTLAB_OK = True
except ImportError:
    _REPORTLAB_OK = False
    logger.warning("reportlab not installed — PDF generation disabled.")

try:
    import arabic_reshaper  # type: ignore
    from bidi.algorithm import get_display  # type: ignore

    _BIDI_OK = True
except ImportError:
    _BIDI_OK = False
    logger.warning("arabic-reshaper / python-bidi not installed — Dari text may render incorrectly.")

try:
    import qrcode  # type: ignore
    from PIL import Image as PILImage  # type: ignore

    _QRCODE_OK = True
except ImportError:
    _QRCODE_OK = False

# ---------------------------------------------------------------------------
# Font registration
# ---------------------------------------------------------------------------

_FONT_REGISTERED = False
_FONT_NAME = "Tahoma"
_FONT_BOLD_NAME = "TahomaBold"

# Candidate paths for Tahoma on Windows / Linux / macOS
_TAHOMA_PATHS = [
    r"C:\Windows\Fonts\tahoma.ttf",
    r"C:\Windows\Fonts\Tahoma.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Tahoma.ttf",
    "/Library/Fonts/Tahoma.ttf",
]
_TAHOMA_BOLD_PATHS = [
    r"C:\Windows\Fonts\tahomabd.ttf",
    r"C:\Windows\Fonts\TahomaB.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Tahoma_Bold.ttf",
    "/Library/Fonts/Tahoma Bold.ttf",
]


def _register_fonts() -> None:
    global _FONT_REGISTERED, _FONT_NAME, _FONT_BOLD_NAME
    if _FONT_REGISTERED or not _REPORTLAB_OK:
        return

    # Regular
    for p in _TAHOMA_PATHS:
        if Path(p).exists():
            try:
                pdfmetrics.registerFont(TTFont("Tahoma", p))
                _FONT_NAME = "Tahoma"
                break
            except Exception:
                pass

    # Bold
    for p in _TAHOMA_BOLD_PATHS:
        if Path(p).exists():
            try:
                pdfmetrics.registerFont(TTFont("TahomaBold", p))
                _FONT_BOLD_NAME = "TahomaBold"
                break
            except Exception:
                pass

    _FONT_REGISTERED = True


# ---------------------------------------------------------------------------
# RTL text helper
# ---------------------------------------------------------------------------

def _rtl(text: str) -> str:
    """Shape and apply BiDi algorithm to Dari/Arabic text for reportlab."""
    if not _BIDI_OK or not text:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


# ---------------------------------------------------------------------------
# The 14 official Dari questions (from the HTML form)
# ---------------------------------------------------------------------------

_DARI_QUESTIONS: list[str] = [
    "آیا در آغاز سمستر کورس پالیسی توسط استاد تشریح و توزیع گردیده است؟",
    "آیا تدریس مطابق کورس پالیسی مضمون صورت گرفته است؟",
    "آیا مواد درسی برای شما معرفی شده و موجود است؟",
    "آیا تدریس استاد قابل فهم است؟",
    "آیا از میتود تدریس استاد راضی هستید؟",
    "آیا استاد محصلان را در تدریس سهم میسازد؟ (محصل محوری)",
    "آیا از سلوک و رویه اکادمیک استاد راضی هستید؟",
    "آیا استاد با پلان درسی منظم و آمادگی کامل داخل صنف می شود؟",
    "آیا استاد به سوالات شما جواب های قناعت بخش میدهد؟",
    "آیا استاد پابند به اصول، وقت و زمان معین میباشد؟",
    "آیا استاد در صنف نسبت به درس بیشتر به موضوعات غیر مرتبط به درس تماس میگیرد؟",
    "آیا مشکلات درسی شما توسط استاد حل میگردد؟",
    "آیا از شیوه های ارزیابی استاد راضی هستید؟",
    "آیا استاد در تدریس خویش از تکنالوژی معلوماتی استفاده می نماید؟",
]

# Eastern-Arabic numerals for row numbers
_EASTERN_NUMS = ["۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹", "۱۰", "۱۱", "۱۲", "۱۳", "۱۴"]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DEFAULT_COORDS: dict[str, Any] = {
    "fiducial_size": 7,
    "fiducial_inset": 5,
    "qr_x": 170,
    "qr_y": 248,
    "qr_size": 22,
}


def generate_prefilled_form(
    survey: Any,
    output_path: str | Path,
    *,
    persistence: Any | None = None,
    logo_path: str | Path | None = None,
) -> Path:
    """Generate the official Afghan MoHE QA survey PDF.

    Args:
        survey: A ``models.Survey`` instance with faculty, department,
            subject, professor, semester, academic_year, id fields.
        output_path: Destination file path (created/overwritten).
        persistence: Optional ``PersistenceManager`` for logo_path and
            question_texts overrides from AppSettings.
        logo_path: Explicit university logo image path.

    Returns:
        Resolved ``Path`` of the written PDF.

    Raises:
        RuntimeError: If reportlab is not installed.
    """
    if not _REPORTLAB_OK:
        raise RuntimeError(
            "reportlab is required for PDF generation. "
            "Install it with: pip install reportlab"
        )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    _register_fonts()

    questions = list(_DARI_QUESTIONS)
    resolved_logo: str | None = None
    coords = dict(_DEFAULT_COORDS)

    if persistence is not None:
        stored_q = persistence.get_setting("question_texts")
        if isinstance(stored_q, list) and len(stored_q) == 14:
            questions = stored_q

        stored_coords = persistence.get_setting("pdf_coords")
        if isinstance(stored_coords, dict):
            coords.update(stored_coords)

        if logo_path is None:
            stored_logo = persistence.get_setting("logo_path")
            if stored_logo and Path(stored_logo).exists():
                resolved_logo = str(stored_logo)

    # Import Config at the top of the function to ensure paths are resolved correctly
    from config import Config
    
    if logo_path is not None and Path(str(logo_path)).exists():
        resolved_logo = str(logo_path)
    elif resolved_logo is None and Config.DEFAULT_LOGO_PATH.exists():
        resolved_logo = str(Config.DEFAULT_LOGO_PATH)

    _draw_form(survey, output_path, questions, coords, resolved_logo)
    logger.info("PDF generated: %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Main drawing routine
# ---------------------------------------------------------------------------

def _draw_form(
    survey: Any,
    output_path: Path,
    questions: list[str],
    coords: dict[str, Any],
    logo_path: str | None,
) -> None:
    c = rl_canvas.Canvas(str(output_path), pagesize=A4)
    page_w, page_h = A4

    # Margins (mm)
    margin_l = 10 * mm
    margin_r = 10 * mm
    margin_t = 10 * mm
    margin_b = 10 * mm
    content_w = page_w - margin_l - margin_r

    # Current Y cursor (starts from top, moves down)
    y = page_h - margin_t

    # ---- Fiducial markers ------------------------------------------------- #
    _draw_fiducials(c, page_w, page_h, coords)

    # ---- Header ------------------------------------------------------------ #
    y = _draw_header(c, survey, logo_path, coords, margin_l, content_w, y)

    # ---- Metadata row ------------------------------------------------------ #
    y = _draw_metadata(c, survey, margin_l, content_w, y)

    # ---- Instructions ------------------------------------------------------ #
    y = _draw_instructions(c, margin_l, content_w, y)

    # ---- OMR Table --------------------------------------------------------- #
    y = _draw_table(c, questions, margin_l, content_w, y)

    # ---- Comments section -------------------------------------------------- #
    y = _draw_comments(c, margin_l, content_w, y)

    # ---- Footer ------------------------------------------------------------ #
    _draw_footer(c, survey, margin_l, content_w, margin_b)

    c.save()


# ---------------------------------------------------------------------------
# Section drawers
# ---------------------------------------------------------------------------

def _draw_fiducials(c: Any, page_w: float, page_h: float, coords: dict) -> None:
    size = coords["fiducial_size"] * mm
    inset = coords["fiducial_inset"] * mm
    c.setFillColor(colors.black)
    for x, y in [
        (inset, page_h - inset - size),
        (page_w - inset - size, page_h - inset - size),
        (inset, inset),
        (page_w - inset - size, inset),
    ]:
        c.rect(x, y, size, size, fill=1, stroke=0)


def _draw_header(
    c: Any,
    survey: Any,
    logo_path: str | None,
    coords: dict,
    lx: float,
    cw: float,
    y: float,
) -> float:
    """Draw the ministry header with two logo circles and centred text."""
    header_h = 22 * mm
    logo_d = 18 * mm  # logo circle diameter
    logo_r = logo_d / 2

    # Logo circle centres
    left_logo_cx = lx + logo_r
    right_logo_cx = lx + cw - logo_r
    logo_cy = y - logo_r - 1 * mm

    # Draw logo circles (border only — placeholder)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.5)
    c.setFillColor(colors.white)

    # Left logo (university)
    if logo_path:
        try:
            c.drawImage(
                logo_path,
                left_logo_cx - logo_r,
                logo_cy - logo_r,
                width=logo_d,
                height=logo_d,
                preserveAspectRatio=True,
                mask="auto",
            )
        except Exception:
            c.circle(left_logo_cx, logo_cy, logo_r, fill=1, stroke=1)
            _draw_rtl_centred(c, _rtl("لوگوی پوهنتون"), _FONT_NAME, 6, left_logo_cx, logo_cy, colors.black)
    else:
        c.circle(left_logo_cx, logo_cy, logo_r, fill=1, stroke=1)
        _draw_rtl_centred(c, _rtl("لوگوی پوهنتون"), _FONT_NAME, 6, left_logo_cx, logo_cy, colors.black)

    # Right logo (QA)
    qa_logo_drawn = False
    from config import Config
    
    # Use Config.QA_LOGO_PATH which handles PyInstaller bundles correctly
    if Config.QA_LOGO_PATH.exists():
        try:
            c.drawImage(
                str(Config.QA_LOGO_PATH),
                right_logo_cx - logo_r,
                logo_cy - logo_r,
                width=logo_d,
                height=logo_d,
                preserveAspectRatio=True,
                mask="auto",
            )
            qa_logo_drawn = True
        except Exception:
            pass

    if not qa_logo_drawn:
        c.circle(right_logo_cx, logo_cy, logo_r, fill=1, stroke=1)
        _draw_rtl_centred(c, _rtl("لوگوی تضمین کیفیت"), _FONT_NAME, 5.5, right_logo_cx, logo_cy, colors.black)

    # Centre text block
    text_cx = lx + cw / 2
    line_h = 5.5 * mm

    lines = [
        (_rtl("وزارت تحصیلات عالی"), _FONT_BOLD_NAME, 13),
        (_rtl("معینیت علمی"), _FONT_BOLD_NAME, 11),
        (_rtl("ریاست تضمین کیفیت و اعتباردهی"), _FONT_NAME, 10),
        (_rtl("پرسشنامه ارزیابی خودی استادان"), _FONT_BOLD_NAME, 13),
    ]

    text_top = y - 2 * mm
    for text, font, size in lines:
        c.setFont(font, size)
        c.setFillColor(colors.black)
        c.drawCentredString(text_cx, text_top - size * 0.35, text)
        text_top -= line_h

    return y - header_h - 3 * mm


def _draw_metadata(c: Any, survey: Any, lx: float, cw: float, y: float) -> float:
    """Draw the single metadata row: پوهنحی / دیپارتمنت / اسم استاد / مضمون / سمستر"""
    row_h = 7 * mm
    y -= 2 * mm

    # Background
    c.setFillColor(colors.HexColor("#f9f9f9"))
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(lx, y - row_h, cw, row_h, fill=1, stroke=1)
    c.setFillColor(colors.black)

    # Fields: (label_dari, value)
    # RTL layout — fields go right to left: پوهنحی | دیپارتمنت | اسم استاد | مضمون | سمستر
    fields = [
        ("پوهنحی:", survey.faculty or ""),
        ("دیپارتمنت:", survey.department or ""),
        ("اسم استاد:", survey.professor or ""),
        ("مضمون:", survey.subject or ""),
        ("سمستر:", survey.semester or ""),
    ]

    # Explicit proportional widths (must sum to 1.0):
    # semester is numeric/short → 0.05, department & professor are longer → 0.26 each
    field_ratios = [0.21, 0.26, 0.26, 0.18, 0.09]  # faculty, dept, professor, subject, semester
    field_widths = [cw * r for r in field_ratios]
    # Compute left-edge x for each field (RTL: field 0 is rightmost)
    field_rights = []
    x = lx + cw
    for w in field_widths:
        field_rights.append(x)
        x -= w

    text_y = y - row_h / 2 - 1.5 * mm

    for i, (label, value) in enumerate(fields):
        field_x_right = field_rights[i]
        field_x_left  = field_x_right - field_widths[i]

        # Vertical divider between fields
        if i > 0:
            c.setLineWidth(0.5)
            c.setStrokeColor(colors.black)
            c.line(field_x_right, y, field_x_right, y - row_h)

        # Label (bold)
        c.setFont(_FONT_BOLD_NAME, 7.5)
        label_shaped = _rtl(label)
        label_w = c.stringWidth(label_shaped, _FONT_BOLD_NAME, 7.5)
        c.setFillColor(colors.black)
        c.drawString(field_x_right - label_w - 2 * mm, text_y, label_shaped)

        # Value
        c.setFont(_FONT_NAME, 7.5)
        val_text = _rtl(value) if value else ""
        if val_text:
            c.drawRightString(field_x_right - label_w - 3 * mm, text_y, val_text)

    return y - row_h - 2 * mm


def _draw_instructions(c: Any, lx: float, cw: float, y: float) -> float:
    """Draw the instructions paragraph."""
    logical = (
        "محصلان عزیز! این پرسشنامه صرف به منظور ارتقای سطح کیفیت تدریس طراحی شده است؛ "
        "امید است با کمال دقت و امانت داری پرسشنامه مذکور را خانه پری نموده و در ارتقای کیفیت با ما همکاری کنید."
    )
    c.setFont(_FONT_NAME, 8.5)
    c.setFillColor(colors.black)

    max_w = cw - 4 * mm
    lines = _wrap_rtl_logical(c, logical, _FONT_NAME, 8.5, max_w)

    line_h = 4.5 * mm
    y -= 1 * mm
    for line in lines:
        c.drawRightString(lx + cw - 2 * mm, y - line_h + 1.5 * mm, line)
        y -= line_h

    return y - 2 * mm


def _draw_table(c: Any, questions: list[str], lx: float, cw: float, y: float) -> float:
    """Draw the 14-row OMR table in true RTL column order.

    RTL visual order (right - left on page):
        timing | # | question text | بلی | نخیر | نسبتاً | پیشنهادات

    In PDF coordinate space (left - right) this becomes:
        پیشنهادات | نسبتاً | نخیر | بلی | question text | # | timing
    """
    # Column widths as fractions of content width
    suggest_w = cw * 0.24   # پیشنهادات  — leftmost in PDF coords (rightmost visually for RTL reader)
    bubble_w  = cw * 0.07   # each of نسبتاً / نخیر / بلی
    q_w       = cw * 0.44   # question text
    num_w     = cw * 0.05   # row number
    timing_w  = cw - suggest_w - bubble_w * 3 - q_w - num_w  # timing mark — rightmost in PDF

    header_h = 7 * mm
    row_h    = 11 * mm
    border_lw = 1.0

    # Pre-compute left-edge x for each column (PDF left-right order):
    # [پیشنهادات] [نسبتاً] [نخیر] [بلی] [question] [#] [timing]
    x_suggest  = lx
    x_nesbatan = lx + suggest_w
    x_nakhir   = lx + suggest_w + bubble_w
    x_bali     = lx + suggest_w + bubble_w * 2
    x_question = lx + suggest_w + bubble_w * 3
    x_num      = lx + suggest_w + bubble_w * 3 + q_w
    x_timing   = lx + suggest_w + bubble_w * 3 + q_w + num_w

    # All column left-edges for drawing dividers
    col_edges = [x_suggest, x_nesbatan, x_nakhir, x_bali, x_question, x_num, x_timing]

    # ---- Header row -------------------------------------------------------- #
    c.setFillColor(colors.HexColor("#e0e0e0"))
    c.setStrokeColor(colors.black)
    c.setLineWidth(border_lw)
    c.rect(lx, y - header_h, cw, header_h, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont(_FONT_BOLD_NAME, 8.5)

    header_text_y = y - header_h / 2 - 1.5 * mm

    # پیشنهادات header
    c.drawCentredString(x_suggest + suggest_w / 2, header_text_y, _rtl("پیشنهادات"))
    # نسبتاً
    c.drawCentredString(x_nesbatan + bubble_w / 2, header_text_y, _rtl("نسبتاً"))
    # نخیر
    c.drawCentredString(x_nakhir + bubble_w / 2, header_text_y, _rtl("نخیر"))
    # بلی
    c.drawCentredString(x_bali + bubble_w / 2, header_text_y, _rtl("بلی"))
    # موارد ارزیابی
    c.drawCentredString(x_question + q_w / 2, header_text_y, _rtl("موارد ارزیابی"))
    # شماره
    c.drawCentredString(x_num + num_w / 2, header_text_y, _rtl("شماره"))
    # timing column — blank header

    y -= header_h

    # ---- Data rows --------------------------------------------------------- #
    bubble_size = 3.5 * mm

    for i, question in enumerate(questions[:14]):
        row_bg = colors.white

        c.setFillColor(row_bg)
        c.setStrokeColor(colors.black)
        c.setLineWidth(0.5)
        c.rect(lx, y - row_h, cw, row_h, fill=1, stroke=1)

        row_mid_y = y - row_h / 2

        # Column dividers
        for xe in col_edges[1:]:  # skip leftmost (outer border)
            c.setLineWidth(0.5)
            c.line(xe, y, xe, y - row_h)

        # --- Timing mark (rightmost column in PDF = leftmost for RTL reader) ---
        tm_cx = x_timing + timing_w / 2
        tm_w  = timing_w * 0.55
        tm_h  = 4 * mm
        c.setFillColor(colors.black)
        c.rect(tm_cx - tm_w / 2, row_mid_y - tm_h / 2, tm_w, tm_h, fill=1, stroke=0)

        # --- Row number ---
        c.setFont(_FONT_NAME, 9)
        c.setFillColor(colors.black)
        c.drawCentredString(x_num + num_w / 2, row_mid_y - 1.5 * mm, _rtl(_EASTERN_NUMS[i]))

        # --- Question text (RTL, right-aligned within its column) ---
        q_right = x_question + q_w - 2 * mm
        q_max_w = q_w - 4 * mm
        c.setFont(_FONT_NAME, 8.5)
        c.setFillColor(colors.black)
        # Pass the logical (unshaped) text — _draw_wrapped_rtl handles shaping per line
        _draw_wrapped_rtl(c, question, _FONT_NAME, 8.5, q_right, row_mid_y, q_max_w, row_h)

        # --- OMR square bubbles ---
        # بلی  (rightmost bubble in PDF = first answer column for RTL reader)
        # نخیر
        # نسبتاً (leftmost bubble in PDF)
        for bx_left in [x_bali, x_nakhir, x_nesbatan]:
            bx_centre = bx_left + bubble_w / 2
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.circle(
                bx_centre,
                row_mid_y,
                bubble_size / 2,
                fill=1,
                stroke=1,
            )

        y -= row_h

    # Outer border
    c.setStrokeColor(colors.black)
    c.setLineWidth(border_lw)
    total_h = header_h + row_h * len(questions[:14])
    c.rect(lx, y, cw, total_h, fill=0, stroke=1)

    return y - 1 * mm


def _draw_comments(c: Any, lx: float, cw: float, y: float) -> float:
    """Draw the سایر نظریات و پیشنهادات comments box."""
    box_h = 20 * mm
    c.setFillColor(colors.white)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    c.rect(lx, y - box_h, cw, box_h, fill=1, stroke=1)

    c.setFont(_FONT_BOLD_NAME, 8.5)
    c.setFillColor(colors.black)
    label = _rtl("سایر نظریات و پیشنهادات:")
    c.drawRightString(lx + cw - 3 * mm, y - 5 * mm, label)

    return y - box_h - 2 * mm


def _draw_footer(c: Any, survey: Any, lx: float, cw: float, margin_b: float) -> None:
    """Draw the footer note and approval text at the bottom of the page."""
    footer_y = margin_b + 18 * mm

    note_logical = (
        "نوت: از استادان محترم خواهش میشود این فورم را در هفته یازدهم به محصلان توزیع نموده، "
        "نتایج آن را تحلیل و در مطابقت با آن پلان بهبود تدریس را برای سمستر آینده ترتیب کرده "
        "و با آمر دیپارتمنت مربوطه شریک سازند."
    )
    c.setFont(_FONT_NAME, 7.5)
    c.setFillColor(colors.black)

    lines = _wrap_rtl_logical(c, note_logical, _FONT_NAME, 7.5, cw - 4 * mm)
    line_h = 4 * mm
    note_y = footer_y
    for line in lines:
        c.drawRightString(lx + cw - 2 * mm, note_y, line)
        note_y -= line_h

    # Approval text (single line)
    approval = _rtl("تائید شده جلسه مورخ ۲۱ حمل ۱۳۹۹ پروتوکول شماره (۲) بورد تضمین کیفیت و اعتباردهی")
    c.setFont(_FONT_NAME, 7.5)
    c.drawRightString(lx + cw - 2 * mm, margin_b + 3 * mm, approval)


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _draw_rtl_centred(
    c: Any,
    text: str,
    font: str,
    size: float,
    cx: float,
    cy: float,
    fill_color: Any,
) -> None:
    """Draw RTL text centred at (cx, cy)."""
    c.setFont(font, size)
    c.setFillColor(fill_color)
    c.drawCentredString(cx, cy - size * 0.35, text)


def _wrap_rtl_logical(
    c: Any,
    logical_text: str,
    font: str,
    size: float,
    max_w: float,
) -> list[str]:
    """Split *logical_text* into visual lines that each fit within *max_w*.

    Wrapping is done on the **logical** (unshaped) text so that word order is
    preserved correctly.  Each resulting line is then shaped with ``_rtl()``
    for rendering.  This avoids the reversed-line-order bug that occurs when
    splitting an already-shaped (visually reordered) string.
    """
    c.setFont(font, size)
    words = logical_text.split()
    logical_lines: list[str] = []
    current: list[str] = []

    for word in words:
        candidate = " ".join(current + [word])
        # Measure the shaped version so width is accurate
        if c.stringWidth(_rtl(candidate), font, size) <= max_w:
            current.append(word)
        else:
            if current:
                logical_lines.append(" ".join(current))
            current = [word]
    if current:
        logical_lines.append(" ".join(current))

    # Shape each logical line individually for display
    return [_rtl(line) for line in logical_lines]


def _draw_wrapped_rtl(
    c: Any,
    logical_text: str,
    font: str,
    size: float,
    right_x: float,
    mid_y: float,
    max_w: float,
    row_h: float,
) -> None:
    """Draw RTL text wrapped within max_w, vertically centred in row_h.

    Args:
        logical_text: The original (unshaped) Dari/Arabic string.
        right_x: Right edge x-coordinate for ``drawRightString``.
        mid_y: Vertical centre of the cell.
        max_w: Maximum line width in points.
        row_h: Total cell height in points (used for vertical centering).
    """
    lines = _wrap_rtl_logical(c, logical_text, font, size, max_w)

    line_h = size * 1.4
    total_text_h = len(lines) * line_h
    # Start from top of the text block, centred in the cell
    start_y = mid_y + total_text_h / 2 - line_h * 0.75

    c.setFont(font, size)
    c.setFillColor(colors.black)
    for line in lines:
        c.drawRightString(right_x, start_y, line)
        start_y -= line_h


# ---------------------------------------------------------------------------
# Convenience: open the generated PDF with the OS default viewer
# ---------------------------------------------------------------------------

def open_pdf(path: str | Path) -> None:
    """Open *path* with the system default PDF viewer."""
    path = str(Path(path).resolve())
    try:
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])
    except Exception as exc:
        logger.error("Could not open PDF: %s", exc)
