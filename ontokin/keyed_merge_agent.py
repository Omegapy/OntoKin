"""Durable .17 authoring, scoped repairs and recorded artifact retrieval."""
from .keyed_merge_program_runtime import KeyedMergeProgramRuntime
from .keyed_merge_protocol import KeyedMergeProtocol, SCHEMA_VERSION
from .keyed_merge_store import KeyedMergeProgramStore
from .texture_agent import TextureAgentService


class KeyedMergeAgentService(TextureAgentService):
    protocol_type = KeyedMergeProtocol
    runtime_type = KeyedMergeProgramRuntime
    store_type = KeyedMergeProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_merge_agent_catalog import catalog
        return catalog(**kwargs)
