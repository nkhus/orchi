"""Disposable, scope-bound Markdown retrieval. Inputs are resolved knowledge, not files.

SQLite only proposes matching chunks. Result text and provenance are reconstructed
from the supplied authority snapshot; packets and exact reads never use this cache.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from difflib import SequenceMatcher
from functools import lru_cache
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import tempfile
import unicodedata
from typing import Iterator

from .common import OrchiError, digest, require, sha

MAX_QUERY_CHARS = 512
MAX_QUERY_TERMS = 16
MAX_RESULTS = 100
CHUNK_LINES = 100
CHUNK_CHARS = 8000
SNIPPET_CHARS = 280
WORD = re.compile(r"[^\W_]+", re.UNICODE)
ATX = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*)|[ \t]*)$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
SETEXT = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")


def normalize(text: str) -> str:
    """Casefold and normalize compatibility characters; fold Latin accents only."""
    result = []
    for char in unicodedata.normalize("NFKC", text).casefold():
        if "LATIN" in unicodedata.name(char, ""):
            result.append("".join(c for c in unicodedata.normalize("NFD", char)
                                  if not unicodedata.combining(c)))
        else:
            result.append(char)
    return "".join(result)


def query_terms(query: str) -> list[str]:
    require(isinstance(query, str) and len(query) <= MAX_QUERY_CHARS and
            not any(ord(c) < 32 and c not in "\t\r\n" for c in query),
            "INVALID_QUERY", "Use at most 512 characters of plain search text")
    terms = list(dict.fromkeys(WORD.findall(normalize(query))))
    require(0 < len(terms) <= MAX_QUERY_TERMS and all(len(t) <= 64 for t in terms),
            "INVALID_QUERY", "Use 1-16 terms, each at most 64 characters; use stat to inspect an empty index")
    return terms


def capabilities() -> dict:
    """Detect the SQLite actually linked to Python, without a filesystem write."""
    con = sqlite3.connect(":memory:")
    try:
        try:
            con.execute("CREATE VIRTUAL TABLE lex USING fts5(text, tokenize='unicode61 remove_diacritics 2')")
        except sqlite3.OperationalError:
            return {"fts5": False, "trigram": False}
        try:
            con.execute("CREATE VIRTUAL TABLE tri USING fts5(text, tokenize='trigram')")
        except sqlite3.OperationalError:
            return {"fts5": True, "trigram": False}
        return {"fts5": True, "trigram": True}
    finally:
        con.close()


@dataclass(frozen=True)
class Chunk:
    line: int
    end_line: int
    heading_path: tuple[str, ...]
    body: str

    @property
    def heading(self) -> str:
        return self.heading_path[-1] if self.heading_path else ""


def chunks(text: str) -> list[Chunk]:
    """ATX/Setext sections, ignoring headings inside fences and YAML metadata.

    Line ranges are 1-based and inclusive in the original source, including its
    frontmatter. Large sections split at line boundaries; a long single line is
    indivisible. This is section extraction, not a general Markdown renderer.
    """
    lines = text.splitlines()
    start = 0
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] in {"---", "..."}:
                start = i + 1
                break
    headings: dict[int, tuple[int, str]] = {}
    fence: tuple[str, int] | None = None
    i = start
    while i < len(lines):
        line = lines[i]
        marker = FENCE.match(line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1] and not marker[2].strip():
                fence = None
        elif marker:
            fence = (marker[1][0], len(marker[1]))
        else:
            atx = ATX.match(line)
            underline = SETEXT.match(lines[i + 1]) if i + 1 < len(lines) else None
            if atx:
                label = re.sub(r"[ \t]+#+[ \t]*$", "", atx[2] or "").strip()
                headings[i] = (len(atx[1]), label)
            elif line.strip() and not line.startswith(("    ", "\t")) and underline:
                headings[i] = (1 if underline[1][0] == "=" else 2, line.strip())
                i += 1
        i += 1
    sections: list[tuple[int, int, tuple[str, ...]]] = []
    stack: list[tuple[int, str]] = []
    section_start, section_heading = start, ()
    for at, (level, label) in headings.items():
        if at > section_start:
            sections.append((section_start, at, section_heading))
        stack = [h for h in stack if h[0] < level]
        stack.append((level, label))
        section_start, section_heading = at, tuple(h[1] for h in stack)
    if section_start < len(lines):
        sections.append((section_start, len(lines), section_heading))
    result: list[Chunk] = []
    for begin, end, heading in sections:
        at = begin
        while at < end:
            stop, size = at, 0
            while stop < end and stop - at < CHUNK_LINES:
                extra = len(lines[stop]) + 1
                if stop > at and size + extra > CHUNK_CHARS:
                    break
                size += extra
                stop += 1
            body = "\n".join(lines[at:stop])
            if body.strip():
                result.append(Chunk(at + 1, stop, heading, body))
            at = stop
    return result


def document_title(target: str, parts: list[Chunk]) -> str:
    return next((c.heading_path[0] for c in parts if c.heading_path), PurePosixPath(target).stem)


@dataclass
class Snapshot:
    records: dict[str, dict]
    identity: dict
    diagnostics: list[dict]

    @property
    def fingerprint(self) -> str:
        # Content and provenance both matter: revalidation can preserve the prose.
        manifest = {p: {k: v for k, v in r.items() if k != "content"}
                    for p, r in self.records.items()}
        return digest({"identity": self.identity, "documents": manifest})


@lru_cache(maxsize=1)
def engine_signature() -> str:
    # No release counter or cache migration. A changed implementation is rebuilt.
    return sha(Path(__file__).read_bytes())


def _metadata(snapshot: Snapshot, caps: dict) -> dict:
    return {"snapshot": snapshot.fingerprint, "engine": engine_signature(),
            "sqlite": sqlite3.sqlite_version, "capabilities": caps}


def _populate(con: sqlite3.Connection, snapshot: Snapshot, meta: dict) -> None:
    con.executescript("""
        CREATE TABLE meta(value TEXT NOT NULL);
        CREATE TABLE chunks(
            id INTEGER PRIMARY KEY, target TEXT NOT NULL, line INTEGER NOT NULL,
            end_line INTEGER NOT NULL, heading TEXT NOT NULL, title TEXT NOT NULL,
            body TEXT NOT NULL, content_hash TEXT NOT NULL,
            UNIQUE(target, line));
        CREATE VIRTUAL TABLE lex USING fts5(target, title, heading, body,
            tokenize='unicode61 remove_diacritics 2');
    """)
    trigram = meta["capabilities"]["trigram"]
    if trigram:
        con.execute("CREATE VIRTUAL TABLE tri USING fts5(target, title, heading, body, tokenize='trigram')")
    for target, record in sorted(snapshot.records.items()):
        parts = chunks(record["content"])
        title = document_title(target, parts)
        for chunk in parts:
            heading = " > ".join(chunk.heading_path)
            rowid = con.execute("INSERT INTO chunks(target,line,end_line,heading,title,body,content_hash) VALUES(?,?,?,?,?,?,?)",
                                (target, chunk.line, chunk.end_line, heading, title, chunk.body,
                                 record["content_hash"])).lastrowid
            values = (rowid, *(normalize(v) for v in (target, title, heading, chunk.body)))
            con.execute("INSERT INTO lex(rowid,target,title,heading,body) VALUES(?,?,?,?,?)", values)
            if trigram:
                con.execute("INSERT INTO tri(rowid,target,title,heading,body) VALUES(?,?,?,?,?)", values)
    con.execute("INSERT INTO meta VALUES(?)", (json.dumps(meta, sort_keys=True),))
    con.commit()


def _open_readonly(file: Path) -> sqlite3.Connection:
    con = sqlite3.connect(file.as_uri() + "?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA query_only=ON")
    return con


def _unsafe_cache(file: Path) -> bool:
    return any(p.is_symlink() for p in (file, *file.parents)) or (file.exists() and not file.is_file())


@contextmanager
def projection(snapshot: Snapshot, cache_root: Path | None = None,
               force: bool = False) -> Iterator[tuple[sqlite3.Connection, dict, list[dict]]]:
    caps = capabilities()
    require(caps["fts5"], "FTS5_UNAVAILABLE", "Use a Python build with SQLite FTS5; exact get and owners remain available")
    meta = _metadata(snapshot, caps)
    warnings = [] if caps["trigram"] else [{"code": "TRIGRAM_UNAVAILABLE",
                "message": "Token/prefix BM25 search is available; substring and fuzzy channels are disabled"}]
    con = None
    file = None
    status = "memory"
    try:
        if cache_root is not None:
            scope = {k: snapshot.identity.get(k) for k in ("repository", "kind", "initiative_id", "canonical_ref")}
            # Use one replaceable projection per scope, not an ever-growing snapshot history.
            file = Path(os.path.abspath(cache_root)) / (digest(scope) + ".sqlite")
            try:
                if _unsafe_cache(file):
                    raise OSError("The cache path must contain no symlinks or special files")
                existed = file.exists()
                if existed and not force:
                    try:
                        con = _open_readonly(file)
                        valid = con.execute("PRAGMA quick_check").fetchone()[0] == "ok"
                        valid = valid and json.loads(con.execute("SELECT value FROM meta").fetchone()[0]) == meta
                        # Check required tables now, rather than failing after reporting reuse.
                        con.execute("SELECT count(*) FROM chunks").fetchone()
                        con.execute("SELECT count(*) FROM lex").fetchone()
                        if caps["trigram"]:
                            con.execute("SELECT count(*) FROM tri").fetchone()
                        if valid:
                            status = "reused"
                        else:
                            con.close(); con = None
                    except (sqlite3.DatabaseError, ValueError, TypeError, IndexError):
                        if con is not None:
                            con.close(); con = None
                        warnings.append({"code": "CACHE_REBUILT", "message": "Invalid retrieval cache was discarded"})
                if con is None:
                    file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    fd, name = tempfile.mkstemp(prefix=".retrieval-", suffix=".sqlite", dir=file.parent)
                    os.close(fd)
                    temporary = Path(name)
                    try:
                        writer = sqlite3.connect(temporary)
                        try:
                            _populate(writer, snapshot, meta)
                        finally:
                            writer.close()
                        # Retain this exact inode even if a simultaneous builder publishes another snapshot.
                        con = _open_readonly(temporary)
                        os.replace(temporary, file)
                    finally:
                        temporary.unlink(missing_ok=True)
                    status = "rebuilt" if existed else "built"
            except (OSError, sqlite3.DatabaseError) as exc:
                if con is not None:
                    con.close(); con = None
                warnings.append({"code": "CACHE_UNAVAILABLE", "message": "Using an in-memory index: " + str(exc)})
                file = None
        if con is None:
            con = sqlite3.connect(":memory:")
            con.row_factory = sqlite3.Row
            _populate(con, snapshot, meta)
            status = "memory"
        info = {"status": status, "path": str(file) if file else None, "fingerprint": snapshot.fingerprint,
                "documents": len(snapshot.records), "chunks": con.execute("SELECT count(*) FROM chunks").fetchone()[0],
                "capabilities": caps}
        yield con, info, warnings
    except sqlite3.DatabaseError as exc:
        raise OrchiError("RETRIEVAL_ERROR", "SQLite retrieval failed; rebuild the disposable index with index --force") from exc
    finally:
        if con is not None:
            con.close()


def index(snapshot: Snapshot, cache_root: Path | None = None, force: bool = False) -> dict:
    with projection(snapshot, cache_root, force) as (_, info, warnings):
        return {"scope": snapshot.identity["scope"], "snapshot": snapshot.identity,
                "index": info, "diagnostics": [*snapshot.diagnostics, *warnings]}


def _quoted(term: str) -> str:
    return '"' + term.replace('"', '""') + '"'


def _windows(term: str) -> set[str]:
    return {term[i:i + 4] for i in range(len(term) - 3)}


def _fuzzy_term(term: str, words: set[str]) -> bool:
    if len(term) < 4:
        return False
    grams = _windows(term)
    threshold = max(1, math.ceil(len(grams) / 5))
    for word in words:
        if abs(len(word) - len(term)) > max(2, len(term) // 3):
            continue
        if sum(g in word for g in grams) >= threshold and SequenceMatcher(None, term, word, autojunk=False).ratio() >= 0.72:
            return True
    return False


def _coverage(terms: list[str], text: str, fuzzy: bool) -> tuple[int, bool]:
    folded = normalize(text)
    words = set(WORD.findall(folded)) if fuzzy else set()
    direct = sum(term in folded for term in terms)
    extra = sum(term not in folded and _fuzzy_term(term, words) for term in terms) if fuzzy else 0
    return direct + extra, extra > 0


def _snippet(chunk: Chunk, terms: list[str]) -> tuple[str, int]:
    lines = chunk.body.splitlines()
    # Prefer a line matching the most query terms, then an actual body line over its heading.
    best = max(range(len(lines)), key=lambda i: (_coverage(terms, lines[i], False)[0],
                                                _coverage(terms, lines[i], True)[0],
                                                not bool(ATX.match(lines[i])), -i))
    selected = lines[best].strip()
    # Long lines are cropped near a hit rather than always showing their beginning.
    folded = normalize(selected)
    positions = [folded.find(t) for t in terms if t in folded]
    offset = max(0, (min(positions) if positions else 0) - 70)
    # Normalization can change character counts. Offsets are only a cropping hint,
    # never exposed as exact columns; the returned text always comes from the source.
    offset = min(offset, max(0, len(selected) - (SNIPPET_CHARS - 2)))
    snippet = selected[offset:offset + SNIPPET_CHARS - 2]
    if offset:
        snippet = "…" + snippet
    if offset + SNIPPET_CHARS - 2 < len(selected):
        snippet += "…"
    return snippet, chunk.line + best


def _query(con: sqlite3.Connection, table: str, expression: str, limit: int) -> list[sqlite3.Row]:
    # Table identifiers are fixed by the caller; user input is only a bound MATCH value.
    require(table in {"lex", "tri"}, "RETRIEVAL_ERROR", "Unknown search channel")
    return con.execute(f"SELECT c.*, bm25({table},1.5,2.0,4.0,1.0) AS rank "
                       f"FROM {table} JOIN chunks c ON c.id={table}.rowid WHERE {table} MATCH ? "
                       f"ORDER BY rank, c.target, c.line LIMIT ?", (expression, limit)).fetchall()


def _rank(con: sqlite3.Connection, snapshot: Snapshot, terms: list[str], limit: int,
          caps: dict) -> tuple[list[dict], bool]:
    pool = max(64, limit * 8)
    channels = [("bm25", "lex", " OR ".join(_quoted(t) + "*" for t in terms), 1.0)]
    if caps["trigram"]:
        substrings = [t for t in terms if len(t) >= 3]
        grams = sorted({g for term in terms for g in _windows(term)})
        if substrings:
            channels.append(("trigram", "tri", " OR ".join(map(_quoted, substrings)), 0.6))
        if grams:
            channels.append(("fuzzy", "tri", " OR ".join(map(_quoted, grams)), 0.3))
    candidates: dict[tuple[str, int], dict] = {}
    checked: dict[str, tuple[str, dict[int, Chunk]]] = {}
    for via, table, expression, weight in channels:
        for rank, row in enumerate(_query(con, table, expression, pool), 1):
            target = row["target"]
            record = snapshot.records.get(target)
            # A projection may find candidates; it may never invent source content.
            require(record is not None and row["content_hash"] == record["content_hash"],
                    "CACHE_ENTRY_MISMATCH", "Cached source identity differs from resolved knowledge")
            if target not in checked:
                parts = chunks(record["content"])
                checked[target] = (document_title(target, parts), {c.line: c for c in parts})
            title, parts_by_line = checked[target]
            chunk = parts_by_line.get(row["line"])
            require(chunk is not None and chunk.end_line == row["end_line"] and chunk.body == row["body"]
                    and " > ".join(chunk.heading_path) == row["heading"] and title == row["title"],
                    "CACHE_ENTRY_MISMATCH", "Cached excerpt differs from resolved knowledge")
            searchable = "\n".join((target, title, *chunk.heading_path, chunk.body))
            coverage, fuzzy_match = _coverage(terms, searchable, via == "fuzzy")
            # Four-character windows are candidate generators, not evidence of a typo match.
            if via == "fuzzy" and not fuzzy_match:
                continue
            key = (target, chunk.line)
            if key not in candidates:
                snippet, snippet_line = _snippet(chunk, terms)
                candidates[key] = {k: record[k] for k in ("target", "layer", "source_commit", "source_path", "content_hash")}
                candidates[key].update(title=title, heading=chunk.heading, heading_path=list(chunk.heading_path),
                                       line=chunk.line, end_line=chunk.end_line, snippet=snippet, snippet_line=snippet_line,
                                       score=0.0, matched_terms=0, via=[])
            candidate = candidates[key]
            # BM25 scores from different tokenizers are not comparable. Fuse ranks instead.
            candidate["score"] += weight / (60 + rank)
            candidate["matched_terms"] = max(candidate["matched_terms"], coverage)
            candidate["via"].append(via)
    ordered = sorted(candidates.values(), key=lambda r: (-r["matched_terms"], -r["score"], r["target"], r["line"]))
    for result in ordered[:limit]:
        result["score"] = round(result["score"], 8)
    return ordered[:limit], len(ordered) > limit


def search(snapshot: Snapshot, query: str, limit: int = 8, cache_root: Path | None = None) -> dict:
    terms = query_terms(query)
    require(isinstance(limit, int) and not isinstance(limit, bool) and 1 <= limit <= MAX_RESULTS,
            "INVALID_LIMIT", "limit must be between 1 and 100")
    recovered = []
    for force in (False, True):
        try:
            with projection(snapshot, cache_root, force) as (con, info, warnings):
                results, truncated = _rank(con, snapshot, terms, limit, info["capabilities"])
                return {"scope": snapshot.identity["scope"], "query": query, "limit": limit,
                        "snapshot": snapshot.identity, "index": info, "results": results,
                        "truncated": truncated, "diagnostics": [*snapshot.diagnostics, *recovered, *warnings]}
        except OrchiError as exc:
            if force or exc.code not in {"CACHE_ENTRY_MISMATCH", "RETRIEVAL_ERROR"}:
                raise
            recovered.append({"code": "CACHE_REBUILT", "message": "Search projection failed validation and was rebuilt"})
    raise AssertionError("Unreachable retrieval retry")


def format_text(result: dict) -> str:
    """Human rendering is opt-in; JSON remains the agent-facing protocol."""
    def display(value: str) -> str:
        return json.dumps(value, ensure_ascii=False)[1:-1]
    lines = ["Scope: " + display(result["scope"]) + " | snapshot: " + result["index"]["fingerprint"]]
    for hit in result["results"]:
        lines.append(f"{display(hit['target'])}:{hit['line']}-{hit['end_line']} | "
                     f"{display(' > '.join(hit['heading_path']) or hit['title'])} | {','.join(hit['via'])}")
        lines.append("  " + display(hit["snippet"]))
        lines.append(f"  {hit['layer']} | {hit['source_commit']}:{display(hit['source_path'])} | sha256:{hit['content_hash']}")
    if not result["results"]:
        lines.append("No matching knowledge.")
    for warning in result["diagnostics"]:
        lines.append("Warning: " + display(warning["code"] + " " + warning.get("target", warning.get("message", ""))))
    return "\n".join(lines)
