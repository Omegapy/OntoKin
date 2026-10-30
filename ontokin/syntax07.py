"""Source 0.7 keeps the force grammar and adds one literal entry declaration."""
from __future__ import annotations

from .diagnostics import OntoKinError
from .execution_budget import budget_error, elapsed_literal, operation_literal
from .profile_capabilities import BUDGET_PROFILE
from .syntax02 import Parser02
from .syntax05 import Parser05


class Parser07(Parser05):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.7", expected_profile=BUDGET_PROFILE)

    def take(self, kind):
        if kind == "EOF" and self.token.kind == "IDENT" and self.token.value == "execution":
            budget_error("invalid_declaration", "An execution declaration must occur once in the entry header.",
                         self.token)
        return super().take(kind)

    def execution_declaration(self):
        if self.token.kind != "IDENT" or self.token.value != "execution":
            return None
        start = self.token
        if self.source_id != "entry":
            budget_error("invalid_declaration", "Only the entry source may declare an execution budget.", start)
        self.take("IDENT")
        request = {}
        try:
            self.take("{")
            while self.token.kind != "}":
                field = self.take("IDENT")
                if field.value not in {"max_operations", "max_elapsed"}:
                    budget_error("invalid_declaration", "Unknown execution budget field.", field)
                name = "max_elapsed_ms" if field.value == "max_elapsed" else field.value
                if name in request:
                    budget_error("invalid_declaration", "Duplicate execution budget field.", field)
                self.take("=")
                number = self.take("NUMBER")
                if name == "max_elapsed_ms":
                    self.take("[")
                    unit = self.take("IDENT")
                    if unit.value != "s":
                        budget_error("invalid_declaration", "max_elapsed requires seconds written [s].", unit)
                    self.take("]")
                    request[name] = elapsed_literal(number.value, number)
                else:
                    request[name] = operation_literal(number.value, number)
                self.take(";")
            self.take("}")
        except OntoKinError as exc:
            if exc.diagnostic.code == "OKL-E-SYNTAX":
                budget_error("invalid_declaration", "Invalid literal execution declaration.", exc.diagnostic.node)
            raise
        if not request:
            budget_error("invalid_declaration", "An execution declaration cannot be empty.", start)
        if self.token.kind == "requires":
            budget_error("invalid_declaration", "An execution declaration must follow all requirements.", start)
        return self.node("execution", start, request=request)
