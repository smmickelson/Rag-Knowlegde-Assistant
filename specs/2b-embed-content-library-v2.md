# 2b - Embed the new four-layer content library

**Story:** Enabler: As a developer, I can chunk and embed the new four-layer content library (philosophy, archetype, behavior) from `knowledge_base/` into a vector store, so item #4b can retrieve from it instead of the old flat action-item store.

**Backlog item:** #2b

**Status:** draft

## What it does

Reads every markdown file in `knowledge_base/` (repo `werkitgirls-resources`) as plain text: 2 philosophy files, 8 archetype files, 30 behavior files, 40 total. Each file becomes exactly one chunk. Its YAML frontmatter is parsed and kept as metadata (`layer`, plus `archetype`/`piece` for archetype files, or `question`/`slug`/`mode`/`archetypes` for behavior files); its body text below the frontmatter is the chunk's stored text. The source ID for each chunk is its filename without the `.md` extension (for example `behavior_q04_connect_others_building`). Chunks are embedded by the same small local model already in use (Chroma's built-in `all-MiniLM-L6-v2`) and saved in a new, separate file-based Chroma store in `data/`. A query returns the 3 closest chunks. Every run rebuilds this store from scratch.

## What it does NOT do

- Touch, rebuild, or delete the existing `action_items` store built by item #2. This item writes to its own store location; the old store keeps working untouched.
- Embed the situational layer (items #13/#14). No files exist there yet — this item covers only the 40 files currently in `knowledge_base/`, and will need a rerun once situational files are added.
- Decide how #4b ranks or filters these chunks for a given user's answers. That's a separate step (the analogue of item #3 for this new store), scoped later.
- Call TensorX or write any generated coaching text. That's item #4b.
- Change `networking-assessment.html` or any file outside `knowledge_base/`.
- Store any user answers or personal data.
- Update the store item by item. A run replaces the whole store or leaves the old one untouched, same as item #2.

## Acceptance criteria

- [ ] It's done when building from `knowledge_base/` stores exactly 40 chunks — 2 philosophy, 8 archetype, 30 behavior — each with non-empty text, a unique source ID, and valid frontmatter metadata, and when the folder has any other count, a file with missing or malformed frontmatter, or an empty body, the run stops with an error naming the problem and stores nothing.
- [ ] It's done when the text of every stored chunk matches the file's body content exactly (frontmatter stripped, nothing else altered), checked by a test.
- [ ] It's done when the vector store holds one embedding for each of the 40 chunks, each lookup-able by its source ID, with its frontmatter fields stored and retrievable as metadata.
- [ ] It's done when a test query using a known phrase from each of the three layers (one philosophy, one archetype, one behavior) returns the expected chunk as the first result.
- [ ] It's done when running the build twice leaves exactly the same 40 chunks with no leftover records, and a run that fails leaves the previous version of this store unchanged.
- [ ] It's done when this item's store lives at a location separate from the existing `action_items` store, and running this build never modifies, reads from, or deletes that existing store.
- [ ] It's done when an empty or whitespace-only query, and a query over 500 characters, each stop with a clear error, and a query embedded with a different model than the store's stops with an error naming both.
- [ ] It's done when `python3 -m pytest` runs the tests for this item with no failures, with no internet or password needed after the model's first download.

## Question round

<!-- Paste the questioner AI's questions here with your one-line answers. -->

| # | Question | Answer |
|---|---|---|
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Source: 40 files in `knowledge_base/` in the `werkitgirls-resources` repo, built 2026-11-07 — `philosophy_werk_it_compass.md`, `philosophy_blend.md`, 8 `archetype_*_{identity,strengths}.md` files, and 30 `behavior_q01` through `behavior_q15` `_{building,using}.md` pairs.
- Frontmatter shapes:
  - Philosophy: `layer: philosophy`, `piece: werk_it_compass` or `blend`.
  - Archetype: `layer: archetype`, `archetype: connector|cultivator|opportunity_seeker|community_builder`, `piece: identity|strengths`.
  - Behavior: `layer: behavior`, `question: 1`-`15`, `slug: <question-slug>`, `mode: building|using`, `archetypes: [<one or more of the four archetype names>]`.
- Chunk size: one file per chunk, same as item #2's one-action-item-per-chunk approach.
- This item is scoped to embedding only, mirroring how item #2 was scoped before item #3 added ranking/retrieval for that store. A follow-on item (the analogue of #3) will cover querying this store for a given user's answers.
- The old `action_items` store (item #2) and this new store can coexist in `data/` under different names/paths for as long as needed; nothing requires removing the old one before this ships.
