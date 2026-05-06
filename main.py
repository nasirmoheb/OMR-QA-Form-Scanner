"""Application entry point for the Tadris QA System."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from gui import OMRGUI


def main() -> None:
    """Create and launch the Tadris QA GUI."""
    app = OMRGUI()
    app.run()


if __name__ == "__main__":
    main()
