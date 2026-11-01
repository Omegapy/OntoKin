"""Independent .16 storage for immutable source and image revisions."""
from .keyed_filter_protocol import KeyedFilterProtocol
from .texture_store import TextureProgramStore


class KeyedFilterProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedFilterProtocol())
