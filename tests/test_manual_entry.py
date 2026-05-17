"""Unit tests for the manual data entry generation and persistence pipeline."""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest

from config import Config
from models import FormResult, Survey
from persistence import PersistenceManager
from analytics_engine import AnalyticsEngine


@pytest.fixture
def test_env():
    """Set up database and return (persistence, analytics) instances."""
    tmpdir = tempfile.mkdtemp()
    db_path = Path(tmpdir) / "test.db"
    pm = PersistenceManager(db_path=db_path)
    ae = AnalyticsEngine()
    yield pm, ae
    try:
        shutil.rmtree(tmpdir, ignore_errors=True)
    except Exception:
        pass


def test_manual_entry_synthesis(test_env):
    persistence, analytics = test_env

    # 1. Create a survey
    survey = Survey(
        university="Kabul University",
        faculty="Science",
        department="Computer Science",
        subject="Algorithms",
        professor="Ahmad",
        semester="1",
        academic_year="2025-2026",
    )
    survey = persistence.create_survey(survey)
    assert survey.id is not None
    assert survey.status == "Draft"

    # Mock manually entered counts for Q1 to Q14
    # Suppose Q1: Yes=10, Somewhat=2, No=1  -> total = 13
    # Q2: Yes=5, Somewhat=5, No=0           -> total = 10
    # Q14: Yes=2, Somewhat=3, No=8          -> total = 13
    # All others: Yes=12, Somewhat=1, No=0   -> total = 13
    # Therefore, N (maximum responses) = 13.
    yes_counts = [10, 5] + [12] * 11 + [2]
    somewhat_counts = [2, 5] + [1] * 11 + [3]
    no_counts = [1, 0] + [0] * 11 + [8]

    # Calculate expected N
    totals_per_q = [
        yes_counts[i] + somewhat_counts[i] + no_counts[i]
        for i in range(14)
    ]
    N = max(totals_per_q)
    assert N == 13

    # Build pools of answers, padding with "Invalid"
    pools = []
    for i in range(14):
        pool = (
            ["Yes"] * yes_counts[i] +
            ["Somewhat"] * somewhat_counts[i] +
            ["No"] * no_counts[i]
        )
        pool += ["Invalid"] * (N - len(pool))
        pools.append(pool)

    # 2. Clear old form results
    persistence.delete_form_results_for_survey(survey.id)

    # 3. Generate N synthetic form results
    for j in range(N):
        answers = [pools[i][j] for i in range(14)]
        form_score = analytics.calculate_form_score(answers)
        valid = any(ans != "Invalid" for ans in answers)

        result = FormResult(
            survey_id=survey.id,
            form_id=f"Manual_Form_{j + 1}",
            image_path="",
            q1=answers[0], q2=answers[1], q3=answers[2], q4=answers[3],
            q5=answers[4], q6=answers[5], q7=answers[6], q8=answers[7],
            q9=answers[8], q10=answers[9], q11=answers[10], q12=answers[11],
            q13=answers[12], q14=answers[13],
            form_score=form_score,
            valid=valid,
            confidence=1.0,
            manually_corrected=True,
            comment="Manually Entered Data"
        )
        persistence.create_form_result(result)

    # 4. Update survey status to Processed
    survey.status = "Processed"
    persistence.update_survey(survey)

    # Verify Database State
    fetched_results = persistence.get_form_results(survey.id)
    assert len(fetched_results) == N

    # Verify that the generated answers match entered counts perfectly
    # Let's count them back from the database
    db_yes_counts = [0] * 14
    db_somewhat_counts = [0] * 14
    db_no_counts = [0] * 14
    db_invalid_counts = [0] * 14

    for fr in fetched_results:
        answers = fr.answers()
        assert len(answers) == 14
        for i in range(14):
            ans = answers[i]
            if ans == "Yes":
                db_yes_counts[i] += 1
            elif ans == "Somewhat":
                db_somewhat_counts[i] += 1
            elif ans == "No":
                db_no_counts[i] += 1
            elif ans == "Invalid":
                db_invalid_counts[i] += 1

    # Check question-by-question totals
    for i in range(14):
        assert db_yes_counts[i] == yes_counts[i], f"Mismatch Q{i+1} Yes"
        assert db_somewhat_counts[i] == somewhat_counts[i], f"Mismatch Q{i+1} Somewhat"
        assert db_no_counts[i] == no_counts[i], f"Mismatch Q{i+1} No"
        
        # Verify padding logic
        expected_padding = N - (yes_counts[i] + somewhat_counts[i] + no_counts[i])
        assert db_invalid_counts[i] == expected_padding, f"Mismatch Q{i+1} Padding"

    # Verify that the survey status is indeed Processed
    fetched_survey = persistence.get_survey(survey.id)
    assert fetched_survey.status == "Processed"
