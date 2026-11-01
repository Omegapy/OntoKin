"""Independent .18 storage for immutable source and image revisions."""
from .keyed_zip_protocol import KeyedZipProtocol
from .texture_store import TextureProgramStore


class KeyedZipProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedZipProtocol())
