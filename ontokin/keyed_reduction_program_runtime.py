"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import KEYED_REDUCTION_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedReductionProgramRuntime(TextureProgramRuntime):
    profile = KEYED_REDUCTION_PROFILE
