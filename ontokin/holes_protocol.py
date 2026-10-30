"""Explicit Agent/0.9 ring binding with its own durable store identity."""
from .budget_protocol import BudgetProtocol
from .program_bindings import ProgramBinding
from .profile_capabilities import HOLES_PROFILE


SCHEMA_VERSION = "ontokin.agent/0.9"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.9", HOLES_PROFILE,
    "ontokin.glb/0.9", "holes-program-agent.sqlite3",
    "ontokin.holes-program-agent-store/0.1", True, True)


class HolesProtocol(BudgetProtocol):
    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = HOLES_PROFILE
    destination = DEFINITION.destination
