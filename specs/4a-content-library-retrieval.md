# 4a - Retrieve content-library chunks for a user's result

**Story:** Enabler: As a developer, I can retrieve the right philosophy, archetype, and behavior
chunks for a user's score result from the #2b content library, so item #4b has material to
generate from.

**Backlog item:** #4a

**Status:** draft

## What it does

Given a user's score result (the same dict `score_assessment` returns: four style totals,
`winner`, `tier`), returns 6 chunks total from the #2b content-library store, each with its
source ID:

- The `philosophy_blend` chunk, always — not personalized, every user gets it.
- Both archetype chunks (`identity` and `strengths`) for the user's winning style.
- Exactly 3 behavior chunks: filtered first to the chunks whose `archetypes` list includes the
  user's winning style AND whose `mode` matches a tier-derived rule (`low` or `mid` tier →
  `building`; `high` tier → `using`), then ranked by closeness to a phrase built from the
  user's full four-style score pattern — same two-step filter-then-rank approach as item #3,
  applied to this store instead.

Same input against an unchanged store always returns the same 6 chunks in the same order.

## What it does NOT do

- Call TensorX or write any generated text. That's #4b.
- Retrieve `philosophy_werk_it_compass`. That chunk exists in the library but is reserved for a
  separate, not-yet-scoped worksheet feature — this item never returns it.
- Randomize which behavior chunks come back. Deliberately deterministic, like #2/#3. Variety on
  a retake is a possible future item, not this one.
- Read, modify, or depend on the #2/#3 `action_items` store in any way.
- Change the #2b build/embedding logic. This item only queries the store #2b already builds.
- Personalize to the user's raw 15 answers. Only to their score pattern (the four totals) and
  tier, same boundary #3 already drew.

## Acceptance criteria

- [ ] It's done when, for every one of the 4 winning styles, retrieval returns the
      `philosophy_blend` chunk, both archetype chunks for that style, and exactly 3 behavior
      chunks — 6 chunks total — each carrying its source ID.
- [ ] It's done when every returned behavior chunk has the user's winning style in its
      `archetypes` list and the tier-derived mode (`low`/`mid`→`building`, `high`→`using`).
- [ ] It's done when, for two sample score results sharing a winning style and tier but
      differing in their other three totals, the ranked set of 3 behavior chunks differs
      between them.
- [ ] It's done when the same input against an unchanged store returns the identical 6 chunks
      in the identical order every time.
- [ ] It's done when a missing store, a corrupted/malformed score result, or a mismatched
      embedding model each raise a clear error, reusing #2b's and #3's existing error patterns
      rather than inventing new ones.
- [ ] It's done when `python3 -m pytest` runs this item's tests with no failures, and all
      existing tests (items #1, #2, #2b, #3, #18a, #18b) still pass unchanged.

## Question round

<!-- Paste the questioner AI's questions here with your one-line answers. -->

| # | Question | Answer |
|---|---|---|
| 1 | What exactly counts as a valid score result? Should #4a require the same seven keys as #3, including `overall`, and reject extra keys, booleans, and numeric strings? Should it inherit #3's bounds of 0–24 per style with at least one nonzero total and no range check on `overall`, or enforce the scorer's actual ranges of 6–24 per style and 15–60 overall? | Reuse #3's exact validation wholesale — same 7 keys, same rejection of extra keys/booleans/numeric strings, same 0–24-per-style range with the all-zero and overflow guards. Don't tighten to the scorer's real 6–24/15–60 ranges, same reasoning as #3's own amendment: the broader check closes the crash risk without inventing an unauthorized restriction. Since #4a receives the identical dict #3 does, this should call #3's existing validation function rather than duplicate it. |
| 2 | Who decides the winner and tier? Once `winner` and `tier` pass validation as exact, case-sensitive names, should #4a trust them as #3 does, or reject a result if they conflict with the totals or the scorer's tie rule? | Same as #3 — trust them as given, never cross-check against the totals or the scorer's tie rule. |
| 3 | How should the four scores become a search phrase? Should #4a reproduce #3's wording, style order, and strong/moderate/light cutoffs at 85%/55%, or may the phrase and cutoffs be tuned against the #2b library? Should only the four style totals feed that phrase? | Reuse #3's general approach (translating each style's total into a strong/moderate/light qualifier), but the exact wording and cutoffs may be tuned empirically against the #2b library's actual text during test-writing, same as #3's own phrase was tuned empirically against #2's content, not assumed. Only the four style totals feed it, same as #3. |
| 4 | How exactly should behaviors be ranked? Cosine distance, alphabetical tie-break by source_id including third-place ties? Should near-equal distances keep numeric order or count as ties within a tolerance? | Same cosine distance measure, same alphabetical tie-break by source_id including third-place ties, no tolerance window — exact numeric order, matching #3's existing precision. |
| 5 | Which stored fields decide what matches? philosophy_blend by source ID, archetype chunks by archetype+piece, behaviors by exact archetypes membership + exact mode? Are the naming conversions opportunitySeeker→opportunity_seeker and communityBuilder→community_builder correct? | Yes to all three matching rules, and yes to both conversions (connector/cultivator need no conversion, already matching). |
| 6 | What should #4b receive? A flat list of philosophy_blend, identity, strengths, then 3 ranked behaviors, each with source_id, text, layer, and full metadata? Should distance be exposed, and what should the three fixed chunks carry for it? | Flat list of 6 in that order, each with source_id, text, layer, metadata, and distance — matching #3's QueryResult shape. For the 3 fixed (non-ranked) chunks, distance is None, since they weren't selected by similarity. |
| 7 | What makes a store usable for this request? Should a missing philosophy_blend, zero/multiple archetype matches, or fewer than 3 eligible behaviors raise an error? Is the six-per-style-and-mode count a requirement? | Any of these fails the request: philosophy_blend missing, not-exactly-one match for either archetype piece, or fewer than 3 eligible behaviors. 3, 4, or 5 eligible behaviors is fine — only the "at least 3" floor matters; the real count being 6 everywhere isn't a hard requirement, just a verified fact about the current library. |
| 8 | Which errors should callers be able to distinguish — RetrievalError vs #2b's QueryError? How should malformed stored tags, unusable vectors, or phrase-to-vector conversion failures be reported? What's the check order, and do score errors omit caller-supplied values? | RetrievalError for anything about the caller's input or the store's content being insufficient (bad score dict, missing/wrong-count chunks). QueryError for anything about reaching or using the store/model itself (missing store, unreadable, model mismatch, embedding/phrase-conversion failure). Input validated before any store access, same order as #3. Score errors never echo caller-supplied values, same rule as #3. |
| 9 | What proves personalization for acceptance? Does a different source ID matter, or does reordering count? Which fixture pair, and does the check need the real library or also a small test library? | Require at least one different source ID among the 3 returned — a reordering of the same 3 is not sufficient proof. Reuse #3's existing connector_mid/mixed_realistic fixture pair rather than inventing new ones. Cover both: a small hand-built synthetic library for the default suite (so it doesn't silently skip), plus a real-library test that skips when unavailable — same dual-coverage pattern #2b ended up with after review. |
| 10 | What should happen if #2b rebuilds during retrieval? Must a response take all six chunks from one published version? Should #4a retry against a new version or raise an error if the version becomes unavailable mid-request? | All 6 chunks must come from one single published version, never a mix of old and new mid-rebuild, consistent with #2b's atomic-swap guarantee. If that version becomes unavailable mid-request, raise a clear error rather than silently retrying — no retry logic, fail loud, same philosophy as everywhere else in this project. |

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Verified against the real `knowledge_base/` files: every style/mode combination has exactly
  6 matching behavior chunks, comfortably more than the 3 needed — no combination risks coming
  up short.
- Mirrors item #3's filter-then-rank pattern closely: narrow by metadata that matches the
  person first (style + tier-derived mode here, vs. style + tier directly for #3), then rank
  the narrowed set by a phrase built from the full score pattern.
- `philosophy_werk_it_compass` is unused by this item on purpose — see "What it does NOT do."
  Worth a note in #2b's spec too, so it's clear elsewhere why that chunk looks orphaned.
