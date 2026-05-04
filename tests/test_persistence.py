"""Unit tests for the PersistenceManager layer."""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from config import Config
from models import FormResult, Survey
from persistence import PersistenceManager


@pytest.fixture
def manager():
    """Return a PersistenceManager backed by a temporary database."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test.db"
    pm = PersistenceManager(db_path=db_path)
    yield pm
    # Windows may keep the SQLite file locked briefly; ignore cleanup errors
    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass


# ------------------------------------------------------------------ #
#  Survey CRUD
# ------------------------------------------------------------------ #

class TestSurveyCrud:
    def test_create_survey(self, manager):
        survey = Survey(
            university="Kabul University",
            faculty="Engineering",
            department="Computer Science",
            subject="Database Systems",
            professor="Dr. Ahmadi",
            semester="3",
            academic_year="2023-2024",
        )
        created = manager.create_survey(survey)
        assert created.id is not None
        assert created.status == "Draft"

    def test_get_survey(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        created = manager.create_survey(survey)
        fetched = manager.get_survey(created.id)
        assert fetched is not None
        assert fetched.university == "U1"
        assert fetched.professor == "P1"

    def test_get_survey_missing(self, manager):
        assert manager.get_survey(9999) is None

    def test_update_survey(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        created = manager.create_survey(survey)
        created.subject = "Advanced S1"
        updated = manager.update_survey(created)
        fetched = manager.get_survey(updated.id)
        assert fetched.subject == "Advanced S1"

    def test_delete_survey(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        created = manager.create_survey(survey)
        assert manager.delete_survey(created.id) is True
        assert manager.get_survey(created.id) is None
        assert manager.delete_survey(created.id) is False

    def test_list_surveys_empty(self, manager):
        assert manager.list_surveys() == []

    def test_list_surveys(self, manager):
        s1 = Survey(university="U1", faculty="F1", department="D1", subject="Math", professor="P1", semester="1", academic_year="2024")
        s2 = Survey(university="U1", faculty="F1", department="D1", subject="Physics", professor="P2", semester="2", academic_year="2024")
        manager.create_survey(s1)
        manager.create_survey(s2)
        results = manager.list_surveys()
        assert len(results) == 2
        subjects = {r.subject for r in results}
        assert subjects == {"Math", "Physics"}

    def test_list_surveys_filter_status(self, manager):
        s1 = Survey(university="U1", faculty="F1", department="D1", subject="A", professor="P1", semester="1", academic_year="2024", status="Draft")
        s2 = Survey(university="U1", faculty="F1", department="D1", subject="B", professor="P2", semester="2", academic_year="2024", status="Processed")
        manager.create_survey(s1)
        manager.create_survey(s2)
        drafts = manager.list_surveys(status="Draft")
        assert len(drafts) == 1
        assert drafts[0].subject == "A"

    def test_list_surveys_search(self, manager):
        s1 = Survey(university="U1", faculty="F1", department="D1", subject="Algebra", professor="Ali", semester="1", academic_year="2024")
        s2 = Survey(university="U1", faculty="F1", department="D1", subject="Biology", professor="Babar", semester="2", academic_year="2024")
        manager.create_survey(s1)
        manager.create_survey(s2)
        results = manager.list_surveys(search="Alg")
        assert len(results) == 1
        assert results[0].subject == "Algebra"

        results = manager.list_surveys(search="Bab")
        assert len(results) == 1
        assert results[0].professor == "Babar"

    def test_list_surveys_filter_department(self, manager):
        s1 = Survey(university="U1", faculty="F1", department="CS", subject="A", professor="P1", semester="1", academic_year="2024")
        s2 = Survey(university="U1", faculty="F1", department="EE", subject="B", professor="P2", semester="2", academic_year="2024")
        manager.create_survey(s1)
        manager.create_survey(s2)
        results = manager.list_surveys(department="CS")
        assert len(results) == 1
        assert results[0].subject == "A"

    def test_survey_cascading_delete(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        created = manager.create_survey(survey)
        result = FormResult(
            survey_id=created.id,
            form_id="form_001",
            image_path="/tmp/test.jpg",
            q1="Yes", q2="No",
            form_score=50.0,
            valid=True,
            confidence=0.95,
        )
        manager.create_form_result(result)
        manager.delete_survey(created.id)
        assert manager.get_form_results(created.id) == []


# ------------------------------------------------------------------ #
#  FormResult CRUD
# ------------------------------------------------------------------ #

class TestFormResultCrud:
    def test_create_form_result(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        survey = manager.create_survey(survey)
        result = FormResult(
            survey_id=survey.id,
            form_id="form_001",
            image_path="/tmp/test.jpg",
            q1="Yes", q2="Somewhat", q3="No",
            q4="Yes", q5="Yes", q6="Yes", q7="Yes",
            q8="Yes", q9="Yes", q10="Yes",
            q11="Yes", q12="Yes", q13="Yes", q14="Yes",
            form_score=75.0,
            valid=True,
            confidence=0.92,
            manually_corrected=False,
        )
        created = manager.create_form_result(result)
        assert created.id is not None

    def test_get_form_results(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        survey = manager.create_survey(survey)
        r1 = FormResult(survey_id=survey.id, form_id="f1", image_path="/a.jpg", form_score=80.0, valid=True)
        r2 = FormResult(survey_id=survey.id, form_id="f2", image_path="/b.jpg", form_score=60.0, valid=False)
        manager.create_form_result(r1)
        manager.create_form_result(r2)
        results = manager.get_form_results(survey.id)
        assert len(results) == 2
        assert {r.form_id for r in results} == {"f1", "f2"}

    def test_update_form_result(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        survey = manager.create_survey(survey)
        result = FormResult(survey_id=survey.id, form_id="f1", image_path="/a.jpg", form_score=80.0, valid=True, manually_corrected=False)
        created = manager.create_form_result(result)
        created.form_score = 95.0
        created.manually_corrected = True
        manager.update_form_result(created)
        fetched = manager.get_form_results(survey.id)[0]
        assert fetched.form_score == 95.0
        assert fetched.manually_corrected is True

    def test_delete_form_results_for_survey(self, manager):
        survey = Survey(university="U1", faculty="F1", department="D1", subject="S1", professor="P1", semester="1", academic_year="2024")
        survey = manager.create_survey(survey)
        r1 = FormResult(survey_id=survey.id, form_id="f1", image_path="/a.jpg", form_score=80.0, valid=True)
        r2 = FormResult(survey_id=survey.id, form_id="f2", image_path="/b.jpg", form_score=60.0, valid=True)
        manager.create_form_result(r1)
        manager.create_form_result(r2)
        count = manager.delete_form_results_for_survey(survey.id)
        assert count == 2
        assert manager.get_form_results(survey.id) == []


# ------------------------------------------------------------------ #
#  AppSettings
# ------------------------------------------------------------------ #

class TestAppSettings:
    def test_set_and_get(self, manager):
        manager.set_setting("university_name", "Kabul University")
        assert manager.get_setting("university_name") == "Kabul University"

    def test_get_default(self, manager):
        assert manager.get_setting("missing_key", "fallback") == "fallback"
        assert manager.get_setting("missing_key") is None

    def test_update_existing(self, manager):
        manager.set_setting("language", "fa")
        assert manager.get_setting("language") == "fa"
        manager.set_setting("language", "ps")
        assert manager.get_setting("language") == "ps"

    def test_get_all_settings(self, manager):
        manager.set_setting("key_a", 1)
        manager.set_setting("key_b", [1, 2, 3])
        all_settings = manager.get_all_settings()
        assert all_settings["key_a"] == 1
        assert all_settings["key_b"] == [1, 2, 3]

    def test_delete_setting(self, manager):
        manager.set_setting("temp", "value")
        assert manager.delete_setting("temp") is True
        assert manager.delete_setting("temp") is False
        assert manager.get_setting("temp") is None

    def test_complex_json_value(self, manager):
        coords = {
            "university_name": {"x": 120, "y": 45},
            "logo": {"x": 30, "y": 30, "w": 80, "h": 80},
        }
        manager.set_setting("pdf_coords", coords)
        assert manager.get_setting("pdf_coords") == coords


# ------------------------------------------------------------------ #
#  Config integration
# ------------------------------------------------------------------ #

class TestConfigPersistence:
    def test_round_trip(self, manager):
        cfg = Config()
        cfg.CHECKBOX_THRESHOLD = 0.35
        cfg.SCORE_YES = 90
        cfg.SCORE_SOMEWHAT = 45
        cfg.SCORE_NO = 10
        cfg.APPEARANCE_MODE = "Dark"
        cfg.LANGUAGE = "fa"
        cfg.save_to_persistence(manager)

        loaded = Config.from_persistence(manager)
        assert loaded.CHECKBOX_THRESHOLD == pytest.approx(0.35)
        assert loaded.SCORE_YES == 90
        assert loaded.SCORE_SOMEWHAT == 45
        assert loaded.SCORE_NO == 10
        assert loaded.APPEARANCE_MODE == "Dark"
        assert loaded.LANGUAGE == "fa"

    def test_defaults_when_empty(self, manager):
        loaded = Config.from_persistence(manager)
        assert loaded.CHECKBOX_THRESHOLD == pytest.approx(Config.CHECKBOX_THRESHOLD)
        assert loaded.SCORE_YES == Config.SCORE_YES
        assert loaded.LANGUAGE == Config.LANGUAGE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
