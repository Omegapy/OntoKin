"""Authored section frames under the shared request-budget lifecycle."""
from .budget_agent import BudgetAgentService
from .budget_program_runtime import BudgetProgramRuntime
from .framed_loft_protocol import FramedLoftProtocol, SCHEMA_VERSION
from .profile_capabilities import FRAMED_LOFT_PROFILE


class FramedLoftProgramRuntime(BudgetProgramRuntime):
    profile = FRAMED_LOFT_PROFILE


class FramedLoftAgentService(BudgetAgentService):
    """Select .11 explicitly while preserving previous services and stores."""

    protocol_type = FramedLoftProtocol
    runtime_type = FramedLoftProgramRuntime

    @staticmethod
    def catalog(**kwargs):
        from .framed_loft_agent_catalog import catalog
        return catalog(**kwargs)

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)
