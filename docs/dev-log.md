<!-- Course: Stage 2 (graded) and Stage 4 (feeds your final report). Several of
     the Friday lab milestones get recorded here. See docs/course/DELIVERABLES.md -->

# Development log

A running record of how this project got built and how AI was used to build it.

Add an entry when something notable happens: a feature ships, an assistant does
something surprising (well or badly), you get stuck, you change your approach.
Two or three sentences is plenty. Writing it as you go takes minutes; recon-
structing it in week 15 takes hours and the result is worse.

**Screenshots go in `assets/`** and get linked from the relevant entry.

---

## Pre-port debugging (werkitgirls-resources)
Before porting scoring logic to Python (item #1), found and fixed a bug in the live tool: a missing DOM reset in showResults() let action items pile up across retakes without a page reload, producing misleading results. Fixed and changelogged in werkitgirls-resources (separate repo) on 2026-09-27 — see that repo's CHANGELOG.md for the full fix. Confirms the reference scoring behavior used for item #1's test fixtures is the corrected version, not the buggy one.
## Template for an entry

### YYYY-MM-DD - Short title

**What happened:**
**AI tools used, and for what:**
**What surprised me:**

---

## Lab milestones

Check these off as you hit them, and link to the entry or screenshot.

- [x] **Task list + red tests**: first tests written and failing. See the 2026-10-12 entry.
- [ ] **First green**: a test flips from red to green on your own project
- [ ] **Sabotage**: you broke your own app on purpose and confirmed the tests caught it
- [ ] **Real API call**: your app talks to an outside service
- [ ] **Bug reports filed**: on a classmate's prototype
- [ ] **README v1**: a classmate ran your app from your setup steps
- [ ] **User-test notes**: recorded in [feedback-log.md](feedback-log.md)
- [ ] **Criteria v2 + review report**: acceptance criteria revised after real feedback

---

## Entries

<!-- Newest first. -->

### 2026-10-24 - Item 18b review rounds, fixes, and merge (ChatGPT, DeepSeek, Claude)

**What happened:** Three reviewers (ChatGPT, one concern each) reviewed the finished work and found one security gap, one spec gap, and five test weaknesses. I accepted all of them. Claude fixed the tests and DeepSeek fixed the code. Claude then found a related case (a class that defines its own name), so we added four tests, I approved them on the PR, and DeepSeek made a second fix. A second Security review found one more case, a class whose name is a custom string with its own formatting code. I accepted it as a known limit, because only code that builds such a class can trigger it and a web request cannot carry one. It is recorded in the spec's Amendments and in the PR. I did not re-run the Spec match review with ChatGPT. Claude compared the final diff to the spec line by line instead and found no mismatch. Final result: 107 tests pass locally and on GitHub.

**AI tools used, and for what:** ChatGPT reviewed. Claude (chat) wrote and strengthened the tests, ranked the findings, and found the extra case. DeepSeek V4 Flash in Kilo made both code fixes. Kilo's auto-approve was on during one session, so I checked each result with git before committing. I made the decisions and wrote the approvals.

**What surprised me:** Claude wanted to run another round to fix a name field that ultimately would not have affected the user experience. 

### 2026-10-14 - Item 1: AI roles

**What happened:** I ran item 1 end to end with three AI tools in separate roles. Agent 1 (builder) was DeepSeek V4 Flash 0731 in Kilo (VS Code). It wrote the stub, revised the tests, implemented `score_assessment`, replied to the review comments, and made the commits. I picked it for the most capability per dollar after the class costing walkthrough. Agent 2 (reviewer) was ChatGPT. It reviewed the spec, the tests (twice), and the code, and posted each review as a comment on PR #1. Claude (in chat, with no access to the repo) was a process coach: it explained the routine, wrote the prompts I pasted to each agent, and checked each agent's report against the spec. It wrote no code and posted nothing to the repo.

**Decisions I made myself:** accepting or declining each test-review finding (Missing 1, 2, 4 accepted; Missing 3 declined; losing-style tiers not allowed), approving the tests, accepting invalid input as out of scope for item 1 (tracked as backlog row 18), and confirming the 41 tests pass by running them myself.

**Checks I ran on my own:** `git diff` showed `tests/` unchanged after approval, and I ran the scoring function by hand on four answer sets.

### 2026-10-14 - Item 1 scoring built by DeepSeek, reviewed by ChatGPT

DeepSeek V4 Flash 0731 in Kilo was Agent 1 (builder) and ChatGPT was Agent 2 (reviewer), chosen for cost after the class costing walkthrough.

### 2026-10-13 - ChatGPT read an older copy of the tests, caught by a test count

**What happened:** Asked ChatGPT to describe the item 1 tests in plain English for the PR pause, using only tests/test_scoring.py and tests/fixtures/known_answers.json and told not to read specs/ or docs/. Its first answer listed 7 tests and said other two-way ties and three-way ties were not covered. I counted the test functions in the file and got 8. I asked ChatGPT to re-read the file. Its corrected answer described the eighth test, the one with four tie examples (Cultivator and Opportunity Seeker, Cultivator and Community Builder, Connector and Opportunity Seeker, and a three-way tie), and its list of gaps was updated to match.

**Likely cause:** The first answer matches the file as it stood after commit dbb1b98 (7 tests) and before commit ee22d5f added the tie-cases test (8 tests), so ChatGPT most likely read an older copy. This is consistent with git log. I cannot confirm which copy it was given.

**AI tools used, and for what:** ChatGPT again served as the independent second check, writing the plain-English descriptions and the coverage-gap list. Claude walked me through the same 8 tests separately and checked ChatGPT's corrected tie examples against the test file. The two descriptions agree.

**What surprised me:** I expected the second AI to be a safe check, and its first answer was wrong in a way I would not have caught by reading it. The count of tests in the file caught it. A reviewer is only as current as the file it is given.

**What I'm changing:** Each time the tests change, give the reviewing AI the current file again (paste it or re-upload it), and compare its test count to the file before relying on its summary.

**Still to do before approval:** Post the plain-English descriptions of all 8 tests on the pull request with my `approved`.


### 2026-10-12 - Tests described by a second AI, gaps found

**What happened:** Mapped the 7 acceptance criteria in specs/01-scoring-port.md to tests/test_scoring.py and found two thin spots: no dedicated test for the overall sum, and no test for winning totals of 11 and 19. Added three tests (commit dbb1b98) and confirmed they fail with ModuleNotFoundError because src/scoring.py does not exist yet. Then gave ChatGPT only the test file and the fixtures, with instructions not to read the spec, and asked it to describe every test in plain English. Its descriptions matched the spec on all 10 fixtures: Claude recomputed each fixture from the spec's question-to-style table and found no difference in totals, winner, or tier (no drift between the tests and the spec).

**AI tools used, and for what:** Claude is my primary AI tool. It worked with me on drafting the spec, wrote the original tests (commit bfdd8ed), and wrote the three tests added in dbb1b98. ChatGPT is the independent second check: it wrote the plain-English test descriptions for the pause and listed coverage it thought was missing. The routine says "a different AI writes tests"; I plan to ask my instructor whether that means different from the AI that drafted the spec, and will record the answer here.

**What surprised me:** ChatGPT's list of what the tests do not cover matched questions I had already been asking myself. The tie rule is tested for Connector-Cultivator and the four-way tie, but not for other two-way ties or any three-way tie. The tier boundaries at 11, 12, 19, and 20 are tested only through Cultivator, not systematically for the other three styles. Having a second AI reach the same gaps I suspected told me they were real, and not a worry I had made up.

**Decisions on ChatGPT's coverage gaps:** (1) Other tie combinations: adding tests for three more two-way ties and one three-way tie, because criterion 3 states a general rule and only one pair was tested. (2) Tier boundaries for the other three styles: deferred to docs/backlog.md. Criterion 4 is about the winning total, not any one style, and the fixtures already show other styles in low, mid, and high. (3) One-answer-at-a-time test: deferred to docs/backlog.md. The spec does not require it, and the fixtures catch many wrong assignments, though some could slip through where questions share identical answers, which is why it is logged as a deferred row.

### 2026-10-07 - Second AI attacks the spec

**What happened:** ChatGPT reviewed the scoring spec using the prompt from docs/course/routine.md, section 2. Its questions became rows 10 to 16 of the question round, and two fixtures were added (all 1s, all 4s), bringing the answer key to 10 answer sets. A second AI's description of the tests also surfaced two rules the spec had not written down: the question-to-style table and the rule that overall does not affect winner or tier. The same day, I separately gave ChatGPT the known answers and test_scoring.py with my own prompt (quoted below) to see what it thought the function must do.

**AI tools used, and for what:** ChatGPT attacked the spec as the second AI. Claude had worked with me on drafting it.

**What surprised me:** I gave ChatGPT the known answers and test_scoring.py with the prompt "Read these tests. In plain English, what must the function score_assessment do? Don't write the code." It came back saying the tests require no coaching text or AI service calls, and I had to tell it that was a later phase. That showed me the scope boundary lived only in my head. Nothing in the tests or fixtures said it. The spec's "What it does NOT do" section now says it in writing. The tie question also came up: the spec first assumed the earlier style wins an exact tie, and the reference code showed the later style wins, so the spec was corrected (question round, row 2).

### 2026-10-18 - Tidying the item 1 spec before starting item 2

**What happened:** Before branching for item 2, I reread the merged spec the way a grader would see it on GitHub and fixed four things. The spec status and the backlog row for item 1 now both say shipped. A note above the question round says where each group of questions came from: rows 1 to 9 from drafting, rows 10 to 16 from ChatGPT's question round, and rows 17 to 21 from the later test review. The "finalized after the tests were written" line in Notes was replaced with an order-of-work note, and a dated row was added to the Amendments table. No behavior and no acceptance criteria changed.

**AI tools used, and for what:** Claude (chat, no repo access) drafted the wording for each edit and explained why the question round note matters. I made every edit myself in VS Code and checked each one against the file.

**What surprised me:** The spec showed 21 question round rows, and the course says the question round asks at most 10 questions. Nothing in the file explained that the rows came from three different sources over time, so a grader could read it as a broken rule. I also decided against a glossary Claude suggested, because the readers of this file are my instructor and graders, and the plain-language writing that matters for non-coders belongs in the README.
### 2026-10-19 - Item 2 spec question round (ChatGPT)

**What happened:** I opened PR #2 for item 2 (embed the action-item content) and gave ChatGPT the spec with the prompt from docs/course/routine.md, section 2, plus the Connector block from the quiz as a sample. It asked 10 questions. I answered each, and every answer is in the spec's question round. The answers added new rules: the run fails unless there are exactly 60 items, every run rebuilds the store from scratch, queries have length and empty-input rules, and the stored and query embeddings must come from the same model. I also checked all four styles for a test phrase that appears in only one of the 60 items, and amended the acceptance criteria so each new rule can be tested. Then I decided to pause item 2 and build the input validation item (18b) first, because Stage 2 is due 10/30 and item 2 brings several new tools.

**AI tools used, and for what:** Claude (chat, no repo access) drafted the spec, helped me turn ChatGPT's questions into answers, and found the test phrases. ChatGPT ran the question round. I made the decisions and checked the TensorX model list myself.

**What surprised me:** TensorX has no embedding model, so the numbers step has to run on my own computer with a small model, which changed three of the answers (the model, the store, and the offline tests). I also found that a few action items appear word for word in two tiers, which will matter when item 3 searches the store.
### 2026-10-22 - Item 18b spec question round (ChatGPT)

**What happened:** I opened PR #3 for item 18b (the scorer rejects invalid input) and gave ChatGPT the spec with the prompt from docs/course/routine.md, section 2. It asked 7 questions, mostly about how strict "list" and "whole number" are and what the error messages say. I answered each, and every answer is in the spec's question round. The answers added new rules: only Python's own list and int are accepted, error messages name the type received but never the value, and a rejected list is left unchanged. I amended the acceptance criteria so each new rule has a test.

**AI tools used, and for what:** Claude (chat, no repo access) drafted the spec, turned ChatGPT's questions into draft answers for me to confirm, and rewrote the spec after each decision. ChatGPT ran the question round. I made the decisions.

**What surprised me:** I asked what a "bad" answer is, because every quiz answer from 1 to 4 is a fine choice. It means a value the scorer cannot use, such as a skipped question or a 7, and the word read like a judgment of the person. I changed the spec to say "invalid" and added a plain definition.

### 2026-10-22 - Item 18b tests, pause, and build (Claude, Claude Code, DeepSeek)

**What happened:** From the finished spec, Claude wrote 51 tests in tests/test_validation.py, and I pushed them to PR #3. The first run showed 47 failed and 4 passed. The 4 that pass are on purpose: they guard that old behavior (a valid list, a 1 or a 4 at question 7, the 41 old scoring tests) still works. GitHub's check was red for the same reason, 47 failed and 45 passed, which is the 4 guards plus the 41 old tests. Claude Code then checked the tests against the real repo and found one cosmetic issue, an unneeded fallback in the import line. I approved the fix and it was committed (1ff9a69). At the pause, I read the plain-English descriptions and the table against the spec's acceptance criteria and wrote my approval on the PR. Then DeepSeek V4 Flash in Kilo added 28 lines to src/scoring.py, with none removed, and all 92 tests passed. I checked the result myself: only src/scoring.py changed, tests/test_scoring.py is identical to main, 92 passed locally, and the GitHub check turned green.

**AI tools used, and for what:** Claude (chat, no repo access) wrote the tests and the plain-English descriptions. Claude Code, with access to the repo, checked the tests against the real code and was not allowed to edit anything except the test file, and only with my approval. DeepSeek V4 Flash in Kilo wrote the implementation and was not allowed to touch any test. I made the approval and merge decisions.

**What surprised me:** The red GitHub check was expected and not a sign of trouble. Turned green as soon as the test was run.
