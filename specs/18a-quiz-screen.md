# 18a - Quiz screen

**Story:** As a user taking the quiz, I answer all 15 questions on a single screen and see my networking style result. I cannot submit until every question has an answer.
**Backlog item:** #18a
**Status:** approved

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

 After a result is shown, a Retake control clears all 15 answers and clears the displayed result. After Retake, the screen looks exactly like a fresh page load: nothing selected, no result shown. Retake is not shown until a result is displayed. Once Submit is clicked and a result is shown, all 15 question inputs and the Submit button become disabled; nothing can be changed or re-submitted until Retake is clicked. The two buttons are labeled exactly "Submit" and "Retake".

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
- No handling for `score_assessment` raising an exception or returning an unexpected result.
- No handling for `docs/quiz-questions.md` being missing or malformed.
- No handling for multiple browser tabs or session reconnects beyond Streamlit's own defaults.
- No accessibility requirements beyond Streamlit's defaults.

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
| 1 | Can users change answers after a result appears? | No. Once Submit is clicked and a result is shown, all 15 inputs and the Submit button are disabled. Nothing can change until Retake is clicked. |
| 2 | What if score_assessment raises or returns something unexpected? | Out of scope. Submit only ever sends 15 valid integers (1-4), so this isn't exercised by 18a. |
| 3 | What is score_assessment's return structure? | A dict with the four style totals (keyed connector/cultivator/opportunitySeeker/communityBuilder), plus `overall`, `winner`, and `tier`. `winner` and `tier` are looked up in the display-name table. |
| 4 | Double-click on Submit? | Can't happen - Submit disables itself immediately after a successful click (see answer 1). |
| 5 | Answer changes while a submission is "processing"? | Not applicable. Streamlit reruns the whole script per interaction; there's no separate processing window for an answer to change during. |
| 6 | docs/quiz-questions.md missing or malformed? | Out of scope. It's a repo file, not user input - if it's broken, the app can fail to start. |
| 7 | Independent tabs / reconnecting sessions? | Out of scope - relies on Streamlit's own default per-session behavior; 18a doesn't add anything on top. |
| 8 | Is Retake visible before submission? Focus/scroll after Retake? | Retake isn't shown until a result is displayed. No special focus/scroll handling - a fresh load has none, so Retake shouldn't either. |
| 9 | Forged/bypassed Submit sending invalid answers? | Not possible in this architecture - Streamlit enforces widget state server-side, there's no client-side form to forge. |
| 10 | Does "all 15 visible" mean one scrollable page? Accessibility requirements? | Yes, one scrollable page. No accessibility requirements beyond Streamlit's own defaults. |

## Amendments

| Date | Change | Why |
|---|---|---|
| 2026-10-25 | Added test_retake_clears_the_displayed_result after approval; fixed two Retake bugs found in manual browser testing (archetype text not clearing, then checkmarks not visually clearing) | Automated tests passed but the real app didn't match the spec's Retake behavior — found only by testing in an actual browser |
| 2026-10-31 | This item's acceptance criterion that the result screen "displays no other generated or written text as 'the result'" is superseded by backlog item #2a (specs/2a-quiz-ui-polish.md), which adds explicit "Your networking style:" / "Your tier:" labels and a fixed "coming soon" line below the bare display names. | #2a's own acceptance criteria now cover what the result screen shows; this note exists so nobody reads 18a's original criterion and thinks the extra text is a bug. |
|  |  |  |

## Notes

- `docs/quiz-questions.md` is now present on this branch (confirmed 2026-10-24).
- Enabling `streamlit` in `requirements.txt` was done as a separate setup commit (confirmed 2026-10-24), so tests can import it before the build step starts. The build step touches only `app.py`.
