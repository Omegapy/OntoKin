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

from .reach_reference import (
    MAX_BOUNDARIES, MAX_CACHE, MAX_OPERAND_BITS, PoseEnclosure, ReferenceError, ZERO, _RecordingBodyRate,
)


# Sufficient domains for this optional structural proof. Larger graphs retain
# the complete original walker and unchanged public resource allowances.
MAX_TARGETS = 64
MAX_NODES = 128
MAX_CURSORS = 32
MAX_BATCH_PLANS = 16
MAX_BATCH_RECEIPTS = 1024
_SOURCE_MAPS = ("objects", "sites", "joints", "follows", "actions")


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
            if key[3] == "recording_body_orientation":
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
    cache_identity: object = field(default_factory=object, compare=False)

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
                if node.kind == "hinge" and body.zero_origin and reference._recording_body_domain():
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
                    # In particular, a nonzero child origin or a Y-axis
                    # head retains both ordinary local compositions. A body
                    # orientation recipe never replaces its position proof.
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


def _build(reference, state, targets, context):
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

    def visit(path):
        if path in bodies:
            return True
        if path in visiting or len(nodes) + len(visiting) >= MAX_NODES:
            return False
        a.tick()
        visiting.add(path)
        stem = path.removesuffix(".frame")
        if stem in model.sites:
            parent = model.sites[stem].owner + ".frame"
            if not visit(parent):
                return False
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
        node = replace(node, stationary=fixed)
        stationary[path] = fixed
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
    return _Plan(state, context, targets, tuple(nodes), tuple(receipts), owners)


def _phase_poses(reference, time, state, targets, context, batch=None):
    """Return the optional plan's fresh frames, or the original-walk sentinel."""
    # Reject unimplemented dynamic root laws before capturing any recipes.
    # These bounded metadata predicates share the caller's entry admission;
    # no numeric operation or source-result read is hidden behind them.
    if (len(targets) > MAX_TARGETS or len(reference.model.objects) > 64 or
            len(reference.model.joints) > 32 or len(state.claims) > 128 or
            len(state.modes) > 64 or
            any(mode == "dynamic" for mode in state.modes.values()) or
            max(abs(time.numerator).bit_length(), time.denominator.bit_length()) > 1024):
        return None
    plan = reference._recording_phase_plan
    if (plan is None or plan.state is not state or plan.context != context or
            plan.targets != targets or not plan.current(reference, batch)):
        reference._recording_phase_plan = None
        if not reference._recording_body_domain():
            return None
        plan = _build(reference, state, targets, context)
        if plan is None:
            return None
    adopted = batch if batch is not None and batch.register(plan, time) else None
    if adopted is None:
        result = plan.evaluate(reference, time)
        if batch is not None and result is not None:
            batch.completed_ordinary_request()
    else:
        adopted.check_cursors()
        adopted.current_plan = plan
        try:
            result = plan.evaluate(reference, time, adopted)
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
