"""Explicit .14 syntax for one bounded, key-preserving value expression."""
from .profile_capabilities import KEYED_TRANSFORM_PROFILE
from .syntax02 import Parser02
from .syntax07 import Parser07


class Parser14(Parser07):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.14", expected_profile=KEYED_TRANSFORM_PROFILE)

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
