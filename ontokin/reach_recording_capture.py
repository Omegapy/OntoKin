"""Complete immutable inputs for repeated constant-parent recording carriers.

The optional graph contains source operands and structural receipts only.
Completed parent transforms and carrier cursors use the existing work LRU.
A captured phase retains its bounded working parents and latest private
cursor group until all of its ordinary output callbacks have completed.
No producer receipt is available to the independent supplied-byte reader.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from math import isfinite
from types import MappingProxyType

from .model import Pose
from .reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, rational
from .reach_pose import PoseValue, RotationValue, SpinPlan
from .reach_phase import (AnchorError, PhaseBound, RecordingAngularFrame, RecordingAngularProof, _AxialRate,
                          _current_recording_angular_witness,
                          current_recording_angular_witness, _recording_orientation_recipe)


@dataclass(frozen=True)
class _CoordinateInputs:
    initial: object
    target: object
    duration: F
    elapsed: F
    running_since: F
    running: bool


@dataclass(frozen=True)
class _RootLaw:
    initial: object
    vector: tuple
    elapsed: F
    running_since: F
    running: bool


@dataclass(frozen=True)
class _SpinInputs:
    original: SpinPlan
    copied: SpinPlan


@dataclass(frozen=True)
class _DynamicReceipt:
    identities: tuple
    witness: tuple
    force_sizes: tuple


@dataclass(frozen=True)
class _DynamicInputs:
    receipt: _DynamicReceipt
    anchor_time: F
    duration: F
    position: tuple
    velocity: tuple
    rotation: object
    omega: tuple
    acceleration: tuple
    spin: _SpinInputs | None


@dataclass(frozen=True)
class _Node:
    frame: str
    kind: str
    path: str
    record: RecordingAngularFrame | None
    identities: tuple
    operands: tuple
    constant: bool
    recipe: tuple
    static_recipe: tuple | None
    local_constant: bool


@dataclass(frozen=True)
class _Graph:
    model: object
    state: object
    root_state: object
    original_proof: RecordingAngularProof
    proof: RecordingAngularProof
    selected: tuple
    nodes: MappingProxyType
    topology_extra: tuple
    topology_sizes: tuple
    active_grips: frozenset
    static_carriers: bool
    spin_plans: MappingProxyType


def _identity(table, path, value):
    if (type(value.path) is not str or type(value.element_id) is not tuple
            or any(type(part) is not str for part in value.element_id)
            or getattr(value, "owner", None) is not None
                and type(value.owner) is not str):
        raise TypeError("A captured source identity must be immutable.")
    return (table, path, value, value.path, value.element_id, getattr(value, "owner", None))


def _same_identity(model, receipt):
    table, path, expected, name, element_id, owner = receipt
    current = getattr(model, table).get(path)
    return (current is expected and type(current.path) is str and current.path == name
            and current.element_id == element_id
            and type(current.element_id) is tuple
            and all(type(part) is str for part in current.element_id)
            and (getattr(current, "owner", None) is None or type(current.owner) is str)
            and getattr(current, "owner", None) == owner)


def _immutable_witness(value, work):
    pending, count = [(value, 0)], 0
    while pending:
        current, depth = pending.pop()
        if count % 32 == 0:
            work.charge("recording_captured_witness_block")
        count += 1
        if count > 512 or depth > 8:
            return False
        if type(current) is tuple:
            if len(current) > 32:
                return False
            pending.extend((part, depth + 1) for part in current)
        elif current is not None and type(current) not in (int, str):
            return False
    return True


def _topology_record(model, kind, path):
    value = (model.joints if kind == "joint" else model.follows)[path]
    if (type(path) is not str or type(value.path) is not str or value.path != path
            or type(value.parent) is not str or type(value.child) is not str
            or kind == "joint" and (type(value.kind) is not str
                or type(model.sites[value.child].owner) is not str)):
        raise TypeError("A captured topology edge must have immutable source names.")
    return (kind, path, value, value.kind if kind == "joint" else None,
            value.parent, value.child,
            model.sites[value.child].owner if kind == "joint" else value.child)


def _coordinate_inputs(model, state, path):
    claimant = state.claims.get((path, "coordinate"))
    if claimant is None:
        return None, state.coordinates[path]
    action, active = model.actions[claimant], state.actions[claimant]
    if action.kind == "reach_planar":
        if path not in (action.reach.shoulder, action.reach.elbow):
            return None, None
        index = 0 if path == action.reach.shoulder else 1
        initial, target = active.initial[index], active.solution.target_rad[index]
    elif action.kind == "tween":
        initial, target = active.initial, action.goal
    else:
        return None, None
    return _CoordinateInputs(initial, target, action.duration, active.elapsed,
                             active.running_since, active.status == "running"), None


def _root_law(model, state, path, channel):
    claimant = state.claims.get((path, channel))
    if claimant is None:
        return None
    action, active = model.actions[claimant], state.actions[claimant]
    if (action.kind != ("move" if channel == "translation" else "spin")
            or action.target != path or active.status not in {"running", "paused"}
            or type(active.elapsed) is not F or type(active.running_since) is not F):
        raise TypeError("A captured root needs an admitted move or spin law.")
    initial = ((active.initial_rotation or active.initial)
               if channel == "orientation" else active.initial)
    if type(initial) is RotationValue:
        initial = RotationValue(initial.components, initial.error_rad, initial.frozen_projection)
    return _RootLaw(initial, action.vector, active.elapsed, active.running_since,
                    active.status == "running")


def _spin_inputs(law, ops):
    if law is None or not any(law.vector):
        return None
    plan = ops.work.lookup(("reach_source_spin_phase", law.vector))
    ops._require_domain()
    if not ops._reusable_spin_plan(plan):
        raise TypeError("A captured spin needs its complete source phase plan.")
    copied = SpinPlan(plan.scaled_omega, plan.maximum, plan.norm_bounds,
        plan.pi_bounds, plan.max_elapsed_s, plan.precision_bits, plan.argument_error_rad)
    return _SpinInputs(plan, copied)


def _elapsed(law, time, ops):
    if not law.running:
        ops.work.guard(law.elapsed)
        return law.elapsed
    op = ops.source_ops._op
    return op(law.elapsed, op(time, law.running_since, "sub"), "add")


def _root_pose(node, time, ops, context, publication):
    from .reach_recording_fast import METHOD
    from .scene import MAX_KEYFRAMES

    position, rotation, move, spin, plan = node.operands
    if move is not None:
        position = ops.recording_affine(move.initial, move.vector, _elapsed(move, time, ops))
    if spin is not None:
        rotation = ops.recording_advance_orientation(spin.initial, spin.vector,
            _elapsed(spin, time, ops), context=context,
            path=METHOD + ":prescribed:" + node.path, max_steps=MAX_KEYFRAMES,
            phase_plan=None if plan is None else plan.copied,
            stage_cursor=publication.stage, read_cursor=getattr(publication, "read_cursor", None))
    return ops.make_recording(position=position, orientation=rotation)


def _dynamic_source(simulator, state, path, ops, force_sizes, *, copy_initial=False):
    """Snapshot actual dynamic inputs without callbacks or angular authority.

    Only fixed-size numeric fields and the precharged bounded force rows are
    read. Projection caches are copied before any projection callback; their
    canonical values are checked by the original source helper on that copy.
    The complete live snapshot is compared again before cursor publication.
    """
    from .evaluator import _DynamicInitial, _Kinematics
    from .force_runtime import _ActiveForce, _ForceState
    from .model import ForcePayload

    work, model = ops.work, simulator.model

    def freeze(value):
        if value is None or type(value) is str:
            return (type(value), value)
        if type(value) is float and isfinite(value):
            work.guard_bits(1075)
            return (float, value.hex())
        if type(value) in (F, int):
            work.guard(value)
            return (type(value), value.numerator, value.denominator)
        raise TypeError("A captured dynamic input needs a canonical scalar.")

    def vector(value, size):
        if type(value) is not tuple or len(value) != size:
            raise TypeError("A captured dynamic vector must be immutable and fixed-size.")
        return tuple(freeze(part) for part in value)

    def rotation(value):
        if type(value) is not RotationValue or type(value.error_rad) is not F:
            raise TypeError("A captured dynamic private rotation must be immutable.")
        return (vector(value.components, 4), freeze(value.error_rad),
                None if value.frozen_projection is None else vector(value.frozen_projection, 4))

    if (state.modes[path] != "dynamic"
            or state.claims.get((path, "translation")) is not None
            or state.claims.get((path, "orientation")) is not None):
        raise TypeError("A captured dynamic root must be free of prescribed claims.")
    anchor, history = state.dynamic[path], state.forces[path]
    if (type(anchor) is not _DynamicInitial or type(anchor.time) is not F
            or type(anchor.since) is not F or type(model.duration) is not F
            or type(history) is not _ForceState or type(history.active) is not dict
            or type(history.last_changes) is not list
            or (len(history.active), len(history.last_changes)) != force_sizes):
        raise TypeError("A captured dynamic root needs its actual bounded source history.")
    initial, error = anchor.state, state.dynamic_errors.get(path)
    if error is not None and type(error) is not AnchorError:
        raise TypeError("A captured dynamic root needs its actual source anchor errors.")
    identities = [anchor, initial, history, error]
    fields = ("position", "orientation", "velocity", "omega")
    if type(initial) is PoseValue:
        if initial._ops is not ops.source_ops or type(initial._projection) is not dict:
            raise TypeError("A captured dynamic anchor belongs to this source arithmetic.")
        values = (initial.exact_position, initial.rotation, initial.exact_velocity,
                  initial.exact_omega, initial.position_error_m)
        projections = dict(initial._projection)
        if len(projections) > 4 or set(projections) - set(fields):
            raise TypeError("A captured dynamic anchor has only its public projection fields.")
        projected = tuple((field, vector(projections[field], 4 if field == "orientation" else 3))
                          for field in fields if field in projections)
        initial_witness = ("private", vector(values[0], 3), rotation(values[1]),
            vector(values[2], 3), vector(values[3], 3), freeze(values[4]), projected)
        if copy_initial:
            value = values[1]
            initial = PoseValue(values[0], RotationValue(value.components, value.error_rad,
                value.frozen_projection), values[2], values[3], values[4], ops.source_ops, projections)
    elif type(initial) is _Kinematics:
        values = tuple(getattr(initial, field) for field in fields)
        initial_witness = ("native", *(vector(value, 4 if index == 1 else 3)
                                      for index, value in enumerate(values)))
        if copy_initial:
            initial = _Kinematics(*values)
    else:
        raise TypeError("An unsupported dynamic anchor retains ordinary sampling.")

    def force(value):
        if type(value) is not _ActiveForce or type(value.payload) is not ForcePayload:
            raise TypeError("A captured force row must be an actual source activation.")
        identities.extend((value, value.payload))
        payload = value.payload
        return (freeze(value.target), freeze(value.activation), freeze(payload.key),
                vector(payload.force_world_n, 3), freeze(payload.duration), freeze(payload.sequence_index))

    active = tuple((freeze(key), force(value)) for key, value in history.active.items())
    changes = []
    for row in history.last_changes:
        if type(row) is not tuple or len(row) != 2:
            raise TypeError("A captured force change must retain its actual source row.")
        changes.append((freeze(row[0]), force(row[1])))
    acceleration = model.gravity if history.acceleration is None else history.acceleration
    error_values = error if error is not None else AnchorError()
    witness = (freeze(model.duration), vector(model.gravity, 3), freeze(state.modes[path]),
        freeze(anchor.time), freeze(anchor.since), initial_witness,
        vector(history.net, 3), None if history.acceleration is None else vector(history.acceleration, 3),
        freeze(history.started_count), freeze(history.completed_count), freeze(history.last_time),
        active, tuple(changes), tuple(freeze(getattr(error_values, field)) for field in (
            "position_m", "rotation_rad", "velocity_m_per_s", "angular_velocity_rad_per_s")),
        freeze(state.dynamic_error_times[path]), vector(state.ideal_accelerations[path], 3),
        freeze(model.objects[path].mass))
    receipt = _DynamicReceipt(tuple(identities), witness, force_sizes)
    return receipt, initial, anchor.time, model.duration, acceleration


def _dynamic_inputs(simulator, state, path, ops):
    history = state.forces[path]
    sizes = (len(history.active), len(history.last_changes))
    if sum(sizes) > ops.work.max_cache_entries:
        raise TypeError("An oversized dynamic source history retains ordinary sampling.")
    ops.work.charge("recording_captured_dynamic_input", sum(sizes) + 1)
    ops._require_domain()
    receipt, initial, anchor_time, duration, acceleration = _dynamic_source(
        simulator, state, path, ops, sizes, copy_initial=True)
    # No live source field is read below. These public anchor values are the
    # same operands used by recording_dynamic_pose, projected once from the
    # copied materialized anchor with its original source arithmetic.
    position, velocity, omega = initial.position, initial.velocity, initial.omega
    rotation = initial.rotation if type(initial) is PoseValue else initial.orientation
    components = rotation.components if type(rotation) is RotationValue else rotation
    if components[1] or components[2] or omega[0] or omega[1]:
        raise TypeError("A captured dynamic root requires scalar/Z rotation and spin.")
    spin = _spin_inputs(_RootLaw(rotation, omega, F(0), anchor_time, True), ops)
    return _DynamicInputs(receipt, anchor_time, duration, position, velocity,
                          rotation, omega, acceleration, spin)


def _dynamic_pose(node, time, ops, context, publication, phase):
    from .reach_recording_fast import METHOD, _FloatPose
    from .scene import MAX_KEYFRAMES

    inputs = node.operands[0]
    ops.work.charge("recording_dynamic_clock_domain")
    ops._require_domain()
    ops._immutable_scalar_domain((time,), small=True)
    elapsed = ops.source_ops._op(time, inputs.anchor_time, "sub")
    # Exact ordering was proved by the complete phase clock preflight. The
    # original ballistic helper retains the anchor/horizon/extent proof and
    # the actual elapsed clock's small domain before each native operation.
    law = ops._ballistic_law(inputs.position, inputs.velocity, inputs.acceleration,
        anchor_time=inputs.anchor_time, phase_interval=phase,
        root_extent=publication.bound_inputs[node.frame][3], context=context,
        path=node.path, scene_duration=inputs.duration)
    position, zeros = ops._ballistic_position(law, elapsed)
    orientation = ops.recording_advance_orientation(inputs.rotation, inputs.omega, elapsed,
        context=context, path=METHOD + ":dynamic:" + node.path, max_steps=MAX_KEYFRAMES,
        phase_plan=None if inputs.spin is None else inputs.spin.copied,
        stage_cursor=publication.stage, read_cursor=publication.read_cursor)
    ops._rotation_domain(orientation)
    ops._require_domain()
    ops.dynamic_extents[node.path] = law
    return _FloatPose(position, orientation, zeros, 0)


def _capture(simulator, state, selected, proof, ops, *, varying_parents=False,
             maximum_nodes=None):
    """Capture prescribed roots and complete planar dependencies from frozen operands."""
    model, work, root_state = simulator.model, simulator.work, simulator.state
    sizes = (len(model.objects), len(model.sites), len(model.joints), len(model.follows))
    grip_count = len(state.active_grips)
    work.charge("recording_captured_topology", sizes[2] + sizes[3] + grip_count + 1)
    ops._require_domain()
    if (sizes != (len(model.objects), len(model.sites), len(model.joints), len(model.follows))
            or grip_count != len(state.active_grips)):
        return None
    # After all topology callbacks, this snapshot and its incoming index are
    # read together without another callback. Every row is read again at the
    # final receipt, either as a full source witness or as an unused edge.
    try:
        topology = tuple(_topology_record(model, "joint", path) for path in model.joints)
        topology += tuple(_topology_record(model, "follow", path) for path in model.follows)
        active_grips = frozenset(state.active_grips)
        incoming = {row[6]: (row[0], row[1]) for row in topology
                    if row[0] != "joint" or row[3] != "grip" or row[1] in active_grips}
    except (KeyError, AttributeError, TypeError):
        return None
    nodes, visiting, used_edges = {}, set(), set()

    def visit(frame):
        if frame in nodes:
            return nodes[frame]
        # The native arithmetic already has a 64-composition ceiling. A
        # deeper optional capture is rejected before unbounded recursion.
        if (type(frame) is not str or frame in visiting or len(visiting) > 64
                or maximum_nodes is not None and len(nodes) + len(visiting) >= maximum_nodes):
            return None
        work.charge("recording_body_witness")
        ops._require_domain()
        # Copy only required fixed-size records, never an arbitrarily large
        # externally supplied backing map. Already captured records survive a
        # temporary mutation of the caller's MappingProxyType backing dict.
        record = proof.frames.get(frame)
        try:
            stem = frame[:-6] if frame.endswith(".frame") else None
            if (varying_parents and stem in model.objects and stem not in incoming
                    and state.modes[stem] == "dynamic"):
                # The phase angular proof deliberately has no dynamic lineage.
                # Only an actual selected free root gets a separate complete
                # anchor receipt; no descendant can use it as a body proof.
                if frame not in selected or record is not None:
                    return None
                identities = (_identity("objects", stem, model.objects[stem]),)
                inputs = _dynamic_inputs(simulator, state, stem, ops)
                node = _Node(frame, "dynamic", stem, None, identities, (inputs,),
                             False, (), None, False)
                nodes[frame] = node
                return node
        except (KeyError, AttributeError, TypeError, IndexError):
            return None
        if (type(record) is not RecordingAngularFrame or type(record.rate) is not _AxialRate
                or type(record.rate.value) is not F or type(record.trig_count) is not int
                or record.trig_count < 0
                or record.rate.axis is not None and (type(record.rate.axis) is not int or record.rate.axis != 2)
                or record.rate.value and not record.trig_count
                or type(record.token) is not object
                or record.parent is not None and type(record.parent) is not str
                or not _immutable_witness(record.witness, work)):
            return None
        work.guard(record.rate.value, record.trig_count)
        try:
            if frame == "world":
                kind, path, identities = "world", "world", ()
            elif frame.endswith(".frame") and frame[:-6] in model.objects:
                stem = frame[:-6]
                kind, path = incoming.get(stem, ("root", stem))
                identities = (_identity("objects", stem, model.objects[stem]),)
            elif frame.endswith(".frame") and frame[:-6] in model.sites:
                kind, path = "site", frame[:-6]
                identities = ()
            else:
                return None
            current = current_recording_angular_witness(model, state, kind, path, work=work)
            ops._require_domain()
            if current != (record.parent, record.witness):
                return None
            # No callback occurs between the witness comparison and binding
            # these immutable inputs. Later arithmetic never reads live fields.
            local_constant = True
            if kind == "world":
                operands = ()
            elif kind == "root":
                if state.modes[path] == "dynamic":
                    return None
                move = _root_law(model, state, path, "translation")
                spin = _root_law(model, state, path, "orientation")
                position = state.positions[path]
                rotation = state.root_rotation_values.get(path, state.orientations[path])
                if type(rotation) is RotationValue:
                    rotation = RotationValue(rotation.components, rotation.error_rad, rotation.frozen_projection)
                components = rotation.components if type(rotation) is RotationValue else rotation
                if components[1] or components[2]:
                    return None
                if spin is not None:
                    initial = spin.initial.components if type(spin.initial) is RotationValue else spin.initial
                    if initial[1] or initial[2] or spin.vector[0] or spin.vector[1]:
                        return None
                local_constant = not any(law is not None and law.running and any(law.vector)
                                         for law in (move, spin))
                # Source operands above are captured before this cache callback.
                # Every later calculation uses the copied plan and laws; final
                # admission still compares the complete current source witness.
                plan = _spin_inputs(spin, ops)
                operands = (position, rotation, move, spin, plan)
            elif kind == "site":
                site = model.sites[path]
                identities += (_identity("sites", path, site),)
                operands = (site.pose,)
            elif kind == "follow":
                value = model.follows[path]
                identities += (_identity("follows", path, value),)
                operands = (value.offset,)
                used_edges.add((kind, path))
            else:
                joint = model.joints[path]
                child = model.sites[joint.child]
                identities += (_identity("joints", path, joint),
                               _identity("sites", joint.child, child))
                if joint.kind not in {"hinge", "rigid", "grip"}:
                    return None
                law, coordinate = (_coordinate_inputs(model, state, path)
                                   if joint.kind == "hinge" else (None, None))
                if joint.kind == "hinge":
                    if (type(joint.axis) is not tuple or len(joint.axis) != 3
                            or joint.axis[0] or joint.axis[1] or not joint.axis[2]
                            or law is None and coordinate is None):
                        return None
                    local_constant = law is None or law.initial == law.target
                    if not local_constant and not law.running:
                        return None
                operands = (joint.kind, joint.axis, child.pose, law, coordinate)
                used_edges.add((kind, path))
            if kind in {"site", "follow", "joint"}:
                local = operands[2] if kind == "joint" else operands[0]
                if (type(local) is not Pose or type(local.position) is not tuple
                        or type(local.rotation) is not tuple or local.rotation[1] or local.rotation[2]):
                    return None
                if (kind == "joint" and not local_constant
                        and (len(local.position) != 3
                             or any(type(value) is not float or value != 0.0 for value in local.position))):
                    # A varying hinge uses the existing independent complete
                    # body cursor. Nonzero child offsets retain the ordinary
                    # local-factor sampler and its own cursor publication.
                    return None
        except (KeyError, AttributeError, TypeError, IndexError):
            return None
        visiting.add(frame)
        try:
            parent = visit(record.parent) if record.parent is not None else None
        finally:
            visiting.remove(frame)
        if record.parent is not None and (parent is None or parent.kind == "dynamic"
                or not parent.constant and not varying_parents):
            return None
        recipe = _recording_orientation_recipe(record, parent.recipe if parent else None, work=work)
        ops._require_domain()
        if recipe is None:
            return None
        constant = local_constant and (parent is None or parent.constant)
        static_recipe = ((record.witness, parent.static_recipe if parent else None)
                         if constant else None)
        node = _Node(frame, kind, path, record, identities, operands, constant,
                     recipe, static_recipe, local_constant)
        nodes[frame] = node
        return node

    static_carriers = True
    for frame in selected:
        node = visit(frame)
        if node is None or node.constant:
            return None
        static_leaf = (node.kind == "joint" and node.operands[0] == "hinge"
            and not node.local_constant and node.record.parent is not None
            and nodes[node.record.parent].constant)
        if not static_leaf:
            static_carriers = False
            if not varying_parents:
                return None
    captured_proof = RecordingAngularProof(proof.start, proof.end, proof.program_revision,
        MappingProxyType({path: node.record for path, node in nodes.items() if node.record is not None}))
    return _Graph(model, state, root_state, proof, captured_proof, selected,
                  MappingProxyType(nodes), tuple(row for row in topology if row[:2] not in used_edges),
                  sizes, active_grips, static_carriers,
                  MappingProxyType({node.frame: node.operands[4].copied
                      for node in nodes.values() if node.kind == "root" and node.operands[4] is not None}))


class _Publication:
    def __init__(self, simulator, graph, ops):
        self.simulator, self.graph, self.ops = simulator, graph, ops
        self.pending = []
        self.capacity = ops.work.max_cache_entries

    def stage(self, key, previous, value):
        self.ops.work.charge("recording_body_cursor_stage")
        self.ops._require_domain()
        if (self.ops.work.max_cache_entries != self.capacity
                or len(self.pending) >= self.capacity):
            from .reach_recording_fast import _UnsupportedPlanar
            self.pending.clear()
            raise _UnsupportedPlanar("The pending carrier group exceeds its current cache domain.")
        self.pending.append((key, previous, value))

    def admit(self):
        graph, simulator, work = self.graph, self.simulator, self.ops.work
        self.ops._require_domain()
        model, state, proof = graph.model, graph.state, graph.original_proof
        valid = (simulator.model is model and simulator.state is graph.root_state
                 and simulator.pose_ops is self.ops.source_ops and simulator.work is work
                 and model.program_revision == graph.proof.program_revision
                 and type(proof.frames) is MappingProxyType
                 and proof.start == graph.proof.start and proof.end == graph.proof.end
                 and proof.program_revision == graph.proof.program_revision
                 and graph.topology_sizes == (len(model.objects), len(model.sites),
                                              len(model.joints), len(model.follows))
                 and frozenset(state.active_grips) == graph.active_grips)
        if valid:
            for node in graph.nodes.values():
                if (proof.frames.get(node.frame) is not node.record
                        or not all(_same_identity(model, item) for item in node.identities)):
                    valid = False
                    break
                plan = None
                if node.kind == "dynamic":
                    expected = node.operands[0].receipt
                    try:
                        current = _dynamic_source(simulator, state, node.path, self.ops,
                                                  expected.force_sizes)[0]
                        valid = (current.witness == expected.witness
                            and len(current.identities) == len(expected.identities)
                            and all(a is b for a, b in zip(current.identities, expected.identities)))
                    except (KeyError, AttributeError, TypeError, IndexError):
                        valid = False
                    plan = node.operands[0].spin
                else:
                    valid = (_current_recording_angular_witness(model, state, node.kind, node.path,
                        work=work) == (node.record.parent, node.record.witness))
                    if node.kind == "root":
                        plan = node.operands[4]
                if not valid:
                    break
                if plan is not None:
                    if (not self.ops._reusable_spin_plan(plan.original)
                            or plan.original != plan.copied):
                        valid = False
                        break
        if valid:
            try:
                for row in graph.topology_extra:
                    current = _topology_record(model, row[0], row[1])
                    if current[2] is not row[2] or current[:2] + current[3:] != row[:2] + row[3:]:
                        valid = False
                        break
            except (KeyError, AttributeError, TypeError):
                valid = False
        if not valid:
            raise ReachAdmissionError("reach_domain", "The captured carrier source changed during sampling.")
        return True

    def finish(self):
        work = self.ops.work
        # One charge per actual complete record, plus every otherwise unused
        # topology edge. There is no repeated common-ancestor comparison.
        work.charge("recording_angular_witness_guard", len(self.graph.nodes))
        dynamic_rows = sum(sum(node.operands[0].receipt.force_sizes) + 1
                           for node in self.graph.nodes.values() if node.kind == "dynamic")
        if dynamic_rows:
            work.charge("recording_captured_dynamic_guard", dynamic_rows)
        work.charge("recording_captured_topology_guard", len(self.graph.topology_extra)
                    + len(self.graph.active_grips) + 1)
        self.ops._require_domain()
        admitted = False

        def receipt():
            nonlocal admitted
            self.admit()
            admitted = True
            # A callback earlier in the graph may have completed a newer
            # cursor for this same key. Preserve that reentrant result even
            # when it predates remember_batch's own generation snapshot.
            return all(work._cache.get(key) is previous for key, previous, _ in self.pending)

        if work.max_cache_entries != self.capacity:
            self.pending.clear()
            self.admit()
            return
        work.remember_batch(tuple((key, value) for key, _, value in self.pending), admission=receipt)
        self.ops._require_domain()
        if work.max_cache_entries != self.capacity:
            self.pending.clear()
        if not admitted:
            receipt()


def _capture_graph(simulator, time, state, selected, proof, ops, *, minimum_selected,
                   varying_parents=False):
    from .reach_recording_fast import METHOD
    work = ops.work
    if (len(selected) < minimum_selected or len(selected) > work.max_cache_entries
            or type(proof) is not RecordingAngularProof or type(proof.frames) is not MappingProxyType
            or type(proof.start) is not F or type(proof.end) is not F
            or proof.program_revision != simulator.model.program_revision):
        return None
    work.charge("recording_captured_graph_domain")
    ops._require_domain()
    time = rational(time, work)
    work.guard(proof.start, proof.end)
    from .reach_recording_fast import _checked_compare
    if (_checked_compare(proof.start, time, work) > 0
            or _checked_compare(time, proof.end, work) > 0):
        return None
    key = (METHOD, "captured_carrier_graph", MAX_OPERAND_BITS, id(simulator.model),
           id(state), id(proof), selected)
    graph = work.lookup(key)
    ops._require_domain()
    if type(graph) is not _Graph:
        graph = _capture(simulator, state, selected, proof, ops, varying_parents=varying_parents,
                         maximum_nodes=work.max_cache_entries if varying_parents else None)
        if graph is None:
            return None
        work.remember(key, graph)
        ops._require_domain()
    if (not varying_parents and not graph.static_carriers
            or varying_parents and len(graph.nodes) > work.max_cache_entries):
        return None
    # The graph has captured every relevant claim. A constant unclaimed hinge
    # must not consult the ordinary callback that reads the live source again.
    ops.constant_hinge_check = None
    ops.constant_hinges = frozenset("hinge:" + node.path for node in graph.nodes.values()
                                   if node.kind == "joint" and node.local_constant)
    return graph, time


def _sample_graph(graph, time, ops, context, publication, *, parents=None):
    from .reach_recording_fast import (METHOD, _FloatPose, _UnsupportedPlanar,
                                       captured_recording_orientation)
    from .scene import MAX_KEYFRAMES

    work = ops.work
    frames, shared = {}, {}

    def source_constant(pose, *, inverse=False):
        return (ops.source_ops.inverse_pose(pose) if inverse else ops.source_ops.constant_pose(pose))

    def constant(frame):
        if frame in frames:
            return frames[frame]
        node = graph.nodes[frame]
        if not node.constant:
            raise _UnsupportedPlanar("A captured carrier parent must be constant throughout its phase.")
        if node.kind == "world":
            value = ops.make_recording()
        elif node.kind == "root":
            value = _root_pose(node, time, ops, context, publication)
        else:
            parent = constant(node.record.parent)
            if node.kind in {"site", "follow"}:
                local = node.operands[0]
                build = lambda base=parent: ops.compose_recording_fast(base,
                    ops.recording_constant_pose(local, build=source_constant))
                signature = ((parent, local) if node.kind == "site" else ("follow", parent, local))
            else:
                kind, axis, local, law, coordinate = node.operands
                if kind == "hinge" and law is not None:
                    # Prove both phase endpoints before omitting later clock
                    # arithmetic. Identical endpoints make the entire admitted
                    # affine law constant; this cache key includes that law.
                    for clock in (graph.proof.start, graph.proof.end):
                        coordinate = ops.recording_affine_coordinate(law.initial, law.target, law.duration,
                            law.elapsed, law.running_since, clock, running=law.running)
                def build(base=parent):
                    relative = ops.make_recording()
                    if kind == "hinge":
                        rotation = ops.recording_axis_rotation(axis, coordinate, context=context,
                            path="hinge:" + node.path, max_steps=MAX_KEYFRAMES)
                        relative = ops.make_recording(orientation=rotation)
                    return ops.compose_recording_fast(ops.compose_recording_fast(base, relative),
                        ops.recording_constant_pose(local, inverse=True, build=source_constant))
                signature = ("joint", parent, kind, axis, coordinate, F(0) if kind == "hinge" else None, local)
            value = ops.recording_relative_pose(signature, build, context=context,
                path=node.path, max_steps=MAX_KEYFRAMES)
            if value is None:
                value = build()
        frames[frame] = value
        return value

    for index, frame in enumerate(graph.selected):
        node = graph.nodes[frame]
        if parents is not None and index < len(parents):
            # These are already required immutable operands of this phase's
            # output stream, in selected order. They are not a new keyed cache.
            # recording_parent_origin still checks each actual occurrence.
            parent = parents[index]
        else:
            parent_node = graph.nodes[node.record.parent]
            parent_key = (METHOD, "captured_constant_parent", MAX_OPERAND_BITS,
                          graph.proof.start, graph.proof.end, parent_node.static_recipe)
            parent = work.lookup(parent_key)
            ops._require_domain()
            if type(parent) is not _FloatPose:
                parent = constant(node.record.parent)
                work.remember(parent_key, parent)
                ops._require_domain()
            if parents is not None:
                parents.append(parent)
        representative = shared.get(node.recipe)
        if representative is None:
            rotation = ops.recording_body_orientation(lambda: captured_recording_orientation(
                ops.source_ops, graph.proof, frame, time, spin_plans=graph.spin_plans), node.record.rate.axis,
                node.record.rate.value, time, phase_start=graph.proof.start, phase_end=graph.proof.end,
                context=context, path="carrier:" + frame[:-6], proof_token=node.record.token,
                max_steps=MAX_KEYFRAMES, stage_cursor=publication.stage,
                read_cursor=getattr(publication, "read_cursor", None))
        else:
            work.charge("recording_body_shared_orientation")
            ops._require_domain()
            rotation = frames[representative].rotation
            ops._rotation_domain(rotation)
        frames[frame] = ops.recording_parent_origin(parent, rotation)
        shared.setdefault(node.recipe, frame)
    return frames


def _sample_chain_graph(graph, time, ops, context, publication, constants):
    """Evaluate varying ancestors in the original native composition order.

    A moving parent origin is recomputed at every key. Only complete poses
    proved constant throughout this source phase survive in the working set.
    The source proof independently seeds each varying hinge's complete body
    orientation; an approximate parent never seeds that recurrence.
    """
    from .reach_recording_fast import captured_recording_orientation
    from .scene import MAX_KEYFRAMES

    work, frames, shared = ops.work, {}, {}

    def source_constant(pose, *, inverse=False):
        return (ops.source_ops.inverse_pose(pose) if inverse else ops.source_ops.constant_pose(pose))

    def resolve(frame):
        if frame in frames:
            return frames[frame]
        node = graph.nodes[frame]
        if node.constant and frame in constants:
            work.charge("recording_captured_constant_reuse")
            ops._require_domain()
            value = constants[frame]
        elif node.kind == "world":
            value = ops.make_recording()
        elif node.kind == "root":
            value = _root_pose(node, time, ops, context, publication)
        elif node.kind == "dynamic":
            value = _dynamic_pose(node, time, ops, context, publication,
                                  (graph.proof.start, graph.proof.end))
        else:
            parent = resolve(node.record.parent)
            if node.kind == "joint" and not node.local_constant:
                representative = shared.get(node.recipe)
                if representative is None:
                    rotation = ops.recording_body_orientation(lambda: captured_recording_orientation(
                        ops.source_ops, graph.proof, frame, time, spin_plans=graph.spin_plans), node.record.rate.axis,
                        node.record.rate.value, time, phase_start=graph.proof.start,
                        phase_end=graph.proof.end, context=context, path="carrier:" + frame[:-6],
                        proof_token=node.record.token, max_steps=MAX_KEYFRAMES,
                        stage_cursor=publication.stage, read_cursor=publication.read_cursor)
                else:
                    work.charge("recording_body_shared_orientation")
                    ops._require_domain()
                    rotation = frames[representative].rotation
                    ops._rotation_domain(rotation)
                value = ops.recording_parent_origin(parent, rotation)
                shared.setdefault(node.recipe, frame)
            else:
                if node.kind in {"site", "follow"}:
                    local = node.operands[0]
                    build = lambda: ops.compose_recording_fast(parent,
                        ops.recording_constant_pose(local, build=source_constant))
                    signature = ((parent, local) if node.kind == "site"
                                 else ("follow", parent, local))
                else:
                    kind, axis, local, law, coordinate = node.operands
                    if kind == "hinge" and law is not None:
                        coordinate = ops.recording_affine_coordinate(law.initial, law.target, law.duration,
                            law.elapsed, law.running_since, time, running=law.running)
                    def build():
                        relative = ops.make_recording()
                        if kind == "hinge":
                            rotation = ops.recording_axis_rotation(axis, coordinate, context=context,
                                path="hinge:" + node.path, max_steps=MAX_KEYFRAMES)
                            relative = ops.make_recording(orientation=rotation)
                        return ops.compose_recording_fast(ops.compose_recording_fast(parent, relative),
                            ops.recording_constant_pose(local, inverse=True, build=source_constant))
                    signature = ("joint", parent, kind, axis, coordinate,
                                 F(0) if kind == "hinge" else None, local)
                value = ops.recording_relative_pose(signature, build, context=context,
                    path=node.path, max_steps=MAX_KEYFRAMES)
                if value is None:
                    value = build()
        frames[frame] = value
        if node.constant:
            constants[frame] = value
        return value

    for frame in graph.selected:
        resolve(frame)
    return frames


def sample_captured_carriers(simulator, time, state, selected, proof, ops, context):
    """Return a private graph/final receipt, or keep the existing full sampler."""
    captured = _capture_graph(simulator, time, state, selected, proof, ops, minimum_selected=17)
    if captured is None:
        return None
    graph, time = captured
    publication = _Publication(simulator, graph, ops)
    frames = _sample_graph(graph, time, ops, context, publication)
    return frames, publication.finish


_EXCESS_FIELDS = ("trig_count", "product_count", "path_offset_l1_m", "max_position_l1_m",
                 "position_error_m", "rotation_error_rad")


class _PhasePublication(_Publication):
    """One private latest cursor per recipe, admitted with the whole phase."""
    def __init__(self, simulator, graph, ops, bounds, records):
        super().__init__(simulator, graph, ops)
        self.bounds, self.bound_records = bounds, records
        self.bound_inputs = MappingProxyType({path: inputs for path, _, inputs in records})
        self.indices = {}

    def _capacity(self):
        if (type(self.ops.work.max_cache_entries) is not int
                or self.ops.work.max_cache_entries != self.capacity):
            from .reach_recording_fast import _UnsupportedPlanar
            raise _UnsupportedPlanar("The private phase cursor domain changed.")

    def read_cursor(self, key):
        index = self.indices.get(key)
        if index is None:
            value = self.ops.work.lookup(key)
        else:
            self.ops.work.charge("recording_body_cursor_reuse")
            value = self.pending[index][2]
        self.ops._require_domain()
        self._capacity()
        return value

    def stage(self, key, previous, value):
        self.ops.work.charge("recording_body_cursor_stage")
        self.ops._require_domain()
        self._capacity()
        index = self.indices.get(key)
        if index is None:
            if len(self.pending) >= self.capacity:
                from .reach_recording_fast import _UnsupportedPlanar
                raise _UnsupportedPlanar("The private phase cursor group exceeds its cache bound.")
            self.indices[key] = len(self.pending)
            self.pending.append((key, previous, value))
        else:
            original = self.pending[index]
            if previous is not original[2]:
                raise ReachAdmissionError("reach_domain", "A private carrier cursor changed during sampling.")
            # Retain the original live-cache identity for the final reentrant
            # receipt, but discard every superseded private numeric result.
            self.pending[index] = (key, original[1], value)

    def admit(self):
        super().admit()
        for path, original, inputs in self.bound_records:
            current = self.bounds.get(path)
            if (current is not original or type(current) is not PhaseBound
                    or any(type(getattr(current, field)) is not type(value)
                           or getattr(current, field) != value
                           for field, value in zip(_EXCESS_FIELDS, inputs))):
                raise ReachAdmissionError("reach_domain", "The captured phase bounds changed during sampling.")
        return True

    def finish(self):
        self.ops.work.charge("recording_captured_bound_guard", len(self.bound_records))
        self.ops._require_domain()
        super().finish()


class _CapturedPhase:
    """Stream a finite phase into existing private output arrays.

    This object is owned by one invocation of the exporter, never retained in
    a cache. Parents are immutable working operands in selected-frame order;
    only the latest pending cursor survives for each complete recipe. The
    caller must finish after all output callbacks and before publishing.
    """
    def __init__(self, simulator, graph, ops, context, times, bounds, records):
        self.simulator, self.graph, self.ops, self.context = simulator, graph, ops, context
        self.times, self.index, self.finished, self.active = times, 0, False, False
        self.parents = []
        self.constants = {}
        self.publication = _PhasePublication(simulator, graph, ops, bounds, records)
        self.excesses = None

    def sample(self, time):
        from .reach_recording_fast import (CertifiedRecordingFrames, _BallisticLaw,
                                           _UnsupportedPlanar, recording_float_excess)
        from .reach_runtime import RecordingPose

        if (self.finished or self.active or self.index >= len(self.times)
                or type(time) is not F or time != self.times[self.index]):
            raise ReachAdmissionError("reach_domain", "Captured phase samples must follow their exact clock sequence.")
        self.active = True
        try:
            self.ops._domain()
            self.publication._capacity()
            private = (_sample_graph(self.graph, time, self.ops, self.context,
                self.publication, parents=self.parents) if self.graph.static_carriers else
                _sample_chain_graph(self.graph, time, self.ops, self.context,
                                    self.publication, self.constants))
            frames, excesses = {}, {} if self.excesses is None else None
            for path, _, inputs in self.publication.bound_records:
                # Each actual selected pose keeps its original cancellation
                # checkpoint and finite native result admission. The source
                # and bound identities are rechecked together at phase end.
                self.simulator._check()
                self.ops._require_domain()
                value = private[path]
                node = self.graph.nodes[path]
                dynamic = node.kind == "dynamic"
                if dynamic:
                    self.ops.work.charge("recording_dynamic_path_extent")
                    self.ops._require_domain()
                    law = self.ops.dynamic_extents.get(node.path)
                    if (type(law) is not _BallisticLaw or type(law.proved_extent) is not F
                            or law.proved_extent != inputs[3]):
                        raise _UnsupportedPlanar("A captured free root needs its actual proved source extent.")
                    self.ops.work.guard(law.extent, law.proved_extent)
                if excesses is not None:
                    bound = PhaseBound(**dict(zip(_EXCESS_FIELDS, inputs)))
                    excesses[path] = recording_float_excess(bound, work=self.ops.work,
                        include_cell_radii=False, dynamic=dynamic)
                    self.ops._require_domain()
                frames[path] = RecordingPose(value.position, value.orientation)
            if excesses is not None:
                self.excesses = MappingProxyType(excesses)
            self.index += 1
            return CertifiedRecordingFrames(frames, self.excesses)
        finally:
            self.active = False

    def finish(self):
        if self.finished or self.active or self.index != len(self.times):
            raise ReachAdmissionError("reach_domain", "A captured phase must complete every retained sample before admission.")
        self.publication.finish()
        self.finished = True
        self.parents.clear()
        self.constants.clear()
        self.publication.pending.clear()
        self.publication.indices.clear()


def begin_captured_phase(simulator, times, state, selected, proof, ops, context,
                         *, phase_bounds, phase_interval):
    """Prepare an optional complete static-ancestry phase, including small graphs."""
    from .reach_recording_fast import _checked_compare
    from .scene import MAX_BAKED_POSES, MAX_KEYFRAMES

    work = ops.work
    if (type(times) is not tuple or not 2 <= len(times) <= MAX_KEYFRAMES
            or type(selected) is not tuple or not selected
            # Smaller caches retain their original scalar eviction/reseed
            # behavior instead of extending a cursor through a private phase.
            or type(work.max_cache_entries) is not int or work.max_cache_entries != 256
            or len(selected) > work.max_cache_entries or len(times) * len(selected) > MAX_BAKED_POSES
            or any(type(path) is not str for path in selected) or len(set(selected)) != len(selected)
            or type(proof) is not RecordingAngularProof
            or type(proof.start) is not F or type(proof.end) is not F
            or type(phase_interval) is not tuple or phase_interval != (proof.start, proof.end)
            or type(phase_bounds) not in (dict, MappingProxyType)):
        return None
    work.charge("recording_captured_phase_domain")
    ops._require_domain()
    if type(times[0]) is not F:
        return None
    # Determine structural eligibility before walking every future clock or
    # binding allowance operands. Unsupported phases keep their scalar path
    # without repeating a time-dependent preflight that cannot be used.
    captured = _capture_graph(simulator, times[0], state, selected, proof, ops,
                              minimum_selected=1, varying_parents=True)
    if captured is None:
        return None
    graph, _ = captured
    previous = proof.start
    for time in times:
        work.charge("recording_captured_phase_clock")
        ops._require_domain()
        if type(time) is not F:
            return None
        work.guard(time, previous, proof.end)
        if (_checked_compare(previous, time, work) >= 0
                or _checked_compare(time, proof.end, work) >= 0):
            return None
        previous = time
    records = []
    for path in selected:
        work.charge("recording_captured_phase_bound")
        ops._require_domain()
        bound = phase_bounds.get(path)
        if type(bound) is not PhaseBound:
            return None
        inputs = tuple(getattr(bound, field) for field in _EXCESS_FIELDS)
        if (any(type(value) is not int or value < 0 for value in inputs[:2])
                or any(type(value) is not F or value.numerator < 0 for value in inputs[2:])):
            return None
        work.guard(*inputs)
        records.append((path, bound, inputs))
    return _CapturedPhase(simulator, graph, ops, context, times, phase_bounds, tuple(records))
