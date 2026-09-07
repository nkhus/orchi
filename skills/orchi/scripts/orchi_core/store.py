"""Single transactional aggregate plus immutable, content-addressed audit artifacts."""
from __future__ import annotations
from contextlib import contextmanager
import json
import os
import tempfile
from pathlib import Path
import sqlite3
import time
from .common import canonical, digest, require


class Store:
    def __init__(self, directory: str | Path):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "state.sqlite"
        with self.connect() as con:
            con.executescript("""
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS state(id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at REAL NOT NULL, kind TEXT NOT NULL, state_hash TEXT NOT NULL);
            """)

    def connect(self):
        c = sqlite3.connect(self.db, timeout=30, isolation_level=None)
        c.execute("PRAGMA busy_timeout=30000")
        c.execute("PRAGMA synchronous=FULL")
        return c

    def read(self) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT data FROM state WHERE id=1").fetchone()
        require(row is not None, "NOT_INITIALIZED", "Initialize an operator control directory first")
        return json.loads(row[0])

    def initialize(self, state: dict):
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            require(con.execute("SELECT 1 FROM state").fetchone() is None, "ALREADY_INITIALIZED", str(self.root))
            con.execute("INSERT INTO state VALUES(1, ?)", (canonical(state).decode(),))
            con.execute("INSERT INTO events(at,kind,state_hash) VALUES(?,?,?)", (time.time(), "setup", digest(state)))
            con.commit()

    @contextmanager
    def transaction(self, kind: str):
        con = self.connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT data FROM state WHERE id=1").fetchone()
            require(row is not None, "NOT_INITIALIZED", "Missing controller state")
            s = json.loads(row[0])
            yield s
            con.execute("UPDATE state SET data=? WHERE id=1", (canonical(s).decode(),))
            con.execute("INSERT INTO events(at,kind,state_hash) VALUES(?,?,?)", (time.time(), kind, digest(s)))
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def artifact(self, value: dict) -> str:
        data = canonical(value)
        oid = digest(value)
        directory = self.root / "artifacts"
        directory.mkdir(exist_ok=True)
        p = directory / (oid + ".json")
        if p.exists():
            require(p.read_bytes() == data, "ARTIFACT_CORRUPT", oid)
            return oid
        # Publish a fully written blob atomically. No reader can see a partially written
        # digest path, including concurrent identical writers or a process interruption.
        fd, temporary = tempfile.mkstemp(prefix=".pending-", dir=directory)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            try:
                os.link(temporary, p)
            except FileExistsError:
                require(p.read_bytes() == data, "ARTIFACT_CORRUPT", oid)
            if os.name == "posix":
                d = os.open(directory, os.O_RDONLY)
                try:
                    os.fsync(d)
                finally:
                    os.close(d)
        finally:
            os.unlink(temporary)
        return oid

    def get_artifact(self, oid: str) -> dict:
        require(len(oid) == 64 and all(c in "0123456789abcdef" for c in oid), "INVALID_ID", oid)
        p = self.root / "artifacts" / (oid + ".json")
        value = json.loads(p.read_bytes())
        require(digest(value) == oid, "ARTIFACT_CORRUPT", oid)
        return value
