"""Membership uses the existing admitted complete-request execution ledger."""
from .profile_capabilities import KEYED_MEMBERSHIP_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class KeyedMembershipProgramRuntime(TextureProgramRuntime):
    profile = KEYED_MEMBERSHIP_PROFILE
