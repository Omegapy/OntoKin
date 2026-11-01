"""Independent .19 storage for immutable source and image revisions."""
from .keyed_rekey_protocol import KeyedRekeyProtocol
from .texture_store import TextureProgramStore


class KeyedRekeyProgramStore(TextureProgramStore):
    def __init__(self, path, implementation, *, protocol=None):
        super().__init__(path, implementation, protocol=protocol or KeyedRekeyProtocol())
