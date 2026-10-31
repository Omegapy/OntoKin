"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import KEYED_TRANSFORM_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedTransformProgramRuntime(TextureProgramRuntime):
    profile = KEYED_TRANSFORM_PROFILE
