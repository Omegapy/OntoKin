"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import KEYED_MERGE_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedMergeProgramRuntime(TextureProgramRuntime):
    profile = KEYED_MERGE_PROFILE
