"""Explicit .22 event grammar without new globally reserved identifiers."""
from .diagnostics import OntoKinError
from .profile_capabilities import TORQUE_PROFILE
from .syntax02 import Parser02
from .syntax21 import Parser21


class Parser22(Parser21):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.22", expected_profile=TORQUE_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def event_block(self):
        start = self.take("at")
        time = self.expression()
        self.take("sequence")
        self.take("{")
        events = []
        while self.token.kind != "}":
            token = self.token
            if token.kind == "IDENT" and token.value == "torque":
                self.take("IDENT")
                path = self.path()
                key = self.identity()
                about = self.take("IDENT")
                if about.value != "about":
                    raise OntoKinError("OKL-E-SYNTAX", "Expected 'about'; found '" + about.value + "'.",
                                       about, phase="syntax")
                axis = self.take("IDENT").value
                self.take("using")
                operand = self.expression()
                self.take("for")
                duration = self.expression()
                self.take(";")
                events.append(self.node("torque", token, path=path, key=key,
                                        axis=axis, operand=operand, duration=duration))
            elif token.kind in {"start", "pause", "resume", "stop"}:
                kind = self.take(token.kind).value
                name = self.take("IDENT").value
                self.take(";")
                events.append(self.node(kind, token, name=name))
            elif token.kind == "IDENT" and token.value in {"force", "impulse"}:
                kind = self.take("IDENT").value
                path = self.path()
                key = self.identity() if kind == "force" else None
                self.take("using")
                vector = self.expression()
                if kind == "force":
                    self.take("for")
                    duration = self.expression()
                    self.take(";")
                    events.append(self.node(kind, token, path=path, key=key,
                                            vector=vector, duration=duration))
                else:
                    self.take("at")
                    point = self.expression()
                    self.take(";")
                    events.append(self.node(kind, token, path=path, vector=vector, point=point))
            else:
                self.take("release")
                path = self.path()
                self.take("using")
                self.take("incoming")
                self.take(";")
                events.append(self.node("release", token, path=path))
        self.take("}")
        return self.node("event_block", start, time=time, events=events)
