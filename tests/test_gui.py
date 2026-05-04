"""Basic tests for OMRGUI instantiation and helper methods."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from gui import OMRGUI


class TestOMRGUIInit:
    def test_can_instantiate(self):
        app = OMRGUI()
        assert app.root is not None
        assert app.root.title() == "OMR QA Form Scanner"
        app.root.destroy()

    def test_widgets_created(self):
        app = OMRGUI()
        assert app.folder_label is not None
        assert app.browse_btn is not None
        assert app.start_btn is not None
        assert app.report_btn is not None
        assert app.status_text is not None
        app.root.destroy()

    def test_buttons_initial_state(self):
        app = OMRGUI()
        # Start button disabled until folder selected
        assert app.start_btn.cget("state") == "disabled"
        # Report button always disabled at start
        assert app.report_btn.cget("state") == "disabled"
        app.root.destroy()


class TestUpdateStatus:
    def test_appends_text(self):
        app = OMRGUI()
        app.update_status("Test message")
        content = app.status_text.get("1.0", "end")
        assert "Test message" in content
        app.root.destroy()
