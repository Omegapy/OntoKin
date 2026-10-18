"""Independent durable program snapshots using the tested local lifecycle store.

SQL document-key columns retain their internal names; public revisions are always
program revisions, and every source file keeps its own immutable content hash.
No core0.1 database is migrated or opened by this binding.
"""
from __future__ import annotations

import json

from .agent_store import AgentStore, dumps
from .agent_protocol import ProtocolError
from .bundle import load_bundle, BundleError
from . import program_protocol


class ProgramStore(AgentStore):
    database_name = "program-agent.sqlite3"
    schema_version = "ontokin.program-agent-store/0.1"
    revision_key = "program_revision"
    envelope = staticmethod(program_protocol.envelope)

    def __init__(self, path, implementation, *, protocol=None):
        binding = protocol or program_protocol.bind()
        self.envelope = binding.envelope
        self.database_name = binding.definition.store_filename
        self.schema_version = binding.definition.store_schema
        super().__init__(path, implementation)

    @staticmethod
    def snapshot(db, project, program):
        raw = dumps(program.to_payload()).encode("utf-8")
        db.execute("INSERT OR IGNORE INTO sources (project_id,revision,filename,raw) VALUES (?,?,?,?)",
                   (project, program.program_revision, "<program-bundle>", raw))

    def read_source(self, project, revision):
        with self.connection() as db:
            row = db.execute("SELECT raw FROM sources WHERE project_id=? AND revision=?", (project, revision)).fetchone()
        if row is None:
            raise ProtocolError("OKL-E-REVISION", "The program revision is absent from this project.", program_revision=revision)
        try:
            program = load_bundle(json.loads(bytes(row["raw"]).decode("utf-8")))
        except (ValueError, UnicodeError, BundleError) as exc:
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "The retained program payload is invalid.") from exc
        if program.program_revision != revision:
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "Stored sources do not match their immutable program revision.")
        return program
