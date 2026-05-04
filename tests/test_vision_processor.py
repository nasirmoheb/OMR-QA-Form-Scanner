"""Unit tests for the VisionProcessor class."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np
import pytest

from vision_processor import VisionProcessor


# ------------------------------------------------------------------ #
#  Synthetic form helpers (re-use ImageAligner / CheckboxReader logic)
# ------------------------------------------------------------------ #

def make_full_synthetic_form(
    selections: list[int | None],
    width: int = 800,
    height: int = 1000,
) -> np.ndarray:
    """Create a synthetic aligned form with small corner markers and circular checkboxes."""
    img = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Small corner markers (centres near image edges → near-identity transform)
    ms = 18
    corners = [
        (0, 0),
        (width - 1, 0),
        (width - 1, height - 1),
        (0, height - 1),
    ]
    for cx, cy in corners:
        x1, y1 = max(cx - ms // 2, 0), max(cy - ms // 2, 0)
        x2, y2 = min(cx + ms // 2, width - 1), min(cy + ms // 2, height - 1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), -1)

    from checkbox_reader import CheckboxReader
    from config import Config

    reader = CheckboxReader(Config())
    for row, col in enumerate(selections):
        if col is None:
            continue
        x1, y1, x2, y2 = reader.get_checkbox_bounds(row, col)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        radius = min(x2 - x1, y2 - y1) // 2 - 2
        cv2.circle(img, (cx, cy), radius, (0, 0, 0), -1)
    # Add timing marks on the right edge
    for row in range(Config.ROW_COUNT):
        _, y1, _, y2 = reader.get_checkbox_bounds(row, 0)
        cy = (y1 + y2) // 2
        cv2.rectangle(img, (740, cy - 6), (780, cy + 6), (0, 0, 0), -1)
    return img


@pytest.fixture
def tmp_image(tmp_path: Path) -> Path:
    """Return path to a temporary folder."""
    return tmp_path


class TestValidateFormCount:
    def test_valid_four_markers(self):
        img = make_full_synthetic_form([0] * 14)
        vp = VisionProcessor()
        assert vp.validate_form_count(img) is True

    def test_no_markers(self):
        img = np.ones((1000, 800, 3), dtype=np.uint8) * 255
        vp = VisionProcessor()
        assert vp.validate_form_count(img) is False


class TestProcessForm:
    def test_process_valid_form(self, tmp_path: Path):
        img = make_full_synthetic_form([0, 1, 2, None] * 3 + [0, 1])
        path = tmp_path / "form_001.jpg"
        cv2.imwrite(str(path), img)

        vp = VisionProcessor()
        result = vp.process_form(path)

        assert result["Form_ID"] == "form_001"
        assert result["status"] == "ok"
        assert result["aligned"] is not None
        # All 14 question keys exist
        for i in range(1, 15):
            assert f"Q{i}" in result
        assert 0.0 <= result["Form_Score"] <= 100.0

    def test_process_missing_file(self, tmp_path: Path):
        vp = VisionProcessor()
        result = vp.process_form(tmp_path / "nonexistent.png")
        assert result["status"] == "load_error"
        assert result["Valid"] is False
        assert result["Form_Score"] == 0.0

    def test_process_bad_image(self, tmp_path: Path):
        # Empty white image — no markers
        img = np.ones((1000, 800, 3), dtype=np.uint8) * 255
        path = tmp_path / "bad.jpg"
        cv2.imwrite(str(path), img)

        vp = VisionProcessor()
        result = vp.process_form(path)
        assert result["status"] == "validation_failed"
        assert result["Valid"] is False


class TestComputeFormScore:
    def test_all_yes(self):
        score = VisionProcessor._compute_form_score(["Yes"] * 14)
        assert score == 100.0

    def test_all_no(self):
        score = VisionProcessor._compute_form_score(["No"] * 14)
        assert score == 0.0

    def test_mixed(self):
        answers = ["Yes", "Somewhat", "No", "Invalid"] * 3 + ["Yes", "Somewhat"]
        score = VisionProcessor._compute_form_score(answers)
        # 3*(100+50+0) + 100 + 50 = 600  over 11 valid = ~54.545
        assert score == pytest.approx(600 / 11, abs=0.01)

    def test_all_invalid(self):
        score = VisionProcessor._compute_form_score(["Invalid"] * 14)
        assert score == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
