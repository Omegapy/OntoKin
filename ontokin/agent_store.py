"""Local SQLite durability and fencing for the OntoKin agent service.

All accepted source, run changes, artifact bytes, and their terminal request
result share one transaction. This store is designed for one host's local
filesystem. It is not a distributed lease or a multi-tenant network server.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import time
import uuid

from .agent_protocol import ProtocolError, envelope
from .diagnostics import Source

STORE_VERSION = "ontokin.agent-store/0.1"


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _process_start(pid: int) -> str | None:
    """Linux start ticks disambiguate PID reuse; elsewhere liveness is conservative."""
    try:
        # The executable name in parentheses may contain spaces and parentheses.
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return fields[19]
    except (OSError, IndexError):
        return None


class AgentStore:
    database_name = "agent.sqlite3"
    schema_version = STORE_VERSION
    revision_key = "source_revision"
    envelope = staticmethod(envelope)

    def __init__(self, path: Path, implementation: dict):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.database_path = self.path / self.database_name
        self.owner = "worker:" + uuid.uuid4().hex
        self.host, self.pid = socket.gethostname(), os.getpid()
        self.closed = False
        self.implementation = implementation
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, accepted_revision TEXT);
                CREATE TABLE IF NOT EXISTS sources (
                    project_id TEXT NOT NULL, revision TEXT NOT NULL, filename TEXT NOT NULL,
                    raw BLOB NOT NULL, accepted_once INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (project_id, revision));
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY, pid INTEGER NOT NULL, host TEXT NOT NULL,
                    process_start TEXT, closed INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS requests (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL, id TEXT NOT NULL, operation TEXT NOT NULL,
                    digest TEXT NOT NULL, payload TEXT, state TEXT NOT NULL, engine TEXT,
                    response TEXT NOT NULL, cancel_requested INTEGER NOT NULL DEFAULT 0,
                    owner TEXT, created REAL NOT NULL, updated REAL NOT NULL,
                    UNIQUE (project_id, id));
                CREATE INDEX IF NOT EXISTS pending_requests ON requests(state, sequence);
                CREATE TABLE IF NOT EXISTS runs (
                    project_id TEXT NOT NULL, id TEXT NOT NULL, source_revision TEXT NOT NULL,
                    descriptor TEXT NOT NULL, version INTEGER NOT NULL,
                    PRIMARY KEY (project_id, id));
                CREATE TABLE IF NOT EXISTS artifacts (
                    project_id TEXT NOT NULL, id TEXT NOT NULL, source_revision TEXT NOT NULL,
                    data BLOB NOT NULL, report TEXT NOT NULL, sha256 TEXT NOT NULL,
                    PRIMARY KEY (project_id, id));
            """)
            # Pre-release stores can identify old receipts without ever replaying them.
            if "engine" not in {column["name"] for column in db.execute("PRAGMA table_info(requests)")}:
                db.execute("ALTER TABLE requests ADD COLUMN engine TEXT")
        with self.transaction() as db:
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('schema_version', ?)", (self.schema_version,))
            version = db.execute("SELECT value FROM metadata WHERE name='schema_version'").fetchone()[0]
            if version != self.schema_version:
                raise ProtocolError("OKA-E-STORE-VERSION", "This store uses an unsupported schema version.", actual=version)
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('cursor_secret', ?)", (secrets.token_hex(32),))
            self.cursor_secret = bytes.fromhex(db.execute("SELECT value FROM metadata WHERE name='cursor_secret'").fetchone()[0])
            self.recover(db)
            db.execute("INSERT INTO sessions (id,pid,host,process_start) VALUES (?,?,?,?)",
                       (self.owner, self.pid, self.host, _process_start(self.pid)))

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.database_path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def transaction(self):
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    @staticmethod
    def accepted(db, project: str) -> str | None:
        row = db.execute("SELECT accepted_revision FROM projects WHERE id=?", (project,)).fetchone()
        return row[0] if row is not None else None

    @staticmethod
    def request(db, project: str, request_id: str):
        return db.execute("SELECT * FROM requests WHERE project_id=? AND id=?", (project, request_id)).fetchone()

    def record(self, db, request: dict, digest: str, payload: str, response: dict) -> None:
        now = time.time()
        db.execute("INSERT INTO requests (project_id,id,operation,digest,payload,state,response,created,updated,engine) VALUES (?,?,?,?,?,?,?,?,?,?)",
                   (request["project_id"], request["request_id"], request["operation"], digest, payload,
                    response["status"], dumps(response), now, now, dumps(self.implementation)))

    @staticmethod
    def update_response(db, project: str, request_id: str, response: dict) -> None:
        db.execute("UPDATE requests SET state=?,response=?,updated=? WHERE project_id=? AND id=?",
                   (response["status"], dumps(response), time.time(), project, request_id))

    @staticmethod
    def snapshot(db, project: str, source: Source) -> None:
        db.execute("INSERT OR IGNORE INTO sources (project_id,revision,filename,raw) VALUES (?,?,?,?)",
                   (project, source.revision, source.filename, source.raw))

    def read_source(self, project: str, revision: str) -> Source:
        with self.connection() as db:
            row = db.execute("SELECT * FROM sources WHERE project_id=? AND revision=?", (project, revision)).fetchone()
        if row is None:
            raise ProtocolError("OKL-E-REVISION", "The source revision is not present in this project.", source_revision=revision)
        raw = bytes(row["raw"])
        source = Source(raw.decode("utf-8"), row["filename"], raw)
        if source.revision != revision:
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "Stored source bytes do not match their immutable revision.")
        return source

    def source_accepted_once(self, project: str, revision: str) -> bool:
        with self.connection() as db:
            row = db.execute("SELECT accepted_once FROM sources WHERE project_id=? AND revision=?", (project, revision)).fetchone()
        return bool(row and row[0])

    def read_run(self, project: str, run_id: str) -> tuple[dict, int]:
        with self.connection() as db:
            row = db.execute("SELECT * FROM runs WHERE project_id=? AND id=?", (project, run_id)).fetchone()
        if row is None:
            raise ProtocolError("OKL-E-SAMPLE", "The supplied run identity does not exist in this project.", run_id=run_id)
        return json.loads(row["descriptor"]), row["version"]

    def unknown(self, db, row, reason: str) -> dict:
        old = json.loads(row["response"])
        result = self.envelope({"project_id": row["project_id"], "request_id": row["id"], "operation": row["operation"]},
                          "unknown_outcome", self.accepted(db, row["project_id"]))
        result[self.revision_key] = old.get(self.revision_key)
        result["requested_level"] = old.get("requested_level")
        result["protocol_error"] = {"code": "OKA-E-UNKNOWN-OUTCOME", "message": reason,
                                    "details": {"replay_permitted": False, "reconcile": "Inspect the accepted revision and existing run before deliberately issuing new work."}}
        self.update_response(db, row["project_id"], row["id"], result)
        db.execute("UPDATE requests SET payload=NULL,owner=NULL WHERE project_id=? AND id=?", (row["project_id"], row["id"]))
        return result

    def recover(self, db) -> None:
        """Fence proven-dead local workers; never steal a live worker's request."""
        rows = db.execute("SELECT DISTINCT s.* FROM sessions s JOIN requests r ON r.owner=s.id WHERE r.state='running'").fetchall()
        for session in rows:
            dead = bool(session["closed"])
            if not dead and session["host"] == self.host:
                try:
                    os.kill(session["pid"], 0)
                except ProcessLookupError:
                    dead = True
                except PermissionError:
                    pass
                start = _process_start(session["pid"])
                if start is not None and session["process_start"] is not None and start != session["process_start"]:
                    dead = True
            if dead:
                for row in db.execute("SELECT * FROM requests WHERE owner=? AND state='running'", (session["id"],)).fetchall():
                    self.unknown(db, row, "The worker stopped before a terminal result was retained; this identity is fenced against replay.")
                db.execute("UPDATE sessions SET closed=1 WHERE id=?", (session["id"],))

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        with self.transaction() as db:
            db.execute("UPDATE sessions SET closed=1 WHERE id=?", (self.owner,))
            for row in db.execute("SELECT * FROM requests WHERE owner=? AND state='running'", (self.owner,)).fetchall():
                self.unknown(db, row, "The service closed while this work was running; no replay is authorized.")
