"""Tests for specs/20-content-library-html-parity.md.

This item replaces the body text of 22 files in content_library/ with wording
drawn from the live HTML tool at tools.werkitgirls.com: 14 action-plan
behavior files (the "using"-mode files, q15 excluded) gain a concrete,
time-bound task to pair with their reflection, and 8 archetype
identity/strengths files are shortened to the exact replacement sentences.

No file is renamed and no frontmatter changes (layer, question, slug, mode,
archetype/archetypes, piece all stay exactly as they are).

These tests are the automated, tests-first proxy for the acceptance criteria.
They are written against the CURRENT (pre-edit) content_library files, so
most fail right now -- the old text is still in place. Two tests are expected
to pass immediately and are flagged as such:

- q15_grow_network_intentionally_using.md is already correct, so its "body
  unchanged" test passes now.
- Frontmatter is untouched, so the "frontmatter unchanged" test passes now.

Per the spec's acceptance criterion #7, the action-plan check is a proxy for
a timeframe marker only; actual wording quality and brand voice are confirmed
by Sharon's manual read-through, not by this test. The reflective/affirming
check below is likewise a light pattern proxy (an affirming lead), not a
writing-quality judgment.
"""

import re
from pathlib import Path

import pytest

CONTENT_LIBRARY_DIR = Path(__file__).resolve().parent.parent / "content_library"

# --- The 14 action-plan files being rewritten (q15 excluded) --------------
ACTION_PLAN_FILES = [
    "behavior_q01_introduce_yourself_using.md",
    "behavior_q02_share_updates_using.md",
    "behavior_q03_participate_in_orgs_using.md",
    "behavior_q04_connect_others_using.md",
    "behavior_q05_remember_details_using.md",
    "behavior_q06_attend_events_using.md",
    "behavior_q07_follow_up_gratitude_using.md",
    "behavior_q08_expand_diverse_network_using.md",
    "behavior_q09_respond_promptly_using.md",
    "behavior_q10_support_others_networks_using.md",
    "behavior_q11_engage_social_events_using.md",
    "behavior_q12_reintroduce_yourself_using.md",
    "behavior_q13_volunteer_cross_functional_using.md",
    "behavior_q14_ask_for_support_using.md",
]

# The 8 archetype identity/strengths files being replaced.
IDENTITY_STRENGTHS_FILES = [
    "archetype_connector_identity.md",
    "archetype_connector_strengths.md",
    "archetype_cultivator_identity.md",
    "archetype_cultivator_strengths.md",
    "archetype_opportunity_seeker_identity.md",
    "archetype_opportunity_seeker_strengths.md",
    "archetype_community_builder_identity.md",
    "archetype_community_builder_strengths.md",
]

# All 22 files covered by the "no frontmatter changes" criterion.
ALL_22_FILES = ACTION_PLAN_FILES + IDENTITY_STRENGTHS_FILES

# q15 is intentionally left unchanged.
Q15_FILE = "behavior_q15_grow_network_intentionally_using.md"


def _split_md(text):
    """Return (frontmatter_dict, body_text). The body is everything after the
    closing `---`, with leading/trailing whitespace stripped."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    assert match, "expected frontmatter delimited by ---"
    import yaml
    return yaml.safe_load(match.group(1)), match.group(2).strip()


def _body_of(filename):
    return _split_md((CONTENT_LIBRARY_DIR / filename).read_text(encoding="utf-8"))[1]


def _frontmatter_of(filename):
    return _split_md((CONTENT_LIBRARY_DIR / filename).read_text(encoding="utf-8"))[0]


# --- Timeframe marker proxy ------------------------------------------------

# Acceptable timeframe markers: "today", "this week", "this month", or a
# bounded relative-time phrase like "a week later" / "within 48 hours".
TIMEFRAME_MARKER = re.compile(
    r"\btoday\b"
    r"|\bthis week\b"
    r"|\bthis month\b"
    r"|\bwithin \d+ (?:hours?|days?|weeks?)\b"
    r"|\b\d+ (?:days?|weeks?) later\b"
    r"|\ba week later\b",
    re.IGNORECASE,
)

# A permissive proxy for "the body opens with a reflective/affirming
# statement": an affirming lead that recognizes something the user already
# does. Covers every approved replacement text. Writing quality itself is
# checked by Sharon's manual read, not here.
AFFIRMING_LEAD = re.compile(
    r"you already|you're already|\balready\b|you invest|you give|"
    r"think about who in your network|you show up",
    re.IGNORECASE,
)


# --- Exact replacement text for the 8 identity/strengths files ------------

IDENTITY_STRENGTHS_EXPECTED = {
    "archetype_connector_identity.md": (
        "Creating value for others without keeping score. You're the person "
        "people think of when they say 'you have to meet so-and-so.'"
    ),
    "archetype_connector_strengths.md": (
        "Slowing down to deepen the connections you already have, so your "
        "network has roots — not just reach."
    ),
    "archetype_cultivator_identity.md": (
        "Loyalty and authenticity. People don't just know you — they count "
        "on you."
    ),
    "archetype_cultivator_strengths.md": (
        "Expanding your circle so that your influence reaches as far as your "
        "impact. The depth is there — now stretch the width."
    ),
    "archetype_opportunity_seeker_identity.md": (
        "Strategic visibility and initiative. You put yourself in rooms where "
        "things happen."
    ),
    "archetype_opportunity_seeker_strengths.md": (
        "Making sure people experience your genuine curiosity, not just your "
        "agenda — so relationships outlast the opportunity that started them."
    ),
    "archetype_community_builder_identity.md": (
        "Creating belonging. People feel seen and included around you."
    ),
    "archetype_community_builder_strengths.md": (
        "Investing in one-on-one relationships outside the group, so your "
        "network isn't tied to any single room or organization."
    ),
}

# --- Current frontmatter, recorded before the edit (must not change) ------

EXPECTED_FRONTMATTER = {
    "behavior_q01_introduce_yourself_using.md": {
        "layer": "behavior", "question": 1, "slug": "introduce_yourself",
        "mode": "using", "archetypes": ["cultivator"],
    },
    "behavior_q02_share_updates_using.md": {
        "layer": "behavior", "question": 2, "slug": "share_updates",
        "mode": "using", "archetypes": ["cultivator"],
    },
    "behavior_q03_participate_in_orgs_using.md": {
        "layer": "behavior", "question": 3, "slug": "participate_in_orgs",
        "mode": "using",
        "archetypes": ["opportunity_seeker", "community_builder"],
    },
    "behavior_q04_connect_others_using.md": {
        "layer": "behavior", "question": 4, "slug": "connect_others",
        "mode": "using", "archetypes": ["connector", "community_builder"],
    },
    "behavior_q05_remember_details_using.md": {
        "layer": "behavior", "question": 5, "slug": "remember_details",
        "mode": "using", "archetypes": ["cultivator"],
    },
    "behavior_q06_attend_events_using.md": {
        "layer": "behavior", "question": 6, "slug": "attend_events",
        "mode": "using",
        "archetypes": ["opportunity_seeker", "community_builder"],
    },
    "behavior_q07_follow_up_gratitude_using.md": {
        "layer": "behavior", "question": 7, "slug": "follow_up_gratitude",
        "mode": "using", "archetypes": ["cultivator"],
    },
    "behavior_q08_expand_diverse_network_using.md": {
        "layer": "behavior", "question": 8, "slug": "expand_diverse_network",
        "mode": "using", "archetypes": ["connector", "opportunity_seeker"],
    },
    "behavior_q09_respond_promptly_using.md": {
        "layer": "behavior", "question": 9, "slug": "respond_promptly",
        "mode": "using", "archetypes": ["cultivator"],
    },
    "behavior_q10_support_others_networks_using.md": {
        "layer": "behavior", "question": 10, "slug": "support_others_networks",
        "mode": "using", "archetypes": ["connector", "community_builder"],
    },
    "behavior_q11_engage_social_events_using.md": {
        "layer": "behavior", "question": 11, "slug": "engage_social_events",
        "mode": "using",
        "archetypes": ["opportunity_seeker", "community_builder"],
    },
    "behavior_q12_reintroduce_yourself_using.md": {
        "layer": "behavior", "question": 12, "slug": "reintroduce_yourself",
        "mode": "using", "archetypes": ["cultivator"],
    },
    "behavior_q13_volunteer_cross_functional_using.md": {
        "layer": "behavior", "question": 13, "slug": "volunteer_cross_functional",
        "mode": "using", "archetypes": ["connector", "opportunity_seeker"],
    },
    "behavior_q14_ask_for_support_using.md": {
        "layer": "behavior", "question": 14, "slug": "ask_for_support",
        "mode": "using", "archetypes": ["connector", "opportunity_seeker"],
    },
    "archetype_connector_identity.md": {
        "layer": "archetype", "archetype": "connector", "piece": "identity",
    },
    "archetype_connector_strengths.md": {
        "layer": "archetype", "archetype": "connector", "piece": "strengths",
    },
    "archetype_cultivator_identity.md": {
        "layer": "archetype", "archetype": "cultivator", "piece": "identity",
    },
    "archetype_cultivator_strengths.md": {
        "layer": "archetype", "archetype": "cultivator", "piece": "strengths",
    },
    "archetype_opportunity_seeker_identity.md": {
        "layer": "archetype", "archetype": "opportunity_seeker",
        "piece": "identity",
    },
    "archetype_opportunity_seeker_strengths.md": {
        "layer": "archetype", "archetype": "opportunity_seeker",
        "piece": "strengths",
    },
    "archetype_community_builder_identity.md": {
        "layer": "archetype", "archetype": "community_builder",
        "piece": "identity",
    },
    "archetype_community_builder_strengths.md": {
        "layer": "archetype", "archetype": "community_builder",
        "piece": "strengths",
    },
}

# --- q15's current body, recorded before the edit (must stay unchanged) ----

Q15_CURRENT_BODY = (
    "You already think intentionally about growing your network — put it on "
    "paper. A simple quarterly check of who's in your corner and who's "
    "missing keeps the habit from running only in your head."
)


# ---------------------------------------------------------------------------
# AC1: each of the 14 action-plan files contains both a reflective/affirming
# statement and an explicit timeframe marker (proxy pattern check).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename", ACTION_PLAN_FILES,
                         ids=[f.split("_")[1] for f in ACTION_PLAN_FILES])
def test_action_plan_file_has_reflection_and_a_timeframe_marker(filename):
    body = _body_of(filename)

    # (a) Reflective/affirming lead (proxy for writing quality).
    assert AFFIRMING_LEAD.search(body), (
        f"{filename}: body does not contain an affirming/reflective lead"
    )
    # (b) Explicit timeframe marker.
    assert TIMEFRAME_MARKER.search(body), (
        f"{filename}: body has no explicit timeframe marker (today / this "
        "week / this month / a bounded relative time)"
    )


# ---------------------------------------------------------------------------
# AC2: q15_grow_network_intentionally_using.md is unchanged.
# ---------------------------------------------------------------------------

def test_q15_grow_network_intentionally_using_is_unchanged():
    assert _body_of(Q15_FILE) == Q15_CURRENT_BODY, (
        "q15 should be untouched; its body must still be the original text"
    )


# ---------------------------------------------------------------------------
# AC3: each of the 8 identity/strengths files matches the exact replacement
# text given in the spec.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename", IDENTITY_STRENGTHS_FILES,
                         ids=[f.replace(".md", "") for f in IDENTITY_STRENGTHS_FILES])
def test_identity_or_strengths_file_matches_exact_replacement_text(filename):
    body = _body_of(filename)
    assert body == IDENTITY_STRENGTHS_EXPECTED[filename], (
        f"{filename}: body does not match the approved replacement text"
    )


# ---------------------------------------------------------------------------
# AC4: no frontmatter changes in any of the 22 files.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename", ALL_22_FILES,
                         ids=[f.replace(".md", "") for f in ALL_22_FILES])
def test_frontmatter_is_unchanged(filename):
    actual = _frontmatter_of(filename)
    assert actual == EXPECTED_FRONTMATTER[filename], (
        f"{filename}: frontmatter changed from its recorded value"
    )