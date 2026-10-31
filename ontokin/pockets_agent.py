"""Blind polygon pockets under the existing cumulative request lifecycle."""
from .budget_agent import BudgetAgentService
from .budget_program_runtime import BudgetProgramRuntime
from .pockets_protocol import PocketsProtocol, SCHEMA_VERSION
from .pockets_agent_catalog import catalog as pockets_catalog
from .profile_capabilities import POCKETS_PROFILE


class PocketsProgramRuntime(BudgetProgramRuntime):
    profile = POCKETS_PROFILE


class PocketsAgentService(BudgetAgentService):
    """Select .12 explicitly with its own accepted revisions and artifacts."""

    protocol_type = PocketsProtocol
    runtime_type = PocketsProgramRuntime

    @staticmethod
    def catalog(**kwargs):
        return pockets_catalog(**kwargs)

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)
