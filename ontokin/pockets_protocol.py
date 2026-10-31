"""Explicit Agent/0.12 binding for a separate pocket-program store."""
from .budget_protocol import BudgetProtocol
from .program_bindings import ProgramBinding
from .profile_capabilities import POCKETS_PROFILE


SCHEMA_VERSION = "ontokin.agent/0.12"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.12", POCKETS_PROFILE,
    "ontokin.glb/0.12", "pockets-program-agent.sqlite3",
    "ontokin.pockets-program-agent-store/0.1", True, True)


class PocketsProtocol(BudgetProtocol):
    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = POCKETS_PROFILE
    destination = DEFINITION.destination
