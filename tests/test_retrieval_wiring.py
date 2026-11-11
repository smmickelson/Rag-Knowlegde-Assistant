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
from unittest.mock import patch

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
    """A fresh AppTest with retrieval (and the on-demand build) patched so the
    tests never touch a real vector store or vendored files."""
    canned = canned if canned is not None else _canned_results()
    at = _fresh_app()
    patchers = [
        patch("content_library_store.build_store"),
        patch("content_library_store.retrieve_for_score", return_value=canned),
    ]
    for p in patchers:
        p.start()
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
         patch("content_library_store.retrieve_for_score",
               return_value=_canned_results()) as retrieve:
        _answer_all(at, FIXTURES[0]["answers"])
        _submit(at)

        build.assert_called_once()
        assert list(at.exception) == []
        assert retrieve.called


# ---------------------------------------------------------------------------
# AC3: after submitting, the result screen shows the philosophy_blend text,
# the winning style's identity and strengths text, and all 3 ranked behavior
# chunks' text — each matching the stored chunk exactly.
# ---------------------------------------------------------------------------

def test_result_screen_shows_philosophy_identity_and_strengths_text():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        texts = [m.value for m in at.markdown]
        assert "Philosophy: there is no single best networking style." in texts, texts
        assert "Identity: you are a natural connector of people." in texts, texts
        assert "Strengths: your gift is introducing people who fit." in texts, texts
    finally:
        for p in patchers:
            p.stop()


def test_result_screen_shows_all_three_behavior_chunk_texts():
    at, patchers = _patched_retrieval_app()
    try:
        _submit_with_patched_retrieval(at)
        texts = [m.value for m in at.markdown]
        for behavior in _canned_results()[3:]:
            assert behavior.text in texts, (
                f"behavior chunk text not shown verbatim: {behavior.text!r}"
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

        # No retrieved content, no behavior choice, subtitle + progress back.
        assert [m.value for m in at.markdown] == [], [m.value for m in at.markdown]
        assert not [r for r in at.radio if getattr(r, "key", "") == "behavior_choice"]
        assert list(at.caption) != []
        assert len(list(at.progress)) == 1
        assert list(at.progress)[0].text == "0 of 15 answered"
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