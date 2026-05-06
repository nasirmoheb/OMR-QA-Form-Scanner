"""Vision processing: read checkbox selections from an aligned OMR form."""

from typing import Any

import cv2
import numpy as np

from config import Config, setup_logging

logger = setup_logging()

# Grid layout constants (calibrated against the real A4 Persian form)
# These are defaults — Config values take precedence when set.
_MARGIN_LEFT: int = 310
_MARGIN_RIGHT: int = 690
_MARGIN_TOP: int = 355
_MARGIN_BOTTOM: int = 430
_COL_GAP: int = 15
_ROW_GAP: int = 10

# Special handling: wide rows (Q1, Q11, Q14) — no offset needed for A4 form
_WIDE_ROW_V_OFFSET: int = 0  # pixels to shift wide rows downward

# Inner padding: ignore the outer border of each cell to focus on the mark
_CELL_PAD_X: int = 8
_CELL_PAD_Y: int = 4

# Timing mark detection constants (calibrated against the real A4 form)
_TIMING_MARK_X_START: int = 100
_TIMING_MARK_X_END: int = 100
_TIMING_MARK_MIN_AREA: int = 30
_TIMING_MARK_MAX_AREA: int = 10
_TIMING_MARK_FILL_RATIO: float = 0.5
_TIMING_MARK_COUNT_TOLERANCE: int = 3


def _cell_box(
    row: int,
    col: int,
    form_w: int,
    form_h: int,
    rows: int,
    cols: int,
    row_y_positions: list[int] | None = None,
    margin_left: int = _MARGIN_LEFT,
    margin_right: int = _MARGIN_RIGHT,
    margin_top: int = _MARGIN_TOP,
    margin_bottom: int = _MARGIN_BOTTOM,
    col_gap: int = _COL_GAP,
    row_gap: int = _ROW_GAP,
) -> tuple[int, int, int, int]:
    """Return ``(x1, y1, x2, y2)`` for the checkbox at *row*, *col*.

    Args:
        row: Zero-based row index.
        col: Zero-based column index.
        form_w: Form width in pixels.
        form_h: Form height in pixels.
        rows: Total number of rows.
        cols: Total number of columns.
        row_y_positions: Optional calibrated y-centres from timing marks.
        margin_left: Left margin in pixels.
        margin_right: Right margin in pixels.
        margin_top: Top margin in pixels.
        margin_bottom: Bottom margin in pixels.
        col_gap: Gap between columns in pixels.
        row_gap: Gap between rows in pixels.

    Returns:
        Bounding-box tuple ``(x1, y1, x2, y2)``.
    """
    usable_w = form_w - margin_left - margin_right
    usable_h = form_h - margin_top - margin_bottom

    cell_w = (usable_w - (cols - 1) * col_gap) // cols
    cell_h = (usable_h - (rows - 1) * row_gap) // rows

    x1 = margin_left + col * (cell_w + col_gap)

    if row_y_positions is not None and 0 <= row < len(row_y_positions):
        cy = row_y_positions[row]
        y1 = cy - cell_h // 2
    else:
        y1 = margin_top + row * (cell_h + row_gap)
        # Apply vertical offset for rows after wide Q1, Q11, and Q14
        if row >= 1:
            y1 += _WIDE_ROW_V_OFFSET
        if row >= 11:
            y1 += _WIDE_ROW_V_OFFSET
        if row >= 13:
            y1 += _WIDE_ROW_V_OFFSET

    x2 = x1 + cell_w
    y2 = y1 + cell_h

    return x1, y1, x2, y2


class CheckboxReader:
    """Reads a 14 x 3 checkbox grid from an aligned form image."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize with configuration.

        Args:
            config: Application configuration. Uses global defaults when
                ``None``.
        """
        self.config = config or Config()

    # ------------------------------------------------------------------ #
    #  Pixel-density helper
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_pixel_density(
        region: np.ndarray, invert: bool = True
    ) -> float:
        """Return the ratio of dark pixels in *region*.

        Grayscale conversion and binary thresholding are applied
        internally so the function accepts colour or greyscale images.

        Args:
            region: Image patch (H, W) or (H, W, 3).
            invert: If ``True`` (default) black pixels are considered
                "marked". If ``False`` white pixels are marked.

        Returns:
            Ratio in ``[0.0, 1.0]`` of marked pixels.
        """
        if len(region.shape) == 3:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        else:
            gray = region.copy()

        # Otsu is robust to varying lighting; fallback to 127 if it fails
        if gray.size == 0:
            return 0.0

        try:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        except cv2.error:
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        marked = cv2.countNonZero(binary) if invert else (binary.size - cv2.countNonZero(binary))
        return marked / binary.size

    # ------------------------------------------------------------------ #
    #  Grid coordinate helper
    # ------------------------------------------------------------------ #

    def get_checkbox_bounds(
        self, row: int, col: int, row_y_positions: list[int] | None = None
    ) -> tuple[int, int, int, int]:
        """Compute bounding box for the checkbox at *row*, *col*.

        Args:
            row: Zero-based row index (0 .. ROW_COUNT-1).
            col: Zero-based column index (0 .. COLUMN_COUNT-1).
            row_y_positions: Optional list of calibrated y-centres from
                detected timing marks.

        Returns:
            ``(x1, y1, x2, y2)`` in pixel coordinates.
        """
        return _cell_box(
            row,
            col,
            self.config.FORM_WIDTH,
            self.config.FORM_HEIGHT,
            self.config.ROW_COUNT,
            self.config.COLUMN_COUNT,
            row_y_positions,
            margin_left=getattr(self.config, "MARGIN_LEFT", _MARGIN_LEFT),
            margin_right=getattr(self.config, "MARGIN_RIGHT", _MARGIN_RIGHT),
            margin_top=getattr(self.config, "MARGIN_TOP", _MARGIN_TOP),
            margin_bottom=getattr(self.config, "MARGIN_BOTTOM", _MARGIN_BOTTOM),
            col_gap=getattr(self.config, "COL_GAP", _COL_GAP),
            row_gap=getattr(self.config, "ROW_GAP", _ROW_GAP),
        )

    # ------------------------------------------------------------------ #
    #  Timing mark detection
    # ------------------------------------------------------------------ #

    def detect_timing_marks(
        self, aligned_image: np.ndarray
    ) -> list[int] | None:
        """Detect solid black timing marks on the far-right edge.

        Returns ``None`` immediately when ``config.USE_TIMING_MARKS`` is
        ``False`` (forms that use only corner fiducial markers).

        Args:
            aligned_image: Perspective-corrected form image.

        Returns:
            List of y-centre integers (one per timing mark) or ``None``
            if detection is disabled or fails.
        """
        if not getattr(self.config, "USE_TIMING_MARKS", True):
            return None
        if len(aligned_image.shape) == 3:
            gray = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = aligned_image.copy()

        h, w = gray.shape
        x1 = max(0, min(w, _TIMING_MARK_X_START))
        x2 = max(0, min(w, _TIMING_MARK_X_END))
        if x2 <= x1:
            x1, x2 = max(0, w - 80), w

        strip = gray[:, x1:x2]
        _, binary = cv2.threshold(strip, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[int, int, int, float]] = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < _TIMING_MARK_MIN_AREA or area > _TIMING_MARK_MAX_AREA:
                continue
            bx, by, bw, bh = cv2.boundingRect(cnt)
            if bw < 3 or bh < 3:
                continue
            fill_ratio = area / (bw * bh)
            if fill_ratio < _TIMING_MARK_FILL_RATIO:
                continue
            moments = cv2.moments(cnt)
            if moments["m00"] == 0:
                continue
            cy = int(moments["m01"] / moments["m00"])
            cx = int(moments["m10"] / moments["m00"])
            candidates.append((cy, area, fill_ratio, cx + x1))

        candidates.sort(key=lambda t: t[0])
        expected = self.config.ROW_COUNT
        tol = _TIMING_MARK_COUNT_TOLERANCE

        if len(candidates) < expected - tol:
            logger.warning(
                "Only %d timing mark(s) found (need ~%d).", len(candidates), expected
            )
            return None

        if len(candidates) > expected + tol:
            logger.info("%d timing marks; keeping %d largest.", len(candidates), expected)
            candidates = sorted(candidates, key=lambda t: t[1], reverse=True)[:expected]
            candidates.sort(key=lambda t: t[0])

        if len(candidates) != expected:
            logger.info(
                "Timing mark count mismatch (%d vs %d); falling back to uniform grid.",
                len(candidates), expected
            )
            return None

        return [c[0] for c in candidates]

    # ------------------------------------------------------------------ #
    #  Grid reading
    # ------------------------------------------------------------------ #

    def read_checkbox_grid(
        self, aligned_image: np.ndarray
    ) -> list[list[float]]:
        """Measure pixel density for every cell in the 14 x 3 grid.

        Uses detected timing marks (when available) to calibrate each
        row's y-position, compensating for paper stretch, shrink, or
        minor skew after perspective correction.

        Args:
            aligned_image: Perspective-corrected form image.

        Returns:
            2-D list ``densities[row][col]``.
        """
        if len(aligned_image.shape) == 3:
            gray = cv2.cvtColor(aligned_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = aligned_image.copy()

        row_y_positions = self.detect_timing_marks(aligned_image)
        if row_y_positions is not None:
            logger.info("Using %d timing marks for row calibration.", len(row_y_positions))

        densities: list[list[float]] = []
        for row in range(self.config.ROW_COUNT):
            row_densities: list[float] = []
            for col in range(self.config.COLUMN_COUNT):
                x1, y1, x2, y2 = self.get_checkbox_bounds(row, col, row_y_positions)
                # Clamp to image bounds
                h, w = gray.shape
                x1, y1 = max(x1, 0), max(y1, 0)
                x2, y2 = min(x2, w), min(y2, h)
                if x2 <= x1 or y2 <= y1:
                    row_densities.append(0.0)
                    continue
                region = gray[y1:y2, x1:x2]
                density = self.calculate_pixel_density(region, invert=True)
                row_densities.append(density)
            densities.append(row_densities)
        return densities

    # ------------------------------------------------------------------ #
    #  Selection determination
    # ------------------------------------------------------------------ #

    def determine_selection(
        self, densities: list[float]
    ) -> str:
        """Classify a single row given its three column densities.

        Args:
            densities: Three-element list ``[col0, col1, col2]``.

        Returns:
            ``"Yes"``, ``"Somewhat"``, ``"No"`` or ``"Invalid"``.
        """
        if len(densities) != self.config.COLUMN_COUNT:
            logger.warning("Unexpected density count: %d", len(densities))
            return "Invalid"

        above = [
            i
            for i, d in enumerate(densities)
            if d >= self.config.CHECKBOX_THRESHOLD
        ]

        # RTL form: columns from right to left are YES, NO, MAYBE
        # Our code scans left-to-right, so reverse: col0=MAYBE, col1=NO, col2=YES
        col_labels = ["Somewhat", "No", "Yes"]

        if len(above) == 0:
            return "Invalid"
        if len(above) == 1:
            return col_labels[above[0]]
        # More than one checkbox marked
        logger.info(
            "Multiple selections detected (densities %s); marking Invalid.",
            densities,
        )
        return "Invalid"

    # ------------------------------------------------------------------ #
    #  Convenience: full form decode
    # ------------------------------------------------------------------ #

    def decode_form(self, aligned_image: np.ndarray) -> list[str]:
        """Return the selected answer for every row.

        Args:
            aligned_image: Aligned form image.

        Returns:
            List of 14 answer strings (one per question).
        """
        grid = self.read_checkbox_grid(aligned_image)
        return [self.determine_selection(row) for row in grid]
