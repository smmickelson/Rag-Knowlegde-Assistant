<!-- Course: first required in Stage 1, graded again in Stage 2. Revised whenever
     you learn a rule the hard way. See docs/course/DELIVERABLES.md -->

# AGENTS.md

Rules for any AI assistant working in this repository. Read this file before
doing anything else. If a request conflicts with a rule below, stop and say so
rather than guessing.

---

## 1. What this project is

**Purpose:** A RAG-powered networking self-assessment tool for Werk It Girls.
Users answer 15 questions and receive a personalized written result — generated
via retrieval-augmented generation against a brand-approved content library,
rather than a fixed pre-written paragraph — identifying which of four networking
styles (Connector, Cultivator, Opportunity Seeker, Community Builder) best fits
them and what to do next.

**Who uses it:** Women early-to-mid career, often mid-transition (job search,
return-to-work, industry pivot), arriving from Instagram to tools.werkitgirls.com
for a free, no-signup read on their networking style.

**What kind of app:** python-tool (Streamlit backend). See docs/course/tracks.md.
Note: the existing static quiz UI at tools.werkitgirls.com is a separate,
already-deployed asset outside this repo — this repo covers the new server-side
RAG backend only.

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

- Never use the words "actually" or "just" in any user-facing generated text.
  This is a Werk It Girls brand voice rule — checked in tests, not just prompts.
- All generated results must empower, never shame. If a test run produces
  language that reads as critical or judgmental, that's a failing result even
  if it's factually accurate.
- Never capture or store user quiz answers, email, or any personal data. The
  tool is intentionally ungated — this is a brand promise, not just a technical
  default.
- The overall score is the sum of all 15 raw answers directly — never sum
  cluster subtotals first, or the total can exceed the 60-point max.
- The "Owning It" (top-tier) threshold is 10 out of 12 per cluster and 50/60
  overall — not 9/12. Do not loosen this without being asked.
- Cluster mapping (which questions belong to which style) must stay hidden
  from the user during the quiz itself, to avoid skewing answers.
- **Communication style:** plain language first, in anything a non-technical
  reader might see — proposal.md, specs, PR descriptions, test explanations,
  or any user-facing text the app generates. Reach for a technical term only
  when it's load-bearing (something the reader will need to recognize again
  outside this document), and pair it with its plain-language meaning every
  time rather than leaving it to stand alone. This isn't a style preference —
  unexplained AI jargon is a real barrier that keeps non-technical people,
  especially women new to this space, out of rooms where they belong.
  Section 1's Purpose above is the one place the RAG mechanism gets named
  directly, since that reader is a technical grader — even there, the term is
  paired with what it means, which is the model to follow everywhere else.

  | Term | Load-bearing? | How to write it |
  |---|---|---|
  | API | Yes — appears constantly across tools and job postings | "the app calls out to an AI service" — introduce the word once, paired with the plain version |
  | RAG | Only in Section 1, for a technical reader | Elsewhere: "the app looks up material I've already written before it answers," not the acronym |
  | JSON | No — pure plumbing, rarely needs to be said aloud | "the format data gets passed around in" — usually omit the term entirely |
  | Python | Yes — the tool name itself, low-stakes to say | Fine to name once; doesn't need re-explaining every time |
  | Vector store / embeddings | No, outside Section 1 | "a searchable version of my own notes and content" |
  - Write tests before writing the implementation for any new feature.
  A red test that fails for the right reason comes before any code
  meant to make it pass — this is how test coverage stays honest
  rather than written after the fact to match whatever the code
  already does.
- Never change an existing test's expected behavior to make it pass.
  If a test looks wrong, stop and ask before touching it — a test
  that silently gets loosened to fit broken code defeats the
  point of having it.
- Before building a new feature, restate the plan and the tests
  you intend to write, then wait for explicit approval before
  writing any implementation code. This is the checkpoint where
  Sharon catches a misunderstanding before it becomes fifty lines
  of code to unwind.

---

## 5. Conventions

- **Source code:** `src/`
- **Tests:** `tests/`, one file per feature, named for the spec it tests
- **Feature specs:** `specs/NN-name.md`, numbered to match `docs/backlog.md`
- **Data files:** `data/`
- **Branches:** `feature/NN-short-name`
- **Commits:** present tense, one line, says what changed and why
- **Language / framework:** Python, Streamlit
- **Run the app:** `streamlit run app.py`
- **Run the tests:** `pytest`
