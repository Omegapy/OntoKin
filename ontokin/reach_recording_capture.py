"""Complete immutable inputs for repeated constant-parent recording carriers.

The optional graph contains source operands and structural receipts only.
Completed parent transforms and carrier cursors use the existing work LRU;
the pending cursor group lasts for one sample and is bounded by that LRU.
No producer receipt is available to the independent supplied-byte reader.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from types import MappingProxyType

from .model import Pose
from .reach_numeric import MAX_OPERAND_BITS, ReachAdmissionError, rational
from .reach_pose import RotationValue
from .reach_phase import (RecordingAngularFrame, RecordingAngularProof, _AxialRate,
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
class _Node:
    frame: str
    kind: str
    path: str
    record: RecordingAngularFrame
    identities: tuple
    operands: tuple
    constant: bool
    recipe: tuple
    static_recipe: tuple | None


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


def _capture(simulator, state, selected, proof, ops):
    """Capture only a complete static ancestry and varying zero-offset leaves."""
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
        if type(frame) is not str or frame in visiting or len(visiting) > 64:
            return None
        work.charge("recording_body_witness")
        ops._require_domain()
        # Copy only required fixed-size records, never an arbitrarily large
        # externally supplied backing map. Already captured records survive a
        # temporary mutation of the caller's MappingProxyType backing dict.
        record = proof.frames.get(frame)
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
                if (state.modes[path] == "dynamic" or state.claims.get((path, "translation"))
                        is not None or state.claims.get((path, "orientation")) is not None):
                    return None
                operands = (state.positions[path],
                            state.root_rotation_values.get(path, state.orientations[path]))
                components = (operands[1].components if type(operands[1]) is RotationValue else operands[1])
                if components[1] or components[2]:
                    return None
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
        except (KeyError, AttributeError, TypeError, IndexError):
            return None
        visiting.add(frame)
        try:
            parent = visit(record.parent) if record.parent is not None else None
        finally:
            visiting.remove(frame)
        if record.parent is not None and (parent is None or not parent.constant):
            return None
        recipe = _recording_orientation_recipe(record, parent.recipe if parent else None, work=work)
        ops._require_domain()
        if recipe is None:
            return None
        static_recipe = ((record.witness, parent.static_recipe if parent else None)
                         if local_constant else None)
        node = _Node(frame, kind, path, record, identities, operands, local_constant,
                     recipe, static_recipe)
        nodes[frame] = node
        return node

    for frame in selected:
        node = visit(frame)
        if (node is None or node.kind != "joint" or node.constant
                or node.operands[0] != "hinge" or node.record.parent is None
                or type(node.operands[2].position) is not tuple
                or len(node.operands[2].position) != 3
                or any(type(value) is not float or value != 0.0
                       for value in node.operands[2].position)):
            return None
    captured_proof = RecordingAngularProof(proof.start, proof.end, proof.program_revision,
                                          MappingProxyType({path: node.record for path, node in nodes.items()}))
    return _Graph(model, state, root_state, proof, captured_proof, selected,
                  MappingProxyType(nodes), tuple(row for row in topology if row[:2] not in used_edges),
                  sizes, active_grips)


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
                        or not all(_same_identity(model, item) for item in node.identities)
                        or _current_recording_angular_witness(model, state, node.kind, node.path,
                            work=work) != (node.record.parent, node.record.witness)):
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


def sample_captured_carriers(simulator, time, state, selected, proof, ops, context):
    """Return a private graph/final receipt, or keep the existing full sampler."""
    from .reach_recording_fast import (METHOD, _FloatPose, _UnsupportedPlanar,
                                       captured_recording_orientation)
    from .scene import MAX_KEYFRAMES

    work = ops.work
    if (len(selected) <= 16 or len(selected) > work.max_cache_entries
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
        graph = _capture(simulator, state, selected, proof, ops)
        if graph is None:
            return None
        work.remember(key, graph)
        ops._require_domain()
    # The graph has captured every relevant claim. A constant unclaimed hinge
    # must not consult the ordinary callback that reads the live source again.
    ops.constant_hinge_check = None
    ops.constant_hinges = frozenset("hinge:" + node.path for node in graph.nodes.values()
                                   if node.kind == "joint" and node.constant)
    publication = _Publication(simulator, graph, ops)
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
            value = ops.make_recording(position=node.operands[0], orientation=node.operands[1])
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

    for frame in selected:
        node = graph.nodes[frame]
        parent_node = graph.nodes[node.record.parent]
        parent_key = (METHOD, "captured_constant_parent", MAX_OPERAND_BITS,
                      graph.proof.start, graph.proof.end, parent_node.static_recipe)
        parent = work.lookup(parent_key)
        ops._require_domain()
        if type(parent) is not _FloatPose:
            parent = constant(node.record.parent)
            work.remember(parent_key, parent)
            ops._require_domain()
        representative = shared.get(node.recipe)
        if representative is None:
            rotation = ops.recording_body_orientation(lambda: captured_recording_orientation(
                ops.source_ops, graph.proof, frame, time), node.record.rate.axis,
                node.record.rate.value, time, phase_start=graph.proof.start, phase_end=graph.proof.end,
                context=context, path="carrier:" + frame[:-6], proof_token=node.record.token,
                max_steps=MAX_KEYFRAMES, stage_cursor=publication.stage)
        else:
            work.charge("recording_body_shared_orientation")
            ops._require_domain()
            rotation = frames[representative].rotation
            ops._rotation_domain(rotation)
        frames[frame] = ops.recording_parent_origin(parent, rotation)
        shared.setdefault(node.recipe, frame)
    return frames, publication.finish
