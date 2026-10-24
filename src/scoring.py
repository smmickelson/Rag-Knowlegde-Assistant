"""Score the 15-question networking self-assessment (specs/01-scoring-port.md).

Pure scoring logic: takes the 15 answers a person gave (each 1 to 4, in
question order) and returns the overall score, the four style totals, the
winning style, and its tier. No screens, no coaching text, no AI, no
knowledge-base reads, and no network requests.
"""

# Which questions (1-indexed) count toward each style. Some questions count
# toward more than one style, matching the reference scoring behavior.
_STYLE_QUESTIONS = {
    "connector": [4, 8, 10, 13, 14, 15],
    "cultivator": [1, 2, 5, 7, 9, 12],
    "opportunitySeeker": [3, 6, 8, 11, 13, 14],
    "communityBuilder": [3, 4, 6, 10, 11, 15],
}

# Iteration order for styles; on an exact tie the later style wins.
_STYLE_ORDER = [
    "connector",
    "cultivator",
    "opportunitySeeker",
    "communityBuilder",
]


def _tier(total):
    """Return the tier for a winning total: low, mid, or high."""
    if total >= 20:
        return "high"
    if total >= 12:
        return "mid"
    return "low"


def _type_name(value):
    """The name of ``value``'s type, read without running class code.

    The scorer only names the type of input it is about to reject. That input
    can be an instance of a class whose own code misbehaves when its name is
    asked for (a metaclass override or a ``name`` property). Reading straight
    from the built-in descriptor never runs any of that class's code.
    """
    return type.__dict__["__name__"].__get__(type(value))


def score_assessment(answers):
    """Score 15 answers and return the result dict.

    Returns a dict with the four style totals, ``overall`` (the sum of all 15
    answers, informational only), ``winner`` (the style with the highest
    total, later style winning an exact tie), and ``tier`` (low/mid/high for
    the winner only).

    Raises ``ValueError`` if ``answers`` is not exactly the built-in list
    holding exactly 15 whole numbers from 1 to 4, checking in order and
    stopping at the first problem. Only exact types are accepted, so no code
    from a subclass ever runs. The input is only read, never changed.
    """
    if type(answers) is not list:
        raise ValueError(
            "answers must be a list of exactly 15 whole numbers from 1 to 4, "
            f"but received a "
            f"{_type_name(answers)}"
        )
    if len(answers) != 15:
        raise ValueError(
            "answers must be a list of exactly 15 whole numbers from 1 to 4, "
            f"but received a list of length {len(answers)}"
        )
    for index, value in enumerate(answers):
        question = index + 1
        if type(value) is not int:
            raise ValueError(
                f"question {question} must be a whole number from 1 to 4, "
                f"but received a "
                f"{_type_name(value)}"
            )
        if value < 1 or value > 4:
            raise ValueError(
                f"question {question} must be a whole number from 1 to 4, "
                f"but received a {_type_name(value)} "
                "outside that range"
            )

    totals = {}
    for style, questions in _STYLE_QUESTIONS.items():
        totals[style] = sum(answers[q - 1] for q in questions)

    winner = _STYLE_ORDER[0]
    for style in _STYLE_ORDER[1:]:
        if totals[style] >= totals[winner]:
            winner = style

    return {
        "connector": totals["connector"],
        "cultivator": totals["cultivator"],
        "opportunitySeeker": totals["opportunitySeeker"],
        "communityBuilder": totals["communityBuilder"],
        "overall": sum(answers),
        "winner": winner,
        "tier": _tier(totals[winner]),
    }