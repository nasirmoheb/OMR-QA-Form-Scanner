"""Unit tests for the ImageAligner class."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import cv2
import numpy as np
import pytest

from image_aligner import ImageAligner


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def make_synthetic_image(
    width: int = 1200,
    height: int = 1600,
    marker_centers: list[tuple[int, int]] | None = None,
    marker_size: int = 40,
) -> np.ndarray:
    """Create a white image with black square markers at given centres."""
    img = np.ones((height, width), dtype=np.uint8) * 255
    if marker_centers is None:
        # Default 4 corners
        margin = 80
        marker_centers = [
            (margin, margin),
            (width - margin, margin),
            (width - margin, height - margin),
            (margin, height - margin),
        ]
    half = marker_size // 2
    for cx, cy in marker_centers:
        x1, y1 = max(cx - half, 0), max(cy - half, 0)
        x2, y2 = min(cx + half, width), min(cy + half, height)
        cv2.rectangle(img, (x1, y1), (x2, y2), 0, -1)
    return img


def add_noise_markers(
    img: np.ndarray, centers: list[tuple[int, int]], size: int = 20
) -> np.ndarray:
    """Inject extra small black squares as distractors."""
    half = size // 2
    h, w = img.shape
    for cx, cy in centers:
        x1, y1 = max(cx - half, 0), max(cy - half, 0)
        x2, y2 = min(cx + half, w), min(cy + half, h)
        cv2.rectangle(img, (x1, y1), (x2, y2), 0, -1)
    return img


# ------------------------------------------------------------------ #
#  Tests
# ------------------------------------------------------------------ #


class TestDetectFiducialMarkers:
    def test_detect_four_markers(self):
        img = make_synthetic_image()
        aligner = ImageAligner()
        centers, status = aligner.detect_fiducial_markers(img)
        assert status == "ok"
        assert len(centers) == 4

    def test_detect_too_few(self):
        img = make_synthetic_image(marker_centers=[(100, 100), (200, 200)])
        aligner = ImageAligner()
        centers, status = aligner.detect_fiducial_markers(img)
        assert status == "too_few"
        assert len(centers) == 2

    def test_detect_too_many_keeps_four_largest(self):
        base = [(80, 80), (1120, 80), (1120, 1520), (80, 1520)]
        img = make_synthetic_image(marker_centers=base, marker_size=50)
        # Add tiny distractors far from corners
        noise = [(400, 400), (800, 800), (600, 1200)]
        img = add_noise_markers(img, noise, size=15)
        aligner = ImageAligner()
        centers, status = aligner.detect_fiducial_markers(img)
        assert status == "too_many"
        assert len(centers) == 4
        # The four large corner markers should survive
        for expected in base:
            assert any(
                abs(c[0] - expected[0]) < 10 and abs(c[1] - expected[1]) < 10
                for c in centers
            )

    def test_detect_with_color_image(self):
        gray = make_synthetic_image()
        bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        aligner = ImageAligner()
        centers, status = aligner.detect_fiducial_markers(bgr)
        assert status == "ok"
        assert len(centers) == 4


class TestOrderPoints:
    def test_order_points_standard(self):
        raw = [(50, 50), (750, 50), (750, 950), (50, 950)]  # TL TR BR BL
        aligner = ImageAligner()
        ordered = aligner._order_points(raw)
        expected = np.array(
            [[50, 50], [750, 50], [750, 950], [50, 950]], dtype="float32"
        )
        np.testing.assert_array_almost_equal(ordered, expected)

    def test_order_points_shuffled(self):
        raw = [(750, 950), (50, 50), (50, 950), (750, 50)]  # random order
        aligner = ImageAligner()
        ordered = aligner._order_points(raw)
        expected = np.array(
            [[50, 50], [750, 50], [750, 950], [50, 950]], dtype="float32"
        )
        np.testing.assert_array_almost_equal(ordered, expected)


class TestCalculatePerspectiveTransform:
    def test_transform_with_four_markers(self):
        aligner = ImageAligner()
        markers = [(50, 50), (750, 50), (750, 950), (50, 950)]
        matrix = aligner.calculate_perspective_transform(markers)
        assert matrix is not None
        assert matrix.shape == (3, 3)

    def test_transform_with_fewer_than_four(self):
        aligner = ImageAligner()
        markers = [(50, 50), (750, 50), (750, 950)]
        matrix = aligner.calculate_perspective_transform(markers)
        assert matrix is None


class TestAlignImage:
    def test_align_success(self):
        aligner = ImageAligner()
        img = make_synthetic_image()
        aligned = aligner.align_image(img)
        assert aligned is not None
        h, w = aligned.shape[:2]
        assert w == 800
        assert h == 1000

    def test_align_with_precomputed_matrix(self):
        aligner = ImageAligner()
        img = make_synthetic_image()
        markers, _ = aligner.detect_fiducial_markers(img)
        matrix = aligner.calculate_perspective_transform(markers)
        aligned = aligner.align_image(img, matrix=matrix)
        assert aligned is not None
        h, w = aligned.shape[:2]
        assert w == 800
        assert h == 1000

    def test_align_too_few_markers(self):
        aligner = ImageAligner()
        img = make_synthetic_image(marker_centers=[(100, 100)])
        aligned = aligner.align_image(img)
        assert aligned is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
