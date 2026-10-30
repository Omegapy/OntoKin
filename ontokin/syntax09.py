"""Explicit source .9 keeps execution headers and adds typed polygon rings."""
from .profile_capabilities import HOLES_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser09(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version='0.9', expected_profile=HOLES_PROFILE)
