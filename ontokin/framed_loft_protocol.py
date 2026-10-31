"""Explicit Agent/0.11 binding and its independent durable program store."""
from .budget_protocol import BudgetProtocol
from .program_bindings import ProgramBinding
from .profile_capabilities import FRAMED_LOFT_PROFILE


SCHEMA_VERSION = "ontokin.agent/0.11"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.11", FRAMED_LOFT_PROFILE,
    "ontokin.glb/0.11", "framed-loft-program-agent.sqlite3",
    "ontokin.framed-loft-program-agent-store/0.1", True, True)


class FramedLoftProtocol(BudgetProtocol):
    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = FRAMED_LOFT_PROFILE
    destination = DEFINITION.destination
