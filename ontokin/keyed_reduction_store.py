"""Independent .15 storage for immutable source and image revisions."""
from .keyed_reduction_protocol import KeyedReductionProtocol
from .texture_store import TextureProgramStore


class KeyedReductionProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedReductionProtocol())
