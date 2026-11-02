"""Independent .21 storage for immutable source and image revisions."""
from .keyed_membership_protocol import KeyedMembershipProtocol
from .texture_store import TextureProgramStore


class KeyedMembershipProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedMembershipProtocol())
