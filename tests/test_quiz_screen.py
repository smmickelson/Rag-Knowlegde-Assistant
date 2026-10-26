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

Note on score_assessment: AppTest re-executes app.py as a script each run, so
unittest.mock cannot intercept a call made from inside it. Instead of mocking,
test_submit_sends_answers_in_correct_question_order computes the expected
result directly from the real scorer and checks the app's displayed result
matches — a reordering bug would show up as a wrong winner/tier.
"""

import json
import re
from pathlib import Path

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

    texts = [m.value for m in at.markdown]
    assert any(DISPLAY_NAMES[expected["winner"]] in t for t in texts), texts
    assert any(DISPLAY_NAMES[expected["tier"]] in t for t in texts), texts


@pytest.mark.parametrize("fixture", FIXTURES, ids=[f["name"] for f in FIXTURES])
def test_known_fixture_shows_correct_display_names(fixture):
    at = _fresh_app()
    _answer_all(at, fixture["answers"])
    _by_key(at.button, "submit_btn").click().run()

    expected_winner = DISPLAY_NAMES[fixture["expected"]["winner"]]
    expected_tier = DISPLAY_NAMES[fixture["expected"]["tier"]]

    texts = [m.value for m in at.markdown]
    assert any(expected_winner in t for t in texts), texts
    assert any(expected_tier in t for t in texts), texts


def test_result_shows_only_display_names_not_raw_scorer_values():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()

    all_text = " ".join(m.value for m in at.markdown)
    for raw_value in (
        "connector", "cultivator", "opportunitySeeker", "communityBuilder",
        "low", "mid", "high",
    ):
        assert raw_value not in all_text, (
            f"raw scorer value {raw_value!r} leaked into the display: {all_text!r}"
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
    assert len(list(at.markdown)) > 0

    _by_key(at.button, "retake_btn").click().run()

    assert len(list(at.markdown)) == 0, [m.value for m in at.markdown]


def test_buttons_labeled_exactly():
    at = _fresh_app()
    assert _by_key(at.button, "submit_btn").label == "Submit"
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()
    assert _by_key(at.button, "retake_btn").label == "Retake"
