"""Brute-force search for the best MARGIN_LEFT value."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np

from checkbox_reader import CheckboxReader
from config import Config
from image_aligner import ImageAligner

# Fixed values
MARGIN_RIGHT = 100
MARGIN_TOP = 240
MARGIN_BOTTOM = 130
COL_GAP = 30
ROW_GAP = 5


def cell_box(row, col, form_w, form_h, rows, cols, margin_left):
    usable_w = form_w - margin_left - MARGIN_RIGHT
    cell_w = (usable_w - (cols - 1) * COL_GAP) // cols
    usable_h = form_h - MARGIN_TOP - MARGIN_BOTTOM
    cell_h = (usable_h - (rows - 1) * ROW_GAP) // rows

    x1 = margin_left + col * (cell_w + COL_GAP)
    y1 = MARGIN_TOP + row * (cell_h + ROW_GAP)
    x2 = x1 + cell_w
    y2 = y1 + cell_h
    return x1, y1, x2, y2


def max_density_for_margin(aligned, margin_left):
    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    max_d = 0.0
    best_pos = None

    for row in range(14):
        for col in range(3):
            x1, y1, x2, y2 = cell_box(row, col, w, h, 14, 3, margin_left)
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, w), min(y2, h)
            region = gray[y1:y2, x1:x2]
            if region.size == 0:
                continue
            _, binary = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            density = cv2.countNonZero(binary) / binary.size
            if density > max_d:
                max_d = density
                best_pos = (row, col, x1, y1, x2, y2)
    return max_d, best_pos


def main():
    img_path = Path("C:/Users/nasir/Pictures/OMR/1.jpeg")
    raw = cv2.imread(str(img_path))
    aligner = ImageAligner()
    aligned = aligner.align_image(raw)

    print(f"Aligned size: {aligned.shape[1]} x {aligned.shape[0]}")
    print("Searching MARGIN_LEFT from 300 to 700...\n")
    print(f"{'MARGIN_LEFT':>12} | {'cell_w':>6} | {'max_density':>11} | {'best_pos':>20}")
    print("-" * 60)

    best_margin = 0
    best_density = 0.0
    for ml in range(300, 701, 20):
        md, pos = max_density_for_margin(aligned, ml)
        usable_w = 800 - ml - MARGIN_RIGHT
        cell_w = (usable_w - 2 * COL_GAP) // 3
        print(f"{ml:>12} | {cell_w:>6} | {md:>11.3f} | {str(pos):>20}")
        if md > best_density:
            best_density = md
            best_margin = ml

    print(f"\nBest MARGIN_LEFT = {best_margin} with max density = {best_density:.3f}")

    # Also try a finer search around the best
    print(f"\nFine search around {best_margin}...")
    for ml in range(best_margin - 20, best_margin + 21, 5):
        md, pos = max_density_for_margin(aligned, ml)
        usable_w = 800 - ml - MARGIN_RIGHT
        cell_w = (usable_w - 2 * COL_GAP) // 3
        print(f"{ml:>12} | {cell_w:>6} | {md:>11.3f} | {str(pos):>20}")


if __name__ == "__main__":
    main()
