"""Independent canonical angular origins and source graph evaluation.

Every retained origin contains its complete exact rotation, publication state
and kernel allowance. Genuine source materializations create new origins;
reference/error-only boundaries retain the original object. Current points
are evaluated from these origins, never from a previously sampled point.
The separate smooth reference and its full uncertainty remain in
``torque_reference``. Neither an interval nor Boolean support decides a
canonical cancellation.
"""
from dataclasses import dataclass, replace
from fractions import Fraction as F

from .reach_reference import ReferenceError
from . import torque_axis_exact as exact_axis

ZERO = (False, False, False)
IDENTITY = (True, False, False, False)
UNIT = (F(1), F(0), F(0), F(0))
VECTOR_ZERO = (F(0),) * 3
PRODUCT_ERROR = F(1, 1 << 91)
AXIS_ERROR = F(1, 1 << 74)
EXPOSED_ERROR = F(1, 1 << 50)


@dataclass(frozen=True)
class AngularSupport:
    time: F
    quaternion: tuple
    omega: tuple
    exact_quaternion: tuple | None = None
    exact_omega: tuple | None = None
    frozen_projection: tuple | None = None
    rotation_error: F = F(0)


def constants(values):
    return tuple(value != 0 for value in values)


def quaternion_product(a, b, work):
    work.tick()
    pairs = (((0, 0), (1, 1), (2, 2), (3, 3)),
             ((0, 1), (1, 0), (2, 3), (3, 2)),
             ((0, 2), (1, 3), (2, 0), (3, 1)),
             ((0, 3), (1, 2), (2, 1), (3, 0)))
    return tuple(any(a[i] and b[j] for i, j in row) for row in pairs)


def rotate(q, vector, work):
    """Support of the homogeneous quaternion matrix, including its divisor.

    Diagonals are conservatively possibly nonzero. Each off-diagonal entry
    contains exactly q_i*q_j and q_w*q_k. Rescaling, division and binary64
    materialization all preserve an already exact zero numerator.
    """
    work.tick()
    result = []
    for i in range(3):
        possible = vector[i]
        for j in range(3):
            if i == j:
                continue
            k = 3 - i - j
            possible = possible or vector[j] and (q[i + 1] and q[j + 1] or q[0] and q[k + 1])
        result.append(bool(possible))
    return tuple(result)


def cross(a, b, work):
    work.tick()
    return tuple(a[j] and b[k] or a[k] and b[j] for j, k in ((1, 2), (2, 0), (0, 1)))


def _value(time, quaternion, omega, *, projection=None, error=F(0)):
    return AngularSupport(time, constants(quaternion), constants(omega),
                          quaternion, omega, projection, error)


def admit(value, a):
    a.tick()
    if (type(value) is not AngularSupport or type(value.exact_quaternion) is not tuple
            or len(value.exact_quaternion) != 4 or type(value.exact_omega) is not tuple
            or len(value.exact_omega) != 3):
        raise ReferenceError("source_admission", "Independent canonical angular origin is incomplete")
    a.guard(value.time, *value.exact_quaternion, *value.exact_omega, value.rotation_error)
    if value.frozen_projection is not None:
        if type(value.frozen_projection) is not tuple or len(value.frozen_projection) != 4:
            raise ReferenceError("source_admission", "Independent angular publication origin is incomplete")
        a.guard(*value.frozen_projection)
    return value


def materialize(value, a):
    """Retain a previously exposed rotation verbatim at another real anchor."""
    admit(value, a)
    q = (value.frozen_projection if value.frozen_projection is not None else
         exact_axis.materialized(value.exact_quaternion, a))
    w = exact_axis.exposed_vector(value.exact_omega, a)
    return _value(value.time, q, w, projection=q,
                  error=a.exact(value.rotation_error, EXPOSED_ERROR, "add"))


def _advance(value, omega, elapsed, time, a):
    admit(value, a)
    omega, elapsed = tuple(F(v) for v in omega), F(elapsed)
    a.guard(*omega, elapsed)
    if not elapsed or not any(omega):
        return replace(value, time=time)
    increment = exact_axis.spin_rotation(omega, elapsed, a)
    q = exact_axis.product(increment, value.exact_quaternion, a)
    error = a.exact_sum(value.rotation_error, AXIS_ERROR, PRODUCT_ERROR, PRODUCT_ERROR)
    return _value(time, q, omega, error=error)


def root_support(reference, path, time, state):
    a = reference.a
    history = state.torques[path]
    saved = admit(history.support, a)
    if state.modes[path] == "dynamic":
        dt = a.exact(time, saved.time, "sub")
        if history.rotation is None:
            return _advance(saved, saved.exact_omega, dt, time, a)
        index = {"world_x": 0, "world_y": 1, "world_z": 2}[history.axis]
        square = a.exact(dt, dt, "mul")
        curved = a.exact(a.exact(history.acceleration, square, "mul"), 2, "div")
        phase = a.exact(a.exact(saved.exact_omega[index], dt, "mul"), curved, "add")
        if abs(phase) > F(1 << 20):
            raise ReferenceError("numeric", "Independent torque phase exceeds the complete segment domain",
                                 torque_reason="phase_domain")
        speed = F(a.round64(a.exact(saved.exact_omega[index],
                    a.exact(history.acceleration, dt, "mul"), "add")))
        rounded_phase = F(a.round64(phase))
        omega = tuple(speed if i == index else F(0) for i in range(3))
        if not phase:
            return replace(saved, time=time, omega=constants(omega), exact_omega=omega)
        axis = tuple(F(i == index) for i in range(3))
        q = exact_axis.product(exact_axis.axis_rotation(axis, rounded_phase, a),
                               saved.exact_quaternion, a)
        error = a.exact_sum(saved.rotation_error, PRODUCT_ERROR,
                           AXIS_ERROR if rounded_phase else F(0),
                           PRODUCT_ERROR if rounded_phase else F(0))
        return _value(time, q, omega, error=error)
    action_path = state.claims.get((path, "orientation"))
    result = replace(saved, time=time, omega=ZERO, exact_omega=VECTOR_ZERO)
    if action_path is not None:
        action, active = reference.model.actions[action_path], state.actions[action_path]
        # Action elapsed is accumulated running time, not scene-time minus
        # the original start. Pauses never replace this rotation's origin.
        elapsed = active.elapsed_at(time)
        result = _advance(saved, action.vector, elapsed, time, a)
        omega = tuple(F(value) for value in action.vector) if active.status == "running" else VECTOR_ZERO
        result = replace(result, omega=constants(omega), exact_omega=omega)
    return result


def frame_support(reference, path, time, state):
    """Evaluate the complete authored angular ancestry without recipe recursion.

    This walk stores one value per visited source frame. Its only size bound
    is the admitted source graph itself and the original charged work. It
    introduces no smaller encoding-depth limit or retained expression history.
    """
    a, model = reference.a, reference.model
    incoming = reference._incoming(state)
    seen = {"world": _value(time, UNIT, VECTOR_ZERO)}
    visiting, stack = set(), [(path, False)]

    def constant(q):
        return _value(time, exact_axis.rotation(q, a), VECTOR_ZERO, error=PRODUCT_ERROR)

    def compose(parent, local):
        admit(parent, a); admit(local, a)
        transformed = (exact_axis.rotated(parent.exact_quaternion, local.exact_omega, a)
                       if any(local.exact_omega) else VECTOR_ZERO)
        omega = tuple(exact_axis.nearest_grid(a.exact(x, y, "add"), a)
                      for x, y in zip(parent.exact_omega, transformed))
        q = exact_axis.product(parent.exact_quaternion, local.exact_quaternion, a)
        return _value(time, q, omega,
                      error=a.exact_sum(parent.rotation_error, local.rotation_error, PRODUCT_ERROR))

    def parent_of(frame):
        stem = frame.removesuffix(".frame")
        if stem in model.sites:
            return model.sites[stem].owner + ".frame"
        if stem in incoming:
            kind, relation = incoming[stem]
            return model.follows[relation].parent if kind == "follow" else model.joints[relation].parent + ".frame"
        return None

    while stack:
        a.tick()
        frame, ready = stack.pop()
        if frame in seen:
            continue
        parent = parent_of(frame)
        if not ready:
            if frame in visiting:
                raise ReferenceError("unsupported", "Independent canonical angular source graph is cyclic")
            visiting.add(frame)
            stack.append((frame, True))
            if parent is not None and parent not in seen:
                stack.append((parent, False))
            continue
        stem = frame.removesuffix(".frame")
        if stem in model.sites:
            value = compose(seen[parent], constant(model.sites[stem].pose.rotation))
        elif stem in incoming:
            kind, relation = incoming[stem]
            if kind == "follow":
                value = compose(seen[parent], constant(model.follows[relation].offset.rotation))
            else:
                joint = model.joints[relation]
                value = seen[parent]
                if joint.kind in {"hinge", "slider"}:
                    coordinate, rate = reference._coordinate(relation, time, state, ideal=False)
                    a.guard(coordinate, rate)
                    if joint.kind == "hinge":
                        q = exact_axis.axis_rotation(joint.axis, coordinate, a)
                        omega = tuple(a.exact(component, rate, "mul") for component in joint.axis)
                        local = _value(time, q, omega,
                            error=a.exact(AXIS_ERROR, PRODUCT_ERROR, "add") if coordinate else F(0))
                    else:
                        # The slider's identity rotation is still imported and
                        # composed. That product and final angular grid matter
                        # for an off-grid materialized parent.
                        local = constant(UNIT)
                    value = compose(value, local)
                child = constant(model.sites[joint.child].pose.rotation)
                child = replace(child, exact_quaternion=(child.exact_quaternion[0],
                    *(-part for part in child.exact_quaternion[1:])))
                value = compose(value, child)
        else:
            value = root_support(reference, stem, time, state)
        visiting.remove(frame)
        seen[frame] = value
    return seen[path]
