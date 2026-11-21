"""Tests for the 4e retrieval wiring (app.py), run with Streamlit's AppTest
framework (no real browser needed, no cross-file import). Written before the
build step, per the project routine — the builder implements the changes in
app.py to make these pass; it never edits this file.

This item (specs/4e-wire-retrieval-into-app.md) replaces the placeholder
"more coaching coming soon" line on the result screen with real content pulled
from the content-library store via content_library_store.retrieve_for_score()
(returned by item #4a), which the app builds on demand from vendored files.

IMPLEMENTATION CONTRACT these tests require app.py to follow, on top of the
contract already established in test_quiz_screen.py and test_quiz_ui_polish.py:

- Vendored source: the 40 content-library markdown files live in this repo
  under ``content_library/`` (copied as-is from
  werkitgirls-resources/knowledge_base). Let that folder be KB_DIR.

- Imports: app.py imports ``build_store``, ``retrieve_for_score``, and
  ``DEFAULT_STORE_DIR`` from ``content_library_store`` (the #2b/#4a module).

- Build on demand: each run, if the store does not already exist at
  ``DEFAULT_STORE_DIR`` (the default path data/content_library), app.py calls
  ``build_store(KB_DIR, DEFAULT_STORE_DIR)`` before retrieving. No manual
  setup step, and no error is shown to the user on a successful build.

- Result screen: once Submit produces a score result, app.py calls
  ``retrieve_for_score(DEFAULT_STORE_DIR, result)`` and, instead of
  COMING_SOON_TEXT, renders:
    - the philosophy_blend chunk's text as st.markdown (same for everyone),
    - the winning style's ``identity`` chunk's text as st.markdown,
    - the winning style's ``strengths`` chunk's text as st.markdown,
    - the 3 ranked behavior chunks' text presented as an st.radio (a single
      radio whose options are exactly the 3 behavior texts, in retrieval
      order), so the user can pick one; nothing happens on selection and
      nothing is saved.
  Every chunk's text is shown exactly as returned — no rewording or trimming.

- Failure handling: if ``build_store`` or ``retrieve_for_score`` raises
  anything, app.py catches it and shows a single calm st.markdown message
  instead of crashing or showing a traceback. The exact message this suite
  requires is:
      "We couldn't load your personalized suggestions right now. Please
      retake the quiz in a moment."
  (RETRIEVAL_ERROR_TEXT below.) It must NOT show the placeholder
  COMING_SOON_TEXT in the failure case.

- Retake: clicking Retake clears the retrieved content along with the
  style/tier result, returning to the exact blank state (subtitle + progress
  restored, no behavior radio, no retrieved text, no result markdown), the
  same restoration the 2a tests already cover for the existing elements.

PATCHING NOTE: AppTest re-executes app.py's whole script (imports included)
on every run, so patching "content_library_store.retrieve_for_score" and
"content_library_store.build_store" works — those modules stay loaded between
reruns, so when app.py's "from content_library_store import ..." re-executes,
it picks up whatever is currently on the module. This is the same technique
test_quiz_screen.py uses for src.scoring.score_assessment.

These tests deliberately avoid building or reading a real vector store, so
they are self-contained: the build-on-demand and retrieval calls are patched
with canned behaviour. Only the vendored-folder existence test touches the
real filesystem, and it passes as soon as the 40 files are vendored.
"""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from content_library_store import QueryResult

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_PATH = REPO_ROOT / "tests" / "fixtures" / "known_answers.json"
KB_DIR = REPO_ROOT / "content_library"

CHOICE_LABELS = ["Never", "Occasionally", "Frequently", "Always"]

COMING_SOON_TEXT = (
    "More personalized coaching based on your specific answers is coming soon."
)

RETRIEVAL_ERROR_TEXT = (
    "We couldn't load your personalized suggestions right now. "
    "Please retake the quiz in a moment."
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


def _submit(at):
    _by_key(at.button, "submit_btn").click().run()


def _fresh_store_dir():
    """A store path that does not yet exist, unique per call.

    app.py only calls build_store when the store path doesn't already exist.
    Patching content_library_store.DEFAULT_STORE_DIR to a fresh non-existent
    path makes the "first use" tests deterministic regardless of whether some
    other test in the full suite has already built the real store.
    """
    import tempfile
    parent = Path(tempfile.mkdtemp())
    store = parent / "content_library"
    assert not store.exists()
    return str(store)


def _canned_results():
    """Six canned QueryResults with distinctive, exactly-known text.

    Every text is deliberately unique so a test can assert each chunk's text
    appears verbatim on the result screen without ambiguity.
    """
    return [
        QueryResult("philosophy_blend",
                    "Philosophy: there is no single best networking style.",
                    "philosophy", {"layer": "philosophy", "piece": "blend"},
                    None),
        QueryResult("archetype_connector_identity",
                    "Identity: you are a natural connector of people.",
                    "archetype",
                    {"layer": "archetype", "archetype": "connector",
                     "piece": "identity"}, None),
        QueryResult("archetype_connector_strengths",
                    "Strengths: your gift is introducing people who fit.",
                    "archetype",
                    {"layer": "archetype", "archetype": "connector",
                     "piece": "strengths"}, None),
        QueryResult("behavior_q01_introduce_yourself_building",
                    "Behavior one: introduce yourself to one new person this week.",
                    "behavior", {"layer": "behavior", "mode": "building"}, 0.11),
        QueryResult("behavior_q02_share_updates_building",
                    "Behavior two: share one useful update with a contact.",
                    "behavior", {"layer": "behavior", "mode": "building"}, 0.22),
        QueryResult("behavior_q03_participate_in_orgs_building",
                    "Behavior three: join one group and take part.",
                    "behavior", {"layer": "behavior", "mode": "building"}, 0.33),
    ]


def _patched_retrieval_app(canned=None):
    """A fresh AppTest with the content-library pipeline patched so the tests
    never touch a real vector store or vendored files. Covers the on-demand
    build, the intro-screen philosophy fetch (get_item), and the post-submit
    retrieval.

    The patches are started *before* the app's first run, so even the very
    first run's intro-screen philosophy fetch is mocked.
    """
    from types import SimpleNamespace

    canned = canned if canned is not None else _canned_results()
    patchers = [
        patch("content_library_store.build_store"),
        patch("content_library_store.get_item",
              return_value=SimpleNamespace(text=canned[0].text)),
        patch("content_library_store.retrieve_for_score", return_value=canned),
    ]
    for p in patchers:
        p.start()
    at = _fresh_app()
    return at, patchers


def _submit_with_patched_retrieval(at):
    _answer_all(at, FIXTURES[0]["answers"])
    _submit(at)


# ---------------------------------------------------------------------------
# AC1: the 40 content-library markdown files exist in this repo under a
# clearly named folder.
# ---------------------------------------------------------------------------

def test_vendored_knowledge_base_folder_contains_forty_markdown_files():
    """The vendored folder must exist and hold exactly 40 .md files."""
    if not KB_DIR.is_dir():
        raise AssertionError(
            f"vendored content-library folder not found at {KB_DIR}. Vendor "
            "the 40 markdown files from werkitgirls-resources/knowledge_base "
            "as part of this item."
        )
    files = [p for p in KB_DIR.iterdir() if p.is_file() and p.suffix == ".md"]
    assert len(files) == 40, f"expected 40 .md files, found {len(files)}"


# ---------------------------------------------------------------------------
# AC2: the store builds automatically on first use (no manual step, no error
# shown to the user).
# ---------------------------------------------------------------------------

def test_store_builds_automatically_on_first_use():
    at = _fresh_app()
    fresh_store = _fresh_store_dir()
    with patch("content_library_store.DEFAULT_STORE_DIR", fresh_store), \
         patch("content_library_store.build_store") as build, \
         patch("content_library_store.get_item",
               return_value=SimpleNamespace(text="intro philosophy")), \
         patch("content_library_store.retrieve_for_score",
               return_value=_canned_results()) as retrieve:
        _answer_all(at, FIXTURES[0]["answers"])
        _submit(at)

        build.assert_called_once()
        assert list(at.exception) == []
        assert retrieve.called


# ---------------------------------------------------------------------------
# AC3: the philosophy text shows on the intro screen (before any answers);
# the winning style's identity and strengths text shows on the result screen
# after submit. Each matches the stored chunk exactly.
# ---------------------------------------------------------------------------

def test_intro_screen_shows_the_philosophy_text_before_any_answers():
    at, patchers = _patched_retrieval_app()
    try:
        # A fresh load, before any question is answered.
        texts = [m.value for m in at.markdown]
        assert _canned_results()[0].text in texts, texts
    finally:
        for p in patchers:
            p.stop()


def test_result_screen_shows_identity_and_strengths_but_not_philosophy():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        texts = [m.value for m in at.markdown]
        assert "Identity: you are a natural connector of people." in texts, texts
        assert "Strengths: your gift is introducing people who fit." in texts, texts
        # Philosophy now lives on the intro screen, not the result screen.
        assert _canned_results()[0].text not in texts, texts
    finally:
        for p in patchers:
            p.stop()


def test_result_screen_shows_all_three_behavior_chunk_texts():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        behavior_radios = [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
        assert len(behavior_radios) == 1, behavior_radios
        radio = behavior_radios[0]
        option_labels = list(radio.options)
        for behavior in _canned_results()[3:]:
            assert behavior.text in option_labels, (
                f"behavior chunk text not shown verbatim as a radio option: "
                f"{behavior.text!r}"
            )
    finally:
        for p in patchers:
            p.stop()


def test_coming_soon_placeholder_is_gone_once_real_content_is_shown():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        texts = [m.value for m in at.markdown]
        assert COMING_SOON_TEXT not in texts, (
            "the placeholder must be replaced, not shown alongside real content"
        )
    finally:
        for p in patchers:
            p.stop()


# ---------------------------------------------------------------------------
# AC4: the 3 behavior chunks are presented as a choice the user can select
# between, and nothing breaks if the user changes their selection.
# ---------------------------------------------------------------------------

def test_behavior_chunks_are_presented_as_a_choice():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        behavior_radios = [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
        assert len(behavior_radios) == 1, behavior_radios
        radio = behavior_radios[0]
        expected_options = [b.text for b in _canned_results()[3:]]
        assert radio.options == expected_options, radio.options
    finally:
        for p in patchers:
            p.stop()


def test_changing_behavior_selection_does_not_break_the_app():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        behavior_radios = [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
        assert len(behavior_radios) == 1
        radio = behavior_radios[0]

        radio.set_value(_canned_results()[4].text).run()
        assert list(at.exception) == []

        radio.set_value(_canned_results()[5].text).run()
        assert list(at.exception) == []
    finally:
        for p in patchers:
            p.stop()


def test_behavior_choice_has_no_pre_selected_value_on_first_appearance():
    """Regression: on first reaching the result screen, before the user clicks
    anything, the behavior-choice radio must have value None (nothing
    pre-chosen) — the same explicit-choice rule the 15 quiz questions follow."""
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        behavior_radios = [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
        assert len(behavior_radios) == 1, behavior_radios
        radio = behavior_radios[0]
        assert radio.value is None, (
            "the behavior-choice radio must have no pre-selected option"
        )
    finally:
        for p in patchers:
            p.stop()


# Status-line and header wording for the action-plan block (#4g 11/15
# amendment, exact wording from tools.werkitgirls.com).
STATUS_PROMPT_TEXT = "Pick 1 to commit to"
STATUS_CONFIRM_TEXT = "You've got your move. Now go do it."
ACTION_PLAN_HEADER = "Your action plan — pick one and start"
ACTION_PLAN_INSTRUCTION = (
    "These are moves that fit your style. Pick the one that feels most "
    "doable right now and commit to it this week."
)


def _injected_style(at):
    """The app's injected <style> block(s), as raw strings, if any.

    The result screen is expected to inject custom CSS via
    st.markdown(<style>...</style>, unsafe_allow_html=True) to turn the
    behavior-choice radio into bordered option cards. AppTest exposes those
    injected strings as markdown element values.
    """
    return [m.value for m in at.markdown if "<style" in m.value]


def _behavior_radio(at):
    radios = [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
    assert len(radios) == 1, radios
    return radios[0]


def _ordered_main_elements(at):
    """The result screen's top-level elements in render order.

    ``at.main.children`` is a dict keyed by position index, each entry a single
    element in the order it was rendered, so this returns a list of
    (position, element) pairs preserving that order.
    """
    children = at.main.children
    return [(pos, children[pos]) for pos in sorted(children.keys())]


def _first_position(at, predicate):
    """The render position of the first top-level element matching predicate."""
    for pos, el in _ordered_main_elements(at):
        if predicate(el):
            return pos
    raise AssertionError("no matching element found in render order")


def _markdown_value(el):
    return getattr(el, "value", None)


def test_behavior_cards_inject_css_that_gives_them_visible_spacing():
    """PROXY (limits noted): verifies the app injects a CSS rule that gives
    the behavior-choice option cards visible spacing between them.

    WHAT THIS CATCHES: an app that forgot to add any card-spacing CSS at all
    (no `gap`/`margin`/`padding` rule targeting the option cards) will fail
    here, because the injected <style> block won't contain a spacing rule.

    WHAT IT CANNOT CATCH: AppTest has no real browser, so it cannot compute or
    measure actual rendered pixels. A spacing rule present but too small to be
    visually noticeable, or a rule targeting the wrong element, would pass
    this proxy while still looking wrong on screen. That pixel-level check is
    a manual/visual-review step, out of reach of AppTest.
    """
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        styles = _injected_style(at)
        assert styles, (
            "expected the app to inject a <style> block with card-spacing CSS, "
            "but none was found"
        )
        joined = "\n".join(styles)
        # A spacing rule must be present for the option cards: `gap` on a
        # flex/grid container, or vertical margin/padding on the cards.
        assert any(
            token in joined.lower()
            for token in ("gap:", "margin-bottom:", "margin-top:", "padding:")
        ), joined
    finally:
        for p in patchers:
            p.stop()


def test_behavior_cards_inject_css_that_highlights_the_full_selected_card():
    """PROXY (limits noted): verifies the app injects a CSS rule that changes
    the selected option card's background/border across the full card, not
    just the radio dot.

    Streamlit's radio options don't expose a usable `:checked` state in this
    version; the selected option's <label> gains a real `data-selected="true"`
    attribute instead (confirmed via Playwright DOM inspection). The CSS
    targets `label[data-selected="true"]`.

    WHAT THIS CATCHES: an app that only relies on Streamlit's default radio
    dot feedback (no rule that recolors/borders the card on selection) will
    fail here, because the injected <style> block won't contain a
    `data-selected="true"` selector applying background/border.

    WHAT IT CANNOT CATCH: AppTest cannot render CSS, so it cannot confirm the
    highlight actually appears visually on the right card or is large enough
    to read as "across the full card". A rule that is present but targets the
    wrong element, or is too subtle, would pass this proxy. The visual
    confirmation is a manual/visual-review step.
    """
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        styles = _injected_style(at)
        assert styles, (
            "expected the app to inject a <style> block with a full-card "
            "highlight rule, but none was found"
        )
        joined = "\n".join(styles)
        assert 'data-selected="true"' in joined, joined
        # The selection rule must change the card's background and/or border
        # (a full-card highlight), not only the radio dot's accent color.
        assert any(token in joined.lower() for token in ("background", "border")), joined
    finally:
        for p in patchers:
            p.stop()


@pytest.mark.parametrize("behavior_index", [0, 1, 2])
def test_status_line_changes_from_prompt_to_confirm_for_each_behavior_option(behavior_index):
    """The status line under the behavior options starts as a prompt and
    becomes a confirming line once a choice is made (the same pattern as
    tools.werkitgirls.com). Checked for every one of the three behavior
    options, each starting from a fresh no-selection state so a regression
    that broke the swap for only the second or third option is still caught."""
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        # Before any selection: the prompt is shown, the confirming line is not.
        texts = [m.value for m in at.markdown]
        assert STATUS_PROMPT_TEXT in texts, texts
        assert STATUS_CONFIRM_TEXT not in texts, texts

        # Pick this behavior option.
        radio = _behavior_radio(at)
        radio.set_value(_canned_results()[3 + behavior_index].text).run()

        # After the selection: the confirming line is shown, the prompt is not.
        texts = [m.value for m in at.markdown]
        assert STATUS_CONFIRM_TEXT in texts, texts
        assert STATUS_PROMPT_TEXT not in texts, texts
    finally:
        for p in patchers:
            p.stop()


def test_action_plan_block_renders_in_this_order_header_instruction_radio_status():
    """The action-plan block must render in order: header, then instruction,
    then the behavior radio, then the status line. A regression that put the
    status above the radio or the instruction before the header would swap
    these positions and fail here, even though the same strings still appear
    somewhere on the page."""
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        header_pos = _first_position(
            at, lambda el: _markdown_value(el) == ACTION_PLAN_HEADER)
        instruction_pos = _first_position(
            at, lambda el: _markdown_value(el) == ACTION_PLAN_INSTRUCTION)
        # The radio may be a direct top-level child, or wrapped in a container;
        # find whichever top-level element actually carries the behavior choice.
        radio_pos = _first_position(
            at, lambda el: getattr(el, "key", "") == "behavior_choice"
            or "behavior_choice" in str(getattr(el, "key", "")))
        status_pos = _first_position(
            at, lambda el: _markdown_value(el) == STATUS_PROMPT_TEXT)

        assert header_pos < instruction_pos < radio_pos < status_pos, (
            f"action-plan block out of order: header={header_pos}, "
            f"instruction={instruction_pos}, radio={radio_pos}, "
            f"status={status_pos}"
        )
    finally:
        for p in patchers:
            p.stop()


def test_action_plan_block_shows_header_and_instruction_above_the_options():
    """The action-plan block must show a header and an instruction line above
    the behavior options, with the exact wording from tools.werkitgirls.com."""
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        texts = [m.value for m in at.markdown]
        assert ACTION_PLAN_HEADER in texts, texts
        assert ACTION_PLAN_INSTRUCTION in texts, texts
    finally:
        for p in patchers:
            p.stop()


def test_identity_and_strengths_render_side_by_side_in_two_columns():
    """The winning style's identity and strengths text must be side by side
    (two columns), not stacked one under the other."""
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        columns = list(at.columns)
        assert len(columns) == 2, (
            f"expected exactly two columns for identity/strengths, got "
            f"{len(columns)}"
        )
        # Each column holds the identity/strengths markdown, confirming they
        # are laid out in separate columns rather than a single column.
        for col in columns:
            assert col.children, "a column should contain markdown content"
    finally:
        for p in patchers:
            p.stop()


# ---------------------------------------------------------------------------
# AC5: Retake clears this new content along with the style/tier result, back
# to a blank quiz with no retrieved content showing.
# ---------------------------------------------------------------------------

def test_retake_clears_retrieved_content_back_to_blank_state():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        assert [m.value for m in at.markdown]  # content is showing

        _by_key(at.button, "retake_btn").click().run()

        # The user-specific result content (style, score, identity, strengths,
        # behaviors, behavior choice) is cleared, while the permanent
        # intro-screen philosophy text remains.
        texts = [m.value for m in at.markdown]
        assert not any("Your networking style:" in t for t in texts), texts
        assert not any("Your overall score:" in t for t in texts), texts
        assert not any("Your superpower" in t for t in texts), texts
        assert not any("Your growth opportunity" in t for t in texts), texts
        assert not any(b.text in texts for b in _canned_results()[3:]), texts
        assert not [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
        assert list(at.caption) != []
        assert len(list(at.progress)) == 1
        assert list(at.progress)[0].text == "0 of 15 answered"
        # The permanent intro philosophy text is still there.
        assert _canned_results()[0].text in texts, texts
    finally:
        for p in patchers:
            p.stop()


# ---------------------------------------------------------------------------
# AC6: a retrieval or store-build failure is caught and shown as a clear,
# non-crashing message rather than an unhandled error page.
# ---------------------------------------------------------------------------

def test_retrieval_failure_shows_graceful_message_not_a_crash():
    at = _fresh_app()
    with patch("content_library_store.build_store"), \
         patch("content_library_store.get_item",
               return_value=SimpleNamespace(text="intro philosophy")), \
         patch("content_library_store.retrieve_for_score",
               side_effect=RuntimeError("boom")):
        _answer_all(at, FIXTURES[0]["answers"])
        _submit(at)

        assert list(at.exception) == []
        texts = [m.value for m in at.markdown]
        assert RETRIEVAL_ERROR_TEXT in texts, texts


def test_store_build_failure_shows_graceful_message_not_a_crash():
    at = _fresh_app()
    fresh_store = _fresh_store_dir()
    with patch("content_library_store.DEFAULT_STORE_DIR", fresh_store), \
         patch("content_library_store.build_store",
               side_effect=RuntimeError("build boom")), \
         patch("content_library_store.get_item",
               return_value=SimpleNamespace(text="intro philosophy")), \
         patch("content_library_store.retrieve_for_score",
               return_value=_canned_results()):
        _answer_all(at, FIXTURES[0]["answers"])
        _submit(at)

        assert list(at.exception) == []
        texts = [m.value for m in at.markdown]
        assert RETRIEVAL_ERROR_TEXT in texts, texts


def test_failure_message_does_not_show_the_placeholder():
    at = _fresh_app()
    with patch("content_library_store.build_store"), \
         patch("content_library_store.get_item",
               return_value=SimpleNamespace(text="intro philosophy")), \
         patch("content_library_store.retrieve_for_score",
               side_effect=RuntimeError("boom")):
        _answer_all(at, FIXTURES[0]["answers"])
        _submit(at)

        texts = [m.value for m in at.markdown]
        assert COMING_SOON_TEXT not in texts, texts


# ---------------------------------------------------------------------------
# Lifecycle guard: no exception anywhere through the full flow.
# ---------------------------------------------------------------------------

def test_no_exceptions_through_full_flow_with_retrieval():
    at, patchers = _patched_retrieval_app()
    try:
        assert list(at.exception) == []
        _answer_all(at, FIXTURES[0]["answers"])
        assert list(at.exception) == []
        _submit(at)
        assert list(at.exception) == []
        _by_key(at.button, "retake_btn").click().run()
        assert list(at.exception) == []
    finally:
        for p in patchers:
            p.stop()


# ---------------------------------------------------------------------------
# #4h: the single Retake button moves from the top of the page to the very
# bottom, immediately after the action-plan status line. Exactly one Retake
# button exists once a result is present, none before, and it keeps clearing
# the same state as before.
# ---------------------------------------------------------------------------

def _retake_buttons(at):
    """All buttons whose label is exactly 'Retake'."""
    return [b for b in at.button if b.label == "Retake"]


def test_retake_button_exists_and_is_labeled_exactly_retake_when_result_present():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        retake = _by_key(at.button, "retake_btn")
        assert retake is not None, "expected a Retake button once a result exists"
        assert retake.label == "Retake", retake.label
    finally:
        for p in patchers:
            p.stop()


def test_retake_button_is_the_last_element_immediately_after_the_status_line():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        ordered = _ordered_main_elements(at)
        last_pos, last_el = ordered[-1]
        assert getattr(last_el, "key", "") == "retake_btn", (
            f"Retake must be the last element; the last element was "
            f"{type(last_el).__name__} key={getattr(last_el, 'key', None)}"
        )

        status_pos = _first_position(
            at, lambda el: _markdown_value(el) == STATUS_PROMPT_TEXT)
        assert last_pos == status_pos + 1, (
            f"Retake must come immediately after the status line: status="
            f"{status_pos}, retake={last_pos}"
        )
    finally:
        for p in patchers:
            p.stop()


def test_no_retake_button_at_the_top_under_the_title():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        title_pos = _first_position(at, lambda el: type(el).__name__ == "Title")
        ordered = _ordered_main_elements(at)
        next_el = ordered[title_pos + 1][1]
        assert getattr(next_el, "key", "") != "retake_btn", (
            "the Retake button must not sit directly under the title"
        )
    finally:
        for p in patchers:
            p.stop()


def test_exactly_one_retake_button_when_a_result_is_present():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)

        retakes = _retake_buttons(at)
        assert len(retakes) == 1, (
            f"expected exactly one Retake button, found {len(retakes)}"
        )
    finally:
        for p in patchers:
            p.stop()


def test_no_retake_button_appears_before_a_result_exists():
    at, patchers = _patched_retrieval_app()
    try:
        # A fresh load with no answers has no result yet.
        assert _retake_buttons(at) == [], "no Retake may appear before a result"
    finally:
        for p in patchers:
            p.stop()


def test_clicking_retake_clears_state_and_makes_questions_editable_again():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        # After submit, the questions are locked and show the chosen answers.
        for i in range(15):
            assert _by_key(at.radio, f"q{i + 1}").disabled is True

        _by_key(at.button, "retake_btn").click().run()

        # Result content is gone, the behavior choice is gone, and the 15
        # questions are cleared and editable again.
        texts = [m.value for m in at.markdown]
        assert not any("Your networking style:" in t for t in texts), texts
        assert not any("Your overall score:" in t for t in texts), texts
        assert not [
            r for r in at.radio if getattr(r, "key", "") == "behavior_choice"
        ], "behavior choice should be cleared"
        for i in range(15):
            radio = _by_key(at.radio, f"q{i + 1}")
            assert radio.value is None, f"q{i + 1} should be cleared"
            assert radio.disabled is False, f"q{i + 1} should be editable again"
    finally:
        for p in patchers:
            p.stop()