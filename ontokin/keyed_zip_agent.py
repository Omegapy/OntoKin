"""Durable .18 authoring, scoped repairs and recorded artifact retrieval."""
from .keyed_zip_program_runtime import KeyedZipProgramRuntime
from .keyed_zip_protocol import KeyedZipProtocol, SCHEMA_VERSION
from .keyed_zip_store import KeyedZipProgramStore
from .texture_agent import TextureAgentService


class KeyedZipAgentService(TextureAgentService):
    protocol_type = KeyedZipProtocol
    runtime_type = KeyedZipProgramRuntime
    store_type = KeyedZipProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_zip_agent_catalog import catalog
        return catalog(**kwargs)
