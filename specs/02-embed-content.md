# 02 - Embed the action-item content

**Story:** Enabler: As a developer, I can chunk and embed the existing action-item content library (4 styles × 3 tiers) into a vector store.
**Backlog item:** #2
**Status:** drafted

## What it does

Reads every action item from the `actions` lists in the `profiles` object of `networking-assessment.html` (repo `werkitgirls-resources`): 4 styles × 3 tiers × 5 items = 60 items. Each item becomes one chunk with a source ID in the form `style-tier-position` (for example `connector-high-1`), saved with its style, tier, and text. The chunks are turned into numbers that capture their meaning (embeddings) and stored in a file-based vector store in `data/`. A test query can then return the matching chunk.

## What it does NOT do

- Change the quiz page. The HTML file is read as a source only (item 5 keeps it unchanged).
- Embed the style name, tagline, narrative, superpower, or growth text. Only action items are in scope.
- Rank chunks for a user's scores. That is item 3.
- Call TensorX or write any coaching text. That is item 4b.
- Store any user answers or personal data.

## Acceptance criteria

- [ ] It's done when `data/` holds exactly 60 action items, 5 for each of the 12 style-and-tier pairs, each with a non-empty text and a unique source ID.
- [ ] It's done when the text of every item matches the text in `networking-assessment.html` exactly, checked by a test.
- [ ] It's done when the vector store contains one stored embedding for each of the 60 items, and each can be looked up by its source ID.
- [ ] It's done when a test query using a phrase from one item ("last 90 days" returns `connector-high-4`) returns that item as the first result. One such phrase per style is listed in Notes.
- [ ] It's done when `python3 -m pytest` runs the tests for this item with no failures.

## Question round

(Left empty for the second AI.)

## Amendments

| Date | Change | Why |
|---|---|---|

## Notes

- Source: `profiles.[style].actions.[high|mid|low]` in `networking-assessment.html`. Counts assumed from the Connector block and still to be confirmed for the other three styles.
- Chunk size: one action item per chunk (recommended; open to challenge in the question round).
- Distinctive test phrases: Connector, "last 90 days" (high, item 4). Cultivator, Opportunity Seeker, and Community Builder phrases to be added after checking that each is unique across all 60 items.
- Open for the question round: which service creates the embeddings, and whether the content is copied into `data/` or read from the HTML each time.