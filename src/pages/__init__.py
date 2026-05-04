"""Pages sub-package for the OMR Scanner GUI."""

from .base import PageRouter, BasePage
from .dashboard import DashboardPage
from .survey_form import SurveyFormPage
from .process import ProcessPage
from .results import ResultsPage
from .settings import SettingsFrame

__all__ = [
    "PageRouter",
    "BasePage",
    "DashboardPage",
    "SurveyFormPage",
    "ProcessPage",
    "ResultsPage",
    "SettingsFrame",
]
