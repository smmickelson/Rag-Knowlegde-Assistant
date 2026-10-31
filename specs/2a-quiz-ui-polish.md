# 2a - Quiz screen structural polish

**Story:** As a user taking the quiz, I always know how far along I am and what my result means, so the alpha doesn't look unfinished or abandoned.
**Backlog item:** #2a
**Status:** tests written

## What it does

The page gets a real browser tab title and an on-page header with a one-line
subtitle, shown above question 1 before anything is answered:

- **Title:** "What Kind of Networker Are You?"
- **Subtitle:** "Connector, Cultivator, Opportunity Seeker, or Community Builder — 15 quick questions, instant answer."

A progress indicator is shown above question 1, below the subtitle, throughout
the quiz. It shows both a text count (for example, "6 of 15 answered") and a
visual progress bar using Streamlit's built-in progress bar widget, and both
update immediately as each question is answered. It does not stay pinned to
the screen while scrolling. Once a result is shown, the subtitle and progress
indicator are hidden; the header title remains visible.

After Submit, the result screen shows the style and tier with explicit labels
— for example "Your networking style: Community Builder" and "Your tier:
Mid" — instead of the two bare words `app.py` currently displays. Below those
labels, a fixed line of text reads: "More personalized coaching based on your
specific answers is coming soon." This same wording shows for every result —
it is not personalized and does not change based on the user's style or tier.

## What it does NOT do

- No color, font, or logo branding (the navy/orange/taupe Werk It Girls visual
  identity used on tools.werkitgirls.com). That's deliberately out of scope
  for this item.
- No AI-generated or written coaching text on the result screen. That's
  backlog items #4b and #4d — this item only labels what `score_assessment`
  already returns, plus one fixed "coming soon" line that never changes
  between users or results.
- No changes to `src/scoring.py`, the question text or order in
  `docs/quiz-questions.md`, or the four answer choices.
- No changes to Submit or Retake behavior as specified in
  `specs/18a-quiz-screen.md` — Retake still clears everything, including
  resetting the progress indicator to "0 of 15 answered."
- No changes to the existing quiz at tools.werkitgirls.com.
- No accessibility work beyond Streamlit's own defaults.
- No sticky or pinned positioning for the progress indicator while scrolling — it's placed above the questions on page load and stays there, not fixed to the viewport.

## Acceptance criteria

- [ ] It's done when the browser tab shows "What Kind of Networker Are You?" on page load, not the Streamlit default. (Verified by hand, not by an automated test — Streamlit's AppTest testing framework has no way to inspect the browser tab title, confirmed 2026-10-31.)
- [ ] It's done when the header "What Kind of Networker Are You?" and the subtitle "Connector, Cultivator, Opportunity Seeker, or Community Builder — 15 quick questions, instant answer." appear above question 1 before any question is answered.
- [ ] It's done when a progress indicator showing the count of answered questions out of 15 is visible from page load (starting at 0 of 15) through submission.
- [ ] It's done when the progress indicator includes both the text count and a visual progress bar that fills proportionally as questions are answered.
- [ ] It's done when, once a result is shown, the subtitle and progress indicator are no longer visible, while the header title remains visible.
- [ ] It's done when answering or changing an answer to any single question updates the progress indicator's count immediately, without affecting any other question's answer.
- [ ] It's done when, after Submit, the result screen shows "Your networking style: [display name]" and "Your tier: [display name]" using the display-name table from `specs/18a-quiz-screen.md`, never the bare words alone.
- [ ] It's done when the result screen also shows the fixed line "More personalized coaching based on your specific answers is coming soon." below the style/tier labels, worded identically regardless of which style or tier the user got.
- [ ] It's done when clicking Retake after a result is shown returns the page to its fresh-load state: header and subtitle visible, progress indicator at 0 of 15, no result shown — matching `specs/18a-quiz-screen.md`'s Retake behavior.
- [ ] It's done when all existing tests in `tests/test_quiz_screen.py` still pass unchanged.

## Question round

| # | Question | Answer |
|---|---|---|
| 1 | Does "visible at all times" mean the progress indicator stays on screen while scrolling, or is placing it above the questions sufficient? | Placed above the questions on page load is sufficient; it does not need to stay pinned while scrolling. Pinning would require custom CSS, which this item avoids. |
| 2 | Should changing an already answered question keep the count unchanged, with each question contributing at most one to the total? | Yes — each of the 15 questions contributes at most 1 to the count; changing an answer updates which choice counts, not the total. |
| 3 | Should the header, subtitle, and progress indicator remain visible on the result screen, with progress showing "15 of 15 answered"? | The header stays visible; the subtitle and progress indicator are hidden once a result is shown — a static "15 of 15 answered" label isn't useful once the quiz is done. |
| 4 | Should progress use just the text "6 of 15 answered," or include a visual progress bar too? Where should it appear relative to the header and subtitle? | Both — the text and a visual progress bar, using Streamlit's built-in progress bar widget (native look, no custom styling). Appears directly below the subtitle, above question 1. |
| 5 | If Submit is attempted with unanswered questions, should the progress indicator remain visible alongside the existing validation message? | Not applicable — per spec 18a, Submit stays disabled until all 15 questions are answered, so there's no failed-submit case or validation message. |
| 6 | If score_assessment fails or returns a style/tier missing from the display-name table, what should show? | Out of scope, same as spec 18a — Submit only ever sends 15 valid integers (1-4), so score_assessment never raises or returns an unrecognized value in this architecture. |
| 7 | If the user refreshes or reconnects, should progress reflect retained answers or reset? | Same as spec 18a — a refresh clears everything, so progress resets to 0 of 15. |
| 8 | Does "one-line subtitle" allow natural wrapping on narrow screens? | Yes — "one-line" describes the subtitle's content (a single sentence), not a requirement that it render as one visual line on every screen. |

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Title/subtitle wording decided with Claude (coach role) on 2026-10-30, choosing the "which archetype are you" framing over a plainer "Networking Self-Assessment" title, specifically so the four archetype names are visible and memorable before someone finishes the quiz — not a Werk It Girls branding decision, just copy.
- Inserted as #2a (between shipped #2 and not-started #3) rather than appended, per the instructor's advice to address UI before deeper build work — the quiz-flow screen won't need rework later once #4b/#4d's written results are wired in.