"""Explicit source 0.8 keeps the admitted budget grammar and adds typed values."""
from .profile_capabilities import EXTRUSION_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser08(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version='0.8', expected_profile=EXTRUSION_PROFILE)
