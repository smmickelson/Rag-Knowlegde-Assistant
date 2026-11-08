"""Build and query a file-based vector store of the four-layer content
library (specs/2b-embed-content-library-v2.md).

Reads every ``*.md`` file directly inside ``knowledge_base_dir`` (no
recursion, no hidden files, no symlinks): 2 philosophy, 8 archetype, 30
behavior, 40 total. Each file becomes one chunk: its YAML frontmatter is
parsed and kept as metadata, and everything after the closing ``---`` is the
chunk's stored text. Chunks are embedded by Chroma's built-in local model
(``all-MiniLM-L6-v2``) and saved in a file-based Chroma store, separate from
the ``action_items`` store built by item #2. A query returns the 3 closest
chunks. Every run rebuilds the store from scratch, built in a temporary
directory and swapped in only when complete, so a half-finished or
concurrent run never corrupts a previous good store.

No user answers or personal data are stored. No internet or password is
needed after the model's first download.
"""

import errno
import fcntl
import json
import os
import re
import shutil
import stat
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import yaml
from chromadb import PersistentClient
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

# The small model that runs on this computer (Chroma's built-in default).
DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"

COLLECTION_NAME = "content_library"
DEFAULT_STORE_DIR = "data/content_library"

# Every question/behavior file must declare one of these 15 questions.
BEHAVIOR_QUESTIONS = frozenset(range(1, 16))

# The fixed taxonomy from the spec (specs/2b-embed-content-library-v2.md):
# a fixed universe, not whatever values happen to show up in the files being
# validated, so a build can't be fooled into accepting an invented archetype,
# piece, or mode just because it's internally consistent with itself.
ARCHETYPE_NAMES = frozenset(
    {"connector", "cultivator", "opportunity_seeker", "community_builder"}
)
ARCHETYPE_PIECE_NAMES = frozenset({"identity", "strengths"})
BEHAVIOR_MODE_NAMES = frozenset({"building", "using"})

# The frontmatter fields each layer requires, and the only fields it allows.
_LAYER_FIELDS = {
    "philosophy": {"layer", "piece"},
    "archetype": {"layer", "archetype", "piece"},
    "behavior": {"layer", "question", "slug", "mode", "archetypes"},
}
_LAYER_REQUIRED = {
    "philosophy": {"layer", "piece"},
    "archetype": {"layer", "archetype", "piece"},
    "behavior": {"layer", "question", "slug", "mode", "archetypes"},
}

# Fields (besides `layer`, checked separately) whose value must be a plain
# string -- checked before any value is used as a dict key or set element,
# so a malformed value (a list, a mapping) is rejected with a clear
# BuildError instead of surfacing as a raw TypeError deep in a set/dict op.
_STRING_FIELDS = {
    "philosophy": {"piece"},
    "archetype": {"archetype", "piece"},
    "behavior": {"slug", "mode"},
}

# behavior_q01_introduce_yourself_building (real library) or
# behavior_q04_mode_building (synthetic fixtures) — the question number is
# the first token, the mode is the *last* underscore-separated token (never
# containing an underscore itself), and the slug is whatever sits between
# them. This is purely positional, so it does not need to know the literal
# set of valid mode words to correctly separate slug from mode.
_BEHAVIOR_FILENAME_RE = re.compile(r"^behavior_q(\d{1,2})_(.+)_([^_]+)$")


class BuildError(Exception):
    """Raised when the content library cannot be built into a store."""


class QueryError(Exception):
    """Raised when a query is invalid or incompatible with the store."""


def _type_name(value) -> str:
    """The name of ``value``'s type, read without running class code."""
    return type.__dict__["__name__"].__get__(type(value))


@dataclass
class ItemRecord:
    """A stored chunk: its text plus its layer and full frontmatter metadata."""

    source_id: str
    layer: str
    metadata: dict
    text: str


@dataclass
class QueryResult:
    """A single result from a query: the chunk and its distance from the query."""

    source_id: str
    text: str
    layer: str
    metadata: dict
    distance: float


class _StrictLoader(yaml.SafeLoader):
    """A SafeLoader that rejects duplicate mapping keys instead of silently
    keeping the last one."""


def _construct_mapping_no_duplicates(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            is_duplicate = key in mapping
        except TypeError as exc:
            # A key that YAML allowed (e.g. a list or another mapping) but
            # Python cannot hash. Surface it the same way a syntax error
            # would be surfaced, never as a raw TypeError.
            raise yaml.constructor.ConstructorError(
                None, None, f"unhashable mapping key {key!r}: {exc}",
                key_node.start_mark,
            ) from exc
        if is_duplicate:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key {key!r} in mapping",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_no_duplicates,
)


def _list_markdown_files(kb_dir: Path) -> List[Path]:
    """Every ``*.md`` name directly inside ``kb_dir``.

    No recursion (``iterdir`` only), no hidden files (names starting with
    ``.``), and the extension must be exactly lowercase ``.md`` — ``.MD`` or
    mixed case does not count. Whether an entry is a symlink is deliberately
    *not* checked here: checking now and reading later would leave a gap
    where the entry could be swapped for a symlink in between. That check
    happens atomically at the moment each file is opened, in
    ``_read_markdown_file``.
    """
    files = []
    for entry in sorted(kb_dir.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.suffix != ".md":
            continue
        files.append(entry)
    return files


def _read_markdown_file(path: Path):
    """Read ``path``'s text, refusing to follow a symlink.

    The check ("is this a symlink?") and the use (reading it) happen as one
    atomic kernel call (``O_NOFOLLOW``), so there is no window between
    checking and reading where the target could be swapped for a symlink.
    Returns ``None`` if ``path`` is a symlink (symlinks never count toward
    the library, same as if they were never listed). Raises BuildError if
    the path cannot be read for any other reason, or is not a regular file.
    """
    try:
        fd = os.open(str(path), os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            return None
        raise BuildError(f"{path.name}: cannot read file ({exc})") from exc

    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise BuildError(f"{path.name}: not a regular file")

    try:
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise BuildError(f"{path.name}: cannot read file ({exc})") from exc


def _split_frontmatter(raw_text: str, filename: str):
    """Split a file's text into (frontmatter_text, body).

    The file must open with a line that is exactly ``---`` and contain a
    second such line closing the frontmatter block; everything after that
    second line is the body (UTF-8, line endings normalized to ``\\n``,
    leading/trailing whitespace trimmed). Raises BuildError if the opening
    or closing marker is missing, or the body is empty or whitespace-only.
    """
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise BuildError(f"{filename}: missing opening '---' frontmatter marker")
    close = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            close = i
            break
    if close is None:
        raise BuildError(f"{filename}: frontmatter is never closed with '---'")
    frontmatter_text = "\n".join(lines[1:close])
    body = "\n".join(lines[close + 1:]).strip()
    if body == "":
        raise BuildError(f"{filename}: body is empty or whitespace-only")
    return frontmatter_text, body


def _parse_frontmatter(frontmatter_text: str, filename: str) -> dict:
    """Parse frontmatter YAML strictly: no duplicate keys, no custom tags.

    Raises BuildError on any YAML syntax error or a frontmatter that is not
    a mapping.
    """
    try:
        data = yaml.load(frontmatter_text, Loader=_StrictLoader)
    except yaml.YAMLError as exc:
        raise BuildError(f"{filename}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(data, dict):
        raise BuildError(f"{filename}: frontmatter must be a mapping of fields")
    return data


def _validate_frontmatter(metadata: dict, filename: str) -> str:
    """Validate ``metadata`` against its declared layer's field contract.

    Requires a known ``layer`` value, exactly the required fields for that
    layer, no unknown fields, ``question`` as a real int (not a quoted
    string), and ``archetypes`` as a list with no repeated name. Returns the
    layer name. Raises BuildError naming the problem.
    """
    if "layer" not in metadata:
        raise BuildError(f"{filename}: missing required field 'layer'")
    layer = metadata["layer"]
    # Check the type before any dict/set membership test below: a YAML value
    # that parses fine but isn't a plain string (a list, a mapping, ...) is
    # unhashable, and testing membership with it would raise a raw TypeError
    # instead of a clear BuildError. `or` short-circuits, so the membership
    # test on the right is never reached once the type check already fails.
    if type(layer) is not str or layer not in _LAYER_FIELDS:
        raise BuildError(f"{filename}: unknown layer {layer!r}")

    allowed = _LAYER_FIELDS[layer]
    required = _LAYER_REQUIRED[layer]
    # Frontmatter keys come from the custom loader above, which already
    # rejects an unhashable mapping key as a YAMLError before this point, so
    # it's always safe to put these keys in a set.
    present = set(metadata.keys())

    missing = required - present
    if missing:
        raise BuildError(
            f"{filename}: '{layer}' layer is missing required field(s): "
            f"{', '.join(sorted(missing))}"
        )
    unknown = present - allowed
    if unknown:
        raise BuildError(
            f"{filename}: '{layer}' layer has unknown frontmatter field(s): "
            f"{', '.join(sorted(unknown))}"
        )

    # Every other field this layer uses is expected to be a plain string;
    # checking that now, before any field value is ever used as a dict key
    # or set element, is what keeps a malformed value (a list, a mapping)
    # from surfacing downstream as a raw TypeError.
    for field in _STRING_FIELDS.get(layer, ()):
        if field not in metadata:
            continue  # not every string field is required for every layer
        if type(metadata[field]) is not str:
            raise BuildError(
                f"{filename}: {field!r} must be a string, "
                f"not {_type_name(metadata[field])}"
            )

    if layer == "archetype":
        if metadata["archetype"] not in ARCHETYPE_NAMES:
            raise BuildError(
                f"{filename}: unknown archetype {metadata['archetype']!r}; "
                f"expected one of {sorted(ARCHETYPE_NAMES)}"
            )
        if metadata["piece"] not in ARCHETYPE_PIECE_NAMES:
            raise BuildError(
                f"{filename}: unknown archetype piece {metadata['piece']!r}; "
                f"expected one of {sorted(ARCHETYPE_PIECE_NAMES)}"
            )

    if layer == "behavior":
        if type(metadata["question"]) is not int:
            raise BuildError(
                f"{filename}: 'question' must be a whole number, "
                f"not {_type_name(metadata['question'])}"
            )
        if metadata["question"] not in BEHAVIOR_QUESTIONS:
            raise BuildError(
                f"{filename}: 'question' {metadata['question']!r} is outside "
                "the expected range 1-15"
            )
        if metadata["mode"] not in BEHAVIOR_MODE_NAMES:
            raise BuildError(
                f"{filename}: unknown behavior mode {metadata['mode']!r}; "
                f"expected one of {sorted(BEHAVIOR_MODE_NAMES)}"
            )
        archetypes = metadata["archetypes"]
        if not isinstance(archetypes, list):
            raise BuildError(
                f"{filename}: 'archetypes' must be a list, "
                f"not {_type_name(archetypes)}"
            )
        if any(type(a) is not str for a in archetypes):
            raise BuildError(f"{filename}: 'archetypes' must be a list of strings")
        if len(set(archetypes)) != len(archetypes):
            raise BuildError(f"{filename}: 'archetypes' has a repeated name")
        if any(a not in ARCHETYPE_NAMES for a in archetypes):
            raise BuildError(
                f"{filename}: 'archetypes' contains an unknown archetype name"
            )

    return layer


def _check_filename_agreement(stem: str, layer: str, metadata: dict) -> None:
    """A behavior filename's implied question/mode must match its frontmatter.

    ``behavior_q01_introduce_yourself_building.md`` must carry
    ``question: 1`` and ``mode: building`` (the ``introduce_yourself`` slug
    in the middle is not checked here). Raises BuildError on a mismatch, or
    if a behavior filename does not follow the expected
    ``behavior_q<NN>_<slug>_<mode>`` shape at all.
    """
    if layer != "behavior":
        return
    match = _BEHAVIOR_FILENAME_RE.match(stem)
    if not match:
        raise BuildError(
            f"{stem}: behavior filename does not match the expected "
            "behavior_q<NN>_<slug>_<mode> shape"
        )
    implied_question = int(match.group(1))
    implied_mode = match.group(3)
    if metadata["question"] != implied_question:
        raise BuildError(
            f"{stem}: filename implies question {implied_question}, "
            f"but frontmatter says {metadata['question']!r}"
        )
    if metadata["mode"] != implied_mode:
        raise BuildError(
            f"{stem}: filename implies mode {implied_mode!r}, "
            f"but frontmatter says {metadata['mode']!r}"
        )


def _check_combination_completeness(chunks: dict) -> None:
    """Every archetype/piece and question/mode combination must appear once.

    Checked against the spec's fixed taxonomy (the 4 known archetypes x 2
    known pieces, and the 15 known questions x 2 known modes) -- not
    whatever set of values happens to appear in the files -- so a library
    that is internally consistent but doesn't match the real taxonomy still
    gets rejected. Raises BuildError on a duplicate or a missing combination.
    """
    archetype_combos = [
        (meta["archetype"], meta["piece"])
        for _layer, meta, _body in chunks.values()
        if meta["layer"] == "archetype"
    ]
    if len(set(archetype_combos)) != len(archetype_combos):
        raise BuildError("duplicate archetype/piece combination in archetype files")
    expected_archetype_combos = {
        (name, piece) for name in ARCHETYPE_NAMES for piece in ARCHETYPE_PIECE_NAMES
    }
    if set(archetype_combos) != expected_archetype_combos:
        raise BuildError(
            "archetype files must cover every archetype/piece combination "
            "in the fixed taxonomy exactly once"
        )

    behavior_combos = [
        (meta["question"], meta["mode"])
        for _layer, meta, _body in chunks.values()
        if meta["layer"] == "behavior"
    ]
    if len(set(behavior_combos)) != len(behavior_combos):
        raise BuildError("duplicate question/mode combination in behavior files")
    expected_behavior_combos = {
        (question, mode) for question in BEHAVIOR_QUESTIONS for mode in BEHAVIOR_MODE_NAMES
    }
    if set(behavior_combos) != expected_behavior_combos:
        raise BuildError(
            "behavior files must cover every question/mode combination "
            "in the fixed taxonomy exactly once"
        )


def _collect_chunks(kb_dir: Path) -> dict:
    """Read, validate, and parse every chunk in ``kb_dir``.

    Returns ``{source_id: (layer, metadata, body)}``. Raises BuildError
    naming the problem on any malformed file, or if the library is not
    exactly 2 philosophy, 8 archetype, and 30 behavior files.
    """
    files = _list_markdown_files(kb_dir)
    chunks = {}
    for path in files:
        raw_text = _read_markdown_file(path)
        if raw_text is None:
            continue  # a symlink, discovered atomically at open time; never counts
        source_id = path.stem
        frontmatter_text, body = _split_frontmatter(raw_text, path.name)
        metadata = _parse_frontmatter(frontmatter_text, path.name)
        layer = _validate_frontmatter(metadata, path.name)
        _check_filename_agreement(source_id, layer, metadata)
        chunks[source_id] = (layer, metadata, body)

    counts = {"philosophy": 0, "archetype": 0, "behavior": 0}
    for layer, _meta, _body in chunks.values():
        counts[layer] += 1

    if len(chunks) != 40:
        raise BuildError(
            f"expected exactly 40 files but found {len(chunks)}"
        )
    for layer, expected in (("philosophy", 2), ("archetype", 8), ("behavior", 30)):
        if counts[layer] != expected:
            raise BuildError(
                f"expected exactly {expected} {layer} file(s) but found {counts[layer]}"
            )

    _check_combination_completeness(chunks)
    return chunks


# A file this module writes inside every store it builds, so it can tell a
# store it built apart from an arbitrary existing directory (such as item
# #2's `action_items` store) before ever moving or deleting anything there.
_MARKER_FILENAME = ".content_library_store"


def _is_our_store(path: Path) -> bool:
    """Whether ``path`` -- directly, or by following one symlink -- is a
    directory this module created.

    Used before anything destructive ever touches ``path``: a directory
    without our marker file is never moved aside or deleted, no matter what
    ``store_dir`` a caller passes in.
    """
    try:
        if not path.exists():
            return False
        resolved = path.resolve() if path.is_symlink() else path
        return resolved.is_dir() and (resolved / _MARKER_FILENAME).is_file()
    except OSError:
        return False


def _new_data_dir_name(store_path: Path) -> str:
    """A fresh, collision-free sibling name to hold one build's data."""
    return f"{store_path.name}.data-{uuid.uuid4().hex}"


def _collection_for(store_dir: Path):
    client = PersistentClient(path=str(store_dir))
    return client.get_or_create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def build_store(knowledge_base_dir, store_dir=DEFAULT_STORE_DIR,
                embedding_model=DEFAULT_EMBEDDING_MODEL) -> None:
    """Read ``knowledge_base_dir``, embed its 40 chunks, and write a fresh
    store at ``store_dir``.

    The new store is built in a temporary directory and swapped in only
    when it is complete, so a failed run leaves the previous store at
    ``store_dir`` (if any) untouched. A concurrent build fails immediately
    with BuildError instead of racing to publish. Raises BuildError on any
    malformed input; never reads, modifies, or deletes any other store.
    """
    if embedding_model != DEFAULT_EMBEDDING_MODEL:
        raise BuildError(
            f"unsupported embedding model {embedding_model!r}; "
            f"expected {DEFAULT_EMBEDDING_MODEL!r}"
        )

    kb_path = Path(knowledge_base_dir)
    if not kb_path.is_dir():
        raise BuildError(f"knowledge base folder not found: {kb_path}")

    chunks = _collect_chunks(kb_path)

    store_path = Path(store_dir)
    # Fail fast, before spending any time on embeddings, if store_dir points
    # at something this module didn't create -- never move or delete a
    # directory (e.g. item #2's `action_items` store) that isn't ours.
    if store_path.exists() and not _is_our_store(store_path):
        raise BuildError(
            f"refusing to build into {store_path}: it already exists and "
            "was not created by this module"
        )

    parent = store_path.parent if store_path.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    lock_path = parent / (store_path.name + ".lock")
    lock_file = open(lock_path, "w")
    try:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise BuildError(
                f"another build is already in progress for {store_path}"
            ) from exc

        ids = sorted(chunks.keys())
        texts = [chunks[sid][2] for sid in ids]
        metadatas = [
            {
                "layer": chunks[sid][0],
                "metadata_json": json.dumps(chunks[sid][1]),
            }
            for sid in ids
        ]

        embedding = ONNXMiniLM_L6_V2()

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
                metadatas=metadatas,
                embeddings=embedding(texts),
            )
            client.close()
            (tmp_path / _MARKER_FILENAME).write_text(
                "content_library_store\n", encoding="utf-8"
            )

            try:
                _replace_store(tmp_path, store_path)
            except BuildError:
                raise
            except Exception as exc:
                raise BuildError(
                    f"could not place the new store at {store_path}: {exc}"
                ) from exc
    finally:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()


def _replace_store(new_store: Path, store_path: Path) -> None:
    """Make ``store_path`` point at the fully-built ``new_store``, with no
    moment where it points at nothing.

    ``store_path`` is always a symlink to a sibling ``<name>.data-<id>``
    directory that holds the real Chroma files, never a plain directory
    itself. A plain directory the size of a Chroma store cannot be replaced
    by another one in a single filesystem call (the OS only allows that for
    an *empty* directory) -- which is exactly the gap a crash could land in.
    A symlink has no such limit: swapping it for a new symlink is one atomic
    rename, so a reader always resolves either the complete old store or the
    complete new one, never neither, even if the process dies mid-swap.

    Raises BuildError (touching nothing) if ``store_path`` already exists
    and is not a store this module created, so a caller can never point
    this at an unrelated directory and have it moved aside or deleted.
    """
    if store_path.exists() and not _is_our_store(store_path):
        raise BuildError(
            f"refusing to replace {store_path}: it is not a content-library "
            "store created by this module"
        )

    parent = store_path.parent
    previous_data_dir = None
    if store_path.is_symlink():
        previous_data_dir = store_path.resolve()
    elif store_path.exists():
        # The guard above already requires this to be one of ours, and this
        # module never creates a store that is a plain directory at
        # store_path itself -- so this should be unreachable. Refuse rather
        # than guess what to do with it.
        raise BuildError(f"refusing to replace {store_path}: not a symlink")

    data_dir = parent / _new_data_dir_name(store_path)
    os.replace(new_store, data_dir)  # same-filesystem move; cheap and atomic

    tmp_link = Path(tempfile.mktemp(dir=str(parent)))
    try:
        os.symlink(data_dir.name, tmp_link)
        os.replace(tmp_link, store_path)  # the one atomic step; no gap
    except BaseException:
        for stray in (tmp_link,):
            try:
                stray.unlink()
            except OSError:
                pass
        shutil.rmtree(data_dir, ignore_errors=True)
        raise

    if previous_data_dir is not None and previous_data_dir != data_dir:
        shutil.rmtree(previous_data_dir, ignore_errors=True)


def _open_store(store_dir):
    """Open the store at ``store_dir``, or raise QueryError.

    Checked before ``PersistentClient`` is ever constructed: a missing path
    or one that isn't a store this module built raises QueryError without
    creating anything on disk (``PersistentClient`` would otherwise create
    an empty directory at a path that doesn't exist yet), and a path that
    is, say, a regular file raises QueryError instead of leaking whatever
    internal exception Chroma happens to throw.
    """
    path = Path(store_dir)
    if not _is_our_store(path):
        raise QueryError(f"no usable store at {store_dir}")
    try:
        client = PersistentClient(path=str(path))
    except Exception as exc:
        raise QueryError(f"no usable store at {store_dir}: {exc}") from exc
    try:
        return client, client.get_collection(COLLECTION_NAME)
    except Exception as exc:
        client.close()
        raise QueryError(f"no usable store at {store_dir}: {exc}") from exc


def count_items(store_dir) -> int:
    """How many chunks are stored."""
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


def _record_from_meta(source_id: str, text: str, meta: dict) -> ItemRecord:
    meta = meta or {}
    metadata = json.loads(meta.get("metadata_json", "{}"))
    return ItemRecord(
        source_id=source_id,
        layer=meta.get("layer", ""),
        metadata=metadata,
        text=text or "",
    )


def get_item(store_dir, source_id) -> ItemRecord:
    """The stored chunk for ``source_id`` as an ItemRecord."""
    client, collection = _open_store(store_dir)
    try:
        got = collection.get(ids=[source_id], include=["documents", "metadatas"])
        ids = got["ids"]
        if not ids:
            raise QueryError(f"no item with source ID {source_id!r}")
        return _record_from_meta(ids[0], got["documents"][0], got["metadatas"][0])
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
    """Return the ``n_results`` chunks closest to ``text``.

    Raises QueryError if ``text`` is not a string (naming the type
    received), empty/whitespace-only, longer than 500 raw characters, the
    store is missing or unreadable, or ``embedding_model`` does not match
    the model the store was built with. Never triggers a build.
    """
    if not isinstance(text, str):
        raise QueryError(
            f"query must be a string, not {_type_name(text)}"
        )
    if text.strip() == "":
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
        total = collection.count()
        results = collection.query(
            query_texts=[text],
            n_results=max(n_results, total),
            include=["documents", "metadatas", "distances"],
        )
    finally:
        client.close()

    ids = results["ids"][0]
    distances = results["distances"][0]
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    raw = []
    for sid, distance, doc, meta in zip(ids, distances, documents, metadatas):
        record = _record_from_meta(sid, doc, meta)
        raw.append(
            QueryResult(
                source_id=record.source_id,
                text=record.text,
                layer=record.layer,
                metadata=record.metadata,
                distance=distance,
            )
        )
    # Order by distance, then by source ID (alphabetical), so equal-distance
    # ties resolve to the same stable result rather than Chroma's arbitrary
    # order.
    raw.sort(key=lambda r: (r.distance, r.source_id))
    return raw[:n_results]
