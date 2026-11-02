"""Durable .19 keyed renaming, scoped repairs and recorded artifact retrieval."""
from .keyed_rekey_program_runtime import KeyedRekeyProgramRuntime
from .keyed_rekey_protocol import KeyedRekeyProtocol, SCHEMA_VERSION
from .keyed_rekey_store import KeyedRekeyProgramStore
from .texture_agent import TextureAgentService


class KeyedRekeyAgentService(TextureAgentService):
    protocol_type = KeyedRekeyProtocol
    runtime_type = KeyedRekeyProgramRuntime
    store_type = KeyedRekeyProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_rekey_agent_catalog import catalog
        return catalog(**kwargs)
