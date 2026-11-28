# Spec 20: Bring content_library text in line with the live HTML tool

## Problem

The Streamlit app's personalized results pull their text from markdown 
files in content_library/. Two parts of that content fall short of the 
bar set by the original, already-tested assessment at tools.werkitgirls.com 
(source: werkitgirls-resources/networking-assessment.html):

1. **Action-plan items.** 14 of the 15 unique "using"-mode behavior files 
   are reflection-only -- an affirming statement with no concrete task. 
   Only one (q15_grow_network_intentionally_using.md) already pairs a 
   reflection with a specific, time-bound action. The live HTML's action 
   items, by contrast, consistently give a concrete task with an explicit 
   timeframe ("this week," "this month," "today").

2. **Superpower / growth-opportunity text.** The content_library archetype 
   identity/strengths files run roughly 60-90 words (3-4 sentences). The 
   live HTML's equivalent text is a single sentence each, roughly 10-20 
   words. Testers flagged the Streamlit version as too long to read 
   closely during alpha testing (see docs/feedback-log.md, comments 3 
   and 5).

This is a text-only, placeholder fix: it reuses wording that's already 
been tested and works, as a stand-in until a planned future phase 
develops fully personalized, original writing for this content.

Note: this item shares a topic area with existing backlog item #19 
(an enabler for catching future content-library regressions in CI), 
but is a different, unrelated fix -- #19 stays deferred as-is.

## What it does

Replaces the body text of 22 files in content_library/ with text drawn 
from (or closely adapted from) the live HTML tool. No file is renamed, 
no frontmatter tag changes (archetype/archetypes, layer, question, 
slug, mode all stay exactly as they are), no retrieval or scoring logic 
changes, no app.py changes.

The text below is final, approved copy -- do not reword or "improve" 
any of it during the build. If something looks like it doesn't fit, 
flag it instead of changing it.

### Action-plan files (14 of 15; q15 is already correct and untouched)

Cultivator-only files (6):
- q07_follow_up_gratitude_using.md -> "Think about who in your network 
  has been quietly showing up for you. Send them a genuine and specific 
  thank-you this week."
- q02_share_updates_using.md -> "You invest in people -- make sure that 
  investment is visible. Share a win or insight with your network this 
  week."
- q12_reintroduce_yourself_using.md -> "You already reintroduce 
  yourself, which keeps people at ease -- do it on purpose. This week, 
  reintroduce yourself to one person you're fairly sure already 
  remembers you, just to keep that habit visible."
- q09_respond_promptly_using.md -> "Your responsiveness is already a 
  strength people notice and rely on -- keep it going. Starting today, 
  reply to every message within 24 hours; begin with the very next one 
  you get."
- q05_remember_details_using.md -> "You already remember the details 
  that make people feel valued -- put one to use this week. Bring up 
  something specific someone told you a while back; it's a small thing 
  that lands big."
- q01_introduce_yourself_using.md -> "You already introduce yourself 
  with ease -- put that same clarity to work for someone else. This 
  week, think of one person you could introduce to someone new, just 
  as clearly as you'd introduce yourself."

Shared files (8; tagged to 2 styles each -- q15 excluded, already correct):
- q04_connect_others_using.md -> "Your introductions are already 
  creating connections -- this week, make one more, then follow up with 
  both people a week later to see how it landed and close the loop."
- q10_support_others_networks_using.md -> "You already have a strong 
  connector instinct -- this week, put it to use looking backward as 
  well as forward. Document who you've introduced in the last 90 days 
  and what came of it, then use that to sharpen your next move."
- q14_ask_for_support_using.md -> "You give generously -- make sure 
  you're also receiving. Reach out to someone this week and ask for 
  their perspective on something you're working through."
- q06_attend_events_using.md -> "You already show up well -- the 
  follow-up is where it pays off. The next time you're at an event or 
  meeting, send a personal follow-up within 48 hours and reference 
  something specific you discussed."
- q11_engage_social_events_using.md -> "You already notice who's 
  sitting on the edges of a room -- use that this week. Identify one 
  person who tends to stay on the edges and personally invite them into 
  a conversation the next time you're both at an event or in a 
  meeting."
- q03_participate_in_orgs_using.md -> "You're already active in 
  organizations that matter to you -- the next move is depth, not 
  breadth. This month, take on one small, visible role in one you're 
  already part of."
- q08_expand_diverse_network_using.md -> "You're already comfortable 
  branching out -- go one step further. This week, think of one person 
  in your network who could benefit from meeting someone completely 
  outside their usual circles, and make that connection."
- q13_volunteer_cross_functional_using.md -> "You already step up for 
  cross-functional work -- notice who you meet through it. This week, 
  follow up individually with one or two people from a recent project - 
  outside the project itself."

### Superpower / growth-opportunity files (8)

- archetype_connector_identity.md (superpower) -> "Creating value for 
  others without keeping score. You're the person people think of when 
  they say 'you have to meet so-and-so.'"
- archetype_connector_strengths.md (growth) -> "Slowing down to deepen 
  the connections you already have, so your network has roots -- not 
  just reach."
- archetype_cultivator_identity.md (superpower) -> "Loyalty and 
  authenticity. People don't just know you -- they count on you."
- archetype_cultivator_strengths.md (growth) -> "Expanding your circle 
  so that your influence reaches as far as your impact. The depth is 
  there -- now stretch the width."
- archetype_opportunity_seeker_identity.md (superpower) -> "Strategic 
  visibility and initiative. You put yourself in rooms where things 
  happen."
- archetype_opportunity_seeker_strengths.md (growth) -> "Making sure 
  people experience your genuine curiosity, not just your agenda -- so 
  relationships outlast the opportunity that started them."
- archetype_community_builder_identity.md (superpower) -> "Creating 
  belonging. People feel seen and included around you."
- archetype_community_builder_strengths.md (growth) -> "Investing in 
  one-on-one relationships outside the group, so your network isn't 
  tied to any single room or organization."

### Rebuilding the local cache after this change

This app does not read content_library/*.md fresh every time it runs. 
It builds a cached, embedded copy of the library once and saves it to 
data/content_library, and only rebuilds automatically if that path 
doesn't already exist. Editing the markdown text alone will not make 
the new wording show up in a locally running app -- the old cached 
copy will keep being served.

After editing the 22 files, delete the local cache so the app is forced 
to rebuild from the updated files on its next run:
- Delete the data/content_library symlink/directory, its target 
  .data-*  directory, and any lock file alongside it.
- The next time the app runs, _ensure_content_library_store() in app.py 
  will see that data/content_library doesn't exist and call build_store() 
  automatically to recreate it from the current (now-updated) markdown 
  files.

No existing automated test exercises this cached path, so this step 
must be verified manually: after deleting the cache and re-running the 
app, actually take the quiz and confirm the new wording appears in a 
real result for at least one style, rather than relying on the test 
suite alone to prove this landed.

## Acceptance criteria

1. Each of the 14 action-plan files listed above contains both a 
   reflective/affirming statement and one specific, concrete action 
   with an explicit timeframe marker (e.g. "this week," "today," "this 
   month," or a bounded relative time like "within 48 hours" or "a week 
   later").
2. q15_grow_network_intentionally_using.md is unchanged.
3. Each of the 8 identity/strengths files listed above is replaced with 
   the exact text given.
4. No frontmatter changes in any of the 22 files -- only body text.
5. No changes to content_library_store.py, scoring.py, or app.py.
6. The full existing test suite still passes unchanged.
7. New automated tests confirm, for each of the 14 action-plan files, 
   that the body text contains a timeframe marker as defined above. 
   (This is a proxy check only -- actual wording quality and brand 
   voice are confirmed by Sharon's manual read-through, not by the 
   test.)
8. After editing, the local cached store (data/content_library and its 
   target directory/lock file) is deleted, and the new wording is 
   manually confirmed by running the app and taking the quiz -- since 
   no automated test can verify this step.

## Out of scope

- Any new retrieval, blending, or personalization logic.
- Original, newly-written content beyond what's listed above (that's a 
  separate, later phase).
- Changes to q15 or to any file not listed above.
- Adding a new test file for the timeframe check is in scope (the "no 
  other files" restriction above applies to content_library/ files 
  only, not to adding tests); modifying any *existing* test file is 
  still out of scope.
- Item #19 (CI regression gating) -- unrelated, left as-is.
- Automatically detecting a stale local cache -- tracked separately as 
  backlog item #21, not solved here. This item only adds 
  the manual rebuild step for this one change.
