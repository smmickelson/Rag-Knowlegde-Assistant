"""
Tests for backlog item #4a — "Retrieve content-library chunks for a user's
result" (specs/4a-content-library-retrieval.md, status: draft)

These tests are written against the spec only. No implementation exists yet,
so every test below is expected to FAIL (most with a collection-time
ImportError) until the feature is built. That failure is the point: it
proves the suite is actually exercising the acceptance criteria rather than
passing by accident.

ASSUMED INTERFACE
-----------------
The spec does not name a function, so this suite assumes the #2b module
`content_library_store` (which already builds the content-library store)
gains one retrieval function:

    retrieve_for_score(store_dir: Path | str, score_result: dict,
                       embedding_model: str = DEFAULT_EMBEDDING_MODEL)
                           -> list[QueryResult]
        Returns exactly 6 chunks, in order:
          1. the philosophy_blend chunk (exact source-ID lookup, not ranked)
          2. the archetype `identity` chunk for the winning style
          3. the archetype `strengths` chunk for the winning style
          4-6. exactly 3 behavior chunks, filtered to chunks whose
               `archetypes` includes the winning style (after converting
               opportunitySeeker -> opportunity_seeker and
               communityBuilder -> community_builder) and whose `mode`
               matches the tier-derived rule (low/mid -> building, high ->
               using), then ranked by cosine distance to a phrase built from
               the four style totals, ties broken alphabetically by source_id.
        Each result is a QueryResult with .source_id .text .layer .metadata
        .distance. The 3 fixed chunks carry distance None.

        Raises the module's own `RetrievalError` for bad input (reusing #3's
        validation from action_item_store rather than duplicating it) or for
        insufficient store content (philosophy_blend missing, not-exactly-one
        archetype match for either piece, fewer than 3 eligible behaviors).
        Raises the module's existing `QueryError` for anything about reaching
        or using the store/model itself (missing/unreadable store, model
        mismatch, embedding failure). Input is validated before any store
        access, and error messages never echo caller-supplied values.

    The module also exposes (already present from #2b): DEFAULT_EMBEDDING_MODEL,
    BuildError, QueryError, build_store, count_items, get_item,
    get_store_embedding_model, list_source_ids, query_store.

If the real function/exception names differ, update the single import block
below and the two constants (REAL_KB_PATH, ALT_EMBEDDING_MODEL) — the test
bodies encode the acceptance criteria, not this module's naming choices.

WHAT THIS SUITE DOES NOT DO
---------------------------
It does not re-implement filtering, ranking, or phrase-building. It does not
test score_assessment (that's item #1), the #2b build/embedding (that's item
#2b's suite), or #3's retrieve_for_score (that's item #3's suite, which must
keep passing unchanged).

DUAL-COVERAGE PATTERN
---------------------
Most tests build a small synthetic content-library store in a temp folder,
so the suite runs and actually exercises the acceptance criteria without the
real library. A few tests depend on the real knowledge_base/ (notably the
personalization proof using the connector_mid/mixed_realistic fixture pair)
and skip cleanly when that folder is absent — the same tradeoff items #2/#2b
/#3 already ship with.
"""

import json
import os
from pathlib import Path

import pytest

from src.scoring import score_assessment

# --- Adjust these if the real module/location differs --------------------
from content_library_store import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    QueryError,
    RetrievalError,
    build_store,
    get_item,
    get_store_embedding_model,
    list_source_ids,
    query_store,
    retrieve_for_score,
)

REAL_KB_PATH = Path(
    os.environ.get(
        "KNOWLEDGE_BASE_PATH",
        "werkitgirls-resources/knowledge_base",
    )
)
ALT_EMBEDDING_MODEL = "a-different-embedding-model-than-the-store-used"

FIXTURE_FILE = Path(__file__).parent / "fixtures" / "known_answers.json"
with open(FIXTURE_FILE) as f:
    _ALL_FIXTURES = {fx["name"]: fx for fx in json.load(f)["fixtures"]}

# The score result shapes (style names) used throughout.
WINNING_STYLE_NAMES = [
    "connector", "cultivator", "opportunitySeeker", "communityBuilder",
]

ARCHETYPE_NAMES = [
    "connector", "cultivator", "opportunity_seeker", "community_builder",
]
ARCHETYPE_PIECES = ["identity", "strengths"]
BEHAVIOR_MODE_NAMES = ["building", "using"]
BEHAVIOR_SLUGS = {
    1: "introduce_yourself",
    2: "share_updates",
    3: "participate_in_orgs",
    4: "connect_others",
    5: "remember_details",
    6: "attend_events",
    7: "follow_up_gratitude",
    8: "expand_diverse_network",
    9: "respond_promptly",
    10: "support_others_networks",
    11: "engage_social_events",
    12: "reintroduce_yourself",
    13: "volunteer_cross_functional",
    14: "ask_for_support",
    15: "grow_network_intentionally",
}


def _require_real_knowledge_base():
    if not REAL_KB_PATH.is_dir():
        pytest.skip(
            f"Real knowledge_base folder not found at {REAL_KB_PATH}. Set "
            "KNOWLEDGE_BASE_PATH to point at the real knowledge_base/ from "
            "werkitgirls-resources."
        )


def _score_for(fixture_name):
    """Run the named fixture's 15 answers through the real scorer."""
    return score_assessment(_ALL_FIXTURES[fixture_name]["answers"])


def _valid_score_result(**overrides):
    """A structurally-valid score_result dict, matching score_assessment's
    output shape. Individual fields can be overridden for a bad-input test."""
    result = {
        "connector": 18,
        "cultivator": 6,
        "opportunitySeeker": 12,
        "communityBuilder": 12,
        "overall": 48,
        "winner": "connector",
        "tier": "mid",
    }
    result.update(overrides)
    return result


# ---------------------------------------------------------------------------
# Synthetic content-library builder.
#
# Uses the real naming the #2b store expects (archetype files are
# {connector,cultivator,opportunity_seeker,community_builder} x
# {identity,strengths}; behavior files are behavior_qNN_<slug>_{building,using}).
# Every behavior chunk shares one identical body, so within any eligible
# bucket all chunks embed to the same vector and tie at the same distance —
# the alphabetical tie-break then fully determines which 3 come back, which
# lets the default suite assert exact source IDs without relying on the
# opaque model.
#
# Behavior archetype tags are deliberately staggered: building-mode questions
# 1-3 are tagged `cultivator`, 4-6 `connector`, 7-9 `opportunity_seeker`,
# 10-12 `community_builder`, and 13-15 all four. So connector's alphabetically
# first *eligible* building chunk is behavior_q04..., not the globally-first
# behavior_q01..., which lets a test prove the archetypes filter actually
# excluded non-matching chunks.
# ---------------------------------------------------------------------------

def _write_md(directory: Path, filename: str, frontmatter: dict, body: str):
    import yaml
    fm_text = yaml.safe_dump(frontmatter, sort_keys=False).rstrip()
    (directory / filename).write_text(
        "---\n" + fm_text + "\n---\n" + body + "\n", encoding="utf-8")


def _behavior_tag(q: int, mode: str):
    """Which archetypes a synthetic behavior chunk is tagged with."""
    if q in (1, 2, 3):
        return ["cultivator"]
    if q in (4, 5, 6):
        return ["connector"]
    if q in (7, 8, 9):
        return ["opportunity_seeker"]
    if q in (10, 11, 12):
        return ["community_builder"]
    return ["connector", "cultivator", "opportunity_seeker", "community_builder"]


def _build_synthetic_knowledge_base(tmp_path: Path) -> Path:
    """A small, valid content library in ``tmp_path/knowledge_base``.

    2 philosophy, 8 archetype, 30 behavior files — the same shape the #2b
    build requires — with the controlled behavior tagging described above.
    """
    kb = tmp_path / "knowledge_base"
    kb.mkdir()

    _write_md(kb, "philosophy_blend.md",
              {"layer": "philosophy", "piece": "blend"},
              "There's no single best networking style; it's a blend.")
    _write_md(kb, "philosophy_werk_it_compass.md",
              {"layer": "philosophy", "piece": "werk_it_compass"},
              "Point yourself in a direction before you network.")

    for archetype in ARCHETYPE_NAMES:
        for piece in ARCHETYPE_PIECES:
            _write_md(kb, f"archetype_{archetype}_{piece}.md",
                      {"layer": "archetype", "archetype": archetype, "piece": piece},
                      f"{archetype} {piece} body")

    identical = "the exact same action item text repeated everywhere"
    for q in range(1, 16):
        slug = BEHAVIOR_SLUGS[q]
        for mode in BEHAVIOR_MODE_NAMES:
            _write_md(kb, f"behavior_q{q:02d}_{slug}_{mode}.md",
                      {"layer": "behavior", "question": q, "slug": slug,
                       "mode": mode, "archetypes": _behavior_tag(q, mode)},
                      identical)

    return kb


# Distinct behavior bodies for the connector+building bucket, each strongly
# themed around one networking style. connector_mid and mixed_realistic share
# a winner/tier but differ in their other totals (mixed_realistic weighs
# cultivator/opportunity/community more heavily), so these distinct bodies
# let the two phrases rank the behaviors differently — proving personalization
# without the real library.
_DISTINCT_CONNECTOR_BUILDING_BODIES = {
    4: "You notice when two people should meet and you introduce them, "
       "excited about the connection itself.",
    5: "You nurture relationships steadily, checking in, remembering "
       "details, and caring about how connections grow.",
    6: "You keep your eyes open for chances, and you act on the useful "
       "opportunities that cross your path.",
    13: "You bring people together across groups, building a sense of "
        "belonging wherever you go.",
    14: "Relationships grow because you tend them patiently, offering "
        "support and staying invested.",
    15: "New doors open because you reach out and pursue the right "
        "opportunities deliberately.",
}


def _build_distinct_knowledge_base(tmp_path: Path) -> Path:
    """Like ``_build_synthetic_knowledge_base`` but with distinct behavior
    bodies, so ranking is observable rather than every chunk tying.

    Used by the synthetic personalization test, where two score results that
    share a winner/tier must actually rank the connector+building behaviors
    to different top-3 sets.
    """
    kb = tmp_path / "knowledge_base"
    kb.mkdir()

    _write_md(kb, "philosophy_blend.md",
              {"layer": "philosophy", "piece": "blend"},
              "There's no single best networking style; it's a blend.")
    _write_md(kb, "philosophy_werk_it_compass.md",
              {"layer": "philosophy", "piece": "werk_it_compass"},
              "Point yourself in a direction before you network.")

    for archetype in ARCHETYPE_NAMES:
        for piece in ARCHETYPE_PIECES:
            _write_md(kb, f"archetype_{archetype}_{piece}.md",
                      {"layer": "archetype", "archetype": archetype, "piece": piece},
                      f"{archetype} {piece} body")

    for q in range(1, 16):
        slug = BEHAVIOR_SLUGS[q]
        for mode in BEHAVIOR_MODE_NAMES:
            body = _DISTINCT_CONNECTOR_BUILDING_BODIES.get(
                q, "A generic networking behavior body.")
            _write_md(kb, f"behavior_q{q:02d}_{slug}_{mode}.md",
                      {"layer": "behavior", "question": q, "slug": slug,
                       "mode": mode, "archetypes": _behavior_tag(q, mode)},
                      body)

    return kb


def _build_store_from(tmp_path, kb_dir) -> Path:
    store_dir = tmp_path / "store"
    build_store(kb_dir, store_dir)
    return store_dir


def _open_collection(store_dir):
    """Open the Chroma collection backing a #2b store, to simulate a store
    that became damaged after a healthy build (like #3's unhealthy-bucket
    test)."""
    from chromadb import PersistentClient
    client = PersistentClient(path=str(store_dir))
    return client, client.get_collection("content_library")


# ---------------------------------------------------------------------------
# AC1: for every winning style, retrieval returns philosophy_blend, both
# archetype chunks for that style, and exactly 3 behavior chunks — 6 total —
# each carrying its source ID, in the fixed order, with the fixed chunks'
# distance as None.
# ---------------------------------------------------------------------------

class TestReturnsSixChunks:
    @pytest.mark.parametrize(
        "winner,score_result",
        [
            ("connector", _valid_score_result(winner="connector", tier="mid")),
            ("cultivator", _valid_score_result(winner="cultivator", tier="mid")),
            ("opportunitySeeker",
             _valid_score_result(winner="opportunitySeeker", tier="mid")),
            ("communityBuilder",
             _valid_score_result(winner="communityBuilder", tier="mid")),
        ],
        ids=["connector", "cultivator", "opportunity_seeker", "community_builder"],
    )
    def test_returns_six_chunks_in_fixed_order(self, tmp_path, winner, score_result):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        results = retrieve_for_score(store_dir, score_result)
        assert len(results) == 6

        style = winner.replace("Seeker", "_seeker").replace("Builder", "_builder")
        assert [r.source_id for r in results] == [
            "philosophy_blend",
            f"archetype_{style}_identity",
            f"archetype_{style}_strengths",
            results[3].source_id,
            results[4].source_id,
            results[5].source_id,
        ]

        # Every result carries its source ID and full metadata.
        for r in results:
            assert r.source_id
            assert r.text
            assert r.layer
            assert r.metadata

        # The 3 fixed chunks were not selected by similarity.
        for r in results[:3]:
            assert r.distance is None

    def test_philosophy_blend_is_first_and_not_personalized(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        for winner in WINNING_STYLE_NAMES:
            results = retrieve_for_score(
                store_dir, _valid_score_result(winner=winner, tier="mid"))
            assert results[0].source_id == "philosophy_blend"

    def test_werk_it_compass_is_never_returned(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        results = retrieve_for_score(
            store_dir, _valid_score_result(winner="connector", tier="mid"))
        returned = {r.source_id for r in results}
        assert "philosophy_werk_it_compass" not in returned


# ---------------------------------------------------------------------------
# AC2: every returned behavior chunk has the winning style in its
# `archetypes` list and the tier-derived mode.
# ---------------------------------------------------------------------------

class TestBehaviorFiltering:
    def test_mid_tier_returns_building_mode_behaviors(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        results = retrieve_for_score(
            store_dir, _valid_score_result(winner="connector", tier="mid"))
        behaviors = results[3:]
        assert len(behaviors) == 3
        for b in behaviors:
            assert b.metadata["mode"] == "building"
            assert "connector" in b.metadata["archetypes"]

    def test_high_tier_returns_using_mode_behaviors(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        results = retrieve_for_score(
            store_dir, _valid_score_result(winner="connector", tier="high"))
        behaviors = results[3:]
        for b in behaviors:
            assert b.metadata["mode"] == "using"
            assert "connector" in b.metadata["archetypes"]

    def test_archetypes_filter_excludes_non_matching_behaviors(self, tmp_path):
        """The archetypes filter must run before ranking: connector's
        alphabetically-first eligible building chunk is behavior_q04..., not
        the globally-first behavior_q01... (which is tagged cultivator). An
        implementation that ranks the whole store first would return
        behavior_q01..q03; the correct filtered build returns q04..q06."""
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        results = retrieve_for_score(
            store_dir, _valid_score_result(winner="connector", tier="mid"))
        behavior_ids = [r.source_id for r in results[3:]]
        assert behavior_ids == [
            "behavior_q04_connect_others_building",
            "behavior_q05_remember_details_building",
            "behavior_q06_attend_events_building",
        ]


# ---------------------------------------------------------------------------
# AC3 (real library): for two score results sharing a winning style and tier
# but differing in their other three totals, the ranked set of 3 behavior
# chunks differs by at least one source ID — not merely a reordering.
# ---------------------------------------------------------------------------

class TestPersonalization:
    def test_same_bucket_different_totals_yield_different_behavior_set(
        self, tmp_path
    ):
        _require_real_knowledge_base()
        store_dir = _build_store_from(tmp_path, REAL_KB_PATH)

        connector_mid = _score_for("connector_mid")
        mixed_realistic = _score_for("mixed_realistic")
        assert connector_mid["winner"] == mixed_realistic["winner"] == "connector"
        assert connector_mid["tier"] == mixed_realistic["tier"] == "mid"

        a = retrieve_for_score(store_dir, connector_mid)[3:]
        b = retrieve_for_score(store_dir, mixed_realistic)[3:]

        a_ids = {r.source_id for r in a}
        b_ids = {r.source_id for r in b}
        assert a_ids != b_ids, (
            "the two score results must differ in at least one returned "
            "behavior source ID, not just the order of the same 3"
        )

    def test_synthetic_library_also_demonstrates_personalization(self, tmp_path):
        """A synthetic, non-skipping version of the personalization check.

        Uses the same connector_mid/mixed_realistic fixture pair, but against
        the distinct-bodied synthetic library, so broken personalization is
        caught by the default suite even when the real library is absent. The
        distinct behavior bodies let the two score patterns (which differ in
        their cultivator/opportunity/community totals) rank the connector+
        building behaviors to different top-3 sets.
        """
        kb = _build_distinct_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        connector_mid = _score_for("connector_mid")
        mixed_realistic = _score_for("mixed_realistic")
        assert connector_mid["winner"] == mixed_realistic["winner"] == "connector"
        assert connector_mid["tier"] == mixed_realistic["tier"] == "mid"

        a_ids = {r.source_id for r in retrieve_for_score(store_dir, connector_mid)[3:]}
        b_ids = {r.source_id for r in retrieve_for_score(store_dir, mixed_realistic)[3:]}
        assert a_ids != b_ids, (
            "on the synthetic library the two score results must still yield "
            "at least one different behavior source ID"
        )


# ---------------------------------------------------------------------------
# AC4: same input against an unchanged store returns the identical 6 chunks
# in the identical order every time.
# ---------------------------------------------------------------------------

class TestDeterminism:
    def test_repeated_calls_return_identical_order(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        score_result = _valid_score_result(winner="connector", tier="mid")

        first = [r.source_id for r in retrieve_for_score(store_dir, score_result)]
        second = [r.source_id for r in retrieve_for_score(store_dir, score_result)]
        assert first == second


# ---------------------------------------------------------------------------
# Tie-breaking (spec question round #4): when behavior chunks tie at the same
# distance across the third-place cutoff, the alphabetical source-ID order
# must decide which 3 come back. The existing filter/determinism tests would
# still pass if the source_id sort key were removed (Chroma's natural order
# for tied items can coincide with alphabetical), so this forces the tie
# deliberately and asserts the exact alphabetical top-3.
# ---------------------------------------------------------------------------

class TestAlphabeticalTieBreak:
    def test_tied_behaviors_across_the_cutoff_break_alphabetically(
        self, tmp_path
    ):
        """Six equally-ranked connector+building behaviors: the alphabetical
        first three must be returned, with the fourth (reverse-source-ID
        candidate) the one cut at the boundary."""
        kb = _build_distinct_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        # Force an exact tie among all six eligible connector+building
        # behaviors by overwriting their stored embeddings with one shared
        # vector, so distance to any phrase is identical for all of them.
        tied_ids = [
            "behavior_q04_connect_others_building",
            "behavior_q05_remember_details_building",
            "behavior_q06_attend_events_building",
            "behavior_q13_volunteer_cross_functional_building",
            "behavior_q14_ask_for_support_building",
            "behavior_q15_grow_network_intentionally_building",
        ]
        client, collection = _open_collection(store_dir)
        try:
            collection.update(
                ids=tied_ids,
                embeddings=[[0.1] * 384 for _ in tied_ids],
            )
        finally:
            client.close()

        results = retrieve_for_score(
            store_dir, _valid_score_result(winner="connector", tier="mid"))
        behavior_ids = [r.source_id for r in results[3:]]

        assert behavior_ids == sorted(behavior_ids), (
            "the returned behaviors must be in alphabetical source-ID order"
        )
        # The alphabetical-first three of the six tied candidates.
        assert behavior_ids == tied_ids[:3]


# ---------------------------------------------------------------------------
# AC5 (input validation): the same validation contract as #3, reusing #3's
# logic. Each invalid case raises RetrievalError, and error messages never
# echo caller-supplied values.
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_non_dict_input_is_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, ["not", "a", "dict"])

    def test_dict_subclass_is_rejected(self, tmp_path):
        class SneakyDict(dict):
            pass

        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, SneakyDict(_valid_score_result()))

    @pytest.mark.parametrize(
        "missing_key", ["connector", "cultivator", "opportunitySeeker",
                        "communityBuilder", "overall", "winner", "tier"]
    )
    def test_missing_required_key_is_rejected(self, tmp_path, missing_key):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        score_result = _valid_score_result()
        del score_result[missing_key]
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    def test_unexpected_extra_key_is_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(bogus_key="x"))

    @pytest.mark.parametrize("bad_total", ["12", 12.5, True, None])
    def test_non_int_style_total_is_rejected(self, tmp_path, bad_total):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(connector=bad_total))

    def test_all_zero_totals_are_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(
                connector=0, cultivator=0, opportunitySeeker=0,
                communityBuilder=0, overall=0))

    def test_out_of_range_total_is_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(connector=10**400))

    def test_unknown_winner_name_is_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(winner="nope"))

    def test_mistyped_casing_in_winner_is_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(winner="Connector"))

    def test_unknown_tier_is_rejected(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(tier="extreme"))

    def test_error_message_never_echoes_the_value(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(RetrievalError) as excinfo:
            retrieve_for_score(store_dir, _valid_score_result(connector="eighteen"))
        assert "eighteen" not in str(excinfo.value)

    def test_winner_and_tier_are_trusted_as_given(self, tmp_path):
        """winner/tier are not cross-checked against the totals: a valid style
        name and tier succeed even if they look inconsistent with the totals,
        exactly as #3 trusts them."""
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        results = retrieve_for_score(store_dir, _valid_score_result(
            winner="connector", tier="high"))
        assert len(results) == 6


# ---------------------------------------------------------------------------
# AC5 (store-content insufficient): a missing philosophy_blend, a not-exactly-
# one match for an archetype piece, or fewer than 3 eligible behaviors each
# raise RetrievalError. Simulated by damaging a healthy store's collection.
# ---------------------------------------------------------------------------

class TestStoreContentInsufficient:
    def test_missing_philosophy_blend_raises(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        client, collection = _open_collection(store_dir)
        try:
            collection.delete(ids=["philosophy_blend"])
        finally:
            client.close()

        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result())

    def test_missing_archetype_identity_raises(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        client, collection = _open_collection(store_dir)
        try:
            collection.delete(ids=["archetype_connector_identity"])
        finally:
            client.close()

        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(winner="connector"))

    def test_duplicate_archetype_identity_raises(self, tmp_path):
        """Two identity chunks for the same style (not exactly one match)
        must be rejected."""
        import json as _json

        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        client, collection = _open_collection(store_dir)
        try:
            # Relabel connector's strengths chunk so it is another identity
            # chunk, giving two identity matches for connector.
            collection.update(
                ids=["archetype_connector_strengths"],
                metadatas=[{"layer": "archetype", "metadata_json": _json.dumps(
                    {"layer": "archetype", "archetype": "connector",
                     "piece": "identity"})}],
            )
        finally:
            client.close()

        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(winner="connector"))

    def test_fewer_than_three_eligible_behaviors_raises(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        client, collection = _open_collection(store_dir)
        try:
            # connector+building has 6 eligible (q04-q06, q13-q15). Delete four
            # of them so only 2 remain.
            collection.delete(ids=[
                "behavior_q06_attend_events_building",
                "behavior_q13_volunteer_cross_functional_building",
                "behavior_q14_ask_for_support_building",
                "behavior_q15_grow_network_intentionally_building",
            ])
        finally:
            client.close()

        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, _valid_score_result(winner="connector", tier="mid"))


# ---------------------------------------------------------------------------
# AC5 (reaching/using the store): reuses #2b's existing QueryError for a
# missing store, an unusable store, or a mismatched embedding model.
# ---------------------------------------------------------------------------

class TestReusesStoreErrorHandling:
    def test_missing_store_raises_query_error(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(QueryError):
            retrieve_for_score(missing, _valid_score_result())

    def test_unrelated_directory_is_not_usable(self, tmp_path):
        (tmp_path / "not_a_store").mkdir()
        with pytest.raises(QueryError):
            retrieve_for_score(tmp_path / "not_a_store", _valid_score_result())

    def test_mismatched_embedding_model_raises_naming_both_models(self, tmp_path):
        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        stored_model = get_store_embedding_model(store_dir)
        assert stored_model != ALT_EMBEDDING_MODEL

        with pytest.raises(QueryError) as excinfo:
            retrieve_for_score(store_dir, _valid_score_result(),
                               embedding_model=ALT_EMBEDDING_MODEL)
        message = str(excinfo.value)
        assert stored_model in message
        assert ALT_EMBEDDING_MODEL in message

    def test_store_vanishing_mid_request_raises_query_error(self, tmp_path, monkeypatch):
        """A store that becomes unreadable during the request (after it was
        reached) must surface as QueryError, not a raw exception and not a
        silent success. Simulated by making the Chroma collection's read raise
        a low-level error mid-retrieval."""
        from chromadb.api.models.Collection import Collection

        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        def exploding_get(*args, **kwargs):
            raise RuntimeError("store version disappeared mid-request")

        monkeypatch.setattr(Collection, "get", exploding_get)
        with pytest.raises(QueryError):
            retrieve_for_score(store_dir, _valid_score_result())

    def test_embedding_failure_raises_query_error(self, tmp_path, monkeypatch):
        """A failure converting the search phrase to a vector (the model call
        raising) must surface as QueryError, not a raw exception or a silent
        success against the wrong store version."""
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

        kb = _build_synthetic_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)

        def exploding_embed(*args, **kwargs):
            raise RuntimeError("phrase could not be embedded")

        monkeypatch.setattr(ONNXMiniLM_L6_V2, "__call__", exploding_embed)
        with pytest.raises(QueryError):
            retrieve_for_score(store_dir, _valid_score_result())


# ---------------------------------------------------------------------------
# "What it does NOT do": #2b's own query_store must keep working unchanged.
# This is a guard, not new coverage — #2b's suite owns the real assertions.
# ---------------------------------------------------------------------------

def test_query_store_still_works_unfiltered(tmp_path):
    kb = _build_synthetic_knowledge_base(tmp_path)
    store_dir = _build_store_from(tmp_path, kb)
    results = query_store(store_dir, "a valid unfiltered query", n_results=3)
    assert len(results) == 3