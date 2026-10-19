"""Explicit source 0.5 events; force is contextual, not a new lexer keyword."""
from __future__ import annotations
from .syntax import Node
from .syntax02 import Parser02


class Parser05(Parser02):
    def __init__(self, tokens, source_id, check=None):
        super().__init__(tokens, source_id, check,
                         expected_version='0.5', expected_profile='force-0.1')

    def event_block(self) -> Node:
        start = self.take('at')
        time = self.expression()
        self.take('sequence')
        self.take('{')
        events = []
        while self.token.kind != '}':
            token = self.token
            if token.kind in {'start', 'pause', 'resume', 'stop'}:
                kind = self.take(token.kind).value
                name = self.take('IDENT').value
                self.take(';')
                events.append(self.node(kind, token, name=name))
            elif token.kind == 'IDENT' and token.value in {'force', 'impulse'}:
                kind = self.take('IDENT').value
                path = self.path()
                key = self.identity() if kind == 'force' else None
                self.take('using')
                vector = self.expression()
                if kind == 'force':
                    self.take('for')
                    duration = self.expression()
                    self.take(';')
                    events.append(self.node(kind, token, path=path, key=key,
                                            vector=vector, duration=duration))
                else:
                    self.take('at')
                    point = self.expression()
                    self.take(';')
                    events.append(self.node(kind, token, path=path, vector=vector, point=point))
            else:
                self.take('release')
                path = self.path()
                self.take('using')
                self.take('incoming')
                self.take(';')
                events.append(self.node('release', token, path=path))
        self.take('}')
        return self.node('event_block', start, time=time, events=events)
