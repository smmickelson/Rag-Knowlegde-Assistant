"""
Tests for backlog item #2b — "Embed the new four-layer content library"
(specs/2b-embed-content-library-v2.md, status: questioned)

These tests are written against the spec only. No implementation exists yet,
so every test below is expected to FAIL (most with a collection-time
ImportError) until the feature is built. That failure is the point: it
proves the suite is actually exercising the acceptance criteria rather than
passing by accident.

ASSUMED INTERFACE
-----------------
The spec does not name a module, so this suite assumes a module called
`content_library_store` (mirroring `action_item_store`) exposing:

    build_store(knowledge_base_dir: Path | str, store_dir: Path | str,
                embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> None
        Reads every markdown file in `knowledge_base_dir` (2 philosophy,
        8 archetype, 30 behavior), parses its YAML frontmatter as metadata,
        strips the frontmatter from the body, embeds each body, and writes a
        fresh Chroma store at `store_dir`. Raises BuildError (clearing any
        partial output and leaving the previous store, if any, untouched) on
        any malformed input.

    count_items(store_dir) -> int
    list_source_ids(store_dir) -> list[str]
    get_item(store_dir, source_id) -> ItemRecord
        ItemRecord has .source_id .layer .metadata .text
        (.metadata is the parsed frontmatter dict, including `layer`.)
    get_embedding(store_dir, source_id) -> Sequence[float]
    query_store(store_dir, text, n_results=3,
                embedding_model=DEFAULT_EMBEDDING_MODEL) -> list[QueryResult]
        QueryResult has .source_id .text .layer .metadata .distance
    get_store_embedding_model(store_dir) -> str

    DEFAULT_EMBEDDING_MODEL: str
    class BuildError(Exception): ...
    class QueryError(Exception): ...

If the real module/function names differ, update the single import block
below and the two constants (REAL_KB_PATH, ALT_EMBEDDING_MODEL) — the test
bodies encode the acceptance criteria, not this module's naming choices.

WHAT THIS SUITE DOES NOT DO
---------------------------
It does not re-implement the chunker/embedder. The helpers `_split_md` and
`_expected_chunks` are test-oracle code: they independently split a file's
frontmatter from its body and list which chunks a valid `knowledge_base/`
should contain, giving AC2/AC3/AC4 a ground truth that was not produced by
the feature under test. They perform no embedding and no storage.

Most tests build a small synthetic `knowledge_base/` in a temp folder so
they run without the real resource repo. A few that depend on the real
content skip when `knowledge_base/` is absent, exactly as item #2's tests
skip without the real HTML.
"""

import json
import os
import shutil
import socket
from pathlib import Path

import pytest
import yaml

# --- Adjust these lines if the real module/location differs ---------------
from content_library_store import (  # noqa: E402
    DEFAULT_EMBEDDING_MODEL,
    BuildError,
    QueryError,
    build_store,
    count_items,
    get_embedding,
    get_item,
    get_store_embedding_model,
    list_source_ids,
    query_store,
)

REAL_KB_PATH = Path(
    os.environ.get(
        "KNOWLEDGE_BASE_PATH",
        "werkitgirls-resources/knowledge_base",
    )
)
ALT_EMBEDDING_MODEL = "a-different-embedding-model-than-the-store-used"

PHILOSOPHY_COUNT = 2
ARCHETYPE_COUNT = 8
BEHAVIOR_COUNT = 30
TOTAL_COUNT = 40

ARCHETYPES = ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
ARCHETYPE_PIECES = ["narrative", "superpower"]
BEHAVIOR_MODES = ["building", "recovering"]
QUESTIONS = list(range(1, 16))

# One distinctive phrase per layer, used by the query tests. Each appears in
# exactly one body across the synthetic library.
PHILOSOPHY_QUERY = "networking is a practice not a performance"
ARCHETYPE_QUERY = "the connector makes introductions happen"
BEHAVIOR_QUERY = "follow up within 48 hours"


def _require_real_knowledge_base():
    if not REAL_KB_PATH.is_dir():
        pytest.skip(
            f"Real knowledge_base folder not found at {REAL_KB_PATH}. Set "
            "KNOWLEDGE_BASE_PATH to point at the real knowledge_base/ from "
            "werkitgirls-resources."
        )


# ---------------------------------------------------------------------------
# Test-oracle helpers (independent of the implementation)
# ---------------------------------------------------------------------------

def _split_md(text: str):
    """Independently split a markdown file into (frontmatter, body).

    The file starts with a line ``---``, then YAML frontmatter, then a
    closing ``---``, then the body. Line endings are normalized to ``\\n``
    and the body is stripped of leading/trailing whitespace, matching the
    spec's body contract. This is ground truth for the build.
    """
    lines = text.replace("\r\n", "\n").split("\n")
    if not lines or lines[0].strip() != "---":
        return None, None
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        return None, None
    frontmatter = "\n".join(lines[1:close])
    body = "\n".join(lines[close + 1:]).strip()
    return frontmatter, body


def _expected_chunks(kb_dir: Path) -> dict:
    """Oracle: map {source_id: (layer, metadata, body)} for a valid library.

    Independently lists the ``.md`` files and parses each one's frontmatter
    and body. Used as ground truth for counts, metadata, and exact-body
    checks, so the tests never trust whatever the build happens to produce.
    """
    out = {}
    for path in sorted(kb_dir.iterdir()):
        if path.is_file() and path.suffix == ".md":
            fm, body = _split_md(path.read_text(encoding="utf-8"))
            metadata = yaml.safe_load(fm) or {}
            out[path.stem] = (metadata.get("layer"), metadata, body)
    return out


# ---------------------------------------------------------------------------
# Synthetic knowledge_base builder (fixture data, not the implementation)
# ---------------------------------------------------------------------------

def _write_md(directory: Path, filename: str, frontmatter: dict, body: str):
    """Write one markdown file with YAML frontmatter followed by a body."""
    fm_text = yaml.safe_dump(frontmatter, sort_keys=False).rstrip()
    text = "---\n" + fm_text + "\n---\n" + body + "\n"
    (directory / filename).write_text(text, encoding="utf-8")


def _build_valid_knowledge_base(tmp_path: Path) -> Path:
    """Create the exact 40-file library in ``tmp_path/knowledge_base``.

    2 philosophy, 8 archetype (4 archetypes x 2 pieces), 30 behavior
    (15 questions x 2 modes). Each file's frontmatter agrees with what its
    filename implies, per the spec's exact-input contract.
    """
    kb = tmp_path / "knowledge_base"
    kb.mkdir()

    _write_md(kb, "philosophy_connection.md",
              {"layer": "philosophy"},
              "Connection is the currency of a real career. " + PHILOSOPHY_QUERY + ".")
    _write_md(kb, "philosophy_growth.md",
              {"layer": "philosophy"},
              "Growth comes from showing up consistently over time.")

    for archetype in ARCHETYPES:
        for piece in ARCHETYPE_PIECES:
            filename = f"archetype_{archetype}_{piece}.md"
            body = (
                f"A {piece} for the {archetype} archetype. "
                f"{ARCHETYPE_QUERY if archetype == 'connector' and piece == 'narrative' else ''}"
            ).strip()
            _write_md(kb, filename,
                      {"layer": "archetype", "archetype": archetype, "piece": piece},
                      body)

    for q in QUESTIONS:
        for mode in BEHAVIOR_MODES:
            slug = f"q{q:02d}_mode_{mode}"
            filename = f"behavior_{slug}.md"
            body = (
                f"Behavior for question {q} in {mode} mode. "
                f"{BEHAVIOR_QUERY if q == 14 and mode == 'building' else ''}"
            ).strip()
            _write_md(kb, filename,
                      {"layer": "behavior", "question": q, "slug": slug,
                       "mode": mode, "archetypes": ["connector", "cultivator"]},
                      body)

    return kb


def _build_store_from(tmp_path, kb_dir) -> Path:
    store_dir = tmp_path / "store"
    build_store(kb_dir, store_dir)
    return store_dir


def _assert_no_store_left(store_dir):
    """A rejected build must leave nothing behind: either the store path was
    never created, or (if it exists) it holds zero chunks."""
    assert not Path(store_dir).exists() or count_items(store_dir) == 0


def _assert_store_unchanged(store_dir, before_ids, before_count):
    """A rejected build must leave a previous good store exactly as it was."""
    assert sorted(list_source_ids(store_dir)) == before_ids
    assert count_items(store_dir) == before_count


# ---------------------------------------------------------------------------
# AC1: exactly 40 chunks (2/8/30), unique IDs, non-empty text, valid
# frontmatter metadata; wrong count / missing or malformed frontmatter /
# empty body stops the run with a named error and stores nothing.
# ---------------------------------------------------------------------------

class TestCountAndShape:
    def test_build_stores_exactly_forty_chunks(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        assert count_items(store_dir) == TOTAL_COUNT

    def test_build_stores_expected_layer_counts(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        ids = list_source_ids(store_dir)
        layers = [get_item(store_dir, sid).layer for sid in ids]
        assert layers.count("philosophy") == PHILOSOPHY_COUNT
        assert layers.count("archetype") == ARCHETYPE_COUNT
        assert layers.count("behavior") == BEHAVIOR_COUNT

    def test_build_item_source_ids_are_unique(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        ids = list_source_ids(store_dir)
        assert len(ids) == len(set(ids))

    def test_build_item_source_ids_match_filenames(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        expected = {path.stem for path in kb.iterdir() if path.suffix == ".md"}
        assert set(list_source_ids(store_dir)) == expected

    def test_build_item_text_is_never_empty(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        for sid in list_source_ids(store_dir):
            assert get_item(store_dir, sid).text.strip() != ""

    def test_build_rejects_wrong_total_count(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        (kb / "philosophy_extra.md").write_text(
            "---\nlayer: philosophy\n---\nextra\n", encoding="utf-8")
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_no_store_left(store_dir)

    def test_build_rejects_wrong_layer_count(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        (kb / "archetype_extra.md").unlink()  # 7 archetypes, not 8
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_no_store_left(store_dir)

    def test_rejected_build_does_not_disturb_a_previous_good_store(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        before_ids = sorted(list_source_ids(store_dir))
        before_count = count_items(store_dir)

        (kb / "philosophy_extra.md").write_text(
            "---\nlayer: philosophy\n---\nextra\n", encoding="utf-8")
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_store_unchanged(store_dir, before_ids, before_count)


class TestMalformedFrontmatterAndBody:
    def _build_with_replacement(self, tmp_path, filename, text):
        kb = _build_valid_knowledge_base(tmp_path)
        (kb / filename).write_text(text, encoding="utf-8")
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_no_store_left(store_dir)

    def _build_with_replacement_over_previous_store(self, tmp_path, filename, text):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        before_ids = sorted(list_source_ids(store_dir))
        before_count = count_items(store_dir)

        (kb / filename).write_text(text, encoding="utf-8")
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_store_unchanged(store_dir, before_ids, before_count)

    def test_rejects_missing_frontmatter_field(self, tmp_path):
        # philosophy file missing the `layer` field
        self._build_with_replacement(
            tmp_path, "philosophy_connection.md",
            "---\nnotlayer: x\n---\nbody here\n")

    def test_rejects_malformed_yaml(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_growth.md",
            "---\nlayer: [unclosed\n---\nbody here\n")

    def test_rejects_unknown_frontmatter_field(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_connection.md",
            "---\nlayer: philosophy\nbogus: 1\n---\nbody here\n")

    def test_rejects_duplicate_frontmatter_key(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_connection.md",
            "---\nlayer: philosophy\nlayer: philosophy\n---\nbody here\n")

    def test_rejects_custom_yaml_tag(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_growth.md",
            "---\nlayer: !custom philosophy\n---\nbody here\n")

    def test_rejects_string_question_value(self, tmp_path):
        # behavior_q14_building.md must have int question 14, not the string "14"
        self._build_with_replacement(
            tmp_path, "behavior_q14_mode_building.md",
            "---\nlayer: behavior\nquestion: \"14\"\nslug: q14_mode_building\n"
            "mode: building\narchetypes:\n  - connector\n---\nbody here\n")

    def test_rejects_repeated_name_in_archetypes(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "behavior_q14_mode_building.md",
            "---\nlayer: behavior\nquestion: 14\nslug: q14_mode_building\n"
            "mode: building\narchetypes:\n  - connector\n  - connector\n"
            "---\nbody here\n")

    def test_rejects_empty_body(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_connection.md",
            "---\nlayer: philosophy\n---\n")

    def test_rejects_whitespace_only_body(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_growth.md",
            "---\nlayer: philosophy\n---\n   \n\t\n")

    def test_rejects_missing_closing_frontmatter(self, tmp_path):
        self._build_with_replacement(
            tmp_path, "philosophy_connection.md",
            "---\nlayer: philosophy\nbody never separated\n")

    @pytest.mark.parametrize(
        "filename,text",
        [
            ("philosophy_connection.md",
             "---\nnotlayer: x\n---\nbody here\n"),
            ("philosophy_growth.md",
             "---\nlayer: [unclosed\n---\nbody here\n"),
            ("philosophy_connection.md",
             "---\nlayer: philosophy\nbogus: 1\n---\nbody here\n"),
            ("philosophy_connection.md",
             "---\nlayer: philosophy\nlayer: philosophy\n---\nbody here\n"),
            ("philosophy_growth.md",
             "---\nlayer: !custom philosophy\n---\nbody here\n"),
            ("behavior_q14_mode_building.md",
             "---\nlayer: behavior\nquestion: \"14\"\nslug: q14_mode_building\n"
             "mode: building\narchetypes:\n  - connector\n---\nbody here\n"),
            ("behavior_q14_mode_building.md",
             "---\nlayer: behavior\nquestion: 14\nslug: q14_mode_building\n"
             "mode: building\narchetypes:\n  - connector\n  - connector\n"
             "---\nbody here\n"),
            ("philosophy_connection.md",
             "---\nlayer: philosophy\n---\n"),
            ("philosophy_growth.md",
             "---\nlayer: philosophy\n---\n   \n\t\n"),
            ("philosophy_connection.md",
             "---\nlayer: philosophy\nbody never separated\n"),
        ],
        ids=[
            "missing-field", "malformed-yaml", "unknown-field", "duplicate-key",
            "custom-tag", "string-question", "repeated-archetype",
            "empty-body", "whitespace-body", "missing-close",
        ],
    )
    def test_malformed_rebuild_leaves_previous_good_store_unchanged(
        self, tmp_path, filename, text
    ):
        self._build_with_replacement_over_previous_store(tmp_path, filename, text)


class TestFilenameFrontmatterAgreement:
    def test_rejects_mismatched_question_number(self, tmp_path):
        # Filename implies question 4; frontmatter says 5.
        kb = _build_valid_knowledge_base(tmp_path)
        fm = {"layer": "behavior", "question": 5, "slug": "q04_mode_building",
              "mode": "building", "archetypes": ["connector"]}
        fm_text = yaml.safe_dump(fm, sort_keys=False).rstrip()
        (kb / "behavior_q04_mode_building.md").write_text(
            "---\n" + fm_text + "\n---\nbody\n", encoding="utf-8")
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_no_store_left(store_dir)

    def test_rejects_mismatched_mode(self, tmp_path):
        # Filename implies building; frontmatter says recovering.
        kb = _build_valid_knowledge_base(tmp_path)
        fm = {"layer": "behavior", "question": 14, "slug": "q14_mode_building",
              "mode": "recovering", "archetypes": ["connector"]}
        fm_text = yaml.safe_dump(fm, sort_keys=False).rstrip()
        (kb / "behavior_q14_mode_building.md").write_text(
            "---\n" + fm_text + "\n---\nbody\n", encoding="utf-8")
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        _assert_no_store_left(store_dir)

    def test_rejects_unexpected_layer_file_type(self, tmp_path):
        # A .MD (uppercase) file must not count toward the 40 and the build
        # must still succeed with exactly the 40 lowercase .md files.
        kb = _build_valid_knowledge_base(tmp_path)
        (kb / "NOT_A_CHUNK.MD").write_text(
            "---\nlayer: philosophy\n---\nignored\n", encoding="utf-8")
        store_dir = _build_store_from(tmp_path, kb)
        assert count_items(store_dir) == TOTAL_COUNT
        assert "NOT_A_CHUNK" not in list_source_ids(store_dir)


# ---------------------------------------------------------------------------
# AC2: stored text matches the file's body exactly (frontmatter stripped,
# nothing else altered).
# ---------------------------------------------------------------------------

class TestStoredTextMatchesBody:
    def test_every_stored_chunk_matches_decoded_body_exactly(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        expected = _expected_chunks(kb)
        store_dir = _build_store_from(tmp_path, kb)

        assert set(list_source_ids(store_dir)) == set(expected.keys())
        for sid, (layer, metadata, body) in expected.items():
            stored = get_item(store_dir, sid)
            assert stored.text == body, f"mismatch for {sid}"


# ---------------------------------------------------------------------------
# AC3: one embedding per chunk, each lookup-able by source ID, with the
# frontmatter fields stored and retrievable as metadata.
# ---------------------------------------------------------------------------

class TestEmbeddingsAndMetadata:
    def test_every_chunk_has_exactly_one_embedding(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        for sid in list_source_ids(store_dir):
            vector = get_embedding(store_dir, sid)
            assert vector is not None
            assert len(vector) > 0

    def test_chunk_is_lookupable_by_source_id(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        item = get_item(store_dir, "philosophy_connection")
        assert item.source_id == "philosophy_connection"
        assert item.layer == "philosophy"

    def test_behavior_metadata_is_stored_and_retrievable(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        item = get_item(store_dir, "behavior_q14_mode_building")
        assert item.metadata["question"] == 14
        assert item.metadata["mode"] == "building"
        assert isinstance(item.metadata["archetypes"], list)

    def test_archetype_metadata_is_stored_and_retrievable(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        item = get_item(store_dir, "archetype_connector_narrative")
        assert item.metadata["archetype"] == "connector"
        assert item.metadata["piece"] == "narrative"


# ---------------------------------------------------------------------------
# AC4: a known phrase from each of the three layers returns the expected
# chunk first.
# ---------------------------------------------------------------------------

class TestKnownPhrasesReturnExpectedTopResult:
    @pytest.mark.parametrize(
        "phrase,expected_id",
        [
            (PHILOSOPHY_QUERY, "philosophy_connection"),
            (ARCHETYPE_QUERY, "archetype_connector_narrative"),
            (BEHAVIOR_QUERY, "behavior_q14_mode_building"),
        ],
        ids=["philosophy", "archetype", "behavior"],
    )
    def test_phrase_returns_expected_chunk_first(self, tmp_path, phrase, expected_id):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        results = query_store(store_dir, phrase, n_results=3)
        assert results, f"no results for phrase {phrase!r}"
        assert results[0].source_id == expected_id


# ---------------------------------------------------------------------------
# AC5: rebuilds are idempotent and deterministic; a failed run doesn't
# disturb the previous good store.
# ---------------------------------------------------------------------------

class TestRebuildBehavior:
    def test_rebuilding_twice_yields_same_forty_chunks_with_no_leftovers(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        first_ids = sorted(list_source_ids(store_dir))

        build_store(kb, store_dir)
        second_ids = sorted(list_source_ids(store_dir))

        assert first_ids == second_ids
        assert len(second_ids) == TOTAL_COUNT
        assert count_items(store_dir) == TOTAL_COUNT

    def test_a_failed_rebuild_leaves_the_previous_store_unchanged(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        before_ids = sorted(list_source_ids(store_dir))

        (kb / "philosophy_connection.md").write_text(
            "---\nlayer: [broken\n---\nbad\n", encoding="utf-8")
        with pytest.raises(BuildError):
            build_store(kb, store_dir)

        after_ids = sorted(list_source_ids(store_dir))
        assert after_ids == before_ids
        assert count_items(store_dir) == TOTAL_COUNT

    def test_a_failure_during_replacement_leaves_the_previous_store_unchanged(
        self, tmp_path, monkeypatch
    ):
        import content_library_store

        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        before_ids = sorted(list_source_ids(store_dir))

        real_replace = os.replace

        def failing_replace(src, dst):
            if Path(dst) == store_dir and Path(src).name.startswith("tmp"):
                raise OSError("simulated failure during store replacement")
            return real_replace(src, dst)

        monkeypatch.setattr(content_library_store.os, "replace", failing_replace)
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        monkeypatch.setattr(content_library_store.os, "replace", real_replace)

        after_ids = sorted(list_source_ids(store_dir))
        assert after_ids == before_ids
        assert count_items(store_dir) == TOTAL_COUNT
        assert not (tmp_path / "store.old").exists()

    def test_first_build_failure_leaves_store_path_absent(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        (kb / "philosophy_growth.md").write_text("no frontmatter at all\n", encoding="utf-8")
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(kb, store_dir)
        assert not store_dir.exists() or count_items(store_dir) == 0


# ---------------------------------------------------------------------------
# AC6: this item's store lives separate from the existing action_items store,
# and building it never modifies, reads from, or deletes that store.
# ---------------------------------------------------------------------------

class TestSeparateFromActionItemsStore:
    def test_content_store_is_distinct_and_action_items_store_is_untouched(
        self, tmp_path
    ):
        import action_item_store

        # Build the item #2 action-items store first, in its own directory.
        kb = _build_valid_knowledge_base(tmp_path)
        action_items_dir = tmp_path / "action_items_store"
        # A minimal valid HTML for item #2's build.
        items = '["a", "b", "c", "d", "e"]'
        tiers = "{" + ", ".join(
            f'"{t}": {items}' for t in ["high", "mid", "low"]) + "}"
        profiles = "{" + ", ".join(
            f'"{s}": {{"actions": {tiers}}}' for s in
            ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]) + "}"
        html_path = tmp_path / "valid.html"
        html_path.write_text(
            f"<html><body><script>var profiles = {profiles};</script></body></html>",
            encoding="utf-8",
        )
        action_item_store.build_store(html_path, action_items_dir)
        action_before = sorted(action_item_store.list_source_ids(action_items_dir))

        # Build the content-library store into a separate directory.
        content_dir = _build_store_from(tmp_path, kb)

        # The action-items store is completely unchanged.
        action_after = sorted(action_item_store.list_source_ids(action_items_dir))
        assert action_after == action_before
        assert action_item_store.count_items(action_items_dir) == 60

        # The two stores are genuinely distinct.
        assert set(list_source_ids(content_dir)) != set(action_after)
        assert count_items(content_dir) == TOTAL_COUNT


# ---------------------------------------------------------------------------
# AC7: query validation — empty/whitespace, >500 chars, exactly 3 results,
# and cross-model mismatch.
# ---------------------------------------------------------------------------

class TestQueryValidation:
    def test_empty_query_raises_a_clear_error(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(QueryError):
            query_store(store_dir, "")

    def test_whitespace_only_query_raises_a_clear_error(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(QueryError):
            query_store(store_dir, "   \n\t  ")

    def test_query_over_500_characters_raises_a_clear_error(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(QueryError):
            query_store(store_dir, "a" * 501)

    def test_query_at_exactly_500_characters_is_accepted(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        results = query_store(store_dir, "a" * 500, n_results=3)
        assert len(results) == 3

    def test_valid_query_returns_exactly_three_results(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        results = query_store(store_dir, "building a professional network", n_results=3)
        assert len(results) == 3

    def test_query_with_mismatched_embedding_model_raises_naming_both_models(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        stored_model = get_store_embedding_model(store_dir)
        assert stored_model != ALT_EMBEDDING_MODEL

        with pytest.raises(QueryError) as excinfo:
            query_store(store_dir, "a valid query", embedding_model=ALT_EMBEDDING_MODEL)
        message = str(excinfo.value)
        assert stored_model in message
        assert ALT_EMBEDDING_MODEL in message

    def test_querying_missing_store_raises_query_error(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(QueryError):
            query_store(missing, "a valid query")

    def test_non_string_query_raises_naming_received_type(self, tmp_path):
        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        with pytest.raises(QueryError) as excinfo:
            query_store(store_dir, 12345)
        message = str(excinfo.value)
        assert "int" in message


# ---------------------------------------------------------------------------
# AC8: the suite is runnable offline (after the model's first download) with
# no credentials.
# ---------------------------------------------------------------------------

class TestOfflineAfterFirstDownload:
    def test_build_and_query_require_no_network_once_model_is_cached(self, tmp_path, monkeypatch):
        def _blocked_connect(*args, **kwargs):
            raise AssertionError(
                "Network access was attempted during build/query; the model "
                "must be loaded from local cache with no network calls."
            )

        monkeypatch.setattr(socket.socket, "connect", _blocked_connect)

        kb = _build_valid_knowledge_base(tmp_path)
        store_dir = _build_store_from(tmp_path, kb)
        results = query_store(store_dir, "building a professional network", n_results=3)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# Real-library checks: these skip unless the real knowledge_base/ is present.
# ---------------------------------------------------------------------------

class TestRealLibrary:
    def test_real_library_builds_expected_shape(self, tmp_path):
        _require_real_knowledge_base()
        store_dir = _build_store_from(tmp_path, REAL_KB_PATH)
        ids = list_source_ids(store_dir)
        layers = [get_item(store_dir, sid).layer for sid in ids]
        assert len(ids) == TOTAL_COUNT
        assert layers.count("philosophy") == PHILOSOPHY_COUNT
        assert layers.count("archetype") == ARCHETYPE_COUNT
        assert layers.count("behavior") == BEHAVIOR_COUNT

    def test_real_library_texts_match_bodies_exactly(self, tmp_path):
        _require_real_knowledge_base()
        expected = _expected_chunks(REAL_KB_PATH)
        store_dir = _build_store_from(tmp_path, REAL_KB_PATH)
        assert set(list_source_ids(store_dir)) == set(expected.keys())
        for sid, (layer, metadata, body) in expected.items():
            assert get_item(store_dir, sid).text == body, f"mismatch for {sid}"