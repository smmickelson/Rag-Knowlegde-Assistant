# Alpha Testing Feedback Log

**Date:** 11/19/2026
**Testers:** 2 (Olivina, Aayush)
**Task list given:** see "Try it yourself" in README.md -- take the quiz, commit to
one action, retake with different answers

## Tester 1: Olivina

Completed the quiz quickly and easily, and committed to an action option without
difficulty.

1. **Comment:** Had to scroll back up to find the Retake button after finishing;
   suggested it might be easier if Retake also appeared at the bottom of the
   results screen.
   **Decision:** Yes, fix it. **Reason:** Both testers struggled to locate the
   Retake button after finishing the quiz, so we're adding a Retake action near
   the bottom of the results screen too.

2. **Comment:** Wants her archetype/style name more bolded and prominent on the
   results screen.
   **Decision:** Yes, fix it. **Reason:** Both testers wanted their networking
   style name to stand out more, so we're increasing its visual prominence.

3. **Comment:** Scrolled quickly past the superpower/growth-opportunity boxes
   without reading them closely, then said directly that this text is too much
   to read -- wants it shorter or removed.
   **Decision:** Yes, fix it. **Reason:** Both testers found the
   superpower/growth-opportunity text too long to read closely, so we're
   shortening it to be more scannable.

## Tester 2: Aayush

Completed the quiz easily, read through the superpower/growth-opportunity text
and all three action options carefully before committing.

4. **Comment:** Had real trouble locating the Retake button -- called it "tricky."
   **Decision:** Yes, fix it. Same decision and reason as Olivina's comment #1
   above -- both testers hit the same problem.

5. **Comment:** Disliked the superpower/growth-opportunity boxes -- too much to
   read.
   **Decision:** Yes, fix it. Same decision and reason as Olivina's comment #3
   above.

6. **Comment:** Liked having an archetype name shown, but it's too small; wanted
   it more prominent.
   **Decision:** Yes, fix it. Same decision and reason as Olivina's comment #2
   above.

7. **Comment:** Wanted to see the other three archetypes, not just the winner --
   suggested the main archetype be shown prominently, set against the other
   three. Also wanted to see his second-closest archetype/style, not just the
   winner.
   **Decision:** No, we are keeping the current behavior. **Reason:** We
   considered this; we are keeping the single-result design for now because,
   even though the scoring already computes all four archetype totals
   internally, showing a ranked comparison raises real design questions (how to
   break a tie for second place, how to display it without reintroducing the
   clutter the other two testers asked us to cut) -- worth its own spec in a
   future stage rather than a quick alpha-stage fix.
