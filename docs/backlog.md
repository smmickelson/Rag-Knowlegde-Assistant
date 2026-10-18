<!-- Course: Stage 1, then revised all semester. Graded again in Stage 3 and
     Stage 4: how it CHANGED is the evidence, not whether it stayed the same.
     See docs/course/DELIVERABLES.md -->

# Backlog

Every feature, in the order it gets built. **#1 is what gets built first.**

Each item is one user story plus acceptance criteria that someone else could test
without asking you anything.

> **If you can't say how you'd test it, it isn't ready to be on this list yet.**
> Move it to *Not ready* at the bottom and come back to it.

## How to read this

| Column | Means |
|---|---|
| **#** | Build order. Also the spec filename and the branch name. |
| **Story** | As a [user], I can [do X]. |
| **Acceptance criteria** | Something observable. A stranger could confirm it. Write each as "It's done when ___". |
| **Status** | not started / spec written / tests written / built / shipped |

---

## To build

| # | Story | Acceptance criteria | Status |
|---|---|---|---|
| 1 | Enabler: As a developer, I can run the existing 15-question scoring logic in Python with passing tests, so scoring behavior is preserved before I build anything on top of it. | It's done when all 10 answer sets in tests/fixtures/known_answers.json score exactly as listed, and `python3 -m pytest tests/test_scoring.py` passes with no failures. (Revised 2026-10-12: the flat four-style model is ported first and the cluster layer is deferred, see specs/01-scoring-port.md and the cluster row under Added later.) | shipped |
| 2 | Enabler: As a developer, I can chunk and embed the existing action-item content library (4 styles × 3 tiers) into a vector store. | It's done when every action-tier text block is embedded and stored, and a test query returns the correct source chunk for a known keyword. | not started |
| 3 | Enabler: As a developer, I can run a similarity search against the embedded content and get back the most relevant chunks for a given user's cluster scores. | It's done when, for each of the 5 sample answer sets listed in this item's spec, the top-3 retrieved chunks include the chunk for that user's top style and tier. | not started |
| 4a | Enabler: As the system, I retrieve relevant content chunks for a given style result. | It's done when, for each of the four styles, retrieval returns at least 3 chunks, each carrying a source ID. | not started |
| 4b | **As a user,** I complete the assessment and receive a written result generated via TensorX from the retrieved chunks. | It's done when 3 test runs per style (12 total) each return a non-empty result that names the user's style and includes at least one next step traceable to a retrieved chunk ID. | not started |
| 4c | Enabler: As the content author, I maintain one off-brand phrase list that applies to all four styles. | It's done when `docs/off-brand-phrases.md` exists, contains the two banned words plus at least 5 off-brand phrases, and the 4d test reads its list from that file. | not started |
| 4d | **As a user,** my result is written in Werk It Girls brand voice. | It's done when all 12 test results from 4b contain none of the phrases in `docs/off-brand-phrases.md`, checked by string match. | not started |
| 5 | **As a user,** I can access the client-side quiz at tools.werkitgirls.com exactly as I do today, with no visible change to the intake experience. | It's done when the existing GitHub Pages quiz is redeployed unchanged and passes a manual click-through with no console errors. | not started |
| 6 | Enabler: As a developer, I can get the server-side RAG result delivered without the client-side page exposing scoring logic in its source. | It's done when the server-side Streamlit app is live at a public URL, accepts quiz answers, and returns the generated result without the browser exposing the scoring code. | not started |
| 7 | Enabler: As a developer, I can restart or redeploy the backend and have the knowledge base still there without regenerating it from scratch. | It's done when killing and restarting the Streamlit process still serves correct retrieval results without re-running the embedding step. | not started |
| 8 | **As a tester,** I can follow the README setup instructions on a clean machine and get the app running without asking Sharon anything. | It's done when a classmate follows the README top to bottom and successfully runs both apps locally without outside help. | not started |
| 9 | **As an alpha tester,** I can complete the assessment and leave feedback on whether the result felt accurate and useful. | It's done when at least 5 alpha testers complete the quiz and submit feedback via a simple form/link, logged in feedback-log.md. | not started |
| 10 | Enabler: As a developer, I can see which retrieved chunks led to a given result, so I can trace a bad result instead of guessing. | It's done when each generated result logs (server-side only, not user-facing) the source chunk IDs it was grounded in. | not started |
| 11 | **As a user,** I can still see my networking style result if the RAG/LLM call fails, via a graceful fallback to the original static tier text. | It's done when simulating an API failure (bad key, timeout) still returns the pre-written static tier text instead of an error page. | not started |
| 12 | Enabler: As a developer, I can catch a content-library edit that silently breaks retrieval quality for one or more styles. | It's done when the test suite includes at least one retrieval-quality check per style, and CI fails if a content edit breaks the check for any style. | not started |

<!-- Aim for 8-15 across the semester. Fewer than 8 is probably too little;
     more than 15 usually means individual items are too big. -->

## Added later 
<!-- Things that came out of user testing in Stage 3 and got the answer
     "yes, but later." Put them in position, with a note saying where they came
     from, so the reason survives. -->

| # | Story | Acceptance criteria | Where it came from |
|---|---|---|---|
| 13 | Enabler: As a developer, I can expand the content library beyond the four-style/three-tier action items to include situational coaching material — real questions about things like follow-up timing, reconnecting after time has passed, and asking for an informational interview — so retrieval has something to draw on for open-ended questions, not just quiz results. | It's done when the content library includes sourced material addressing at least 8 distinct situational questions, each tagged so it can be retrieved on its own, independent of a user's cluster scores. | Deferred after deciding the quiz-only build already delivers real granularity on its own (personalized results per answer pattern, not just per tier) — the question layer is a planned v2 upgrade, added once the core build is solid, not required for the class deadlines. |
| 14 | **As a user,** I can type a specific networking situation — for example, "I hit it off with a speaker at a panel and it's been three weeks, is it too late to follow up, what should I do?" — and get a personalized answer grounded in the content library, in Werk It Girls brand voice. | It's done when test runs against a checklist of realistic questions (the panel example, plus at least 5 more: reconnecting with someone you've lost touch with; whether a LinkedIn note is enough or an email is needed; what to do after being ghosted post-conversation; how soon is too soon to ask for an informational interview; how to recover after saying you'd follow up and then not doing it for weeks) each produce a response with no banned words, an empowering tone, and content traceable to a retrieved source chunk. | Same as #13 — reuses the vector store, retrieval, and TensorX call already built for the quiz result, so it's a clean upgrade rather than a rebuild. |
| 15 | **As a user,** if I ask something outside networking, I get a clear, kind redirect instead of a made-up answer, so the tool stays inside what it's actually built and tested for. | It's done when at least 3 out-of-scope test questions each return the same redirect message rather than a generated answer, and this behavior is covered by a test. | Guardrail for #14 — only needed once the question layer itself is built. |
| 16 | Enabler: As a developer, I can see that the tier rule (below 12 is low, 12 to 19 is mid, 20 or more is high) holds for the winning total of every style, so a boundary mistake in any one style gets caught. | It's done when, for each of the four styles, tests exist where that style wins with exactly 11 (low), 12 (mid), 19 (mid), and 20 (high), and all 16 pass. | Gap found in the 2026-10-12 test review: tier boundaries are tested only through Cultivator. Deferred because criterion 4 in specs/01-scoring-port.md is about the winning total, not any one style, the fixtures already show other styles in low, mid, and high, and hand-building boundary answer sets is error-prone where questions count toward more than one style. |
| 17 | Enabler: As a developer, I can see that each question's answer moves exactly the style totals it should, so a question assigned to the wrong style gets caught. | It's done when, for each of the 15 questions, a test raises that one answer from 1 to 2 with every other answer at 1 and confirms that only the styles listed for that question in specs/01-scoring-port.md rise by 1 while the others stay at 6. | Gap found in the 2026-10-12 test review. Deferred because the spec does not require it, and the fixtures catch many wrong assignments, though some could slip through where questions share identical answers. |
| 18a | **As a user taking the quiz,** I cannot submit until all 15 questions are answered, and each question only offers the answers 1 to 4. | It's done when the submit control stays disabled until 15 answers are chosen, no question starts with an answer selected, and a test covers each of those. | Deferred from item #1, whose scoring function deliberately does no input validation (specs/01-scoring-port.md, question round answers 7, 11, and 14). The security review (Agent 2, PR #1) raised that booleans and oversized lists pass through unchecked; deciding where validation lives (the quiz screen limiting choices, or the scoring layer rejecting bad input) is part of this item. |
| 18b | Enabler: As a developer, I get a clear error when the scorer receives anything other than exactly 15 whole numbers from 1 to 4. | It's done when rejected cases (too short, too long, non-numbers, decimals, booleans, out-of-range numbers) each raise a clear error with a test per case. | Deferred from item #1, whose scoring function deliberately does no input validation (specs/01-scoring-port.md, question round answers 7, 11, and 14). The security review (Agent 2, PR #1) raised the unchecked booleans point here; capping the size of incoming requests is a deployment concern for a later item, not the scorer. |
| — | Fixed a live-tool bug (action items accumulating across retakes) found while establishing ground truth for item #1's fixtures. | Confirmed via clean vs. dirty retake comparison; fix committed and changelogged in werkitgirls-resources 2026-09-27, not tracked as a build item here. | Discovered during pre-port testing |
| — | **As a user,** I can see cluster-level detail behind my networking style (e.g., which specific pattern is driving my score), so my coaching feels more precisely tailored. | Not yet defined — scoring function would need to return cluster subtotals alongside style/tier, and the actual 15-question-to-cluster mapping still needs to be designed from scratch (no working implementation of the cluster model was found anywhere in the repo's history). | Design discussion while building item #1 — original cluster-based design doc exists, but was deliberately deferred in favor of shipping the simpler flat model first. |