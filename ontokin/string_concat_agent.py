"""Durable .20 String concatenation, scoped repairs and recorded artifact retrieval."""
from .string_concat_program_runtime import StringConcatProgramRuntime
from .string_concat_protocol import StringConcatProtocol, SCHEMA_VERSION
from .string_concat_store import StringConcatProgramStore
from .texture_agent import TextureAgentService


class StringConcatAgentService(TextureAgentService):
    protocol_type = StringConcatProtocol
    runtime_type = StringConcatProgramRuntime
    store_type = StringConcatProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .string_concat_agent_catalog import catalog
        return catalog(**kwargs)
