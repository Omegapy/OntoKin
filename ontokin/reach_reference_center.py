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
    seal: tuple = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "seal", _integers((self.vector, self.position_radius)))


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
    def __init__(self, reference, plan, batch):
        self.reference, self.plan, self.batch = reference, plan, batch
        self.a, self.p = reference.a, reference.p
        self.work, self.check = self.a.work, self.a.check
        self.external = getattr(self.work, "external_check", None)
        self.work_kind = type(self.work)
        self.leaves, self.records, self.cells = [], [], []
        self.invalidated = False
        self.oracle_guard = None
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

    def lookup(self, key):
        # Expose both original callback boundaries to the live receipt, so a
        # cap narrowed by lookup cannot be restored by cache synchronization
        # before this optional proof notices it.
        self.checked(self.a.tick)
        self.checked(self.a._sync_cache_operand_limit)
        value = self.a.cache.get(key)
        if value is not None:
            del self.a.cache[key]
            self.a.cache[key] = value
        return value

    def remember(self, key, value, *, pending=None, previous=None):
        self.checked(self.a.tick)
        self.checked(self.a._sync_cache_operand_limit)
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
    for node in plan.nodes:
        guard = _Guard(reference, plan, batch)
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
            if any(not _native(value, magnitude=1) for value in vector):
                return replace(plan, centered=False)
            total = F(0)
            for value in vector:
                if value:
                    total = abs(value) if not total else guard.exact(total, abs(value), "add")
            if total > 1:
                return replace(plan, centered=False)
            if node.kind not in {"site", "follow"}:
                vector = tuple(guard.neg(value) if value else value for value in vector)
            depth = depths[node.parent] + int(bool(total))
        a.guard(*vector)
        if not reference._recording_body_domain():
            return plan
        radius = guard.exact(F(depth), F(1, 1 << 102), "mul") if depth else F(0)
        nodes.append(_CenteredNode(vector, radius))
        depths[node.path] = depth
    plan.admit_owners(reference)
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


def _offset(parent, vector, guard):
    """Project the Hamilton center rotation onto the true rotating plane."""
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
    diagonal = guard.exact(guard.exact(w, w, "mul"), guard.exact(s, s, "mul"), "sub")
    cross = guard.exact(guard.exact(w, s, "mul"), 2, "mul")
    def product(first, last):
        return (F(0) if not first or not last else first if last == 1 else
                guard.neg(first) if last == -1 else guard.exact(first, last, "mul"))
    def combined(first, last, subtract=False):
        return ((guard.neg(last) if subtract and last else last) if not first else first if not last else
                guard.exact(first, last, "sub" if subtract else "add"))
    first = guard.floor(combined(product(diagonal, x), product(cross, y), True))
    last = guard.floor(combined(product(cross, x), product(diagonal, y)))
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
    frames = {"world": _CenteredPose((F(0),) * 3, (F(1), F(0), F(0), F(0)), F(0), F(0), None)}
    try:
        for node, recipe in zip(plan.nodes, plan.centered):
            guard = _Guard(reference, plan, batch)
            if (type(recipe) is not _CenteredNode or type(recipe.vector) is not tuple
                    or len(recipe.vector) != 3 or any(not _native(value, magnitude=64) for value in recipe.vector)
                    or not _native(recipe.position_radius, magnitude=1)
                    or _integers((recipe.vector, recipe.position_radius)) != recipe.seal):
                raise ReferenceError("identity", "Independent centered source recipe changed")
            guard.watch(recipe, ("vector", "position_radius", "seal"))
            vector, maximum_radius = guard.vector(recipe.vector), guard.freeze(recipe.position_radius)
            parent = None if node.kind == "root" else guard.pose(frames[node.parent])
            guard.checked(a.tick)
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
                offset, uncertain = _offset(parent, vector, guard)
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
