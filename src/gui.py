"""Backward-compatibility shim.

All GUI code has been refactored into:
  src/app.py          — OMRGUI main window
  src/pages/          — individual page modules
  src/theme.py        — design tokens and widget factories

This module re-exports the public API so existing imports keep working.
"""

from app import OMRGUI  # noqa: F401
from pages import (     # noqa: F401
    PageRouter,
    BasePage,
    DashboardPage,
    SurveyFormPage,
    ProcessPage,
    ResultsPage,
    SettingsFrame,
)

__all__ = [
    "OMRGUI",
    "PageRouter",
    "BasePage",
    "DashboardPage",
    "SurveyFormPage",
    "ProcessPage",
    "ResultsPage",
    "SettingsFrame",
]
