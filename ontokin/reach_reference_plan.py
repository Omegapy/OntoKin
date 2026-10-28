"""Bounded source-formula plans for the independent recording reader.

This module reads only the private source records and arithmetic of
``reach_reference``. It imports no production evaluator, sampler or numeric
kernel. A plan holds source operands and source-derived affine recipes, never
a second table of completed numeric poses. Ordinary requests recheck their
source receipts; an explicit complete-validation batch defers those reads to
its final callback-free admission. All cursor values use the existing cache.
"""
from dataclasses import dataclass, field, replace
from fractions import Fraction as F
import math

from .reach_reference import (
    MAX_BOUNDARIES, MAX_CACHE, MAX_OPERAND_BITS, Interval, PoseEnclosure, ReferenceError, ZERO,
    _Action, _Arithmetic, _PoseArithmetic, _RecordingBodyRate,
)


# Sufficient domains for this optional structural proof. Larger graphs retain
# the complete original walker and unchanged public resource allowances.
MAX_TARGETS = 64
MAX_NODES = 128
MAX_CURSORS = 32
MAX_BATCH_PLANS = 16
MAX_BATCH_RECEIPTS = 1024
_SOURCE_MAPS = ("objects", "sites", "joints", "follows", "actions")
_PARTITION_TICK = _Arithmetic.tick


def _owners(reference):
    """Strong owner identities, separate from equality of source operands."""
    return (reference.model, reference.a, reference.p, reference.p.a,
            reference.a.work, reference.a.check,
            *(getattr(reference.model, name) for name in _SOURCE_MAPS))


class _SourceBatchRestart(Exception):
    """Only the added final batch domain gate may request an ordinary replay."""


class _SourceBatch:
    """Defer repeated source admission until the reader's final callback.

    Plans contain immutable source operands, never completed pose maps. Each
    key still reads and publishes its cursors through the original arithmetic
    cache. The bounded ledger only identifies writes to remove on rejection;
    it is never consulted to obtain a numeric cursor or to defeat eviction.
    """
    def __init__(self, reference, context):
        if type(context) is not object:
            raise ValueError("Independent source batching requires an opaque reader context")
        self.reference, self.context = reference, context
        self.active = self.prepared = False
        self.depth = 0
        self.current_plan = None
        self.plans, self.cursors = {}, {}
        self.receipts, self.seen_receipts = [], set()
        self.restart = None

    def __enter__(self):
        reference = self.reference
        if reference._recording_batch is not None:
            raise ReferenceError("identity", "Independent source batches cannot replace an active reader")
        if not reference._recording_body_domain():
            return self
        # The native history axis is an immutable tuple of exact Fraction
        # clocks. Its strong identity therefore binds every boundary value;
        # mutable or foreign axes retain the ordinary per-key admission.
        if (type(reference.boundaries) is not tuple or len(reference.boundaries) > MAX_BOUNDARIES
                or any(type(time) is not F for time in reference.boundaries)
                or type(reference._before) is not list or type(reference._after) is not list
                or len(reference._before) != len(reference.boundaries)
                or len(reference._after) != len(reference.boundaries)):
            return self
        self.a = reference.a
        self.owners = _owners(reference)
        self.history = (reference.boundaries, reference._before, reference._after)
        self.header = (reference.end, reference.end_side, reference.mode,
                       len(reference._before), len(reference._after))
        reference._recording_batch = self
        self.active = True
        return self

    def admit_owners(self):
        reference = self.reference
        try:
            owned = (reference._recording_batch is self and
                     all(current is saved for current, saved in zip(_owners(reference), self.owners)) and
                     all(current is saved for current, saved in zip(
                         (reference.boundaries, reference._before, reference._after), self.history)) and
                     (reference.end, reference.end_side, reference.mode,
                      len(reference._before), len(reference._after)) == self.header)
        except AttributeError:
            owned = False
        if not owned:
            raise ReferenceError("identity", "Independent source batch owner or phase history changed")

    def matches(self, context):
        return (self.active and not self.prepared and type(context) is tuple and
                len(context) == 4 and context[0] is self.context)

    def contains(self, plan):
        return plan.cache_identity in self.plans

    def register(self, plan, time):
        self.admit_owners()
        if self.prepared or not self.reference._recording_body_domain():
            return False
        if self.contains(plan):
            previous, time = self.plans[plan.cache_identity]
            if previous is not plan and type(plan.centered) is tuple:
                if (previous.state is not plan.state or previous.nodes is not plan.nodes
                        or previous.receipts is not plan.receipts or previous.owners is not plan.owners
                        or previous.context != plan.context or previous.targets != plan.targets
                        or previous.remaining != plan.remaining):
                    raise ReferenceError("identity", "Independent source plan identity changed")
                # An already registered ordinary plan may acquire a private
                # source-only centered recipe. Its stronger final signature
                # admission must accompany later compact endpoint results.
                self.plans[plan.cache_identity] = (plan, time)
            return True
        fresh = [receipt for receipt in plan.receipts if id(receipt) not in self.seen_receipts]
        if len(self.plans) >= MAX_BATCH_PLANS or len(self.receipts) + len(fresh) > MAX_BATCH_RECEIPTS:
            # Already captured plans remain covered by the final admission.
            # A new plan outside this optional bound keeps every original
            # per-request source check and does not enlarge retained storage.
            return False
        self.plans[plan.cache_identity] = (plan, time)
        self.receipts.extend(fresh)
        self.seen_receipts.update(id(receipt) for receipt in fresh)
        return True

    def covers_identity(self, receipts):
        return (self.depth == 1 and self.current_plan is not None and
                self.contains(self.current_plan) and
                all(id(receipt) in self.seen_receipts for receipt in receipts))

    def check_cursors(self):
        # Drop evicted references before recording the next key. A different
        # still-retained value is a nested writer, not ordinary LRU eviction.
        for key, value in tuple(self.cursors.items()):
            current = self.a.cache.get(key)
            if current is None:
                del self.cursors[key]
            elif current is not value:
                raise ReferenceError("identity", "Independent source batch cursor changed in a nested reader")

    def record_cursors(self, values):
        for key, value, _ in values:
            if self.a.cache.get(key) is value:
                self.cursors[key] = value
        self.check_cursors()
        if len(self.cursors) > MAX_CACHE:
            raise ReferenceError("resource", "Independent source batch exceeds its cursor ledger bound")

    def discard_cursors(self):
        for key, value in self.cursors.items():
            if self.a.cache.get(key) is value:
                del self.a.cache[key]
        self.cursors.clear()

    def completed_ordinary_request(self):
        # A new plan beyond the optional capture bound executes its complete
        # original per-key source admission. Its independently completed new
        # values are no longer writes owned by this deferred source batch.
        # Still-retained older values remain owned and must be admitted later.
        for key, value in tuple(self.cursors.items()):
            if self.a.cache.get(key) is not value:
                del self.cursors[key]

    def prepare_admission(self):
        """Precharge receipt reads before the reader's last checked callback."""
        if not self.active or self.prepared:
            return
        self.prepared = True
        if not self.plans:
            return
        self.admit_owners()
        self.depth += 1
        try:
            for _ in self.receipts:
                self.a.tick()
        finally:
            self.depth -= 1
        self.admit_owners()

    def admit(self):
        if not self.plans:
            return
        self.admit_owners()
        self.check_cursors()
        reference = self.reference
        for plan, time in self.plans.values():
            try:
                current = reference._state_at(time, plan.context[-1])
            except (KeyError, AttributeError, IndexError) as error:
                raise ReferenceError("identity", "Independent source batch state binding changed") from error
            if current is not plan.state:
                raise ReferenceError("identity", "Independent source batch state binding changed")
            if type(plan.centered) is tuple:
                from .reach_reference_center import admit_source
                admit_source(plan, reference)
        # Identity rejection must not be relabeled as an optional domain
        # restart when the same callback also changes the operand allowance.
        for receipt in self.receipts:
            try:
                current = receipt.read()
            except (KeyError, AttributeError, IndexError) as error:
                raise ReferenceError("identity", "Independent source changed during source batch") from error
            if (reference._recording_source_witness(*current) is None or
                    current != receipt.values):
                raise ReferenceError("identity", "Independent source changed during source batch")
        if reference.a.bits != 128:
            raise ReferenceError("identity", "Independent source batch arithmetic precision changed")
        if reference.a.operand_limit != MAX_OPERAND_BITS:
            self.restart = _SourceBatchRestart("Final independent source batch operand domain changed")
            raise self.restart
        if not reference._recording_body_domain():
            raise ReferenceError("identity", "Independent source batch arithmetic context changed")
        # The preceding identity-only pass deliberately precedes the optional
        # cap restart. Now retain the original numeric operand admission;
        # its second bounded source read cannot invoke a caller callback.
        reference._recording_admit_receipts(self.receipts)
        for key, value in self.cursors.items():
            if key[0] == "reference_centered_stationary_pose":
                from .reach_reference_center import guard_pose
                guard_pose(self.a, value)
            elif key[3] == "recording_center_body_orientation":
                from .reach_reference_center import guard_cursor
                guard_cursor(self.a, value)
            elif key[3] == "recording_body_orientation":
                _, _, rate, clock, rotation, increment, steps = value
                self.a.guard(rate, clock, steps, *(endpoint for cell in rotation
                                                   for endpoint in (cell.lo, cell.hi)),
                             *((increment or ())))
            else:
                clock, coordinate, sine, cosine, steps = value
                self.a.guard(clock, coordinate, sine.lo, sine.hi, cosine.lo, cosine.hi, steps)

    def __exit__(self, kind, error, traceback):
        if not self.active:
            return False
        try:
            if error is not None:
                self.discard_cursors()
                return False
            try:
                self.prepare_admission()
                self.admit()
            except BaseException:
                self.discard_cursors()
                raise
            self.cursors.clear()
        finally:
            if self.reference._recording_batch is self:
                self.reference._recording_batch = None
            self.active = False
        return False


@dataclass(frozen=True)
class _LocalPose:
    position: tuple
    rotation: tuple


def _identity_child_origin(node):
    """A copied native translation whose inverse rotation is exactly identity.

    The enclosing source batch still admits every actual ancestry record.
    This predicate substitutes no position or interval value: the original
    inverse child pose must be composed after the complete body orientation.
    """
    local = node.local
    return (type(local) is _LocalPose
            and type(local.position) is tuple and len(local.position) == 3
            and type(local.rotation) is tuple and len(local.rotation) == 4
            and all(type(value) is float and math.isfinite(value)
                    for value in (*local.position, *local.rotation))
            and local.rotation == (1.0, 0.0, 0.0, 0.0))


@dataclass(frozen=True)
class _RootTranslation:
    """The original prescribed position equation with captured operands."""
    position: tuple
    vector: tuple | None = None
    initial: tuple | None = None
    status: str | None = None
    elapsed: F = F(0)
    since: F = F(0)

    def evaluate(self, reference, time):
        a, p = reference.a, reference.p
        position = self.position
        velocity, omega = p.vector(ZERO), p.vector(ZERO)
        if self.vector is not None:
            elapsed = (a.exact_sum(self.elapsed, a.exact(time, self.since, "sub"))
                       if self.status == "running" else self.elapsed)
            a.guard(elapsed)
            position = p.add(self.initial, p.scale(self.vector, elapsed))
        return position, velocity, omega


@dataclass(frozen=True)
class _Node:
    path: str
    kind: str
    parent: str | None
    local: object
    body: object
    relation: str | None = None
    axis: tuple | None = None
    stationary: bool = False
    source_stationary: bool | None = None


class _PendingCursors:
    """Precharge bounded cursor writes, then admit them without callbacks.

The ordinary ``remember`` hook is preserved, including its own work callback
and live-cap synchronization. Its admission deliberately defers insertion.
Failure leaves no new partially admitted cursor. Pure arithmetic memoization
continues to use the same bounded cache throughout the calculation.
    """
    def __init__(self, arithmetic):
        self.a = arithmetic
        self.values = []

    def remember(self, key, value, previous, admission):
        def stage():
            if admission() is False:
                return False
            if len(self.values) >= MAX_CURSORS:
                raise ReferenceError("resource", "Independent pending cursor plan exceeds its bounded domain")
            self.values.append((key, value, previous))
            return False
        return self.a.remember(key, value, admission=stage)

    def publish(self):
        # A reentrant request may have advanced the same context while an
        # outer arithmetic callback ran. Do not overwrite its fresh cursor.
        # Ordinary bounded eviction of the previous entry remains harmless.
        for key, _, previous in self.values:
            current = self.a.cache.get(key)
            if current is not None and current is not previous:
                raise ReferenceError("identity", "Independent recording cursor changed during pending proof")
        for key, value, _ in self.values:
            if key in self.a.cache:
                del self.a.cache[key]
            elif len(self.a.cache) >= MAX_CACHE:
                del self.a.cache[next(iter(self.a.cache))]
            self.a.cache[key] = value


@dataclass(frozen=True)
class _Plan:
    state: object
    context: tuple
    targets: tuple
    nodes: tuple
    receipts: tuple
    owners: tuple
    remaining: tuple = ()
    cache_identity: object = field(default_factory=object, compare=False)
    centered: object = field(default=None, compare=False)

    def owned_by(self, reference):
        try:
            return all(current is saved for current, saved in zip(_owners(reference), self.owners))
        except AttributeError:
            return False

    def admit_owners(self, reference):
        if not self.owned_by(reference):
            raise ReferenceError("identity", "Independent recording source or arithmetic owner changed")

    def current(self, reference, batch=None):
        # Each unique actual source record is freshly read under a charged
        # callback. The captured immutable recipe is used only if it matches.
        # Final admission below rechecks the whole batch after all callbacks.
        if not self.owned_by(reference):
            return False
        if batch is not None and batch.contains(self):
            batch.admit_owners()
            return True
        for receipt in self.receipts:
            reference.a.tick()
            self.admit_owners(reference)
            if not reference._recording_body_domain():
                return False
            try:
                current = receipt.read()
            except (KeyError, AttributeError, IndexError):
                return False
            if (reference._recording_source_witness(*current) is None or
                    current != receipt.values):
                return False
        return True

    def evaluate(self, reference, time, batch=None):
        self.admit_owners(reference)
        a, p = reference.a, reference.p
        shared = len(self.targets) > 16
        frames = {"world": p.identity()}
        advanced = set()
        pending = _PendingCursors(a)

        def compose(parent, local, moving):
            if moving and not shared:
                return p._recording_sequential_compose(parent, local, recording=True)
            return p.compose(parent, local, recording=True) if moving else p.compose(parent, local)

        def guard(value):
            a.guard(*(endpoint for vector in (value.position, value.orientation, value.velocity, value.omega)
                      for cell in vector for endpoint in (cell.lo, cell.hi)))

        for node in self.nodes:
            # One topological visit replaces recursive dependency revisits;
            # there is still one charged actual source frame evaluation.
            self.admit_owners(reference)
            a.tick()
            self.admit_owners(reference)
            stationary_key = None
            if node.stationary:
                # This is a pure completed value in the original bounded
                # arithmetic memo, not a retained pose table on the plan.
                # A new source recipe has a new identity even if its values
                # happen to compare equal to a previous phase's operands.
                stationary_key = ("reference_recording_stationary_pose", a.bits, a.operand_limit,
                                  self.cache_identity, node.path)
                value = a.lookup(stationary_key)
                self.admit_owners(reference)
                if not reference._recording_body_domain():
                    return None
                if value is not None:
                    guard(value)
                    frames[node.path] = value
                    continue
            moving = node.parent in advanced
            if node.kind == "root":
                body = node.body
                position, velocity, omega = reference._prescribed_root_translation(
                    node.path.removesuffix(".frame"), time, self.state,
                    ideal=True, pose_only=True, captured=node.local)
                if body.moving and reference._recording_body_domain():
                    rotation, moving = p._recording_body_orientation(
                        lambda: body.direct(time), axis=body.axis, rate=body.rate,
                        witness=body.witness, context=(self.context, node.path), clock=time,
                        shared=shared, return_advance=True, pending=pending)
                else:
                    # An unclaimed root orientation is already the captured
                    # independent interval. A paused/completed spin retains
                    # its ordinary direct seed rather than its running rate.
                    rotation = body.witness[3] if body.witness[4] is None else body.direct(time)
                value = PoseEnclosure(position, rotation, velocity, omega)
            elif node.kind in {"site", "follow"}:
                value = compose(frames[node.parent], p.constant(node.local), moving)
            else:
                value, body = frames[node.parent], node.body
                used_body = False
                # A complete reader batch may advance the already proved
                # body orientation through an identity-rotated child site.
                # Its nonzero inverse translation remains a separate original
                # composition. Direct inspection and ordinary walkers retain
                # their preceding cells and local-angle cursor behavior.
                child_origin = (batch is not None and node.kind == "hinge"
                                and not body.zero_origin and _identity_child_origin(node))
                if (node.kind == "hinge" and (body.zero_origin or child_origin)
                        and reference._recording_body_domain()):
                    identical = reference._recording_identity_parent(value, body)
                    if identical is not None:
                        value, used_body = identical, True
                    elif body.moving:
                        rotation, rotation_advanced = p._recording_body_orientation(
                            lambda: body.direct(time), axis=body.axis, rate=body.rate,
                            witness=body.witness, context=(self.context, node.path), clock=time,
                            shared=shared, return_advance=True, pending=pending)
                        moving = moving or rotation_advanced
                        a.guard(*(endpoint for vector in (value.position, rotation)
                                  for cell in vector for endpoint in (cell.lo, cell.hi)))
                        value = PoseEnclosure(value.position, rotation, value.velocity, value.omega)
                        if child_origin:
                            value = compose(value, p.inverse(p.constant(node.local)), moving)
                        used_body = True
                if not used_body:
                    if node.kind == "hinge":
                        coordinate = body.coordinate_at(time)
                        angle_context = ((self.context, node.relation) if body.coordinate_rate else None)
                        motion = p.hinge(node.axis, coordinate, F(0), ideal=True,
                                         recording_context=angle_context,
                                         recording_time=time if angle_context is not None else None,
                                         shared_recording=shared, pending=pending)
                        value = compose(value, motion, moving)
                    # Unsupported child rotations and ordinary requests keep
                    # both local compositions. A body orientation recipe never
                    # replaces its position proof.
                    value = compose(value, p.inverse(p.constant(node.local)), moving)
            guard(value)
            if stationary_key is not None:
                def admit_stationary():
                    self.admit_owners(reference)
                    if not reference._recording_body_domain():
                        return False
                    guard(value)
                    return True
                a.remember(stationary_key, value, admission=admit_stationary)
            frames[node.path] = value
            if moving:
                advanced.add(node.path)

        if batch is None:
            for _ in self.receipts:
                a.tick()
        self.admit_owners(reference)
        if not reference._recording_body_domain():
            return None
        if batch is None:
            reference._recording_admit_receipts(self.receipts)
        for value in frames.values():
            guard(value)
        if batch is not None:
            batch.check_cursors()
        pending.publish()
        if batch is not None:
            batch.record_cursors(pending.values)
        return frames


@dataclass(frozen=True)
class _PartitionedPlan:
    """A source-only split whose dynamic ancestry still uses the full walker.

    No completed frame table crosses the split. The ordinary remainder runs
    first in its own fresh map; only then may the existing interval plan run.
    A declined plan leaves that ordinary work in place for complete fallback.
    """
    plan: _Plan
    batch: _SourceBatch
    clock: F
    clock_fields: tuple

    def evaluate_remaining(self, reference, frame, frames):
        plan, batch, a = self.plan, self.batch, reference.a
        plan.admit_owners(reference)
        batch.admit_owners()
        if (type(a) is not _Arithmetic or type(reference.p) is not _PoseArithmetic
                or a._recording_after_tick is not None or batch.depth != 0
                or batch.current_plan is not None or not batch.matches(plan.context)
                or not batch.contains(plan) or not reference._recording_body_domain()
                or getattr(a.tick, "__func__", None) is not _PARTITION_TICK
                or getattr(a.tick, "__self__", None) is not a
                or type(a.bits) is not int or a.bits != 128
                or type(a.scale) is not int or a.scale != 1 << 128):
            return None
        valid = True

        def observed():
            nonlocal valid
            plan.admit_owners(reference)
            batch.admit_owners()
            clock = self.clock
            if (a._recording_after_tick is not observed or batch.depth != 1
                    or batch.current_plan is not None and batch.current_plan is not plan
                    or batch.plans.get(plan.cache_identity, (None,))[0] is not plan
                    or getattr(a.tick, "__func__", None) is not _PARTITION_TICK
                    or getattr(a.tick, "__self__", None) is not a
                    or type(clock) is not F or type(clock.numerator) is not int
                    or type(clock.denominator) is not int
                    or (clock.numerator, clock.denominator) != self.clock_fields):
                raise ReferenceError("identity", "Independent source partition owner or clock changed")
            if (type(a.bits) is not int or a.bits != 128
                    or type(a.scale) is not int or a.scale != 1 << 128):
                raise ReferenceError("identity", "Independent source partition precision changed")
            # Latch narrowing even if a later original callback restores it.
            # Do not preempt an original arithmetic operation's prospective
            # resource guard or its caller's exception with optional fallback.
            valid = valid and a.operand_limit == MAX_OPERAND_BITS

        a._recording_after_tick = observed
        batch.depth += 1
        try:
            observed()
            for path in plan.remaining:
                frame(path)
            observed()
            if not valid:
                return None
            # The captured graph partitions complete root ancestries. A live
            # route that traversed a prescribed node cannot silently borrow
            # or overwrite an independently planned parent.
            if any(node.path in frames for node in plan.nodes):
                raise ReferenceError("identity", "Independent source partition ancestry changed")
            batch.check_cursors()
            batch.current_plan = plan
            result = plan.evaluate(reference, self.clock, batch) if plan.nodes else {}
            observed()
            return result if valid else None
        finally:
            if a._recording_after_tick is observed:
                a._recording_after_tick = None
            if batch.current_plan is plan:
                batch.current_plan = None
            batch.depth -= 1


def _build(reference, state, targets, context, *, source_stationarity=False, partition=False):
    """Capture a bounded native graph in the original first-visit order."""
    model, a = reference.model, reference.a
    owners = _owners(reference)
    receipts, seen_receipts = [], set()

    def add_receipts(values):
        for receipt in values:
            if id(receipt) not in seen_receipts:
                seen_receipts.add(id(receipt))
                receipts.append(receipt)

    def header():
        return ("phase_graph", len(model.objects), len(model.sites), len(model.joints),
                len(model.follows), tuple(sorted(state.grips)))
    receipt = reference._recording_capture(header)
    if receipt is None:
        return None
    _, objects, sites, joints, follows, grips = receipt.values
    if objects > 64 or sites > 128 or joints > 32 or follows > 32 or len(grips) > 8:
        return None
    add_receipts((receipt,))

    # Capture all relation endpoints, including relations outside the chosen
    # ancestry. An added/redirected incoming edge must not leave a root plan
    # silently valid. Counts plus every retained relation key also detect a
    # replacement, removal or addition without an unbounded topology tuple.
    incoming, graph_receipts = {}, {}
    for relation in tuple(model.joints):
        def read(relation=relation):
            joint = model.joints[relation]
            child = model.sites[joint.child]
            return (joint.path, joint.kind, joint.parent, joint.child, joint.axis,
                    child.owner + ".frame", child.pose.position, child.pose.rotation)
        item = reference._recording_capture(read)
        if item is None:
            return None
        graph_receipts[("joint", relation)] = item
        if item.values[1] != "grip" or relation in grips:
            incoming[item.values[5].removesuffix(".frame")] = ("joint", relation)
    for relation in tuple(model.follows):
        def read(relation=relation):
            follow = model.follows[relation]
            return ("follow", relation, follow.parent, follow.offset.position,
                    follow.offset.rotation, follow.child + ".frame")
        item = reference._recording_capture(read)
        if item is None:
            return None
        graph_receipts[("follow", relation)] = item
        incoming[item.values[5].removesuffix(".frame")] = ("follow", relation)

    world = _RecordingBodyRate(None, F(0), False, ("world",), "world",
                               lambda clock: reference.p.identity().orientation, ())
    bodies, nodes, visiting, used_relations = {"world": world}, [], set(), set()
    stationary = {"world": True}
    source_stationary = {"world": True}

    def stationary_source(node, fixed):
        # Pose-plan stationarity describes the ideal formula. Reusing a whole
        # endpoint comparison also requires the actual source law to be fixed.
        # These extra immutable source operands join the same bounded receipts;
        # no evaluated pose, clock history or second numeric cache is retained.
        if not source_stationarity:
            return None
        if not fixed:
            return False
        if node.kind == "root":
            stem = node.path.removesuffix(".frame")
            def read():
                move = state.claims.get((stem, "translation"))
                spin = state.claims.get((stem, "orientation"))
                for owner in (move, spin):
                    if owner is not None:
                        active = state.actions[owner]
                        if (type(active) is not _Action or type(active.elapsed) is not F
                                or type(active.since) is not F):
                            return ("stationary_root_actual", stem, active)
                return ("stationary_root_actual", stem, state.positions[stem], state.orientations[stem],
                        None if move is None else state.actions[move].initial,
                        None if spin is None else state.actions[spin].initial)
            receipt = reference._recording_capture(read)
            if receipt is None:
                return None
            for vector, size in zip(receipt.values[2:], (3, 4, 3, 4)):
                if vector is not None and (type(vector) is not tuple or len(vector) != size
                        or any(type(cell) is not Interval for cell in vector)):
                    return None
            add_receipts((receipt,))
            return True
        parent = source_stationary[node.parent]
        if parent is not True or node.kind != "hinge":
            return parent
        relation = node.relation
        def read():
            owner = state.claims.get((relation, "coordinate"))
            if owner is not None:
                active = state.actions[owner]
                if (type(active) is not _Action or type(active.elapsed) is not F
                        or type(active.since) is not F):
                    return ("stationary_coordinate_actual", relation, active)
            return ("stationary_coordinate_actual", relation, owner,
                    state.coordinates[relation] if owner is None else state.actions[owner].initial)
        receipt = reference._recording_capture(read)
        if receipt is None:
            return None
        law = node.body.receipts[-1].values
        if law[1] is None or law[9] != "running":
            add_receipts((receipt,))
            return True
        index = law[4].index(relation) if law[2] == "reach_planar" else None
        actual = receipt.values[3]
        if index is not None:
            if type(actual) is not tuple or len(actual) != 2:
                return None
            actual = actual[index]
        if type(actual) not in (F, int, float):
            return None
        add_receipts((receipt,))
        ideal = law[7][index] if index is not None else law[7]
        target = law[8][index] if index is not None else law[6]
        # A zero ideal slope alone is insufficient: source rounding may have
        # left the actual initial coordinate different from the ideal target.
        return F(actual) == F(ideal) == F(target)

    def visit(path):
        if path in bodies:
            return True
        # Ordinary remainder markers consume the same node bound as recipes.
        if path in visiting or len(bodies) - 1 + len(visiting) >= MAX_NODES:
            return False
        a.tick()
        visiting.add(path)
        stem = path.removesuffix(".frame")
        if stem in model.sites:
            parent = model.sites[stem].owner + ".frame"
            if not visit(parent):
                return False
            if bodies[parent] is None:
                def read(stem=stem):
                    return ("partition_dynamic_site", stem, model.sites[stem].owner + ".frame")
                route = reference._recording_capture(read)
                if route is None or route.values[2] != parent:
                    return False
                add_receipts((route,))
                bodies[path] = None
                visiting.remove(path)
                return True
            body = reference._recording_attached_body(bodies[parent], ("site", stem), path=path)
            if body is None:
                return False
            values = body.receipts[-1].values
            node = _Node(path, "site", parent, _LocalPose(values[3], values[4]), body)
        elif stem in incoming:
            kind, relation = incoming[stem]
            graph = graph_receipts[(kind, relation)]
            parent = graph.values[2] if kind == "follow" else graph.values[2] + ".frame"
            if not visit(parent):
                return False
            if bodies[parent] is None:
                # Its complete relation receipt is retained below, including
                # inactive/unused edges. Only evaluation stays ordinary.
                bodies[path] = None
                visiting.remove(path)
                return True
            if kind == "follow":
                body = reference._recording_attached_body(bodies[parent], (kind, relation), path=path)
                if body is None or body.receipts[-1].values != graph.values:
                    return False
                values = graph.values
                node = _Node(path, kind, parent, _LocalPose(values[3], values[4]), body, relation)
            else:
                joint_kind = graph.values[1]
                if joint_kind == "hinge":
                    body = reference._recording_hinge_body(bodies[parent], relation, state, path=path)
                    if body is None or body.receipts[-2].values != graph.values:
                        return False
                elif joint_kind in {"fixed", "grip"}:
                    body = reference._recording_attached_body(bodies[parent], ("static_joint", relation), path=path)
                    if body is None:
                        return False
                    # Keep the graph receipt too: the fixed attachment's own
                    # source shape intentionally differs from a hinge record.
                    add_receipts((graph,))
                else:
                    return False
                node = _Node(path, joint_kind, parent, _LocalPose(graph.values[6], graph.values[7]),
                             body, relation, graph.values[4])
            used_relations.add((kind, relation))
        else:
            if partition and type(state.modes.get(stem)) is str and state.modes[stem] == "dynamic":
                def read(stem=stem):
                    return ("partition_dynamic_root", stem, int(stem in model.objects), state.modes[stem])
                route = reference._recording_capture(read)
                if route is None or not route.values[2] or route.values[3] != "dynamic":
                    return False
                add_receipts((route,))
                bodies[path] = None
                visiting.remove(path)
                return True
            def read(stem=stem):
                claim = state.claims.get((stem, "translation"))
                head = ("prescribed_root_translation", stem, int(stem in model.objects), state.modes[stem],
                        state.ideal_positions[stem], claim)
                if claim is None:
                    return head
                action, active = model.actions[claim], state.actions[claim]
                return (*head, action.kind, action.target, action.vector, active.ideal_initial,
                        active.status, active.elapsed, active.since)
            root = reference._recording_capture(read)
            if root is None or not root.values[2] or root.values[3] == "dynamic":
                return False
            values = root.values
            translation = _RootTranslation(values[4])
            if values[5] is not None:
                if (values[6] != "move" or values[7] != stem or
                        type(values[8]) is not tuple or len(values[8]) != 3 or
                        type(values[9]) is not tuple or len(values[9]) != 3):
                    return False
                translation = _RootTranslation(values[4], values[8], values[9], values[10],
                                               F(values[11]), F(values[12]))
            body = reference._recording_root_body(stem, state)
            if body is None:
                return False
            add_receipts((root,))
            node = _Node(path, "root", None, translation, body)
        if node.kind == "root":
            fixed = not body.moving and (translation.vector is None or
                    translation.status != "running" or not any(translation.vector))
        else:
            fixed = stationary[node.parent] and (node.kind != "hinge" or not body.coordinate_rate)
        source_fixed = stationary_source(node, fixed)
        node = replace(node, stationary=fixed, source_stationary=source_fixed)
        stationary[path] = fixed
        source_stationary[path] = source_fixed
        add_receipts(body.receipts)
        nodes.append(node)
        bodies[path] = body
        visiting.remove(path)
        return True

    for path in targets:
        if not visit(path):
            return None
    for relation, receipt in graph_receipts.items():
        if relation not in used_relations:
            add_receipts((receipt,))
    if (sum(node.kind == "hinge" or (node.kind == "root" and node.body.moving)
            for node in nodes) > MAX_CURSORS or
            not reference._recording_body_domain()):
        return None
    remaining = tuple(path for path in targets if bodies[path] is None)
    return _Plan(state, context, targets, tuple(nodes), tuple(receipts), owners, remaining)


def _phase_poses(reference, time, state, targets, context, batch=None, *, centered=False):
    """Return the optional plan's fresh frames, or the original-walk sentinel."""
    # A complete outer reader can plan prescribed ancestries independently
    # of released roots. Context-free, nested and centered requests retain
    # their original dynamic-source fallback.
    if (len(targets) > MAX_TARGETS or len(reference.model.objects) > 64 or
            len(reference.model.joints) > 32 or len(state.claims) > 128 or
            len(state.modes) > 64 or
            max(abs(time.numerator).bit_length(), time.denominator.bit_length()) > 1024):
        return None
    dynamic = any(mode == "dynamic" for mode in state.modes.values())
    partition = dynamic and not centered and batch is not None
    if dynamic and (not partition or reference.a._recording_after_tick is not None
                    or any(type(mode) is not str for mode in state.modes.values())
                    or any(type(path) is not str for path in targets)
                    or type(time) is not F or type(time.numerator) is not int
                    or type(time.denominator) is not int or time.denominator <= 0):
        return None
    plan = reference._recording_phase_plan
    if (plan is None or plan.state is not state or plan.context != context or
            plan.targets != targets or not plan.current(reference, batch)):
        reference._recording_phase_plan = None
        if not reference._recording_body_domain():
            return None
        plan = _build(reference, state, targets, context,
                      source_stationarity=batch is not None, partition=partition)
        if plan is None:
            return None
    if centered:
        if batch is None:
            return None
        from .reach_reference_center import _ChangedDomain, evaluate, prepare
        try:
            plan = prepare(plan, reference, batch)
        except _ChangedDomain:
            return None
        except ReferenceError as error:
            if (error.code != "resource" or error is getattr(reference.a.work, "callback_error", None)
                    or reference._recording_body_domain()):
                raise
            return None
        plan.admit_owners(reference)
        if not reference._recording_body_domain():
            return None
        # This is a captured source recipe, not a completed numeric pose.
        # Retain an unsupported recipe too so ordinary same-work fallback
        # does not recapture an unchanged complete source graph.
        reference._recording_phase_plan = plan
        if type(plan.centered) is not tuple:
            return None
    adopted = batch if batch is not None and batch.register(plan, time) else None
    if centered and adopted is None:
        return None
    if plan.remaining:
        if adopted is None:
            return None
        reference._recording_phase_plan = plan
        return _PartitionedPlan(plan, adopted, time, (time.numerator, time.denominator))
    if adopted is None:
        result = plan.evaluate(reference, time)
        if batch is not None and result is not None:
            batch.completed_ordinary_request()
    else:
        adopted.check_cursors()
        adopted.current_plan = plan
        try:
            result = (evaluate(plan, reference, time, adopted) if centered else
                      plan.evaluate(reference, time, adopted))
        finally:
            adopted.current_plan = None
    if result is not None:
        reference._recording_phase_plan = plan
    return result


def recording_phase_poses(reference, time, state, targets, context):
    batch = reference._recording_batch
    if batch is None or not batch.matches(context):
        return _phase_poses(reference, time, state, targets, context)
    batch.admit_owners()
    batch.depth += 1
    try:
        # A nested reader keeps its original source admission. The outer
        # pending publication and ledger must not overwrite its fresh cursor.
        return _phase_poses(reference, time, state, targets, context,
                            batch if batch.depth == 1 else None)
    finally:
        batch.depth -= 1


def recording_centered_poses(reference, time, state, targets, context):
    """Keep compact results private to an outer complete source batch."""
    batch = reference._recording_batch
    if batch is None or not batch.matches(context) or batch.depth:
        return None
    batch.admit_owners()
    batch.depth += 1
    try:
        return _phase_poses(reference, time, state, targets, context, batch, centered=True)
    finally:
        batch.depth -= 1


def recording_stationary_frames(reference, carriers, first, last, side):
    """Use an already registered source plan for a complete reader's reuse.

    The public caller has just executed its original entry checkpoint. Every
    selected source operand remains covered by the batch's final admission.
    Outside this small native domain, or without an already captured plan,
    return the ordinary graph walk sentinel without changing its behavior.
    """
    batch, plan = reference._recording_batch, reference._recording_phase_plan
    if (type(batch) is not _SourceBatch or not batch.active or batch.prepared or batch.depth != 0
            or type(plan) is not _Plan or not batch.contains(plan) or not batch.matches(plan.context)
            or not reference._recording_body_domain() or type(side) is not str or side != plan.context[-1]
            or type(carriers) not in (tuple, list) or len(carriers) > MAX_TARGETS
            or any(type(carrier) is not str for carrier in carriers)
            or type(first) is not F or type(last) is not F
            or any(max(abs(time.numerator).bit_length(), time.denominator.bit_length()) > 1024
                   for time in (first, last))):
        return None
    batch.admit_owners()
    plan.admit_owners(reference)
    selected = tuple(carrier if carrier == "world" or carrier.endswith(".frame")
                     else carrier + ".frame" for carrier in carriers)
    if len(selected) > 1 + len(reference.model.objects) + len(reference.model.sites):
        return None
    known = None
    # Later endpoint requests omit carriers whose preceding comparison is
    # already reusable. Their current pose plan can therefore omit a whole
    # stationary branch. The same bounded batch still owns the earlier full
    # plan and all of its source receipts: select one matching that exact
    # phase/context instead of asking for a new source walk or pose table.
    for candidate, _ in batch.plans.values():
        if (type(candidate) is not _Plan or candidate.state is not plan.state
                or candidate.context != plan.context):
            continue
        flags = {node.path: node.source_stationary for node in candidate.nodes}
        flags.update((path, False) for path in candidate.remaining)
        flags["world"] = True
        if all(carrier in flags and flags[carrier] is not None for carrier in selected):
            candidate.admit_owners(reference)
            known = flags
            break
    if known is None:
        return None
    if first > last:
        return None
    # Native immutable clocks and native bounded history containers were
    # admitted on batch entry. These reads have no work callback. Both sides
    # must select the captured state; a boundary or different side keeps the
    # original same-state rule, including its empty result.
    if (reference._state_at(first, side) is not plan.state
            or reference._state_at(last, side) is not plan.state):
        return None
    reference.a.guard(first, last)
    # Captured native time leaves need at most 1,075 bits. The omitted
    # elapsed subtraction/sum and original scalar guards fit below 4,302 bits
    # on this full-cap domain. Final receipt admission still checks all source
    # values and rejects source replacement before any domain restart.
    return frozenset(carrier for carrier in selected if known[carrier])
