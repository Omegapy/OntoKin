"""Explicit source .12 adds blind pockets under the shared execution header."""
from .profile_capabilities import POCKETS_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser12(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.12", expected_profile=POCKETS_PROFILE)
