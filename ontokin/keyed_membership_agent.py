"""Durable .21 membership, scoped source repairs and recorded delivery."""
from .keyed_membership_program_runtime import KeyedMembershipProgramRuntime
from .keyed_membership_protocol import KeyedMembershipProtocol, SCHEMA_VERSION
from .keyed_membership_store import KeyedMembershipProgramStore
from .texture_agent import TextureAgentService


class KeyedMembershipAgentService(TextureAgentService):
    protocol_type = KeyedMembershipProtocol
    runtime_type = KeyedMembershipProgramRuntime
    store_type = KeyedMembershipProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @staticmethod
    def catalog(**kwargs):
        from .keyed_membership_agent_catalog import catalog
        return catalog(**kwargs)
