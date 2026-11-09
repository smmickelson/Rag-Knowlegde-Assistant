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
| 1 |  |  |

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
