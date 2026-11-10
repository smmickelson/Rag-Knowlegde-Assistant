# 4e - Wire #4a's retrieval into the quiz app

**Story:** As a user, my result screen shows real, personalized content from the content
library — my networking philosophy, my style's identity and strengths, and three next steps
to choose from — instead of a placeholder line.

**Backlog item:** #4e

**Status:** draft

## What it does

Vendors the 40 content-library markdown files (currently only in the separate
`werkitgirls-resources` repo) into this repo, so this project is self-contained. The first
time the app needs the content-library vector store and it doesn't exist yet, it's built
automatically from those vendored files (reusing item #2b's `build_store`), so no manual setup
step is required.

After scoring, the app calls item #4a's `retrieve_for_score` with the score result and replaces
the "more coaching coming soon" line with:

- The `philosophy_blend` chunk's text, shown once, the same for everyone.
- The winning style's `identity` and `strengths` chunks' text.
- The 3 ranked behavior chunks' text, presented as a choice (e.g. radio buttons) so the user
  can pick one to focus on.

All text is shown exactly as stored — nothing is reworded, trimmed, or generated.

## What it does NOT do

- Call TensorX or generate any new text. Every word shown comes verbatim from the content
  library. That's #4b, still to come.
- Change #4a's retrieval, ranking, or filtering logic in any way. This item only calls it and
  displays what it returns.
- Add the situational/open-ended question layer. That's #13/#14.
- Deploy anywhere public, or change how scoring logic is exposed. That's #6.
- Save, log, or transmit which next step the user picks. No answer or choice is ever stored,
  same as the existing quiz.
- Change `action_item_store.py` or the old `action_items` store in any way.

## Acceptance criteria

- [ ] It's done when the 40 content-library markdown files exist in this repo (not only in
      `werkitgirls-resources`), under a clearly named folder.
- [ ] It's done when running the app for the first time with no existing vector store builds
      one automatically from the vendored files, with no manual step and no error shown to
      the user.
- [ ] It's done when, after submitting the quiz, the result screen shows the
      `philosophy_blend` text, the winning style's `identity` and `strengths` text, and all 3
      ranked behavior chunks' text — each matching the stored chunk exactly.
- [ ] It's done when the 3 behavior chunks are presented as a choice the user can select
      between, and nothing breaks if the user changes their selection.
- [ ] It's done when Retake clears this new content along with the existing style/tier result,
      back to a blank quiz with no retrieved content showing.
- [ ] It's done when a retrieval or store-build failure is caught and shown as a clear,
      non-crashing message rather than an unhandled error page.
- [ ] It's done when `python3 -m pytest` passes with no failures, and all existing tests
      (items #1, #2, #2b, #3, #4a, #18a, #18b) still pass unchanged.

## Question round

<!-- Paste the questioner AI's questions here with your one-line answers. -->

| # | Question | Answer |
|---|---|---|
| 1 |  |  |

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Content library source files vendored from `werkitgirls-resources/knowledge_base` — same 40
  files, same naming, copied as-is.
- Reuses #2b's `build_store` and #4a's `retrieve_for_score` unchanged; this item is UI wiring
  and a build-on-demand step, not new retrieval logic.
- The "which next step did they pick" interaction is deliberately throwaway — no persistence,
  consistent with the existing app's "no answer is ever saved" rule.
