"""Tests for OMRGUI and page instantiation (updated for multi-page architecture)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from gui import OMRGUI, DashboardPage, SurveyFormPage, ProcessPage, ResultsPage
from persistence import PersistenceManager
from pages.base import PageRouter


class TestOMRGUIInit:
    def test_can_instantiate(self):
        app = OMRGUI()
        assert app.root is not None
        assert app.root.title() == "OMR QA Form Scanner"
        app.root.destroy()

    def test_sidebar_nav_buttons_exist(self):
        app = OMRGUI()
        assert "dashboard" in app._nav_btns
        assert "survey_form" in app._nav_btns
        assert "process" in app._nav_btns
        assert "results" in app._nav_btns
        assert "settings" in app._nav_btns
        app.root.destroy()

    def test_router_registered(self):
        app = OMRGUI()
        assert app.router is not None
        assert "dashboard" in app.router.pages
        assert "survey_form" in app.router.pages
        assert "process" in app.router.pages
        assert "results" in app.router.pages
        assert "settings" in app.router.pages
        app.root.destroy()

    def test_default_page_is_dashboard(self):
        app = OMRGUI()
        assert app.router.current_page is not None
        assert isinstance(app.router.current_page, DashboardPage)
        app.root.destroy()

    def test_navigate_to_survey_form(self):
        app = OMRGUI()
        app._navigate("survey_form")
        assert isinstance(app.router.current_page, SurveyFormPage)
        app.root.destroy()

    def test_navigate_without_survey_id_falls_back_to_dashboard(self):
        app = OMRGUI()
        # process and results require survey_id; without it they redirect to dashboard
        app._navigate("process")
        assert isinstance(app.router.current_page, DashboardPage)
        app._navigate("results")
        assert isinstance(app.router.current_page, DashboardPage)
        app.root.destroy()


class TestDashboardPage:
    """Page-level tests reuse a single OMRGUI instance to avoid Tcl re-init issues."""

    def test_dashboard_has_search_entry(self):
        app = OMRGUI()
        app._navigate("dashboard")
        page = app.router.current_page
        assert isinstance(page, DashboardPage)
        assert hasattr(page, "search_entry")
        app.root.destroy()

    def test_dashboard_has_dept_filter(self):
        app = OMRGUI()
        app._navigate("dashboard")
        page = app.router.current_page
        assert hasattr(page, "dept_filter")
        app.root.destroy()

    def test_dashboard_has_list_frame(self):
        app = OMRGUI()
        app._navigate("dashboard")
        page = app.router.current_page
        assert hasattr(page, "list_frame")
        app.root.destroy()


class TestSurveyFormPage:
    def test_all_fields_present(self):
        app = OMRGUI()
        app._navigate("survey_form")
        page = app.router.current_page
        assert isinstance(page, SurveyFormPage)
        for key in ("faculty", "department", "subject", "professor", "semester", "academic_year"):
            assert key in page._entries, f"Missing field: {key}"
        app.root.destroy()

    def test_print_btn_disabled_for_new_survey(self):
        app = OMRGUI()
        app._navigate("survey_form")
        page = app.router.current_page
        assert page.print_btn.cget("state") == "disabled"
        app.root.destroy()
