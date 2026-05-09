"""
Find actual checkbox column and row positions from the aligned form image.
Uses simple peak detection on pixel projections — no scipy needed.
Also generates a visual overlay showing detected peaks.
"""
import sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from image_aligner import ImageAligner

FORM_DIR = Path(__file__).resolve().parent.parent / "Data Structure Forms"
OUT_DIR  = Path(__file__).resolve().parent.parent / "debug"
OUT_DIR.mkdir(exist_ok=True)

# Use the last image (most recently processed)
img_path = sorted(FORM_DIR.glob("*.jpg"))[-1]
print(f"Analyzing: {img_path.name}")

raw = cv2.imread(str(img_path))
aligner = ImageAligner()
aligned = aligner.align_image(raw)
gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
h, w = gray.shape
print(f"Aligned size: {w} x {h}")

_, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

# ── Simple peak finder ────────────────────────────────────────────────────────
def find_peaks_simple(signal, min_height, min_distance):
    peaks = []
    n = len(signal)
    for i in range(1, n - 1):
        if signal[i] < min_height:
            continue
        if signal[i] >= signal[i-1] and signal[i] >= signal[i+1]:
            if not peaks or (i - peaks[-1]) >= min_distance:
                peaks.append(i)
            elif signal[i] > signal[peaks[-1]]:
                peaks[-1] = i
    return peaks

def smooth(signal, window=5):
    kernel = np.ones(window) / window
    return np.convolve(signal, kernel, mode='same')

# ── Horizontal projection → column positions ──────────────────────────────────
col_proj = np.sum(binary, axis=0) / 255
col_smooth = smooth(col_proj, 7)
col_peaks = find_peaks_simple(col_smooth, min_height=h * 0.08, min_distance=25)
print(f"\nColumn peaks (x positions, likely checkbox columns/borders):")
for x in col_peaks:
    print(f"  x={x:4d}  density={col_smooth[x]/h:.3f}")

# ── Vertical projection → row positions ───────────────────────────────────────
row_proj = np.sum(binary, axis=1) / 255
row_smooth = smooth(row_proj, 5)
row_peaks = find_peaks_simple(row_smooth, min_height=w * 0.05, min_distance=20)
print(f"\nRow peaks (y positions, likely checkbox rows/borders):")
for y in row_peaks:
    print(f"  y={y:4d}  density={row_smooth[y]/w:.3f}")

# ── Estimate checkbox grid from peaks ─────────────────────────────────────────
# Filter out edge peaks (form border lines) — keep only interior peaks
# Checkbox columns: expect 3 groups of peaks (one per column)
# Checkbox rows: expect 14 groups of peaks (one per row)

# For columns: filter to x range 300-1100 (skip left/right borders)
inner_col_peaks = [x for x in col_peaks if 300 <= x <= 1100]
print(f"\nInner column peaks (x=300..1100): {inner_col_peaks}")

# For rows: filter to y range 200-1400 (skip top/bottom borders)
inner_row_peaks = [y for y in row_peaks if 200 <= y <= 1400]
print(f"Inner row peaks (y=200..1400): {inner_row_peaks}")

# ── Generate annotated image ───────────────────────────────────────────────────
vis = aligned.copy()

# Draw all column peaks (cyan vertical lines)
for x in col_peaks:
    cv2.line(vis, (x, 0), (x, h), (255, 255, 0), 1)
    cv2.putText(vis, str(x), (x-15, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,255,0), 1)

# Draw all row peaks (magenta horizontal lines)
for y in row_peaks:
    cv2.line(vis, (0, y), (w, y), (255, 0, 255), 1)
    cv2.putText(vis, str(y), (5, y-3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,0,255), 1)

# Draw inner column peaks (green)
for x in inner_col_peaks:
    cv2.line(vis, (x, 0), (x, h), (0, 255, 0), 2)

# Draw inner row peaks (orange)
for y in inner_row_peaks:
    cv2.line(vis, (0, y), (w, y), (0, 165, 255), 2)

# Draw current config margins (red rectangle)
cv2.rectangle(vis, (320, 360), (1240-690, 1754-445), (0, 0, 255), 2)
cv2.putText(vis, "CURRENT margins", (320, 355), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

# Draw calibrate_grid margins (blue rectangle)
cv2.rectangle(vis, (300, 240), (1240-100, 1754-130), (255, 100, 0), 2)
cv2.putText(vis, "CALIBRATE margins", (300, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,100,0), 1)

out = OUT_DIR / "peak_analysis.jpg"
cv2.imwrite(str(out), vis)
print(f"\nSaved peak analysis image: {out}")

# ── Print spacing analysis ─────────────────────────────────────────────────────
if len(inner_row_peaks) >= 2:
    spacings = [inner_row_peaks[i+1] - inner_row_peaks[i] for i in range(len(inner_row_peaks)-1)]
    print(f"\nRow spacing between inner peaks: {spacings}")
    print(f"  min={min(spacings)}  max={max(spacings)}  avg={sum(spacings)/len(spacings):.1f}")

if len(inner_col_peaks) >= 2:
    spacings = [inner_col_peaks[i+1] - inner_col_peaks[i] for i in range(len(inner_col_peaks)-1)]
    print(f"\nColumn spacing between inner peaks: {spacings}")
