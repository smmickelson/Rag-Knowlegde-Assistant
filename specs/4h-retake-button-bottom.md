# 4h - Move retake button to bottom

**Story:** As a user who just finished the quiz, I want the retake action to live where I'm
already looking when I'm done reviewing my results, so I don't have to scroll back to the
top of a long page to try again.

**Backlog item:** #4h

**Status:** draft

## What it does

Moves the single "Retake" button from the top of the page (just under the title) to the
very bottom of the page, right after whatever currently renders last in the results
section -- the action-plan status line on a successful result, or the retrieval-error
message if personalized content failed to load. There is exactly one Retake button, and
it behaves exactly as it does today: clears all 15 quiz answers, the result, the
retrieved content, the retrieval-failed flag, and the behavior choice, then returns to a
fresh, empty quiz.

## What it does NOT do

- Does not add a second Retake button -- the top one is removed, not duplicated.
- Does not change what Retake clears, or how it clears it -- same state, same behavior,
  just a different location on the page.
- Does not change whether the 15 answered (disabled) quiz questions remain visible after
  submission -- that stays exactly as it is today. A user will still scroll past those to
  reach the results and the new Retake button underneath them.
- Does not change the quiz-taking screen in any way.
- Does not pin the button to the viewport (no fixed/sticky positioning) -- it's a position
  in the page's normal element order, not a visual overlay.

## Acceptance criteria

- [ ] It's done when a button labeled exactly "Retake" exists whenever a result is present.
- [ ] It's done when that Retake button is the last element in the page's rendered order --
      specifically, immediately after the action-plan status line.
- [ ] It's done when no Retake button exists at the top of the page (just under the title).
- [ ] It's done when exactly one Retake button exists on the page at any time -- never zero
      (once a result exists), never two.
- [ ] It's done when no Retake button of any kind appears before a result exists (during
      active quiz-taking).
- [ ] It's done when clicking the Retake button clears all 15 answers, the result, the
      retrieved content, the retrieval-failed flag, and the behavior choice, and makes the
      15 quiz questions editable again -- identical to the current button's behavior.

## Question round

Q: What does "bottom of the page" mean precisely?
A: The last element on the page, immediately following the action-plan status line. A
position in rendered element order (testable via AppTest), not a fixed/sticky viewport
position.

Q: Can each acceptance criterion fail independently?
A: Yes -- split into: button exists, button is last in render order, no button at top,
exactly one button total, no button before a result exists, and click behavior clears the
correct state. Spacing/visual styling is out of scope for these tests (known AppTest
limitation, same as elsewhere in this project).

Q: What happens before a result exists?
A: No Retake button appears anywhere on the page during active quiz-taking, same as today.

Q: How does this interact with the disabled quiz questions?
A: They remain visible, disabled, and showing prior answers until Retake is clicked, exactly
as today. Clicking Retake clears those answers and makes the quiz editable again -- this
spec only relocates that existing behavior, it doesn't change it.

## Notes

Found during alpha testing (11/19/2026) -- both testers (Olivina, Aayush) struggled to
locate the single top-of-page Retake button after finishing the quiz; moving it to the
bottom addresses this more directly than adding a second button would. See
docs/feedback-log.md comments #1 and #4.
