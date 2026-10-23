"""Bounded source-formula plans for the independent recording reader.

This module reads only the private source records and arithmetic of
``reach_reference``. It imports no production evaluator, sampler or numeric
kernel. A plan holds source operands and source-derived affine recipes, never
a second table of completed numeric poses. Every request rechecks its own
source receipts; all cursor values remain in the existing 256-entry cache.
"""
from dataclasses import dataclass, field, replace
from fractions import Fraction as F

from .reach_reference import (
    MAX_CACHE, PoseEnclosure, ReferenceError, ZERO, _RecordingBodyRate,
)


# Sufficient domains for this optional structural proof. Larger graphs retain
# the complete original walker and unchanged public resource allowances.
MAX_TARGETS = 64
MAX_NODES = 128
MAX_CURSORS = 32
_SOURCE_MAPS = ("objects", "sites", "joints", "follows", "actions")


def _owners(reference):
    """Strong owner identities, separate from equality of source operands."""
    return (reference.model, reference.a, reference.p, reference.p.a,
            reference.a.work, reference.a.check,
            *(getattr(reference.model, name) for name in _SOURCE_MAPS))


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

    def current(self, reference):
        # Each unique actual source record is freshly read under a charged
        # callback. The captured immutable recipe is used only if it matches.
        # Final admission below rechecks the whole batch after all callbacks.
        if not self.owned_by(reference):
            return False
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

    def evaluate(self, reference, time):
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

        for _ in self.receipts:
            a.tick()
        self.admit_owners(reference)
        if not reference._recording_body_domain():
            return None
        reference._recording_admit_receipts(self.receipts)
        for value in frames.values():
            guard(value)
        pending.publish()
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


def recording_phase_poses(reference, time, state, targets, context):
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
            plan.targets != targets or not plan.current(reference)):
        reference._recording_phase_plan = None
        if not reference._recording_body_domain():
            return None
        plan = _build(reference, state, targets, context)
        if plan is None:
            return None
    result = plan.evaluate(reference, time)
    if result is not None:
        reference._recording_phase_plan = plan
    return result
