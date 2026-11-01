"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import KEYED_ZIP_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedZipProgramRuntime(TextureProgramRuntime):
    profile = KEYED_ZIP_PROFILE
