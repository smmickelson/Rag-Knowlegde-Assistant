"""
Tests for backlog item #1: port the 15-question scoring logic to Python.

These tests are written BEFORE the implementation exists. They check
score_assessment() against the answer key in tests/fixtures/known_answers.json,
which was derived independently from the live JavaScript at
tools.werkitgirls.com (not from any Python code).

Scope: scoring only -- overall score, four style totals, winner, tier.
Nothing here touches coaching text, the knowledge base, or any AI service.
"""

import copy
import json
from pathlib import Path

import pytest

from src.scoring import score_assessment

FIXTURE_FILE = Path(__file__).parent / "fixtures" / "known_answers.json"

with open(FIXTURE_FILE) as f:
    FIXTURES = json.load(f)["fixtures"]


@pytest.mark.parametrize("fixture", FIXTURES, ids=[fx["name"] for fx in FIXTURES])
def test_score_matches_known_answer(fixture):
    """Each fixture's 15 answers must produce exactly the expected result."""
    result = score_assessment(fixture["answers"])

    # Compare only the keys the fixture specifies, so the function can later
    # return extra fields (e.g. cluster subtotals) without breaking these tests.
    for key, expected_value in fixture["expected"].items():
        assert result[key] == expected_value, (
            f"{fixture['name']}: {key} should be {expected_value}, got {result[key]}"
        )


def test_exact_tie_goes_to_the_later_style():
    """On an exact tie, the later style wins (live code behavior, not earlier-wins)."""
    tie = next(fx for fx in FIXTURES if fx["name"] == "tie_connector_cultivator")
    result = score_assessment(tie["answers"])
    assert result["connector"] == result["cultivator"]
    assert result["winner"] == "cultivator"


def test_tier_boundaries_are_inclusive():
    """A winning score of exactly 12 is mid (not low); exactly 20 is high (not mid)."""
    mid = next(fx for fx in FIXTURES if fx["name"] == "boundary_mid_exact")
    high = next(fx for fx in FIXTURES if fx["name"] == "boundary_high_exact")
    assert score_assessment(mid["answers"])["tier"] == "mid"
    assert score_assessment(high["answers"])["tier"] == "high"


def test_scoring_is_pure():
    """Same answers in, same result out, and the input list is never modified."""
    answers = FIXTURES[0]["answers"]
    original = copy.deepcopy(answers)
    first = score_assessment(answers)
    second = score_assessment(answers)
    assert first == second
    assert answers == original
