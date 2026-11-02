"""Explicit source .21 header; keyed membership uses ordinary call grammar."""
from .profile_capabilities import KEYED_MEMBERSHIP_PROFILE
from .syntax02 import Parser02
from .syntax20 import Parser20


class Parser21(Parser20):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.21", expected_profile=KEYED_MEMBERSHIP_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0
