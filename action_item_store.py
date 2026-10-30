"""Build and query a file-based vector store of action-item content
(specs/02-embed-content.md).

Reads every action item from the ``actions`` lists in the ``profiles``
object of ``networking-assessment.html`` as plain text, without running any
of it: 4 styles x 3 tiers x 5 items = 60 items. Each item becomes one chunk
with a source ID ``style-tier-position``, stored with its style, tier, and
text, embedded by Chroma's built-in local model (``all-MiniLM-L6-v2``), and
saved in a file-based Chroma store under ``data/``. A query returns the 3
closest chunks. Every run rebuilds the store from scratch, built separately
and swapped in only when complete, so a half-finished run leaves the
previous store untouched.

No user answers or personal data are stored. No internet or password is
needed after the model's first download.
"""

import html
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

from chromadb import PersistentClient
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

# The small model that runs on this computer (Chroma's built-in default).
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

STYLES = ["connector", "cultivator", "opportunitySeeker", "communityBuilder"]
TIERS = ["high", "mid", "low"]
ITEMS_PER_STYLE_TIER = 5
COLLECTION_NAME = "action_items"


class BuildError(Exception):
    """Raised when the action-item content cannot be built into a store."""


class QueryError(Exception):
    """Raised when a query is invalid or incompatible with the store."""


@dataclass
class ItemRecord:
    """A stored action item: its text plus the style, tier, and source ID."""

    source_id: str
    style: str
    tier: str
    text: str


@dataclass
class QueryResult:
    """A single result from a query: the item and its distance from the query."""

    source_id: str
    text: str
    style: str
    tier: str
    distance: float


# Token kinds
_PUNCT = "PUNCT"
_STRING = "STR"
_IDENT = "ID"
_NUMBER = "NUM"

# Punctuation characters that structure the object/array literal.
_STRUCT = {"{", "}", "[", "]", ",", ":"}

_SIMPLE_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "0": "\0",
    "'": "'",
    '"': '"',
    "\\": "\\",
}


def _decode_escape(source: str, i: int) -> str:
    """Decode the escape that starts at ``source[i]`` (a backslash).

    Returns the decoded character and the index just past the escape.
    Supports the JS simple escapes and ``\\uXXXX`` unicode escapes.
    """
    n = len(source)
    if i + 1 >= n:
        raise BuildError(f"dangling backslash at offset {i}")
    nxt = source[i + 1]
    if nxt == "u":
        end = i + 6
        if end > n:
            raise BuildError(f"incomplete unicode escape at offset {i}")
        hexpart = source[i + 2:i + 6]
        if not re.fullmatch(r"[0-9a-fA-F]{4}", hexpart):
            raise BuildError(f"invalid unicode escape {hexpart!r} at offset {i}")
        return chr(int(hexpart, 16)), end
    if nxt in _SIMPLE_ESCAPES:
        return _SIMPLE_ESCAPES[nxt], i + 2
    raise BuildError(f"unsupported escape \\{nxt} at offset {i}")


def _tokenize(source: str):
    """Yield ``(kind, value)`` tokens for a JS object/array literal.

    Quoted strings, bare identifiers, numbers, and structural punctuation
    are each emitted as a distinct token kind, so a parser can tell them
    apart and reject an unquoted word in a value position instead of
    treating it as text. Strings are decoded (simple escapes and
    ``\\uXXXX``), so stored text keeps its true characters. Skips comments
    and whitespace. Raises BuildError on anything that is not a valid
    token.
    """
    i = 0
    n = len(source)
    while i < n:
        ch = source[i]
        if ch in _STRUCT:
            yield _PUNCT, ch
            i += 1
        elif ch in "\"'":
            quote = ch
            start = i
            i += 1
            buf = []
            while i < n:
                c = source[i]
                if c == "\\":
                    decoded, i = _decode_escape(source, i)
                    buf.append(decoded)
                    continue
                if c == quote:
                    i += 1
                    break
                buf.append(c)
                i += 1
            else:
                raise BuildError(f"unterminated string at offset {start}")
            yield _STRING, "".join(buf)
        elif ch.isspace():
            i += 1
        elif ch.isdigit() or (ch in "+-" and i + 1 < n and source[i + 1].isdigit()):
            start = i
            i += 1
            while i < n and (source[i].isdigit() or source[i] in "._eExX+-"):
                i += 1
            token = source[start:i]
            try:
                number = int(token, 0) if re.fullmatch(r"0[xX][0-9a-fA-F]+", token) else (
                    float(token) if "." in token or "e" in token or "E" in token else int(token)
                )
            except ValueError:
                raise BuildError(f"invalid number {token!r} at offset {start}")
            yield _NUMBER, number
        elif ch.isalpha() or ch in "_$":
            start = i
            i += 1
            while i < n and (source[i].isalnum() or source[i] in "_$"):
                i += 1
            yield _IDENT, source[start:i]
        elif ch == "/":
            # skip line and block comments
            nxt = source[i + 1] if i + 1 < n else ""
            if nxt == "/":
                while i < n and source[i] != "\n":
                    i += 1
            elif nxt == "*":
                i += 2
                while i < n and not (source[i] == "*" and i + 1 < n and source[i + 1] == "/"):
                    i += 1
                i += 2
            else:
                raise BuildError(f"unexpected '/' at offset {i}")
        else:
            raise BuildError(f"unexpected character {ch!r} at offset {i}")


class _Reader:
    """A strict parser that turns the typed token stream into Python data.

    Enforces the object/array grammar: exactly one comma between items, no
    leading or trailing comma, no doubled comma, no missing comma, and no
    duplicate key within an object. An unquoted identifier is only ever a
    key or one of the JS literals ``true``/``false``/``null``; any other
    bare word in a value position is rejected. Raises BuildError on any
    deviation.
    """

    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0

    def _peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self):
        tok = self._peek()
        if tok is None:
            raise BuildError("unexpected end of object")
        self.pos += 1
        return tok

    def _expect_punct(self, char):
        tok = self._peek()
        if tok is None or tok[0] != _PUNCT or tok[1] != char:
            got = "end of object" if tok is None else repr(tok[1])
            raise BuildError(f"expected {char!r}, got {got}")
        self.pos += 1
        return tok

    def _accept_punct(self, char):
        tok = self._peek()
        if tok is not None and tok[0] == _PUNCT and tok[1] == char:
            self.pos += 1
            return True
        return False

    def parse(self):
        tok = self._peek()
        if tok is None:
            raise BuildError("unexpected end of object")
        kind, value = tok
        if kind == _PUNCT and value == "{":
            return self._object()
        if kind == _PUNCT and value == "[":
            return self._array()
        return self._scalar()

    def _object(self):
        self._expect_punct("{")
        obj = {}
        seen = set()
        if self._accept_punct("}"):
            return obj
        while True:
            key = self._key()
            self._expect_punct(":")
            value = self.parse()
            if key in seen:
                raise BuildError(f"duplicate key {key!r} in object")
            seen.add(key)
            obj[key] = value
            if self._accept_punct("}"):
                return obj
            self._expect_punct(",")
            # guard against a doubled or trailing comma
            tok = self._peek()
            if tok is not None and tok[0] == _PUNCT and tok[1] in ("}", ","):
                raise BuildError(f"unexpected {tok[1]!r} after comma")

    def _key(self):
        tok = self._peek()
        if tok is None:
            raise BuildError("expected a key, got end of object")
        kind, value = tok
        if kind in (_STRING, _IDENT):
            self.pos += 1
            return str(value)
        if kind == _NUMBER:
            self.pos += 1
            return str(value)
        raise BuildError(f"expected a key, got {value!r}")

    def _array(self):
        self._expect_punct("[")
        arr = []
        if self._accept_punct("]"):
            return arr
        while True:
            arr.append(self.parse())
            if self._accept_punct("]"):
                return arr
            self._expect_punct(",")
            tok = self._peek()
            if tok is not None and tok[0] == _PUNCT and tok[1] in ("]", ","):
                raise BuildError(f"unexpected {tok[1]!r} after comma")

    def _scalar(self):
        tok = self._peek()
        if tok is None:
            raise BuildError("expected a value, got end of object")
        kind, value = tok
        if kind == _STRING:
            self.pos += 1
            return value
        if kind == _NUMBER:
            self.pos += 1
            return value
        if kind == _IDENT:
            self.pos += 1
            if value == "true":
                return True
            if value == "false":
                return False
            if value == "null":
                return None
            raise BuildError(f"bare identifier {value!r} is not a valid value")
        raise BuildError(f"expected a value, got {value!r}")


def _parse_profiles(source: str) -> dict:
    """Parse the JS ``profiles`` object into a plain Python dict.

    Returns the object regardless of quote style, so the real HTML can be
    read as data without running any of it. Raises BuildError if there is no
    ``profiles`` assignment, more than one, or the object cannot be parsed.
    """
    assignments = re.findall(r"profiles\s*=\s*\{", source)
    if not assignments:
        raise BuildError("no `profiles = {...}` object found in the file")
    if len(assignments) > 1:
        raise BuildError(
            f"found {len(assignments)} `profiles` assignments; expected exactly one"
        )
    match = re.search(r"profiles\s*=\s*(\{.*?\})\s*;", source, re.DOTALL)
    if not match:
        raise BuildError("no `profiles = {...}` object found in the file")
    blob = match.group(1)
    return _Reader(_tokenize(blob)).parse()


def _extract_actions(source: str) -> dict:
    """Return {source_id: (style, tier, text)} for every action item.

    Reads the ``profiles`` object as plain data and collects every entry in
    the ``actions`` lists. The text is the decoded text a visitor sees
    (HTML entities unescaped). Raises BuildError naming the problem if the
    shape is wrong, a style or tier is missing, an item is empty, or the
    total count is anything other than 60.
    """
    profiles = _parse_profiles(source)
    if not isinstance(profiles, dict):
        raise BuildError("profiles is not an object")

    for style in STYLES:
        if style not in profiles:
            raise BuildError(f"missing style: {style}")
        data = profiles[style]
        if not isinstance(data, dict) or "actions" not in data:
            raise BuildError(f"style {style} has no actions object")
        actions = data["actions"]
        if not isinstance(actions, dict):
            raise BuildError(f"style {style} actions is not an object")
        for tier in TIERS:
            if tier not in actions:
                raise BuildError(f"missing tier {tier} for style {style}")
            items = actions[tier]
            if not isinstance(items, list):
                raise BuildError(
                    f"actions for {style}-{tier} is not a list"
                )
            if len(items) != ITEMS_PER_STYLE_TIER:
                raise BuildError(
                    f"style {style} tier {tier} has {len(items)} items; "
                    f"expected {ITEMS_PER_STYLE_TIER}"
                )
            for position, item in enumerate(items, start=1):
                if not isinstance(item, str) or item.strip() == "":
                    raise BuildError(
                        f"empty item at {style}-{tier}-{position}"
                    )

    out = {}
    for style in STYLES:
        actions = profiles[style]["actions"]
        for tier in TIERS:
            for position, item in enumerate(actions[tier], start=1):
                source_id = f"{style}-{tier}-{position}"
                out[source_id] = (style, tier, html.unescape(item))
    return out


def _collection_for(store_dir: Path):
    client = PersistentClient(path=str(store_dir))
    return client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_store(html_path, store_dir, embedding_model=DEFAULT_EMBEDDING_MODEL):
    """Read ``html_path``, embed its 60 action items, and write a fresh store.

    The new store is built in a temporary directory and swapped in only when
    it is complete, so a failed run leaves the previous store at ``store_dir``
    (if any) untouched. Raises BuildError on any malformed input.
    """
    if embedding_model != DEFAULT_EMBEDDING_MODEL:
        raise BuildError(
            f"unsupported embedding model {embedding_model!r}; "
            f"expected {DEFAULT_EMBEDDING_MODEL!r}"
        )

    path = Path(html_path)
    if not path.is_file():
        raise BuildError(f"HTML file not found: {path}")
    source = path.read_text(encoding="utf-8")
    items = _extract_actions(source)
    if len(items) != len(STYLES) * len(TIERS) * ITEMS_PER_STYLE_TIER:
        raise BuildError(
            f"expected 60 action items but found {len(items)}"
        )

    store_path = Path(store_dir)
    parent = store_path.parent if store_path.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    embedding = ONNXMiniLM_L6_V2()
    ids = sorted(items.keys())
    texts = [items[sid][2] for sid in ids]
    metadata = [
        {"style": items[sid][0], "tier": items[sid][1]} for sid in ids
    ]

    with tempfile.TemporaryDirectory(dir=str(parent)) as tmp:
        tmp_path = Path(tmp)
        client = PersistentClient(path=str(tmp_path))
        collection = client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedding_model": embedding_model},
        )
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadata,
            embeddings=embedding(texts),
        )
        client.close()

        try:
            _replace_store(tmp_path, store_path)
        except BuildError:
            raise
        except Exception as exc:
            raise BuildError(
                f"could not place the new store at {store_path}: {exc}"
            ) from exc


def _replace_store(new_store: Path, store_path: Path) -> None:
    """Atomically move a fully-built ``new_store`` into ``store_path``.

    The old store (if any) is renamed aside first, never deleted, and is
    restored if the final move into place fails. The old store is removed
    only after the new one is fully in place, so a failed or interrupted
    replacement never loses the previous store.
    """
    backup = store_path.with_name(store_path.name + ".old")
    if backup.exists():
        shutil.rmtree(backup)

    had_old = store_path.exists()
    if had_old:
        os.replace(store_path, backup)
    try:
        os.replace(new_store, store_path)
    except BaseException:
        if had_old and backup.exists():
            os.replace(backup, store_path)
        raise
    else:
        if backup.exists():
            shutil.rmtree(backup)


def _open_store(store_dir):
    client = PersistentClient(path=str(store_dir))
    try:
        return client, client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        client.close()
        raise QueryError(f"no usable store at {store_dir}: {exc}") from exc


def count_items(store_dir) -> int:
    """How many items are stored."""
    client, collection = _open_store(store_dir)
    try:
        return collection.count()
    finally:
        client.close()


def list_source_ids(store_dir) -> List[str]:
    """Every stored source ID, in no particular order."""
    client, collection = _open_store(store_dir)
    try:
        got = collection.get(include=[])
        return list(got["ids"])
    finally:
        client.close()


def get_item(store_dir, source_id) -> ItemRecord:
    """The stored item for ``source_id`` as an ItemRecord."""
    client, collection = _open_store(store_dir)
    try:
        got = collection.get(ids=[source_id], include=["documents", "metadatas"])
        ids = got["ids"]
        if not ids:
            raise QueryError(f"no item with source ID {source_id!r}")
        meta = got["metadatas"][0] or {}
        return ItemRecord(
            source_id=ids[0],
            style=meta.get("style", ""),
            tier=meta.get("tier", ""),
            text=got["documents"][0] or "",
        )
    finally:
        client.close()


def get_embedding(store_dir, source_id) -> Sequence[float]:
    """The stored embedding vector for ``source_id``."""
    client, collection = _open_store(store_dir)
    try:
        got = collection.get(ids=[source_id], include=["embeddings"])
        if not got["ids"]:
            raise QueryError(f"no item with source ID {source_id!r}")
        return got["embeddings"][0]
    finally:
        client.close()


def get_store_embedding_model(store_dir) -> str:
    """The embedding model name the store was built with."""
    client, collection = _open_store(store_dir)
    try:
        meta = collection.metadata or {}
        return meta.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    finally:
        client.close()


def query_store(store_dir, text, n_results=3,
                embedding_model=DEFAULT_EMBEDDING_MODEL) -> List[QueryResult]:
    """Return the ``n_results`` items closest to ``text``.

    Raises QueryError if the query is empty/whitespace, longer than 500
    characters, or embedded with a different model than the store's.
    """
    if text is None or text.strip() == "":
        raise QueryError("query must not be empty or whitespace-only")
    if len(text) > 500:
        raise QueryError(f"query is {len(text)} characters; limit is 500")

    stored_model = get_store_embedding_model(store_dir)
    if embedding_model != stored_model:
        raise QueryError(
            f"query model {embedding_model!r} does not match the store's "
            f"model {stored_model!r}"
        )

    client, collection = _open_store(store_dir)
    try:
        embedding = ONNXMiniLM_L6_V2()
        results = collection.query(
            query_texts=[text],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
    finally:
        client.close()

    results_list = []
    ids = results["ids"][0]
    distances = results["distances"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    for sid, distance, doc, meta in zip(ids, distances, documents, metadatas):
        meta = meta or {}
        results_list.append(
            QueryResult(
                source_id=sid,
                text=doc or "",
                style=meta.get("style", ""),
                tier=meta.get("tier", ""),
                distance=distance,
            )
        )
    return results_list