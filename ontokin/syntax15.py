"""Explicit .15 syntax for a bounded sequential keyed reduction."""
from .profile_capabilities import KEYED_REDUCTION_PROFILE
from .syntax02 import Parser02
from .syntax14 import Parser14


class Parser15(Parser14):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.15", expected_profile=KEYED_REDUCTION_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def primary(self):
        if self.token.kind == "IDENT" and self.token.value == "reduce_keyed":
            start = self.take("IDENT")
            self.take("<")
            accumulator_type = self.type_decl()
            self.take(">")
            self.take("(")
            input_value = self.expression()
            self.take(",")
            seed = self.expression()
            self.take(",")
            self.take("(")
            accumulator_node = self.take("IDENT")
            self.take(",")
            key_node = self.take("IDENT")
            self.take(",")
            value_node = self.take("IDENT")
            self.take(")")
            self.take("->")
            body = self.expression()
            self.take(")")
            return self.node("reduce_keyed", start, accumulator_type=accumulator_type,
                             input=input_value, seed=seed, body=body,
                             accumulator_name=accumulator_node.value,
                             key_name=key_node.value, value_name=value_node.value,
                             accumulator_node=accumulator_node,
                             key_node=key_node, value_node=value_node)
        return super().primary()
