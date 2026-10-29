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


def _load_questions():
    """The 15 question texts, word for word, in the file's order."""
    text = QUESTIONS_PATH.read_text()
    return re.findall(r"^\d+\.\s+(.+)$", text, flags=re.MULTILINE)


QUESTIONS = _load_questions()

if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

submitted = st.session_state["submitted"]

if submitted:
    if st.button("Retake", key="retake_btn"):
        for n in range(1, 16):
            st.session_state[f"q{n}"] = None
        st.session_state.pop("result", None)
        st.session_state["submitted"] = False
        st.rerun()

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
    st.session_state["result"] = score_assessment(numbers)
    st.session_state["submitted"] = True
    st.rerun()

result = st.session_state.get("result")
if result is not None:
    st.markdown(DISPLAY_NAMES[result["winner"]])
    st.markdown(DISPLAY_NAMES[result["tier"]])