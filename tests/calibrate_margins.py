"""
Precisely calibrate checkbox grid margins by scanning the aligned form.

Strategy:
  1. Scan small horizontal strips at known row positions to find checkbox centers
  2. Scan small vertical strips at known column positions to find checkbox centers
  3. Output the exact MARGIN_LEFT, MARGIN_RIGHT, MARGIN_TOP, MARGIN_BOTTOM,
     COL_GAP, ROW_GAP values to put in config.py

Also generates a detailed annotated image showing the calibrated grid.
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

ROWS = 14
COLS = 3
FORM_W = 1240
FORM_H = 1754

# ── Load and align ─────────────────────────────────────────────────────────────
# Use multiple images and average for robustness
images = sorted(FORM_DIR.glob("*.jpg"))
aligner = ImageAligner()

all_col_centers = []
all_row_centers = []

for img_path in images:
    raw = cv2.imread(str(img_path))
    aligned = aligner.align_image(raw)
    if aligned is None:
        continue
    gray = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Preprocess: invert so dark ink = high values
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

    # ── Find checkbox columns ──────────────────────────────────────────────────
    # The form is RTL. Checkboxes are in the right portion of the form.
    # From projection analysis: checkbox columns are around x=390-560 and x=977-1095
    # Let's scan x=350..1150 with a sliding window and find 3 column centers

    col_proj = np.sum(binary, axis=0).astype(float)

    # Smooth
    col_smooth = np.convolve(col_proj, np.ones(15)/15, mode='same')

    # Find local maxima in x=350..1150
    candidates = []
    for x in range(350, 1150):
        if col_smooth[x] > col_smooth[x-1] and col_smooth[x] >= col_smooth[x+1]:
            if col_smooth[x] > h * 30:  # at least 30 dark pixels per row on average
                candidates.append((x, col_smooth[x]))

    # Cluster candidates into 3 groups (3 checkbox columns)
    # Sort by x and merge nearby peaks
    merged = []
    for x, val in candidates:
        if merged and x - merged[-1][0] < 40:
            # merge: keep higher value
            if val > merged[-1][1]:
                merged[-1] = (x, val)
        else:
            merged.append((x, val))

    # Keep top 3 by value if we have more
    merged.sort(key=lambda t: t[1], reverse=True)
    top3 = sorted(merged[:3], key=lambda t: t[0])  # sort by x position
    col_centers = [x for x, _ in top3]
    all_col_centers.append(col_centers)

    # ── Find checkbox rows ─────────────────────────────────────────────────────
    # Scan y=180..1380 for row centers
    row_proj = np.sum(binary, axis=1).astype(float)
    row_smooth = np.convolve(row_proj, np.ones(7)/7, mode='same')

    # Find local maxima in y=180..1380
    row_candidates = []
    for y in range(180, 1380):
        if row_smooth[y] > row_smooth[y-1] and row_smooth[y] >= row_smooth[y+1]:
            if row_smooth[y] > w * 20:
                row_candidates.append((y, row_smooth[y]))

    # Cluster into 14 groups
    row_merged = []
    for y, val in row_candidates:
        if row_merged and y - row_merged[-1][0] < 30:
            if val > row_merged[-1][1]:
                row_merged[-1] = (y, val)
        else:
            row_merged.append((y, val))

    # Keep top 14 by value
    row_merged.sort(key=lambda t: t[1], reverse=True)
    top14 = sorted(row_merged[:14], key=lambda t: t[0])
    row_centers = [y for y, _ in top14]
    all_row_centers.append(row_centers)

    print(f"{img_path.name}: cols={col_centers}  rows(count={len(row_centers)})={row_centers}")

# ── Average across all images ──────────────────────────────────────────────────
print("\n=== Averaging across all images ===")

# Average column centers
valid_cols = [c for c in all_col_centers if len(c) == 3]
if valid_cols:
    avg_cols = [int(np.mean([c[i] for c in valid_cols])) for i in range(3)]
    print(f"Average column centers: {avg_cols}")
else:
    print("WARNING: Could not find 3 columns consistently")
    avg_cols = []

# Average row centers (only use images with exactly 14 rows)
valid_rows = [r for r in all_row_centers if len(r) == 14]
if valid_rows:
    avg_rows = [int(np.mean([r[i] for r in valid_rows])) for i in range(14)]
    print(f"Average row centers: {avg_rows}")
else:
    print(f"WARNING: Could not find 14 rows consistently. Counts: {[len(r) for r in all_row_centers]}")
    # Use the most common count
    from collections import Counter
    count = Counter(len(r) for r in all_row_centers)
    print(f"Row count distribution: {count}")
    avg_rows = []

# ── Compute margins from centers ───────────────────────────────────────────────
if avg_cols and avg_rows:
    # Estimate cell size from spacing
    col_spacings = [avg_cols[i+1] - avg_cols[i] for i in range(len(avg_cols)-1)]
    row_spacings = [avg_rows[i+1] - avg_rows[i] for i in range(len(avg_rows)-1)]

    avg_col_spacing = int(np.mean(col_spacings))
    avg_row_spacing = int(np.mean(row_spacings))

    # Cell size is roughly spacing - gap
    # Estimate cell width from the column projection width
    # Use half-spacing as approximate cell half-width
    cell_w_est = avg_col_spacing - 10  # subtract estimated gap
    cell_h_est = avg_row_spacing - 5

    # Margins: first cell center minus half cell size
    margin_left = avg_cols[0] - cell_w_est // 2
    margin_right = FORM_W - avg_cols[-1] - cell_w_est // 2
    margin_top = avg_rows[0] - cell_h_est // 2
    margin_bottom = FORM_H - avg_rows[-1] - cell_h_est // 2

    col_gap = avg_col_spacing - cell_w_est
    row_gap = avg_row_spacing - cell_h_est

    print(f"\n=== Calibrated config values ===")
    print(f"MARGIN_LEFT   = {margin_left}")
    print(f"MARGIN_RIGHT  = {margin_right}")
    print(f"MARGIN_TOP    = {margin_top}")
    print(f"MARGIN_BOTTOM = {margin_bottom}")
    print(f"COL_GAP       = {col_gap}")
    print(f"ROW_GAP       = {row_gap}")
    print(f"(cell_w≈{cell_w_est}, cell_h≈{cell_h_est})")
    print(f"(col_spacing≈{avg_col_spacing}, row_spacing≈{avg_row_spacing})")

    # ── Generate annotated image with calibrated grid ──────────────────────────
    raw = cv2.imread(str(images[-1]))
    aligned = aligner.align_image(raw)
    vis = aligned.copy()

    # Draw calibrated cell boxes
    for ri, cy in enumerate(avg_rows):
        for ci, cx in enumerate(avg_cols):
            x1 = cx - cell_w_est // 2
            y1 = cy - cell_h_est // 2
            x2 = cx + cell_w_est // 2
            y2 = cy + cell_h_est // 2

            gray_r = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
            region = gray_r[max(y1,0):min(y2,FORM_H), max(x1,0):min(x2,FORM_W)]
            if region.size > 0:
                _, bin_r = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                density = cv2.countNonZero(bin_r) / bin_r.size
            else:
                density = 0.0

            color = (0, 200, 0) if density >= 0.08 else (0, 0, 255)
            cv2.rectangle(vis, (max(x1,0), max(y1,0)), (min(x2,FORM_W), min(y2,FORM_H)), color, 2)
            cv2.putText(vis, f"R{ri+1}C{ci+1}", (max(x1,0)+2, max(y1,0)+12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255,200,0), 1)
            cv2.putText(vis, f"{density:.2f}", (max(x1,0)+2, max(y1,0)+24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3,
                        (0,200,0) if density >= 0.08 else (180,180,180), 1)

    # Draw column center lines
    for cx in avg_cols:
        cv2.line(vis, (cx, 0), (cx, FORM_H), (0, 255, 255), 1)
    # Draw row center lines
    for cy in avg_rows:
        cv2.line(vis, (0, cy), (FORM_W, cy), (255, 0, 255), 1)

    out = OUT_DIR / "calibrated_grid.jpg"
    cv2.imwrite(str(out), vis)
    print(f"\nSaved calibrated grid image: {out}")

    # ── Print density matrix with calibrated grid ──────────────────────────────
    print("\n=== Density matrix with calibrated grid (last image) ===")
    gray_a = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
    for ri, cy in enumerate(avg_rows):
        row_d = []
        for ci, cx in enumerate(avg_cols):
            x1 = max(cx - cell_w_est // 2, 0)
            y1 = max(cy - cell_h_est // 2, 0)
            x2 = min(cx + cell_w_est // 2, FORM_W)
            y2 = min(cy + cell_h_est // 2, FORM_H)
            region = gray_a[y1:y2, x1:x2]
            if region.size > 0:
                _, bin_r = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                d = cv2.countNonZero(bin_r) / bin_r.size
            else:
                d = 0.0
            row_d.append(round(d, 3))
        winner = max(range(3), key=lambda i: row_d[i])
        labels = ["Somewhat", "No", "Yes"]  # col0=S, col1=N, col2=Y (RTL form)
        ans = labels[winner] if row_d[winner] >= 0.06 else "Invalid"
        print(f"  Q{ri+1:02d}: {ans:8s}  {row_d}")
