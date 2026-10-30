<!-- Course: Stage 1. Revise it whenever your thinking changes. A proposal that
     still says what you believed in September is not evidence of learning.
     See docs/course/DELIVERABLES.md -->

# Project proposal

**Project name:** Werk It Girls Networking Assessment — RAG Edition
**Author:** Sharon Mickelson

**Last updated:** October 21, 2026 (first version: September 18, 2026; see "What changed since September" at the bottom)

---

## 1. The problem

Women navigating a career pivot or job search are told constantly to "network more," but almost none of them get told *how they, specifically, network well* — or what to do next given their own style. The current Werk It Girls self-assessment (live at tools.werkitgirls.com) sorts a user into one of four networking styles (Connector, Cultivator, Opportunity Seeker, Community Builder) using fixed scoring rules, then hands back one of a small set of pre-written action tiers (low, mid, or high). It works, but every person who scores "mid-tier Cultivator" gets the identical paragraph of advice, regardless of their actual answers within that tier.

That's the gap this project closes: a user who answers "Rarely" on networking follow-up but "Frequently" on event attendance has a different problem than someone with the opposite pattern, even if both land in the same style and tier. A fixed lookup table can't reflect that. A tool that looks up material I've already written, picks the pieces that match each person's answers, and then writes a result from them, can.

**How I'll know it worked:** two test users who land in the same style and tier but answered the 15 questions differently receive different next steps, and each next step can be traced to a specific piece of my content library. Every result is also free of the off-brand phrases listed in `docs/off-brand-phrases.md`.

### How personalization will work, in plain words

The scoring stays plain arithmetic, because it has to give the same answer every time and the tests depend on that. What moves away from fixed rules is the advice: my own writing supplies what to say, and the AI service decides how the right pieces fit together for each person.

1. The quiz scores the 15 answers into four style totals. The highest total names the user's style, and its size sets the tier (below 12 is low, 12 to 19 is mid, 20 or more is high).
2. Each of the 15 questions describes one networking habit. An answer of 1 or 2 marks that habit as a gap, a 4 marks it as a strength, and a 3 is neutral. This is checked across all 15 questions, not only the winning style's, because my goal for every user is a blend of the four styles.
3. My content library is written at the habit level. For each of the 15 habits there are two short pieces in my voice, one on building the habit and one on using it. Alongside them sit short pieces on each style (who you are, your strengths, your growth advice) and a small always-included piece on my networking philosophy and the blend goal. Every piece is written to "you," makes sense on its own, and stays under about 150 words.
4. The app describes the user in a few plain sentences (her style, her tier, her gaps and strengths) and looks up the pieces that best match. If she has many gaps, a fixed rule keeps the list to a set number (lowest answer first, then question number), so the same answers always give the same result. If she has no gaps, she gets the style pieces with her strengths in front.
5. The AI service writes the result in Werk It Girls voice using only those pieces, and every next step carries the ID of the piece it came from.

The finer-grained "cluster" scoring from the original design is deferred (it is parked under *Not ready* in the backlog). Personalization comes from steps 2 to 4, not from clusters.

## 2. Who uses this

**Primary user:** Women early-to-mid career, often mid-transition (job search, return-to-work, industry pivot), who land on tools.werkitgirls.com, typically from an Instagram post, the Werk It Girls podcast, or (post-launch) the Werk It Girls YouTube channel, looking for a quick, free read on their networking style.

**What they do today instead:** They default to generic "network more" advice from career blogs, or they take the current static version of this assessment and get a useful but generic result. The apps they already have on their phone don't fill the gap: LinkedIn and Indeed are built to help someone *find* a job or a connection, not to help them understand or build the underlying skill of networking itself. That gap matters more as AI-written applications and easy-apply tools raise the competition for every opening, which makes a strong personal network less optional than it used to be.

**Why they'd switch:** The upgraded version keeps the same 3-minute, no-signup, no-cost experience the audience already trusts, but the feedback reads like it was written for *their* specific answers instead of a bucket they got sorted into, which matters for a brand built on "professional, energetic, confident, direct" messaging that empowers rather than generalizes.

**Brand promise that shapes the build:** the tool never stores quiz answers, emails, or personal data. Server logs keep source content IDs only. Feedback from alpha testers comes through a separate, optional form and holds only what a tester chooses to type.

## 3. Tools and services

| What | Choice | Why this one |
|---|---|---|
| Track | python-tool (see docs/course/tracks.md) | My app needs to call an outside AI service to generate personalized coaching responses, and that service requires a private password (API key). A plain webpage — the kind that's only HTML and can sit on GitHub Pages — can't hide a password from anyone who looks at the page's code. python-tool is the option built to run on a real server, where that password stays hidden. |
| Language | Python | Required entry point for python-tool; needed for the retrieval-and-generation work and it's what the class is teaching. |
| How tests run | `pytest` | Standard for python-tool per tracks.md; keeps scoring logic (15-question, 60-point, 10/12-cluster threshold rules) regression-tested — this logic already has a documented history of subtle bugs (e.g., a misplaced action item, an off-by-one threshold). |
| Where it's hosted | Client-side quiz stays on GitHub Pages (tools.werkitgirls.com), unchanged and outside this repo; server-side backend (`app.py`) deployed on Streamlit Community Cloud | Matches the class's two-deployed-apps milestone directly: one static, one server-side — and matches tracks.md's hosting default for python-tool. |
| Data storage | Local file-based vector store in `data/` (e.g. a Chroma or FAISS index checked into the repo/rebuilt on deploy) for the retrieval content; no user data stored | Matches tracks.md's storage default for python-tool (files in `data/`); keeps the "ungated, no data collection" brand promise intact — the persistent storage requirement (W9) is satisfied by the knowledge base itself, not by capturing user answers. |
| Outside services (APIs) | TensorX | One of the class's listed alternative model providers; OpenAI-compatible endpoint already tested end-to-end and meets the class's required-model list. |
| Embedding model | Chroma's built-in `all-MiniLM-L6-v2`, run locally | TensorX has no embedding model listed, and a local model needs no key. |
| App framework | Streamlit | It turns a Python script into a web page without front-end coding, and it is the framework python-tool and its hosting default are built around. |
| Automatic test runs | GitHub Actions | It runs the tests on every pull request (draft ones excluded), so a content edit that quietly breaks results gets caught before it merges. |
| Alpha feedback | A Google Form linked from the app, with every response copied word for word into `docs/feedback-log.md` | It is free and needs no code or hosting, and because it sits outside the app, quiz answers are never collected. |
| AI coding assistants | DeepSeek in Kilo builds the code, ChatGPT runs the question round and reviews, and Claude drafts specs and writes tests | Splitting the roles matches the course routine, where the builder never touches the tests it has to pass. |

**Entry point:** `app.py` (Streamlit) · **Tests:** `pytest` · **Hosting:** Streamlit Community Cloud · **Storage:** files in `data/`

**What this rules out:** Choosing a file-based content store instead of a hosted one (like Pinecone) rules out updating the content library from a separate admin screen. Updating content means editing files and redeploying, which is acceptable for a project this size with one content owner. There is no front-end coding framework, and no keys or passwords stored anywhere a visitor could see them. The client-side quiz stays exactly as it is; this repo covers only the new server-side piece that writes personalized results.

**Rules for keeping the tools in step:** the content store has to be built and searched with the same embedding model, so if the model ever changes, the store is rebuilt. Chroma and the other key packages are pinned to exact versions in `requirements.txt`, so my laptop, the automatic tests, and the deployed app all load the same store the same way.

**Outside dependency:** the quiz page lives in a separate repo (`werkitgirls-resources`). Backlog item 5 redeploys it unchanged, and the README setup covers this repo only. Anything the class counts as "both apps running" depends on that page staying as it is.

**Scope note:** The build described here (quiz in, personalized written result out) is the full scope for the class deadlines. A freeform question feature (type in a specific situation like "is it too late to follow up?" and get a grounded answer) is a planned upgrade for after the core build is solid, since it reuses the same lookup-and-write pipeline. It is tracked in `docs/backlog.md` under **Added later**, not in the build plan below.

## 4. Timeline

Dates are the week each piece starts. Backlog numbers are the build order, with the changes explained under the table.

| Week of | Features | Milestone |
|---|---|---|
| Oct 12 | #1 Scoring logic ported to Python, tests passing (shipped Oct 12) | First feature through the full routine |
| Oct 19 | #18b The scorer gives a clear error for anything other than 15 whole numbers from 1 to 4 (spec, question round, failing tests, `approved`); split my existing style write-ups into short, self-contained pieces | |
| Oct 26 | #18b built, reviewed, merged; test deployment of Chroma on Streamlit Community Cloud; start writing the habit-level pieces (30 in all) | **Stage 2 due Oct 30:** two features through the full routine (#1 and #18b), evidence on the pull requests |
| Nov 2 | #2a Content library finished as short habit-level pieces; #2 Embed the content library; #3 and #4a Similarity search and retrieval for a user's style, tier, and flagged habits | |
| Nov 9 | #4b Written result via TensorX; #4c and #4d Off-brand phrase list and brand voice check; #6 Backend deployed | Alpha live, testers invited |
| Nov 16 | #5 Quiz redeployed unchanged; #18a Quiz screen limits answers to 1 to 4; #8 README tested on a classmate; #9 Alpha feedback collected; 0.1.0 changelog entry | **Stage 3 due Nov 20:** alpha with feedback from testers |
| Nov 23 | #11 Fallback to static text if the AI call fails; start sorting feedback into decisions | Thanksgiving week: lighter load |
| Nov 30 | #7 Restart keeps the content store; #10 Log source IDs server-side; #12 Retrieval-quality checks; feedback decisions turned into revised acceptance criteria and updated tests | Feedback built in, tests updated |
| Dec 7 | Final polish, demo prep (including sabotage-round practice), report | |
| Dec 14 | Final report and demo | **Stage 4 due Dec 16** |

**Changes from September:**
- #18b moved forward to be my second Stage 2 feature. It needs none of the search or deployment work, so my most uncertain work stays off the Oct 30 deadline. My instructor confirmed that features do not have to be customer-facing.
- #2a is a new item for writing the content library as habit-level pieces. It replaces the plan to embed the existing four-style, three-tier action text as it stood.
- #3 and #4a are combined, and so are #4c and #4d, because each pair tests one thing from two sides. The backlog is renumbered to match.
- #12 moved from week 8 to the end, because its checks need a working pipeline to test. #11 moved ahead of #10, because the fallback is the safety net for the whole alpha.
- #4b returns source IDs with each result from the start, so tracing a result to its content does not wait for #10, which only adds server-side logging.
- #7 moved later. With the built store committed to the repo, a restart should already load it, so #7 may need only a confirming test.

**What slipped and why:** the September plan had #2 and #3 done by week 6. The scoring port (#1) took longer than planned because I was learning the routine, it needed a full question round and test review, and I chose to ship the simple four-style model before building anything on top of it.

**Where I expect to get stuck:** the lookup layer. I had never built embeddings, content splitting, or similarity search before this class, and the week of Nov 9 is overloaded (three items plus a deployment). Two specific risks have plans:
- **Chroma on Streamlit Community Cloud.** Chroma needs a newer SQLite than the cloud machine provides, and the usual fix is a small package (`pysqlite3-binary`) plus three lines at the top of `app.py`. I will test this the week of Oct 26 with a tiny page and three sample pieces, not on deploy day. If the fix fails there, I switch to a plain saved file of vectors searched in a few lines of Python, and I do not lose a week finding out in November.
- **First-load time.** The embedding model downloads the first time it runs, so the first visit to the deployed app and the first automatic test run will be slow. I will time the first load in the same test deployment.

If I am behind on Nov 9, I cut in this order: #12, then #10, then #5. I do not cut #11. If retrieval quality is still poor by Nov 9, I ship the hybrid: the existing tiered text as the floor, with generated content layered on top rather than replacing it. Writing the 30 habit-level pieces in my voice is also real work; if it runs long, I write the pieces for each style's own habits first and fill in the rest as the alpha shows which ones matter.

## 5. Setup instructions

The first draft lives in [`../README.md`](../README.md) under **Setup**, because
that's where a stranger will look for it. Write it there, not here.

---

## What changed since September

- **Scoring model:** the plan said 15 questions, 60 points, and 10/12 cluster thresholds. On Oct 12 I ported the simpler four-style model first and deferred the cluster layer. Tiers now follow the winning style total (below 12 low, 12 to 19 mid, 20 or more high).
- **Personalization:** the September plan assumed answers within a tier would drive the result but did not say how. Section 1 now spells out the mechanism: the 15 habits flag gaps and strengths, and my content is rewritten at the habit level so there is something specific to look up.
- **Tools:** added the framework, automatic test runs, embeddings, feedback form, and AI assistants. Picked Chroma over FAISS because it stores labels with each piece and can filter on them, which my design needs. Picked Chroma's built-in local embedding model over a TensorX embedding call so the tests need no secrets and each search has no extra network call to fail.
- **Timeline:** rebuilt around the real due dates (Oct 30, Nov 20, Dec 16), with the reorder and the slip explained. #18b is now my second Stage 2 feature.
- **Risks:** named the Chroma and Streamlit Community Cloud SQLite issue and the model download time, each with an early test and a fallback.
- **Privacy:** the no-data promise now says what logs and the feedback form do and do not hold.
