"""
Tests for backlog item #2 — "Embed the action-item content"
(status: questioned)

These tests are written against the spec only. No implementation exists yet,
so every test below is expected to FAIL (most with a collection-time
ImportError) until the feature is built. That failure is the point: it
proves the suite is actually exercising the acceptance criteria rather than
passing by accident.

ASSUMED INTERFACE
------------------
The spec does not name any functions, modules, or files, so this suite
assumes a module called `action_item_store` exposing:

    build_store(html_path: Path | str, store_dir: Path | str,
                embedding_model: str = DEFAULT_EMBEDDING_MODEL) -> None
        Reads `html_path`, chunks+embeds the 60 action items, and writes a
        fresh Chroma store at `store_dir`. Raises BuildError (clearing any
        partial output and leaving the previous store, if any, untouched) on
        any malformed input.

    count_items(store_dir) -> int
    list_source_ids(store_dir) -> list[str]
    get_item(store_dir, source_id) -> ItemRecord  # has .style .tier .text .source_id
    get_embedding(store_dir, source_id) -> Sequence[float]
    query_store(store_dir, text, n_results=3,
                embedding_model=DEFAULT_EMBEDDING_MODEL) -> list[QueryResult]
        QueryResult has .source_id .text .style .tier .distance
    get_store_embedding_model(store_dir) -> str

    DEFAULT_EMBEDDING_MODEL: str
    class BuildError(Exception): ...
    class QueryError(Exception): ...

If the real module/function names differ, update the single import block
below and the two constants (REAL_HTML_PATH, ALT_EMBEDDING_MODEL) — the test
bodies encode the acceptance criteria, not this module's naming choices.

WHAT THIS SUITE DOES NOT DO
----------------------------
It does not re-implement the chunker/embedder. The one helper below,
`_extract_actions_independently`, is test-oracle code: it independently
re-reads `networking-assessment.html` so AC2 ("text matches the HTML
exactly") has a ground truth that was not produced by the feature under
test. It performs no chunking, no embedding, and no storage, so it is not
an implementation of this backlog item.
"""

import ast
import html
import json
import os
import re
import shutil
from pathlib import Path

import pytest

# --- Adjust these two lines if the real module/location differs ----------
from action_item_store import (  # noqa: E402
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

REAL_HTML_PATH = Path(
    os.environ.get(
        "ACTION_ITEMS_HTML_PATH",
        "werkitgirls-resources/networking-assessment.html",
    )
)
ALT_EMBEDDING_MODEL = "a-different-embedding-model-than-the-store-used"

STYLES = ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
TIERS = ["high", "mid", "low"]

TEST_PHRASES = [
    ("last 90 days", "connector-high-4"),
    ("write down one detail to remember", "cultivator-low-4"),
    ("head in your phone", "opportunitySeeker-low-2"),
    ("cross-functional project", "communityBuilder-low-3"),
]


def _require_real_html():
    if not REAL_HTML_PATH.exists():
        pytest.skip(
            f"Real HTML fixture not found at {REAL_HTML_PATH}. Set "
            "ACTION_ITEMS_HTML_PATH to point at the real "
            "networking-assessment.html from werkitgirls-resources."
        )
_STRING_LITERAL_RE = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')


def _normalize_js_object_to_python_literal(blob: str) -> str:
    """Convert JS object/array syntax toward a Python literal (quote bare
    keys, drop trailing commas, convert true/false/null), WITHOUT touching
    the contents of any quoted string. This matters because a real action
    item's text can legitimately contain the word "true", "false", or
    "null" (e.g. "it's true that..."), and those words must survive
    untouched -- only the surrounding JS object syntax should be rewritten.
    """
    pieces = _STRING_LITERAL_RE.split(blob)
    strings = _STRING_LITERAL_RE.findall(blob)
    out = []
    for i, code in enumerate(pieces):
        code = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', code)
        code = re.sub(r",\s*([}\]])", r"\1", code)
        code = re.sub(r"\btrue\b", "True", code)
        code = re.sub(r"\bfalse\b", "False", code)
        code = re.sub(r"\bnull\b", "None", code)
        out.append(code)
        if i < len(strings):
            out.append(strings[i])
    return "".join(out)

def _extract_actions_independently(html_path: Path) -> dict:
    """
    Test-oracle only: pulls the `profiles` object's actions out of the raw
    HTML text by locating the `profiles = {...}` assignment and loading it
    as JSON (after normalizing JS-object syntax to JSON), then HTML-unescapes
    every leaf string. Used only to check AC2 against ground truth that was
    not produced by the code under test.
    """
    raw = html_path.read_text(encoding="utf-8")
    match = re.search(r"profiles\s*=\s*(\{.*?\})\s*;", raw, re.DOTALL)
    if not match:
        pytest.fail("Could not locate a `profiles = {...}` object in the real HTML fixture")
    blob = match.group(1)
    # Normalize JS-object syntax toward a Python literal: quote bare keys,
    # drop trailing commas, and convert JS true/false/null to Python's
    # True/False/None. String values (single- or double-quoted, including
    # ones containing the other quote character, e.g. '"quoted" text' or
    # "it's fine") are left untouched and parsed by ast.literal_eval, which
    # — unlike json.loads — understands both quoting styles natively and
    # doesn't require re-escaping embedded quotes.
    blob = _normalize_js_object_to_python_literal(blob)
    profiles = ast.literal_eval(blob)
    out = {}
    for style, data in profiles.items():
        for tier, items in data.get("actions", {}).items():
            for i, text in enumerate(items, start=1):
                out[f"{style}-{tier}-{i}"] = html.unescape(text)
    return out


def _write_malformed_html(tmp_path: Path, profiles_js: str) -> Path:
    path = tmp_path / "malformed.html"
    path.write_text(
        f"<html><body><script>var profiles = {profiles_js};</script></body></html>",
        encoding="utf-8",
    )
    return path


def _valid_profiles_js() -> str:
    """A complete, valid profiles object: 4 styles x 3 tiers x 5 items.

    Stands in for the real HTML so a test can build a good store without
    needing the real fixture.
    """
    items = '["a", "b", "c", "d", "e"]'
    tiers = (
        '{'
        + ', '.join(f'"{tier}": {items}' for tier in ["high", "mid", "low"])
        + '}'
    )
    styles = []
    for style in ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]:
        styles.append(f'"{style}": {{"actions": {tiers}}}')
    return "{" + ", ".join(styles) + "}"


# ---------------------------------------------------------------------------
# AC1: exactly 60 items, 5 per each of the 12 style/tier pairs, non-empty
# text, unique source IDs; malformed input stops the run with a named error
# and stores nothing.
# ---------------------------------------------------------------------------

class TestCountAndShapeFromRealFile:
    def setup_method(self):
        _require_real_html()

    def test_build_stores_exactly_60_items(self, tmp_path):
        """
        Deleting this test removes the only check that the build produced
        the total item count the spec requires (60). A build that silently
        drops or duplicates items would pass every other test undetected.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        assert count_items(store_dir) == 60

    @pytest.mark.parametrize("style", STYLES)
    @pytest.mark.parametrize("tier", TIERS)
    def test_build_stores_five_items_per_style_tier_pair(self, tmp_path, style, tier):
        """
        Deleting this test removes per-(style,tier) coverage: a build that
        gets the *overall* count of 60 right by accident (e.g. 6 items in
        one pair and 4 in another) would otherwise go unnoticed.
        """
        store_dir = tmp_path / "store"
        if not store_dir.exists():
            build_store(REAL_HTML_PATH, store_dir)
        ids = [sid for sid in list_source_ids(store_dir) if sid.startswith(f"{style}-{tier}-")]
        assert len(ids) == 5

    def test_build_item_source_ids_are_unique(self, tmp_path):
        """
        Deleting this test removes the guarantee that every one of the 60
        chunks has a distinct ID. A collision would cause silent overwrite
        in the vector store (item 3's per-ID lookups would then return the
        wrong item).
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        ids = list_source_ids(store_dir)
        assert len(ids) == len(set(ids))

    def test_build_item_source_ids_match_expected_format(self, tmp_path):
        """
        Deleting this test removes the check that IDs follow the
        `style-tier-position` scheme the spec names explicitly (e.g.
        `connector-high-1`), which downstream lookups rely on.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        pattern = re.compile(r"^(connector|cultivator|opportunitySeeker|communityBuilder)-(high|mid|low)-[1-5]$")
        for sid in list_source_ids(store_dir):
            assert pattern.match(sid), f"unexpected source ID shape: {sid}"

    def test_build_item_text_is_never_empty(self, tmp_path):
        """
        Deleting this test removes the only check against the spec's
        explicit error case of an empty item being silently stored as a
        blank chunk.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        for sid in list_source_ids(store_dir):
            item = get_item(store_dir, sid)
            assert item.text.strip() != ""


class TestMalformedInputIsRejected:
    def test_build_raises_on_wrong_total_item_count(self, tmp_path):
        """
        Deleting this test removes coverage for the spec's "any other
        count" error case; a build that tolerates a missing/extra item
        would corrupt every downstream count-based assumption.
        """
        # Only 3 styles present and one tier has 4 items instead of 5.
        profiles_js = (
            '{"connector": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d"]}},'
            '"cultivator": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}}}'
        )
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(bad_html, store_dir)
        assert not store_dir.exists() or count_items(store_dir) == 0

    def test_build_raises_on_missing_style(self, tmp_path):
        """
        Deleting this test removes coverage for the "missing style" error
        case named explicitly in the acceptance criteria.
        """
        profiles_js = (
            '{"connector": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}}}'
        )
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError, match=r"(?i)style"):
            build_store(bad_html, store_dir)

    def test_build_raises_on_missing_tier(self, tmp_path):
        """
        Deleting this test removes coverage for the "missing tier" error
        case named explicitly in the acceptance criteria.
        """
        profiles_js = (
            '{"connector": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"]}},'
            '"cultivator": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}}}'
        )
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError, match=r"(?i)tier"):
            build_store(bad_html, store_dir)

    def test_build_raises_on_empty_item_text(self, tmp_path):
        """
        Deleting this test removes coverage for the "empty item" error case
        named explicitly in the acceptance criteria.
        """
        profiles_js = (
            '{"connector": {"actions": {"high": ["a","b","c","d",""],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}}}'
        )
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(bad_html, store_dir)

    def test_failed_build_stores_nothing(self, tmp_path):
        """
        Deleting this test removes the check that a rejected build leaves
        no partial/corrupt store behind, which the spec requires ("stores
        nothing").
        """
        profiles_js = '{"connector": {"actions": {"high": ["only-one-item"]}}}'
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        store_dir = tmp_path / "store"
        with pytest.raises(BuildError):
            build_store(bad_html, store_dir)
        assert not store_dir.exists() or count_items(store_dir) == 0


# ---------------------------------------------------------------------------
# Review finding (Agent 2): hostile source data must not silently pass the
# parser. These isolated cases exercise the tokenizer/parser directly (no
# real HTML, no store) and do not overlap the end-to-end tests above.
# ---------------------------------------------------------------------------

class TestParserRejectsHostileSyntax:
    """Unquoted words in value positions, bad comma grammar, and duplicate
    keys are malformed input and must raise BuildError, not be accepted."""

    def _parse(self, source):
        import action_item_store as store
        return store._Reader(store._tokenize(source)).parse()

    def test_bare_identifier_in_value_position_is_rejected(self):
        """`undefined` is not text: an unquoted word where a value belongs
        must fail instead of being stored as a string."""
        with pytest.raises(BuildError):
            self._parse('{"high": [undefined]}')

    def test_bare_identifier_as_an_item_is_rejected_by_build(self, tmp_path):
        """Same case end-to-end: the whole build must stop with BuildError
        rather than silently storing 'undefined' as an action item."""
        profiles_js = (
            '{"connector": {"actions": {"high": [undefined,"b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}},'
            '"cultivator": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}},'
            '"opportunitySeeker": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}},'
            '"communityBuilder": {"actions": {"high": ["a","b","c","d","e"],'
            '"mid": ["a","b","c","d","e"], "low": ["a","b","c","d","e"]}}}'
        )
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        with pytest.raises(BuildError):
            build_store(bad_html, tmp_path / "store")

    def test_missing_comma_between_items_is_rejected(self):
        with pytest.raises(BuildError):
            self._parse('{"high": ["a" "b"]}')

    def test_doubled_comma_is_rejected(self):
        with pytest.raises(BuildError):
            self._parse('{"high": ["a",, "b"]}')

    def test_trailing_comma_is_rejected(self):
        with pytest.raises(BuildError):
            self._parse('{"high": ["a",]}')

    def test_leading_comma_is_rejected(self):
        with pytest.raises(BuildError):
            self._parse('{"high": [, "a"]}')

    def test_duplicate_key_in_object_is_rejected(self):
        with pytest.raises(BuildError):
            self._parse('{"high": ["a"], "high": ["b"]}')


class TestParserDecodesEscapes:
    """Supported JS escapes must decode to their real characters, so hostile
    or ordinary escaped text cannot corrupt what gets stored."""

    def _parse(self, source):
        import action_item_store as store
        return store._Reader(store._tokenize(source)).parse()

    def test_unicode_escape_decodes_to_the_actual_character(self):
        result = self._parse('{"a": "\\u0041"}')
        assert result["a"] == "A"

    def test_unicode_escape_after_other_text_decodes_in_place(self):
        result = self._parse('{"a": "x\\u0041y"}')
        assert result["a"] == "xAy"

    def test_simple_escapes_still_decode(self):
        result = self._parse('{"a": "line\\nbreak\\tTab"}')
        assert result["a"] == "line\nbreak\tTab"

    def test_escaped_text_survives_through_the_store(self, tmp_path):
        """A \\u escape in the source must be stored as its real character."""
        items = '["\\u0041","b","c","d","e"]'
        tiers = (
            '{'
            + ', '.join(f'"{tier}": {items}' for tier in ["high", "mid", "low"])
            + '}'
        )
        styles = []
        for style in ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]:
            styles.append(f'"{style}": {{"actions": {tiers}}}')
        profiles_js = "{" + ", ".join(styles) + "}"
        html_path = tmp_path / "escaped.html"
        html_path.write_text(
            f"<html><body><script>var profiles = {profiles_js};</script></body></html>",
            encoding="utf-8",
        )
        store_dir = tmp_path / "store"
        build_store(html_path, store_dir)
        item = get_item(store_dir, "connector-high-1")
        assert item.text == "A"


# ---------------------------------------------------------------------------
# Review finding (Agent 2): the complete set of styles and tiers must be
# validated. An otherwise-valid file that also carries a fifth style, a
# fourth tier, or an extra sixth item in one tier must be rejected, not
# silently have the extra data discarded. These run without the real HTML.
# ---------------------------------------------------------------------------

def _valid_profile_js(items=None):
    """A valid profiles JS object for one style with all three tiers."""
    items = items or '["a", "b", "c", "d", "e"]'
    tiers = (
        '{'
        + ', '.join(f'"{tier}": {items}' for tier in ["high", "mid", "low"])
        + '}'
    )
    return '{"actions": ' + tiers + '}'


class TestRejectsUnexpectedStylesAndTiers:
    def _profiles(self, body):
        return f'<html><body><script>var profiles = {body};</script></body></html>'

    def test_extra_style_is_rejected(self, tmp_path):
        """A fifth style key beyond the four expected must fail the build."""
        base = _valid_profile_js()
        profiles = (
            "{"
            + ', '.join(
                f'"{style}": {base}'
                for style in ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
            )
            + f', "sneaky": {base}'
            + "}"
        )
        html_path = tmp_path / "extra_style.html"
        html_path.write_text(self._profiles(profiles), encoding="utf-8")
        with pytest.raises(BuildError, match=r"(?i)style"):
            build_store(html_path, tmp_path / "store")

    def test_extra_tier_is_rejected(self, tmp_path):
        """A fourth tier key within a style must fail the build."""
        items = '["a", "b", "c", "d", "e"]'
        tiers = (
            "{"
            + ', '.join(f'"{t}": {items}' for t in ["high", "mid", "low", "ultra"])
            + "}"
        )
        profiles = (
            "{"
            + ', '.join(
                f'"{style}": {{"actions": {tiers}}}'
                for style in ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
            )
            + "}"
        )
        html_path = tmp_path / "extra_tier.html"
        html_path.write_text(self._profiles(profiles), encoding="utf-8")
        with pytest.raises(BuildError, match=r"(?i)tier"):
            build_store(html_path, tmp_path / "store")

    def test_six_items_in_one_tier_is_rejected(self, tmp_path):
        """One too many items in an otherwise valid tier must fail the build."""
        six = '["a", "b", "c", "d", "e", "f"]'
        good = '["a", "b", "c", "d", "e"]'
        profiles = (
            "{"
            + ', '.join(
                f'"{style}": {{"actions": '
                f'{{"high": {six}, "mid": {good}, "low": {good}}}}}'
                for style in ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
            )
            + "}"
        )
        html_path = tmp_path / "six_items.html"
        html_path.write_text(self._profiles(profiles), encoding="utf-8")
        with pytest.raises(BuildError, match=r"(?i)item"):
            build_store(html_path, tmp_path / "store")


def test_oracle_preserves_literal_true_false_null_words_in_text(tmp_path):
    """The oracle's JS-to-Python normalization must only touch object
    syntax, never string contents: literal text containing the words
    "true", "false", or "null" must come back unchanged, not silently
    converted to Python's True/False/None.
    """
    profiles_js = (
        '{"connector": {"actions": {'
        '"high": ["it is true that showing up matters", "b", "c", "d", "e"],'
        '"mid": ["this is false confidence talking", "b", "c", "d", "e"],'
        '"low": ["do not leave this null and void", "b", "c", "d", "e"]'
        '}}}'
    )
    html_path = tmp_path / "words.html"
    html_path.write_text(
        f"<html><body><script>var profiles = {profiles_js};</script></body></html>",
        encoding="utf-8",
    )
    result = _extract_actions_independently(html_path)
    assert result["connector-high-1"] == "it is true that showing up matters"
    assert result["connector-mid-1"] == "this is false confidence talking"
    assert result["connector-low-1"] == "do not leave this null and void"


# ---------------------------------------------------------------------------
# AC2: stored text matches the decoded HTML text exactly.
# ---------------------------------------------------------------------------

class TestStoredTextMatchesSource:
    def setup_method(self):
        _require_real_html()

    def test_every_stored_item_matches_decoded_html_text_exactly(self, tmp_path):
        """
        Deleting this test removes the only check that chunk text is a
        faithful, fully-decoded copy of the source (e.g. HTML entities like
        `&amp;` or `&#39;` left un-decoded, or text truncated/whitespace
        mangled during chunking, would go unnoticed).
        """
        expected = _extract_actions_independently(REAL_HTML_PATH)
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)

        assert set(list_source_ids(store_dir)) == set(expected.keys())
        for sid, expected_text in expected.items():
            stored = get_item(store_dir, sid)
            assert stored.text == expected_text, f"mismatch for {sid}"


# ---------------------------------------------------------------------------
# AC3: one embedding per item, each retrievable by source ID.
# ---------------------------------------------------------------------------

class TestEmbeddingsExistPerItem:
    def setup_method(self):
        _require_real_html()

    def test_every_item_has_exactly_one_embedding(self, tmp_path):
        """
        Deleting this test removes the check that each of the 60 chunks
        actually got embedded (as opposed to being stored as text-only
        metadata with no vector, which would silently break all querying).
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        for sid in list_source_ids(store_dir):
            vector = get_embedding(store_dir, sid)
            assert vector is not None
            assert len(vector) > 0

    def test_item_is_lookupable_by_source_id(self, tmp_path):
        """
        Deleting this test removes the check that source-ID lookup (the
        mechanism item 3's ranking step depends on) actually returns the
        matching item rather than erroring or returning something else.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        item = get_item(store_dir, "connector-high-1")
        assert item.source_id == "connector-high-1"
        assert item.style == "connector"
        assert item.tier == "high"


# ---------------------------------------------------------------------------
# AC4: the four Notes test phrases each return the listed item first.
# ---------------------------------------------------------------------------

class TestKnownPhrasesReturnExpectedTopResult:
    def setup_method(self):
        _require_real_html()

    @pytest.mark.parametrize("phrase,expected_id", TEST_PHRASES)
    def test_phrase_returns_expected_item_first(self, tmp_path, phrase, expected_id):
        """
        Deleting this test removes the suite's only semantic-correctness
        check: without it, a build that embeds garbage (e.g. all-zero
        vectors, or items shuffled onto the wrong IDs) could still pass
        every structural test above.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        results = query_store(store_dir, phrase, n_results=3)
        assert results, f"no results for phrase {phrase!r}"
        assert results[0].source_id == expected_id


# ---------------------------------------------------------------------------
# AC5: rebuilds are idempotent and deterministic; a failed run doesn't
# disturb the previous good store.
# ---------------------------------------------------------------------------

class TestRebuildBehavior:
    def setup_method(self):
        _require_real_html()

    def test_rebuilding_twice_yields_the_same_sixty_items_with_no_leftovers(self, tmp_path):
        """
        Deleting this test removes the check against the spec's "every run
        rebuilds from scratch" requirement; without it, a build that
        appends instead of replacing could silently accumulate duplicate
        or stale chunks across runs.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        first_ids = sorted(list_source_ids(store_dir))

        build_store(REAL_HTML_PATH, store_dir)
        second_ids = sorted(list_source_ids(store_dir))

        assert first_ids == second_ids
        assert len(second_ids) == 60
        assert count_items(store_dir) == 60

    def test_a_failed_rebuild_leaves_the_previous_store_unchanged(self, tmp_path):
        """
        Deleting this test removes the only check that a bad second run
        can't destroy a previously-good store — without it, re-running the
        build against a corrupted HTML file could leave the project with no
        usable store at all, worse off than before the run.
        """
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        before_ids = sorted(list_source_ids(store_dir))
        # Keep an independent copy to compare against, in case build_store
        # mutates store_dir in place before detecting the error.
        backup_dir = tmp_path / "store_backup"
        shutil.copytree(store_dir, backup_dir)

        profiles_js = '{"connector": {"actions": {"high": ["only-one-item"]}}}'
        bad_html = _write_malformed_html(tmp_path, profiles_js)
        with pytest.raises(BuildError):
            build_store(bad_html, store_dir)

        after_ids = sorted(list_source_ids(store_dir))
        assert after_ids == before_ids
        assert count_items(store_dir) == 60


# ---------------------------------------------------------------------------
# Review finding (Agent 2): a failure during the replacement step itself —
# not during input validation — must still leave the previous good store
# intact. The test above fails before the swap step, so it cannot cover this.
# ---------------------------------------------------------------------------

def test_a_failure_during_replacement_leaves_the_previous_store_unchanged(
    tmp_path, monkeypatch
):
    """Forcing the swap step to fail must not lose the previous store.

    Unlike the failed-input test (which errors during validation, before any
    swap), this drives a failure inside the replacement step by making
    ``os.replace`` fail precisely when the finished new store is moved into
    the store directory. The previous store must survive untouched.
    """
    import action_item_store

    store_dir = tmp_path / "store"
    html_path = tmp_path / "valid.html"
    html_path.write_text(
        f"<html><body><script>var profiles = {_valid_profiles_js()};"
        "</script></body></html>",
        encoding="utf-8",
    )

    build_store(html_path, store_dir)
    before_ids = sorted(list_source_ids(store_dir))
    assert len(before_ids) == 60

    real_replace = os.replace

    def failing_replace(src, dst):
        if Path(dst) == store_dir and Path(src).name.startswith("tmp"):
            raise OSError("simulated failure during store replacement")
        return real_replace(src, dst)

    monkeypatch.setattr(action_item_store.os, "replace", failing_replace)
    with pytest.raises(BuildError):
        build_store(html_path, store_dir)
    monkeypatch.setattr(action_item_store.os, "replace", real_replace)

    after_ids = sorted(list_source_ids(store_dir))
    assert after_ids == before_ids
    assert count_items(store_dir) == 60
    assert not (tmp_path / "store.old").exists()


# ---------------------------------------------------------------------------
# AC6: query validation — empty/whitespace, >500 chars, valid (exactly 3
# results), and cross-model mismatch.
# ---------------------------------------------------------------------------

class TestQueryValidation:
    def setup_method(self):
        _require_real_html()

    @pytest.fixture
    def built_store(self, tmp_path):
        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        return store_dir

    def test_empty_query_raises_a_clear_error(self, built_store):
        """
        Deleting this test removes coverage for the empty-query error case
        named explicitly in the acceptance criteria.
        """
        with pytest.raises(QueryError):
            query_store(built_store, "")

    def test_whitespace_only_query_raises_a_clear_error(self, built_store):
        """
        Deleting this test removes coverage for the whitespace-only-query
        error case, distinct from (and easy to miss alongside) the plain
        empty-string case above.
        """
        with pytest.raises(QueryError):
            query_store(built_store, "   \n\t  ")

    def test_query_over_500_characters_raises_a_clear_error(self, built_store):
        """
        Deleting this test removes coverage for the spec's explicit
        500-character query length limit.
        """
        too_long = "a" * 501
        with pytest.raises(QueryError):
            query_store(built_store, too_long)

    def test_query_at_exactly_500_characters_is_accepted(self, built_store):
        """
        Deleting this test removes the boundary check proving the limit is
        ">500", not "any query 500 characters or longer" — i.e. that a
        500-character query is NOT wrongly rejected.
        """
        exactly_500 = "a" * 500
        results = query_store(built_store, exactly_500, n_results=3)
        assert len(results) == 3

    def test_valid_query_returns_exactly_three_results(self, built_store):
        """
        Deleting this test removes the check that the spec's fixed result
        count (3) is honored, rather than some other default (top-1, top-5,
        or all 60).
        """
        results = query_store(built_store, "building a professional network", n_results=3)
        assert len(results) == 3

    def test_query_with_mismatched_embedding_model_raises_naming_both_models(self, built_store):
        """
        Deleting this test removes the only check for the spec's
        cross-model safety requirement; without it, a query embedded with
        the wrong model could silently return meaningless nearest-neighbor
        results instead of failing loudly.
        """
        stored_model = get_store_embedding_model(built_store)
        assert stored_model != ALT_EMBEDDING_MODEL  # sanity: fixture is actually "different"

        with pytest.raises(QueryError) as excinfo:
            query_store(built_store, "a valid query", embedding_model=ALT_EMBEDDING_MODEL)

        message = str(excinfo.value)
        assert stored_model in message
        assert ALT_EMBEDDING_MODEL in message


# ---------------------------------------------------------------------------
# Review finding (Agent 2): ties at the n_results cutoff must resolve
# alphabetically by source ID. Identical action text (which the spec
# confirms occurs across tiers) yields identical embeddings and therefore
# identical distances, so a tie spanning the cutoff is an expected case.
# These tests build a store where many items tie at the same distance and
# confirm the alphabetically-first n_results come back — not whatever order
# Chroma happened to return first. No real HTML needed.
# ---------------------------------------------------------------------------

class TestAlphabeticalTieBreaker:
    def _build_tied_store(self, tmp_path):
        """A store where many items share one identical text, so they all
        embed to the same vector and tie at distance 0.0 for that text."""
        identical = "the exact same action item text repeated everywhere"
        items = json.dumps([identical] * 5)
        tiers = (
            "{"
            + ', '.join(f'"{t}": {items}' for t in ["high", "mid", "low"])
            + "}"
        )
        profiles = (
            "{"
            + ', '.join(
                f'"{style}": {{"actions": {tiers}}}'
                for style in ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
            )
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

    def test_more_than_three_items_tied_returns_alphabetical_first_three(self, tmp_path):
        """With 60 items all at the same distance, the top-3 must be the
        alphabetically-first three source IDs, proving the tie-breaker runs
        before the cutoff is applied."""
        store_dir = self._build_tied_store(tmp_path)
        results = query_store(store_dir, "the exact same action item text", n_results=3)
        assert len(results) == 3
        # communityBuilder is alphabetically last among styles, but within a
        # style communityBuilder-high-1/2/3 are the alphabetically first IDs
        # across the whole tie, so they must win the cutoff.
        assert [r.source_id for r in results] == [
            "communityBuilder-high-1",
            "communityBuilder-high-2",
            "communityBuilder-high-3",
        ]
        # Every returned item must actually be tied at the same distance.
        distances = {r.distance for r in results}
        assert len(distances) == 1

    def test_tie_at_cutoff_is_stable_across_queries(self, tmp_path):
        """Running the same tied query twice must give identical results."""
        store_dir = self._build_tied_store(tmp_path)
        first = [r.source_id for r in query_store(store_dir, "the exact same action item text", n_results=3)]
        second = [r.source_id for r in query_store(store_dir, "the exact same action item text", n_results=3)]
        assert first == second


# ---------------------------------------------------------------------------
# AC7: the suite is runnable offline (after the model's first download) with
# no credentials.
# ---------------------------------------------------------------------------

class TestOfflineAfterFirstDownload:
    def setup_method(self):
        _require_real_html()

    def test_build_and_query_require_no_network_once_model_is_cached(self, tmp_path, monkeypatch):
        """
        Deleting this test removes the only check against the spec's "no
        internet ... needed after the model's first download" requirement;
        without it, a regression that makes every build/query silently
        depend on a live network call (e.g. re-downloading the model, or
        calling a hosted embedding API) would go undetected until it broke
        in an offline grading environment.
        """
        import socket

        def _blocked_connect(*args, **kwargs):
            raise AssertionError(
                "Network access was attempted during build/query; the model "
                "must be loaded from local cache with no network calls."
            )

        monkeypatch.setattr(socket.socket, "connect", _blocked_connect)

        store_dir = tmp_path / "store"
        build_store(REAL_HTML_PATH, store_dir)
        results = query_store(store_dir, "building a professional network", n_results=3)
        assert len(results) == 3
