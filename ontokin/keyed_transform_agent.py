"""Durable .14 authoring, scoped repairs and recorded artifact retrieval."""
from .keyed_transform_program_runtime import KeyedTransformProgramRuntime
from .keyed_transform_protocol import KeyedTransformProtocol, SCHEMA_VERSION
from .keyed_transform_store import KeyedTransformProgramStore
from .texture_agent import TextureAgentService


class KeyedTransformAgentService(TextureAgentService):
    protocol_type = KeyedTransformProtocol
    runtime_type = KeyedTransformProgramRuntime
    store_type = KeyedTransformProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_transform_agent_catalog import catalog
        return catalog(**kwargs)
