<!-- Course: Stage 2 (graded) and Stage 4 (feeds your final report). Several of
     the Friday lab milestones get recorded here. See docs/course/DELIVERABLES.md -->

# Development log

A running record of how this project got built and how AI was used to build it.

Add an entry when something notable happens: a feature ships, an assistant does
something surprising (well or badly), you get stuck, you change your approach.
Two or three sentences is plenty. Writing it as you go takes minutes; recon-
structing it in week 15 takes hours and the result is worse.

**Screenshots go in `assets/`** and get linked from the relevant entry.

---

## Pre-port debugging (werkitgirls-resources)
Before porting scoring logic to Python (item #1), found and fixed a bug in the live tool: a missing DOM reset in showResults() let action items pile up across retakes without a page reload, producing misleading results. Fixed and changelogged in werkitgirls-resources (separate repo) on 2026-09-27 — see that repo's CHANGELOG.md for the full fix. Confirms the reference scoring behavior used for item #1's test fixtures is the corrected version, not the buggy one.
## Template for an entry

### YYYY-MM-DD - Short title

**What happened:**
**AI tools used, and for what:**
**What surprised me:**

---

## Lab milestones

Check these off as you hit them, and link to the entry or screenshot.

- [ ] **Task list + red tests**: first tests written and failing
- [ ] **First green**: a test flips from red to green on your own project
- [ ] **Sabotage**: you broke your own app on purpose and confirmed the tests caught it
- [ ] **Real API call**: your app talks to an outside service
- [ ] **Bug reports filed**: on a classmate's prototype
- [ ] **README v1**: a classmate ran your app from your setup steps
- [ ] **User-test notes**: recorded in [feedback-log.md](feedback-log.md)
- [ ] **Criteria v2 + review report**: acceptance criteria revised after real feedback

---

## Entries

<!-- Newest first. -->

### YYYY-MM-DD

**What happened:**

**AI tools used, and for what:**

**What surprised me:**
