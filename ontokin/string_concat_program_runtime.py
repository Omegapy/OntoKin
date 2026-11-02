"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import STRING_CONCAT_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class StringConcatProgramRuntime(TextureProgramRuntime):
    profile = STRING_CONCAT_PROFILE
