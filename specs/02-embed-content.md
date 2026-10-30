# 02 - Embed the action-item content

**Story:** Enabler: As a developer, I can chunk and embed the existing action-item content library (4 styles × 3 tiers) into a vector store.

**Backlog item:** #2

**Status:** shipped

## What it does

Reads every action item from the `actions` lists in the `profiles` object of `networking-assessment.html` (repo `werkitgirls-resources`) as plain text, without running any of it: 4 styles × 3 tiers × 5 items = 60 items. Each item becomes one chunk with a source ID in the form `style-tier-position` (for example `connector-high-1`), saved with its style, tier, and text. The chunks are turned into numbers that capture their meaning (embeddings) by a small model that runs on this computer, and stored in a file-based vector store (Chroma) in `data/`. A query returns the 3 closest chunks. Every run rebuilds the store from scratch.

## What it does NOT do

- Change the quiz page. The HTML file is read as a source only (item 5 keeps it unchanged).
- Embed the style name, tagline, narrative, superpower, or growth text. Only action items are in scope.
- Rank chunks for a user's scores. That is item 3.
- Call TensorX or write any coaching text. That is item 4b.
- Store any user answers or personal data.
- Update the store item by item. A run replaces the whole store or leaves the old one untouched.

## Acceptance criteria

- [x] It's done when building from the real `networking-assessment.html` stores exactly 60 items, 5 for each of the 12 style-and-tier pairs, each with non-empty text and a unique source ID, and when the file has any other count, a missing style or tier, or an empty item, the run stops with an error naming the problem and stores nothing.
- [x] It's done when the text of every stored item matches the decoded text in `networking-assessment.html` exactly, checked by a test.
- [x] It's done when the vector store holds one embedding for each of the 60 items, and each can be looked up by its source ID.
- [x] It's done when a test query using each phrase in the table in Notes returns the listed item as the first result.
- [x] It's done when running the build twice leaves exactly the same 60 items with no leftover records, and a run that fails leaves the previous store unchanged.
- [x] It's done when an empty or whitespace-only query, and a query over 500 characters, each stop with a clear error, a valid query returns exactly 3 results, and a query embedded with a different model than the store's stops with an error naming both.
- [x] It's done when `python3 -m pytest` runs the tests for this item with no failures, with no internet or password needed after the model's first download.

## Question round

Where these questions came from: ChatGPT's question round on 2026-10-18, using the prompt in `docs/course/routine.md`, section 2. The answers are Sharon's decisions.

| # | Question | Answer |
|---|---|---|
| 1 | Which embedding service and model, and what if it fails partway? | A small model that runs on this computer, Chroma's built-in default (`all-MiniLM-L6-v2`). No password and no paid service. If any item fails to embed, the whole run stops with a clear error and nothing partial is saved. |
| 2 | What if the HTML has fewer or more than 60 items, missing styles or tiers, or empty items? | The run fails entirely with an error naming the problem. It requires 4 styles, 3 tiers each, 5 items each, and every item non-empty text. |
| 3 | Does "matches exactly" mean the decoded text or the literal source text? | The decoded text, which is what a visitor sees on the page. An escape like `\"` counts as the quote mark, so the Opportunity Seeker item containing "make connections" is stored with plain quote marks. Words and punctuation must match exactly. |
| 4 | How is `profiles` read without running hostile JavaScript, and what if the file is missing, broken, or has two `profiles`? | The file is read as plain text and the `profiles` data is parsed without running any of it. If the file is missing, malformed, or defines `profiles` more than once, the run stops with a clear error. |
| 5 | What happens when it runs twice, or after a run that stopped halfway? | Every run rebuilds the store from scratch. The new store is built separately and swapped in only when complete, so a half-finished run leaves the previous store untouched. |
| 6 | Are source IDs permanently tied to list positions? | Yes, for now. IDs are position-based (`connector-high-4`). If items are reordered or removed, the full rebuild regenerates all IDs and leaves no obsolete records. |
| 7 | Which file-based store, and do queries need the HTML? | Chroma, saved in `data/`. Queries read only the saved store and never the HTML. The same embedding model must build the store and embed queries. |
| 8 | What about empty, whitespace-only, very long, or no-match queries, and how many results? | Empty or whitespace-only queries return a clear error. Queries over 500 characters return a clear error. A valid query always returns the 3 closest items, even if the match is weak. |
| 9 | Which similarity measure and tie-breaker decide the first result, and what are the test phrases for the other styles? | Cosine similarity, with ties broken by source ID in alphabetical order. The four test phrases and expected IDs are in the table in Notes. |
| 10 | Do tests run offline, and what if stored embeddings came from a different model than the query's? | The model is downloaded once, the first time it runs, and that needs internet. After that, tests run offline with no password. If the stored embeddings and the query come from different models or sizes, the query stops with a clear error naming both. |

## Amendments

| Date | Change | Why |
|---|---|---|
| 2026-10-18 | Added question round rows 1 to 10, the four test phrases, and criteria for rebuilds and query rules. Removed the two open items from Notes (embedding service, data copy). | A second AI (ChatGPT) asked what the spec forgot, using the prompt from `docs/course/routine.md`, section 2. |

## Notes

- Source: `profiles.[style].actions.[high|mid|low]` in `networking-assessment.html`. All four styles have 5 items in each tier, 60 in total, confirmed 2026-10-19.
- Chunk size: one action item per chunk.
- Some items repeat across tiers. Two Opportunity Seeker items (high-2 with mid-3, and high-4 with mid-5) have identical text, and others are near-copies. Each stays its own chunk with its own ID. Item 3 may need to handle two identical results.
- The embedding model is local, because the TensorX model list shows no embedding model. TensorX is used only for writing the results (item 4b).

Test phrases (each appears in only one of the 60 items):

| Style | Phrase | Expected first result |
|---|---|---|
| Connector | "last 90 days" | `connector-high-4` |
| Cultivator | "write down one detail to remember" | `cultivator-low-4` |
| Opportunity Seeker | "head in your phone" | `opportunitySeeker-low-2` |
| Community Builder | "cross-functional project" | `communityBuilder-low-3` |