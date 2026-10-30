# 2b - Quiz screen structural polish

**Story:** As a user taking the quiz, I always know how far along I am and what my result means, so the alpha doesn't look unfinished or abandoned.
**Backlog item:** #2b
**Status:** draft

## What it does

The page gets a real browser tab title and an on-page header with a one-line
subtitle, shown above question 1 before anything is answered:

- **Title:** "What Kind of Networker Are You?"
- **Subtitle:** "Connector, Cultivator, Opportunity Seeker, or Community Builder — 15 quick questions, instant answer."

A progress indicator is visible at all times during the quiz, showing how many
of the 15 questions are currently answered (for example, "6 of 15 answered"),
and it updates immediately as each question is answered.

After Submit, the result screen shows the style and tier with explicit labels
— for example "Your networking style: Community Builder" and "Your tier:
Mid" — instead of the two bare words `app.py` currently displays.

## What it does NOT do

- No color, font, or logo branding (the navy/orange/taupe Werk It Girls visual
  identity used on tools.werkitgirls.com). That's deliberately out of scope
  for this item.
- No AI-generated or written coaching text on the result screen. That's
  backlog items #4b and #4d — this item only labels what `score_assessment`
  already returns.
- No changes to `src/scoring.py`, the question text or order in
  `docs/quiz-questions.md`, or the four answer choices.
- No changes to Submit or Retake behavior as specified in
  `specs/18a-quiz-screen.md` — Retake still clears everything, including
  resetting the progress indicator to "0 of 15 answered."
- No changes to the existing quiz at tools.werkitgirls.com.
- No accessibility work beyond Streamlit's own defaults.

## Acceptance criteria

- [ ] It's done when the browser tab shows "What Kind of Networker Are You?" on page load, not the Streamlit default.
- [ ] It's done when the header "What Kind of Networker Are You?" and the subtitle "Connector, Cultivator, Opportunity Seeker, or Community Builder — 15 quick questions, instant answer." appear above question 1 before any question is answered.
- [ ] It's done when a progress indicator showing the count of answered questions out of 15 is visible from page load (starting at 0 of 15) through submission.
- [ ] It's done when answering or changing an answer to any single question updates the progress indicator's count immediately, without affecting any other question's answer.
- [ ] It's done when, after Submit, the result screen shows "Your networking style: [display name]" and "Your tier: [display name]" using the display-name table from `specs/18a-quiz-screen.md`, never the bare words alone.
- [ ] It's done when clicking Retake after a result is shown returns the page to its fresh-load state: header and subtitle visible, progress indicator at 0 of 15, no result shown — matching `specs/18a-quiz-screen.md`'s Retake behavior.
- [ ] It's done when all existing tests in `tests/test_quiz_screen.py` still pass unchanged.

## Question round

<!-- Paste the questioner AI's questions here with your one-line answers.
     Every answer goes in, including "no, keep current behavior."
     An answer recorded here never has to be argued again. -->

| # | Question | Answer |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Title/subtitle wording decided with Claude (coach role) on 2026-10-30, choosing the "which archetype are you" framing over a plainer "Networking Self-Assessment" title, specifically so the four archetype names are visible and memorable before someone finishes the quiz — not a Werk It Girls branding decision, just copy.
- Inserted as #2b (between shipped #2 and not-started #3) rather than appended, per the instructor's advice to address UI before deeper build work — the quiz-flow screen won't need rework later once #4b/#4d's written results are wired in.