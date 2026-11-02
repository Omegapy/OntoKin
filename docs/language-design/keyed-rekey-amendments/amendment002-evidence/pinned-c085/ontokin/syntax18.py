"""Explicit .18 syntax for bounded exact-key pairing of immutable values."""

from .profile_capabilities import KEYED_ZIP_PROFILE
from .syntax02 import Parser02
from .syntax17 import Parser17


class Parser18(Parser17):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.18", expected_profile=KEYED_ZIP_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def primary(self):
        if self.token.kind == "IDENT" and self.token.value == "zip_keyed":
            start = self.take("IDENT")
            self.take("<")
            left_type = self.type_decl()
            self.take(",")
            right_type = self.type_decl()
            self.take(",")
            output_type = self.type_decl()
            self.take(">")
            self.take("(")
            left_token = self.token
            left = self.expression()
            self.take(",")
            right_token = self.token
            right = self.expression()
            self.take(",")
            self.take("(")
            key_node = self.take("IDENT")
            self.take(",")
            left_node = self.take("IDENT")
            self.take(",")
            right_node = self.take("IDENT")
            self.take(")")
            self.take("->")
            body_token = self.token
            body = self.expression()
            self.take(")")
            return self.node("zip_keyed", start, left_type=left_type,
                             right_type=right_type, output_type=output_type,
                             left=left, right=right, body=body,
                             operator_token=start, left_token=left_token,
                             right_token=right_token, body_token=body_token,
                             key_name=key_node.value, left_name=left_node.value,
                             right_name=right_node.value, key_node=key_node,
                             left_node=left_node, right_node=right_node)
        return super().primary()
