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
