"""Tests for backlog item 18b: score_assessment rejects invalid input.

Written from specs/18b-input-validation.md. Question numbers are 1-based,
so "question 7" is index 6 in the list.
"""
import copy
import re
import subprocess
import sys
from pathlib import Path

import pytest

from src.scoring import score_assessment


# ---------------------------------------------------------------- helpers

VALID = [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3]  # exactly 15 answers


def valid_with(question, value):
    """A valid list with `value` placed at the given 1-based question."""
    answers = list(VALID)
    answers[question - 1] = value
    return answers


def rejected_text(answers):
    """Call the scorer, expect a ValueError, return its message as written.

    Fails with a plain explanation if nothing is raised, or if some other
    kind of error is raised.
    """
    try:
        score_assessment(answers)
    except ValueError as error:
        return str(error)
    except Exception as error:  # wrong kind of error
        pytest.fail(
            f"expected a ValueError, but got {type(error).__name__}: {error}"
        )
    pytest.fail("expected a ValueError, but the scorer accepted the input")


def rejected_message(answers):
    """The same message in lowercase, so phrase checks ignore capitalization."""
    return rejected_text(answers).lower()


def assert_mentions(message, *phrases):
    for phrase in phrases:
        assert phrase.lower() in message, (
            f"error message should mention {phrase!r}, but it was: {message!r}"
        )


def assert_names_question(message, number):
    """The message names exactly this question (question 1 is not question 15)."""
    assert re.search(rf"question {number}\b", message), (
        f"error message should name question {number}, but it was: {message!r}"
    )


class MyList(list):
    """A custom subclass of list."""


class MyInt(int):
    """A custom subclass of int (stands in for numbers from other libraries)."""


class ExplodingList(list):
    """A list subclass whose own code fails if the scorer ever runs it."""

    def __len__(self):
        raise RuntimeError("subclass code ran: __len__")

    def __iter__(self):
        raise RuntimeError("subclass code ran: __iter__")

    def __getitem__(self, index):
        raise RuntimeError("subclass code ran: __getitem__")


class ExplodingInt(int):
    """An int subclass whose own code fails if the scorer ever runs it."""

    def _boom(self, *args):
        raise RuntimeError("subclass code ran")

    __eq__ = __ne__ = __lt__ = __le__ = __gt__ = __ge__ = _boom
    __repr__ = __str__ = __format__ = _boom
    __hash__ = int.__hash__


class Unprintable:
    """A value that cannot be turned into text."""

    def __repr__(self):
        raise RuntimeError("cannot be printed")

    __str__ = __repr__


# ------------------------------------------- criterion 1: old tests still pass

def test_existing_scoring_tests_still_pass():
    scoring_tests = Path(__file__).parent / "test_scoring.py"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(scoring_tests), "-q",
         "-p", "no:cacheprovider"],
        capture_output=True,
        text=True,
        cwd=scoring_tests.parent.parent,
    )
    assert result.returncode == 0 and "41 passed" in result.stdout, (
        "tests/test_scoring.py should still show 41 passing tests:\n"
        + result.stdout[-1500:]
    )


def test_valid_list_is_still_scored():
    result = score_assessment(list(VALID))
    assert isinstance(result, dict), f"expected a dict of results, got {result!r}"
    assert result["overall"] == sum(VALID)


# ------------------------------------------- criterion 2: wrong length

@pytest.mark.parametrize("length", [14, 16, 0], ids=["14", "16", "empty"])
def test_wrong_length_is_rejected_and_message_says_15(length):
    message = rejected_message([1] * length)
    assert_mentions(message, "15")


# ------------------------------------------- criterion 3: not a list

NOT_LISTS = [
    pytest.param(None, id="none"),
    pytest.param("hello", id="text"),
    pytest.param(3, id="single-number"),
    pytest.param(tuple(VALID), id="tuple"),
    pytest.param({"a": 1}, id="dict"),
    pytest.param(set(VALID), id="set"),
    pytest.param((n for n in VALID), id="generator"),
]


@pytest.mark.parametrize("value", NOT_LISTS)
def test_non_list_is_rejected_with_list_and_type_name(value):
    message = rejected_message(value)
    assert_mentions(message, "list", type(value).__name__)


def test_list_subclass_is_rejected_like_any_non_list():
    message = rejected_message(MyList(VALID))
    assert_mentions(message, "list", "MyList")


# ------------------------------------------- criterion 4: not a whole number

@pytest.mark.parametrize(
    "value",
    [
        pytest.param("3", id="text-3"),
        pytest.param(None, id="none"),
        pytest.param(2.5, id="decimal-2.5"),
        pytest.param(3.0, id="decimal-3.0"),
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
        pytest.param([2, 3], id="nested-list"),
    ],
)
def test_non_whole_number_at_question_7_is_rejected(value):
    message = rejected_message(valid_with(7, value))
    assert_mentions(message, "question 7", "whole number")


def test_int_subclass_at_question_7_is_rejected():
    message = rejected_message(valid_with(7, MyInt(3)))
    assert_mentions(message, "question 7", "whole number")


@pytest.mark.parametrize(
    "value", [None, "3", 2.5, True, MyInt(3)],
    ids=["none", "text", "decimal", "true", "int-subclass"],
)
def test_message_names_the_type_of_the_invalid_answer(value):
    message = rejected_message(valid_with(7, value))
    assert_mentions(message, type(value).__name__)


# ------------------------------------------- criterion 5: out of range

@pytest.mark.parametrize("value", [0, 5, -1])
def test_out_of_range_number_at_question_7_is_rejected(value):
    message = rejected_message(valid_with(7, value))
    assert_mentions(message, "question 7", "1 to 4")


@pytest.mark.parametrize("value", [1, 4])
def test_edge_values_1_and_4_at_question_7_are_scored(value):
    answers = valid_with(7, value)
    result = score_assessment(answers)
    assert isinstance(result, dict), f"expected a dict of results, got {result!r}"
    assert result["overall"] == sum(answers)


# ------------------------------------------- review finding: first and last question

@pytest.mark.parametrize("question", [1, 15])
def test_non_whole_number_at_first_and_last_question_is_rejected(question):
    message = rejected_message(valid_with(question, "3"))
    assert_names_question(message, question)
    assert_mentions(message, "whole number")


@pytest.mark.parametrize("question", [1, 15])
def test_out_of_range_at_first_and_last_question_is_rejected(question):
    message = rejected_message(valid_with(question, 5))
    assert_names_question(message, question)
    assert_mentions(message, "1 to 4")


# ------------------------------------------- criterion 6: first problem wins

def test_error_names_question_3_when_questions_3_and_5_are_invalid():
    answers = valid_with(3, 9)
    answers[4] = "five"
    message = rejected_message(answers)
    assert_mentions(message, "question 3")
    assert "question 5" not in message, (
        f"only the first problem should be reported, but got: {message!r}"
    )


def test_length_is_checked_before_the_answers():
    answers = valid_with(3, 9)[:14]  # too short AND question 3 invalid
    message = rejected_message(answers)
    assert_mentions(message, "15")
    assert "question 3" not in message, (
        f"the length problem should win, but got: {message!r}"
    )


# ------------------------------------------- criterion 7: never show the value

def test_secret_text_at_question_7_is_not_in_the_message():
    message = rejected_message(valid_with(7, "secret-value-123"))
    assert_mentions(message, "question 7", "str")
    assert "secret-value-123" not in message, f"value leaked: {message!r}"


@pytest.mark.parametrize(
    "value, leak",
    [
        pytest.param(987654, "987654", id="out-of-range-number"),
        pytest.param(123.456, "123.456", id="decimal"),
        pytest.param([31337], "31337", id="nested-list"),
    ],
)
def test_other_invalid_values_are_not_in_the_message(value, leak):
    message = rejected_message(valid_with(7, value))
    assert leak not in message, f"value leaked: {message!r}"


def test_secret_text_in_place_of_the_list_is_not_in_the_message():
    message = rejected_message("secret-value-123")
    assert "secret-value-123" not in message, f"value leaked: {message!r}"


def test_very_long_text_is_not_repeated_in_the_message():
    message = rejected_message(valid_with(7, "LONGSECRET-" * 10_000))
    assert "longsecret" not in message, f"part of the text leaked: {message[:200]!r}"
    assert_mentions(message, "question 7", "whole number")


def test_value_that_cannot_be_printed_still_gives_a_clean_error():
    message = rejected_message(valid_with(7, Unprintable()))
    assert_mentions(message, "question 7", "whole number")


# ------------------------------------------- question round: subclass code

def test_list_subclass_code_never_runs():
    message = rejected_message(ExplodingList(VALID))
    assert_mentions(message, "list")


def test_int_subclass_code_never_runs():
    message = rejected_message(valid_with(7, ExplodingInt(3)))
    assert_mentions(message, "question 7", "whole number")


# ------------------------------------------- criterion 8: no changes, repeatable

def _invalid_lists():
    nested = valid_with(7, [1, 2])
    return [
        pytest.param(valid_with(7, "3"), id="text-answer"),
        pytest.param(valid_with(7, 9), id="out-of-range"),
        pytest.param([1] * 14, id="too-short"),
        pytest.param(nested, id="nested-list"),
    ]


@pytest.mark.parametrize("answers", _invalid_lists())
def test_rejected_list_is_unchanged_afterward(answers):
    before = copy.deepcopy(answers)
    rejected_message(answers)
    assert answers == before, f"the scorer changed the input: {answers!r}"


def test_nested_list_inside_rejected_input_is_unchanged():
    inner = [1, 2]
    answers = valid_with(7, inner)
    rejected_message(answers)
    assert inner == [1, 2], f"the nested list was changed: {inner!r}"


@pytest.mark.parametrize("answers", _invalid_lists())
def test_same_invalid_list_gives_same_message_twice(answers):
    first = rejected_text(answers)
    second = rejected_text(answers)
    assert first == second, f"messages differ: {first!r} vs {second!r}"


# ------------------------------------------- review finding: hostile type names
# Security review (Agent 2, ChatGPT): reading a type's name can run code that
# belongs to the invalid input's own class (its metaclass). The scorer must still
# raise a plain ValueError, and must never repeat text the input supplies.
#
# The hostile classes below misbehave only while the scorer is running. If
# they misbehaved all the time, pytest would crash while printing a failure.

HOSTILE_NOW = [False]


def rejected_message_while_hostile(answers):
    HOSTILE_NOW[0] = True
    try:
        return rejected_message(answers)
    finally:
        HOSTILE_NOW[0] = False


class ExplodingNameMeta(type):
    """A class definition whose own code fails when its name is requested."""

    def __getattribute__(cls, name):
        if name == "__name__" and HOSTILE_NOW[0]:
            raise RuntimeError("class code ran: __name__")
        return super().__getattribute__(name)


class LeakyNameMeta(type):
    """A class definition that lies about its name to smuggle in text."""

    def __getattribute__(cls, name):
        if name == "__name__" and HOSTILE_NOW[0]:
            return "secret-value-123"
        return super().__getattribute__(name)


class ExplodingNameList(list, metaclass=ExplodingNameMeta):
    pass


class ExplodingNameInt(int, metaclass=ExplodingNameMeta):
    pass


class LeakyNameList(list, metaclass=LeakyNameMeta):
    pass


class LeakyNameInt(int, metaclass=LeakyNameMeta):
    pass


def test_hostile_class_name_in_place_of_the_list_still_gives_valueerror():
    message = rejected_message_while_hostile(ExplodingNameList(VALID))
    assert_mentions(message, "list", "ExplodingNameList")


def test_hostile_class_name_at_question_7_still_gives_valueerror():
    message = rejected_message_while_hostile(valid_with(7, ExplodingNameInt(3)))
    assert_mentions(message, "question 7", "whole number", "ExplodingNameInt")


def test_lying_class_name_in_place_of_the_list_is_not_in_the_message():
    message = rejected_message_while_hostile(LeakyNameList(VALID))
    assert "secret-value-123" not in message, f"text leaked: {message!r}"
    assert_mentions(message, "list", "LeakyNameList")


def test_lying_class_name_at_question_7_is_not_in_the_message():
    message = rejected_message_while_hostile(valid_with(7, LeakyNameInt(3)))
    assert "secret-value-123" not in message, f"text leaked: {message!r}"
    assert_mentions(message, "question 7", "whole number", "LeakyNameInt")


# ------------------------------------------- review finding: range message
# Spec match review (Agent 2, ChatGPT): every message about an invalid answer
# must name the type received, including the out-of-range message.

@pytest.mark.parametrize("value", [0, 5, -1])
def test_out_of_range_message_names_the_type_received(value):
    message = rejected_message(valid_with(7, value))
    assert re.search(r"\bint\b", message), (
        f"the message should name the type 'int' as a word, but it was: {message!r}"
    )


# ------------------------------------------- coach finding: a class that defines its own name
# A class definition can also define a `__name__` property of its own. Asking
# for the type's name must not run that code either, and the text it supplies
# must never reach the message. (Same arming trick as above: these classes
# misbehave only while the scorer runs.)

def _real_name(cls):
    return type.__dict__["__name__"].__get__(cls)


def _exploding_name(cls):
    if HOSTILE_NOW[0]:
        raise RuntimeError("class code ran: name property")
    return _real_name(cls)


def _lying_name(cls):
    if HOSTILE_NOW[0]:
        return "secret-value-123"
    return _real_name(cls)


class ExplodingPropertyMeta(type):
    __name__ = property(_exploding_name)


class LyingPropertyMeta(type):
    __name__ = property(_lying_name)


class ExplodingPropertyList(list, metaclass=ExplodingPropertyMeta):
    pass


class ExplodingPropertyInt(int, metaclass=ExplodingPropertyMeta):
    pass


class LyingPropertyList(list, metaclass=LyingPropertyMeta):
    pass


class LyingPropertyInt(int, metaclass=LyingPropertyMeta):
    pass


def test_hostile_name_property_in_place_of_the_list_still_gives_valueerror():
    message = rejected_message_while_hostile(ExplodingPropertyList(VALID))
    assert_mentions(message, "list", "ExplodingPropertyList")


def test_hostile_name_property_at_question_7_still_gives_valueerror():
    message = rejected_message_while_hostile(valid_with(7, ExplodingPropertyInt(3)))
    assert_mentions(message, "question 7", "whole number", "ExplodingPropertyInt")


def test_lying_name_property_in_place_of_the_list_is_not_in_the_message():
    message = rejected_message_while_hostile(LyingPropertyList(VALID))
    assert "secret-value-123" not in message, f"text leaked: {message!r}"
    assert_mentions(message, "list", "LyingPropertyList")


def test_lying_name_property_at_question_7_is_not_in_the_message():
    message = rejected_message_while_hostile(valid_with(7, LyingPropertyInt(3)))
    assert "secret-value-123" not in message, f"text leaked: {message!r}"
    assert_mentions(message, "question 7", "whole number", "LyingPropertyInt")
