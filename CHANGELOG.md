<!-- Course: first required in Stage 3 (alpha). Stage 4 grades your documentation
     of what changed between alpha and final. This file is that documentation.
     See docs/course/DELIVERABLES.md -->

# Changelog

Every notable change to this project. Newest first.

Add a line here whenever you merge a feature. It takes ten seconds now and saves
you an hour of archaeology when you write your final report.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- Item 4a: retrieves the right philosophy, archetype, and behavior chunks for a user's score
  result from the #2b content-library store — philosophy_blend always, both archetype chunks
  for the winning style, and 3 behavior chunks filtered by style and tier-derived mode then
  ranked by the user's full score pattern — built through the full routine with 6 review
  findings fixed along the way (a broken .gitignore pattern that could have let local tooling
  files get committed, a store-version consistency gap where a rebuild mid-request could mix
  chunks from two different published versions, raw exceptions escaping instead of QueryError
  for store/model failures, a personalization test that only ran against the real library,
  a tie-break test that passed even with the tie-break logic removed, and error-handling
  tests that only covered failures before the store opens, not after).

### Added
- Item 2b: the new four-layer content library (philosophy, archetype, behavior — 40 files in
  knowledge_base/) is chunked and embedded into its own vector store, separate from item #2's
  action_items store, built through the full routine with 7 review findings fixed along the
  way (fixed a filename-parsing bug that broke real behavior files, closed a destination-
  collision risk that could have let a build overwrite or delete an unrelated store like
  action_items, closed a gap in the atomic store swap where a reader could briefly see no
  store at all, enforced the spec's exact taxonomy instead of deriving valid values from
  input, closed a symlink swap-in window between the file check and the read, converted raw
  type errors on malformed input into clear BuildError messages, and hardened store-opening
  to raise a clear error instead of silently creating a directory or leaking an internal
  exception).

### Added
- Item 3: similarity search against the embedded content narrows results to a user's winning style/tier bucket before ranking by their full four-style score pattern, returning exactly 3 chunks each with a source ID — built through the full routine on PR #9 with 6 review findings fixed along the way (range-checked style totals to prevent a crash, stopped echoing attacker-supplied key names into error messages, named the received type for an invalid style/tier value, removed an unauthorized n_results parameter, strengthened tests to prove exact nearest-match ordering and tie-break correctness, and isolated per-total phrase sensitivity), plus one known limitation documented (tests skip without the real content library, same tradeoff item #2 already shipped with).

### Added
- Item 2a: the quiz screen now shows a title and subtitle, a progress indicator tracking how many of the 15 questions are answered, and labeled result text ("Your networking style: ___" / "Your tier: ___") with a fixed "coming soon" line below it — built through the full routine on PR #8 with 4 review findings fixed along the way (progress tested question-by-question instead of in batches, a check added for silent app errors, the result screen checked for exactly the three expected lines with nothing left over, and a flawed self-comparing test rewritten to use two genuinely different results).

### Added
- Item 2: the 60 action items are chunked and embedded into a local vector store (Chroma), built through the full routine on PR #2 with 5 review findings fixed along the way (atomic store replacement so a failed rebuild can't corrupt the previous store, strict typed parsing that rejects hostile/malformed input, rejection of unexpected styles/tiers, alphabetical tie-breaking for equal-distance query results).

### Added
- Item 18b: the scorer now rejects invalid input with a clear error. It accepts only exactly 15 whole numbers from 1 to 4, and every error names the type received but never the value. Valid input is scored exactly as before.

### Added
- Item 18a: a Streamlit quiz screen (app.py) where users answer all 15 networking-style questions and see their style and tier. Submit stays disabled until every question is answered, and Retake fully resets the page back to a blank state.

### Added
- Scoring port to Python with 41 passing tests, built through the full routine on PR #1.
- <!-- new features -->

### Changed
- <!-- changes to features that already existed -->

### Fixed
- <!-- bug fixes -->

### Removed
- <!-- features you took out, and one clause on why -->

---

## [0.1.0] - Alpha - YYYY-MM-DD

The version your classmates tested in Stage 3.

### Added
- <!-- everything that worked at alpha -->

### Known issues
- <!-- what was broken or missing, honestly. Alpha users need this. -->
