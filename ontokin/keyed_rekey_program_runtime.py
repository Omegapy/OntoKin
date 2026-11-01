"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import KEYED_REKEY_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedRekeyProgramRuntime(TextureProgramRuntime):
    profile = KEYED_REKEY_PROFILE
