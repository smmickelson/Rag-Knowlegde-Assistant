# 18a - Quiz screen

**Story:** As a user taking the quiz, I answer all 15 questions on a single screen and see my networking style result. I cannot submit until every question has an answer.
**Backlog item:** #18a
**Status:** draft

## What it does

A new Streamlit page, `app.py` at the repo root, shows all 15 questions from `docs/quiz-questions.md`, in that file's order, using the question text and the four choice labels word for word as they appear in that file. Each question offers exactly four choices, in this fixed order: Never, Occasionally, Frequently, Always — matching the order in `docs/quiz-questions.md`. Nothing is selected for any question when the page first loads. Selections persist for as long as the page stays open in the browser: answering one question never clears or changes another question's answer. A browser refresh starts the page over with nothing selected; no answer is saved anywhere.

A Submit control stays disabled until every one of the 15 questions has a choice selected. Once enabled and clicked, the screen converts each chosen label to its number (Never=1, Occasionally=2, Frequently=3, Always=4), builds a list of 15 numbers in question order, and passes that list to `score_assessment` unchanged. It then displays the result using display names, not the scorer's raw values:

| Scorer value | Display name |
|---|---|
| `connector` | Connector |
| `cultivator` | Cultivator |
| `opportunitySeeker` | Opportunity Seeker |
| `communityBuilder` | Community Builder |
| `low` | Low |
| `mid` | Mid |
| `high` | High |

After a result is shown, a Retake control clears all 15 answers and clears the displayed result. After Retake, the screen looks exactly like a fresh page load: nothing selected, no result shown. The two buttons are labeled exactly "Submit" and "Retake".

Tests for this item live in `tests/test_quiz_screen.py`, written before the build step, following the project routine (`docs/course/routine.md`, step 3). Writing those tests is not part of the build step.

## What it does NOT do

- No written or AI-generated result text — only the display names for the winning style and tier are shown.
- No retrieval or RAG.
- No saving or logging of answers anywhere (file, database, or otherwise).
- No deployment — this item is local-only; going live is a separate backlog item.
- No changes to the existing quiz at tools.werkitgirls.com.
- No changes to `src/scoring.py` — the scorer's values are only relabeled for display, never changed before being sent to it.
- No changes to the content or wording of `docs/quiz-questions.md`.
- No handling for more or fewer than 15 questions, or any answer choices beyond the four listed labels.
- No error messages for invalid scorer input — the screen's whole job is to make an invalid submission impossible.
- No persistence across a browser refresh — a refresh clears all answers, the same as Retake.
- The build step changes no file other than `app.py`.

## Acceptance criteria

- [ ] It's done when the page loads with all 15 questions visible, each showing exactly the four choices, in the order Never, Occasionally, Frequently, Always, and none of the four is pre-selected for any question.
- [ ] It's done when the 15 question texts and the 4 choice labels shown on the page are word for word the ones in `docs/quiz-questions.md`.
- [ ] It's done when the Submit control is disabled while at least one question has no choice selected.
- [ ] It's done when the Submit control becomes enabled only once all 15 questions have a choice selected.
- [ ] It's done when selecting an answer for one question leaves every other question's already-selected answer unchanged.
- [ ] It's done when clicking Submit, after all 15 are answered, calls `score_assessment` with a list of exactly 15 integers, each 1 to 4, where position 1 is the answer to question 1 of `docs/quiz-questions.md`, and so on through position 15, using Never=1, Occasionally=2, Frequently=3, Always=4.
- [ ] It's done when, after Submit, the screen displays the winning style and its tier using the display names table above (for example "Community Builder" and "Mid", never "communityBuilder" and "mid"), and displays no other generated or written text as "the result."
- [ ] It's done when, for each of the 10 fixtures in `tests/fixtures/known_answers.json`, entering that fixture's answers and clicking Submit shows the display names of the winner and tier that fixture lists.
- [ ] It's done when clicking Retake after a result is shown clears all 15 selections and the displayed result, leaving the page identical to a fresh load.

## Question round

| # | Question | Answer |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## Amendments

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

- `docs/quiz-questions.md` is now present on this branch (confirmed 2026-10-24).
- Enabling `streamlit` in `requirements.txt` was done as a separate setup commit (confirmed 2026-10-24), so tests can import it before the build step starts. The build step touches only `app.py`.
