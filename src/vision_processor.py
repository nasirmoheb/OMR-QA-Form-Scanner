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
    #  Confidence scoring
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_row_confidence(densities: list[float], threshold: float) -> float:
        """Calculate a confidence score for a single row's checkbox densities.

        Args:
            densities: List of density values for each column in the row.
            threshold: The checkbox detection threshold.

        Returns:
            Confidence score in [0.0, 1.0]:
            - 0.0 if no checkbox is above threshold (no selection)
            - 0.0 if more than one checkbox is above threshold (ambiguous)
            - ``min(1.0, max(above) / (threshold * 2))`` if exactly one
              checkbox is above threshold (clear selection)
        """
        above = [d for d in densities if d >= threshold]
        if len(above) == 0:
            return 0.0
        if len(above) > 1:
            return 0.0
        # Exactly one selection: scale so that density == threshold gives 0.5
        # and density == 2*threshold gives 1.0
        return min(1.0, max(above) / (threshold * 2))

    @staticmethod
    def calculate_form_confidence(row_confidences: list[float]) -> float:
        """Calculate the overall form confidence as the mean of row confidences.

        Args:
            row_confidences: Per-row confidence scores.

        Returns:
            Mean confidence in [0.0, 1.0], or 0.0 for an empty list.
        """
        if not row_confidences:
            return 0.0
        return sum(row_confidences) / len(row_confidences)

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
            ``Form_Score``, ``Valid``, ``densities``,
            ``row_confidences``, ``form_confidence``, and metadata keys
            ``aligned`` and ``status``.
        """
        path = Path(image_path)
        result: dict[str, Any] = {
            "Form_ID": path.stem,
            "Valid": False,
            "status": "unknown",
            "aligned": None,
            "densities": [],
            "row_confidences": [],
            "form_confidence": 0.0,
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

        # --- read checkboxes and compute confidence --------------------- #
        densities = self.reader.read_checkbox_grid(aligned)
        row_confidences = [
            self.calculate_row_confidence(row_d, self.config.CHECKBOX_THRESHOLD)
            for row_d in densities
        ]
        form_confidence = self.calculate_form_confidence(row_confidences)
        result["densities"] = densities
        result["row_confidences"] = row_confidences
        result["form_confidence"] = form_confidence

        answers = [self.reader.determine_selection(row_d) for row_d in densities]
        for i, ans in enumerate(answers, start=1):
            result[f"Q{i}"] = ans

        # --- compute form score ---------------------------------------- #
        score = self._compute_form_score(answers)
        result["Form_Score"] = score

        # Valid if at least one answer is not "Invalid" AND form_confidence > 0
        has_valid_answer = any(a != "Invalid" for a in answers)
        result["Valid"] = has_valid_answer and form_confidence > 0.0

        logger.info(
            "Processed %s -> score %.1f, confidence %.2f",
            path.name, score, form_confidence,
        )
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
