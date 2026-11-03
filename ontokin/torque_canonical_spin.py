"""Owned point-spin computations for the adopted C092 .22 method.

The original work object remains the only allowance and the only numerical
LRU. Immutable payloads in a distinct namespace retain completion provenance;
a callback-written cache value cannot establish numerical authority. This is
ordinary callback ownership, not a sandbox for a hostile Python interpreter.
"""
from __future__ import annotations

from collections import OrderedDict
from fractions import Fraction as F
import math
import struct
import sys
from types import FunctionType, MethodType
from weakref import WeakKeyDictionary

from . import reach_numeric as numeric
from . import reach_pose as pose
from .diagnostics import OntoKinError


_NAMESPACE = "ontokin.c092.canonical-point/0.1.0"
_OWNERS = WeakKeyDictionary()
_MISSING = object()
_RUNTIME_BINDING = None


def _fail():
    raise OntoKinError("OKL-E-RESOURCE",
        "Canonical torque point work requires its original operands and numerical authority.",
        category="resource_limit", phase="evaluation",
        details={"budget_reason": "execution_context_required"})


def _pack(value, work, watches=None):
    """Callback-free, bounded native tokens; no Fraction is retained in a key."""
    kind = type(value)
    if value is None:
        return ("none",)
    if kind is bool:
        return ("bool", value)
    if kind is int:
        work.guard(value)
        return ("int", value)
    if kind is str and len(value) <= 4096:
        return ("str", value)
    if kind is float and math.isfinite(value):
        return ("float", value.hex())
    if kind is F:
        n, d = value._numerator, value._denominator
        if type(n) is not int or type(d) is not int or d <= 0:
            _fail()
        work.guard(n, d)
        if watches is not None:
            watches.append((value, F, (n, d)))
        return ("fraction", n, d)
    if kind in (tuple, list) and len(value) <= 256:
        if watches is not None and kind is list:
            watches.append((value, list, tuple(value)))
        return ("tuple" if kind is tuple else "list",
                tuple(_pack(v, work, watches) for v in value))
    if kind is pose.RotationValue:
        parts = (value.components, value.error_rad, value.frozen_projection)
        if watches is not None:
            watches.append((value, kind, parts))
        return ("rotation", tuple(_pack(v, work, watches) for v in parts))
    if kind is pose.SpinPlan:
        parts = (value.scaled_omega, value.maximum, value.norm_bounds,
                 value.pi_bounds, value.max_elapsed_s, value.precision_bits,
                 value.argument_error_rad)
        if watches is not None:
            watches.append((value, kind, parts))
        return ("spin", tuple(_pack(v, work, watches) for v in parts))
    _fail()


def _unpack(token):
    kind = token[0]
    if kind == "none": return None
    if kind in ("bool", "int", "str"): return token[1]
    if kind == "float": return float.fromhex(token[1])
    if kind == "fraction": return F(token[1], token[2])
    parts = tuple(_unpack(v) for v in token[1])
    if kind == "tuple": return parts
    if kind == "list": return list(parts)
    if kind == "rotation": return pose.RotationValue(*parts)
    if kind == "spin": return pose.SpinPlan(*parts)
    _fail()


def _watches_current(watches):
    for value, kind, parts in watches:
        if type(value) is not kind:
            return False
        if kind is F:
            if value._numerator is not parts[0] or value._denominator is not parts[1]:
                return False
        elif kind is list:
            if len(value) != len(parts) or any(a is not b for a, b in zip(value, parts)):
                return False
        elif kind is pose.RotationValue:
            if any(a is not b for a, b in zip(
                    (value.components, value.error_rad, value.frozen_projection), parts)):
                return False
        elif kind is pose.SpinPlan:
            if any(a is not b for a, b in zip(
                    (value.scaled_omega, value.maximum, value.norm_bounds,
                     value.pi_bounds, value.max_elapsed_s, value.precision_bits,
                     value.argument_error_rad), parts)):
                return False
        else:
            return False
    return True


def _authority_snapshot():
    """Bind the actual unchanged primitives, descriptors and their globals."""
    modules = (numeric, pose, sys.modules[__name__])
    functions, classes, bindings = {}, {}, {}
    for module in modules:
        for name, item in tuple(vars(module).items()):
            if type(item) is FunctionType and item.__module__ == module.__name__:
                functions[id(item)] = item
                bindings[(id(vars(module)), name)] = (vars(module), name, item)
            elif type(item) is type and item.__module__ == module.__name__:
                classes[id(item)] = item
    classes[id(F)] = F
    for cls in tuple(classes.values()):
        for name, item in tuple(vars(cls).items()):
            function = item.__func__ if type(item) in (classmethod, staticmethod) else item
            if type(function) is FunctionType:
                functions[id(function)] = function
            elif type(item) is property:
                for f in (item.fget, item.fset, item.fdel):
                    if f is not None: functions[id(f)] = f
    records = []
    for function in functions.values():
        namespace, builtins = function.__globals__, function.__builtins__
        names, pending = set(), [function.__code__]
        while pending:
            code = pending.pop()
            names.update(code.co_names)
            pending.extend(v for v in code.co_consts if type(v) is type(code))
        for name in names:
            # This receipt's own completed catalogue is assigned once below.
            if namespace is globals() and name in ("_AUTHORITY", "_RUNTIME_BINDING"):
                continue
            owner = namespace if name in namespace else builtins
            if name in owner:
                bindings[(id(owner), name)] = (owner, name, owner[name])
        records.append((function, function.__code__, function.__defaults__,
                        function.__kwdefaults__, function.__closure__, namespace,
                        builtins, None if function.__kwdefaults__ is None
                        else tuple(function.__kwdefaults__.items())))
    class_records = []
    for cls in classes.values():
        slots = []
        for base in cls.__mro__:
            declared = vars(base).get("__slots__", ())
            declared = (declared,) if type(declared) is str else declared
            for name in declared:
                if name not in ("__dict__", "__weakref__"):
                    slots.append("_" + base.__name__.lstrip("_") + name
                        if name.startswith("__") and not name.endswith("__") else name)
        class_records.append((cls, cls.__bases__, cls.__mro__,
            tuple((k,v) for k,v in vars(cls).items() if k != "__slotnames__"), tuple(slots)))
    # Attribute calls through these native modules are part of the primitives.
    module_records = tuple((m, tuple(vars(m).items())) for m in (math, struct))
    fractional = tuple((value, value._numerator, value._denominator)
        for _, _, value in bindings.values() if type(value) is F)
    return tuple(records), tuple(class_records), tuple(bindings.values()), module_records, fractional


def _authority_current(authority):
    functions, classes, bindings, modules, fractions = authority
    for f, code, defaults, kwdefaults, closure, namespace, builtins, kwitems in functions:
        if (type(f) is not FunctionType or f.__code__ is not code
                or f.__defaults__ is not defaults or f.__kwdefaults__ is not kwdefaults
                or f.__closure__ is not closure or f.__globals__ is not namespace
                or f.__builtins__ is not builtins
                or kwdefaults is not None and (len(kwdefaults) != len(kwitems)
                    or any(a is not x or b is not y for (a,b),(x,y)
                           in zip(kwdefaults.items(), kwitems)))):
            return False
    for cls, bases, mro, entries, slots in classes:
        current = vars(cls)
        if (cls.__bases__ is not bases or cls.__mro__ is not mro
                or len(current) != len(entries) + int("__slotnames__" in current)
                or any(current.get(name, _MISSING) is not value for name, value in entries)):
            return False
        # copyreg lazily publishes this exact nonsemantic slot-name cache.
        # It may appear after deepcopy; foreign names/types still refuse.
        if "__slotnames__" in current:
            actual = current["__slotnames__"]
            if type(actual) is not list or any(type(v) is not str for v in actual) or tuple(actual) != slots:
                return False
    if any(owner.get(name, _MISSING) is not value for owner, name, value in bindings):
        return False
    for module, entries in modules:
        current = vars(module)
        if len(current) != len(entries) or any(current.get(name, _MISSING) is not value for name,value in entries):
            return False
    return all(type(v) is F and v._numerator is n and v._denominator is d
               for v,n,d in fractions)


def bind_simulator_type(cls):
    """Seal the .22 dispatch once, after its class has finished importing."""
    global _RUNTIME_BINDING
    if _RUNTIME_BINDING is not None:
        _fail()
    rows = []
    for name in ("_advance_orientation", "_context", "_guard_context"):
        function = vars(cls)[name]
        namespace, builtins = function.__globals__, function.__builtins__
        bindings = []
        for key in function.__code__.co_names:
            owner = namespace if key in namespace else builtins
            if key in owner:
                bindings.append((owner, key, owner[key]))
        rows.append((name, function, function.__code__, function.__defaults__,
            function.__kwdefaults__, function.__closure__, namespace, builtins,
            None if function.__kwdefaults__ is None else tuple(function.__kwdefaults__.items()),
            tuple(bindings)))
    _RUNTIME_BINDING = (cls, cls.__bases__, cls.__mro__, tuple(rows))


def admit_simulator(simulator):
    cls, bases, mro, rows = _RUNTIME_BINDING
    actual = type(simulator)
    if (type(actual) is not type or cls not in actual.__mro__
            or cls.__bases__ is not bases or cls.__mro__ is not mro):
        _fail()
    namespace = object.__getattribute__(simulator, "__dict__")
    for name, function, code, defaults, kwdefaults, closure, module, builtins, kwitems, bindings in rows:
        owner = next(base for base in actual.__mro__ if name in vars(base))
        if (name in namespace or vars(owner)[name] is not function
                or function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not kwdefaults or function.__closure__ is not closure
                or function.__globals__ is not module or function.__builtins__ is not builtins
                or kwdefaults is not None and (len(kwdefaults) != len(kwitems)
                    or any(a is not x or b is not y for (a,b),(x,y) in zip(kwdefaults.items(),kwitems)))
                or any(mapping.get(key, _MISSING) is not value for mapping,key,value in bindings)):
            _fail()


class _PointScope:
    def __init__(self, simulator, initial, omega, elapsed):
        admit_simulator(simulator)
        self.simulator, self.work = simulator, simulator.work
        self.ops, self.context = simulator.pose_ops, simulator._context
        self.authority = _AUTHORITY
        if not _authority_current(self.authority):
            _fail()
        self.watches = []
        self.inputs = tuple(_pack(v, self.work, self.watches) for v in (initial, omega, elapsed))
        self.cache = self.work._cache
        self.methods = tuple((name, getattr(numeric.ReachExecutionWork, name))
            for name in ("charge", "guard", "guard_bits", "resource", "lookup", "remember"))
        if type(self.cache) is not OrderedDict:
            _fail()
        self.admit()

    def admit(self):
        admit_simulator(self.simulator)
        if (self.simulator.work is not self.work or self.simulator.pose_ops is not self.ops
                or type(self.ops) is not pose.ReachPoseOps or self.ops.work is not self.work
                or type(self.work) is not numeric.ReachExecutionWork
                or self.work._cache is not self.cache or type(self.cache) is not OrderedDict
                or not _authority_current(self.authority)
                or not _watches_current(self.watches)):
            _fail()
        for name, function in self.methods:
            actual = getattr(self.work, name)
            if type(actual) is not MethodType or actual.__self__ is not self.work or actual.__func__ is not function:
                _fail()
        self.context()


class _CacheWork(tuple):
    """Read-only adapter: all allowance, counters and callbacks stay original."""
    __slots__ = ()

    def __new__(cls, scope):
        return tuple.__new__(cls, (scope,))

    @property
    def parent(self): return self[0].work
    @property
    def max_operand_bits(self): return self.parent.max_operand_bits
    @property
    def max_cache_entries(self): return self.parent.max_cache_entries
    @property
    def callback_error(self): return self.parent.callback_error

    def charge(self, kind="checkpoint", amount=1):
        self[0].admit()
        self.parent.charge(kind, amount)
        self[0].admit()

    def guard(self, *values): self.parent.guard(*values)
    def guard_bits(self, bits): self.parent.guard_bits(bits)
    def resource(self, *args): self.parent.resource(*args)

    def _owners(self):
        parent = self.parent
        owners = _OWNERS.setdefault(parent, {})
        # Metadata only retains identities of entries still in the one LRU.
        current = {id(value) for value in parent._cache.values()}
        for identity in tuple(owners):
            if identity not in current:
                del owners[identity]
        return owners

    def lookup(self, key):
        scope = self[0]
        scope.admit()
        encoded = (_NAMESPACE, _pack(key, self.parent))
        value = self.parent.lookup(encoded)
        scope.admit()
        owners = self._owners()
        if value is None:
            return None
        if owners.get(id(value)) is not value or type(value) is not tuple or value[0] != encoded:
            _fail()
        # The owned tuple contains native immutable leaves only. Detached
        # arithmetic operands cannot be changed through the shared cache.
        result = _unpack(value[1])
        scope.admit()
        return result

    def remember(self, key, value, *, admission=None):
        scope = self[0]
        scope.admit()
        encoded = (_NAMESPACE, _pack(key, self.parent))
        entry = (encoded, _pack(value, self.parent))
        self.parent.remember(encoded, entry, admission=admission)
        scope.admit()
        owners = self._owners()
        if self.parent._cache.get(encoded) is entry:
            owners[id(entry)] = entry


def advance_orientation(simulator, initial, omega, elapsed):
    """Apply the unchanged first-certifying kernel to detached exact operands."""
    scope = _PointScope(simulator, initial, omega, elapsed)
    copied_initial, copied_omega, copied_elapsed = (_unpack(v) for v in scope.inputs)
    ops = pose.ReachPoseOps(_CacheWork(scope))
    result = ops.advance_orientation(copied_initial, copied_omega, copied_elapsed,
                                     phase_plan=None)
    scope.admit()
    # A stationary operation preserves the actual complete admitted origin,
    # including its frozen public projection and exact error allowance.
    if result is copied_initial:
        return initial
    return result


_AUTHORITY = _authority_snapshot()
