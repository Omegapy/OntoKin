"""Source-authored openings with the shared execution-budget lifecycle."""
from .budget_agent import BudgetAgentService
from .budget_program_runtime import BudgetProgramRuntime
from .holes_protocol import HolesProtocol, SCHEMA_VERSION
from .profile_capabilities import HOLES_PROFILE


class HolesProgramRuntime(BudgetProgramRuntime):
    profile = HOLES_PROFILE


class HolesAgentService(BudgetAgentService):
    """Select .9 explicitly while retaining source, run and artifact isolation."""

    protocol_type = HolesProtocol
    runtime_type = HolesProgramRuntime

    @staticmethod
    def catalog(**kwargs):
        from .holes_agent_catalog import catalog
        return catalog(**kwargs)

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)
