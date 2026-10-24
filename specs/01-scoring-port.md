# 01 - Scoring port

**Story:** Enabler: As a developer, I can run the existing 15-question scoring logic in Python with passing tests, so scoring behavior is preserved before anything gets built on top of it.
**Backlog item:** #1
**Status:** shipped

## What it does

A Python function, `score_assessment(answers)`, takes the 15 answers a person gave (each a number from 1 to 4, in question order) and returns the results defined by the reference scoring behavior verified on 2026-09-27 and recorded in the answer key: an overall score out of 60, a total out of 24 for each of the four styles (Connector, Cultivator, Opportunity Seeker, Community Builder), the winning style, and a tier (low, mid, or high) based on the winner's total. Some questions count toward more than one style, exactly as they do in that reference behavior. The function is the scoring half of the quiz with no screens, no coaching text, and no AI.

## What it does NOT do

- Write, retrieve, or generate any coaching text, and read nothing from the knowledge base.
- Call any AI service or make any network request.
- Change a scoring rule, a threshold, or the question-to-style mapping from the reference scoring behavior verified on 2026-09-27 and recorded in the answer key.
- Add a cluster layer (Value Creation, Network Expansion, and so on). The flat model is ported as it is; the cluster version is logged as a deferred row in `docs/backlog.md`.
- Check for bad input such as missing answers, values outside 1 to 4, or a list that is not 15 long.
- Return a tier for the three styles that did not win. This is a specific prohibition and overrides the general extra-fields allowance in question 5, which is meant for things like cluster subtotals (see question 21).
- Draw any screen. This is logic only.

## Acceptance criteria

- [ ] It's done when each of the 10 answer sets in `tests/fixtures/known_answers.json` returns exactly the overall score, four style totals, winner, and tier listed for it.
- [ ] It's done when the overall score equals the sum of all 15 answers, with each answer counted once.
- [ ] It's done when an exact tie for the highest total goes to the later style in the order `connector`, `cultivator`, `opportunitySeeker`, `communityBuilder` (`connector` 16 and `cultivator` 16 returns `cultivator`).
- [ ] It's done when a winning total below 12 returns "low", 12 through 19 returns "mid", and 20 or more returns "high" (a total of exactly 12 returns "mid", exactly 20 returns "high", and 11 returns "low").
- [ ] It's done when all 15 answers being 1 returns 6 for every style, 15 overall, `communityBuilder`, and "low", and all 15 answers being 4 returns 24 for every style, 60 overall, `communityBuilder`, and "high".
- [ ] It's done when the same 15 answers always return the same result, and the list passed in is unchanged afterward.
- [ ] It's done when `python3 -m pytest tests/test_scoring.py` runs with no failures.

## Question round

Where these questions came from:

- Rows 1-9: written while drafting the spec (Claude and Sharon).
- Rows 10-16: ChatGPT's question round, using the prompt in docs/course/routine.md, section 2.
- Rows 17-21: a later full test review on 2026-10-14, not a question round.


| # | Question | Answer |
|---|---|---|
| 1 | What does "preserved" mean for the port? | Same overall score, same four style totals, same winner, same tier as the reference JavaScript verified on 2026-09-27 for the same answers. Close is not enough. |
| 2 | What happens when two styles tie for the highest total? | The later style in the order `connector`, `cultivator`, `opportunitySeeker`, `communityBuilder` wins. This is how the reference code behaves, and it corrects an earlier assumption that the first style would win. |
| 3 | Does this item build the cluster model (Value Creation, Network Expansion, and so on)? | No. The simpler flat model recorded in the answer key gets ported first. The cluster version is logged as a deferred row in `docs/backlog.md`. |
| 4 | Does this item include any coaching text or AI? | No. Feedback and voice work belong to items #2 to #4. |
| 5 | What does the function return? | Seven named values: `connector`, `cultivator`, `opportunitySeeker`, and `communityBuilder` (the four style totals), plus `overall`, `winner`, and `tier`. `winner` is one of those four style names, spelled exactly the same way, and `tier` is `low`, `mid`, or `high`. Extra fields are allowed later, for example cluster subtotals, without breaking the tests. |
| 6 | Does it return a tier for every style or only the winner? | Winner only for now. The reference behavior also uses a tier for each style's coaching line, so a later item may need per-style tiers. |
| 7 | How should it handle missing or invalid answers? | This function assumes 15 valid answers with values from 1 to 4. Input validation is outside this item and must be addressed when exposing scoring through a server. |
| 8 | Does the overall score affect the winner or the tier? | No. Winner and tier come only from the four style totals. Overall is informational. |
| 9 | Which questions count toward which style? | See the table in Notes. Some questions count toward more than one style. |
| 10 | What are the complete tier ranges? | A winning total below 12 is `low`, 12 through 19 is `mid`, and 20 or more is `high`. A style total can be at most 24. |
| 11 | What counts as a valid answer? | The whole numbers 1, 2, 3, and 4 only. Decimals such as 2.5 are not valid, and the function does not check for them. |
| 12 | What if the written spec, the answer key, and the original JavaScript disagree? | Stop and ask Sharon. Until she decides, the verified answer key wins, and the resolution is recorded as a dated row in Amendments. |
| 13 | What are the input and output formats? | Input is a list of 15 whole numbers. Output is a dictionary with the seven named values: the four style totals and `overall` are whole numbers, and `winner` and `tier` are text. The tests compare values, so whole-number type is not separately enforced. |
| 14 | Is behavior on invalid input deliberately unspecified? | Yes. The function may raise an ordinary Python error or return a meaningless result, and nothing is guaranteed until validation exists. A list longer than 15, or values outside 1 to 4, would score without any error. |
| 15 | Should completion require more than the eight fixtures? | Yes. Two fixtures are added: all answers 1 (four-way tie, `communityBuilder`, `low`) and all answers 4 (maximum score, `communityBuilder`, `high`). The answer key now has 10 answer sets. |
| 16 | Who guarantees the order of the answers? | The caller. Position 1 in the list must be the answer to question 1, and so on. The function cannot detect reordered answers. |
| 17 | Should the tests check that scoring makes no network request? | Yes. A test is added that blocks network connections and fails if scoring tries to open one. The AI-service and coaching-text prohibitions are checked in code review instead of by a test. |
| 18 | Should tests cover every style's tier transitions, not just Cultivator's? | No. Per-style tier transitions and each question's individual contribution to the totals are deferred (backlog items 16 and 17). The 10 answer sets are the acceptance criteria. |
| 19 | Should the unchanged-answer promise be checked across every answer set? | Yes. The test now verifies the answer list is unchanged after scoring for all 10 fixtures, not just the first. |
| 20 | Should tests cover the Connector/Community Builder and Opportunity Seeker/Community Builder ties? | Yes. Both missing tie pairs are added to the tie test, alongside the existing Cultivator/Connector, Cultivator/Community Builder, Connector/Opportunity Seeker, and three-way ties. |
| 21 | May the function return a tier for the three styles that did not win? | No. The "does not do" rule is specific and overrides the general extra-fields allowance in question 5, which is meant for things like cluster subtotals. Code review will check this. |

## Amendments

| Date | Change | Why |
|---|---|---|
| 2026-10-24 | Invalid input is now rejected with a ValueError (see item 18b). Previously left unspecified (question round rows 7, 11, 14). | Item 18b merged. |
| 2026-10-07 | Added the question-to-style table (Notes) and question 8 (overall does not affect winner or tier). | Neither was written in the spec. A second AI's description of the tests restated both. |
| 2026-10-07 | Added question round rows 10 to 16, spelled out the tier ranges, and added the four-way tie and maximum cases (answer key now has 10 answer sets). | A second AI (ChatGPT) attacked the spec with the prompt from `docs/course/routine.md`, section 2. |
| 2026-10-14 | Added question round rows 17 to 21 and applied the review resolutions: added a no-network test, added the two missing tie pairs, checked the unchanged-answer promise across all 10 fixtures, and clarified that per-style tiers are deferred. | A full test review found coverage gaps; the item was on pause. |
| 2026-10-18 | Status set to shipped; added question sources and an order-of-work note. | Readability for reviewers. No change to behavior or criteria. |

## Notes

- Reference behavior: the scoring code in `networking-assessment.html` (repo `werkitgirls-resources`), verified on 2026-09-27 against live quiz runs.
- Answer key: `tests/fixtures/known_answers.json`, derived from that JavaScript and not from any Python code.
- Tests: `tests/test_scoring.py`. A stub `src/scoring.py` (which only raises `NotImplementedError`) lets every test load and run and fail individually, instead of stopping at import with `No module named 'src.scoring'`. At the time the tests were written, no scoring logic existed yet.
- Order of work: the spec was drafted first, then the tests were written against it. The spec was amended afterward, after ChatGPT's question round (2026-10-07) and after the test review (2026-10-14). The Amendments table has the dates and reasons.
- Question round rows 10 to 16 came from ChatGPT, a different AI from the one that drafted the spec, using the prompt from `docs/course/routine.md`, section 2.
- Related: the deferred cluster-scoring row in `docs/backlog.md`, and the action-item bug fix in `werkitgirls-resources/CHANGELOG.md`.

Question-to-style mapping (question numbers start at 1; matches `tests/fixtures/known_answers.json`):

| Style | Questions |
|---|---|
| connector | 4, 8, 10, 13, 14, 15 |
| cultivator | 1, 2, 5, 7, 9, 12 |
| opportunitySeeker | 3, 6, 8, 11, 13, 14 |
| communityBuilder | 3, 4, 6, 10, 11, 15 |

### Criteria-to-test map (written at the pause, 2026-10-13)

Which tests in `tests/test_scoring.py` cover each acceptance criterion. Use it to predict which tests fail when something breaks, and to see which tests change when a criterion is amended.

| # | Criterion (short form) | Covered by |
|---|---|---|
| 1 | Each of the 10 saved answer sets returns its listed result | Saved answer sets test (runs 10 times) |
| 2 | Overall score equals the sum of all 15 answers | Overall score test (runs 10 times); also checked by the saved answer sets |
| 3 | Exact tie goes to the later style | Connector and Cultivator tie test; More ties test (runs 6 times, covering Connector/Opportunity Seeker, Cultivator/Opportunity Seeker, Cultivator/Community Builder, Connector/Community Builder, Opportunity Seeker/Community Builder, and a three-way tie); the tie and all-ones sets inside the saved answer sets |
| 4 | Below 12 is low, 12 to 19 is mid, 20 or more is high | Tier edges test (12 and 20); winning total of 11 test; winning total of 19 test |
| 5 | All 1s and all 4s give the listed totals, winner, and tier | Saved answer sets test only, through the `all_ones_four_way_tie` and `all_fours_maximum` fixtures |
| 6 | Same answers give the same result, and the input is unchanged | Repeatable and harmless test, now run against all 10 answer sets |
| 7 | The whole test file runs with no failures | No single test. Checked when the suite passes at the build step and by the GitHub run |

**Things to remember**
- Criterion 5 has no dedicated test. Its coverage depends on the two named fixtures staying in `tests/fixtures/known_answers.json`, so treat that file as part of the spec.
- Criterion 4 is about the winning total, not any one style. The tier edges at 11, 12, 19, and 20 are tested through Cultivator only; the other three styles are deferred (backlog item 16).
- Each question's individual contribution to the style totals is not tested directly (backlog item 17).
- Wrong answer counts and values outside 1 to 4 are not tested. This is deliberate: see Question round answers 7, 11, and 14. Validation has to be added when scoring is exposed through a server.
- The no-network test covers the "makes no network request" line under "What it does NOT do", not an acceptance criterion, so it is not listed in the map above. The AI-service and coaching-text prohibitions are reviewed in code, not tested.

## User test (2026-10-14)
| 2026-10-18 | Status set to shipped; added question sources, an order-of-work note, and a glossary. | Readability for reviewers and testers. No change to behavior or criteria. |

Manual runs of `score_assessment` done by Sharon in the terminal on 2026-10-14, after the build. Each entry lists what she tried, what she expected, what happened, and which step it went back to. No bugs found: all four went back to none.

1. `[4] * 15` → expected all four styles at 24, overall 60, communityBuilder winning the four-way tie, tier high. Happened: exactly that, matched expectation. Went back to none.
2. `[1, 1, 1, 4, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 4]` → expected connector 15, cultivator 6, opportunitySeeker 6, communityBuilder 15, overall 24, winner communityBuilder, tier mid. Happened: exactly that, matched expectation. Went back to none.
3. `[7] + [1] * 14` (an out-of-range answer) → expected connector 6, cultivator 12, opportunitySeeker 6, communityBuilder 6, overall 21, winner cultivator, tier mid, with the 7 accepted silently and no error. Happened: exactly that, matched expectation. The out-of-range value was accepted without error because questions 7, 11, and 14 leave input validation out of item 1; tracked as backlog row 18. Went back to none.
4. `[1] * 14` (too short) → expected a crash. Happened: crashed with an `IndexError` at `src/scoring.py` line 46, matched expectation. Also tracked in backlog row 18. Went back to none.
