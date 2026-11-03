"""Finite torque uses the existing admitted complete-request execution ledger."""
from .profile_capabilities import TORQUE_PROFILE
from .texture_program_runtime import TextureProgramRuntime


class TorqueProgramRuntime(TextureProgramRuntime):
    profile = TORQUE_PROFILE
