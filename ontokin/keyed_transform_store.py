"""Independent .14 storage for immutable source and image revisions."""
from .keyed_transform_protocol import KeyedTransformProtocol
from .texture_store import TextureProgramStore


class KeyedTransformProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedTransformProtocol())
