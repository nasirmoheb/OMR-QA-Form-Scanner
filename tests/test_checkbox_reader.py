"""Unit tests for the CheckboxReader class."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np
import pytest

from checkbox_reader import CheckboxReader, _cell_box
from config import Config


# ------------------------------------------------------------------ #
#  Synthetic image helpers
# ------------------------------------------------------------------ #

def make_aligned_form(
    selections: list[int | None], width: int = 800, height: int = 1000
) -> np.ndarray:
    """Create a synthetic aligned form with 14 rows x 3 columns.

    Args:
        selections: List of 14 items. Each item is ``0, 1, 2`` (column
            index) or ``None`` for no selection.
        width: Form width.
        height: Form height.

    Returns:
        Greyscale image with white background and black filled checkboxes.
    """
    img = np.ones((height, width), dtype=np.uint8) * 255
    reader = CheckboxReader(Config())

    for row, col in enumerate(selections):
        if col is None:
            continue
        x1, y1, x2, y2 = reader.get_checkbox_bounds(row, col)
        # Draw a filled black rectangle in the centre of the cell
        pad_x = (x2 - x1) // 8
        pad_y = (y2 - y1) // 8
        cv2.rectangle(
            img,
            (x1 + pad_x, y1 + pad_y),
            (x2 - pad_x, y2 - pad_y),
            0,
            -1,
        )
    _add_timing_marks(img)
    return img


def _add_timing_marks(img: np.ndarray) -> np.ndarray:
    """Draw solid black timing marks on the far-right edge (one per row)."""
    reader = CheckboxReader(Config())
    for row in range(Config.ROW_COUNT):
        _, y1, _, y2 = reader.get_checkbox_bounds(row, 0)
        cy = (y1 + y2) // 2
        my1 = max(0, cy - 6)
        my2 = min(img.shape[0], cy + 6)
        mx1 = max(0, img.shape[1] - 60)
        mx2 = min(img.shape[1], img.shape[1] - 10)
        cv2.rectangle(img, (mx1, my1), (mx2, my2), 0, -1)
    return img


def make_empty_form(width: int = 800, height: int = 1000) -> np.ndarray:
    """Return a blank white aligned form with timing marks."""
    img = np.ones((height, width), dtype=np.uint8) * 255
    return _add_timing_marks(img)


# ------------------------------------------------------------------ #
#  _cell_box tests
# ------------------------------------------------------------------ #


class TestCellBox:
    def test_top_left_cell(self):
        x1, y1, x2, y2 = _cell_box(0, 0, 800, 1000, 14, 3)
        assert x1 >= 0
        assert y1 >= 0
        assert x2 > x1
        assert y2 > y1

    def test_bottom_right_cell(self):
        x1, y1, x2, y2 = _cell_box(13, 2, 800, 1000, 14, 3)
        assert x2 <= 800
        assert y2 <= 1000
        assert x2 > x1
        assert y2 > y1


# ------------------------------------------------------------------ #
#  calculate_pixel_density tests
# ------------------------------------------------------------------ #


class TestCalculatePixelDensity:
    def test_all_white_region(self):
        white = np.full((50, 50), 255, dtype=np.uint8)
        assert CheckboxReader.calculate_pixel_density(white) == pytest.approx(0.0, abs=1e-6)

    def test_all_black_region(self):
        black = np.zeros((50, 50), dtype=np.uint8)
        assert CheckboxReader.calculate_pixel_density(black) == pytest.approx(1.0, abs=1e-6)

    def test_half_black_region(self):
        half = np.zeros((50, 50), dtype=np.uint8)
        half[:, :25] = 255
        density = CheckboxReader.calculate_pixel_density(half)
        assert density == pytest.approx(0.5, abs=0.05)

    def test_color_region(self):
        bgr = np.full((50, 50, 3), 255, dtype=np.uint8)
        assert CheckboxReader.calculate_pixel_density(bgr) == pytest.approx(0.0, abs=1e-6)

    def test_empty_region(self):
        empty = np.array([], dtype=np.uint8).reshape(0, 0)
        assert CheckboxReader.calculate_pixel_density(empty) == 0.0


# ------------------------------------------------------------------ #
#  read_checkbox_grid tests
# ------------------------------------------------------------------ #


class TestReadCheckboxGrid:
    def test_empty_form_all_zeros(self):
        img = make_empty_form()
        reader = CheckboxReader()
        grid = reader.read_checkbox_grid(img)
        assert len(grid) == 14
        for row in grid:
            assert len(row) == 3
            for d in row:
                assert d < Config.CHECKBOX_THRESHOLD

    def test_first_row_first_column_filled(self):
        selections = [0] + [None] * 13
        img = make_aligned_form(selections)
        reader = CheckboxReader()
        grid = reader.read_checkbox_grid(img)
        assert grid[0][0] > Config.CHECKBOX_THRESHOLD
        assert grid[0][1] < Config.CHECKBOX_THRESHOLD
        assert grid[0][2] < Config.CHECKBOX_THRESHOLD
        # All other rows empty
        for r in range(1, 14):
            for c in range(3):
                assert grid[r][c] < Config.CHECKBOX_THRESHOLD

    def test_multiple_rows_filled(self):
        selections = [0, 1, 2, None, 0, 1, 2, None, 0, 1, 2, None, 0, 1]
        img = make_aligned_form(selections)
        reader = CheckboxReader()
        grid = reader.read_checkbox_grid(img)
        for row, col in enumerate(selections):
            if col is not None:
                assert grid[row][col] > Config.CHECKBOX_THRESHOLD
                # Other columns in the same row should be low
                for other in range(3):
                    if other != col:
                        assert grid[row][other] < Config.CHECKBOX_THRESHOLD
            else:
                for c in range(3):
                    assert grid[row][c] < Config.CHECKBOX_THRESHOLD


# ------------------------------------------------------------------ #
#  determine_selection tests
# ------------------------------------------------------------------ #


class TestDetermineSelection:
    def test_no_selection(self):
        reader = CheckboxReader()
        assert reader.determine_selection([0.1, 0.05, 0.02]) == "Invalid"

    def test_single_selection_yes(self):
        reader = CheckboxReader()
        assert reader.determine_selection([0.9, 0.05, 0.02]) == "Yes"

    def test_single_selection_somewhat(self):
        reader = CheckboxReader()
        assert reader.determine_selection([0.05, 0.9, 0.02]) == "Somewhat"

    def test_single_selection_no(self):
        reader = CheckboxReader()
        assert reader.determine_selection([0.05, 0.02, 0.9]) == "No"

    def test_multiple_selections(self):
        reader = CheckboxReader()
        assert reader.determine_selection([0.9, 0.9, 0.02]) == "Invalid"

    def test_all_three_selected(self):
        reader = CheckboxReader()
        assert reader.determine_selection([0.9, 0.9, 0.9]) == "Invalid"

    def test_edge_case_at_threshold(self):
        reader = CheckboxReader()
        # Exactly at threshold counts as "above"
        threshold = Config.CHECKBOX_THRESHOLD
        assert reader.determine_selection([threshold, 0.0, 0.0]) == "Yes"


# ------------------------------------------------------------------ #
#  decode_form integration tests
# ------------------------------------------------------------------ #


class TestDecodeForm:
    def test_decode_all_yes(self):
        selections = [0] * 14
        img = make_aligned_form(selections)
        reader = CheckboxReader()
        answers = reader.decode_form(img)
        assert answers == ["Yes"] * 14

    def test_decode_mixed(self):
        selections = [0, 1, 2, None, 0, 1, 2, None, 0, 1, 2, None, 0, 1]
        img = make_aligned_form(selections)
        reader = CheckboxReader()
        answers = reader.decode_form(img)
        expected = ["Yes", "Somewhat", "No", "Invalid"] * 3 + ["Yes", "Somewhat"]
        assert answers == expected

    def test_decode_empty_form(self):
        img = make_empty_form()
        reader = CheckboxReader()
        answers = reader.decode_form(img)
        assert answers == ["Invalid"] * 14


# ------------------------------------------------------------------ #
#  Timing mark detection tests
# ------------------------------------------------------------------ #


class TestDetectTimingMarks:
    def test_detect_all_14(self):
        img = make_empty_form()
        reader = CheckboxReader()
        marks = reader.detect_timing_marks(img)
        assert marks is not None
        assert len(marks) == 14
        # Should be sorted top-to-bottom
        assert marks == sorted(marks)

    def test_too_few_returns_none(self):
        img = np.ones((1000, 800), dtype=np.uint8) * 255
        # Draw only 3 marks
        for cy in [300, 500, 700]:
            cv2.rectangle(img, (740, cy - 6), (780, cy + 6), 0, -1)
        reader = CheckboxReader()
        assert reader.detect_timing_marks(img) is None

    def test_grid_uses_timing_marks(self):
        selections = [0, 1, 2, None, 0, 1, 2, None, 0, 1, 2, None, 0, 1]
        img = make_aligned_form(selections)
        reader = CheckboxReader()
        grid = reader.read_checkbox_grid(img)
        assert len(grid) == 14
        for row, col in enumerate(selections):
            if col is not None:
                assert grid[row][col] > Config.CHECKBOX_THRESHOLD
                for other in range(3):
                    if other != col:
                        assert grid[row][other] < Config.CHECKBOX_THRESHOLD
            else:
                for c in range(3):
                    assert grid[row][c] < Config.CHECKBOX_THRESHOLD


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
