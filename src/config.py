"""Core configuration and constants for the OMR QA Form Scanner."""

import logging
import sys
from pathlib import Path
from typing import Any


class Config:
    """Application-wide configuration constants."""

    # Form geometry
    FORM_WIDTH: int = 800
    FORM_HEIGHT: int = 1000

    # Checkbox detection
    CHECKBOX_THRESHOLD: float = 0.20

    # Grid layout
    ROW_COUNT: int = 14
    COLUMN_COUNT: int = 3

    # Score weights (legacy 0/50/100 scale — used when LIKERT_MODE is False)
    SCORE_YES: int = 100
    SCORE_SOMEWHAT: int = 50
    SCORE_NO: int = 0

    # Likert scale mode (Yes=3, Somewhat=2, No=1, Invalid=0)
    LIKERT_MODE: bool = True

    # Pedagogical dimension mapping  {dimension_name: [1-based question indices]}
    DIMENSION_MAP: dict = {
        "Curriculum & Resources":            [1, 2, 3],
        "Pedagogical Delivery":              [4, 5, 9, 12],
        "Classroom Management":              [7, 8, 10, 11],
        "Modern & Student-Centric Teaching": [6, 13, 14],
    }

    # QA alert threshold — dimension mean below this triggers a flag
    DIMENSION_ALERT_THRESHOLD: float = 2.2

    # Polarization threshold — question SD above this is flagged
    POLARIZATION_SD_THRESHOLD: float = 0.8

    # Batch score alert threshold (0–100 legacy scale)
    BATCH_SCORE_ALERT_THRESHOLD: float = 60.0

    # Punctuality question index (1-based) and max % "No" before alert
    PUNCTUALITY_QUESTION: int = 10
    PUNCTUALITY_NO_THRESHOLD: float = 0.15

    # Supported image extensions
    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png")

    # UI preferences
    APPEARANCE_MODE: str = "Dark"   # dark-navy palette is the primary design
    LANGUAGE: str = "fa"             # en, fa (Dari), ps (Pashto)

    # Survey question texts (14 items; empty list means use defaults from pdf_generator)
    QUESTION_TEXTS: list = []

    # Derived paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"
    DEFAULT_LOGO_PATH: Path = ASSETS_DIR / "uni_logo.png"
    QA_LOGO_PATH: Path = ASSETS_DIR / "mohe_logo.png"

    @classmethod
    def from_persistence(cls, persistence: Any) -> "Config":
        """Create a Config with values loaded from AppSettings.

        Args:
            persistence: A PersistenceManager instance (imported
                locally to avoid circular dependencies).

        Returns:
            Config instance with fields overridden by stored values.
        """
        cfg = cls()
        settings = persistence.get_all_settings()

        def _load(name: str, cast: type, default: Any) -> Any:
            val = settings.get(name)
            if val is None:
                return default
            try:
                return cast(val)
            except (ValueError, TypeError):
                return default

        cfg.CHECKBOX_THRESHOLD = _load("CHECKBOX_THRESHOLD", float, cls.CHECKBOX_THRESHOLD)
        cfg.SCORE_YES = _load("SCORE_YES", int, cls.SCORE_YES)
        cfg.SCORE_SOMEWHAT = _load("SCORE_SOMEWHAT", int, cls.SCORE_SOMEWHAT)
        cfg.SCORE_NO = _load("SCORE_NO", int, cls.SCORE_NO)
        cfg.APPEARANCE_MODE = _load("APPEARANCE_MODE", str, cls.APPEARANCE_MODE)
        cfg.LANGUAGE = _load("LANGUAGE", str, cls.LANGUAGE)
        stored_q = settings.get("question_texts")
        if isinstance(stored_q, list) and len(stored_q) == 14:
            cfg.QUESTION_TEXTS = stored_q
        return cfg

    def save_to_persistence(self, persistence: Any) -> None:
        """Write mutable configuration values to AppSettings.

        Args:
            persistence: A PersistenceManager instance.
        """
        persistence.set_setting("CHECKBOX_THRESHOLD", self.CHECKBOX_THRESHOLD)
        persistence.set_setting("SCORE_YES", self.SCORE_YES)
        persistence.set_setting("SCORE_SOMEWHAT", self.SCORE_SOMEWHAT)
        persistence.set_setting("SCORE_NO", self.SCORE_NO)
        persistence.set_setting("APPEARANCE_MODE", self.APPEARANCE_MODE)
        persistence.set_setting("LANGUAGE", self.LANGUAGE)
        if self.QUESTION_TEXTS:
            persistence.set_setting("question_texts", self.QUESTION_TEXTS)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure application logging.

    Args:
        level: Logging level (default: INFO).

    Returns:
        Configured root logger instance.
    """
    logger = logging.getLogger("omr_qa_scanner")
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
