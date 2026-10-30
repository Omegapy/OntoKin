"""Explicit Agent/0.8 polygon binding without changing earlier registries."""
from .budget_protocol import BudgetProtocol
from .program_bindings import ProgramBinding
from .profile_capabilities import EXTRUSION_PROFILE


SCHEMA_VERSION = "ontokin.agent/0.8"
DEFINITION = ProgramBinding(SCHEMA_VERSION, "0.8", EXTRUSION_PROFILE,
    "ontokin.glb/0.8", "extrusion-program-agent.sqlite3",
    "ontokin.extrusion-program-agent-store/0.1", True, True)


class ExtrusionProtocol(BudgetProtocol):
    SCHEMA_VERSION = SCHEMA_VERSION
    definition = DEFINITION
    profile = EXTRUSION_PROFILE
    destination = DEFINITION.destination
