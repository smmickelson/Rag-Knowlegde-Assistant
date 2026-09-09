<!-- Course: Stage 4. Section weights below match the grading rubric. Spend your
     effort accordingly. Section 3 is worth more than the rest combined.
     See docs/course/DELIVERABLES.md -->

# Final report

**Project:**
**Author:**
**Date:**

---

## 1. What this project is *(overview)*

<!-- A page. What it does, who it's for, what state it's in. Assume the reader
     has not seen your proposal. -->

## 2. Status against the original acceptance criteria *(25%)*

<!-- Go through docs/backlog.md item by item. Be honest. An unmet condition
     with a clear account of what you tried is worth far more than a vague claim
     that everything works. -->

| # | Feature | Original acceptance criteria | Met? | If not: what I tried, and what stopped me |
|---|---|---|---|---|
| 1 |  |  | yes / partly / no |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |

**Cut on purpose:** <!-- Features you dropped, and the reasoning. Cutting scope
deliberately is a legitimate engineering decision. Say so. -->

## 3. User feedback, and what it changed *(40%, the largest single section)*

<!-- Pull from docs/feedback-log.md. Don't just summarize what people said.
     show the chain: comment → decision → revised acceptance criteria → new or changed
     test → code. That chain is what's being graded. -->

### What the testers found

### What I changed, and what it cost

| Comment | Decision | Acceptance criteria added or revised | Test added or changed |
|---|---|---|---|
|  |  |  |  |
|  |  |  |  |

### What I decided not to change, and why

### Alpha → final: everything that changed

<!-- CHANGELOG.md should already have most of this. Summarize it here and link. -->

## 4. How this got built, and how AI was used *(part of the process grade)*

<!-- Pull from docs/dev-log.md. Specifics beat generalities:
     - Where did the routine catch something you would have missed?
     - Where did an assistant confidently do the wrong thing?
     - What did the question round find that you hadn't thought of?
     - Did the stop-and-read pause ever change your mind about a test? -->

## 5. Reflection *(15%)*

<!-- The honest section. What would have made you more effective? -->

**What I got better at:**

**Where my lack of technical knowledge cost me time:**
<!-- Be specific. "I didn't understand what an error message meant, so I pasted
     it back four times instead of reading it" is a real answer. -->

**What I'd learn first if I kept going:**

**What I now think about building software this way:**
<!-- Not the answer you think is wanted. What you actually concluded. -->

---

## Appendix: demo notes

<!-- The live demo includes a sabotage round: something in your running app gets
     broken, and you predict which tests will fail and how, before running them.

     You cannot prepare for the specific sabotage. You can prepare by knowing
     what each of your tests actually covers. This table is that preparation. -->

| If this broke... | These tests would fail | And the message would say roughly |
|---|---|---|
|  |  |  |
|  |  |  |
|  |  |  |

**Tests that cover nothing** <!-- Parts of the app where a break would go
undetected. Knowing your own blind spots is worth more in the demo than
pretending you have none. -->
