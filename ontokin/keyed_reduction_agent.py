"""Durable .15 authoring, scoped repairs and recorded artifact retrieval."""
from .keyed_reduction_program_runtime import KeyedReductionProgramRuntime
from .keyed_reduction_protocol import KeyedReductionProtocol, SCHEMA_VERSION
from .keyed_reduction_store import KeyedReductionProgramStore
from .texture_agent import TextureAgentService


class KeyedReductionAgentService(TextureAgentService):
    protocol_type = KeyedReductionProtocol
    runtime_type = KeyedReductionProgramRuntime
    store_type = KeyedReductionProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_reduction_agent_catalog import catalog
        return catalog(**kwargs)
