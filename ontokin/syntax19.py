"""Explicit .19 syntax for bounded payload-preserving keyed renaming."""

from .profile_capabilities import KEYED_REKEY_PROFILE
from .syntax02 import Parser02
from .syntax18 import Parser18


class Parser19(Parser18):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.19", expected_profile=KEYED_REKEY_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def primary(self):
        if self.token.kind == "IDENT" and self.token.value == "rekey_keyed":
            start = self.take("IDENT")
            self.take("<")
            element_type = self.type_decl()
            self.take(">")
            self.take("(")
            input_token = self.token
            source = self.expression()
            self.take(",")
            self.take("(")
            key_node = self.take("IDENT")
            self.take(",")
            value_node = self.take("IDENT")
            self.take(")")
            self.take("->")
            body_token = self.token
            body = self.expression()
            self.take(")")
            return self.node("rekey_keyed", start, element_type=element_type,
                             input=source, body=body, operator_token=start,
                             input_token=input_token, body_token=body_token,
                             key_name=key_node.value, value_name=value_node.value,
                             key_node=key_node, value_node=value_node)
        return super().primary()
