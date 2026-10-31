"""Explicit .16 syntax for a strict, key-preserving pure filter."""
from .profile_capabilities import KEYED_FILTER_PROFILE
from .syntax02 import Parser02
from .syntax15 import Parser15


class Parser16(Parser15):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.16", expected_profile=KEYED_FILTER_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def primary(self):
        if self.token.kind == "IDENT" and self.token.value == "filter_keyed":
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
            predicate = self.expression()
            self.take(")")
            return self.node("filter_keyed", start, element_type=element_type,
                             input=input_value, key_name=key_node.value,
                             value_name=value_node.value, key_node=key_node,
                             value_node=value_node, predicate=predicate)
        return super().primary()
