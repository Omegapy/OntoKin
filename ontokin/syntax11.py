"""Explicit source .11 retains execution headers and adds framed sections."""
from .profile_capabilities import FRAMED_LOFT_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser11(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.11", expected_profile=FRAMED_LOFT_PROFILE)
