<!-- Course: Stage 1. Revise it whenever your thinking changes. A proposal that
     still says what you believed in September is not evidence of learning.
     See docs/course/DELIVERABLES.md -->

# Project proposal

**Project name:** Werk It Girls Networking Assessment — RAG Edition
**Author:** Sharon Mickelson
**Last updated:** September 18, 2026

---

## 1. The problem

Women navigating a career pivot or job search are told constantly to "network more," but almost none of them get told *how they, specifically, network well* — or what to do next given their own style. The current Werk It Girls self-assessment (live at tools.werkitgirls.com) sorts a user into one of four networking styles (Connector, Cultivator, Opportunity Seeker, Community Builder) using fixed scoring logic, then hands back one of a small set of pre-written action tiers. It works, but every person who scores "mid-tier Cultivator" gets the identical paragraph of advice, regardless of their actual answers within that tier.

That's the gap this project closes: a user who answers "Rarely" on networking follow-up but "Frequently" on event attendance has a different problem than someone with the opposite pattern — even if both land in the same overall tier. A static lookup table can't reflect that; a retrieval-augmented response, grounded in the same brand-approved content library, can.

## 2. Who uses this

**Primary user:** Women early-to-mid career, often mid-transition (job search, return-to-work, industry pivot), who land on tools.werkitgirls.com — typically from an Instagram post, the Werk It Girls podcast, or (post-launch) the Werk It Girls YouTube channel — looking for a quick, free read on their networking style.

**What they do today instead:** They default to generic "just network more" advice from career blogs, or they take the current static version of this assessment and get a useful but generic result. The apps they already have on their phone don't fill the gap: LinkedIn and Indeed are built to help someone *find* a job or a connection, not to help them understand or build the underlying skill of networking itself — and that gap matters more every year, as AI-written applications and easy-apply tools drive up competition for a shrinking pool of jobs, making a strong personal network less optional than it used to be.

**Why they'd switch:** The upgraded version keeps the same 3-minute, no-signup, no-cost experience the audience already trusts, but the feedback reads like it was written for *their* specific answers instead of a bucket they got sorted into — which matters a lot for a brand built on "professional, energetic, confident, direct" messaging that empowers rather than generalizes.

## 3. Tools and services

| What | Choice | Why this one |
|---|---|---|
| Track | python-tool (see docs/course/tracks.md) | My app needs to call an outside AI service to generate personalized coaching responses, and that service requires a private password (API key). A plain webpage — the kind that's only HTML and can sit on GitHub Pages — can't hide a password from anyone who looks at the page's code. python-tool is the option built to run on a real server, where that password stays hidden. |
| Language | Python | Required entry point for python-tool; needed for the retrieval-and-generation work and it's what the class is teaching. |
| How tests run | `pytest` | Standard for python-tool per tracks.md; keeps scoring logic (15-question, 60-point, 10/12-cluster threshold rules) regression-tested — this logic already has a documented history of subtle bugs (e.g., a misplaced action item, an off-by-one threshold). |
| Where it's hosted | Client-side quiz stays on GitHub Pages (tools.werkitgirls.com), unchanged and outside this repo; server-side backend (`app.py`) deployed on Streamlit Community Cloud | Matches the class's two-deployed-apps milestone directly: one static, one server-side — and matches tracks.md's hosting default for python-tool. |
| Data storage | Local file-based vector store in `data/` (e.g. a Chroma or FAISS index checked into the repo/rebuilt on deploy) for the retrieval content; no user data stored | Matches tracks.md's storage default for python-tool (files in `data/`); keeps the "ungated, no data collection" brand promise intact — the persistent storage requirement (W9) is satisfied by the knowledge base itself, not by capturing user answers. |
| Outside services (APIs) | TensorX | One of the class's listed alternative model providers; OpenAI-compatible endpoint already tested end-to-end and meets the class's required-model list. |

**Entry point:** `app.py` (Streamlit) · **Tests:** `pytest` · **Hosting:** Streamlit Community Cloud · **Storage:** files in `data/`

**What this rules out:** Choosing a file-based vector store instead of a hosted vector database (e.g. Pinecone) rules out real-time updates to the knowledge base from a separate admin tool — updating the content library means editing files and redeploying, not editing through a UI. That's an acceptable tradeoff for a project this size with one content owner. No front-end coding framework, and no passwords stored anywhere a visitor could see them. The client-side quiz stays exactly as it is; this repo's track only covers the new server-side piece that writes personalized responses.

**Scope note:** The build described here — quiz in, personalized written result out — is the full scope for the class deadlines. A freeform question feature (type in a specific situation, like "is it too late to follow up," and get a grounded answer) is a planned upgrade for after the core build is solid, since it reuses the same retrieval-and-generation pipeline rather than needing a separate one. It's tracked in `docs/backlog.md` under **Added later**, not in the build plan below.

## 4. Timeline

| Week | Features | Milestone |
|---|---|---|
| 5 | #1 (port scoring logic to Python with passing tests) | First test goes from red to green |
| 6 | #2, #3 (embed content library; wire similarity search) | |
| 7 | #4, #5, #6 (generate personalized results via TensorX; deploy client-side quiz unchanged; deploy Streamlit backend) | Two deployed apps live (client-side quiz + server-side RAG backend) |
| 8 | #12 (retrieval-quality regression tests), harden prompt for voice rules | Stage 2: prototype, two features working |
| 9 | #7 (confirm knowledge base survives restart/redeploy) | App keeps its data between restarts |
| 10 | #8 (setup instructions a stranger can follow) | Setup instructions a stranger can follow |
| 11 | #9 (alpha testing with real Werk It Girls audience members) | Stage 3: alpha, peer testing |
| 12–14 | #10, #11 (trace bad results to source chunks; graceful fallback on API failure); triage alpha feedback into backlog "Added later" | Feedback built in, tests updated |
| 15 | Final polish, demo prep, report | Stage 4: demo and report |

**Where I expect to get stuck:** The RAG layer itself — I have never built a retrieval pipeline (embeddings, chunking strategy, similarity search) before this class, so weeks 5–7 are the real risk window. My fallback if retrieval quality is poor by week 7: ship a hybrid version that still uses the existing tiered logic as a floor, with RAG-generated content layered on top rather than fully replacing it.

## 5. Setup instructions

The first draft lives in [`../README.md`](../README.md) under **Setup**, because
that's where a stranger will look for it. Write it there, not here.
