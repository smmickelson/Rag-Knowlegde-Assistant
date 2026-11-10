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

from content_library_store import DEFAULT_STORE_DIR, build_store, retrieve_for_score
from src.scoring import score_assessment

REPO_ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = REPO_ROOT / "docs" / "quiz-questions.md"
CONTENT_LIBRARY_DIR = REPO_ROOT / "content_library"

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


def _load_personalized_content(result):
    """Build the content-library store on demand, then retrieve the 6
    chunks personalized to ``result`` (item #4a's retrieve_for_score).

    Builds the store from the vendored ``content_library/`` files only if
    it doesn't already exist at DEFAULT_STORE_DIR -- no manual setup step,
    and a store already on disk is never rebuilt. Raises whatever
    build_store/retrieve_for_score raise; the caller is responsible for
    catching that and showing a graceful message instead of a crash.
    """
    if not Path(DEFAULT_STORE_DIR).exists():
        build_store(CONTENT_LIBRARY_DIR, DEFAULT_STORE_DIR)
    return retrieve_for_score(DEFAULT_STORE_DIR, result)


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
    st.markdown(f"Your tier: {DISPLAY_NAMES[result['tier']]}")

    if st.session_state.get("retrieval_failed"):
        st.markdown(RETRIEVAL_ERROR_TEXT)
    else:
        retrieved = st.session_state.get("retrieved_content")
        if retrieved:
            philosophy, identity, strengths, *behaviors = retrieved
            st.markdown(philosophy.text)
            st.markdown(identity.text)
            st.markdown(strengths.text)
            for behavior in behaviors:
                st.markdown(behavior.text)
            st.radio(
                "Pick one next step to focus on:",
                options=[behavior.text for behavior in behaviors],
                key="behavior_choice",
            )