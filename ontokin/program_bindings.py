"""Explicit immutable bindings for the inherited program-service lifecycle.

Protocol numbers select contracts, not a version ordering or automatic
migration. This leaf module imports no compiler, evaluator, service or store.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ProgramBinding:
    protocol: str
    language_version: str
    profile: str
    destination: str
    store_filename: str
    store_schema: str
    native_surfaces: bool
    bounded_delivery: bool
    delivery_available: bool = True


PROGRAM_BINDINGS = MappingProxyType({binding.protocol: binding for binding in (
    ProgramBinding("ontokin.agent/0.2", "0.2", "construction-0.1", "ontokin.glb/0.2",
                   "program-agent.sqlite3", "ontokin.program-agent-store/0.1", False, False),
    ProgramBinding("ontokin.agent/0.3", "0.3", "surface-0.1", "ontokin.glb/0.3",
                   "surface-program-agent.sqlite3", "ontokin.surface-program-agent-store/0.1", True, True),
    ProgramBinding("ontokin.agent/0.4", "0.4", "impulse-0.1", "ontokin.glb/0.4",
                   "impulse-program-agent.sqlite3", "ontokin.impulse-program-agent-store/0.1", True, True),
    ProgramBinding("ontokin.agent/0.5", "0.5", "force-0.1", "ontokin.glb/0.5",
                   "force-program-agent.sqlite3", "ontokin.force-program-agent-store/0.1", True, True),
    ProgramBinding("ontokin.agent/0.6", "0.6", "planar-reach-0.1", "ontokin.glb/0.6",
                   "planar-reach-program-agent.sqlite3", "ontokin.planar-reach-program-agent-store/0.1",
                   True, True, delivery_available=False),
)})
PROFILE_BINDINGS = MappingProxyType({binding.profile: binding for binding in PROGRAM_BINDINGS.values()})
