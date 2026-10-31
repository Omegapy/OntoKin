"""Explicit .14 syntax for one bounded, key-preserving value expression."""
from .diagnostics import OntoKinError
from .profile_capabilities import KEYED_TRANSFORM_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


_PRECEDENCE = {operator: level for level, operators in enumerate(Parser07._LEVELS)
               for operator in operators}


class Parser14(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.14", expected_profile=KEYED_TRANSFORM_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def _nesting_error(self, budget, limit, consumed):
        raise OntoKinError("OKL-E-RESOURCE", "Parser nesting exceeds bounded source work.",
                           self.token, category="resource_limit", phase="syntax",
                           rule_ids=["CON-012"],
                           details={"budget": budget, "limit": limit, "consumed": consumed})

    def expression(self):
        self._expression_nesting += 1
        try:
            if self._expression_nesting > 128:
                self._nesting_error("parser_expression_depth", 128, self._expression_nesting)
            if self.token.kind == "if":
                start = self.take("if")
                condition = self.expression()
                self.take("then")
                then = self.expression()
                self.take("else")
                otherwise = self.expression()
                return self.node("conditional", start, condition=condition, then=then, otherwise=otherwise)
            return self.binary(0)
        finally:
            self._expression_nesting -= 1

    def binary(self, level):
        # An explicit six-level operator stack preserves inherited precedence
        # without six Python calls for every nested argument or map body.
        # This reserves enough host stack for the real cancellation callback.
        values, operators = [self.unary()], []
        while self.token.kind in _PRECEDENCE and _PRECEDENCE[self.token.kind] >= level:
            incoming = _PRECEDENCE[self.token.kind]
            while operators and _PRECEDENCE[operators[-1].kind] >= incoming:
                if incoming in {2, 3} and _PRECEDENCE[operators[-1].kind] == incoming:
                    break
                operator = operators.pop()
                right, left = values.pop(), values.pop()
                values.append(self.node("binary", left, op=operator.value, left=left, right=right))
            if operators and incoming in {2, 3} and _PRECEDENCE[operators[-1].kind] == incoming:
                break
            operators.append(self.take(self.token.kind))
            values.append(self.unary())
        while operators:
            operator = operators.pop()
            right, left = values.pop(), values.pop()
            values.append(self.node("binary", left, op=operator.value, left=left, right=right))
        return values[0]

    def unary(self):
        operators = []
        while self.token.kind in {"-", "not"}:
            operators.append(self.take(self.token.kind))
            if len(operators) > 128:
                self._nesting_error("parser_unary_depth", 128, len(operators))
        value = self.postfix()
        for start in reversed(operators):
            value = self.node("unary", start, op=start.value, value=value)
        return value

    def type_decl(self):
        self._type_nesting += 1
        try:
            if self._type_nesting > 64:
                self._nesting_error("type_depth", 64, self._type_nesting)
            return super().type_decl()
        finally:
            self._type_nesting -= 1

    def primary(self):
        # Earlier parsers keep this identifier available to ordinary functions
        # A qualified older function is parsed through its namespace as before
        if self.token.kind == "IDENT" and self.token.value == "map_keyed":
            start = self.take("IDENT")
            self.take("<")
            element_type = self.type_decl()
            self.take(">")
            self.take("(")
            input_value = self.expression()
            self.take(",")
            self.take("(")
            key_node = self.take("IDENT")
            self.take(",")
            value_node = self.take("IDENT")
            self.take(")")
            self.take("->")
            body = self.expression()
            self.take(")")
            return self.node("map_keyed", start, element_type=element_type,
                             input=input_value, key_name=key_node.value,
                             value_name=value_node.value, key_node=key_node,
                             value_node=value_node, body=body)
        return super().primary()
