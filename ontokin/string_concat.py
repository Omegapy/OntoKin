"""Bounded immutable String concatenation for explicitly declared source .20.

Only the caller's admitted request ledger owns work, cancellation and the
monotone logical-result reservation. Scanning never constructs an encoding or
an intermediate copy of either operand.
"""
from __future__ import annotations

from .diagnostics import OntoKinError
from .execution_budget import SharedExecutionBudget


MAX_RESULT_BYTES = 65536
MAX_TOTAL_BYTES = 4194304
PROFILE = "string-concat-0.1"
_REPAIR = "Reduce computed String sizes or the number of concatenation results in this request."


def _limit_error(budget: str, limit: int, consumed: int, node) -> None:
    message = ("String concatenation exceeds 65536 UTF-8 result bytes."
               if budget == "string_concat_result_bytes" else
               "String concatenation exceeds 4194304 cumulative UTF-8 result bytes.")
    raise OntoKinError("OKL-E-RESOURCE", message, node,
                       category="resource_limit", phase="support", repair=_REPAIR,
                       details={"budget": budget, "limit": limit,
                                "consumed": consumed, "profile": PROFILE})


def concat_strings(left: str, right: str, node, ledger: SharedExecutionBudget) -> str:
    """Execute one known String operation on the original admitted ledger.

    Source admission already guarantees Unicode scalar Strings. This private
    helper has no independent authority or fallback execution context.
    """
    if (not isinstance(ledger, SharedExecutionBudget) or ledger.resolved is None
            or ledger.admitted_entry_revision is None):
        raise OntoKinError("OKL-E-RESOURCE", "Construction requires one admitted execution context.",
                           node, phase="support",
                           details={"budget_reason": "execution_context_required"})
    if type(left) is not str or type(right) is not str:
        raise TypeError("String concatenation requires two exact String payloads.")
    previous_stage = ledger.stage
    try:
        ledger.stage = "string_concat_admission"
        ledger.tick(node)
        ledger.stage = "string_concat_scan"
        total = 0
        for operand in (left, right):
            operand_bytes = 0
            for scalar in operand:
                codepoint = ord(scalar)
                if codepoint < 0x80:
                    width = 1
                elif codepoint < 0x800:
                    width = 2
                elif codepoint < 0x10000:
                    if 0xD800 <= codepoint <= 0xDFFF:
                        raise ValueError("Source Strings contain Unicode scalars only.")
                    width = 3
                else:
                    width = 4
                next_bytes = operand_bytes + width
                charge = (next_bytes + 63) // 64 - (operand_bytes + 63) // 64
                if charge:
                    ledger.tick(node, amount=charge)
                operand_bytes = next_bytes
                total += width
                if total > MAX_RESULT_BYTES:
                    _limit_error("string_concat_result_bytes", MAX_RESULT_BYTES, total, node)
        ledger.stage = "string_concat_allocation"
        ledger.tick(node, amount=1 + (total + 63) // 64)
        reserved = ledger.string_concat_bytes + total
        if reserved > MAX_TOTAL_BYTES:
            _limit_error("string_concat_total_bytes", MAX_TOTAL_BYTES, reserved, node)
        ledger.string_concat_bytes = reserved
        result = left + right
        ledger.stage = "string_concat_publication"
        ledger.tick(node)
        return result
    finally:
        ledger.stage = previous_stage
