"""Quiz screen (specs/18a-quiz-screen.md).

A single Streamlit page showing all 15 questions from
docs/quiz-questions.md. Each question offers the four choices Never,
Occasionally, Frequently, Always. Nothing is pre-selected; Submit stays
disabled until all 15 have an answer. Submitting passes the chosen labels
as the numbers 1 to 4, in question order, to score_assessment, then shows
the winning style and its tier with display names. Retake clears
everything back to a fresh page. No answer is ever saved anywhere.
"""

import re
from pathlib import Path

import streamlit as st

from src.scoring import score_assessment

REPO_ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = REPO_ROOT / "docs" / "quiz-questions.md"
CONTENT_LIBRARY_DIR = REPO_ROOT / "content_library"
PHILOSOPHY_BLEND_ID = "philosophy_blend"
MAX_OVERALL_SCORE = 60

CHOICE_LABELS = ["Never", "Occasionally", "Frequently", "Always"]
CHOICE_VALUES = {"Never": 1, "Occasionally": 2, "Frequently": 3, "Always": 4}

DISPLAY_NAMES = {
    "connector": "Connector",
    "cultivator": "Cultivator",
    "opportunitySeeker": "Opportunity Seeker",
    "communityBuilder": "Community Builder",
    "low": "Low",
    "mid": "Mid",
    "high": "High",
}

# One fixed, non-personalized tagline per style, shown in quotes under the
# style name on the result screen. Plain lookup, no retrieval or ranking
# involved -- same pattern as DISPLAY_NAMES above.
STYLE_TAGLINES = {
    "connector": "Let me introduce you two.",
    "cultivator": "I'd rather have five real ones than fifty followers.",
    "opportunitySeeker": "If there's a seat at the table, I'm pulling up a chair.",
    "communityBuilder": "We go further together.",
}

HEADER_TEXT = "What Kind of Networker Are You?"
SUBTITLE_TEXT = (
    "Connector, Cultivator, Opportunity Seeker, or Community Builder — "
    "15 quick questions, instant answer."
)
RETRIEVAL_ERROR_TEXT = (
    "We couldn't load your personalized suggestions right now. "
    "Please retake the quiz in a moment."
)


def _load_questions():
    """The 15 question texts, word for word, in the file's order."""
    text = QUESTIONS_PATH.read_text()
    return re.findall(r"^\d+\.\s+(.+)$", text, flags=re.MULTILINE)


def _ensure_content_library_store():
    """Build the content-library store from the vendored files, if it
    doesn't already exist at DEFAULT_STORE_DIR. A store already on disk is
    never rebuilt.

    content_library_store is imported locally (here and in every helper
    below) rather than at module load time, so that on a platform where it
    fails to import (e.g. native Windows, which lacks the fcntl module it
    relies on), the failure surfaces inside a caller's try/except instead
    of crashing the whole app at startup.
    """
    from content_library_store import DEFAULT_STORE_DIR, build_store

    if not Path(DEFAULT_STORE_DIR).exists():
        build_store(CONTENT_LIBRARY_DIR, DEFAULT_STORE_DIR)


def _load_personalized_content(result):
    """Build the content-library store on demand, then retrieve the 6
    chunks personalized to ``result`` (item #4a's retrieve_for_score).

    Raises whatever build_store/retrieve_for_score raise; the caller is
    responsible for catching that and showing a graceful message instead
    of a crash.
    """
    from content_library_store import DEFAULT_STORE_DIR, retrieve_for_score

    _ensure_content_library_store()
    return retrieve_for_score(DEFAULT_STORE_DIR, result)


def _load_philosophy_text():
    """The philosophy_blend chunk's text -- the same for everyone,
    not personalized -- shown on the intro screen before any question is
    answered. Raises whatever build_store/get_item raise; the caller is
    responsible for catching that and simply omitting the line instead of
    blocking the quiz.
    """
    from content_library_store import DEFAULT_STORE_DIR, get_item

    _ensure_content_library_store()
    return get_item(DEFAULT_STORE_DIR, PHILOSOPHY_BLEND_ID).text


QUESTIONS = _load_questions()

st.set_page_config(page_title=HEADER_TEXT)
st.title(HEADER_TEXT)

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

submitted = st.session_state["submitted"]

if submitted:
    if st.button("Retake", key="retake_btn"):
        for n in range(1, 16):
            st.session_state[f"q{n}"] = None
        st.session_state.pop("result", None)
        st.session_state.pop("retrieved_content", None)
        st.session_state.pop("retrieval_failed", None)
        st.session_state.pop("behavior_choice", None)
        st.session_state["submitted"] = False
        st.rerun()

result = st.session_state.get("result")

if result is None:
    st.caption(SUBTITLE_TEXT)

    if "philosophy_text" not in st.session_state:
        try:
            st.session_state["philosophy_text"] = _load_philosophy_text()
        except Exception:
            st.session_state["philosophy_text"] = None
    if st.session_state["philosophy_text"]:
        st.markdown(st.session_state["philosophy_text"])

    answered = sum(
        1 for n in range(1, 16) if st.session_state.get(f"q{n}") is not None
    )
    st.progress(answered / 15, text=f"{answered} of 15 answered")

answers = [
    st.radio(
        question,
        options=CHOICE_LABELS,
        index=None,
        key=f"q{n}",
        disabled=submitted,
    )
    for n, question in enumerate(QUESTIONS, start=1)
]

all_answered = all(answer is not None for answer in answers)

submit = st.button(
    "Submit",
    key="submit_btn",
    disabled=submitted or not all_answered,
)

if submit:
    numbers = [CHOICE_VALUES[answer] for answer in answers]
    score_result = score_assessment(numbers)
    st.session_state["result"] = score_result
    st.session_state["submitted"] = True
    try:
        st.session_state["retrieved_content"] = _load_personalized_content(score_result)
        st.session_state["retrieval_failed"] = False
    except Exception:
        st.session_state["retrieved_content"] = None
        st.session_state["retrieval_failed"] = True
    st.rerun()

result = st.session_state.get("result")
if result is not None:
    st.markdown(f"Your networking style: {DISPLAY_NAMES[result['winner']]}")
    st.markdown(f'"{STYLE_TAGLINES[result["winner"]]}"')
    st.markdown(f"Your overall score: {result['overall']} / {MAX_OVERALL_SCORE}")

    if st.session_state.get("retrieval_failed"):
        st.markdown(RETRIEVAL_ERROR_TEXT)
    else:
        retrieved = st.session_state.get("retrieved_content")
        if retrieved:
            _philosophy, identity, strengths, *behaviors = retrieved
            superpower_col, growth_col = st.columns(2)
            with superpower_col:
                st.markdown("**Your superpower**")
                st.markdown(identity.text)
            with growth_col:
                st.markdown("**Your growth opportunity**")
                st.markdown(strengths.text)
            st.radio(
                "Pick one next step to focus on:",
                options=[behavior.text for behavior in behaviors],
                index=None,
                key="behavior_choice",
            )