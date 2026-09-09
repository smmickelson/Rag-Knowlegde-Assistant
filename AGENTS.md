<!-- Course: first required in Stage 1, graded again in Stage 2. Revised whenever
     you learn a rule the hard way. See docs/course/DELIVERABLES.md -->

# AGENTS.md

Rules for any AI assistant working in this repository. Read this file before
doing anything else. If a request conflicts with a rule below, stop and say so
rather than guessing.

---

## 1. What this project is

<!-- Fill this in. Two or three sentences. An assistant that knows what the app
     is for makes better guesses about everything you forgot to specify. -->

**Purpose:**

**Who uses it:**

**What kind of app:** (static-web, server-side web app, python-tool, other, see docs/course/tracks.md)

---

## 2. Rules that do not change

These are course requirements. Do not edit this section.

1. **Tests before code.** Write the automatic tests for a feature before
   writing any code that implements it. At that point every new test must fail.
   A test that passes before the feature exists proves nothing.

2. **Never modify an existing test to make it pass.** If you believe a test is
   wrong, say so out loud in the pull request and wait. Quietly editing a test
   so your code passes is the single most serious failure possible here.

3. **Stop and explain, then wait.** After writing the tests and before writing
   any implementation, describe each test to the human in plain English: what
   it tries, and why it matters. Use no code in these descriptions. Then stop.
   Do not write implementation code until the human replies `approved`.

4. **One feature at a time.** A pull request should cover one item from
   `docs/backlog.md` and be readable in one sitting. If a change is growing past
   that, stop and propose splitting it.

5. **Never write a secret into a file.** No API keys, tokens, or passwords in
   source, tests, config, or commit messages; not even fake-looking ones, not
   even temporarily. Secrets go in `.env`, which is git-ignored. If you need a
   key that doesn't exist yet, stop and ask.

6. **A static site cannot keep a secret.** If this project deploys as static
   files, there is no server, so any key in the page is public to every visitor.
   Never add one. Use a keyless API, or have the user supply their own key at
   runtime. See `docs/deploying.md`.

7. **Say when you are unsure.** "I don't know" and "this could go two ways" are
   correct answers. Confident invention is not.

---

## 3. How work happens here

The full routine is in [docs/course/routine.md](docs/course/routine.md). Short version:

```
backlog item  →  feature spec  →  question round  →  failing tests
              →  STOP: explain tests, wait for "approved"
              →  build until tests pass  →  review  →  reply to every comment  →  merge
```

Which role you are will be stated when you're asked to work. If it wasn't
stated, ask before starting. The roles have different rules.

| Role | Does | Must not |
|---|---|---|
| **Spec writer** | Expands a backlog item into `specs/NN-name.md` | Write code |
| **Questioner** | Finds what the spec forgot; max 10 questions, most important first | Answer its own questions, or write code |
| **Test writer** | Writes failing tests in `tests/`, then explains them in plain English and stops | Write implementation code |
| **Builder** | Writes code until tests pass | Touch any existing test |
| **Reviewer** | One concern only; max 5 comments, ranked most important first | Fix things itself |

---

## 4. Project rules

<!-- Yours. Add a rule every time an assistant does something you didn't want.
     A rule written here is a mistake that never happens twice. Examples of the
     shape. Delete these and write your own:

     - Keep all user-facing text in one place so it can be changed without
       hunting through the code.
     - Do not add a new dependency without asking. Prefer what's already here.
     - Every user-visible date shows as "Mar 3, 2026", never as a raw timestamp.
     - If the app can't reach the network, show a message and keep working
       offline. Never show a blank screen.
-->

-
-
-

---

## 5. Conventions

<!-- How this repo is laid out and named. Fill in as you go. -->

- **Source code:** `src/`
- **Tests:** `tests/`, one file per feature, named for the spec it tests
- **Feature specs:** `specs/NN-name.md`, numbered to match `docs/backlog.md`
- **Data files:** `data/`
- **Branches:** `feature/NN-short-name`
- **Commits:** present tense, one line, says what changed and why
- **Language / framework:**
- **Run the app:**
- **Run the tests:**
