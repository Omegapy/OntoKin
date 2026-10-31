"""A separate durable source-and-asset store for Agent/0.13."""
from __future__ import annotations

import json

from .agent_protocol import ProtocolError
from .budget_agent import BudgetProgramStore
from .bundle import BundleError
from .texture_bundle import load_texture_bundle
from .texture_protocol import TextureProtocol


class TextureProgramStore(BudgetProgramStore):
    """Retain exact attachment bytes in the immutable bundle snapshot."""

    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or TextureProtocol())

    def read_source(self, project, revision):
        with self.connection() as db:
            row = db.execute("SELECT raw FROM sources WHERE project_id=? AND revision=?",
                             (project, revision)).fetchone()
        if row is None:
            raise ProtocolError("OKL-E-REVISION", "The program revision is absent from this project.",
                                program_revision=revision)
        try:
            program = load_texture_bundle(json.loads(bytes(row["raw"]).decode("utf-8")))
        except (ValueError, UnicodeError, BundleError) as exc:
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "The retained source-and-asset payload is invalid.") from exc
        if program.program_revision != revision:
            raise ProtocolError("OKA-E-STORE-INTEGRITY", "Retained source and asset bytes differ from their revision.")
        return program
