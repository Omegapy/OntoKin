"""Source transformations use the existing one-request execution ledger."""
from .profile_capabilities import KEYED_FILTER_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedFilterProgramRuntime(TextureProgramRuntime):
    profile = KEYED_FILTER_PROFILE
