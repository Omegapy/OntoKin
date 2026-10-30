"""Matched polygon sections under the shared request-budget lifecycle."""
from .budget_agent import BudgetAgentService
from .budget_program_runtime import BudgetProgramRuntime
from .ring_loft_protocol import RingLoftProtocol, SCHEMA_VERSION
from .profile_capabilities import RING_LOFT_PROFILE


class RingLoftProgramRuntime(BudgetProgramRuntime):
    profile = RING_LOFT_PROFILE


class RingLoftAgentService(BudgetAgentService):
    """Select .10 explicitly without changing earlier protocol or store routes."""

    protocol_type = RingLoftProtocol
    runtime_type = RingLoftProgramRuntime

    @staticmethod
    def catalog(**kwargs):
        from .ring_loft_agent_catalog import catalog
        return catalog(**kwargs)

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)
