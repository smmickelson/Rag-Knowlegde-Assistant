# What's due, and where to find the files

---

## Stage 1 - Specifications and Design. Due 10/2

*10% of semester grade*

| File | Must contain |
|---|---|
| [`docs/proposal.md`](../proposal.md) | Problem statement, intended users, tools and services each with a one-sentence justification, development timeline mapping features to weeks |
| [`docs/backlog.md`](../backlog.md) | Prioritized user stories, one sentence each, each with testable acceptance criteria, numbered in planned build order |
| [`AGENTS.md`](../../AGENTS.md) | The standing rules your AI assistant must follow, sections 1 and 4 filled in |
| [`README.md`](../../README.md) | First draft of the setup instructions - steps and accounts a stranger needs |

**Graded on:** problem definition (25%); user stories and how testable their
acceptance criteria are (25%); technology choices and their justification (25%);
timeline and build order (25%)

> The most common way to lose points here is acceptance criteria nobody else could
> test. "It's done when it feels fast" fails. "It's done when the reply appears
> within 3 seconds" passes.

---

## Stage 2 - Prototype with Tests. Due 10/30

*10% of semester grade*

At least two core features, each built through the full routine.

| Where | Must show |
|---|---|
| [`specs/`](../../specs/) | A one-page spec per feature, with the question round answered **in the spec** |
| `tests/` | Tests written before implementation, covering the acceptance criteria |
| **Pull requests** | The plain-English test descriptions, your `approved`, ranked review findings, and a builder reply under every comment |
| [`AGENTS.md`](../../AGENTS.md) | Current and being followed |
| [`docs/dev-log.md`](../dev-log.md) | How AI tools were used |

**Graded on:** functionality (25%); test coverage of acceptance criteria (25%);
process evidence visible on the pull requests (25%); your ability to explain how
each feature works conceptually, without reading the code (25%)

> There is nothing extra to write up for this stage. If you ran the routine, the
> evidence is already on GitHub. If you didn't, it can't be added afterward.

---

## Stage 3 - Alpha Release with User Feedback. Due 11/20

*10% of semester grade*

A working alpha a peer can set up and run **without asking you anything**.

| File | Must contain |
|---|---|
| [`README.md`](../../README.md) | Setup instructions, now tested on a real classmate |
| [`docs/feedback-log.md`](../feedback-log.md) | Every comment from at least three testers, each with one of three decisions and a reason |
| [`docs/backlog.md`](../backlog.md) | Updated with everything you decided to do later |
| [`specs/`](../../specs/) | Amendments recording everything you decided to do now |
| [`CHANGELOG.md`](../../CHANGELOG.md) | An 0.1.0 alpha entry |

**Graded on:** completeness and usability of the alpha (25%); setup
documentation and whether it's testable (25%); quality of feedback collection
(25%); thoughtfulness of your decisions, **with every comment resolved in
writing** (25%)

> "No, we're keeping the current behavior because ___" is a full-credit answer.
> A comment with no decision next to it is not.

---

## Stage 4 - Final Demo and Report. Due 12/16

*10% of semester grade*

| File | Must contain |
|---|---|
| [`docs/final-report.md`](../final-report.md) | Overview, process and AI use, how feedback changed the app, alpha→final changes, reflection |
| [`CHANGELOG.md`](../../CHANGELOG.md) | Complete through the final version |
| [`docs/backlog.md`](../backlog.md) | Final status of every item, including what didn't get built |

Plus a **live demo**, which includes a sabotage round: the instructor breaks
something in your running app and you predict which tests will fail, and how,
before running them.

**Graded on:** status against your original acceptance criteria, with an account of
anything unmet (25%); **incorporation of user feedback, including revised
acceptance criteria and updated tests (40%)**; reflection (15%); the demo and
sabotage prediction (20%)

> The 40% is the largest single block in the course. It is not "did users like
> it" - it is whether you can show the chain from a comment, to a decision, to
> revised acceptance criteria, to a changed test, to code.

---

## Everything, in one table

| File | 1 | 2 | 3 | 4 |
|---|:-:|:-:|:-:|:-:|
| `README.md` | draft | | **rewritten** | |
| `AGENTS.md` | **new** | graded | | |
| `docs/proposal.md` | **new** | | | referenced |
| `docs/backlog.md` | **new** | | revised | final status |
| `specs/*.md` | | **new** | amended | |
| `tests/*` | | **new** | added to | updated |
| `docs/dev-log.md` | | **new** | | source |
| `docs/feedback-log.md` | | | **new** | source |
| `CHANGELOG.md` | | | **new** | completed |
| `docs/final-report.md` | | | | **new** |
| Pull requests | | **evidence** | evidence | evidence |
