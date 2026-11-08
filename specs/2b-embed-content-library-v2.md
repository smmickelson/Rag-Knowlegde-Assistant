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
| 1 | What build command and store path should #2b use, and which files outside `knowledge_base/` may it add or change? | No CLI command — a Python function (e.g. `build_store(knowledge_base_dir, store_dir)` in a new module, mirroring `action_item_store.py`) called directly or from a test. It reads only from `knowledge_base/` and writes only inside the given `store_dir` (default `data/content_library/`, kept separate from item #2's store); no other file is read, created, modified, or deleted. |
| 2 | If a build is interrupted while replacing the store, what must a reader see during the rebuild and after restart? Should the store path remain absent if the first build fails? | Same crash-safety pattern as item #2: built in a temp directory, atomically swapped in only once complete. A reader always sees either the complete previous store or the complete new one, never a partial one. If the very first build fails, the store path remains absent. |
| 3 | If two builds start at the same time, should the second wait, fail, or be allowed to publish? What if source files change mid-build? | A second concurrent build fails with a clear error rather than racing to publish. A build already in progress reading from `knowledge_base/` completes against the snapshot it read; it does not need to detect a mid-build change — the next rebuild simply picks it up. |
| 4 | Is the input contract the exact 40 filenames, or can a replacement pass if layer counts match? Must each expected pair appear exactly once with metadata matching its filename? | The contract is exact: all three layer counts (2/8/30) must match, every expected archetype/piece and question/mode combination must appear exactly once, and each file's frontmatter must agree with what its filename implies (e.g. `behavior_q04..._building.md` must have `question: 4` and `mode: building`). A mismatch between filename and frontmatter is a build error. |
| 5 | Which files count toward the 40 — recurse into subfolders, hidden files, `.MD`, symlinks, future situational files? | Flat and exact: only files directly inside `knowledge_base/` ending in lowercase `.md` count. No recursion, no hidden files, no `.MD`/mixed case, no following symlinks. Future situational files aren't specially ignored — they'll just change the expected count once added, which is why this item's criteria say "exactly 40," not "at least 40." |
| 6 | What makes frontmatter invalid beyond a missing field or YAML syntax error — unknown fields, duplicate keys, custom tags, quoted numbers, repeated `archetypes` names? Must `archetypes` read back as a list? | All of those are invalid and fail the build: missing field, YAML syntax error, unknown field, duplicate key, custom YAML tag, a quoted/string `question` value, or a repeated name inside `archetypes`. `question` must read back as an int. `archetypes` must always read back as a list, even for a single-archetype file. |
| 7 | What does an exact body match require for encoding, line endings, blank lines after frontmatter, final newline? Is a whitespace-only body invalid? | UTF-8, body is everything after the closing `---`, line endings normalized to `\n`, leading/trailing whitespace trimmed before storing (so no stray leading blank line or trailing newline survives into the chunk). A whitespace-only body is invalid, same as an empty item in #2. |
| 8 | What should the query entry point return before the first successful build or when the store is unreadable? Should querying ever trigger a build? | Raises the same QueryError item #2 already raises for "no usable store," naming the problem. Querying never triggers a build — building and querying stay two separate operations, exactly as in item #2. |
| 9 | How should the query side identify the embedding model, and what counts as a mismatch if the name matches but revision/config differs? | Item #2 only compares the model name string, not a deeper revision/config fingerprint. This item inherits that same shallow check for consistency. |
| 10 | For the 500-character limit, does validation count before or after trimming, and how should it count emoji/combined characters? Should non-string input error the same way? | Validate on the raw string length before trimming, using plain `len()` (code points — same simple approach already implicit in #2's module, not grapheme-cluster-aware). Non-string input (e.g. `None`, a list) raises a clear error naming the received type, same pattern as elsewhere in that module. |

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
