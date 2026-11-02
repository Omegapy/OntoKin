"""Independent .20 storage for immutable source and image revisions."""
from .string_concat_protocol import StringConcatProtocol
from .texture_store import TextureProgramStore


class StringConcatProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or StringConcatProtocol())
