"""Revision-bound diagnostics with original UTF-8 source coordinates."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from typing import Any


@dataclass
class Source:
    text: str
    filename: str = "<input>"
    raw: bytes | None = None

    def __post_init__(self) -> None:
        if self.raw is None:
            self.raw = self.text.encode("utf-8", errors="surrogatepass")
        self.revision = "sha256:" + hashlib.sha256(self.raw).hexdigest()


def seconds_text(value: Fraction | float | int | str) -> str:
    """Serialize a canonical binary64 time without losing its exact value."""
    value = Fraction(value)
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        # Public sample times are decimal; elaborated times are binary64.
        raise ValueError("Time must have a finite decimal representation")
    places = max(twos, fives)
    with localcontext() as ctx:
        ctx.prec = max(32, len(str(abs(value.numerator))) + places + 4)
        result = format(Decimal(value.numerator) / Decimal(value.denominator), "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


_RULES = {
    "LEXICAL": "LANG-001", "SYNTAX": "LANG-002", "ID": "LANG-007",
    "NAME": "LANG-007", "TYPE": "LANG-003", "UNIT": "LANG-005",
    "FRAME": "LANG-006", "NUMERIC": "LANG-004", "UNDERFLOW": "LANG-004",
    "AXIS": "LANG-006", "ROTATION": "LANG-006", "OVERRIDE": "LANG-008",
    "ACCESS": "LANG-010", "READONLY": "LANG-008",
    "DEPENDENCY-CYCLE": "LANG-009", "INHERITANCE-CYCLE": "LANG-008",
    "RECURSIVE-COMPOSITION": "LANG-009", "ASSERT": "LANG-010",
    "PHYSICAL-DOMAIN": "LANG-015", "MOTION-MODE": "LANG-018",
    "POSE-AUTHORITY": "LANG-014", "FOLLOW-CYCLE": "LANG-014",
    "SITE-INTERFACE": "LANG-013", "JOINT-LIMIT": "LANG-018",
    "CONTROL-CONFLICT": "LANG-018", "ACTION-STATE": "LANG-019",
    "EVENT-ORDER": "LANG-020", "EVENT-CONFLICT": "LANG-017",
    "RELEASE-STATE": "LANG-017", "HANDOFF": "LANG-017",
    "CAPABILITY-UNSUPPORTED": "LANG-024", "REVISION": "LANG-025",
    "REQUEST-ID": "LANG-026", "RESOURCE": "LANG-009", "SAMPLE": "LANG-027",
}

_REPAIRS = {
    "LEXICAL": "Use the UTF-8 token and string forms in LANG-001.",
    "SYNTAX": "Correct the source at this span using the core grammar.",
    "NAME": "Use a declared name and update every affected reference.",
    "ID": "Give this declaration a unique key in its declared scope.",
    "UNIT": "Supply a quantity with the required physical dimension.",
    "FRAME": "Express the value in the frame required by this operation.",
    "TYPE": "Use the declared type and the callable's positional signature.",
    "CONTROL-CONFLICT": "Stop the current channel owner before starting another action.",
    "JOINT-LIMIT": "Choose a target within the joint's authored limits.",
    "CAPABILITY-UNSUPPORTED": "Use supported core behavior or an implementation that supplies the requested capability.",
}


@dataclass
class Diagnostic:
    code: str
    message: str
    node: Any = None
    category: str = "invalid"
    phase: str = "elaboration"
    rule_ids: list[str] | None = None
    details: dict = field(default_factory=dict)
    repair: str | None = None
    time: Fraction | None = None
    side: str = "after"
    element_id: list[str] | None = None
    related: list[Any] = field(default_factory=list)
    blocks: list[str] | None = None

    def to_dict(self, source: Source, run_id: str | None = None) -> dict:
        suffix = self.code[6:]
        warning = self.code.startswith("OKL-W-")
        start = getattr(self.node, "start", 0)
        end = getattr(self.node, "end", start)
        repair = self.repair or _REPAIRS.get(suffix)
        if repair is None and not warning:
            repair = "Correct the reported condition and validate the complete candidate again."
        blocks = self.blocks
        if blocks is None:
            blocks = [] if warning else ["represented", "constructed", "evaluated", "delivered"]
            if self.category == "unsupported":
                blocks = ["constructed", "evaluated", "delivered"]
            if self.phase in {"admission", "transition", "evaluation"}:
                blocks = ["evaluated", "delivered"]
            if self.phase == "inspection":
                blocks = []
        return {
            "schema_version": "ontokin.diagnostic/0.1",
            "code": self.code,
            "severity": "warning" if warning else "error",
            "category": self.category,
            "phase": self.phase,
            "message": self.message,
            "source_revision": source.revision,
            "run_id": run_id,
            "time": None if self.time is None else {
                "seconds": seconds_text(self.time), "side": self.side,
            },
            "primary": {"file": source.filename, "start_byte": start,
                        "end_byte": end, "element_id": self.element_id},
            "related": [
                {"file": source.filename, "start_byte": n.start,
                 "end_byte": n.end, "element_id": None} for n in self.related
            ],
            "rule_ids": self.rule_ids or [_RULES.get(suffix, "LANG-024")],
            "details": self.details or {},
            "repair": None if repair is None else {"summary": repair, "patches": []},
            "blocks": blocks,
        }


class OntoKinError(Exception):
    def __init__(self, code: str, message: str, node: Any = None, **kwargs: Any):
        super().__init__(message)
        self.diagnostic = Diagnostic(code, message, node, **kwargs)

    @property
    def code(self) -> str:
        return self.diagnostic.code
