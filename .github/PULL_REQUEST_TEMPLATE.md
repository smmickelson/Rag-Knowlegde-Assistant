<!-- This fills itself in when you open a pull request. Delete the lines that
     don't apply, but don't delete the Pause section; that's the graded one.
     The full routine: docs/course/routine.md -->

## What this builds

**Backlog item:** #
**Spec:** `specs/NN-____.md`

<!-- One or two sentences in plain language. What can a user do after this that
     they couldn't before? -->

---

## 1. Question round

- [ ] A second AI reviewed the spec and asked its questions
- [ ] Every answer is recorded **in the spec**, including the ones that changed nothing

<!-- How many questions, and the one that mattered most: -->

---

## 2. Tests were written first, and they failed

- [ ] Tests were written before any implementation code
- [ ] All of them failed when first run

<!-- Paste the failing run, or say how many failed and why that was correct: -->

```
```

---

## 3. The pause

**The AI's plain-English description of each test, and my approval.**

<!-- Paste the descriptions here: what each test tries and why it matters.
     No code. Then read them against your spec and answer the questions below
     before writing "approved". This section is graded directly. -->

| Test | What it tries | Why it matters |
|---|---|---|
|  |  |  |
|  |  |  |

Before approving:

- [ ] Every test traces back to a line in the spec's acceptance criteria
- [ ] Every acceptance criteria line has a test
- [ ] I can say what would break if each test were deleted

**My approval:** <!-- write `approved` here, and not before you mean it -->

---

## 4. Build

- [ ] Every test passes
- [ ] **No existing test was modified**

<!-- If you believe a test is wrong, say so here instead of changing it: -->

---

## 5. Review

Each reviewer gets one concern and at most 5 comments, ranked.

- [ ] Security: leaked keys, unchecked input, anything an unkind user could do
- [ ] Spec match: does this do what the spec says, no more and no less?
- [ ] Test quality: would these actually catch a break? What isn't covered?

- [ ] **Every review comment has a builder reply underneath it**

---

## Before merging

- [ ] Full suite passes
- [ ] `docs/backlog.md` status updated
- [ ] `CHANGELOG.md` has a line for this
- [ ] This diff can be read in one sitting
