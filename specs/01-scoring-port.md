# 01 - Scoring port

**Story:** As a developer, I can run the existing 15-question scoring logic in Python with passing tests, so scoring behavior is preserved before anything gets built on top of it.
**Backlog item:** #1
**Status:** approved

## What it does

A Python function, `score_assessment(answers)`, takes the 15 answers a person gave (each a number from 1 to 4, in question order) and returns the results defined by the reference scoring behavior verified on 2026-09-27 and recorded in the answer key: an overall score out of 60, a total out of 24 for each of the four styles (Connector, Cultivator, Opportunity Seeker, Community Builder), the winning style, and a tier (low, mid, or high) based on the winner's total. Some questions count toward more than one style, exactly as they do in that reference behavior. The function is the scoring half of the quiz with no screens, no coaching text, and no AI.

## What it does NOT do

- Write, retrieve, or generate any coaching text, and read nothing from the knowledge base.
- Call any AI service or make any network request.
- Change a scoring rule, a threshold, or the question-to-style mapping from the reference scoring behavior verified on 2026-09-27 and recorded in the answer key.
- Add a cluster layer (Value Creation, Network Expansion, and so on). The flat model is ported as it is; the cluster version is logged as a deferred row in `docs/backlog.md`.
- Check for bad input such as missing answers, values outside 1 to 4, or a list that is not 15 long.
- Return a tier for the three styles that did not win.
- Draw any screen. This is logic only.

## Acceptance criteria

- [ ] It's done when each of the 8 answer sets in `tests/fixtures/known_answers.json` returns exactly the overall score, four style totals, winner, and tier listed for it.
- [ ] It's done when the overall score equals the sum of all 15 answers, with each answer counted once.
- [ ] It's done when an exact tie for the highest total goes to the later style in the order `connector`, `cultivator`, `opportunitySeeker`, `communityBuilder` (`connector` 16 and `cultivator` 16 returns `cultivator`).
- [ ] It's done when a winning total of exactly 12 returns "mid", exactly 20 returns "high", and 11 returns "low".
- [ ] It's done when the same 15 answers always return the same result, and the list passed in is unchanged afterward.
- [ ] It's done when `python3 -m pytest tests/test_scoring.py` runs with no failures.

## Question round

| # | Question | Answer |
|---|---|---|
| 1 | What does "preserved" mean for the port? | Same overall score, same four style totals, same winner, same tier as the reference JavaScript verified on 2026-09-27 for the same answers. Close is not enough. |
| 2 | What happens when two styles tie for the highest total? | The later style in the order `connector`, `cultivator`, `opportunitySeeker`, `communityBuilder` wins. This is how the reference code behaves, and it corrects an earlier assumption that the first style would win. |
| 3 | Does this item build the cluster model (Value Creation, Network Expansion, and so on)? | No. The simpler flat model recorded in the answer key gets ported first. The cluster version is logged as a deferred row in `docs/backlog.md`. |
| 4 | Does this item include any coaching text or AI? | No. Feedback and voice work belong to items #2 to #4. |
| 5 | What does the function return? | Seven named values: `connector`, `cultivator`, `opportunitySeeker`, and `communityBuilder` (the four style totals), plus `overall`, `winner`, and `tier`. `winner` is one of those four style names, spelled exactly the same way, and `tier` is `low`, `mid`, or `high`. Extra fields are allowed later, for example cluster subtotals, without breaking the tests. |
| 6 | Does it return a tier for every style or only the winner? | Winner only for now. The reference behavior also uses a tier for each style's coaching line, so a later item may need per-style tiers. |
| 7 | How should it handle missing or invalid answers? | This function assumes 15 valid answers with values from 1 to 4. Input validation is outside this item and must be addressed when exposing scoring through a server. |

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Reference behavior: the scoring code in `networking-assessment.html` (repo `werkitgirls-resources`), verified on 2026-09-27 against live quiz runs.
- Answer key: `tests/fixtures/known_answers.json`, derived from that JavaScript and not from any Python code.
- Tests: `tests/test_scoring.py`, committed as `bfdd8ed` while `src/scoring.py` did not exist. They failed with `No module named 'src.scoring'`.
- This spec was finalized after the tests were written. The question round above records the decisions made while writing them.
- Related: the deferred cluster-scoring row in `docs/backlog.md`, and the action-item bug fix in `werkitgirls-resources/CHANGELOG.md`.
