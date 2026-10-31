"""Explicit source .13 adds immutable textures under shared execution admission."""
from .profile_capabilities import TEXTURE_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser13(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.13", expected_profile=TEXTURE_PROFILE)
