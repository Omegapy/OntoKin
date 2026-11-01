"""Independent .17 storage for immutable source and image revisions."""
from .keyed_merge_protocol import KeyedMergeProtocol
from .texture_store import TextureProgramStore


class KeyedMergeProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedMergeProtocol())
