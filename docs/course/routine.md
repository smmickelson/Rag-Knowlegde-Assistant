# The routine

Every feature goes through the same eight steps. You'll run this 8-15 times.

The grade is not "does the app work." The grade is evidence that you ran the
routine, and that evidence accumulates on GitHub by itself as you work. There is
nothing to write up at the end.

```
 1. spec          take the next backlog item, expand it to one page
 2. questions     a second AI attacks the spec; you answer; answers go in the spec
 3. tests         a third AI writes the tests; they all fail, and that's correct
 4. ══ PAUSE ══   it explains each test in plain English. You read. You approve.
 5. build         a fourth AI writes code until the tests pass
 6. review        reviewers inspect, one concern each, ranked findings
 7. reply         the builder answers every comment
 8. merge         combine into main; the whole suite runs once more
```

Use a different chat or model for each role where you can. A model that wrote
something is a bad judge of it; it will defend its own work, and it will
overlook exactly what it overlooked the first time.

---

## 1. Feature spec

Copy [`specs/TEMPLATE.md`](../../specs/TEMPLATE.md) to `specs/NN-name.md`, where
`NN` is the backlog number. Have an AI expand the one-line story into a page:
what it does, what it does **not** do, and what done means.

The "does not do" section is the one people skip and the one that saves you.
Without it an assistant will cheerfully build three features you didn't ask for.

## 2. Question round

Bring in a **different** AI. Its only job is to find what your spec forgot:

> Read this feature spec. Do not write code and do not implement anything. Ask me
> at most 10 questions about what it fails to specify: edge cases, empty inputs,
> errors, things done twice, things done in the wrong order, hostile input. Most
> important first.

Answer each one in a single line. **Every answer goes into the spec**, including
the ones that change nothing. That's the point: a question answered in the spec
never gets asked again, by you or by any AI that shows up next week with no
memory of this conversation.

## 3. Tests before building

A different AI writes tests in `tests/`, one for each line of your acceptance criteria. Run them.

**Every one should fail.** The feature doesn't exist yet. A test that passes
right now proves nothing, and you've just learned that before it could cost
you anything.

## 4. The pause

**This is the graded step, and the only place the whole process stops.**

The AI must now describe each test to you in plain sentences: what it tries and
why it matters. No code in the descriptions. If you find yourself reading code,
ask again.

Read each description against your feature spec:

- Does this test something the spec actually asks for?
- Would this catch a real mistake, or would it pass no matter what?
- Is anything in the acceptance criteria missing a test?

Only when you understand them and agree do you write `approved`. Until then,
nobody builds anything.

Post the descriptions and your `approved` on the pull request. That's what makes
the pause visible to a grader, and it's the difference between knowing what your
software does and hoping.

## 5. Build

A different AI writes code until every test passes.

**It may not touch the tests.** If it thinks a test is wrong, it says so on the
pull request and waits for you. An assistant that quietly edits a test so its
code passes has broken the one rule that makes any of this mean anything.

## 6. Review

One or more AIs inspect the finished work. **Each gets exactly one concern**, and
each leaves at most 5 comments, ranked most important first:

| Reviewer | Looks for |
|---|---|
| Security | Anything an unkind user could exploit. Leaked keys. Unchecked input. |
| Spec match | Does the code do what the spec says, no more, no less? |
| Test quality | Would these tests actually catch a break? What isn't covered? |

One concern each is deliberate. A reviewer asked to look for everything finds
nothing in particular.

## 7. Reply

The builder answers **every** comment, under the comment itself:

- "Fixed. Here's the test that proves it."
- "I disagree, because ___."

When builder and reviewer disagree, **you decide.** You own what the app should
do. Neither of them does.

## 8. Merge

When a review round ends with no must-fix findings, merge. The full suite runs
once more.

Then: update `docs/backlog.md` status, add a line to `CHANGELOG.md`, and take the
next item.

### The suite also runs on GitHub

`.github/workflows/tests.yml` runs your tests on a clean machine every time a
pull request is opened or pushed to. You never have to start it.

It stays quiet while a pull request is a **draft**, which is where the red phase
belongs. Mark it ready for review once the tests pass, and that's when GitHub
runs them.

Its job is to catch the one thing you can't catch yourself: your project working
on your laptop only because you installed something in September and forgot to
write it down. That's the most common reason a classmate can't run your project
in Stage 3.

**If it goes red,** read the log. Either a test genuinely failed, or a dependency
is missing from `requirements.txt`. Both are worth fixing now rather than in
week 11. It is free on public repositories.

---

## What a grader looks for

For each feature, on the pull request:

- [ ] A spec, with the question round answered in it
- [ ] The pause in plain sight: descriptions plus your `approved`
- [ ] Review comments that are specific and ranked
- [ ] A builder reply under every single comment
- [ ] Small enough to read in one sitting

That last one matters more than it looks. A pull request with thirty files can't
be reviewed by anyone, human or AI. If it's growing that big, the feature was too
big. Split it and run the routine on each half.
