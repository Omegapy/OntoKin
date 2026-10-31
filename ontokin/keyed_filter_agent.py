"""Durable .16 authoring, scoped repairs and recorded artifact retrieval."""
from .keyed_filter_program_runtime import KeyedFilterProgramRuntime
from .keyed_filter_protocol import KeyedFilterProtocol, SCHEMA_VERSION
from .keyed_filter_store import KeyedFilterProgramStore
from .texture_agent import TextureAgentService


class KeyedFilterAgentService(TextureAgentService):
    protocol_type = KeyedFilterProtocol
    runtime_type = KeyedFilterProgramRuntime
    store_type = KeyedFilterProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_filter_agent_catalog import catalog
        return catalog(**kwargs)
