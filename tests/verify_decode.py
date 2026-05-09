"""
Run the real decode_form() path (same as the app) on all Data Structure Forms
and print results. Also generates annotated debug images using the preprocessed
image so we can see exactly what the density calculation sees.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np

from checkbox_reader import CheckboxReader
from config import Config
from image_aligner import ImageAligner

FORM_DIR = Path(__file__).resolve().parent.parent / "Data Structure Forms"
OUT_DIR  = Path(__file__).resolve().parent.parent / "debug"
OUT_DIR.mkdir(exist_ok=True)

aligner = ImageAligner()
reader  = CheckboxReader(Config())

images = sorted(FORM_DIR.glob("*.jpg"))

for img_path in images:
    raw = cv2.imread(str(img_path))
    aligned = aligner.align_image(raw)
    if aligned is None:
        print(f"{img_path.name}: alignment failed")
        continue

    # ── Real decode path ───────────────────────────────────────────────────────
    answers = reader.decode_form(aligned)
    grid    = reader.read_checkbox_grid(aligned)

    print(f"\n{'='*60}")
    print(f"File: {img_path.name}")
    print(f"{'Q':>4}  {'Answer':10}  {'col0(S)':>9}  {'col1(N)':>9}  {'col2(Y)':>9}")
    print(f"{'-'*55}")
    for i, (ans, row) in enumerate(zip(answers, grid), start=1):
        flag = " <<<" if ans == "Invalid" else ""
        print(f"  Q{i:02d}  {ans:10}  {row[0]:9.4f}  {row[1]:9.4f}  {row[2]:9.4f}{flag}")

    invalid_count = answers.count("Invalid")
    print(f"\n  Invalid count: {invalid_count}/14")

    # ── Annotated image using preprocessed grayscale ───────────────────────────
    preprocessed = reader.preprocess_for_omr(aligned)
    vis = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2BGR)

    cfg = reader.config
    for row_i in range(cfg.ROW_COUNT):
        for col_i in range(cfg.COLUMN_COUNT):
            x1, y1, x2, y2 = reader.get_checkbox_bounds(row_i, col_i)
            x1c = max(x1, 0); y1c = max(y1, 0)
            x2c = min(x2, cfg.FORM_WIDTH); y2c = min(y2, cfg.FORM_HEIGHT)

            d = grid[row_i][col_i]
            color = (0, 200, 0) if d >= cfg.CHECKBOX_THRESHOLD else (0, 0, 255)
            cv2.rectangle(vis, (x1c, y1c), (x2c, y2c), color, 2)
            cv2.putText(vis, f"{d:.3f}", (x1c+2, y1c+14),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                        (0, 200, 0) if d >= cfg.CHECKBOX_THRESHOLD else (100, 100, 255), 1)

    # Label answers on the right side
    for i, ans in enumerate(answers):
        y = reader.get_checkbox_bounds(i, 0)[1] + 20
        color = (0, 200, 0) if ans != "Invalid" else (0, 0, 255)
        cv2.putText(vis, f"Q{i+1}: {ans}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

    out = OUT_DIR / f"decode_{img_path.stem}.jpg"
    cv2.imwrite(str(out), vis)
    print(f"  Saved: {out.name}")
