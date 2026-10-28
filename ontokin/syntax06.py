"""Explicit 0.6 header with the inherited force/event and expression grammar."""
from __future__ import annotations

from .syntax02 import Parser02
from .syntax05 import Parser05


class Parser06(Parser05):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.6", expected_profile="planar-reach-0.1")
