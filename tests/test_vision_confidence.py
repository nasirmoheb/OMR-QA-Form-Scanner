"""Tests for VisionProcessor confidence scoring methods.

Covers:
- calculate_row_confidence: single clear selection, at-threshold, no selection,
  multiple selections
- calculate_form_confidence: average, empty list, all zeros, mixed values

cv2 and numpy are mocked so this file can run without OpenCV installed.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Ensure src/ is on the path when running from the project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# Mock cv2 before importing vision_processor (only if not already available).
# We do NOT mock numpy globally because other test modules (e.g. pandas) need
# the real numpy.  cv2 is the only hard dependency that may be absent in CI.
_cv2_mock = MagicMock()
_cv2_mock.__version__ = "4.8.0"
if "cv2" not in sys.modules:
    sys.modules["cv2"] = _cv2_mock

# Import only the static methods we need — they don't touch cv2 at runtime.
from vision_processor import VisionProcessor  # noqa: E402


# ---------------------------------------------------------------------------
# calculate_row_confidence
# ---------------------------------------------------------------------------


class TestCalculateRowConfidence:
    """Tests for VisionProcessor.calculate_row_confidence."""

    def test_single_clear_selection_above_threshold(self) -> None:
        """One density well above threshold → confidence > 0.5."""
        threshold = 0.20
        # density = 0.40 = 2 * threshold → confidence should be 1.0
        densities = [0.40, 0.01, 0.02]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert confidence > 0.5, f"Expected > 0.5, got {confidence}"

    def test_single_selection_at_threshold(self) -> None:
        """One density exactly at threshold → confidence ≈ 0.5."""
        threshold = 0.20
        densities = [0.20, 0.01, 0.02]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert abs(confidence - 0.5) < 1e-9, f"Expected ~0.5, got {confidence}"

    def test_no_selection_below_threshold(self) -> None:
        """All densities below threshold → confidence == 0.0."""
        threshold = 0.20
        densities = [0.05, 0.03, 0.07]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert confidence == 0.0, f"Expected 0.0, got {confidence}"

    def test_multiple_selections_above_threshold(self) -> None:
        """Two densities above threshold → confidence == 0.0 (ambiguous)."""
        threshold = 0.20
        densities = [0.35, 0.40, 0.05]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert confidence == 0.0, f"Expected 0.0, got {confidence}"

    def test_confidence_clamped_to_one(self) -> None:
        """Density far above 2*threshold → confidence clamped to 1.0."""
        threshold = 0.20
        densities = [0.99, 0.01, 0.01]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert confidence == 1.0, f"Expected 1.0, got {confidence}"

    def test_all_zeros_no_selection(self) -> None:
        """All-zero densities → confidence == 0.0."""
        threshold = 0.20
        densities = [0.0, 0.0, 0.0]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert confidence == 0.0

    def test_single_selection_between_threshold_and_double(self) -> None:
        """Density between threshold and 2*threshold → 0.5 < confidence < 1.0."""
        threshold = 0.20
        # density = 0.30 → confidence = 0.30 / 0.40 = 0.75
        densities = [0.30, 0.01, 0.02]
        confidence = VisionProcessor.calculate_row_confidence(densities, threshold)
        assert 0.5 < confidence < 1.0, f"Expected between 0.5 and 1.0, got {confidence}"
        assert abs(confidence - 0.75) < 1e-9, f"Expected 0.75, got {confidence}"


# ---------------------------------------------------------------------------
# calculate_form_confidence
# ---------------------------------------------------------------------------


class TestCalculateFormConfidence:
    """Tests for VisionProcessor.calculate_form_confidence."""

    def test_average_of_row_confidences(self) -> None:
        """Returns the correct mean of a list of row confidences."""
        row_confidences = [0.8, 0.6, 1.0, 0.4]
        expected = sum(row_confidences) / len(row_confidences)
        result = VisionProcessor.calculate_form_confidence(row_confidences)
        assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"

    def test_empty_list_returns_zero(self) -> None:
        """Empty list → 0.0."""
        result = VisionProcessor.calculate_form_confidence([])
        assert result == 0.0, f"Expected 0.0, got {result}"

    def test_all_zeros_returns_zero(self) -> None:
        """All-zero row confidences → 0.0."""
        result = VisionProcessor.calculate_form_confidence([0.0, 0.0, 0.0])
        assert result == 0.0, f"Expected 0.0, got {result}"

    def test_mixed_values_correct_mean(self) -> None:
        """Mixed confidence values → correct mean."""
        row_confidences = [1.0, 0.5, 0.0, 0.75, 0.25]
        expected = 2.5 / 5  # = 0.5
        result = VisionProcessor.calculate_form_confidence(row_confidences)
        assert abs(result - expected) < 1e-9, f"Expected {expected}, got {result}"

    def test_single_value(self) -> None:
        """Single-element list → that value."""
        result = VisionProcessor.calculate_form_confidence([0.7])
        assert abs(result - 0.7) < 1e-9, f"Expected 0.7, got {result}"

    def test_all_ones_returns_one(self) -> None:
        """All-one row confidences → 1.0."""
        result = VisionProcessor.calculate_form_confidence([1.0] * 14)
        assert abs(result - 1.0) < 1e-9, f"Expected 1.0, got {result}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
