"""Explicit source .10 retains execution headers and adds polygon sections."""
from .profile_capabilities import RING_LOFT_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser10(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.10", expected_profile=RING_LOFT_PROFILE)
