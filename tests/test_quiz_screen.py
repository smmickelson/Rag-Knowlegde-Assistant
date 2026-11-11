"""Tests for the 18a Streamlit quiz screen (app.py), run with Streamlit's
AppTest framework (no real browser needed). Written before the build step,
per the project routine — the builder (DeepSeek) implements app.py to make
these pass; it never edits this file.

IMPLEMENTATION CONTRACT these tests require app.py to follow:

- One st.radio per question, in question order (1-15 matching
  docs/quiz-questions.md), each with:
    key=f"q{n}"             (n = 1..15)
    label=<question text>   (word for word from docs/quiz-questions.md)
    options=["Never", "Occasionally", "Frequently", "Always"]  (this order)
    index=None               (nothing selected on first load)
- Submit button: st.button("Submit", key="submit_btn")
- Retake button: st.button("Retake", key="retake_btn"), rendered only once a
  result exists — not present at all before that.
- Once Submit produces a result: all 15 st.radio widgets and the Submit
  button get disabled=True, and stay that way until Retake is clicked.
- The result is shown as two st.markdown elements (not st.success, st.info,
  st.header, or similar — those are different element types and these tests
  would not find them), each containing one of the display-name strings from
  the spec's table (e.g. a markdown element containing "Community Builder",
  another containing "Mid"). Both disappear again after Retake.

Note on score_assessment: AppTest re-executes app.py's whole script (imports
included) on every run, so patching "app.score_assessment" doesn't work --
there's no stable "app" module for the patch to stick to between reruns.
Patching "src.scoring.score_assessment" does work, though: src/scoring.py
stays loaded normally between reruns, so when app.py's "from src.scoring
import score_assessment" line re-executes, it picks up whatever is currently
on that module -- the patched version included. That's what
test_submit_sends_exact_answer_list_to_the_scorer relies on.
test_submit_sends_answers_in_correct_question_order takes the older, more
roundabout approach (computing the expected result directly from the real
scorer and checking the app's displayed result matches it) and is kept
alongside the newer test since it also verifies the display step.
"""

import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src.scoring import score_assessment

REPO_ROOT = Path(__file__).resolve().parent.parent
QUIZ_QUESTIONS_PATH = REPO_ROOT / "docs" / "quiz-questions.md"
FIXTURES_PATH = REPO_ROOT / "tests" / "fixtures" / "known_answers.json"

CHOICE_LABELS = ["Never", "Occasionally", "Frequently", "Always"]

DISPLAY_NAMES = {
    "connector": "Connector",
    "cultivator": "Cultivator",
    "opportunitySeeker": "Opportunity Seeker",
    "communityBuilder": "Community Builder",
    "low": "Low",
    "mid": "Mid",
    "high": "High",
}


def _load_questions():
    text = QUIZ_QUESTIONS_PATH.read_text()
    matches = re.findall(r"^\d+\.\s+(.+)$", text, flags=re.MULTILINE)
    assert len(matches) == 15
    return matches


def _load_fixtures():
    return json.loads(FIXTURES_PATH.read_text())["fixtures"]


QUESTIONS = _load_questions()
FIXTURES = _load_fixtures()

# Canned content-library text shown on the intro screen (philosophy). Used so
# tests never touch the real content-library pipeline unless they mean to.
INTRO_PHILOSOPHY_TEXT = "Intro philosophy: there is no single best style."


@pytest.fixture(autouse=True)
def _mock_content_library(monkeypatch):
    """Mock the content-library pipeline so no test in this file exercises the
    real store (build, intro philosophy fetch, or post-submit retrieval).

    The intro screen now fetches the philosophy_blend chunk on every fresh
    load, so without this every test would trigger the real build/read. The
    post-submit retrieval is also mocked so result-screen tests are fast and
    order-independent.
    """
    monkeypatch.setattr("content_library_store.build_store", lambda *a, **k: None)
    monkeypatch.setattr(
        "content_library_store.get_item",
        lambda *a, **k: SimpleNamespace(text=INTRO_PHILOSOPHY_TEXT),
    )
    monkeypatch.setattr("content_library_store.retrieve_for_score", lambda *a, **k: [])


def _by_key(elements, key):
    for e in elements:
        if getattr(e, "key", None) == key:
            return e
    return None


def _fresh_app():
    at = AppTest.from_file(str(REPO_ROOT / "app.py"))
    at.run()
    return at


def _answer_all(at, answers):
    for i, value in enumerate(answers):
        _by_key(at.radio, f"q{i + 1}").set_value(CHOICE_LABELS[value - 1])
    at.run()


def test_all_15_questions_render_with_four_choices_in_order_matching_docs():
    at = _fresh_app()
    for i, question_text in enumerate(QUESTIONS):
        radio = _by_key(at.radio, f"q{i + 1}")
        assert radio is not None, f"no radio with key='q{i + 1}'"
        assert radio.label == question_text
        assert list(radio.options) == CHOICE_LABELS


def test_nothing_preselected_on_first_load():
    at = _fresh_app()
    for i in range(15):
        assert _by_key(at.radio, f"q{i + 1}").value is None


def test_submit_disabled_on_first_load():
    at = _fresh_app()
    assert _by_key(at.button, "submit_btn").disabled is True


def test_submit_enabled_once_all_15_answered():
    at = _fresh_app()
    _answer_all(at, [4] * 15)
    assert _by_key(at.button, "submit_btn").disabled is False


def test_submit_stays_disabled_with_one_question_left_unanswered():
    at = _fresh_app()
    for i in range(14):
        _by_key(at.radio, f"q{i + 1}").set_value("Always")
    at.run()
    assert _by_key(at.button, "submit_btn").disabled is True


def test_answering_one_does_not_change_others():
    at = _fresh_app()
    _by_key(at.radio, "q1").set_value("Always")
    at.run()
    _by_key(at.radio, "q2").set_value("Never")
    at.run()
    assert _by_key(at.radio, "q1").value == "Always"
    assert _by_key(at.radio, "q2").value == "Never"
    assert _by_key(at.radio, "q3").value is None


def test_submit_sends_answers_in_correct_question_order():
    at = _fresh_app()
    distinctive_answers = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3]
    expected = score_assessment(distinctive_answers)

    _answer_all(at, distinctive_answers)
    _by_key(at.button, "submit_btn").click().run()

    # This test's purpose is question order -> correct winner. The tier label
    # is intentionally no longer displayed (the tier is still computed and
    # used internally, just not shown), so only the winner name is checked.
    texts = [m.value for m in at.markdown]
    assert any(DISPLAY_NAMES[expected["winner"]] in t for t in texts), texts


def test_submit_sends_exact_answer_list_to_the_scorer():
    at = _fresh_app()
    answers = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3]
    with patch("src.scoring.score_assessment", wraps=score_assessment) as mocked:
        _answer_all(at, answers)
        _by_key(at.button, "submit_btn").click().run()
        mocked.assert_called_once()
        assert mocked.call_args[0][0] == answers


@pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
def test_known_fixture_shows_correct_winner_display_name(fixture):
    at = _fresh_app()
    _answer_all(at, fixture["answers"])
    _by_key(at.button, "submit_btn").click().run()

    expected_winner = DISPLAY_NAMES[fixture["expected"]["winner"]]

    # Only the winner display name is checked; the tier label is intentionally
    # no longer shown on the result screen.
    texts = [m.value for m in at.markdown]
    assert any(expected_winner in t for t in texts), texts


def test_result_shows_only_display_names_not_raw_scorer_values():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()

    all_text = " ".join(m.value for m in at.markdown)
    # The raw scorer values must not appear as standalone words (the exact
    # tier labels or style names). Since #4e shows real content-library prose,
    # which naturally contains these as substrings of ordinary words (e.g.
    # "follow" contains "low"), only a standalone-token match is forbidden.
    for raw_value in (
        "connector", "cultivator", "opportunitySeeker", "communityBuilder",
        "low", "mid", "high",
    ):
        assert not re.search(rf"(?<![A-Za-z]){re.escape(raw_value)}(?![A-Za-z])", all_text), (
            f"raw scorer value {raw_value!r} leaked into the display as a "
            f"standalone token: {all_text!r}"
        )


def test_inputs_and_submit_lock_after_result():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()

    for i in range(15):
        assert _by_key(at.radio, f"q{i + 1}").disabled is True
    assert _by_key(at.button, "submit_btn").disabled is True


def test_retake_not_shown_before_result():
    at = _fresh_app()
    assert _by_key(at.button, "retake_btn") is None


def test_retake_appears_after_result():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()
    assert _by_key(at.button, "retake_btn") is not None


def test_retake_resets_to_fresh_state():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()

    _by_key(at.button, "retake_btn").click().run()

    for i in range(15):
        radio = _by_key(at.radio, f"q{i + 1}")
        assert radio.value is None
        assert radio.disabled is False
    assert _by_key(at.button, "submit_btn").disabled is True
    assert _by_key(at.button, "retake_btn") is None


def test_retake_clears_the_displayed_result():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()

    result_texts = " ".join(m.value for m in at.markdown)
    assert "Your networking style:" in result_texts, result_texts

    _by_key(at.button, "retake_btn").click().run()

    # Retake clears the user-specific result content (style label, score,
    # tagline), but the permanent intro-screen philosophy text remains.
    after_texts = [m.value for m in at.markdown]
    assert not any("Your networking style:" in t for t in after_texts), after_texts
    assert not any("Your overall score:" in t for t in after_texts), after_texts
    assert INTRO_PHILOSOPHY_TEXT in after_texts, after_texts


def test_buttons_labeled_exactly():
    at = _fresh_app()
    assert _by_key(at.button, "submit_btn").label == "Submit"
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()
    assert _by_key(at.button, "retake_btn").label == "Retake"
