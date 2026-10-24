# 18b - Scorer rejects invalid input

**Story:** Enabler: As a developer, I get a clear error when the scorer receives anything other than exactly 15 whole numbers from 1 to 4.

**Backlog item:** #18b

**Status:** shipped

## What it does

Before scoring anything, `score_assessment(answers)` checks its input using only exact type tests (is it exactly Python's built-in `list`, is each answer exactly Python's built-in `int`), so no custom code from a subclass ever runs. It accepts only a list of exactly 15 whole numbers, each from 1 to 4. Anything else raises a `ValueError`. The message says what was wrong, names the type it received (for example `tuple` or `str`), and for an invalid answer gives the question number. It never includes the offending value itself. Checks run in this order and stop at the first problem: is it a list, is it 15 long, then each answer from question 1 to question 15 (whole number first, then 1 to 4). Valid input is scored exactly as before, and invalid input is never changed or corrected.

**What "invalid" means here:** an invalid answer is anything other than the whole numbers 1, 2, 3, or 4, such as a skipped question, a number like 7, or a value like 2.5 or the word "three". It is never a judgment of a person's networking habits, since every answer from 1 to 4 is a valid choice. Invalid input is anything other than a list of exactly 15 valid answers.

## What it does NOT do

- Change any scoring rule, tier, tie-break, or the seven returned values for valid input.
- Convert invalid input into valid input. The text "3" and the decimal 3.0 are rejected, not fixed.
- Accept subclasses of `list` or `int`, numbers from other libraries, or other containers (tuples, generators, dictionaries), even when the values look right.
- Put the offending value in any error message.
- Limit the size of incoming requests. That is a deployment concern for a later item.
- Stop a person from choosing an invalid answer on the quiz screen. That is item 18a.
- Change `tests/test_scoring.py`. New tests go in `tests/test_validation.py`.

## Acceptance criteria

- [ ] It's done when all 41 tests in `tests/test_scoring.py` still pass with that file unchanged.
- [ ] It's done when a list of 14, a list of 16, and an empty list each raise a `ValueError` whose message contains "15".
- [ ] It's done when `None`, a text string, a single number, a tuple, and a dictionary passed in place of the list each raise a `ValueError` whose message contains "list" and the name of the type received, and a custom subclass of `list` holding 15 valid answers is rejected the same way.
- [ ] It's done when each of the text "3", `None`, 2.5, 3.0, `True`, and `False` placed at question 7 of an otherwise valid list raises a `ValueError` whose message contains "question 7" and "whole number", and a custom subclass of `int` with the value 3 at question 7 is rejected the same way.
- [ ] It's done when 0, 5, and -1 at question 7 each raise a `ValueError` whose message contains "question 7" and "1 to 4", while 1 and 4 at that position are scored normally.
- [ ] It's done when a list with an invalid answer at question 3 and another at question 5 raises an error naming question 3 only.
- [ ] It's done when the text "secret-value-123" placed at question 7 raises an error whose message contains "question 7" and "str" but not "secret-value-123".
- [ ] It's done when a rejected list equals an unmodified copy of itself afterward, and submitting the same invalid list twice gives the same error message both times.
- [ ] It's done when `python3 -m pytest` runs with no failures.

## Question round

Where these questions came from: ChatGPT's question round on 2026-10-22 (7 questions, within the 10-question limit), using the prompt in `docs/course/routine.md`, section 2. The answers are Sharon's decisions.

| # | Question | Answer |
|---|---|---|
| 1 | Does "type `int`" mean exactly Python's built-in `int`, rejecting subclasses and integer types from other libraries even when the value is 1 to 4? | Yes. Each answer must be exactly the built-in `int`. Subclasses and numbers from other libraries are rejected, as are `True` and `False`. |
| 2 | Does "a list" include subclasses of `list`? | No. The input must be exactly the built-in `list`. A subclass of `list` is rejected with the same message as any other non-list. |
| 3 | What must the message contain when the input is not a list, and are tuples, generators, dictionaries, and other containers all rejected the same way? | Yes, all rejected the same way. The message says the answers must be a list and names the type received, for example "tuple". |
| 4 | Must error messages follow exact wording and capitalization? | No. Tests check only the required phrases ("15", "list", "question N", "whole number", "1 to 4", and the type name), ignoring capitalization. The rest of the wording is free. |
| 5 | Should messages include the offending value or its type, and how are sensitive, huge, or unprintable values handled? | Messages include the type name of the offending value and never the value itself. That keeps private text and very long text out of messages, and a value that cannot be printed cannot break the message. |
| 6 | If a subclass with custom behavior raises an exception during validation, must it become a `ValueError`? | Not applicable. Because only exact types are accepted, subclass code never runs during validation. Any such input is rejected with a `ValueError`. |
| 7 | Does "unchanged afterward" cover nested objects as well as the list, including repeated submissions? | Yes. Validation only reads the input and never changes it. A rejected list equals an unmodified copy of itself afterward, and the same invalid list submitted twice gives the same error both times. Nested lists are rejected as non-whole numbers, so they are never changed either. |

## Amendments

| Date | Change | Why |
|---|---|---|
| 2026-10-24 | The out-of-range message now names the type received, following question round row 5. No change to criteria. | Spec match review. |
| 2026-10-24 | Added and strengthened tests after the review round, plus four tests for a class that defines its own name. No change to behavior or criteria. | Security, spec match, and test quality reviews. |
| 2026-10-24 | Known limit: the type name in an error message can come from a class that gives itself a custom string as its name, and that string's own code could run when the message is built. Only code that builds such a class can trigger it, and a web request cannot. Not fixed in this item. | Security review round 2, finding 1. |
| 2026-10-22 | Added question round rows 1 to 7. Added the exact-type rule, the rule that messages never include the offending value, and four amended or new acceptance criteria. Removed the open item from Notes. | A second AI (ChatGPT) asked what the spec forgot, using the prompt from `docs/course/routine.md`, section 2. |
| 2026-10-22 | Replaced "bad" with "invalid" throughout and added a plain definition of "invalid" under What it does. No change to behavior or criteria. | The word "bad" could read as a judgment of a person's networking answers, when it means a value the scorer cannot use. |

## Notes

- Source: backlog row 18b, and the security review on PR #1 (Agent 2), which flagged that booleans, decimals, and oversized lists pass through unchecked.
- Item 1's spec deliberately left invalid input unspecified (question round rows 7, 11, and 14). This item changes that, so the item 1 spec needs an Amendments row, and backlog rows 18a and 18b need a status update, when this item merges.
- Added beyond the backlog row: the "not a list" check, the "first problem wins" rule, the exact-type rule, and the rule that messages never include the offending value.
- Numbers from other libraries are rejected by the exact-type rule but are not tested directly, because those libraries are not part of the test environment. A custom subclass of `int` stands in for them.