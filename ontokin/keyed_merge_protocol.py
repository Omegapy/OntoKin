"""Explicit .17 binding with the unchanged source and asset request transport."""
from __future__ import annotations

import json

from .agent_protocol import ProtocolError, _bad
from .json_limits import JSONLimitError, bounded_dumps
from .program_bindings import ProgramBinding
from .profile_capabilities import KEYED_MERGE_PROFILE
from .texture_protocol import TextureProtocol, MAX_REQUEST_BYTES


SCHEMA_VERSION = "ontokin.agent/0.17"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.17", KEYED_MERGE_PROFILE,
    "ontokin.glb/0.17", "keyed-merge-program-agent.sqlite3",
    "ontokin.keyed-merge-program-agent-store/0.1", True, True)


def canonical_request(value):
    try:
        payload = bounded_dumps(value, max_bytes=MAX_REQUEST_BYTES)
        clean = json.loads(payload)
    except JSONLimitError as exc:
        raise ProtocolError("OKA-E-RESOURCE", "The request exceeds the Agent/0.17 JSON transport.",
                            **exc.details) from exc
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("OKA-E-REQUEST", "The request requires finite JSON and UTF-8 scalar strings.") from exc
    if not isinstance(clean, dict):
        _bad("A request must be a JSON object.")
    return clean, payload


class KeyedMergeProtocol(TextureProtocol):
    """Select .17 without registering it as a replacement for an older binding."""

    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = KEYED_MERGE_PROFILE
    destination = DEFINITION.destination
    canonical_request = staticmethod(canonical_request)
