"""
Tests for backlog item #3 — "Similarity search against the embedded content"
(specs/03-similarity-search.md, status: questioned)

These tests are written against the spec only. No implementation exists yet,
so every test below is expected to FAIL (most with a collection-time
ImportError) until the feature is built. That failure is the point: it
proves the suite is actually exercising the acceptance criteria rather than
passing by accident.

ASSUMED INTERFACE
------------------
The spec does not name a function, so this suite assumes `action_item_store`
(the same module item #2 built) gains:

    class RetrievalError(Exception): ...
        Raised for anything wrong with the *input* to retrieval: not a
        dict, missing/extra keys, wrong value types, or an unknown style/
        tier name. Per the spec's question round (#2, #6), the message
        never includes the bad value itself, only what was wrong.

    retrieve_for_score(store_dir, score_result,
                        embedding_model=DEFAULT_EMBEDDING_MODEL)
            -> list[QueryResult]
        `score_result` is exactly the dict `score_assessment` returns:
        the four style totals (int), `overall` (int), `winner` (one of
        the four style names), `tier` (one of "high"/"mid"/"low").
        Filters to the 5 chunks stored under the winning style+tier pair,
        ranks them by closeness to a phrase built from all four totals,
        and returns the top `n_results` (QueryResult: .source_id .text
        .style .tier .distance — the same shape item #2's query_store
        already returns).
        For a missing/incompatible store, raises the *existing* QueryError
        from action_item_store (spec question round, #5) — not a new
        error type.

If the real names differ, update the import block below and the two
constants (REAL_HTML_PATH, ALT_EMBEDDING_MODEL) — the test bodies encode
the acceptance criteria and the spec's question-round answers, not this
module's naming choices.

WHAT THIS SUITE DOES NOT DO
----------------------------
It does not re-implement filtering or ranking. It does not test
score_assessment itself (that's item #1's suite) or query_store's
unfiltered behavior (that's item #2's suite, which must keep passing
unchanged per this item's own "What it does NOT do").
"""

import json
import os
from pathlib import Path

import pytest

from src.scoring import score_assessment

# --- Adjust these if the real module/location differs --------------------
from action_item_store import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    STYLES,
    TIERS,
    QueryError,
    RetrievalError,
    build_store,
    get_item,
    retrieve_for_score,
)

REAL_HTML_PATH = Path(
    os.environ.get(
        "ACTION_ITEMS_HTML_PATH",
        "werkitgirls-resources/networking-assessment.html",
    )
)
ALT_EMBEDDING_MODEL = "a-different-embedding-model-than-the-store-used"

FIXTURE_FILE = Path(__file__).parent / "fixtures" / "known_answers.json"
with open(FIXTURE_FILE) as f:
    _ALL_FIXTURES = {fx["name"]: fx for fx in json.load(f)["fixtures"]}

# The 5 sample answer sets named in the spec's Notes.
SAMPLE_FIXTURE_NAMES = [
    "cultivator_high",
    "connector_mid",
    "opportunity_seeker_low",
    "community_builder_mid",
    "mixed_realistic",
]
SAMPLE_FIXTURES = {name: _ALL_FIXTURES[name] for name in SAMPLE_FIXTURE_NAMES}


def _require_real_html():
    if not REAL_HTML_PATH.exists():
        pytest.skip(
            f"Real HTML fixture not found at {REAL_HTML_PATH}. Set "
            "ACTION_ITEMS_HTML_PATH to point at the real "
            "networking-assessment.html from werkitgirls-resources."
        )


def _score_for(fixture_name):
    """Run the named fixture's 15 answers through the real scorer."""
    return score_assessment(_ALL_FIXTURES[fixture_name]["answers"])


def _valid_profiles_js():
    """A complete, valid profiles object: 4 styles x 3 tiers x 5 items."""
    items = '["a", "b", "c", "d", "e"]'
    tiers = (
        "{"
        + ", ".join(f'"{tier}": {items}' for tier in ["high", "mid", "low"])
        + "}"
    )
    styles = []
    for style in STYLES:
        styles.append(f'"{style}": {{"actions": {tiers}}}')
    return "{" + ", ".join(styles) + "}"


def _build_minimal_valid_store(tmp_path):
    """A small, structurally-valid store, for tests that only care about
    input validation or error plumbing, not retrieval quality."""
    html_path = tmp_path / "valid.html"
    html_path.write_text(
        f"<html><body><script>var profiles = {_valid_profiles_js()};"
        "</script></body></html>",
        encoding="utf-8",
    )
    store_dir = tmp_path / "store"
    build_store(html_path, store_dir)
    return store_dir


def _build_store_with_identical_text(tmp_path):
    """A store where all 60 items share one identical text, so every item
    embeds to the same vector and is exactly equidistant from any query,
    regardless of what that query is. Used to prove that retrieval filters
    to the winning style+tier *before* ranking, independent of whatever
    search phrase the implementation builds from the four totals."""
    identical = "the exact same action item text repeated everywhere"
    items = json.dumps([identical] * 5)
    tiers = (
        "{"
        + ", ".join(f'"{t}": {items}' for t in ["high", "mid", "low"])
        + "}"
    )
    profiles = (
        "{"
        + ", ".join(f'"{style}": {{"actions": {tiers}}}' for style in STYLES)
        + "}"
    )
    html_path = tmp_path / "tied.html"
    html_path.write_text(
        f"<html><body><script>var profiles = {profiles};</script></body></html>",
        encoding="utf-8",
    )
    store_dir = tmp_path / "store"
    build_store(html_path, store_dir)
    return store_dir


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


class _FixedVectorEmbedding:
    """A stand-in embedding function that always returns the same vector,
    regardless of the text it's given. Used to control exactly what "query
    vector" retrieve_for_score computes, so a test can assert an exact,
    hand-computed ranking order instead of trusting the real embedding
    model to behave a particular way."""

    def __init__(self, vector):
        self._vector = vector

    def __call__(self, texts):
        return [self._vector for _ in texts]


def _build_store_with_known_vectors(tmp_path, items):
    """A store built by writing chosen embedding vectors directly into
    Chroma for one style+tier bucket, bypassing build_store's real-text
    embedding entirely. ``items`` is an ordered list of (source_id, style,
    tier, vector) tuples; passing them in a shuffled, non-alphabetical
    order (rather than build_store's own sorted-by-ID insertion order)
    lets a test prove sorting is actually happening, not just reflecting
    whatever order they happened to be stored in."""
    from chromadb import PersistentClient

    store_dir = tmp_path / "store"
    client = PersistentClient(path=str(store_dir))
    collection = client.get_or_create_collection(
        "action_items",
        metadata={"hnsw:space": "cosine", "embedding_model": DEFAULT_EMBEDDING_MODEL},
    )
    collection.add(
        ids=[sid for sid, _, _, _ in items],
        documents=[f"text for {sid}" for sid, _, _, _ in items],
        metadatas=[{"style": style, "tier": tier} for _, style, tier, _ in items],
        embeddings=[vector for _, _, _, vector in items],
    )
    client.close()
    return store_dir


# ---------------------------------------------------------------------------
# Test quality review: nothing previously proved retrieval actually ranks
# by *closeness* — only that different people get different top results,
# which a build that ranked by the farthest match (or shuffled the order)
# could still pass by coincidence. These use hand-picked vectors with
# distances computed by hand, so the expected order is unambiguous.
# ---------------------------------------------------------------------------

class TestNearestChunksActuallyWin:
    def test_exact_order_matches_known_cosine_distances(self, tmp_path, monkeypatch):
        """
        Deleting this test removes the only proof that retrieval ranks by
        genuine closeness to the query. Without it, a build that sorted by
        the *farthest* match instead of the nearest, or that returned the
        right 3 chunks in a scrambled order, could still pass every other
        test in this suite, since those only check that different inputs
        produce different top results, never that the winner is the
        actually-closest one.
        """
        # Five hand-picked vectors with cosine distances from [1, 0, 0]
        # computed by hand: identical (0.0), very close (~0.0061), ~45
        # degrees (~0.2929), orthogonal (1.0), and opposite (2.0). Stored
        # in a shuffled, non-alphabetical order so a pass-through-storage-
        # order bug can't accidentally look correct.
        items = [
            ("connector-mid-4", "connector", "mid", [0.0, 1.0, 0.0]),
            ("connector-mid-2", "connector", "mid", [0.9, 0.1, 0.0]),
            ("connector-mid-5", "connector", "mid", [-1.0, 0.0, 0.0]),
            ("connector-mid-1", "connector", "mid", [1.0, 0.0, 0.0]),
            ("connector-mid-3", "connector", "mid", [0.5, 0.5, 0.0]),
        ]
        store_dir = _build_store_with_known_vectors(tmp_path, items)

        import action_item_store
        monkeypatch.setattr(
            action_item_store, "ONNXMiniLM_L6_V2",
            lambda: _FixedVectorEmbedding([1.0, 0.0, 0.0]),
        )

        score_result = _valid_score_result(winner="connector", tier="mid")
        results = retrieve_for_score(store_dir, score_result)

        assert [r.source_id for r in results] == [
            "connector-mid-1", "connector-mid-2", "connector-mid-3",
        ]
        assert results[0].distance == pytest.approx(0.0, abs=1e-6)
        assert results[1].distance == pytest.approx(0.0061, abs=1e-3)
        assert results[2].distance == pytest.approx(0.2929, abs=1e-3)

    def test_tie_break_sorts_regardless_of_storage_order(self, tmp_path, monkeypatch):
        """
        Deleting this test removes the only proof that the alphabetical
        tie-break is a genuine sort, not an accident of insertion order.
        build_store always inserts items in sorted-by-ID order (it calls
        ``sorted(items.keys())`` before writing), so a store built the
        normal way can't tell "correctly sorts tied results" apart from
        "just returns whatever order Chroma handed back, which happens to
        already be sorted." Storing 5 identically-distanced items in a
        deliberately shuffled order closes that gap.
        """
        tied_vector = [1.0, 0.0, 0.0]
        items = [
            ("connector-mid-5", "connector", "mid", tied_vector),
            ("connector-mid-3", "connector", "mid", tied_vector),
            ("connector-mid-1", "connector", "mid", tied_vector),
            ("connector-mid-4", "connector", "mid", tied_vector),
            ("connector-mid-2", "connector", "mid", tied_vector),
        ]
        store_dir = _build_store_with_known_vectors(tmp_path, items)

        import action_item_store
        monkeypatch.setattr(
            action_item_store, "ONNXMiniLM_L6_V2",
            lambda: _FixedVectorEmbedding(tied_vector),
        )

        score_result = _valid_score_result(winner="connector", tier="mid")
        results = retrieve_for_score(store_dir, score_result)

        assert [r.source_id for r in results] == [
            "connector-mid-1", "connector-mid-2", "connector-mid-3",
        ]


# ---------------------------------------------------------------------------
# Test quality review: the existing personalization test (below, AC4)
# changes three secondary totals at once, so it can't prove the phrase
# actually reflects each one independently — a build that only looked at
# one of the three could still pass it. These call the phrase-building
# step directly, varying one total at a time.
# ---------------------------------------------------------------------------

class TestPhraseRespondsToEachTotalIndependently:
    def test_changing_cultivator_alone_changes_the_phrase(self):
        """
        Deleting this test removes the only check that the ranking phrase
        reflects the cultivator total specifically, as opposed to a build
        that silently drops it while still responding to the other two
        non-winning totals (which the existing end-to-end fixture-pair
        test couldn't tell apart from correct behavior).
        """
        from action_item_store import _score_phrase

        base = _score_phrase(_valid_score_result(
            connector=24, cultivator=6, opportunitySeeker=6, communityBuilder=6))
        changed = _score_phrase(_valid_score_result(
            connector=24, cultivator=22, opportunitySeeker=6, communityBuilder=6))
        assert base != changed

    def test_changing_opportunity_seeker_alone_changes_the_phrase(self):
        """
        Deleting this test removes the equivalent check for the
        opportunitySeeker total specifically.
        """
        from action_item_store import _score_phrase

        base = _score_phrase(_valid_score_result(
            connector=24, cultivator=6, opportunitySeeker=6, communityBuilder=6))
        changed = _score_phrase(_valid_score_result(
            connector=24, cultivator=6, opportunitySeeker=22, communityBuilder=6))
        assert base != changed

    def test_changing_community_builder_alone_changes_the_phrase(self):
        """
        Deleting this test removes the equivalent check for the
        communityBuilder total specifically.
        """
        from action_item_store import _score_phrase

        base = _score_phrase(_valid_score_result(
            connector=24, cultivator=6, opportunitySeeker=6, communityBuilder=6))
        changed = _score_phrase(_valid_score_result(
            connector=24, cultivator=6, opportunitySeeker=6, communityBuilder=22))
        assert base != changed


# ---------------------------------------------------------------------------
# AC1 + AC2: for each of the 5 sample answer sets, exactly 3 chunks come
# back, all tagged with that person's winning style/tier, each traceable to
# the item #2 store by its source ID.
# ---------------------------------------------------------------------------

class TestFilteredToWinningBucket:
    def setup_method(self):
        _require_real_html()

    @pytest.fixture(scope="class")
    def built_store(self, tmp_path_factory):
        _require_real_html()
        store_dir = tmp_path_factory.mktemp("store3") / "store"
        build_store(REAL_HTML_PATH, store_dir)
        return store_dir

    @pytest.mark.parametrize("fixture_name", SAMPLE_FIXTURE_NAMES)
    def test_returns_exactly_three_chunks_from_the_winning_bucket(
        self, built_store, fixture_name
    ):
        """
        Deleting this test removes the suite's only check against the
        spec's central promise: 3 results, all from the person's own
        winning style-and-tier bucket. Without it, a build that returns
        the wrong bucket's chunks (or the wrong count) would pass
        unnoticed.
        """
        score_result = _score_for(fixture_name)
        results = retrieve_for_score(built_store, score_result)
        assert len(results) == 3
        for r in results:
            assert r.style == score_result["winner"]
            assert r.tier == score_result["tier"]

    @pytest.mark.parametrize("fixture_name", SAMPLE_FIXTURE_NAMES)
    def test_every_result_has_a_traceable_unique_source_id(
        self, built_store, fixture_name
    ):
        """
        Deleting this test removes the check that each returned chunk
        actually names a real, unique item in the item #2 store — as
        opposed to a made-up or duplicated ID that happens to carry the
        right style/tier labels.
        """
        score_result = _score_for(fixture_name)
        results = retrieve_for_score(built_store, score_result)

        ids = [r.source_id for r in results]
        assert len(ids) == len(set(ids)), "returned source IDs must be unique"

        for r in results:
            stored = get_item(built_store, r.source_id)
            assert stored.text == r.text
            assert stored.style == score_result["winner"]
            assert stored.tier == score_result["tier"]
            assert r.source_id.startswith(f"{score_result['winner']}-{score_result['tier']}-")


# ---------------------------------------------------------------------------
# AC3: scoped to the matching bucket *before* ranking — proven by a case
# where the correct bucket's best match is not in the whole-library top 3,
# yet still comes back correctly once scoped.
# ---------------------------------------------------------------------------

class TestScopedBeforeRanking:
    def test_correct_bucket_wins_even_when_absent_from_whole_library_top_three(
        self, tmp_path
    ):
        """
        Deleting this test removes the only proof that retrieval filters
        to style+tier before ranking, rather than ranking the whole
        60-item library and checking afterward that the top 3 happen to
        match. With every item embedding identically (same text), every
        item is exactly equidistant from any query — so an unfiltered
        top-3 falls back entirely to the alphabetical tie-break, which
        lands on communityBuilder-high (confirmed below), never on
        connector-mid. A build that ranks first and filters after would
        return communityBuilder-high chunks here; only a build that
        filters first can return connector-mid chunks, which the spec
        requires.
        """
        store_dir = _build_store_with_identical_text(tmp_path)

        # Sanity check: confirm the tie-break behavior this test leans on
        # (already covered independently by item #2's own suite).
        from action_item_store import query_store

        whole_library_top3 = query_store(
            store_dir, "the exact same action item text", n_results=3
        )
        whole_library_ids = {r.source_id for r in whole_library_top3}
        assert not any(sid.startswith("connector-mid-") for sid in whole_library_ids), (
            "test setup assumption broke: connector-mid must NOT be in the "
            "unfiltered top 3, or this test cannot prove scoping"
        )

        score_result = _valid_score_result(winner="connector", tier="mid")
        results = retrieve_for_score(store_dir, score_result)

        # Exact IDs and order, not just the right prefix: all 5 items in
        # this bucket are tied at the same distance, so the alphabetical
        # tie-break must pick connector-mid-1/2/3 specifically.
        assert [r.source_id for r in results] == [
            "connector-mid-1", "connector-mid-2", "connector-mid-3",
        ]


# ---------------------------------------------------------------------------
# AC4: for two sample sets sharing a winning style+tier but differing in
# their other three totals, the top-ranked chunk differs.
# ---------------------------------------------------------------------------

class TestRankingRespondsToFullScorePattern:
    def setup_method(self):
        _require_real_html()

    def test_same_bucket_different_secondary_totals_yield_different_top_result(
        self, tmp_path
    ):
        """
        Deleting this test removes the suite's only check that ranking
        within the bucket actually looks at all four totals, not just the
        winning one. `connector_mid` and `mixed_realistic` share the same
        winner (connector) and tier (mid) but have meaningfully different
        cultivator/opportunitySeeker/communityBuilder totals (spec Notes).
        A build that ignores the three non-winning totals (e.g. always
        returning the bucket's first item, or ranking by winner total
        alone) would return the same top result for both and this test
        would catch it.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)

        connector_mid_score = _score_for("connector_mid")
        mixed_realistic_score = _score_for("mixed_realistic")
        assert connector_mid_score["winner"] == mixed_realistic_score["winner"] == "connector"
        assert connector_mid_score["tier"] == mixed_realistic_score["tier"] == "mid"

        connector_mid_results = retrieve_for_score(store_dir, connector_mid_score)
        mixed_realistic_results = retrieve_for_score(store_dir, mixed_realistic_score)

        assert connector_mid_results[0].source_id != mixed_realistic_results[0].source_id


# ---------------------------------------------------------------------------
# Determinism and tie-breaking (spec question round, #8): identical input
# against an unchanged store always returns identical results in identical
# order.
# ---------------------------------------------------------------------------

class TestDeterminism:
    def setup_method(self):
        _require_real_html()

    def test_repeated_calls_with_same_input_return_identical_order(self, tmp_path):
        """
        Deleting this test removes the only check that retrieval is
        stable rather than returning a different-but-equally-valid set of
        3 chunks (or the same 3 in a different order) on each call, which
        would make results impossible to reason about or test reliably
        downstream.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        score_result = _score_for("connector_mid")

        first = [r.source_id for r in retrieve_for_score(store_dir, score_result)]
        second = [r.source_id for r in retrieve_for_score(store_dir, score_result)]
        assert first == second


# ---------------------------------------------------------------------------
# Spec question round #2 and #6: the input-validation contract for
# score_result. Each invalid case must raise RetrievalError naming what was
# wrong, never the bad value itself.
# ---------------------------------------------------------------------------

class TestInputValidation:
    @pytest.fixture
    def store_dir(self, tmp_path):
        return _build_minimal_valid_store(tmp_path)

    def test_non_dict_input_is_rejected(self, store_dir):
        """
        Deleting this test removes coverage for the question round's
        requirement that only the exact built-in dict type is accepted
        (#2) — e.g. a list or a custom mapping-like object must not be
        silently accepted.
        """
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, ["not", "a", "dict"])

    def test_dict_subclass_is_rejected(self, store_dir):
        """
        Deleting this test removes coverage for the "no subclasses" half
        of question round answer #2, matching the same exact-type
        strictness item #18b already established for scoring input.
        """
        class SneakyDict(dict):
            pass

        score_result = SneakyDict(_valid_score_result())
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    @pytest.mark.parametrize(
        "missing_key", ["connector", "cultivator", "opportunitySeeker",
                        "communityBuilder", "overall", "winner", "tier"]
    )
    def test_missing_required_key_is_rejected(self, store_dir, missing_key):
        """
        Deleting this test removes coverage for each of the 7 required
        keys named in question round answer #2 — without it, a build that
        only checks for some of the keys (e.g. forgets to require
        `overall`) would go unnoticed.
        """
        score_result = _valid_score_result()
        del score_result[missing_key]
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    def test_unexpected_extra_key_is_rejected(self, store_dir):
        """
        Deleting this test removes coverage for question round answer
        #2's "unexpected extra keys" rejection — a build that silently
        ignores extra keys instead of rejecting them would pass without
        this test.
        """
        score_result = _valid_score_result(bogus_key="unexpected")
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    @pytest.mark.parametrize("bad_total", ["12", 12.5, True, None])
    def test_non_int_style_total_is_rejected(self, store_dir, bad_total):
        """
        Deleting this test removes coverage for the "as ints" requirement
        in question round answer #2. Includes True/False (booleans are a
        subclass of int in Python) to match the same subclass-rejection
        convention item #18b already established for the scorer's own
        input, so a boolean can't sneak through as a style total.
        """
        score_result = _valid_score_result(connector=bad_total)
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    def test_unknown_winner_name_is_rejected(self, store_dir):
        """
        Deleting this test removes coverage for question round answer #6:
        only the four exact style names already used throughout the
        codebase are accepted for `winner`, nothing else.
        """
        score_result = _valid_score_result(winner="not_a_real_style")
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    def test_mistyped_casing_in_winner_name_is_rejected(self, store_dir):
        """
        Deleting this test removes coverage for the "no normalization of
        casing" half of question round answer #6 — a near-miss like
        "Connector" must be rejected, not silently matched.
        """
        score_result = _valid_score_result(winner="Connector")
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    def test_unknown_tier_name_is_rejected(self, store_dir):
        """
        Deleting this test removes coverage for question round answer #6
        applied to `tier`: only "high"/"mid"/"low" are accepted.
        """
        score_result = _valid_score_result(tier="extreme")
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)

    def test_error_message_names_the_type_not_the_value(self, store_dir):
        """
        Deleting this test removes the check that error messages describe
        *what kind* of problem occurred without echoing the bad value
        itself back (question round answer #6's "naming the received
        type, never the value").
        """
        score_result = _valid_score_result(connector="eighteen")
        with pytest.raises(RetrievalError) as excinfo:
            retrieve_for_score(store_dir, score_result)
        assert "eighteen" not in str(excinfo.value)


# ---------------------------------------------------------------------------
# Spec question round #4 and #9: a bucket that doesn't have 3 healthy
# chunks, or a store with bad chunk metadata, is a store-integrity problem,
# not something retrieval recovers from gracefully.
# ---------------------------------------------------------------------------

class TestUnhealthyBucketIsAnError:
    def test_bucket_with_fewer_than_three_items_raises(self, tmp_path):
        """
        Deleting this test removes coverage for question round answer #4:
        a bucket that doesn't have the 5 items item #2's build normally
        guarantees must raise an error rather than silently returning
        fewer than 3 results. Builds the store directly against the
        collection (bypassing build_store's own validation, which would
        otherwise refuse to create this store at all) to simulate a
        store that became damaged after a healthy build.
        """
        store_dir = _build_minimal_valid_store(tmp_path)

        from chromadb import PersistentClient
        client = PersistentClient(path=str(store_dir))
        collection = client.get_collection("action_items")
        # Remove all but one of the connector-mid items, simulating
        # corruption rather than a bad initial build.
        collection.delete(ids=["connector-mid-2", "connector-mid-3",
                               "connector-mid-4", "connector-mid-5"])
        client.close()

        score_result = _valid_score_result(winner="connector", tier="mid")
        with pytest.raises(RetrievalError):
            retrieve_for_score(store_dir, score_result)


# ---------------------------------------------------------------------------
# Spec question round #5: a missing or model-mismatched store reuses item
# #2's existing QueryError exactly, rather than a new error type.
# ---------------------------------------------------------------------------

class TestReusesExistingStoreErrorHandling:
    def test_missing_store_raises_the_existing_query_error(self, tmp_path):
        """
        Deleting this test removes coverage for question round answer #5:
        a missing store must fail the same way item #2's query_store
        already fails for a missing store (QueryError), not a new or
        different error type that callers would need to handle
        separately.
        """
        missing_store_dir = tmp_path / "does_not_exist"
        score_result = _valid_score_result()
        with pytest.raises(QueryError):
            retrieve_for_score(missing_store_dir, score_result)

    def test_mismatched_embedding_model_raises_the_existing_query_error(self, tmp_path):
        """
        Deleting this test removes coverage for the embedding-model half
        of question round answer #5 — a model mismatch must raise the
        same QueryError item #2's query_store already raises, naming both
        models, not a new error path specific to this item.
        """
        store_dir = _build_minimal_valid_store(tmp_path)
        score_result = _valid_score_result()
        with pytest.raises(QueryError) as excinfo:
            retrieve_for_score(store_dir, score_result, embedding_model=ALT_EMBEDDING_MODEL)
        message = str(excinfo.value)
        assert DEFAULT_EMBEDDING_MODEL in message
        assert ALT_EMBEDDING_MODEL in message


# ---------------------------------------------------------------------------
# "What it does NOT do": item #2's own unfiltered query_store must keep
# working unchanged. This is a guard, not new coverage — item #2's suite
# owns the real assertions.
# ---------------------------------------------------------------------------

def test_query_store_still_works_unfiltered(tmp_path):
    """
    Deleting this test removes the one guard in THIS suite that a change
    made to support filtered retrieval didn't also change query_store's
    own signature or behavior. Item #2's own test suite is the real
    coverage for query_store; this just confirms the two coexist.
    """
    from action_item_store import query_store

    store_dir = _build_minimal_valid_store(tmp_path)
    results = query_store(store_dir, "a valid unfiltered query", n_results=3)
    assert len(results) == 3
