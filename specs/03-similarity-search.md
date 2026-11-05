# 03 - Similarity search against the embedded content

**Story:** Enabler: As a developer, I can run a similarity search against the embedded content and get back the most relevant chunks, each carrying a source ID, for a given user's cluster scores.
**Backlog item:** #3
**Status:** questioned

## What it does

Given a user's score result (the dict `score_assessment` returns: the four style totals, `winner`, and `tier`), this item finds the 3 most relevant action-item chunks from the vector store item #2 built, and returns each one with its source ID.

Retrieval happens in two steps. First, the search is narrowed to the user's winning style and tier before anything else — the 5 chunks stored under that exact style-tier pair (for example `connector-mid-1` through `connector-mid-5`) — using the style and tier metadata every chunk already carries, not a free-text guess at matching the right bucket. Second, within that narrowed set of 5, the chunks are ranked by closeness to a search phrase built from the user's full score pattern — all four style totals, not only the winning one — so two people who share a winning bucket but differ in their other three totals can see a different one of the 5 chunks ranked first.

This personalizes to the shape of someone's scores, not their specific answers. Two different sets of 15 answers can land on identical totals, and this item has no way to tell them apart — only `score_assessment`'s output reaches it, never the raw answers. True answer-level personalization is backlog items #13/#14's job, once the content library has material tagged by individual question.

## What it does NOT do

- Call TensorX or write any coaching text. That's #4b.
- Add new content to the library. That's already built (#2); expanding it with question-level material is #13, deferred to v2.
- Change the quiz screen, the scoring logic, or the embedding build. Items #1, #18a, #18b, and #2 stay exactly as they are.
- Personalize to a user's raw 15 answers. Only to their score pattern (the four totals), as described above.
- Handle open-ended, typed-in questions. That's #14.
- Replace `query_store`'s existing behavior (an unfiltered, whole-library search). This item adds a new, separately tested filtered-search path alongside it, not a replacement — item #2's own tests must keep passing unchanged.

## Acceptance criteria

- [ ] It's done when, for each of the 5 sample answer sets in Notes, searching with that person's score result returns exactly 3 chunks, every one of them tagged with that person's winning style and tier.
- [ ] It's done when every returned chunk carries its source ID (for example `connector-mid-3`), traceable back to the item #2 store.
- [ ] It's done when the search is scoped to the matching style-and-tier chunks before ranking, not by taking the top 3 across the whole 60-item library and checking afterward that they happen to match — proven by a case where the correct bucket's best match is not among the whole-library top 3, yet still comes back correctly once scoped.
- [ ] It's done when, for two sample answer sets that share a winning style and tier but differ in their other three totals, the top-ranked chunk differs between them — proving the ranking step responds to the full score pattern, not just the winning bucket.
- [ ] It's done when `python3 -m pytest` runs this item's tests with no failures, and all existing tests (items #1, #2, #18a, #18b) still pass unchanged.

## Question round

<!-- Paste the questioner AI's questions here with your one-line answers.
     Every answer goes in, including "no, keep current behavior."
     An answer recorded here never has to be argued again. -->

| # | Question | Answer |
|---|---|---|
| 1 | Must the ranking show sensitivity beyond the one fixture pair, or is that pair enough? | The fallback pair documented in Notes is sufficient. Acceptance criterion 4 requires differentiation for one same-bucket pair (with a named fallback if needed), not general sensitivity across every possible pair. |
| 2 | What is the exact accepted input contract — required keys, types, extra keys? | Input must be exactly the dict `score_assessment` returns: the four style totals as ints, `overall` as an int, `winner` as one of the four style names, `tier` as one of `high`/`mid`/`low`. Only the built-in `dict` type is accepted, no subclasses. Missing keys, wrong types, non-dict input, or unexpected extra keys each raise a new `RetrievalError` naming the problem but never the value. |
| 3 | If the supplied `winner`/`tier` contradict the four totals, does retrieval trust them or recompute? | Trusted as given, never recomputed — this item only consumes `score_assessment`'s output. `winner` must be one of the four known style names and `tier` one of the three known tiers, but they are not cross-checked against the totals. |
| 4 | What happens if the matching bucket has fewer than 3 valid chunks? | Not a normal case: item #2's build guarantees exactly 5 items per style-tier bucket. A bucket with fewer than 3 means the store is corrupted, not something to recover from gracefully — it raises `RetrievalError` rather than returning fewer results. |
| 5 | What happens if the store is missing, corrupt, or built with a different embedding model? | Reuses item #2's existing `QueryError` behavior for a missing store or mismatched embedding model exactly as-is; no new handling needed. |
| 6 | How are style names matched — normalized, case-insensitive, or exact? | Only the four exact, case-sensitive style names already used throughout the codebase are accepted (`connector`, `cultivator`, `opportunitySeeker`, `communityBuilder`). No normalization of casing or whitespace. Anything else raises `RetrievalError` naming the received type, never the value. |
| 7 | What is the exact return contract? | The same `QueryResult` shape item #2 already uses: an ordered list of 3 results, each with `source_id`, `text`, `style`, `tier`, and `distance`. All 3 source IDs are guaranteed unique. |
| 8 | How are ties broken, and is the result deterministic? | Same alphabetical-by-source-ID tie-break item #2's `query_store` already uses. Identical input against an unchanged store always returns identical results in identical order. |
| 9 | If a stored chunk has bad or duplicate metadata, does retrieval catch it? | Out of scope for this item — item #2's build validation already guarantees clean, unique metadata for every stored chunk. This item trusts that and does not re-validate it. |
| 10 | What governs the empirical search-phrase tuning and fallback pair? | No restriction beyond what Notes already says: the phrase is settled empirically against real embeddings during test-writing (not mocked data), with the documented fallback fixture pair if the primary pair doesn't differentiate cleanly. |

## Amendments

| Date | Change | Why |
|---|---|---|
|  |  |  |

## Notes

- The 5 sample answer sets are existing, already-shipped fixtures from `tests/fixtures/known_answers.json` — no new fixtures needed:
  - `cultivator_high` → winner `cultivator`, tier `high`
  - `connector_mid` → winner `connector`, tier `mid`
  - `opportunity_seeker_low` → winner `opportunitySeeker`, tier `low`
  - `community_builder_mid` → winner `communityBuilder`, tier `mid`
  - `mixed_realistic` → winner `connector`, tier `mid` (same bucket as `connector_mid`, but with meaningfully different secondary totals — cultivator 6 vs. 13, opportunitySeeker 12 vs. 15, communityBuilder 12 vs. 15 — this is the pair that tests the ranking criterion above)
- `action_item_store.py`'s existing `query_store` function has no way to filter by metadata before ranking; Chroma's underlying `collection.query` supports a `where` clause for this, but nothing in the current code uses it. This item adds that filtered path as a new function rather than changing `query_store`'s signature or behavior, so item #2's own tests are untouched.
- The exact search phrase built from a user's four style totals (for the within-bucket ranking step) is an implementation detail for the build step to settle, verified empirically against the fixture pair above during test-writing — same as how item #2's test phrases were confirmed by running real queries rather than assumed. If `connector_mid`/`mixed_realistic` doesn't differentiate cleanly once real embeddings are available, swap in one of the other two same-bucket pairs already present in the fixtures (`boundary_mid_exact`/`tie_connector_cultivator`, both `cultivator`/`mid`) and record the swap here as an amendment.
