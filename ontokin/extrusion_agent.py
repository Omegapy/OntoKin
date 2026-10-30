"""Source-authored polygon requests with the shared execution-budget lifecycle."""
from .budget_agent import BudgetAgentService
from .budget_program_runtime import BudgetProgramRuntime
from .extrusion_protocol import ExtrusionProtocol, SCHEMA_VERSION
from .profile_capabilities import EXTRUSION_PROFILE


class ExtrusionProgramRuntime(BudgetProgramRuntime):
    profile = EXTRUSION_PROFILE


class ExtrusionAgentService(BudgetAgentService):
    """Select .8 explicitly and retain separate durable source/run/artifact state."""

    protocol_type = ExtrusionProtocol
    runtime_type = ExtrusionProgramRuntime

    @staticmethod
    def catalog(**kwargs):
        from .extrusion_agent_catalog import catalog
        return catalog(**kwargs)

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)
