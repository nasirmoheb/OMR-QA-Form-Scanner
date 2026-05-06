"""Debug script: overlay checkbox grid on a real aligned form image."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np

from checkbox_reader import CheckboxReader
from config import Config
from image_aligner import ImageAligner
from vision_processor import VisionProcessor

# ------------------------------------------------------------------ #
#  Configurable grid constants  (edit these after visual inspection)
# ------------------------------------------------------------------ #
MARGIN_LEFT = 310
MARGIN_RIGHT = 690
MARGIN_TOP = 355
MARGIN_BOTTOM = 430
COL_GAP = 15
ROW_GAP = 10

# Special handling: wide rows (Q1, Q11, Q14) need vertical offset
WIDE_ROW_V_OFFSET = 0  # pixels to shift wide rows downward

# Timing mark detection constants
TIMING_MARK_X_START = 100
TIMING_MARK_X_END = 100
TIMING_MARK_MIN_AREA = 30
TIMING_MARK_MAX_AREA = 10
TIMING_MARK_FILL_RATIO = 0.5


def cell_box(
    row: int,
    col: int,
    form_w: int,
    form_h: int,
    rows: int,
    cols: int,
) -> tuple[int, int, int, int]:
    """Return (x1, y1, x2, y2) for the checkbox at row, col."""
    usable_w = form_w - MARGIN_LEFT - MARGIN_RIGHT
    usable_h = form_h - MARGIN_TOP - MARGIN_BOTTOM

    cell_w = (usable_w - (cols - 1) * COL_GAP) // cols
    cell_h = (usable_h - (rows - 1) * ROW_GAP) // rows

    x1 = MARGIN_LEFT + col * (cell_w + COL_GAP)
    y1 = MARGIN_TOP + row * (cell_h + ROW_GAP)

    # Apply vertical offset for rows after wide Q1, Q11, and Q14
    if row >= 1:  # After Q1
        y1 += WIDE_ROW_V_OFFSET
    if row >= 11:  # After Q10 comes Q11 (also wide)
        y1 += WIDE_ROW_V_OFFSET
    if row >= 13:  # After Q13 comes Q14 (also wide)
        y1 += WIDE_ROW_V_OFFSET

    x2 = x1 + cell_w
    y2 = y1 + cell_h
    return x1, y1, x2, y2


def detect_timing_marks(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Detect timing marks and return list of (cy, area, fill_ratio, cx)."""
    h, w = gray.shape
    x1 = max(0, min(w, TIMING_MARK_X_START))
    x2 = max(0, min(w, TIMING_MARK_X_END))
    if x2 <= x1:
        x1, x2 = max(0, w - 80), w

    strip = gray[:, x1:x2]
    _, binary = cv2.threshold(strip, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[int, int, int, int]] = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < TIMING_MARK_MIN_AREA or area > TIMING_MARK_MAX_AREA:
            continue
        bx, by, bw, bh = cv2.boundingRect(cnt)
        if bw < 3 or bh < 3:
            continue
        fill_ratio = area / (bw * bh)
        if fill_ratio < TIMING_MARK_FILL_RATIO:
            continue
        moments = cv2.moments(cnt)
        if moments["m00"] == 0:
            continue
        cy = int(moments["m01"] / moments["m00"])
        cx = int(moments["m10"] / moments["m00"])
        candidates.append((cy, area, fill_ratio, cx + x1))

    candidates.sort(key=lambda t: t[0])
    return candidates


def annotate(image: np.ndarray) -> np.ndarray:
    """Draw the current grid + densities on the aligned image."""
    vis = image.copy()
    gray = cv2.cvtColor(vis, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Detect and draw timing marks
    timing_marks = detect_timing_marks(gray)
    print(f"Detected {len(timing_marks)} timing marks")
    for cy, area, fill_ratio, cx in timing_marks:
        cv2.circle(vis, (cx, cy), 8, (0, 255, 0), -1)
        cv2.putText(vis, f"TM", (cx - 10, cy - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

    # Draw timing mark search region
    x1 = max(0, min(w, TIMING_MARK_X_START))
    x2 = max(0, min(w, TIMING_MARK_X_END))
    cv2.rectangle(vis, (x1, 0), (x2, h), (255, 255, 0), 1)

    for row in range(14):
        for col in range(3):
            x1, y1, x2, y2 = cell_box(row, col, w, h, 14, 3)
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, w), min(y2, h)

            # Draw cell border
            cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 0, 255), 2)

            # Compute density
            region = gray[y1:y2, x1:x2]
            if region.size == 0:
                density = 0.0
            else:
                _, binary = cv2.threshold(
                    region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
                )
                density = cv2.countNonZero(binary) / binary.size

            label = f"{density:.2f}"
            cv2.putText(
                vis,
                label,
                (x1 + 3, y1 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 0, 0) if density >= 0.35 else (0, 0, 255),
                1,
            )

    return vis


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to scanned form image")
    parser.add_argument("-o", "--out", default="debug_aligned.jpg")
    args = parser.parse_args()

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"File not found: {img_path}")
        sys.exit(1)

    # Load and align
    raw = cv2.imread(str(img_path))
    if raw is None:
        print(f"Could not read image: {img_path}")
        sys.exit(1)

    aligner = ImageAligner()
    markers, status = aligner.detect_fiducial_markers(raw)
    print(f"Markers ({len(markers)}): {markers}  status={status}")

    aligned = aligner.align_image(raw)
    if aligned is None:
        print("Alignment failed.")
        sys.exit(1)

    print(f"Aligned size: {aligned.shape[1]} x {aligned.shape[0]}")

    # Print full density matrix
    print("\n--- Density matrix ---")
    reader = CheckboxReader(Config())
    grid = reader.read_checkbox_grid(aligned)
    for i, row in enumerate(grid, start=1):
        print(f"R{i:02d}: {row}")

    # Test with lower thresholds
    for thr in [0.15, 0.20, 0.25, 0.30, 0.35]:
        print(f"\n--- Answers with threshold={thr} ---")
        for i, row in enumerate(grid, start=1):
            above = [j for j, d in enumerate(row) if d >= thr]
            # RTL form: columns right-to-left are YES, NO, MAYBE
            # Scanning left-to-right: col0=MAYBE(S), col1=NO(N), col2=YES(Y)
            labels = ["S", "N", "Y"]
            ans = labels[above[0]] if len(above) == 1 else "I"
            print(f"Q{i:02d}: {ans}  (densities={[round(d,3) for d in row]})")

    # Annotate and save
    vis = annotate(aligned)
    cv2.imwrite(args.out, vis)
    print(f"\nAnnotated image saved to: {args.out}")

    # Save aligned-only for reference
    cv2.imwrite("debug_aligned_raw.jpg", aligned)
    print("Raw aligned image saved to: debug_aligned_raw.jpg")


if __name__ == "__main__":
    main()
