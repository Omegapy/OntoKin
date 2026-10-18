"""Explicit language 0.4 event syntax, preserving inherited expression rules.

``impulse`` is contextual only at the start of an event statement. It remains
an ordinary identifier in every lexer and in all other declaration contexts.
"""

from __future__ import annotations

from typing import Callable

from .syntax import Node, Token
from .syntax02 import Parser02


VERSION = "0.4"
PROFILE = "impulse-0.1"


class Parser04(Parser02):
    def __init__(self, tokens: list[Token], source_id: str,
                 check: Callable[[], None] | None = None):
        super().__init__(tokens, source_id, check,
                         expected_version=VERSION, expected_profile=PROFILE)

    def event_block(self) -> Node:
        start = self.take("at")
        time = self.expression()
        self.take("sequence")
        self.take("{")
        events = []
        while self.token.kind != "}":
            token = self.token
            if token.kind in {"start", "pause", "resume", "stop"}:
                kind = self.take(token.kind).value
                name = self.take("IDENT").value
                self.take(";")
                events.append(self.node(kind, token, name=name))
            elif token.kind == "IDENT" and token.value == "impulse":
                self.take("IDENT")
                path = self.path()
                self.take("using")
                vector = self.expression()
                self.take("at")
                point = self.expression()
                self.take(";")
                events.append(self.node("impulse", token, path=path,
                                        vector=vector, point=point))
            else:
                self.take("release")
                path = self.path()
                self.take("using")
                self.take("incoming")
                self.take(";")
                events.append(self.node("release", token, path=path))
        self.take("}")
        return self.node("event_block", start, time=time, events=events)
