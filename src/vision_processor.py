"""High-level vision pipeline that orchestrates alignment and checkbox reading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from checkbox_reader import CheckboxReader
from config import Config, setup_logging
from image_aligner import ImageAligner

logger = setup_logging()


class VisionProcessor:
    """Orchestrates form image loading, alignment, and checkbox decoding."""

    def __init__(
        self,
        aligner: ImageAligner | None = None,
        reader: CheckboxReader | None = None,
        config: Config | None = None,
    ) -> None:
        """Initialize with optional component instances.

        Args:
            aligner: ``ImageAligner`` instance. A new one is created when
                ``None``.
            reader: ``CheckboxReader`` instance. A new one is created when
                ``None``.
            config: Shared configuration. Used by sub-components when they
                are created internally.
        """
        self.config = config or Config()
        self.aligner = aligner or ImageAligner(self.config)
        self.reader = reader or CheckboxReader(self.config)

    # ------------------------------------------------------------------ #
    #  Validation helper
    # ------------------------------------------------------------------ #

    def validate_form_count(self, image: np.ndarray) -> bool:
        """Return whether *image* contains enough fiducial markers.

        Args:
            image: Raw input image (BGR or greyscale).

        Returns:
            ``True`` if at least 4 markers are detected (the aligner
            keeps the 4 largest when extras are present).
        """
        _centers, status = self.aligner.detect_fiducial_markers(image)
        return status in ("ok", "too_many")

    # ------------------------------------------------------------------ #
    #  Single-form processing
    # ------------------------------------------------------------------ #

    def process_form(
        self, image_path: str | Path
    ) -> dict[str, Any]:
        """Load, align, and decode a single form image.

        Args:
            image_path: Path to the image file.

        Returns:
            Dictionary with keys ``Form_ID``, ``Q1``..``Q14``,
            ``Form_Score``, ``Valid``, and metadata keys
            ``aligned`` and ``status``.
        """
        path = Path(image_path)
        result: dict[str, Any] = {
            "Form_ID": path.stem,
            "Valid": False,
            "status": "unknown",
            "aligned": None,
        }

        # --- load ------------------------------------------------------ #
        image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if image is None:
            logger.error("Failed to load image: %s", path)
            result["status"] = "load_error"
            for i in range(1, Config.ROW_COUNT + 1):
                result[f"Q{i}"] = "Invalid"
            result["Form_Score"] = 0.0
            return result

        # --- validate / align ------------------------------------------ #
        if not self.validate_form_count(image):
            logger.warning("Form %s did not pass validation (markers).", path.name)
            result["status"] = "validation_failed"
            for i in range(1, Config.ROW_COUNT + 1):
                result[f"Q{i}"] = "Invalid"
            result["Form_Score"] = 0.0
            return result

        aligned = self.aligner.align_image(image)
        if aligned is None:
            logger.warning("Form %s alignment failed.", path.name)
            result["status"] = "alignment_failed"
            for i in range(1, Config.ROW_COUNT + 1):
                result[f"Q{i}"] = "Invalid"
            result["Form_Score"] = 0.0
            return result

        result["aligned"] = aligned
        result["status"] = "ok"

        # --- read checkboxes ------------------------------------------- #
        answers = self.reader.decode_form(aligned)
        for i, ans in enumerate(answers, start=1):
            result[f"Q{i}"] = ans

        # --- compute form score ---------------------------------------- #
        score = self._compute_form_score(answers)
        result["Form_Score"] = score
        result["Valid"] = score > 0.0  # at least one valid answer

        logger.info("Processed %s -> score %.1f", path.name, score)
        return result

    # ------------------------------------------------------------------ #
    #  Score helper (preliminary; AnalyticsEngine will refine later)
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_form_score(answers: list[str]) -> float:
        """Return a simple score: valid answers only.

        This is a preliminary score used for validity flagging.
        The analytics layer recalculates the official score.

        Args:
            answers: 14 answer strings.

        Returns:
            Percentage-like score (0..100) based on valid selections.
        """
        weights = {"Yes": 100, "Somewhat": 50, "No": 0}
        valid = [a for a in answers if a in weights]
        if not valid:
            return 0.0
        total = sum(weights[a] for a in valid)
        return total / len(valid)
