"""Explicit source .20 header; inherited operators keep their grammar."""
from .profile_capabilities import STRING_CONCAT_PROFILE
from .syntax02 import Parser02
from .syntax19 import Parser19


class Parser20(Parser19):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.20", expected_profile=STRING_CONCAT_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0
