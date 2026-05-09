"""
Debug script: visualize grid placement on aligned forms.

Generates two annotated images per input:
  - *_current.jpg  : grid using current config.py margins (broken)
  - *_calibrate.jpg: grid using calibrate_grid.py margins (candidate fix)

Run:
    python tests/debug_grid_margins.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np

from image_aligner import ImageAligner

# ── Margin sets to compare ────────────────────────────────────────────────────

CONFIGS = {
    "current": dict(
        margin_left=320,
        margin_right=690,
        margin_top=360,
        margin_bottom=445,
        col_gap=20,
        row_gap=20,
    ),
    "calibrate": dict(
        margin_left=300,   # calibrate_grid.py starting point
        margin_right=100,
        margin_top=240,
        margin_bottom=130,
        col_gap=30,
        row_gap=5,
    ),
}

ROWS = 14
COLS = 3
FORM_W = 1240
FORM_H = 1754

# ── Helpers ───────────────────────────────────────────────────────────────────

def cell_box(row, col, cfg):
    ml = cfg["margin_left"]
    mr = cfg["margin_right"]
    mt = cfg["margin_top"]
    mb = cfg["margin_bottom"]
    cg = cfg["col_gap"]
    rg = cfg["row_gap"]

    usable_w = FORM_W - ml - mr
    usable_h = FORM_H - mt - mb
    cell_w = (usable_w - (COLS - 1) * cg) // COLS
    cell_h = (usable_h - (ROWS - 1) * rg) // ROWS

    x1 = ml + col * (cell_w + cg)
    y1 = mt + row * (cell_h + rg)
    return x1, y1, x1 + cell_w, y1 + cell_h


def annotate(aligned: np.ndarray, cfg: dict, label: str) -> np.ndarray:
    vis = aligned.copy()
    gray = cv2.cvtColor(vis, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    ml = cfg["margin_left"]
    mr = cfg["margin_right"]
    mt = cfg["margin_top"]
    mb = cfg["margin_bottom"]

    # Draw margin boundary rectangle (yellow)
    cv2.rectangle(vis, (ml, mt), (w - mr, h - mb), (0, 220, 220), 2)
    cv2.putText(vis, f"Usable area  W={w-ml-mr}  H={h-mt-mb}",
                (ml, mt - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 220), 1)

    for row in range(ROWS):
        for col in range(COLS):
            x1, y1, x2, y2 = cell_box(row, col, cfg)
            x1c, y1c = max(x1, 0), max(y1, 0)
            x2c, y2c = min(x2, w), min(y2, h)

            region = gray[y1c:y2c, x1c:x2c]
            if region.size == 0:
                density = 0.0
            else:
                _, binary = cv2.threshold(
                    region, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
                )
                density = cv2.countNonZero(binary) / binary.size

            # Red box, blue density label; green if density looks like a mark
            color = (0, 200, 0) if density >= 0.08 else (0, 0, 255)
            cv2.rectangle(vis, (x1c, y1c), (x2c, y2c), color, 1)
            cv2.putText(vis, f"{density:.2f}",
                        (x1c + 2, y1c + 14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                        (255, 100, 0) if density >= 0.08 else (180, 180, 180), 1)

    # Config label top-left
    cv2.putText(vis, label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    return vis


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    forms_dir = Path(__file__).resolve().parent.parent / "Data Structure Forms"
    out_dir   = Path(__file__).resolve().parent.parent / "debug"
    out_dir.mkdir(exist_ok=True)

    images = sorted(forms_dir.glob("*.jpg")) + sorted(forms_dir.glob("*.jpeg")) + sorted(forms_dir.glob("*.png"))
    if not images:
        print(f"No images found in {forms_dir}")
        sys.exit(1)

    aligner = ImageAligner()

    for img_path in images:
        print(f"\nProcessing: {img_path.name}")
        raw = cv2.imread(str(img_path))
        if raw is None:
            print(f"  Could not read image, skipping.")
            continue

        markers, status = aligner.detect_fiducial_markers(raw)
        print(f"  Markers ({len(markers)}): {markers}  status={status}")

        aligned = aligner.align_image(raw)
        if aligned is None:
            print("  Alignment failed, skipping.")
            continue

        print(f"  Aligned size: {aligned.shape[1]} x {aligned.shape[0]}")

        for cfg_name, cfg in CONFIGS.items():
            vis = annotate(aligned, cfg, cfg_name)
            out_path = out_dir / f"margins_{img_path.stem}_{cfg_name}.jpg"
            cv2.imwrite(str(out_path), vis)
            print(f"  Saved: {out_path.name}")

        # Also save the raw aligned image for reference
        raw_out = out_dir / f"aligned_{img_path.stem}.jpg"
        cv2.imwrite(str(raw_out), aligned)
        print(f"  Saved: {raw_out.name}")

    print("\nDone. Check the debug/ folder.")


if __name__ == "__main__":
    main()
