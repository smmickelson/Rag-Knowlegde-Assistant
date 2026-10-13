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