"""Independent source/context admission for the complete .22 byte reader.

The validator uses a detached native source graph captured before its first
callback. Complete source values and owners are admitted again after its final
callback. No producer state, source sampler, certificate or planning receipt
supplies authority. The existing numeric-work observer is scoped and chained;
the original callback, shared allowance and clock remain unchanged.
"""
from __future__ import annotations
from dataclasses import is_dataclass
from fractions import Fraction as F
import math
from types import MappingProxyType, MethodType

from . import bundle, diagnostics, model, surface, syntax, syntax02, texture_bundle, texture_runtime, values
from . import extrusion, holes, ring_loft, framed_loft, pockets, texture_png
from .execution_budget import SharedExecutionBudget, HostPolicy, ResolvedBudget
from .reach_numeric import ReachExecutionWork, MAX_OPERAND_BITS
from .reach_reference import ReferenceError


_NATIVE = frozenset(value for module in (bundle, diagnostics, model, surface, syntax, syntax02,
                                        texture_bundle, texture_runtime, values,
                                        extrusion, holes, ring_loft, framed_loft, pockets, texture_png)
    for value in vars(module).values() if isinstance(value, type)
    and value.__module__ == module.__name__ and is_dataclass(value))
_MAX_RECORDS = 100000
_MAX_BYTES = 8 * 1024 * 1024
_MISSING = object()
_WORK_METHODS = tuple((name, getattr(ReachExecutionWork, name)) for name in
    ("charge", "tick", "guard", "guard_bits", "resource", "admission", "lookup", "remember",
     "remember_batch", "_sync_cache_operand_limit", "record"))
_LEDGER_METHODS = tuple((name, getattr(SharedExecutionBudget, name)) for name in
    ("tick", "checkpoint", "elapsed_ms", "_fail", "report"))


def _native_methods(owner, methods):
    for name, function in methods:
        method = getattr(owner, name)
        if type(method) is not MethodType or method.__self__ is not owner or method.__func__ is not function:
            _fail("Independent torque validation requires its original native work methods")


def _budget_mapping(value, *, mutable=False, optional=False):
    if value is None and optional: return None
    if type(value) is not (dict if mutable else MappingProxyType):
        _fail("Independent torque allowance mapping changed its native type")
    pairs = tuple(value.items())
    if (len(pairs) > 2 or any(type(key) is not str or key not in ("max_operations", "max_elapsed_ms")
            or type(item) is not int or not 1 <= item <= (1 << 53) - 1 for key, item in pairs)):
        _fail("Independent torque allowance is not a native bounded value")
    return pairs


def _fail(message):
    raise ReferenceError("identity", message)


class _Graph:
    """A bounded callback-free typed read, with an optional detached copy."""
    def __init__(self, root, *, clone=False):
        self.owners, self.seen, self.active = [], {}, set()
        self.records = self.byte_count = 0
        self.copying = clone
        self.token, self.copy = self.visit(root, 0)

    def visit(self, value, depth):
        self.records += 1
        if self.records > _MAX_RECORDS or depth > 128:
            raise ReferenceError("resource", "Independent torque source receipt exceeds its bounded graph domain")
        kind = type(value)
        if value is None or kind is bool:
            return (kind.__name__, value), value
        if value is values.UNKNOWN:
            return ("unknown_source_value",), value
        if kind is int:
            if value.bit_length() > MAX_OPERAND_BITS:
                raise ReferenceError("resource", "Independent source integer exceeds its operand domain")
            return ("int", value), value
        if kind is float:
            if not math.isfinite(value): _fail("Independent source contains a nonfinite scalar")
            return ("float", value.hex()), value
        if kind is F:
            n, d = value.numerator, value.denominator
            if type(n) is not int or type(d) is not int or d <= 0 or max(n.bit_length(), d.bit_length()) > MAX_OPERAND_BITS:
                _fail("Independent source rational is not a bounded native value")
            return ("fraction", n, d), F(n, d) if self.copying else None
        if kind in (str, bytes):
            size = len(value.encode("utf-8")) if kind is str else len(value)
            self.byte_count += size
            if size > 2_000_000 or self.byte_count > _MAX_BYTES:
                raise ReferenceError("resource", "Independent source receipt exceeds its bounded byte domain")
            return (kind.__name__, value), value
        if kind not in (tuple, list, dict, set, frozenset, MappingProxyType) and kind not in _NATIVE:
            _fail("Independent source contains a foreign or unsupported record type: " + kind.__name__)
        identity = id(value)
        if identity in self.active:
            _fail("Independent source graph contains a cycle")
        if identity in self.seen:
            index, copied = self.seen[identity]
            return ("reference", index), copied
        index = len(self.owners)
        self.owners.append(value)
        self.active.add(identity)
        if kind in (dict, MappingProxyType):
            if len(value) > _MAX_RECORDS: _fail("Independent source table is too large")
            rows = []; copied = {}
            self.seen[identity] = (index, copied)
            for key, child in value.items():
                key_token, key_copy = self.visit(key, depth + 1)
                child_token, child_copy = self.visit(child, depth + 1)
                rows.append((key_token, child_token))
                if self.copying: copied[key_copy] = child_copy
            if kind is MappingProxyType: copied = MappingProxyType(copied)
            token = ("mapping", kind.__name__, index, tuple(rows))
        elif kind in (tuple, list, set, frozenset):
            if len(value) > _MAX_RECORDS: _fail("Independent source sequence is too large")
            pairs = [self.visit(child, depth + 1) for child in value]
            if kind in (set, frozenset): pairs.sort(key=lambda pair: repr(pair[0]))
            token = ("sequence", kind.__name__, index, tuple(pair[0] for pair in pairs))
            copied = kind(pair[1] for pair in pairs) if self.copying else None
        else:
            attributes = object.__getattribute__(value, "__dict__")
            if type(attributes) is not dict or len(attributes) > 256:
                _fail("Independent source record storage is not native and bounded")
            rows = []; copied = object.__new__(kind) if self.copying else None
            self.seen[identity] = (index, copied)
            for name, child in attributes.items():
                if type(name) is not str: _fail("Independent source record has a nonstring field")
                child_token, child_copy = self.visit(child, depth + 1)
                rows.append((name, child_token))
                if self.copying: object.__setattr__(copied, name, child_copy)
            token = ("record", kind.__module__, kind.__name__, index, tuple(rows))
        self.seen[identity] = (index, copied)
        self.active.remove(identity)
        return token, copied

    def same(self, other):
        return (self.token == other.token and len(self.owners) == len(other.owners)
                and all(left is right for left, right in zip(self.owners, other.owners)))


class TorqueValidationScope:
    """One complete .22 validation, sealed after all report callbacks."""
    def __init__(self, source, work):
        if type(source) is not model.SceneModel or type(work) is not ReachExecutionWork:
            _fail("Torque supplied-byte validation requires native source and work")
        ledger = work.execution_budget
        if type(ledger) is not SharedExecutionBudget or ledger.resolved is None:
            _fail("Torque supplied-byte validation requires its admitted original allowance")
        self.source, self.work, self.ledger = source, work, ledger
        self.previous_guard = getattr(ledger, "_torque_context_guard", None)
        self.guard_present = "_torque_context_guard" in vars(ledger)
        if self.previous_guard is not None:
            # The producer has completed before the independent reader starts.
            # Its callback-free receipt must still admit the original source
            # before this scope captures a completely detached authority.
            self.previous_guard()
        self.original = _Graph(source, clone=True)
        self.model = self.original.copy
        self.detached = _Graph(self.model)
        self.previous_observer = work._source_after_charge
        self.observer = self._observe
        self.context = self._context()
        self._capture_context_watches()
        self.last_work = work.operations
        self.last_shared = ledger.operations
        self.active = False

    def _capture_context_watches(self):
        work, ledger = self.work, self.ledger
        fields = (
            (work, ("execution_budget", "external_check", "started", "max_operand_bits", "max_cache_entries",
                    "max_operations", "max_elapsed_ms", "counts", "_cache")),
            (ledger, ("check", "_clock", "started", "resolved", "policy", "_limits", "caller_caps",
                      "source_request", "admitted_entry_revision", "_torque_guarded")),
            (ledger.policy, ("max_operations", "max_elapsed_ms", "policy_id")),
            (ledger.resolved, ("source_request", "caller_caps", "host_ceilings", "effective", "policy_id")),
        )
        self.field_watches = tuple((owner, type(owner), vars(owner),
            tuple((name, vars(owner).get(name, _MISSING)) for name in names)) for owner, names in fields)
        self.method_watches = tuple((owner, type(owner), vars(owner), name, function,
            vars(owner).get(name, _MISSING)) for owner, methods in
            ((work, _WORK_METHODS), (ledger, _LEDGER_METHODS)) for name, function in methods)
        mappings = (ledger._limits, ledger.caller_caps, ledger.source_request,
                    ledger.resolved.source_request, ledger.resolved.caller_caps,
                    ledger.resolved.host_ceilings, ledger.resolved.effective)
        self.mapping_watches = tuple((value, tuple(value.items())) for value in mappings if value is not None)

    def _context(self):
        work, ledger = self.work, self.ledger
        if (type(work) is not ReachExecutionWork or type(ledger) is not SharedExecutionBudget
                or work.execution_budget is not ledger or work.external_check != ledger.tick
                or type(ledger._limits) is not dict or type(work.counts) is not dict
                or type(ledger.policy) is not HostPolicy or type(ledger.resolved) is not ResolvedBudget):
            _fail("Independent torque validation lost its original context")
        _native_methods(work, _WORK_METHODS)
        _native_methods(ledger, _LEDGER_METHODS)
        policy, resolved = ledger.policy, ledger.resolved
        maps = (ledger._limits, ledger.caller_caps, ledger.source_request,
                resolved.source_request, resolved.caller_caps, resolved.host_ceilings, resolved.effective)
        owners = (work.external_check, ledger.check, ledger._clock, resolved, policy,
                  work.counts, work._cache, *maps)
        values = (ledger.started, work.started, work.max_operand_bits, work.max_cache_entries,
                  work.max_operations, work.max_elapsed_ms, policy.max_operations,
                  policy.max_elapsed_ms, policy.policy_id, resolved.policy_id,
                  ledger.admitted_entry_revision,
                  *(_budget_mapping(value, mutable=index == 0, optional=index == 2)
                    for index, value in enumerate(maps)))
        return owners, values

    def _admit_context(self):
        # The preflight above proved native types and bounded immutable leaves.
        # Strongly retained field values admit the exact same native graph by
        # identity without rebuilding twenty bound methods and seven allowance
        # maps at each primitive. No replacement object's equality or iterator
        # runs before its identity has been admitted.
        changed = False
        for owner, kind, namespace, fields in self.field_watches:
            if type(owner) is not kind or vars(owner) is not namespace:
                changed = True
                break
            if any(namespace.get(name, _MISSING) is not value for name, value in fields):
                changed = True
                break
        if not changed:
            for owner, kind, namespace, name, function, value in self.method_watches:
                if (vars(kind).get(name) is not function
                        or namespace.get(name, _MISSING) is not value):
                    changed = True
                    break
        if not changed:
            for mapping, pairs in self.mapping_watches:
                if (len(mapping) != len(pairs) or any(key is not old_key or value is not old_value
                        for (key, value), (old_key, old_value) in zip(mapping.items(), pairs))):
                    changed = True
                    break
        expected_guard = None if self.active else self.previous_guard
        guard = vars(self.ledger).get("_torque_context_guard", _MISSING)
        if not self.guard_present and not self.active:
            expected_guard = _MISSING
        if (changed or guard is not expected_guard
                or self.active and self.work._source_after_charge is not self.observer):
            _fail("Independent torque validation source/work authority changed during a callback")

    def _observe(self):
        if self.previous_observer is not None:
            self.previous_observer()
        self._admit_context()
        numerical, shared = self.work.operations, self.ledger.operations
        if (type(numerical) is not int or type(shared) is not int
                or numerical <= self.last_work or shared <= self.last_shared):
            _fail("Independent torque validation work counters must increase at every original charge")
        self.last_work, self.last_shared = numerical, shared

    def _admit_sources(self):
        self._admit_context()
        if not self.original.same(_Graph(self.source)):
            _fail("Original source changed during complete torque byte validation")
        if not self.detached.same(_Graph(self.model)):
            _fail("Detached independent source changed during complete torque byte validation")

    def __enter__(self):
        self._admit_context()
        self.active = True
        # No producer numerical state is read within this complete validator.
        # Its old source watcher is therefore inactive while this scope owns
        # detached authority. The ledger's original callback, exact consumed
        # counter, clock and context guards stay enabled throughout.
        self.ledger._torque_context_guard = None
        self.work._source_after_charge = self.observer
        try:
            # Each complete bounded graph record has a charged receipt read;
            # immutable scalar leaves are admitted together with their owner.
            amount = len(self.original.owners) + (self.original.byte_count + 63) // 64
            self.work.charge("independent_torque_source_capture", amount)
            self._admit_sources()
        except BaseException:
            self._restore_guard()
            self.work._source_after_charge = self.previous_observer
            self.active = False
            raise
        return self

    def __exit__(self, kind, error, traceback):
        try:
            if error is None:
                amount = len(self.original.owners) + (self.original.byte_count + 63) // 64
                self.work.charge("independent_torque_source_final_admission", amount)
                # There are no callbacks or reported-success writes after
                # these complete owner/content checks.
                self._admit_sources()
                self._restore_guard()
                self.active = False
                if self.previous_guard is not None:
                    self.previous_guard()
                self._admit_context()
        finally:
            self._restore_guard()
            self.work._source_after_charge = self.previous_observer
            self.active = False
        return False

    def _restore_guard(self):
        if self.guard_present:
            self.ledger._torque_context_guard = self.previous_guard
        else:
            vars(self.ledger).pop("_torque_context_guard", None)
