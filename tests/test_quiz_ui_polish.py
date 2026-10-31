"""Tests for the 2a quiz screen structural polish (app.py), run with
Streamlit's AppTest framework (no real browser needed). Written before the
build step, per the project routine — the builder (DeepSeek) implements the
changes in app.py to make these pass; it never edits this file.

One acceptance criterion from specs/2a-quiz-ui-polish.md is NOT covered
here: the browser tab title. Streamlit's AppTest has no way to inspect
st.set_page_config(page_title=...) — confirmed by direct probing on
2026-10-31 (there is no "page_config" or similar attribute on an AppTest
instance). That criterion is verified by hand instead; see the spec's
amended acceptance criteria list.

IMPLEMENTATION CONTRACT these tests require app.py to follow, on top of
the contract already established in test_quiz_screen.py for 18a:

- Header: st.title("What Kind of Networker Are You?") — rendered once,
  unconditionally, on every run (before submission, after submission, and
  after Retake). This is the one piece of the new UI that stays visible at
  all times.
- Subtitle: st.caption("Connector, Cultivator, Opportunity Seeker, or
  Community Builder — 15 quick questions, instant answer.") — rendered
  only when no result is shown yet (i.e. omitted entirely once Submit has
  produced a result; present again after Retake).
- Progress: st.progress(answered_count / 15, text=f"{answered_count} of 15
  answered") — one progress element, rendered only when no result is shown
  yet (same visibility rule as the subtitle). answered_count is how many of
  the 15 questions currently have a non-None value, recomputed every run.
  AppTest exposes the fraction passed to st.progress as a 0-100 integer
  percentage on the element's .value (confirmed by probing: passing 0.4
  yields .value == 40), and the text= argument on .text.
- Result labels: once Submit produces a result, two st.markdown elements
  carry the full labeled text — "Your networking style: {display name}"
  and "Your tier: {display name}" — not the bare display name alone. A
  third st.markdown element carries exactly: "More personalized coaching
  based on your specific answers is coming soon." All three disappear
  again after Retake, same as the existing result markdown did before this
  item.
- Retake (already covered by test_quiz_screen.py for the question/result
  state) additionally restores the subtitle and progress elements, since
  this item makes them disappear on submission for the first time.

Shares the same question-loading, fixture-loading, and AppTest helper
pattern as test_quiz_screen.py; kept self-contained (no cross-file import)
since this project has no shared conftest.py yet.
"""

import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parent.parent
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

HEADER_TEXT = "What Kind of Networker Are You?"
SUBTITLE_TEXT = (
    "Connector, Cultivator, Opportunity Seeker, or Community Builder — "
    "15 quick questions, instant answer."
)
COMING_SOON_TEXT = (
    "More personalized coaching based on your specific answers is coming soon."
)


def _load_fixtures():
    return json.loads(FIXTURES_PATH.read_text())["fixtures"]


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


def test_header_and_subtitle_visible_on_fresh_load():
    at = _fresh_app()
    titles = [t.value for t in at.title]
    captions = [c.value for c in at.caption]
    assert HEADER_TEXT in titles, titles
    assert SUBTITLE_TEXT in captions, captions


def test_progress_starts_at_zero_of_15_on_fresh_load():
    at = _fresh_app()
    progress_elements = list(at.progress)
    assert len(progress_elements) == 1, progress_elements
    assert progress_elements[0].value == 0
    assert progress_elements[0].text == "0 of 15 answered"


def test_progress_bar_and_text_fill_proportionally_as_questions_are_answered():
    at = _fresh_app()
    for i in range(6):
        _by_key(at.radio, f"q{i + 1}").set_value("Always")
    at.run()
    progress_elements = list(at.progress)
    assert len(progress_elements) == 1, progress_elements
    assert progress_elements[0].value == 40  # 6 of 15 = 40%
    assert progress_elements[0].text == "6 of 15 answered"


def test_progress_shows_15_of_15_once_all_answered_but_before_submit():
    at = _fresh_app()
    _answer_all(at, [4] * 15)
    progress_elements = list(at.progress)
    assert len(progress_elements) == 1, progress_elements
    assert progress_elements[0].value == 100
    assert progress_elements[0].text == "15 of 15 answered"


def test_changing_an_already_answered_question_does_not_change_the_count():
    at = _fresh_app()
    _by_key(at.radio, "q1").set_value("Always")
    at.run()
    _by_key(at.radio, "q2").set_value("Never")
    at.run()
    assert list(at.progress)[0].text == "2 of 15 answered"

    # Changing q1's existing answer must not raise the count to 3.
    _by_key(at.radio, "q1").set_value("Occasionally")
    at.run()
    assert list(at.progress)[0].text == "2 of 15 answered"


def test_subtitle_and_progress_hidden_once_result_is_shown():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()

    assert list(at.caption) == []
    assert list(at.progress) == []
    titles = [t.value for t in at.title]
    assert HEADER_TEXT in titles, titles


def test_result_shows_labeled_style_and_tier():
    at = _fresh_app()
    fixture = FIXTURES[0]
    _answer_all(at, fixture["answers"])
    _by_key(at.button, "submit_btn").click().run()

    expected_winner = DISPLAY_NAMES[fixture["expected"]["winner"]]
    expected_tier = DISPLAY_NAMES[fixture["expected"]["tier"]]
    texts = [m.value for m in at.markdown]

    assert f"Your networking style: {expected_winner}" in texts, texts
    assert f"Your tier: {expected_tier}" in texts, texts


def test_result_shows_coming_soon_line_worded_identically_across_results():
    # Pick two fixtures that produce different results, so this test proves
    # the coming-soon line doesn't change based on the result -- not just
    # that it shows up twice.
    first = FIXTURES[0]
    second = next(
        f for f in FIXTURES[1:] if f["expected"] != first["expected"]
    )
    assert first["expected"] != second["expected"], (
        "need two fixtures with different results for this test to prove anything"
    )

    for fixture in (first, second):
        at = _fresh_app()
        _answer_all(at, fixture["answers"])
        _by_key(at.button, "submit_btn").click().run()
        texts = [m.value for m in at.markdown]
        assert COMING_SOON_TEXT in texts, texts


def test_retake_restores_subtitle_and_progress():
    at = _fresh_app()
    _answer_all(at, FIXTURES[0]["answers"])
    _by_key(at.button, "submit_btn").click().run()
    assert list(at.caption) == []
    assert list(at.progress) == []

    _by_key(at.button, "retake_btn").click().run()

    captions = [c.value for c in at.caption]
    assert SUBTITLE_TEXT in captions, captions
    progress_elements = list(at.progress)
    assert len(progress_elements) == 1, progress_elements
    assert progress_elements[0].value == 0
    assert progress_elements[0].text == "0 of 15 answered"


def test_each_question_updates_progress_individually_without_disturbing_others():
    at = _fresh_app()
    for i in range(15):
        _by_key(at.radio, f"q{i + 1}").set_value("Always")
        at.run()

        progress_elements = list(at.progress)
        assert len(progress_elements) == 1, progress_elements
        assert progress_elements[0].text == f"{i + 1} of 15 answered"

        for j in range(i + 1):
            assert _by_key(at.radio, f"q{j + 1}").value == "Always", (
                f"q{j + 1} should still be answered after answering q{i + 1}"
            )
        for j in range(i + 1, 15):
            assert _by_key(at.radio, f"q{j + 1}").value is None, (
                f"q{j + 1} should not be answered yet"
            )


def test_result_markdown_shows_only_the_three_expected_lines():
    at = _fresh_app()
    fixture = FIXTURES[0]
    _answer_all(at, fixture["answers"])
    _by_key(at.button, "submit_btn").click().run()

    expected_winner = DISPLAY_NAMES[fixture["expected"]["winner"]]
    expected_tier = DISPLAY_NAMES[fixture["expected"]["tier"]]
    texts = [m.value for m in at.markdown]

    assert set(texts) == {
        f"Your networking style: {expected_winner}",
        f"Your tier: {expected_tier}",
        COMING_SOON_TEXT,
    }, texts


def test_no_exceptions_through_full_quiz_lifecycle():
    at = _fresh_app()
    assert list(at.exception) == []

    _answer_all(at, FIXTURES[0]["answers"])
    assert list(at.exception) == []

    _by_key(at.button, "submit_btn").click().run()
    assert list(at.exception) == []

    _by_key(at.button, "retake_btn").click().run()
    assert list(at.exception) == []
