"""Owned point-spin computations for the adopted C092 .22 method.

The original work object remains the only allowance and the only numerical
LRU. Immutable payloads in a distinct namespace retain completion provenance;
a callback-written cache value cannot establish numerical authority. This is
ordinary callback ownership, not a sandbox for a hostile Python interpreter.
"""
from __future__ import annotations

from collections import OrderedDict
from dis import get_instructions
from fractions import Fraction as F
from itertools import chain, repeat
import math
from operator import attrgetter, is_ as _IDENTICAL
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

# Native readers are captured before the authority catalogue. Their bindings
# are admitted with every other global; they only traverse original functions,
# native dictionaries/proxies, and immutable owning receipts.
_FUNCTION_ATTRIBUTES = attrgetter("__code__", "__defaults__", "__kwdefaults__")
_CHAIN = chain.from_iterable
_DICT_GET = dict.get
_DICT_ITEMS = dict.items
_DICT_CONTAINS = dict.__contains__
_PROXY_GET = type(type.__dict__).get
_PROXY_CONTAINS = type(type.__dict__).__contains__
_PREDICATE_COMPARISONS = 4096
_PREDICATE_TEXT_BYTES = 512 * 1024


def _compile_fixed_predicate(functions=(), keywords=(), present=(), absent=(), *,
                             present_first=False):
    """Specialize a fixed import-time receipt, never a source or an admission.

    Values become strongly owned private closure operands, not generated source
    text. The original generic path remains available for oversized or unusual
    static receipts. Each caller seals the generated executable before use.
    """
    count = 3 * len(functions) + sum(1 + len(row[2]) for row in keywords)
    count += len(present) + len(absent)
    if count > _PREDICATE_COMPARISONS:
        return None
    if (any(type(row[0]) is not FunctionType for row in functions)
            or any(type(owner) is not dict or type(length) is not int
                   or length < 0 or len(expected) != 2 * length
                   for owner, length, expected in keywords)
            or any(type(row[1]) is not str for row in (*present, *absent))):
        return None
    operands, indices, body = [], {}, []

    def operand(value):
        identity = id(value)
        if identity not in indices:
            indices[identity] = len(operands)
            operands.append(value)
        return "v" + str(indices[identity])

    def require(expression):
        body.extend(("        if " + expression + ":", "            return False"))

    for function, code, defaults, kwdefaults in functions:
        name = operand(function)
        for slot, expected in (("__code__", code), ("__defaults__", defaults),
                               ("__kwdefaults__", kwdefaults)):
            require(name + "." + slot + " is not " + operand(expected))
    for owner, length, expected in keywords:
        name = operand(owner)
        require(operand(len) + "(" + name + ") != " + operand(length))
        if length:
            body.append("        iterator = " + operand(iter) + "(" + operand(_DICT_ITEMS)
                        + "(" + name + "))")
            for index in range(length):
                body.append("        pair = " + operand(next) + "(iterator)")
                require("pair[0] is not " + operand(expected[2 * index]))
                require("pair[1] is not " + operand(expected[2 * index + 1]))
    groups = ((present, True), (absent, False)) if present_first else ((absent, False), (present, True))
    for rows, exists in groups:
        for row in rows:
            owner, name = operand(row[0]), operand(row[1])
            if exists:
                require("getter(" + owner + ", " + name + ", " + operand(row[3])
                        + ") is not " + operand(row[2]))
            else:
                require("contains(" + owner + ", " + name + ")")
    lines = ["def build(values):"]
    lines.extend("    v" + str(i) + " = values[" + str(i) + "]" for i in range(len(operands)))
    lines.extend(("    def predicate(getter, contains):", *body,
                  "        return True", "    return predicate"))
    source = "\n".join(lines) + "\n"
    if len(source.encode("ascii")) > _PREDICATE_TEXT_BYTES:
        return None
    namespace = {"__builtins__": {}}
    exec(compile(source, "<ontokin-fixed-authority-predicate>", "exec"), namespace)
    owned = tuple(operands)
    function = namespace["build"](owned)
    forbidden = {"LOAD_GLOBAL", "LOAD_NAME", "IMPORT_NAME", "IMPORT_FROM", "IMPORT_STAR",
                 "STORE_GLOBAL", "STORE_NAME", "DELETE_GLOBAL", "DELETE_NAME"}
    if (type(function) is not FunctionType or function.__defaults__ is not None
            or function.__kwdefaults__ is not None
            or any(item.opname in forbidden for item in get_instructions(function))
            or any(type(value) is type(function.__code__) for value in function.__code__.co_consts)):
        raise ValueError("A fixed authority predicate acquired an unowned executable dependency.")
    return (function, function.__code__, function.__defaults__, function.__kwdefaults__,
            function.__closure__, function.__globals__, function.__builtins__,
            owned, (functions, keywords, present, absent), source)


def compile_point_entry(authority):
    """Keep the private entry's three diagnostic groups and binding order."""
    records, bindings = authority[0], authority[2]
    missing = object()
    slots = tuple(row[:4] for row in records)
    keywords = tuple((row[3], len(row[7]), tuple(_CHAIN(row[7])))
                     for row in records if row[3] is not None)
    present = tuple((*row, missing) for row in bindings if row[1] in row[0])
    absent = tuple(row for row in bindings if row[1] not in row[0])
    predicates = (_compile_fixed_predicate(functions=slots),
                  _compile_fixed_predicate(keywords=keywords),
                  _compile_fixed_predicate(present=present, absent=absent, present_first=True))
    return predicates if all(row is not None for row in predicates) else None


def _compile_functions(records):
    functions = tuple(row[0] for row in records)
    if any(type(function) is not FunctionType for function in functions):
        _fail()
    # Native functions cannot change __class__, __globals__, __closure__, or
    # __builtins__ through ordinary Python assignment, deletion, or instance
    # shadowing. Their original owning records retain those read-only slots;
    # globals/builtins contents remain independently checked below. Only the
    # three mutable function slots require a fresh identity read per callback.
    keywords = tuple((row[3], len(row[7]), tuple(_CHAIN(row[7])))
                     for row in records if row[3] is not None)
    return (functions, tuple(_CHAIN(row[1:4] for row in records)), keywords,
            _compile_fixed_predicate(functions=tuple(row[:4] for row in records), keywords=keywords))


def _functions_current(compiled):
    functions, attributes, keywords, specialized = compiled
    if specialized is not None:
        function, code, defaults, kwdefaults = specialized[:4]
        if (function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not kwdefaults):
            return False
        return function(_DICT_GET, _DICT_CONTAINS)
    if not all(map(_IDENTICAL, _CHAIN(map(_FUNCTION_ATTRIBUTES, functions)), attributes)):
        return False
    for owner, length, identities in keywords:
        if len(owner) != length or not all(map(_IDENTICAL, _CHAIN(_DICT_ITEMS(owner)), identities)):
            return False
    return True


def _compile_bindings(rows):
    present = tuple(row for row in rows if row[1] in row[0])
    absent = tuple(row for row in rows if row[1] not in row[0])
    # This fallback is created after the owning rows and cannot be one of
    # their original values. A removed present sentinel binding cannot mask
    # itself as an absent key, and planted sentinels cannot mask new shadows.
    missing = object()
    return (tuple(row[0] for row in present), tuple(row[1] for row in present),
            tuple(row[2] for row in present), tuple(row[0] for row in absent),
            tuple(row[1] for row in absent), missing,
            _compile_fixed_predicate(present=tuple((*row, missing) for row in present), absent=absent))


def _bindings_current(compiled, getter=_DICT_GET, contains=_DICT_CONTAINS):
    owners, names, expected, absent_owners, absent_names, missing, specialized = compiled
    if specialized is not None:
        function, code, defaults, kwdefaults = specialized[:4]
        if (function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not kwdefaults):
            return False
        return function(getter, contains)
    return (not any(map(contains, absent_owners, absent_names))
            and all(map(_IDENTICAL, map(getter, owners, names, repeat(missing)), expected)))


def _compiled_authority(raw):
    # Keep every original object alive in the first five owning fields. The
    # supplemental native-identity vectors never invoke foreign equality.
    functions, classes, bindings, modules, fractions = raw
    compiled = (_compile_functions(functions),
        tuple((tuple(name for name, _ in row[3]), tuple(value for _, value in row[3]), object())
              for row in classes),
        _compile_bindings(bindings),
        tuple((tuple(name for name, _ in row[1]), tuple(value for _, value in row[1]), object())
              for row in modules))
    return (*raw, compiled)


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
            if namespace is globals() and name in ("_AUTHORITY", "_POINT_AUTHORITY", "_RUNTIME_BINDING"):
                continue
            owner = namespace if name in namespace else builtins
            if name in owner:
                bindings[(id(owner), name)] = (owner, name, owner[name])
                if owner is builtins:
                    bindings[(id(namespace), name)] = (namespace, name, _MISSING)
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


def _classes_current(classes, vectors):
    for (cls, bases, mro, entries, slots), (names, expected, missing) in zip(classes, vectors):
        current = vars(cls)
        if (cls.__bases__ is not bases or cls.__mro__ is not mro
                or len(current) != len(entries) + int("__slotnames__" in current)
                or not all(map(_IDENTICAL, map(_PROXY_GET, repeat(current), names, repeat(missing)), expected))):
            return False
        # copyreg lazily publishes this exact nonsemantic slot-name cache.
        # It may appear after deepcopy; foreign names/types still refuse.
        if "__slotnames__" in current:
            actual = current["__slotnames__"]
            if type(actual) is not list or any(type(v) is not str for v in actual) or tuple(actual) != slots:
                return False
    return True


def _authority_current(authority):
    functions, classes, bindings, modules, fractions, compiled = authority
    function_vectors, class_vectors, binding_vectors, module_vectors = compiled
    if not _functions_current(function_vectors) or not _classes_current(classes, class_vectors):
        return False
    if not _bindings_current(binding_vectors):
        return False
    for (module, entries), (names, expected, missing) in zip(modules, module_vectors):
        current = vars(module)
        if (len(current) != len(entries)
                or not all(map(_IDENTICAL, map(_DICT_GET, repeat(current), names, repeat(missing)), expected))):
            return False
    return all(type(v) is F and v._numerator is n and v._denominator is d
               for v,n,d in fractions)


def bind_simulator_type(cls):
    """Seal the .22 dispatch once, after its class has finished importing."""
    global _RUNTIME_BINDING
    if _RUNTIME_BINDING is not None:
        _fail()
    rows, methods, all_bindings = [], {}, {}
    for base in cls.__mro__:
        for name, function in type.__getattribute__(base, "__dict__").items():
            if name not in methods and type(function) is FunctionType:
                methods[name] = function
    for name, function in methods.items():
        namespace, builtins = function.__globals__, function.__builtins__
        bindings = []
        names, pending = set(), [function.__code__]
        while pending:
            code = pending.pop()
            names.update(code.co_names)
            pending.extend(v for v in code.co_consts if type(v) is type(code))
        for key in sorted(names):
            owner = namespace if key in namespace else builtins
            if key in owner:
                bindings.append((owner, key, owner[key]))
                if owner is builtins:
                    bindings.append((namespace, key, _MISSING))
        for owner, key, value in bindings:
            all_bindings[(id(owner), key)] = (owner, key, value)
        rows.append((name, function, function.__code__, function.__defaults__,
            function.__kwdefaults__, function.__closure__, namespace, builtins,
            None if function.__kwdefaults__ is None else tuple(function.__kwdefaults__.items()),
            tuple(bindings)))
    storage_names = ("__getattribute__", "__getattr__", "__dict__", "work",
        "pose_ops", "model", "state", "events", "_torque_ledger",
        "_torque_work", "_torque_context_receipt", "_torque_model",
        "_torque_revision", "_torque_objects_owner", "_torque_limits_owner",
        "_torque_guard_hook", "_torque_state_owner", "_torque_history_owner",
        "_torque_source_watches", "_torque_constructed", "_torque_event_order")
    dictionaries = tuple(type.__getattribute__(base, "__dict__") for base in cls.__mro__)
    storage = tuple((name, next((mapping[name] for mapping in dictionaries
        if name in mapping), _MISSING)) for name in storage_names)
    descriptors = {}
    for name, expected in (*storage, *((row[0], row[1]) for row in rows)):
        current = _MISSING
        for mapping in dictionaries:
            current = mapping.get(name, _MISSING)
            descriptors[(id(mapping), name)] = (mapping, name, current)
            if name in mapping:
                break
        if current is not expected:
            _fail()
    owned_bindings, owned_descriptors = tuple(all_bindings.values()), tuple(descriptors.values())
    compiled = (_compile_functions(tuple(row[1:9] for row in rows)),
                _compile_bindings(owned_bindings), tuple(row[0] for row in rows),
                _compile_bindings(owned_descriptors),
                owned_bindings, owned_descriptors)
    _RUNTIME_BINDING = (cls, cls.__bases__, cls.__mro__, tuple(rows), storage, compiled)


def admit_simulator(simulator):
    if not _authority_current(_POINT_AUTHORITY):
        _fail()
    _admit_simulator_runtime(simulator)


def admit_simulator_after_entry(simulator):
    """After the request-private guard admitted point functions and bindings.

    There is no callback between that exact entry receipt and this body. Keep
    helper class/descriptor and complete runtime admission here; public callers
    use admit_simulator and retain the full point entry check as well.
    """
    if not _classes_current(_POINT_AUTHORITY[1], _POINT_AUTHORITY[5][1]):
        _fail()
    _admit_simulator_runtime(simulator)


def _admit_simulator_runtime(simulator):
    cls, bases, mro, rows, storage, compiled = _RUNTIME_BINDING
    function_vectors, binding_vectors, names, descriptor_vectors, _, _ = compiled
    actual = type(simulator)
    if (type(actual) is not type or cls not in actual.__mro__
            or cls.__bases__ is not bases or cls.__mro__ is not mro):
        _fail()
    # Even object.__getattribute__(instance, "__dict__") invokes a foreign
    # data descriptor. Check raw class resolution, including subclass lookup
    # hooks and inherited storage, before any ordinary instance attribute.
    if actual is cls:
        # Every earlier MRO namespace retains a witnessed absence until the
        # original provider. New shadow descriptors therefore cannot hide a
        # later method/storage field. All receipts own their original values.
        if not _bindings_current(descriptor_vectors, _PROXY_GET, _PROXY_CONTAINS):
            _fail()
    else:
        # Preserve the existing supported subclass domain and exact effective
        # resolution through its complete MRO; this is not a class allowlist.
        dictionaries = tuple(type.__getattribute__(base, "__dict__")
                             for base in actual.__mro__)
        for name, expected in (*storage, *((row[0], row[1]) for row in rows)):
            current = next((mapping[name] for mapping in dictionaries if name in mapping), _MISSING)
            if current is not expected:
                _fail()
    namespace = object.__getattribute__(simulator, "__dict__")
    if (any(map(_DICT_CONTAINS, repeat(namespace), names))
            or not _functions_current(function_vectors) or not _bindings_current(binding_vectors)):
        _fail()


class _PointScope:
    def __init__(self, simulator, initial, omega, elapsed):
        admit_simulator(simulator)
        self.authority = _AUTHORITY
        if not _authority_current(self.authority):
            _fail()
        self.simulator, self.work = simulator, simulator.work
        self.ops, self.context = simulator.pose_ops, simulator._context
        self.watches = []
        self.inputs = tuple(_pack(v, self.work, self.watches) for v in (initial, omega, elapsed))
        self.cache = self.work._cache
        self.methods = tuple((name, getattr(numeric.ReachExecutionWork, name))
            for name in ("charge", "guard", "guard_bits", "resource", "lookup", "remember"))
        if type(self.cache) is not OrderedDict:
            _fail()
        self.admit()

    def admit(self):
        # Validate helper descriptors before even consulting this instance.
        # The captured public context then admits runtime dispatch and its
        # original context exactly once. No callback occurs before the work,
        # cache, operand, and native-method checks below.
        if not _authority_current(_AUTHORITY):
            _fail()
        self.context()
        if (self.authority is not _AUTHORITY
                or self.simulator.work is not self.work or self.simulator.pose_ops is not self.ops
                or type(self.ops) is not pose.ReachPoseOps or self.ops.work is not self.work
                or type(self.work) is not numeric.ReachExecutionWork
                or self.work._cache is not self.cache or type(self.cache) is not OrderedDict
                or type(self.work.max_cache_entries) is not int
                or not 1 <= self.work.max_cache_entries <= 256
                or len(self.cache) > self.work.max_cache_entries
                or not _watches_current(self.watches)):
            _fail()
        for name, function in self.methods:
            actual = getattr(self.work, name)
            if type(actual) is not MethodType or actual.__self__ is not self.work or actual.__func__ is not function:
                _fail()


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


_AUTHORITY = _compiled_authority(_authority_snapshot())
# The original ledger callback guard checks this small dispatch graph before
# control returns to any helper method or field lookup. Full arithmetic and
# operand admission remains separate and still precedes each point operation.
_POINT_AUTHORITY = _compiled_authority((tuple(row for row in _AUTHORITY[0]
                        if row[0].__module__ == __name__),
                    tuple(row for row in _AUTHORITY[1]
                        if row[0].__module__ == __name__),
                    _AUTHORITY[2], (), ()))
