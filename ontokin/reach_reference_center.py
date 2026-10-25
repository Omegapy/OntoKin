"""Private exact centers for a complete independent supplied-byte proof.

The public reference still returns Fraction intervals.  This optional reader
representation carries a proved Euclidean radius separately and never treats
its center as an exact source pose.  It consumes only independent source-plan
recipes, direct interval seeds and Taylor increments.  Numeric cursors share
the existing arithmetic LRU and pending-publication/source-batch admission.
"""
from dataclasses import dataclass, field, replace
from fractions import Fraction as F
import math
import fractions
import numbers
import sys
from types import FunctionType, GetSetDescriptorType, MemberDescriptorType, MethodType, ModuleType

from .reach_reference import (
    MAX_CACHE, MAX_OPERAND_BITS, Interval, ReferenceError, _Arithmetic, _PoseArithmetic,
    _recording_source_signature,
)


@dataclass(frozen=True)
class _CenteredPose:
    position: tuple
    orientation: tuple
    position_radius: F
    orientation_radius: F
    axis: int | None
    seal: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "seal", _integers((self.position, self.orientation,
                           self.position_radius, self.orientation_radius, self.axis)))


@dataclass(frozen=True)
class _CenteredNode:
    vector: tuple
    position_radius: F
    identity_offset: int = 0
    coefficient_source: str | None = None
    product_pair: tuple | None = None
    product_owner: tuple | None = None
    seal: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "seal", _integers((self.vector, self.position_radius,
                                                  self.identity_offset, self.coefficient_source,
                                                  self.product_pair, self.product_owner)))


@dataclass(frozen=True)
class _CenteredCoefficients:
    scalar: F
    active: F
    diagonal: F
    cross: F
    products: object = None
    seal: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "seal", _integers((self.scalar, self.active,
                                                  self.diagonal, self.cross)))


@dataclass(frozen=True)
class _CenteredProducts:
    token: object
    clock: tuple
    pair: tuple
    operand: F
    first: F
    last: F
    seal: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "seal", _integers((self.clock, self.pair,
                                                   self.operand, self.first, self.last)))


@dataclass(frozen=True)
class _CenteredCursor:
    witness: tuple
    axis: int
    rate: F
    clock: F
    orientation: tuple
    radius: F
    increment: tuple | None
    steps: int
    seal: tuple


class _ChangedDomain(Exception):
    """Only a latched departure from this optional domain may fall back."""


class _OriginalFailure(Exception):
    """Carry an unchanged independent oracle failure outside optional retry."""
    def __init__(self, error):
        self.error = error


def _native(value, *, magnitude=256):
    return (type(value) is F and type(value.numerator) is int
            and type(value.denominator) is int and value.denominator > 0
            and abs(value.numerator).bit_length() <= 138
            and value.denominator.bit_length() <= 129
            and value.denominator <= 1 << 128
            and not value.denominator & (value.denominator - 1)
            and abs(value) <= magnitude)


def _integers(value, _depth=0):
    """A bounded value seal, independent of mutable Fraction aliases."""
    if type(value) is F:
        if (type(value.numerator) is not int or type(value.denominator) is not int
                or value.denominator <= 0):
            raise ReferenceError("identity", "Independent centered rational changed")
        return value.numerator, value.denominator
    if type(value) is tuple:
        if _depth >= 3 or len(value) > 10:
            raise ReferenceError("identity", "Independent centered seal exceeds its bounded shape")
        return tuple(_integers(item, _depth + 1) for item in value)
    if value is None or type(value) in (str, int):
        return value
    raise ReferenceError("identity", "Independent centered value has a foreign shape")


def _cursor_seal(cursor):
    return _integers((cursor.rate, cursor.clock, cursor.orientation, cursor.radius,
                      cursor.increment, cursor.steps, cursor.axis))


def guard_cursor(arithmetic, cursor):
    """Admit this representation at the batch's final callback-free gate."""
    if (type(cursor) is not _CenteredCursor or type(cursor.steps) is not int
            or not 0 <= cursor.steps <= 64 or type(cursor.axis) is not int
            or cursor.axis not in (0, 1, 2)
            or type(cursor.orientation) is not tuple or len(cursor.orientation) != 4
            or any(not _native(value, magnitude=2) for value in cursor.orientation)
            or type(cursor.rate) is not F or type(cursor.clock) is not F
            or cursor.increment is not None and (
                type(cursor.increment) is not tuple or len(cursor.increment) != 10
                or any(type(value) is not F for value in cursor.increment))
            or not _native(cursor.radius, magnitude=1)
            or _cursor_seal(cursor) != cursor.seal
            or not 0 <= cursor.radius <= F(1, 1 << (112 if cursor.steps == 0 else 104))
            or any(cursor.orientation[index] for index in (1, 2, 3)
                   if index != cursor.axis + 1)):
        raise ReferenceError("identity", "Independent centered cursor changed")
    arithmetic.guard(cursor.rate, cursor.clock, cursor.radius, cursor.steps,
                     *cursor.orientation, *((cursor.increment or ())))


def guard_pose(arithmetic, pose):
    if (type(pose) is not _CenteredPose or type(pose.position) is not tuple or len(pose.position) != 3
            or type(pose.orientation) is not tuple or len(pose.orientation) != 4
            or any(not _native(value) for value in pose.position)
            or any(not _native(value, magnitude=2) for value in pose.orientation)
            or not _native(pose.position_radius, magnitude=1)
            or not _native(pose.orientation_radius, magnitude=1)
            or _integers((pose.position, pose.orientation, pose.position_radius,
                          pose.orientation_radius, pose.axis)) != pose.seal
            or not 0 <= pose.position_radius <= F(1, 1 << 94)
            or not 0 <= pose.orientation_radius <= F(1, 1 << 104)):
        raise ReferenceError("identity", "Independent centered pose changed")
    arithmetic.guard(*pose.position, *pose.orientation, pose.position_radius, pose.orientation_radius)


class _Guard:
    """Freeze operands and recheck their live owners after every callback."""
    def __init__(self, reference, plan, batch, product_session=None):
        self.reference, self.plan, self.batch = reference, plan, batch
        self.a, self.p = reference.a, reference.p
        self.work, self.check = self.a.work, self.a.check
        self.external = getattr(self.work, "external_check", None)
        self.work_kind = type(self.work)
        self.leaves, self.records, self.cells = [], [], []
        self.invalidated = False
        self.oracle_guard = None
        self.product_session = product_session
        self.coefficient_slot = None
        if not self.current():
            raise _ChangedDomain()

    def freeze(self, value):
        if type(value) is not F:
            raise ReferenceError("identity", "Independent centered operand is not native")
        numerator, denominator = value.numerator, value.denominator
        if (type(numerator) is not int or type(denominator) is not int or denominator <= 0):
            raise ReferenceError("identity", "Independent centered rational changed")
        self.a.guard(value)
        self.leaves.append((value, numerator, denominator))
        return F(numerator, denominator)

    def vector(self, values):
        if type(values) is not tuple:
            raise ReferenceError("identity", "Independent centered vector changed")
        return tuple(self.freeze(value) for value in values)

    def watch(self, value, names):
        saved = tuple(getattr(value, name) for name in names)
        self.records.append((value, type(value), names, saved))

    def intervals(self, cells):
        result = []
        for cell in cells:
            if type(cell) is not Interval:
                raise ReferenceError("identity", "Independent centered seed cell changed")
            self.cells.append((cell, cell.lo, cell.hi))
            result.append((self.freeze(cell.lo), self.freeze(cell.hi)))
        return tuple(result)

    def pose(self, pose):
        guard_pose(self.a, pose)
        fields = (pose.position, pose.orientation, pose.position_radius,
                  pose.orientation_radius, pose.axis)
        if (_integers(fields) != pose.seal or len(pose.position) != 3
                or len(pose.orientation) != 4
                or any(not _native(value) for value in pose.position)
                or any(not _native(value, magnitude=2) for value in pose.orientation)
                or not _native(pose.position_radius, magnitude=1)
                or not _native(pose.orientation_radius, magnitude=1)
                or pose.position_radius < 0 or not 0 <= pose.orientation_radius <= F(1, 1 << 104)):
            raise ReferenceError("identity", "Independent centered pose changed")
        self.watch(pose, ("position", "orientation", "position_radius", "orientation_radius", "axis", "seal"))
        return _CenteredPose(self.vector(pose.position), self.vector(pose.orientation),
                             self.freeze(pose.position_radius),
                             self.freeze(pose.orientation_radius), pose.axis)

    def current(self):
        self.plan.admit_owners(self.reference)
        self.batch.admit_owners()
        if (type(self.a) is not _Arithmetic or type(self.p) is not _PoseArithmetic
                or self.reference.a is not self.a or self.reference.p is not self.p
                or self.p.a is not self.a or self.a.work is not self.work
                or self.a.check is not self.check or type(self.work) is not self.work_kind
                or getattr(self.work, "external_check", None) is not self.external
                or self.a._recording_after_tick is not self.oracle_guard):
            raise ReferenceError("identity", "Independent centered arithmetic owner changed")
        for value, numerator, denominator in self.leaves:
            if (type(value) is not F or type(value.numerator) is not int
                    or type(value.denominator) is not int
                    or (value.numerator, value.denominator) != (numerator, denominator)):
                raise ReferenceError("identity", "Independent centered operand changed")
        for value, kind, names, fields in self.records:
            if (type(value) is not kind
                    or any(getattr(value, name) is not saved for name, saved in zip(names, fields))):
                raise ReferenceError("identity", "Independent centered record changed")
        for cell, low, high in self.cells:
            if type(cell) is not Interval or cell.lo is not low or cell.hi is not high:
                raise ReferenceError("identity", "Independent centered seed cell changed")
        if self.product_session is not None:
            session = self.product_session
            state = _PRODUCT_SESSION_STATE(session)
            state["guard"] = self
            if state.get("installed") and state.get("valid"):
                if (_product_native is _PRODUCT_NATIVE and _product_native.__code__ is _PRODUCT_NATIVE_CODE
                        and _product_native(self)):
                    _PRODUCT_CURRENT(session, self)
                else:
                    state["valid"] = False
            if state.get("error") is not None:
                raise ReferenceError("identity", state["error"])
        self.invalidated = self.invalidated or not (
            type(self.a.bits) is int and self.a.bits == 128
            and type(self.a.scale) is int and self.a.scale == 1 << 128
            and self.a.operand_limit == MAX_OPERAND_BITS)
        return not self.invalidated

    def checked(self, operation, *args, **kwargs):
        result = operation(*args, **kwargs)
        if not self.current():
            raise _ChangedDomain()
        return result

    def original(self, operation, *args):
        if not self.current():
            raise _ChangedDomain()

        def observed():
            # Arithmetic tick captured this observer before the unchanged
            # caller callback. A replacement cannot hide its own mutation.
            self.current()
            if (type(self.a.bits) is not int or self.a.bits != 128
                    or type(self.a.scale) is not int or self.a.scale != 1 << 128):
                raise _ChangedDomain()
            # A narrowed cap is latched by current(), but the original
            # oracle must still execute its prospective operand checks.
            # Preserve an actual inherited resource failure instead of
            # skipping it through an early optional replay.

        self.oracle_guard = observed
        self.a._recording_after_tick = observed
        try:
            try:
                result = operation(*args)
            except ReferenceError as error:
                raise _OriginalFailure(error) from error
        finally:
            if self.a._recording_after_tick is observed:
                self.a._recording_after_tick = None
            self.oracle_guard = None
        if not self.current():
            raise _ChangedDomain()
        return result

    def exact(self, first, last, operation):
        return self.checked(self.a.exact, first, last, operation)

    def neg(self, value):
        self.checked(self.a.tick)
        self.a.guard(value)
        return -value

    def lookup(self, key, *, admission=None):
        # Expose both original callback boundaries to the live receipt, so a
        # cap narrowed by lookup cannot be restored by cache synchronization
        # before this optional proof notices it.
        self.checked(self.a.tick)
        if admission is not None and not admission():
            return None
        self.checked(self.a._sync_cache_operand_limit)
        if admission is not None and not admission():
            return None
        value = self.a.cache.get(key)
        if value is not None:
            del self.a.cache[key]
            self.a.cache[key] = value
        return value

    def remember(self, key, value, *, pending=None, previous=None, admission=None):
        self.checked(self.a.tick)
        if admission is not None and not admission():
            return
        self.checked(self.a._sync_cache_operand_limit)
        if admission is not None and not admission():
            return
        if pending is not None:
            from .reach_reference_plan import MAX_CURSORS
            if len(pending.values) >= MAX_CURSORS:
                raise ReferenceError("resource", "Independent pending cursor plan exceeds its bounded domain")
            pending.values.append((key, value, previous))
            return
        if key in self.a.cache:
            del self.a.cache[key]
        elif len(self.a.cache) >= MAX_CACHE:
            del self.a.cache[next(iter(self.a.cache))]
        self.a.cache[key] = value

    def floor(self, value):
        self.checked(self.a.tick)
        self.a._grid_domain(value, value)
        return F((value.numerator << 128) // value.denominator, 1 << 128)


def prepare(plan, reference, batch):
    """Compile only source operands and bounded radius counts, never poses."""
    if plan.centered is not None:
        return plan
    admit_source(plan, reference, fresh=False)
    a = reference.a
    nodes, depths = [], {"world": 0}
    orientations, projections = {"world": (None, None)}, {}
    groups, group = [], 0
    identities, extents = {"world": True}, {"world": F(0)}
    product_candidates, product_pair = {}, None
    for node in plan.nodes:
        guard = _Guard(reference, plan, batch)
        identity_offset = 0
        if node.kind == "root":
            local, body = node.local, node.body
            if (local.vector is not None or type(local.position) is not tuple
                    or len(local.position) != 3 or body.moving or body.witness[4] is not None
                    or any(type(cell) is not Interval or type(cell.lo) is not F
                           or type(cell.hi) is not F or cell.lo != cell.hi
                           for cell in local.position)
                    or type(body.witness[3]) is not tuple or len(body.witness[3]) != 4
                    or any(type(cell) is not Interval or type(cell.lo) is not F
                           or type(cell.hi) is not F or cell.lo != cell.hi
                           or cell.lo != expected
                           for cell, expected in zip(body.witness[3], (1, 0, 0, 0)))):
                return replace(plan, centered=False)
            vector = tuple(pair[0] for pair in guard.intervals(local.position))
            guard.intervals(body.witness[3])
            if any(not _native(value, magnitude=64) for value in vector):
                return replace(plan, centered=False)
            guard.checked(a.tick)
            total = F(0)
            for value in vector:
                if value:
                    total = abs(value) if not total else guard.exact(total, abs(value), "add")
            if total > 64:
                return replace(plan, centered=False)
            depth = 0
            identity, extent = True, total
            orientation_source, orientation_axis = None, None
        else:
            local = node.local
            if (node.kind not in {"site", "follow", "hinge", "fixed", "grip"}
                    or type(local.position) is not tuple or len(local.position) != 3
                    or type(local.rotation) is not tuple or len(local.rotation) != 4
                    or any(type(value) not in (int, float, F)
                           or type(value) is float and not math.isfinite(value)
                           for value in (*local.position, *local.rotation))
                    or local.rotation != (1, 0, 0, 0)):
                return replace(plan, centered=False)
            supplied = tuple(guard.freeze(value) if type(value) is F else value for value in local.position)
            guard.checked(a.tick)
            vector = tuple(guard.checked(a.point, value).lo for value in supplied)
            if any(not _native(value, magnitude=64) for value in vector):
                return replace(plan, centered=False)
            total = F(0)
            for value in vector:
                if value:
                    total = abs(value) if not total else guard.exact(total, abs(value), "add")
            # Only the admitted identity source lineage may transport a
            # larger exact translation. A zero rate or a sampled identity
            # center does not establish a zero-width identity orientation.
            identity = identities[node.parent] and (
                node.kind != "hinge" or node.body.identity_relative is True)
            orientation_source, orientation_axis = orientations[node.parent]
            if node.kind == "hinge" and not node.body.identity_relative:
                orientation_source, orientation_axis = node.path, node.body.axis
            identity_offset = int(total > 1)
            if total > 64 or identity_offset and not identity:
                return replace(plan, centered=False)
            if node.kind not in {"site", "follow"}:
                vector = tuple(guard.neg(value) if value else value for value in vector)
            depth = depths[node.parent] + int(bool(total))
            parent_extent = extents[node.parent]
            extent = (parent_extent if not total else total if not parent_extent else
                      guard.exact(parent_extent, total, "add"))
            # Retain the previous global source-position premise: root L1
            # at most 64 plus at most 128 unit attachment offsets. Exact
            # larger translations consume this same total extent allowance.
            if extent > 192:
                return replace(plan, centered=False)
        a.guard(*vector)
        if not reference._recording_body_domain():
            return plan
        radius = guard.exact(F(depth), F(1, 1 << 102), "mul") if depth else F(0)
        # A new orientation seed may populate the shared LRU. Require the
        # repeated projections to share a segment without another seed in
        # between, rather than charging a memo miss for distant one-off uses.
        if node.kind == "hinge" and not node.body.identity_relative:
            group += 1
        coefficient_source = None
        if (orientation_source is not None and type(orientation_axis) is int
                and orientation_axis in (0, 1, 2)
                and any(value for index, value in enumerate(vector) if index != orientation_axis)):
            coefficient_source = orientation_source
            key = coefficient_source, group
            projections[key] = projections.get(key, 0) + 1
            # Source metadata only, inside the existing bounded visit. A
            # single pair in the whole plan avoids overlapping live receipts.
            if (product_pair is None and node.kind in {"site", "follow", "fixed", "grip"}
                    and node.stationary is False):
                order = ((orientation_axis + 1) % 3, (orientation_axis + 2) % 3,
                         orientation_axis)
                x, y, z = (vector[index] for index in order)
                xn, xd, yn, yd = x.numerator, x.denominator, y.numerator, y.denominator
                if xn not in (0, xd, -xd) and yn:
                    candidate = (node.parent, coefficient_source, group, orientation_axis,
                                 xn, xd, z.numerator, z.denominator, abs(yn), yd)
                    previous = product_candidates.get(candidate)
                    if previous is not None and previous[1] == -yn:
                        product_pair = (group, orientation_axis, previous[0], len(nodes))
                    elif previous is None:
                        product_candidates[candidate] = (len(nodes), yn)
        nodes.append(_CenteredNode(vector, radius, identity_offset, coefficient_source))
        groups.append(group)
        depths[node.path] = depth
        identities[node.path], extents[node.path] = identity, extent
        orientations[node.path] = orientation_source, orientation_axis
    plan.admit_owners(reference)
    nodes = [replace(recipe,
             coefficient_source=None if recipe.coefficient_source is not None
                 and projections[recipe.coefficient_source, group] < 2 else recipe.coefficient_source,
             product_pair=product_pair if product_pair is not None and index in product_pair[2:] else None,
             product_owner=(node.path, node.kind, node.parent)
                 if product_pair is not None and index in product_pair[2:] else None)
             for index, (node, recipe, group) in enumerate(zip(plan.nodes, nodes, groups))]
    return replace(plan, centered=tuple(nodes)) if reference._recording_body_domain() else plan


def admit_source(plan, reference, *, fresh=True):
    """Reject source/receipt alias mutation before center use and final pass."""
    for receipt in plan.receipts:
        current = receipt.values
        if fresh:
            try:
                current = receipt.read()
            except (KeyError, AttributeError, IndexError) as error:
                raise ReferenceError("identity", "Independent centered source changed") from error
        if (type(receipt.values) is not tuple or len(receipt.values) > 16
                or reference._recording_source_witness(*receipt.values) is None
                or type(current) is not tuple or len(current) > 16
                or reference._recording_source_witness(*current) is None
                or receipt.signature is None
                or _recording_source_signature(receipt.values) != receipt.signature
                or _recording_source_signature(current) != receipt.signature):
            raise ReferenceError("identity", "Independent centered source changed")


def _seed(cells, axis, guard):
    """Convert independent cells to a point with an honest Euclidean bound."""
    if (type(cells) is not tuple or len(cells) != 4
            or any(type(cell) is not Interval or type(cell.lo) is not F
                   or type(cell.hi) is not F for cell in cells)):
        raise _ChangedDomain()
    endpoints = guard.intervals(cells)
    if (any(not _native(value, magnitude=2) for pair in endpoints for value in pair)
            or any(low > high for low, high in endpoints)
            or any(pair != (0, 0) for index, pair in enumerate(endpoints)
                   if index not in (0, axis + 1))):
        raise _ChangedDomain()
    width = F(0)
    for low, high in endpoints:
        if low != high:
            term = guard.exact(high, low, "sub")
            width = term if not width else guard.exact(width, term, "add")
    if width > F(1, 1 << 112):
        raise _ChangedDomain()
    return tuple(pair[0] for pair in endpoints), width


def _increment(cells, guard):
    zero = Interval(F(0), F(0))
    rotation, _ = _seed((cells[1], zero, zero, cells[0]), 2, guard)
    return rotation[3], rotation[0]


def _orientation(node, time, context, reference, guard, pending):
    a, body = reference.a, node.body
    axis = body.axis
    if type(axis) is not int or axis not in (0, 1, 2):
        raise _ChangedDomain()
    rate, clock = guard.freeze(body.rate), guard.freeze(time)
    key = reference.p._key("recording_center_body_orientation", (context, node.path))
    previous = guard.lookup(key)
    advance = False
    if previous is not None:
        guard_cursor(a, previous)
        guard.watch(previous, ("witness", "axis", "rate", "clock", "orientation", "radius",
                               "increment", "steps", "seal"))
        old_clock, old_rate = guard.freeze(previous.clock), guard.freeze(previous.rate)
        old_rotation = guard.vector(previous.orientation)
        old_radius = guard.freeze(previous.radius)
        old_increment = None if previous.increment is None else guard.vector(previous.increment)
        advance = (previous.witness == body.witness and previous.axis == axis
                   and old_rate == rate and old_clock < clock and previous.steps < 64)
    increment, steps = None, 0
    if advance:
        if rate:
            elapsed = guard.exact(clock, old_clock, "sub")
            increment = old_increment
            cells = reference.p._recording_repeated_increment(increment, rate, elapsed)
            if cells is None:
                product = guard.exact(rate, elapsed, "mul")
                delta = guard.exact(product, 2, "div")
                if abs(delta) > F(1, 4):
                    advance = False
                else:
                    delta_cell = guard.checked(a.grid, delta, delta)
                    sine, cosine = guard.original(a.sincos, delta_cell)
                    increment = (rate, elapsed, product, delta, delta_cell.lo, delta_cell.hi,
                                 sine.lo, sine.hi, cosine.lo, cosine.hi)
                    small_sine, small_cosine = _increment((sine, cosine), guard)
            else:
                # These exact endpoint operands already passed the width
                # proof when their complete increment entered this cursor.
                small_sine, small_cosine = guard.freeze(cells[0].lo), guard.freeze(cells[1].lo)
            if advance:
                sine, cosine = old_rotation[axis + 1], old_rotation[0]
                first = guard.exact(guard.exact(sine, small_cosine, "mul"),
                                    guard.exact(cosine, small_sine, "mul"), "add")
                last = guard.exact(guard.exact(cosine, small_cosine, "mul"),
                                   guard.exact(sine, small_sine, "mul"), "sub")
                result = [F(0)] * 4
                result[axis + 1], result[0] = guard.floor(first), guard.floor(last)
                result, radius = tuple(result), F(1, 1 << 104)
        else:
            result, radius = old_rotation, old_radius
        if advance:
            steps = previous.steps + 1
    if not advance:
        result, radius = _seed(guard.original(body.direct, clock), axis, guard)
        increment, steps = None, 0
    a.guard(*result, radius)
    value = _CenteredCursor(body.witness, axis, rate, clock, result, radius, increment, steps, ())
    value = replace(value, seal=_cursor_seal(value))
    guard_cursor(a, value)
    guard.remember(key, value, pending=pending, previous=previous)
    return result, radius, axis


_COEFFICIENT_METHODS = tuple((name, getattr(_Arithmetic, name)) for name in (
    "exact", "guard", "tick", "_sync_cache_operand_limit"))
_COEFFICIENT_GUARD_METHODS = tuple((name, getattr(_Guard, name)) for name in (
    "exact", "checked", "current", "freeze", "vector", "watch", "lookup", "remember"))


def _coefficient_domain(guard):
    a = guard.a
    for owner, kind, methods in ((a, _Arithmetic, _COEFFICIENT_METHODS),
                                 (guard, _Guard, _COEFFICIENT_GUARD_METHODS)):
        if (type(owner) is not kind
                or any(kind.__dict__.get(name) is not original for name, original in methods)):
            return False
        for name, original in methods:
            method = getattr(owner, name)
            if (type(method) is not MethodType or method.__self__ is not owner
                    or method.__func__ is not original):
                return False
    if (type(a.cache) is not dict
            or type(a.bits) is not int or a.bits != 128
            or type(a.scale) is not int or a.scale != 1 << 128
            or a.operand_limit != MAX_OPERAND_BITS):
        return False
    return True


def _direct_coefficients(w, s, guard, *, completed=None):
    # Preserve Python's original outer-method binding before evaluating its
    # inner calls. A callback may replace instance dispatch between them.
    subtract = guard.exact
    square_w = guard.exact(w, w, "mul")
    if completed is not None:
        completed()
    square_s = guard.exact(s, s, "mul")
    if completed is not None:
        completed()
    diagonal = subtract(square_w, square_s, "sub")
    if completed is not None:
        completed()
    double = guard.exact
    product = guard.exact(w, s, "mul")
    if completed is not None:
        completed()
    cross = double(product, 2, "mul")
    if completed is not None:
        completed()
    return diagonal, cross


def _coefficients(w, s, guard, source):
    """Reuse completed exact arithmetic only for a repeated source orientation.

    One existing LRU slot per admitted source replaces its preceding operands;
    no per-clock coefficient table or pending cursor value is retained.
    """
    guard.coefficient_slot = None
    if (source is None or type(source) is not tuple or len(source) != 2
            or type(source[0]) is not object or type(source[1]) is not str
            or not _coefficient_domain(guard)
            or not _native(w, magnitude=2) or not _native(s, magnitude=2)):
        return _direct_coefficients(w, s, guard)
    w, s = guard.freeze(w), guard.freeze(s)
    # The detached copies become the arithmetic operands and, on a miss,
    # the retained receipt leaves. Watch those exact objects too; watching
    # only their source aliases would miss a cold-publication mutation.
    guard.freeze(w)
    guard.freeze(s)
    guard.watch(guard.a, ("cache",))
    key = ("reference_centered_coefficients", guard.a.bits, guard.a.operand_limit, *source)
    previous = guard.lookup(key, admission=lambda: _coefficient_domain(guard))
    # A lookup callback may install custom arithmetic. Its original five
    # operations then execute on this same work object, without cache reuse.
    if not _coefficient_domain(guard):
        return _direct_coefficients(w, s, guard)
    if previous is not None:
        fields = ("scalar", "active", "diagonal", "cross", "seal", "products")
        if (type(previous) is not _CenteredCoefficients
                or not _native(previous.scalar, magnitude=2)
                or not _native(previous.active, magnitude=2)
                or any(type(value) is not F or type(value.numerator) is not int
                       or type(value.denominator) is not int or value.denominator <= 0
                       or abs(value.numerator).bit_length() > 535
                       or value.denominator.bit_length() > 516
                       for value in (previous.diagonal, previous.cross))
                or type(previous.seal) is not tuple or len(previous.seal) != 4
                or any(type(pair) is not tuple or len(pair) != 2
                       or any(type(value) is not int for value in pair)
                       for pair in previous.seal)
                or _integers((previous.scalar, previous.active, previous.diagonal,
                              previous.cross)) != previous.seal):
            raise ReferenceError("identity", "Independent centered coefficients changed")
        if (previous.scalar, previous.active) == (w, s):
            guard.watch(previous, fields)
            guard.freeze(previous.scalar)
            guard.freeze(previous.active)
            guard.coefficient_slot = key, previous
            return guard.vector((previous.diagonal, previous.cross))
    native = True
    def completed():
        nonlocal native
        native = native and _coefficient_domain(guard)
    diagonal, cross = _direct_coefficients(w, s, guard, completed=completed)
    # Keep the departure latched if later original callbacks restore native
    # dispatch. Custom arithmetic still runs at each original position, but
    # its completed values cannot acquire a native memo receipt afterwards.
    if not native or not _coefficient_domain(guard):
        return diagonal, cross
    value = _CenteredCoefficients(w, s, diagonal, cross)
    guard.watch(value, ("scalar", "active", "diagonal", "cross", "seal", "products"))
    result = guard.vector((diagonal, cross))
    # These are completed pure arithmetic values, not deferred source poses.
    # Like the existing arithmetic memoization, they do not enter the source
    # cursor ledger or the separate pending-publication inventory.
    guard.remember(key, value, admission=lambda: _coefficient_domain(guard))
    guard.coefficient_slot = key, value
    return result


def _product_fields(value, numerator_bits=673, denominator_bits=645):
    if type(value) is not F:
        return None
    numerator, denominator = value.numerator, value.denominator
    if (type(numerator) is not int or type(denominator) is not int or denominator <= 0
            or abs(numerator).bit_length() > numerator_bits
            or denominator.bit_length() > denominator_bits):
        return None
    return numerator, denominator


def _product_pair_shape(pair, length=128):
    return (type(pair) is tuple and len(pair) == 4
            and all(type(value) is int for value in pair)
            and 0 <= pair[0] <= 128 and pair[1] in (0, 1, 2)
            and 0 <= pair[2] < pair[3] < length)


def _product_mapping(owner, fields, *, maximum=32):
    """Read only bounded stored source fields, never caller descriptors."""
    for kind in type.__getattribute__(type(owner), "__mro__"):
        namespace = type.__getattribute__(kind, "__dict__")
        dictionary = namespace.get("__dict__", _PRODUCT_ABSENT)
        if dictionary is not _PRODUCT_ABSENT and type(dictionary) not in (GetSetDescriptorType, MemberDescriptorType):
            return None
        for name in fields:
            member = namespace.get(name, _PRODUCT_ABSENT)
            if member is not _PRODUCT_ABSENT and any("__get__" in type.__getattribute__(base, "__dict__")
                    for base in type.__getattribute__(type(member), "__mro__")):
                return None
    own = object.__getattribute__(owner, "__dict__")
    if type(own) is not dict or len(own) > maximum or any(type(name) is not str for name in own):
        return None
    return own


def _product_plan_identity(plan):
    own = _product_mapping(plan, _PRODUCT_PLAN_FIELDS)
    if own is None or type(own.get("cache_identity")) is not object:
        return None
    fields = tuple(own.get(name, _PRODUCT_ABSENT) for name in _PRODUCT_PLAN_FIELDS)
    context = fields[1]
    if context is _PRODUCT_ABSENT:
        phase = _PRODUCT_ABSENT
    elif type(context) is tuple and len(context) == 4 and all(
            type(value) is object or value is None or type(value) is int and abs(value).bit_length() <= 1024
            or type(value) is str and len(value) <= 128 for value in context):
        phase = tuple((type(value), value) for value in context)
    else:
        return None
    return fields, phase


def _product_source(plan, pair):
    """Bind both sealed prepared recipes to the actual source-node roles."""
    from .reach_reference_plan import _Node
    source = _product_mapping(plan, ("nodes", "centered", "cache_identity"))
    if source is None:
        return None
    nodes, recipes = source.get("nodes"), source.get("centered")
    if (type(nodes) is not tuple or not 1 <= len(nodes) <= 128
            or type(recipes) is not tuple or len(recipes) != len(nodes)
            or not _product_pair_shape(pair, len(nodes))):
        return None
    saved, vectors = [], []
    for index in pair[2:]:
        node, recipe = nodes[index], recipes[index]
        if type(node) is not _Node or type(recipe) is not _CenteredNode:
            return None
        actual = _product_mapping(node, ("path", "kind", "parent", "stationary"))
        prepared = _product_mapping(recipe, ("vector", "position_radius", "identity_offset",
            "coefficient_source", "product_pair", "product_owner", "seal"))
        if actual is None or prepared is None:
            return None
        owner = tuple(actual.get(name) for name in ("path", "kind", "parent"))
        vector = prepared.get("vector")
        if (any(type(value) is not str for value in owner)
                or owner[1] not in {"site", "follow", "fixed", "grip"}
                or actual.get("stationary") is not False
                or prepared.get("product_owner") != owner
                or prepared.get("product_pair") != pair
                or type(prepared.get("coefficient_source")) is not str
                or type(vector) is not tuple or len(vector) != 3
                or _integers(tuple(prepared.get(name) for name in ("vector", "position_radius",
                    "identity_offset", "coefficient_source", "product_pair", "product_owner"))) != prepared.get("seal")):
            return None
        vector = tuple(_product_fields(value, 138, 129) for value in vector)
        if any(value is None for value in vector):
            return None
        saved.append((node, recipe, *owner, prepared["coefficient_source"], prepared["seal"]))
        vectors.append(vector)
    axis = pair[1]
    first, second = vectors
    x, y = (axis + 1) % 3, (axis + 2) % 3
    if saved[0][4] != saved[1][4] or saved[0][5] != saved[1][5]:
        return None
    if (first[x] != second[x] or first[axis] != second[axis]
            or first[x][0] in (0, first[x][1], -first[x][1]) or not first[y][0]
            or (first[y][0], first[y][1]) != (-second[y][0], second[y][1])):
        return None
    return tuple(saved)


def _product_native(guard):
    """Inspect fixed native dispatch without binding foreign descriptors."""
    if type(guard) is not _Guard:
        return False
    for kind, fields in _PRODUCT_CLASS_FIELDS:
        namespace = type.__getattribute__(kind, "__dict__")
        if any(namespace.get(name, _PRODUCT_ABSENT) is not value for name, value in fields):
            return False
    for function, state in _PRODUCT_FUNCTIONS:
        code, defaults, kwdefaults, kwfields, closure, globals_ = state
        if (function.__code__ is not code or function.__defaults__ is not defaults
                or function.__kwdefaults__ is not kwdefaults
                or len(function.__kwdefaults__ or {}) != len(kwfields)
                or any(type(name) is not str or name != saved_name or value is not saved
                       for (name, value), (saved_name, saved) in
                       zip((function.__kwdefaults__ or {}).items(), kwfields))
                or len(function.__closure__ or ()) != len(closure)
                or any(cell.cell_contents is not value for cell, value in
                       zip(function.__closure__ or (), closure))
                or any(function.__globals__.get(name, _PRODUCT_ABSENT) is not value
                       or function.__builtins__.get(name, _PRODUCT_ABSENT) is not builtin
                       for name, value, builtin in globals_)):
            return False
    if any(type(module) is not ModuleType or ModuleType.__getattribute__(module, "__dict__").get(
            name, _PRODUCT_ABSENT) is not value for module, name, value in _PRODUCT_GLOBALS):
        return False
    if sys.gettrace() is not None or sys.getprofile() is not None:
        return False
    own = object.__getattribute__(guard, "__dict__")
    if any(name in own for name in _PRODUCT_GUARD_METHODS):
        return False
    session = own.get("product_session")
    if session is not None:
        if type(session) is not _ProductSession:
            return False
        session_state = _PRODUCT_SESSION_STATE(session)
        if any(name in session_state for name in _PRODUCT_SESSION_METHODS):
            return False
    a = own.get("a")
    if type(a) is not _Arithmetic:
        return False
    state = object.__getattribute__(a, "__dict__")
    if (any(name in state for name in _PRODUCT_ARITHMETIC_METHODS)
            or type(state.get("bits")) is not int or state["bits"] != 128
            or type(state.get("scale")) is not int or state["scale"] != 1 << 128
            or type(state.get("_cache_operand_limit")) is not int
            or state["_cache_operand_limit"] != MAX_OPERAND_BITS
            or type(state.get("cache")) is not dict):
        return False
    work = state.get("work")
    if work is not own.get("work") or state.get("check") is not own.get("check"):
        return False
    # The live cap must be an ordinary stored integer, not a descriptor that
    # could execute caller code during optional admission.
    if work is None:
        return False
    for kind in type.__getattribute__(type(work), "__mro__"):
        namespace = type.__getattribute__(kind, "__dict__")
        if "max_operand_bits" in namespace or "__getattr__" in namespace:
            return False
        if "__getattribute__" in namespace and namespace["__getattribute__"] is not object.__getattribute__:
            return False
    work_state = object.__getattribute__(work, "__dict__")
    return (type(work_state) is dict and type(work_state.get("max_operand_bits")) is int
            and work_state["max_operand_bits"] == MAX_OPERAND_BITS)


class _ProductSession:
    """One evaluation's bounded latch; never a source of evicted numbers."""
    def __init__(self, reference, plan, time, batch):
        self.reference, self.plan, self.time, self.batch = reference, plan, time, batch
        self.a = reference.a
        self.token = object()
        self.observer = self._observe
        self.guard = None
        self.pair = self.source = self.clock = self.slot = None
        self.plan_fields = self.phase_fields = None
        self.cache = self.check = self.work = None
        self.arithmetic_state = None
        self.watched = ()
        self.products = (None, None)
        self.payload = self.payload_fields = None
        self.record = self.record_fields = None
        self.recipient_seen = False
        self.valid = self.installed = False
        self.closed = False
        self.error = None

    def _observe(self):
        # tick invokes this only after the original check succeeds. Never
        # preempt an original prospective guard or replace its exception.
        try:
            if _PRODUCT_SESSION_STATE(self).get("valid") is not True:
                return
            if (_product_native is not _PRODUCT_NATIVE
                    or _product_native.__code__ is not _PRODUCT_NATIVE_CODE
                    or not _product_native(self.guard)):
                self.valid = False
                return
            current = object.__getattribute__(self.a, "__dict__")
            if (current is not self.arithmetic_state
                    or current.get("_recording_product_after_tick") is not self.observer):
                self.valid = False
                self.error = "Independent centered product observer owner changed"
            if not self.valid:
                return
            reference = _product_mapping(self.reference, ("a",), maximum=64)
            if reference is None:
                self.valid = False
                return
            if (current.get("cache") is not self.cache or current.get("check") is not self.check
                    or current.get("work") is not self.work or reference.get("a") is not self.a):
                self.valid = False
                self.error = "Independent centered product arithmetic owner changed"
                return
            plan_identity = _product_plan_identity(self.plan)
            if (plan_identity is None or any(now is not saved for now, saved in
                    zip(plan_identity[0], self.plan_fields)) or plan_identity[1] != self.phase_fields):
                self.valid = False
                self.error = "Independent centered product plan or phase changed"
                return
            if _product_fields(self.time, 1024, 1024) != self.clock:
                self.valid = False
                self.error = "Independent centered product clock changed"
            elif not self._same_source(_product_source(self.plan, self.pair)):
                self.valid = False
                self.error = "Independent centered product source changed"
            elif any(_product_fields(value) != fields for value, fields in self.watched):
                self.valid = False
                self.error = "Independent centered product operand changed"
            elif self.record is not None and (
                    any(getattr(self.record, name) is not value for name, value in self.record_fields)
                    or _integers((self.record.scalar, self.record.active, self.record.diagonal,
                                  self.record.cross)) != self.record.seal):
                self.valid = False
                self.error = "Independent centered product coefficient record changed"
            elif self.payload is not None and not self._same_payload(self._payload_snapshot(self.payload)):
                self.valid = False
                self.error = "Independent centered product receipt changed"
        except Exception:
            # Foreign or malformed metadata cannot authorize a skip. Ordinary
            # operation errors still propagate through their original caller.
            self.valid = False
            self.error = "Independent centered product admission changed"

    def _same_source(self, current):
        return (current is not None and all(now[0] is saved[0] and now[1] is saved[1]
                and now[2:] == saved[2:] for now, saved in zip(current, self.source)))

    def _same_payload(self, current):
        return (current is not None and self.payload_fields is not None
                and all(now is saved for now, saved in zip(current[:7], self.payload_fields[:7]))
                and current[7:] == self.payload_fields[7:])

    def current(self, guard):
        self.guard = guard
        if self.installed:
            _PRODUCT_OBSERVE(self)
            if self.error is not None:
                raise ReferenceError("identity", self.error)

    def enter(self, guard, pair, index, source):
        guard.product_session = self
        self.guard = guard
        if self.closed:
            return False
        if not self.installed:
            if (not _product_pair_shape(pair) or index != pair[2]
                    or _product_native is not _PRODUCT_NATIVE
                    or _product_native.__code__ is not _PRODUCT_NATIVE_CODE
                    or not _product_native(guard)
                    or self.a._recording_product_after_tick is not None):
                return False
            clock = _product_fields(self.time, 1024, 1024)
            saved = _product_source(self.plan, pair)
            identity = _product_plan_identity(self.plan)
            reference = _product_mapping(self.reference, ("a",), maximum=64)
            if (clock is None or saved is None or identity is None or reference is None
                    or reference.get("a") is not self.a or type(source) is not tuple or len(source) != 2
                    or source[0] is not identity[0][0] or source[1] != saved[0][5]):
                return False
            self.pair, self.source, self.clock = pair, saved, clock
            self.plan_fields, self.phase_fields = identity
            self.cache, self.check, self.work = self.a.cache, self.a.check, self.a.work
            self.arithmetic_state = object.__getattribute__(self.a, "__dict__")
            self.valid = self.installed = True
            self.a._recording_product_after_tick = self.observer
        _PRODUCT_CURRENT(self, guard)
        return (self.valid and pair == self.pair and index in pair[2:]
                and type(source) is tuple and len(source) == 2
                and source[0] is self.plan_fields[0] and source[1] == self.source[0][5])

    def bind(self, guard, index, diagonal, cross, operand):
        _PRODUCT_CURRENT(self, guard)
        if not self.valid or guard.coefficient_slot is None:
            return None
        fields = tuple(_product_fields(value) for value in (diagonal, cross, operand))
        if (any(value is None for value in fields) or not fields[0][0] or not fields[1][0]
                or fields[2][0] in (0, fields[2][1], -fields[2][1])):
            return None
        if index == self.pair[2]:
            if self.slot is not None:
                self.valid = False
                return None
            self.slot = guard.coefficient_slot
            self.watched = tuple(zip((diagonal, cross, operand), fields))
            return None
        if self.recipient_seen:
            self.valid = False
            return None
        self.recipient_seen = True
        if self.slot is None or fields[:2] != tuple(fields for _, fields in self.watched[:2]):
            return None
        record = guard.coefficient_slot[1]
        payload = record.products
        if payload is None:
            return None
        snapshot = _PRODUCT_PAYLOAD(self, payload)
        if snapshot is None:
            raise ReferenceError("identity", "Independent centered product receipt changed")
        if (payload.token is not self.token or payload.clock != self.clock
                or payload.pair != self.pair or _product_fields(payload.operand) != fields[2]):
            return None
        if payload is not self.payload:
            return None
        if not _PRODUCT_SAME_PAYLOAD(self, snapshot):
            raise ReferenceError("identity", "Independent centered product receipt changed")
        guard.watch(record, ("scalar", "active", "diagonal", "cross", "seal", "products"))
        guard.watch(payload, ("token", "clock", "pair", "operand", "first", "last", "seal"))
        values = guard.vector((payload.first, payload.last))
        for value in values:
            guard.freeze(value)
        return values

    def _payload_snapshot(self, payload):
        if (type(payload) is not _CenteredProducts or type(payload.token) is not object
                or type(payload.clock) is not tuple or len(payload.clock) != 2
                or any(type(value) is not int or abs(value).bit_length() > 1024 for value in payload.clock)
                or payload.clock[1] <= 0 or not _product_pair_shape(payload.pair)
                or _product_fields(payload.operand, 138, 129) is None
                or _product_fields(payload.first) is None or _product_fields(payload.last) is None
                or _integers((payload.clock, payload.pair, payload.operand,
                              payload.first, payload.last)) != payload.seal):
            return None
        return (payload.token, payload.clock, payload.pair, payload.operand, payload.first,
                payload.last, payload.seal, _product_fields(payload.operand),
                _product_fields(payload.first), _product_fields(payload.last))

    def capture(self, guard, slot, value):
        _PRODUCT_CURRENT(self, guard)
        if self.valid and _product_fields(value) is not None:
            if self.products[slot] is not None:
                self.valid = False
                return
            self.products = (value, self.products[1]) if slot == 0 else (self.products[0], value)
            self.watched += ((value, _product_fields(value)),)

    def reuse(self, guard, value):
        _PRODUCT_CURRENT(self, guard)
        return self.valid

    def publish(self, guard, operand):
        _PRODUCT_CURRENT(self, guard)
        if not self.valid or self.slot is None or any(value is None for value in self.products):
            return
        key, previous = self.slot
        leaves = guard.vector((operand, *self.products))
        payload = _CenteredProducts(self.token, self.clock, self.pair, *leaves)
        self.payload, self.payload_fields = payload, _PRODUCT_PAYLOAD(self, payload)
        expanded = _CenteredCoefficients(previous.scalar, previous.active, previous.diagonal,
                                         previous.cross, products=payload)
        fields = ("scalar", "active", "diagonal", "cross", "seal", "products")
        self.record, self.record_fields = expanded, tuple((name, getattr(expanded, name)) for name in fields)
        guard.watch(expanded, fields)
        guard.watch(payload, ("token", "clock", "pair", "operand", "first", "last", "seal"))
        # The sole additional operation. A callback may replace or evict the
        # slot; never resurrect it or overwrite a nested writer afterwards.
        guard.checked(self.a.tick)
        if not self.valid:
            return
        guard.checked(self.a._sync_cache_operand_limit)
        if self.valid and self.a.cache.get(key) is previous:
            self.a.cache[key] = expanded

    def close(self, _read=None):
        # Use the admitted dictionary directly: a callback-installed property
        # must not run during cleanup or replace an in-flight original error.
        state = (_PRODUCT_SESSION_STATE if _read is None else _read)(self)
        if state["installed"] and state["arithmetic_state"].get("_recording_product_after_tick") is state["observer"]:
            state["arithmetic_state"]["_recording_product_after_tick"] = None
        state["valid"] = state["installed"] = False
        state["closed"] = True


def _offset(parent, vector, guard, *, identity_only=False, coefficient_source=None,
            product_session=None, product_pair=None, product_index=None):
    """Project the Hamilton center rotation onto the true rotating plane."""
    if identity_only and (parent.orientation != (1, 0, 0, 0) or parent.orientation_radius):
        raise _ChangedDomain()
    if not any(vector):
        return vector, False
    q, radius, axis = parent.orientation, parent.orientation_radius, parent.axis
    if not radius and q == (1, 0, 0, 0):
        return vector, False
    if type(axis) is not int or axis not in (0, 1, 2):
        raise _ChangedDomain()
    order = ((axis + 1) % 3, (axis + 2) % 3, axis)
    x, y, z = (vector[index] for index in order)
    if not x and not y:
        return vector, False
    w, s = q[0], q[axis + 1]
    selected = (product_session is not None and _product_pair_shape(product_pair)
                and axis == product_pair[1]
                and _product_native is _PRODUCT_NATIVE and _product_native.__code__ is _PRODUCT_NATIVE_CODE
                and _product_native(guard)
                and _PRODUCT_ENTER(product_session, guard, product_pair, product_index, coefficient_source))
    diagonal, cross = _coefficients(w, s, guard, coefficient_source)
    reused = (_PRODUCT_BIND(product_session, guard, product_index, diagonal, cross, x)
              if selected and _product_native is _PRODUCT_NATIVE
              and _product_native.__code__ is _PRODUCT_NATIVE_CODE and _product_native(guard) else None)
    def product(first, last, slot=None):
        if (reused is not None and slot is not None and _product_native is _PRODUCT_NATIVE
                and _product_native.__code__ is _PRODUCT_NATIVE_CODE and _product_native(guard)
                and _PRODUCT_REUSE(product_session, guard, reused[slot])):
            return reused[slot]
        if not first or not last:
            return F(0)
        if last == 1:
            return first
        if last == -1:
            return guard.neg(first)
        value = guard.exact(first, last, "mul")
        if (selected and slot is not None and product_index == product_pair[2]
                and _product_native is _PRODUCT_NATIVE and _product_native.__code__ is _PRODUCT_NATIVE_CODE
                and _product_native(guard)):
            _PRODUCT_CAPTURE(product_session, guard, slot, value)
        return value
    def combined(first, last, subtract=False):
        return ((guard.neg(last) if subtract and last else last) if not first else first if not last else
                guard.exact(first, last, "sub" if subtract else "add"))
    first = guard.floor(combined(product(diagonal, x, 0), product(cross, y), True))
    last = guard.floor(combined(product(cross, x, 1), product(diagonal, y)))
    if (selected and product_index == product_pair[2] and _product_native is _PRODUCT_NATIVE
            and _product_native.__code__ is _PRODUCT_NATIVE_CODE and _product_native(guard)):
        _PRODUCT_PUBLISH(product_session, guard, x)
    if (product_session is not None and _product_pair_shape(product_pair)
            and product_index == product_pair[3]):
        _PRODUCT_CLOSE(product_session)
    values = [None] * 3
    for index, value in zip(order, (first, last, z)):
        values[index] = value
    return tuple(values), True


def evaluate(plan, reference, time, batch):
    """Return private fresh centers only inside the complete source batch."""
    from .reach_reference_plan import _PendingCursors

    if type(plan.centered) is not tuple or batch is None:
        return None
    a = reference.a
    pending = _PendingCursors(a)
    products = _ProductSession(reference, plan, time, batch)
    frames = {"world": _CenteredPose((F(0),) * 3, (F(1), F(0), F(0), F(0)), F(0), F(0), None)}
    try:
        for index, (node, recipe) in enumerate(zip(plan.nodes, plan.centered)):
            guard = _Guard(reference, plan, batch, product_session=products)
            if (type(recipe) is not _CenteredNode or type(recipe.vector) is not tuple
                    or len(recipe.vector) != 3 or any(not _native(value, magnitude=64) for value in recipe.vector)
                    or not _native(recipe.position_radius, magnitude=1)
                    or type(recipe.identity_offset) is not int or recipe.identity_offset not in (0, 1)
                    or recipe.coefficient_source is not None and type(recipe.coefficient_source) is not str
                    or recipe.product_pair is not None and (
                        not _product_pair_shape(recipe.product_pair, len(plan.nodes))
                        or index not in recipe.product_pair[2:]
                        or type(recipe.product_owner) is not tuple or len(recipe.product_owner) != 3
                        or any(type(value) is not str for value in recipe.product_owner))
                    or recipe.product_pair is None and recipe.product_owner is not None
                    or _integers((recipe.vector, recipe.position_radius, recipe.identity_offset,
                                  recipe.coefficient_source, recipe.product_pair,
                                  recipe.product_owner)) != recipe.seal):
                raise ReferenceError("identity", "Independent centered source recipe changed")
            guard.watch(recipe, ("vector", "position_radius", "identity_offset", "coefficient_source",
                                 "product_pair", "product_owner", "seal"))
            vector, maximum_radius = guard.vector(recipe.vector), guard.freeze(recipe.position_radius)
            parent = None if node.kind == "root" else guard.pose(frames[node.parent])
            guard.checked(a.tick)
            # Check before a stationary-cache hit too. The source-only flag
            # does not substitute for this frozen parent's honest radius.
            if recipe.identity_offset and (parent is None or
                    parent.orientation != (1, 0, 0, 0) or parent.orientation_radius):
                raise _ChangedDomain()
            key = None
            if node.stationary:
                key = ("reference_centered_stationary_pose", a.bits, a.operand_limit,
                       plan.cache_identity, node.path)
                previous = guard.lookup(key)
                if previous is not None:
                    value = guard.pose(previous)
                    if not guard.current():
                        raise _ChangedDomain()
                    frames[node.path] = value
                    continue
            if node.kind == "root":
                value = _CenteredPose(vector, (F(1), F(0), F(0), F(0)), F(0), F(0), None)
            else:
                if node.kind == "hinge" and not node.body.identity_relative:
                    rotation, radius, axis = _orientation(node, time, plan.context, reference, guard, pending)
                    parent = _CenteredPose(parent.position, rotation, parent.position_radius, radius, axis)
                offset, uncertain = _offset(parent, vector, guard,
                    identity_only=bool(recipe.identity_offset),
                    coefficient_source=None if recipe.coefficient_source is None else
                    (plan.cache_identity, recipe.coefficient_source),
                    product_session=products, product_pair=recipe.product_pair, product_index=index)
                position = tuple(first if not last else last if not first else
                                 guard.exact(first, last, "add")
                                 for first, last in zip(parent.position, offset))
                value = _CenteredPose(position, parent.orientation,
                                     maximum_radius if uncertain else parent.position_radius,
                                     parent.orientation_radius, parent.axis)
            if (any(not _native(value, magnitude=256) for value in value.position)
                    or any(not _native(value, magnitude=2) for value in value.orientation)):
                raise _ChangedDomain()
            if key is not None:
                guard.remember(key, value)
                # This is the existing rejection ledger, never a source of
                # numeric values. Stationary writes must be discarded too if
                # the optional attempt or complete batch is later rejected.
                batch.record_cursors(((key, value, None),))
            frames[node.path] = value
        plan.admit_owners(reference)
        batch.admit_owners()
        if not reference._recording_body_domain():
            return None
        batch.check_cursors()
        pending.publish()
        batch.record_cursors(pending.values)
        return frames
    except _OriginalFailure as failure:
        raise failure.error
    except _ChangedDomain:
        batch.discard_cursors()
        return None
    except ReferenceError as error:
        if (error.code != "resource" or error is getattr(a.work, "callback_error", None)
                or reference._recording_body_domain()):
            raise
        # Only an added operation's narrowed-domain refusal may retry. The
        # ordinary reference calculation is outside this handler.
        batch.discard_cursors()
        return None
    finally:
        _PRODUCT_CLOSE(products)


_PRODUCT_ABSENT = object()
_PRODUCT_NATIVE, _PRODUCT_NATIVE_CODE = _product_native, _product_native.__code__
_PRODUCT_SESSION_STATE = _ProductSession.__dict__["__dict__"].__get__
_PRODUCT_OBSERVE, _PRODUCT_CURRENT = _ProductSession._observe, _ProductSession.current
_PRODUCT_ENTER, _PRODUCT_BIND = _ProductSession.enter, _ProductSession.bind
_PRODUCT_CAPTURE, _PRODUCT_REUSE = _ProductSession.capture, _ProductSession.reuse
_PRODUCT_PUBLISH, _PRODUCT_PAYLOAD = _ProductSession.publish, _ProductSession._payload_snapshot
_PRODUCT_SAME_PAYLOAD = _ProductSession._same_payload
# A separate code-bearing function also preserves cleanup if a callback
# replaces the class method or mutates that method's __code__ in place.
_PRODUCT_CLOSE = FunctionType(_ProductSession.close.__code__, globals(),
                              "_close_centered_product_session", (_PRODUCT_SESSION_STATE,))
_PRODUCT_STORAGE = ("__getattribute__", "__getattr__", "__setattr__", "__delattr__", "__dict__")
_PRODUCT_PLAN_FIELDS = ("cache_identity", "context", "state", "nodes", "centered")
_PRODUCT_ARITHMETIC_METHODS = ("exact", "guard", "tick", "_sync_cache_operand_limit",
                               "_grid_domain", "operand_limit")
_PRODUCT_GUARD_METHODS = ("exact", "checked", "current", "freeze", "vector", "watch", "lookup",
                         "remember", "floor", "neg", "original", "pose", "intervals")
_PRODUCT_SESSION_METHODS = ("_observe", "current", "enter", "bind", "capture", "reuse", "publish", "close",
                            "_same_source", "_same_payload", "_payload_snapshot")
from .reach_reference_plan import _Node as _ProductNode, _Plan as _ProductPlan
_PRODUCT_CLASS_FIELDS = tuple((kind, tuple((name, type.__getattribute__(kind, "__dict__").get(
    name, _PRODUCT_ABSENT)) for name in dict.fromkeys((*_PRODUCT_STORAGE, *names)))) for kind, names in (
        (_Arithmetic, (*_PRODUCT_ARITHMETIC_METHODS, "bits", "scale", "cache", "work", "check",
                       "_cache_operand_limit", "_recording_after_tick", "_recording_product_after_tick")),
        (_Guard, (*_PRODUCT_GUARD_METHODS, "a", "work", "check", "coefficient_slot", "product_session")),
        (_ProductNode, ("path", "kind", "parent", "stationary")),
        (_ProductPlan, _PRODUCT_PLAN_FIELDS),
        (_CenteredNode, ("__new__", "__init__", "__post_init__", "vector", "position_radius", "identity_offset", "coefficient_source",
                         "product_pair", "product_owner", "seal")),
        (_CenteredCoefficients, ("__new__", "__init__", "__post_init__", "scalar", "active", "diagonal", "cross", "seal", "products")),
        (_CenteredProducts, ("__new__", "__init__", "__post_init__", "token", "clock", "pair", "operand", "first", "last", "seal")),
        (_ProductSession, ("__init__", *_PRODUCT_SESSION_METHODS, "valid", "installed", "closed", "observer",
                           "a", "cache", "check", "work", "reference", "plan", "time", "token", "error")),
        (F, ("__new__", "__init__", "__mul__", "__add__", "__sub__", "__truediv__", "__neg__", "__abs__",
             "_mul", "_add", "_sub", "_div", "_from_coprime_ints", "__bool__", "__eq__", "__lt__",
             "__le__", "__gt__", "__ge__", "_richcmp", "numerator", "denominator", "_numerator", "_denominator"))))


def _product_function_state(function):
    return (function.__code__, function.__defaults__, function.__kwdefaults__,
            tuple((function.__kwdefaults__ or {}).items()),
            tuple(cell.cell_contents for cell in function.__closure__ or ()),
            tuple((name, function.__globals__.get(name, _PRODUCT_ABSENT),
                   function.__builtins__.get(name, _PRODUCT_ABSENT)) for name in function.__code__.co_names))


def _product_functions():
    functions = [_product_fields, _product_pair_shape, _product_mapping, _product_plan_identity,
                 _product_source, _integers, _native]
    for _, members in _PRODUCT_CLASS_FIELDS:
        for _, function in members:
            if type(function) in (classmethod, staticmethod):
                function = function.__func__
            elif type(function) is property:
                function = function.fget
            if type(function) is FunctionType:
                functions.append(function)
                if function.__closure__ is not None:
                    functions.extend(cell.cell_contents for cell in function.__closure__
                                     if type(cell.cell_contents) is FunctionType)
    return tuple(dict.fromkeys(functions))


_PRODUCT_FUNCTIONS = tuple((function, _product_function_state(function)) for function in _product_functions())
_PRODUCT_GLOBALS = ((fractions, "Fraction", F), (fractions, "math", math), (fractions, "numbers", numbers),
                    (numbers, "Rational", numbers.Rational), (numbers, "Real", numbers.Real),
                    (numbers, "Complex", numbers.Complex), (math, "gcd", math.gcd),
                    (sys, "gettrace", sys.gettrace), (sys, "getprofile", sys.getprofile))
