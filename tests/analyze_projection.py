"""
Analyze pixel projections on an aligned form to find actual checkbox positions.
Prints horizontal and vertical dark-pixel density profiles.
"""
import sys
from pathlib import Path
import cv2
import numpy as np

img_path = Path(r"d:\Projects\OMR\debug\aligned_20260509_102311.jpg")
img = cv2.imread(str(img_path))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape
print(f"Image size: {w} x {h}")

_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

# ── Horizontal projection (dark pixels per column) ────────────────────────────
col_proj = np.sum(binary, axis=0) / 255
print("\n=== Horizontal projection (dark pixels per x, every 10px) ===")
for x in range(0, w, 10):
    val = int(col_proj[x])
    bar = "#" * min(int(val / h * 200), 60)
    print(f"  x={x:4d}: {val:5d}  {bar}")

# ── Vertical projection (dark pixels per row) ─────────────────────────────────
row_proj = np.sum(binary, axis=1) / 255
print("\n=== Vertical projection (dark pixels per y, every 10px) ===")
for y in range(0, h, 10):
    val = int(row_proj[y])
    bar = "#" * min(int(val / w * 200), 60)
    print(f"  y={y:4d}: {val:5d}  {bar}")

# ── Find peaks (likely checkbox column centers and row centers) ───────────────
from scipy.signal import find_peaks

col_smooth = np.convolve(col_proj, np.ones(5)/5, mode='same')
peaks_x, _ = find_peaks(col_smooth, height=h*0.05, distance=30)
print(f"\nColumn peaks (likely checkbox columns or borders): {peaks_x.tolist()}")

row_smooth = np.convolve(row_proj, np.ones(5)/5, mode='same')
peaks_y, _ = find_peaks(row_smooth, height=w*0.03, distance=20)
print(f"Row peaks (likely checkbox rows or borders): {peaks_y.tolist()}")
