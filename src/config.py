"""Core configuration and constants for the OMR QA Form Scanner."""

import logging
import sys
from pathlib import Path


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

    # Score weights
    SCORE_YES: int = 100
    SCORE_SOMEWHAT: int = 50
    SCORE_NO: int = 0

    # Supported image extensions
    SUPPORTED_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png")

    # Derived paths
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    ASSETS_DIR: Path = PROJECT_ROOT / "assets"


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
