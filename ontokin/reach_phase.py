"""Uniform source-phase inputs, with continuous ideal state across anchors.

This module derives bounds from actual topology and exact phase operands. It
does not infer a uniform error from sampled poses or an inverse-solve residual.
All arithmetic consumes the simulator's existing bounded request work context.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F

from .reach_numeric import ReachAdmissionError, compare, exact, rational
from .reach_pose import VECTOR_ERROR, uniform_source_bounds


@dataclass(frozen=True)
class AnchorError:
    position_m: F = F(0)
    rotation_rad: F = F(0)
    velocity_m_per_s: F = F(0)
    angular_velocity_rad_per_s: F = F(0)


@dataclass(frozen=True)
class JointPhase:
    actual_start: F
    actual_end: F
    ideal_start: F
    ideal_end: F
    actual_slope: F
    ideal_slope: F
    coordinate_error: F


@dataclass(frozen=True)
class PhaseBound:
    max_position_l1_m: F = F(0)
    path_offset_l1_m: F = F(0)
    trig_count: int = 0
    product_count: int = 0
    vector_round_count: int = 0
    coordinate_angle_error_rad: F = F(0)
    anchor_position_error_m: F = F(0)
    anchor_rotation_error_rad: F = F(0)
    position_error_m: F = F(0)
    rotation_error_rad: F = F(0)
    velocity_error_m_per_s: F = F(0)
    angular_velocity_error_rad_per_s: F = F(0)
    carrier_speed_upper_m_per_s: F = F(0)
    carrier_acceleration_upper_m_per_s2: F = F(0)
    angular_speed_upper_rad_per_s: F = F(0)
    angular_acceleration_upper_rad_per_s2: F = F(0)
    actual_speed_upper_m_per_s: F = F(0)
    actual_angular_speed_upper_rad_per_s: F = F(0)


class PhaseArithmetic:
    def __init__(self, work):
        self.work = work

    def number(self, value):
        return rational(value, self.work)

    def add(self, *values):
        if 0 < len(values) <= 8 and all(type(value) is F for value in values):
            self.work.charge("phase_sum_domain")
            self.work.guard(*values)
            nonzero = tuple(value for value in values if value)
            if not nonzero:
                return F(0)
            result = nonzero[0]
            for value in nonzero[1:]:
                result = exact(result, value, "add", self.work)
            return result
        result = F(0)
        for value in values:
            result = exact(result, value, "add", self.work)
        return result

    def sub(self, a, b):
        return exact(a, b, "sub", self.work)

    def mul(self, *values):
        if 0 < len(values) <= 8 and all(type(value) is F for value in values):
            self.work.charge("phase_product_domain")
            self.work.guard(*values)
            if not all(values):
                return F(0)
            factors = tuple(value for value in values if value != 1)
            if not factors:
                return F(1)
            result = factors[0]
            for value in factors[1:]:
                result = exact(result, value, "mul", self.work)
            return result
        result = F(1)
        for value in values:
            result = exact(result, value, "mul", self.work)
        return result

    def div(self, a, b):
        return exact(a, b, "div", self.work)

    def absolute(self, value):
        self.work.charge("phase_absolute")
        self.work.guard(value)
        return abs(value)

    def maximum(self, *values):
        result = F(0)
        for value in values:
            if compare(value, result, self.work) > 0:
                result = value
        return result

    def l1(self, vector):
        return self.add(*(self.absolute(self.number(value)) for value in vector))

    def rounding(self, magnitude):
        # L1 component exposure allowance; also bounds its Euclidean norm.
        return self.add(self.mul(magnitude, F(1, 1 << 53)), F(3, 1 << 1075))


def joint_phase(simulator, path, start, end, state):
    """Exact affine endpoints and slopes; continuous ideal starts are retained."""
    a = PhaseArithmetic(simulator.work)
    claimant = state.claims.get((path, "coordinate"))
    if claimant is None:
        actual = a.number(state.coordinates[path])
        ideal = state.ideal_coordinates[path]
        return JointPhase(actual, actual, ideal, ideal, F(0), F(0), a.absolute(a.sub(actual, ideal)))
    action, runtime = simulator.model.actions[claimant], state.actions[claimant]
    if action.kind == "reach_planar":
        index = 0 if path == action.reach.shoulder else 1
        actual_initial = a.number(runtime.initial[index])
        ideal_initial = runtime.ideal_initial[index]
        target = a.number(runtime.solution.target_rad[index])
    else:
        actual_initial = a.number(runtime.initial)
        ideal_initial = runtime.ideal_initial
        target = a.number(action.goal)
    actual_rate = a.div(a.sub(target, actual_initial), action.duration)
    ideal_rate = a.div(a.sub(target, ideal_initial), action.duration)
    actual = tuple(a.add(actual_initial, a.mul(actual_rate, runtime.elapsed_at(time))) for time in (start, end))
    ideal = tuple(a.add(ideal_initial, a.mul(ideal_rate, runtime.elapsed_at(time))) for time in (start, end))
    error = a.maximum(*(a.absolute(a.sub(x, y)) for x, y in zip(actual, ideal)))
    extent = a.maximum(*(a.absolute(value) for value in actual))
    # The affine scalar is rounded once at exposure into the source hinge.
    # Its magnitude lies between these endpoints throughout this phase.
    error = a.add(error, a.rounding(extent))
    running = runtime.status == "running"
    return JointPhase(*actual, *ideal, actual_rate if running else F(0),
                      ideal_rate if running else F(0), error)


def phase_bounds(simulator, start, end, state=None, *, selected_frames=None):
    """Return uniform bounds on one continuous closed source phase.

    The state governs the entire interval; the caller splits at all source and
    natural boundaries. The public result contains immutable bound records and
    exact scalar joint descriptors, never mutable solver/work objects.
    ``selected_frames`` is an internal anchor-proof optimization.
    """
    start, end = F(start), F(end)
    state = simulator.state if state is None else state
    if not 0 <= start <= end <= simulator.model.duration:
        raise ValueError("A source phase must be an ordered interval within the scene.")
    model, work, ops = simulator.model, simulator.work, simulator.pose_ops
    a = PhaseArithmetic(work)
    for block in model.events:
        work.charge("phase_boundary_check")
        if start < block.time < end:
            raise ValueError("A uniform phase cannot cross an authored boundary.")
    for path, runtime in state.actions.items():
        work.charge("phase_boundary_check")
        if runtime.status == "running" and start < runtime.running_since + model.actions[path].duration - runtime.elapsed < end:
            raise ValueError("A uniform phase cannot cross an action completion.")
    for history in state.forces.values():
        for force in history.active.values():
            work.charge("phase_boundary_check")
            if start < force.completion < end:
                raise ValueError("A uniform phase cannot cross a force completion.")
    incoming = simulator._incoming(state)
    objects, frames, joints, resolving = {}, {"world": PhaseBound()}, {}, set()

    def finish(**values):
        inputs = {name: values.get(name, 0 if name.endswith("count") else F(0)) for name in (
            "max_position_l1_m", "path_offset_l1_m", "trig_count", "product_count", "vector_round_count",
            "coordinate_angle_error_rad", "anchor_position_error_m", "anchor_rotation_error_rad")}
        bound = uniform_source_bounds(**inputs, work=work)
        values.update(position_error_m=bound["position_m"], rotation_error_rad=bound["rotation_rad"])
        return PhaseBound(**values)

    def constant(pose, *, inverse=False):
        extent = a.l1(pose.position)
        return finish(max_position_l1_m=a.add(a.mul(F(2), extent), a.mul(F(2), VECTOR_ERROR)) if inverse else extent,
            path_offset_l1_m=extent if inverse else F(0), product_count=1,
            vector_round_count=int(inverse))

    def compose(parent, local):
        work.charge("phase_path_counts", 3)
        offset = local.max_position_l1_m
        ideal_offset = a.add(offset, local.position_error_m)
        p_speed, l_speed = parent.carrier_speed_upper_m_per_s, local.carrier_speed_upper_m_per_s
        p_omega, l_omega = parent.angular_speed_upper_rad_per_s, local.angular_speed_upper_rad_per_s
        speed = a.add(p_speed, a.mul(p_omega, ideal_offset), l_speed)
        acceleration = a.add(parent.carrier_acceleration_upper_m_per_s2,
            a.mul(a.add(parent.angular_acceleration_upper_rad_per_s2, a.mul(p_omega, p_omega)), ideal_offset),
            a.mul(F(2), p_omega, l_speed), local.carrier_acceleration_upper_m_per_s2)
        omega = a.add(p_omega, l_omega)
        alpha = a.add(parent.angular_acceleration_upper_rad_per_s2,
            a.mul(p_omega, l_omega), local.angular_acceleration_upper_rad_per_s2)
        actual_speed = a.add(parent.actual_speed_upper_m_per_s,
            a.mul(parent.actual_angular_speed_upper_rad_per_s, a.add(offset, VECTOR_ERROR)),
            local.actual_speed_upper_m_per_s, a.mul(F(2), VECTOR_ERROR))
        actual_omega = a.add(parent.actual_angular_speed_upper_rad_per_s,
            local.actual_angular_speed_upper_rad_per_s, a.mul(F(2), VECTOR_ERROR))
        offset_error = a.add(local.position_error_m,
            a.mul(parent.rotation_error_rad, offset), VECTOR_ERROR)
        velocity_error = a.add(parent.velocity_error_m_per_s,
            a.mul(parent.angular_velocity_error_rad_per_s, a.add(offset, local.position_error_m)),
            a.mul(parent.actual_angular_speed_upper_rad_per_s, offset_error),
            local.velocity_error_m_per_s,
            a.mul(parent.rotation_error_rad, local.actual_speed_upper_m_per_s),
            a.mul(F(4), VECTOR_ERROR), a.rounding(a.mul(F(2), actual_speed)))
        omega_error = a.add(parent.angular_velocity_error_rad_per_s,
            local.angular_velocity_error_rad_per_s,
            a.mul(parent.rotation_error_rad, local.actual_angular_speed_upper_rad_per_s),
            a.mul(F(2), VECTOR_ERROR), a.rounding(a.mul(F(2), actual_omega)))
        return finish(max_position_l1_m=a.add(parent.max_position_l1_m, a.mul(F(2), offset), a.mul(F(4), VECTOR_ERROR)),
            path_offset_l1_m=a.add(parent.path_offset_l1_m, local.path_offset_l1_m, offset),
            trig_count=parent.trig_count + local.trig_count,
            product_count=parent.product_count + local.product_count + 1,
            vector_round_count=parent.vector_round_count + local.vector_round_count + 2,
            coordinate_angle_error_rad=a.add(parent.coordinate_angle_error_rad, local.coordinate_angle_error_rad),
            anchor_position_error_m=a.add(parent.anchor_position_error_m, local.anchor_position_error_m),
            anchor_rotation_error_rad=a.add(parent.anchor_rotation_error_rad, local.anchor_rotation_error_rad),
            velocity_error_m_per_s=velocity_error, angular_velocity_error_rad_per_s=omega_error,
            carrier_speed_upper_m_per_s=speed, carrier_acceleration_upper_m_per_s2=acceleration,
            angular_speed_upper_rad_per_s=omega, angular_acceleration_upper_rad_per_s2=alpha,
            actual_speed_upper_m_per_s=actual_speed, actual_angular_speed_upper_rad_per_s=actual_omega)

    def rotation_plan(omega, elapsed):
        plan = ops.spin_plan(omega, elapsed)
        simulator._register_spin_plan(omega, plan)

    def root(path):
        actual_position = tuple(a.number(value) for value in state.positions[path])
        ideal_position = state.ideal_positions[path]
        extent = a.l1(actual_position)
        position_error = a.l1(tuple(a.sub(x, y) for x, y in zip(actual_position, ideal_position)))
        speed = omega = F(0)
        rotation_error = state.root_rotation_errors.get(path, F(0))
        trig, products = 0, 1
        claimant = state.claims.get((path, "translation"))
        if claimant is not None:
            action, runtime = model.actions[claimant], state.actions[claimant]
            elapsed = a.maximum(*(a.absolute(runtime.elapsed_at(time)) for time in (start, end)))
            extent = a.add(a.l1(runtime.initial), a.mul(a.l1(action.vector), elapsed))
            position_error = a.l1(tuple(a.sub(a.number(x), y) for x, y in zip(runtime.initial, runtime.ideal_initial)))
            speed = a.l1(action.vector) if runtime.status == "running" else F(0)
        claimant = state.claims.get((path, "orientation"))
        if claimant is not None:
            action, runtime = model.actions[claimant], state.actions[claimant]
            elapsed = a.maximum(*(a.absolute(runtime.elapsed_at(time)) for time in (start, end)))
            rotation_plan(action.vector, elapsed)
            rotation_error = runtime.ideal_rotation_error
            if any(action.vector) and elapsed:
                trig, products = 1, 3
            omega = a.l1(action.vector) if runtime.status == "running" else F(0)
        return finish(max_position_l1_m=extent, trig_count=trig, product_count=products,
            anchor_position_error_m=position_error, anchor_rotation_error_rad=rotation_error,
            carrier_speed_upper_m_per_s=speed, angular_speed_upper_rad_per_s=omega,
            actual_speed_upper_m_per_s=speed, actual_angular_speed_upper_rad_per_s=omega)

    def dynamic(path):
        anchor, error = state.dynamic[path], state.dynamic_errors.get(path, AnchorError())
        initial = anchor.state
        elapsed = a.maximum(a.absolute(a.sub(start, anchor.time)), a.absolute(a.sub(end, anchor.time)))
        error_elapsed = a.maximum(a.absolute(a.sub(start, state.dynamic_error_times[path])),
                                  a.absolute(a.sub(end, state.dynamic_error_times[path])))
        actual_acceleration = tuple(a.number(value) for value in simulator._acceleration(path, state))
        ideal_acceleration = state.ideal_accelerations[path]
        acceleration_error = a.l1(tuple(a.sub(x, y) for x, y in zip(actual_acceleration, ideal_acceleration)))
        velocity = a.l1(initial.velocity)
        acceleration = a.l1(actual_acceleration)
        extent = a.add(a.l1(initial.position), a.mul(velocity, elapsed),
            a.div(a.mul(acceleration, elapsed, elapsed), F(2)))
        actual_speed = a.add(velocity, a.mul(acceleration, elapsed))
        position_error = a.add(error.position_m, a.mul(error.velocity_m_per_s, error_elapsed),
            a.div(a.mul(acceleration_error, error_elapsed, error_elapsed), F(2)))
        velocity_error = a.add(error.velocity_m_per_s, a.mul(acceleration_error, error_elapsed), a.rounding(actual_speed))
        actual_omega = a.l1(initial.omega)
        rotation_plan(initial.omega, elapsed)
        moving = bool(actual_omega and elapsed)
        return finish(max_position_l1_m=extent, trig_count=int(moving), product_count=3 if moving else 1,
            anchor_position_error_m=position_error,
            anchor_rotation_error_rad=a.add(error.rotation_rad, a.mul(error.angular_velocity_rad_per_s, error_elapsed)),
            velocity_error_m_per_s=velocity_error,
            angular_velocity_error_rad_per_s=error.angular_velocity_rad_per_s,
            carrier_speed_upper_m_per_s=a.add(actual_speed, velocity_error),
            carrier_acceleration_upper_m_per_s2=a.l1(ideal_acceleration),
            angular_speed_upper_rad_per_s=a.add(actual_omega, error.angular_velocity_rad_per_s),
            actual_speed_upper_m_per_s=actual_speed, actual_angular_speed_upper_rad_per_s=actual_omega)

    def frame(path):
        if path not in frames:
            stem = path.removesuffix(".frame")
            if stem in model.objects:
                frames[path] = instance(stem)
            else:
                site = model.sites[stem]
                frames[path] = compose(instance(site.owner), constant(site.pose))
        return frames[path]

    def instance(path):
        if path in objects:
            return objects[path]
        work.charge("phase_source_node")
        if path in resolving:
            raise ReachAdmissionError("reach_chain", "A phase topology contains a cycle.")
        resolving.add(path)
        if path in incoming:
            kind, relation = incoming[path]
            if kind == "follow":
                follow = model.follows[relation]
                result = compose(frame(follow.parent), constant(follow.offset))
            else:
                joint = model.joints[relation]
                local = PhaseBound()
                if joint.kind in {"hinge", "slider"}:
                    if relation not in joints:
                        joints[relation] = joint_phase(simulator, relation, start, end, state)
                    scalar = joints[relation]
                    axis = tuple(a.number(value) for value in joint.axis)
                    axis_size = a.l1(axis)
                    rate_error = a.absolute(a.sub(scalar.actual_slope, scalar.ideal_slope))
                    if joint.kind == "hinge":
                        # |norm(axis)-1| <= |norm(axis)^2-1|, without a
                        # host sqrt or an assumption that canonical axes are unit.
                        norm_defect = a.absolute(a.sub(a.add(*(a.mul(x, x) for x in axis)), F(1)))
                        omega_error = a.add(a.mul(axis_size, rate_error),
                            a.mul(norm_defect, a.absolute(scalar.ideal_slope)))
                        local = finish(trig_count=1, product_count=1,
                            coordinate_angle_error_rad=scalar.coordinate_error,
                            angular_velocity_error_rad_per_s=omega_error,
                            angular_speed_upper_rad_per_s=a.absolute(scalar.ideal_slope),
                            actual_angular_speed_upper_rad_per_s=a.mul(axis_size, a.absolute(scalar.actual_slope)))
                    else:
                        extent = a.mul(axis_size, a.maximum(a.absolute(scalar.actual_start), a.absolute(scalar.actual_end)))
                        local = finish(max_position_l1_m=extent, product_count=1,
                            anchor_position_error_m=a.mul(axis_size, scalar.coordinate_error),
                            velocity_error_m_per_s=a.mul(axis_size, rate_error),
                            carrier_speed_upper_m_per_s=a.mul(axis_size, a.absolute(scalar.ideal_slope)),
                            actual_speed_upper_m_per_s=a.mul(axis_size, a.absolute(scalar.actual_slope)))
                result = compose(compose(frame(joint.parent + ".frame"), local),
                                 constant(model.sites[joint.child].pose, inverse=True))
        elif state.modes[path] == "dynamic":
            result = dynamic(path)
        else:
            result = root(path)
        resolving.remove(path)
        objects[path] = result
        frames[path + ".frame"] = result
        return result

    if selected_frames is None:
        for path in model.objects:
            instance(path)
        for path in model.sites:
            frame(path + ".frame")
    else:
        for path in selected_frames:
            frame(path)
    return {"objects": objects, "frames": frames, "joints": joints}
