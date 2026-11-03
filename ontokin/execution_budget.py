"""Host-authorized, request-local execution budgets for explicit source 0.7.

The host constructs policy outside the source interpreter. Header admission
starts a provisional ledger; promotion preserves its work and monotonic start.
The same ledger then pays for compilation, simulation and verified delivery.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
import time
from types import MappingProxyType, MethodType, ModuleType
from typing import Callable, Mapping

from .bundle import SourceUnit
from .diagnostics import OntoKinError
from .profile_capabilities import BUDGET_PROFILE, EXTRUSION_PROFILE, HOLES_PROFILE, RING_LOFT_PROFILE, FRAMED_LOFT_PROFILE, POCKETS_PROFILE, TEXTURE_PROFILE, KEYED_TRANSFORM_PROFILE, KEYED_REDUCTION_PROFILE, KEYED_FILTER_PROFILE, KEYED_MERGE_PROFILE, KEYED_ZIP_PROFILE, KEYED_REKEY_PROFILE, STRING_CONCAT_PROFILE, KEYED_MEMBERSHIP_PROFILE, TORQUE_PROFILE, KEYED_REDUCTION_PROFILES, KEYED_TRANSFORM_PROFILES, TEXTURE_PROFILES, POCKETS_PROFILES
from .syntax import Node, Token


DEFAULT_LIMITS = MappingProxyType({"max_operations": 100000, "max_elapsed_ms": 30000})
# JSON numbers can preserve all integers in this range without a binary64 loss.
MAX_LIMIT = (1 << 53) - 1
MAX_HEADER_BYTES = 65536
MAX_HEADER_TOKEN_CHARS = 256
MAX_LITERAL_CHARS = 32
_INTEGER = re.compile(r"(?:0|[1-9][0-9]*)\Z", re.ASCII)
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z", re.ASCII)
_NATIVE_MONOTONIC = time.monotonic
_NATIVE_MATH = math
_NATIVE_ISFINITE = math.isfinite


def _native_agent_clock_binding(clock):
    """Retain the exact Agent reader and its original host clock, if native."""
    if type(clock) is not MethodType:
        return None
    from .budget_agent import (_BudgetCheck, _NATIVE_BUDGET_READ_CLOCK,
                               _NATIVE_BUDGET_READ_CLOCK_AUTHORITY)
    owner = clock.__self__
    if type(owner) is not _BudgetCheck or clock.__func__ is not _NATIVE_BUDGET_READ_CLOCK:
        return None
    namespace = object.__getattribute__(owner, "__dict__")
    if type(namespace) is not dict:
        return None
    return (clock, owner, _BudgetCheck, namespace, _NATIVE_BUDGET_READ_CLOCK,
            namespace.get("_host_clock"), _NATIVE_BUDGET_READ_CLOCK_AUTHORITY)


def _native_agent_clock_current(binding, clock):
    original, owner, native, namespace, function, host_clock, authority = binding
    if (clock is not original or type(clock) is not MethodType
            or type(owner) is not native or clock.__self__ is not owner
            or clock.__func__ is not function
            or function.__code__ is not authority[0] or function.__defaults__ is not authority[1]
            or function.__kwdefaults__ is not authority[2] or function.__closure__ is not authority[3]
            or function.__globals__ is not authority[4]
            or function.__builtins__ is not authority[5]
            or any(function.__globals__.get(name, authority[5].get(name)) is not original
                   for name, original in authority[6])
            or native.__bases__ is not authority[7] or native.__mro__ is not authority[8]
            or native.__getattribute__ is not object.__getattribute__
            or native.__setattr__ is not object.__setattr__
            or any(name in vars(native) for name in ("_host_clock", "_clock_failed", "_last_clock"))
            or object.__getattribute__(owner, "__dict__") is not namespace
            or namespace.get("_host_clock") is not host_clock
            or namespace.get("_clock_failed") is not False
            or function.__globals__.get("math") is not _NATIVE_MATH
            or type(_NATIVE_MATH) is not ModuleType
            or vars(_NATIVE_MATH).get("isfinite") is not _NATIVE_ISFINITE):
        return False
    last = namespace.get("_last_clock")
    if last is None:
        return True
    if type(last) not in (int, float):
        return False
    try:
        return _NATIVE_ISFINITE(last)
    except OverflowError:
        return False


def _native_elapsed_reader_current(reader, owner):
    function, authority = _NATIVE_SHARED_ELAPSED_MS, _NATIVE_SHARED_ELAPSED_AUTHORITY
    return (type(owner) is SharedExecutionBudget and type(reader) is MethodType
        and reader.__self__ is owner and reader.__func__ is function
        and function.__code__ is authority[0] and function.__defaults__ is authority[1]
        and function.__kwdefaults__ is authority[2] and function.__closure__ is authority[3]
        and function.__globals__ is authority[4]
        and SharedExecutionBudget.__bases__ is authority[5] and SharedExecutionBudget.__mro__ is authority[6]
        and SharedExecutionBudget.__getattribute__ is object.__getattribute__
        and SharedExecutionBudget.__setattr__ is object.__setattr__
        and "_clock" not in vars(SharedExecutionBudget) and "started" not in vars(SharedExecutionBudget))


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
        # Logical computed-String bytes; monotone within this actual request.
        self.string_concat_bytes = 0
        self.check = check
        self.callback_error: BaseException | None = None
        self.resolved: ResolvedBudget | None = None
        self.source_request = None
        self.admitted_entry_revision = None
        self.stage = "header_admission"
        self.budget_reason = None
        # Only the explicit .22 admission enables this callback receipt.
        # Earlier contracts retain their exact callback and charge behavior.
        self._torque_guarded = False
        self._torque_counter = None
        self._torque_context_guard = None
        self._torque_clock_binding = None

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
        guarded = self._torque_guarded
        expected = self._torque_counter
        clock_binding = self._torque_clock_binding
        elapsed_reader = self.elapsed_ms if guarded else None
        clock_before_poll = None if clock_binding is None else clock_binding[3].get("_last_clock")
        if guarded and (type(self.operations) is not int or self.operations != expected):
            self.operations = expected
            self._fail("execution_context_required", "Torque execution cannot change its consumed work.", node)
        if guarded and not _native_elapsed_reader_current(elapsed_reader, self):
            self._fail("execution_context_required", "Torque execution requires its original elapsed-time reader.", node)
        # Capture before the original callback. This is an admission check,
        # not a replacement callback, new work operation, or alternate clock.
        receipt = None
        if guarded and (self.check is not None or self._clock is not _NATIVE_MONOTONIC):
            receipt = (self.check, self._clock, self.started, self.resolved,
                       self._limits, tuple(self._limits.items()), self._torque_context_guard, clock_binding)
        def admit_counter(value):
            if type(self) is not SharedExecutionBudget:
                budget_error("execution_context_required", "Torque execution requires its original native ledger.", node)
            if (not self._torque_guarded or type(self.operations) is not int
                    or self.operations != value or self._torque_counter != value):
                self.operations = self._torque_counter = value
                self._torque_guarded = True
                self._fail("execution_context_required", "Torque execution cannot change its consumed work.", node)
        def admit_callback(value, *, source=True):
            admit_counter(value)
            current_elapsed = self.elapsed_ms
            if (self.check is not receipt[0] or self._clock is not receipt[1]
                    or self.started is not receipt[2] or self.resolved is not receipt[3]
                    or self._limits is not receipt[4] or len(self._limits) != len(receipt[5])
                    or any(key is not old_key or value is not old_value
                           for (key, value), (old_key, old_value) in zip(self._limits.items(), receipt[5]))
                    or self._torque_context_guard is not receipt[6]
                    or self._torque_clock_binding is not receipt[7]
                    or not _native_elapsed_reader_current(current_elapsed, self)
                    or clock_binding is not None and not _native_agent_clock_current(clock_binding, self._clock)):
                self._fail("execution_context_required", "Torque execution cannot replace its original callback context.", node)
            if source and receipt[6] is not None:
                receipt[6]()
        # The receipt was just captured without a callback; comparing it to
        # itself here would repeat every native check without observing work.
        # Admit the original counter above and re-admit this receipt after
        # each actual callback, before the next operation uses its context.
        if self.check is not None:
            try:
                self.check()
            except BaseException as error:
                if guarded:
                    # An original callback exception keeps precedence and
                    # identity, while already consumed work cannot disappear.
                    self.operations = self._torque_counter = expected
                self.callback_error = error
                raise
        if receipt is not None:
            admit_callback(expected)
        # A poll-side read of the original clock is permitted. If its native
        # last-reading field changed, retain the complete second source scan.
        unchanged_clock_state = (clock_binding is not None
                                 and clock_binding[3].get("_last_clock") is clock_before_poll)
        self.operations += amount
        if guarded:
            self._torque_counter = self.operations
            expected += amount
        if self.operations > self._limits["max_operations"]:
            self._fail("operation_budget_exhausted", "Execution exceeded max_operations.", node,
                       budget="max_operations", limit=self._limits["max_operations"],
                       consumed=self.operations)
        elapsed = self.elapsed_ms()
        if receipt is not None:
            # The exact native Agent reader over the captured builtin clock
            # cannot call user code. Its owner/function/host clock and native
            # state are admitted both before and after this actual invocation.
            # The original poll callback still receives its complete source
            # admission above. Every custom clock keeps the second full scan.
            native_clock = (receipt[1] is _NATIVE_MONOTONIC or clock_binding is not None
                            and clock_binding[5] is _NATIVE_MONOTONIC and unchanged_clock_state)
            admit_callback(expected, source=not native_clock)
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


_NATIVE_SHARED_ELAPSED_MS = SharedExecutionBudget.elapsed_ms
_NATIVE_SHARED_ELAPSED_AUTHORITY = (_NATIVE_SHARED_ELAPSED_MS.__code__,
    _NATIVE_SHARED_ELAPSED_MS.__defaults__, _NATIVE_SHARED_ELAPSED_MS.__kwdefaults__,
    _NATIVE_SHARED_ELAPSED_MS.__closure__, _NATIVE_SHARED_ELAPSED_MS.__globals__,
    SharedExecutionBudget.__bases__, SharedExecutionBudget.__mro__)


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
    versions = {BUDGET_PROFILE: "0.7", EXTRUSION_PROFILE: "0.8", HOLES_PROFILE: "0.9", RING_LOFT_PROFILE: "0.10", FRAMED_LOFT_PROFILE: "0.11", POCKETS_PROFILE: "0.12", TEXTURE_PROFILE: "0.13", KEYED_TRANSFORM_PROFILE: "0.14", KEYED_REDUCTION_PROFILE: "0.15", KEYED_FILTER_PROFILE: "0.16", KEYED_MERGE_PROFILE: "0.17", KEYED_ZIP_PROFILE: "0.18", KEYED_REKEY_PROFILE: "0.19", STRING_CONCAT_PROFILE: "0.20", KEYED_MEMBERSHIP_PROFILE: "0.21", TORQUE_PROFILE: "0.22"}
    if profile not in versions:
        budget_error("invalid_declaration", "Unsupported execution-budget source profile.")
    if profile == TORQUE_PROFILE:
        ledger._torque_guarded = True
        ledger._torque_counter = ledger.operations
        ledger._torque_clock_binding = _native_agent_clock_binding(ledger._clock)
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

