"""Explicit Agent/0.10 binding with an isolated durable program store."""
from .budget_protocol import BudgetProtocol
from .program_bindings import ProgramBinding
from .profile_capabilities import RING_LOFT_PROFILE


SCHEMA_VERSION = "ontokin.agent/0.10"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.10", RING_LOFT_PROFILE,
    "ontokin.glb/0.10", "ring-loft-program-agent.sqlite3",
    "ontokin.ring-loft-program-agent-store/0.1", True, True)


class RingLoftProtocol(BudgetProtocol):
    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = RING_LOFT_PROFILE
    destination = DEFINITION.destination
