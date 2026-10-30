"""Host-authorized, request-local execution budgets for explicit source 0.7.

The host constructs policy outside the source interpreter. Header admission
starts a provisional ledger; promotion preserves its work and monotonic start.
The same ledger then pays for compilation, simulation and verified delivery.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import time
from types import MappingProxyType
from typing import Callable, Mapping

from .bundle import SourceUnit
from .diagnostics import OntoKinError
from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE
from .syntax import Node, Token


DEFAULT_LIMITS = MappingProxyType({"max_operations": 100000, "max_elapsed_ms": 30000})
# JSON numbers can preserve all integers in this range without a binary64 loss.
MAX_LIMIT = (1 << 53) - 1
MAX_HEADER_BYTES = 65536
MAX_HEADER_TOKEN_CHARS = 256
MAX_LITERAL_CHARS = 32
_INTEGER = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z", re.ASCII)


def budget_error(reason: str, message: str, node=None, **details):
    """Use the existing resource family without changing legacy diagnostics."""
    raise OntoKinError("OKL-E-RESOURCE", message, node, category="resource_limit",
                       phase="support", details={"budget_reason": reason, **details})


def _positive_limit(value, field: str) -> int:
    if type(value) is not int or not 1 <= value <= MAX_LIMIT:
        raise ValueError(f"{field} must be a positive integer no greater than {MAX_LIMIT}.")
    return value


@dataclass(frozen=True)
class HostPolicy:
    """Finite ceilings supplied by the trusted embedding host or launcher."""

    max_operations: int = 100000
    max_elapsed_ms: int = 30000
    policy_id: str | None = None

    def __post_init__(self):
        _positive_limit(self.max_operations, "max_operations")
        _positive_limit(self.max_elapsed_ms, "max_elapsed_ms")
        if self.policy_id is None:
            canonical = json.dumps(self.ceilings, sort_keys=True, separators=(",", ":"))
            object.__setattr__(self, "policy_id", "sha256:" + hashlib.sha256(canonical.encode()).hexdigest())
        elif (type(self.policy_id) is not str or not self.policy_id
              or len(self.policy_id) > 128
              or any(ord(c) < 32 or ord(c) == 127 for c in self.policy_id)):
            raise ValueError("policy_id must be a nonempty string of at most 128 printable characters.")

    @property
    def ceilings(self) -> dict:
        return {"max_operations": self.max_operations, "max_elapsed_ms": self.max_elapsed_ms}


@dataclass(frozen=True)
class ResolvedBudget:
    source_request: Mapping[str, int]
    caller_caps: Mapping[str, int]
    host_ceilings: Mapping[str, int]
    effective: Mapping[str, int]
    policy_id: str

    def __post_init__(self):
        for name in ("source_request", "caller_caps", "host_ceilings", "effective"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


class SharedExecutionBudget:
    """One counter and one original clock, with exactly one authorization.

    Header work is one charge per started 64 UTF-8 bytes and one per emitted
    prefix token. Later stages retain their existing semantic work units.
    A zero-amount checkpoint polls cancellation and time without another debit.
    """

    def __init__(self, policy: HostPolicy | None = None, caller_caps=None,
                 check: Callable[[], None] | None = None, clock=None):
        if policy is not None and not isinstance(policy, HostPolicy):
            raise TypeError("policy must be a HostPolicy supplied by the host.")
        self.policy = HostPolicy() if policy is None else policy
        if caller_caps is not None and (type(caller_caps) is not dict
                                       or set(caller_caps) - set(DEFAULT_LIMITS)):
            budget_error("invalid_declaration", "Unknown per-call execution cap.")
        caps = dict(caller_caps or {})
        for name, value in caps.items():
            try:
                _positive_limit(value, name)
            except ValueError as exc:
                budget_error("invalid_declaration", str(exc), budget=name)
        self.caller_caps = MappingProxyType(caps)
        self._limits = {name: min(default, self.policy.ceilings[name], caps.get(name, default))
                        for name, default in DEFAULT_LIMITS.items()}
        self._clock = time.monotonic if clock is None else clock
        self.started = self._clock()
        self.operations = 0
        self.check = check
        self.callback_error: BaseException | None = None
        self.resolved: ResolvedBudget | None = None
        self.source_request = None
        self.admitted_entry_revision = None
        self.stage = "header_admission"
        self.budget_reason = None

    @property
    def limits(self) -> dict:
        return dict(self._limits)

    def elapsed_ms(self) -> float:
        return (self._clock() - self.started) * 1000

    def _fail(self, reason, message, node=None, **details):
        self.budget_reason = reason
        budget_error(reason, message, node, stage=self.stage, **details)

    def tick(self, node=None, amount: int = 1) -> None:
        if type(amount) is not int or amount < 0:
            raise ValueError("A work charge must be a nonnegative integer.")
        if self.check is not None:
            try:
                self.check()
            except BaseException as error:
                self.callback_error = error
                raise
        self.operations += amount
        if self.operations > self._limits["max_operations"]:
            self._fail("operation_budget_exhausted", "Execution exceeded max_operations.", node,
                       budget="max_operations", limit=self._limits["max_operations"],
                       consumed=self.operations)
        elapsed = self.elapsed_ms()
        if elapsed > self._limits["max_elapsed_ms"]:
            self._fail("execution_deadline_exceeded", "Execution exceeded max_elapsed_ms.", node,
                       budget="max_elapsed_ms", limit=self._limits["max_elapsed_ms"], consumed=elapsed)

    def checkpoint(self) -> None:
        self.tick(amount=0)

    def promote(self, request: Mapping[str, int], *, entry_revision: str) -> ResolvedBudget:
        if self.resolved is not None:
            raise ValueError("An execution budget cannot be promoted twice.")
        self.checkpoint()
        if set(request) - set(DEFAULT_LIMITS):
            self._fail("invalid_declaration", "Unknown source execution budget field.")
        source = {**DEFAULT_LIMITS, **request}
        for name, value in source.items():
            try:
                _positive_limit(value, name)
            except ValueError as exc:
                self._fail("invalid_declaration", str(exc), budget=name)
        self.source_request = MappingProxyType(source)
        effective = dict(source)
        for name, value in self.caller_caps.items():
            if value > source[name]:
                self._fail("request_cap_exceeds_source", "A caller cap cannot enlarge the source request.",
                           budget=name, source_request=source[name], caller_cap=value)
            effective[name] = value
        for name, value in effective.items():
            if value > self.policy.ceilings[name]:
                self._fail("host_ceiling_exceeded", "The execution request exceeds the host ceiling.",
                           budget=name, requested=value, ceiling=self.policy.ceilings[name])
        self.resolved = ResolvedBudget(source, self.caller_caps, self.policy.ceilings,
                                       effective, self.policy.policy_id)
        self._limits = effective
        self.admitted_entry_revision = entry_revision
        # This is still the original clock and includes all provisional work.
        self.checkpoint()
        self.stage = "execution"
        return self.resolved

    def report(self, *, status=None, budget_reason=None) -> dict:
        return {"schema_version": "ontokin.execution-budget/0.1",
                "defaults": dict(DEFAULT_LIMITS), "policy_id": self.policy.policy_id,
                "host_ceilings": self.policy.ceilings,
                "source_request": None if self.source_request is None else dict(self.source_request),
                "caller_caps": dict(self.caller_caps),
                "effective": None if self.resolved is None else dict(self.resolved.effective),
                "consumed_operations": self.operations, "elapsed_ms": self.elapsed_ms(),
                "stage": self.stage, "status": status,
                "budget_reason": self.budget_reason if budget_reason is None else budget_reason}


def operation_literal(text: str, node=None) -> int:
    if len(text) > MAX_LITERAL_CHARS or _INTEGER.fullmatch(text) is None:
        budget_error("invalid_declaration", "max_operations requires a bounded decimal integer literal.", node)
    value = int(text)
    if not 1 <= value <= MAX_LIMIT:
        budget_error("invalid_declaration", "max_operations is outside the positive representable range.", node,
                     limit=MAX_LIMIT)
    return value


def elapsed_literal(text: str, node=None) -> int:
    if len(text) > MAX_LITERAL_CHARS or _DECIMAL.fullmatch(text) is None:
        budget_error("invalid_declaration", "max_elapsed requires a bounded decimal literal in seconds.", node)
    whole, _, fraction = text.partition(".")
    if len(fraction) > 3 and any(c != "0" for c in fraction[3:]):
        budget_error("invalid_declaration", "max_elapsed must be an exact whole number of milliseconds.", node)
    value = int(whole) * 1000 + int((fraction[:3] + "000")[:3])
    if not 1 <= value <= MAX_LIMIT:
        budget_error("invalid_declaration", "max_elapsed is outside the positive millisecond range.", node,
                     limit=MAX_LIMIT)
    return value


class _HeaderScanner:
    """A bounded lazy lexer that never scans a source body to find authority."""

    def __init__(self, unit: SourceUnit, ledger: SharedExecutionBudget):
        self.unit, self.text, self.ledger = unit, unit.text, ledger
        self.index = self.offset = 0
        self._token = None

    def _error(self, message, start=None):
        budget_error("invalid_declaration", message,
                     Node("span", self.offset if start is None else start, self.offset,
                          source_id=self.unit.source_id))

    def _advance(self):
        char = self.text[self.index]
        count = len(char.encode("utf-8"))
        if self.offset + count > MAX_HEADER_BYTES:
            self._error("The entry header exceeds the 65536-byte admission limit.")
        old_blocks = (self.offset + 63) // 64
        self.offset += count
        new_blocks = (self.offset + 63) // 64
        if new_blocks > old_blocks:
            self.ledger.tick(amount=new_blocks - old_blocks)
        self.index += 1
        return char

    def _skip(self):
        while self.index < len(self.text):
            if self.text[self.index] in " \t\r\n":
                self._advance()
            elif self.text.startswith("//", self.index):
                while self.index < len(self.text) and self.text[self.index] not in "\r\n":
                    self._advance()
            elif self.text.startswith("/*", self.index):
                self._advance()
                self._advance()
                while self.index < len(self.text) and not self.text.startswith("*/", self.index):
                    self._advance()
                if self.index == len(self.text):
                    self._error("Unterminated header comment.")
                self._advance()
                self._advance()
            else:
                return

    def peek(self) -> Token:
        if self._token is not None:
            return self._token
        self._skip()
        start = self.offset
        if self.index == len(self.text):
            kind, value = "EOF", ""
        elif self.text[self.index] == '"':
            self._advance()
            chars = []
            escapes = {'"': '"', "\\": "\\", "n": "\n", "r": "\r", "t": "\t"}
            while self.index < len(self.text) and self.text[self.index] != '"':
                if len(chars) >= MAX_HEADER_TOKEN_CHARS:
                    self._error("The header string exceeds its admission token limit.", start)
                char = self._advance()
                if char == "\\":
                    if self.index == len(self.text) or self.text[self.index] not in escapes:
                        self._error("Unsupported header string escape.", start)
                    char = escapes[self._advance()]
                elif ord(char) < 32 or 0x7F <= ord(char) <= 0x9F:
                    self._error("Raw control characters are forbidden in header strings.", start)
                chars.append(char)
            if self.index == len(self.text):
                self._error("Unterminated header string.", start)
            self._advance()
            kind, value = "STRING", "".join(chars)
        elif self.text[self.index] in "0123456789":
            chars = []
            while self.index < len(self.text) and (self.text[self.index].isalnum()
                                                  or self.text[self.index] in "._+-"):
                if len(chars) >= MAX_LITERAL_CHARS:
                    self._error("The execution literal exceeds its admission token limit.", start)
                chars.append(self._advance())
            kind, value = "NUMBER", "".join(chars)
        elif self.text[self.index].isascii() and (self.text[self.index].isalpha()
                                                 or self.text[self.index] == "_"):
            chars = []
            while self.index < len(self.text) and self.text[self.index].isascii() and (
                    self.text[self.index].isalnum() or self.text[self.index] == "_"):
                if len(chars) >= MAX_HEADER_TOKEN_CHARS:
                    self._error("The header identifier exceeds its admission token limit.", start)
                chars.append(self._advance())
            kind, value = "IDENT", "".join(chars)
        else:
            kind = value = self._advance()
        self.ledger.tick()
        self._token = Token(kind, value, start, self.offset, self.unit.source_id)
        return self._token

    def take(self, kind=None, value=None) -> Token:
        token = self.peek()
        if (kind is not None and token.kind != kind) or (value is not None and token.value != value):
            self._error("Invalid entry execution header.", token.start)
        self._token = None
        return token


def _admit_entry_budget(unit: SourceUnit, ledger: SharedExecutionBudget, *, profile=BUDGET_PROFILE) -> ResolvedBudget:
    """Resolve only the immutable entry header, before linking or body lexing."""
    if not isinstance(unit, SourceUnit) or unit.source_id != "entry":
        raise TypeError("Budget admission requires the immutable entry SourceUnit.")
    if not isinstance(ledger, SharedExecutionBudget):
        raise TypeError("Budget admission requires a SharedExecutionBudget.")
    if ledger.resolved is not None:
        raise ValueError("This execution has already admitted an entry source.")
    versions = {BUDGET_PROFILE: "0.7", EXTRUSION_PROFILE: "0.8", HOLES_PROFILE: "0.9"}
    if profile not in versions:
        budget_error("invalid_declaration", "Unsupported execution-budget source profile.")
    scanner = _HeaderScanner(unit, ledger)
    scanner.take("IDENT", "ontokin")
    scanner.take("STRING", versions[profile])
    scanner.take(";")
    scanner.take("IDENT", "module")
    module_name = scanner.take("IDENT")
    from .syntax02 import RESERVED_02
    if module_name.value in RESERVED_02:
        budget_error("invalid_declaration", "The module name must be an identifier.", module_name)
    scanner.take("@")
    scanner.take("STRING")
    scanner.take(";")
    scanner.take("IDENT", "profile")
    scanner.take("STRING", profile)
    scanner.take(";")
    while scanner.peek().value == "requires" and scanner.peek().kind == "IDENT":
        scanner.take("IDENT", "requires")
        scanner.take("STRING")
        scanner.take(";")
    request = {}
    if scanner.peek().kind == "IDENT" and scanner.peek().value == "execution":
        declaration = scanner.take("IDENT", "execution")
        scanner.take("{")
        while scanner.peek().kind != "}":
            field = scanner.take("IDENT")
            if field.value not in {"max_operations", "max_elapsed"}:
                budget_error("invalid_declaration", "Unknown execution budget field.", field)
            name = "max_elapsed_ms" if field.value == "max_elapsed" else field.value
            if name in request:
                budget_error("invalid_declaration", "Duplicate execution budget field.", field)
            scanner.take("=")
            number = scanner.take("NUMBER")
            if name == "max_elapsed_ms":
                scanner.take("[")
                scanner.take("IDENT", "s")
                scanner.take("]")
                request[name] = elapsed_literal(number.value, number)
            else:
                request[name] = operation_literal(number.value, number)
            scanner.take(";")
        scanner.take("}")
        if not request:
            budget_error("invalid_declaration", "An execution declaration cannot be empty.", declaration)
        if scanner.peek().kind == "IDENT" and scanner.peek().value == "execution":
            budget_error("invalid_declaration", "Only one execution declaration is allowed.", scanner.peek())
        if scanner.peek().kind == "IDENT" and scanner.peek().value == "requires":
            budget_error("invalid_declaration", "An execution declaration must follow all requirements.", declaration)
    return ledger.promote(request, entry_revision=unit.revision)


def admit_entry_budget(unit: SourceUnit, ledger: SharedExecutionBudget, *, profile=BUDGET_PROFILE) -> ResolvedBudget:
    """Admit a header and preserve its bounded failure reason for reporting."""
    try:
        return _admit_entry_budget(unit, ledger, profile=profile)
    except OntoKinError as exc:
        if isinstance(ledger, SharedExecutionBudget) and exc is not ledger.callback_error:
            ledger.budget_reason = exc.diagnostic.details.get("budget_reason")
        raise

