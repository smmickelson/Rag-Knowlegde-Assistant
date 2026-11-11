# 4g - Result screen polish

**Story:** As a user, my result screen shows a numeric score and tagline instead of a tier
label, shows my networking philosophy before I start instead of after, shows identity/strengths
side by side, and never pre-selects a next step for me.

**Backlog item:** #4g

**Status:** draft

## What it does

Removes the tier label from the result screen display (tier stays computed internally and is
still used by `retrieve_for_score` to pick building-vs-using behavior content). Shows the
existing `score_assessment` `overall` field as a raw score out of 60 in its place. Moves the
`philosophy_blend` text to the intro screen, shown once before the quiz starts. Shows the
winning style's identity and strengths side by side in two columns. Adds a one-line tagline
under the style name, from a fixed lookup (not retrieved/ranked content). Removes the default
pre-selected option from the behavior-choice radio.

## What it does NOT do

- Change `retrieve_for_score`, `build_store`, or any retrieval/ranking logic.
- Change what `score_assessment` computes.
- Add new content-library content beyond the four fixed taglines.
- Change #13/#14 or #6.

## Acceptance criteria

- [ ] It's done when the tier label is gone from the result screen (tier itself still computed
      and used internally).
- [ ] It's done when the raw overall score (X / 60) shows in its place.
- [ ] It's done when the `philosophy_blend` text shows on the intro screen before the quiz
      starts.
- [ ] It's done when identity and strengths show in a two-column layout.
- [ ] It's done when each style's tagline shows under its name.
- [ ] It's done when the behavior-choice radio has no option pre-selected.
- [ ] It's done when each behavior suggestion is shown exactly once — as the radio option's full text — not also printed separately above the radio.

## Question round

Skipped — this is a UI/display polish pass based on direct creator testing feedback on the
already-shipped #4e feature, not new retrieval logic.

## Amendments

| Date | Change | Why |
|---|---|---|
| 11/11/2026 | Removed duplicate display of behavior-suggestion text | The result screen was showing all 3 behavior chunks as a paragraph block, then showing the same 3 texts again as the radio choice's option labels. This duplication originated in #4e and was deliberately deferred at the time; found again during #4g's manual UI walkthrough (standing in for formal review) and fixed here, matching the single-list "pick one and start" design from the creator's own original mockup. |

## Notes
