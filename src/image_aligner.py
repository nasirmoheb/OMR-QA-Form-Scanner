"""Vision processing: detect fiducial markers and align scanned forms."""

from typing import Any

import cv2
import numpy as np

from config import Config, setup_logging

logger = setup_logging()


class ImageAligner:
    """Detects corner fiducial markers and applies perspective correction."""

    def __init__(self, config: Config | None = None) -> None:
        """Initialize with configuration.

        Args:
            config: Application configuration instance. Uses global defaults
                when ``None``.
        """
        self.config = config or Config()

    # ------------------------------------------------------------------ #
    #  Fiducial marker detection
    # ------------------------------------------------------------------ #

    def detect_fiducial_markers(
        self, image: np.ndarray
    ) -> tuple[list[tuple[int, int]], str]:
        """Detect black corner fiducial markers via contour analysis.

        Args:
            image: Input image (BGR or greyscale).

        Returns:
            Tuple of ``(marker_centers, status)`` where *status* is
            ``"ok"``, ``"too_few"``, or ``"too_many"``.
        """
        # Ensure greyscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Binary invert so black markers become white blobs
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Use RETR_LIST so nested contours (inside a border frame) are found
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )

        candidates: list[tuple[int, int, float, float]] = []
        h, w = gray.shape
        img_area = h * w

        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Reject tiny noise and huge background shapes
            # Upper bound tightened to 1% of image area to exclude large
            # structural elements (borders, text blocks, checkbox grids)
            if area < 50 or area > img_area * 0.01:
                continue

            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue

            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            # Accept 4-sided (square/rectangle) or circular-ish shapes
            if len(approx) not in (3, 4):
                continue

            # Compute solidity to reject weird slivers
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            if hull_area == 0:
                continue
            solidity = area / hull_area
            if solidity < 0.8:
                continue

            moments = cv2.moments(cnt)
            if moments["m00"] == 0:
                continue
            cx = int(moments["m10"] / moments["m00"])
            cy = int(moments["m01"] / moments["m00"])
            candidates.append((cx, cy, area, solidity))

        # Keep only the 4 candidates closest to the image corners.
        # This filters out checkbox cells and other small rectangles that
        # pass the shape test but are not fiducial markers.
        if len(candidates) >= 4:
            corners_ref = [
                (0, 0),
                (w - 1, 0),
                (0, h - 1),
                (w - 1, h - 1),
            ]
            corner_picks: list[tuple[int, int, float, float]] = []
            used: set[int] = set()
            for ref_x, ref_y in corners_ref:
                best_idx = -1
                best_dist = float("inf")
                for i, (cx, cy, area, sol) in enumerate(candidates):
                    if i in used:
                        continue
                    dist = (cx - ref_x) ** 2 + (cy - ref_y) ** 2
                    if dist < best_dist:
                        best_dist = dist
                        best_idx = i
                if best_idx >= 0:
                    corner_picks.append(candidates[best_idx])
                    used.add(best_idx)
            candidates = corner_picks

        # Sort by area descending and keep top candidates
        candidates.sort(key=lambda x: x[2], reverse=True)

        if len(candidates) < 4:
            logger.warning(
                "Only %d fiducial marker(s) found (need 4).", len(candidates)
            )
            centers = [(int(c[0]), int(c[1])) for c in candidates]
            return centers, "too_few"

        if len(candidates) > 4:
            logger.info(
                "%d candidates found; keeping largest 4.", len(candidates)
            )
            candidates = candidates[:4]
            status = "too_many"
        else:
            status = "ok"

        centers = [(int(c[0]), int(c[1])) for c in candidates]
        return centers, status

    # ------------------------------------------------------------------ #
    #  Perspective transform
    # ------------------------------------------------------------------ #

    @staticmethod
    def _order_points(pts: list[tuple[int, int]]) -> np.ndarray:
        """Order 4 points as top-left, top-right, bottom-right, bottom-left.

        Args:
            pts: List of (x, y) centre coordinates.

        Returns:
            4x2 NumPy array in the canonical order.
        """
        pts_arr = np.array(pts, dtype="float32")
        s = pts_arr.sum(axis=1)
        diff = np.diff(pts_arr, axis=1)

        # top-left  = smallest sum
        # bottom-right = largest sum
        # top-right   = smallest diff (x - y)
        # bottom-left = largest diff
        tl = pts_arr[np.argmin(s)]
        br = pts_arr[np.argmax(s)]
        tr = pts_arr[np.argmin(diff)]
        bl = pts_arr[np.argmax(diff)]
        return np.array([tl, tr, br, bl], dtype="float32")

    def calculate_perspective_transform(
        self, markers: list[tuple[int, int]]
    ) -> np.ndarray | None:
        """Compute the 3x3 perspective transform matrix.

        Args:
            markers: Exactly 4 (x, y) marker centres.

        Returns:
            3x3 perspective transform matrix, or ``None`` if fewer
            than 4 markers were supplied.
        """
        if len(markers) != 4:
            logger.error(
                "Need exactly 4 markers for perspective transform, got %d.",
                len(markers),
            )
            return None

        src = self._order_points(markers)
        dst = np.array(
            [
                [0, 0],
                [self.config.FORM_WIDTH - 1, 0],
                [self.config.FORM_WIDTH - 1, self.config.FORM_HEIGHT - 1],
                [0, self.config.FORM_HEIGHT - 1],
            ],
            dtype="float32",
        )

        matrix = cv2.getPerspectiveTransform(src, dst)
        return matrix

    def align_image(
        self, image: np.ndarray, matrix: np.ndarray | None = None
    ) -> np.ndarray | None:
        """Warp *image* to the standard form size.

        Args:
            image: Input image.
            matrix: Pre-computed perspective matrix. When ``None`` the
                method detects markers and computes the matrix itself.

        Returns:
            Aligned image (``FORM_WIDTH x FORM_HEIGHT``) or ``None`` if
            alignment is impossible.
        """
        if matrix is None:
            markers, status = self.detect_fiducial_markers(image)
            if status == "too_few" or len(markers) != 4:
                return None
            matrix = self.calculate_perspective_transform(markers)
            if matrix is None:
                return None

        aligned = cv2.warpPerspective(
            image,
            matrix,
            (self.config.FORM_WIDTH, self.config.FORM_HEIGHT),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255),
        )
        return aligned
