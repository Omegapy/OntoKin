"""Explicit .17 syntax for a disjoint immutable keyed union."""

from .profile_capabilities import KEYED_MERGE_PROFILE
from .syntax02 import Parser02
from .syntax16 import Parser16


class Parser17(Parser16):
    def __init__(self, tokens, source_id, check=None):
        Parser02.__init__(self, tokens, source_id, check,
                          expected_version="0.17", expected_profile=KEYED_MERGE_PROFILE)
        self._expression_nesting = 0
        self._type_nesting = 0

    def primary(self):
        if self.token.kind == "IDENT" and self.token.value == "merge_keyed":
            start = self.take("IDENT")
            self.take("<")
            element_type = self.type_decl()
            self.take(">")
            self.take("(")
            left_token = self.token
            left = self.expression()
            self.take(",")
            right_token = self.token
            right = self.expression()
            self.take(")")
            # Grouping can extend a semantic node's span. Keep the original
            # operand tokens separately for the new diagnostic contract.
            return self.node("merge_keyed", start, element_type=element_type,
                             left=left, right=right, operator_token=start,
                             left_token=left_token, right_token=right_token)
        return super().primary()
