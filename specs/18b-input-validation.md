# 18b - Scorer rejects bad input

**Story:** Enabler: As a developer, I get a clear error when the scorer receives anything other than exactly 15 whole numbers from 1 to 4.

**Backlog item:** #18b

**Status:** drafted

## What it does

Before scoring anything, `score_assessment(answers)` checks its input. It accepts only a list of exactly 15 whole numbers (type `int`), each from 1 to 4. Anything else raises a `ValueError` whose message says what was wrong and, for a bad answer, which question number. Checks run in this order and stop at the first problem: is it a list, is it 15 long, then each answer from question 1 to question 15 (whole number first, then 1 to 4). Valid input is scored exactly as before, and bad input is never changed or corrected.

## What it does NOT do

- Change any scoring rule, tier, tie-break, or the seven returned values for valid input.
- Convert bad input into good input. The text "3" and the decimal 3.0 are rejected, not fixed.
- Limit the size of incoming requests. That is a deployment concern for a later item.
- Stop a person from choosing a bad answer on the quiz screen. That is item 18a.
- Change `tests/test_scoring.py`. New tests go in `tests/test_validation.py`.

## Acceptance criteria

- [ ] It's done when all 41 tests in `tests/test_scoring.py` still pass with that file unchanged.
- [ ] It's done when a list of 14, a list of 16, and an empty list each raise a `ValueError` whose message contains "15".
- [ ] It's done when `None`, a text string, and a single number passed in place of the list each raise a `ValueError`.
- [ ] It's done when each of the text "3", `None`, 2.5, 3.0, `True`, and `False` placed at question 7 of an otherwise valid list raises a `ValueError` whose message contains "question 7" and "whole number".
- [ ] It's done when 0, 5, and -1 at question 7 each raise a `ValueError` whose message contains "question 7" and "1 to 4", while 1 and 4 at that position are scored normally.
- [ ] It's done when a list with a bad answer at question 3 and another at question 5 raises an error naming question 3 only.
- [ ] It's done when a rejected list is unchanged afterward.
- [ ] It's done when `python3 -m pytest` runs with no failures.

## Question round

(Left empty for the second AI.)

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Source: backlog row 18b, and the security review on PR #1 (Agent 2), which flagged that booleans, decimals, and oversized lists pass through unchecked.
- Item 1's spec deliberately left invalid input unspecified (question round rows 7, 11, and 14). This item changes that, so the item 1 spec needs an Amendments row, and backlog rows 18a and 18b need a status update, when this item merges.
- Added beyond the backlog row, for the question round to challenge: the "not a list" check and the "first problem wins" rule.
- Open for the question round: tuples and other sequence types, numbers from other libraries, very large integers, and nested lists.