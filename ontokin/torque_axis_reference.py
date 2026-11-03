"""Independent exact-zero witnesses for canonical angular admission.

An interval containing zero does not prove an exactly zero canonical scalar.
This small abstract interpretation follows only which source terms can be
nonzero. A False component is proved zero because every contributing product
has a proved-zero factor. No cancellation, tolerance, producer state or error
enclosure supplies that proof. The full numerical enclosures remain separate.
"""
from dataclasses import dataclass
from fractions import Fraction as F

from .reach_reference import ReferenceError
from . import torque_axis_exact as exact_axis

ZERO = (False, False, False)
IDENTITY = (True, False, False, False)


@dataclass(frozen=True)
class AngularSupport:
    time: F
    quaternion: tuple
    omega: tuple
    exact_quaternion: tuple | None = None
    exact_omega: tuple | None = None


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


def root_support(reference, path, time, state):
    a = reference.a
    a.tick()
    if state.modes[path] == "dynamic":
        saved = state.torques[path].support
        if saved is None:
            raise ReferenceError("source_admission", "Independent canonical angular origin has no zero witness")
        dt = a.exact(time, saved.time, "sub")
        quaternion = saved.quaternion
        exact_q, exact_w = saved.exact_quaternion, saved.exact_omega
        if dt and any(saved.omega):
            quaternion = quaternion_product((True, *saved.omega), quaternion, a)
            exact_q = None
        history = state.torques[path]
        if dt and history.rotation is not None and exact_w is not None:
            index = {"world_x": 0, "world_y": 1, "world_z": 2}[history.axis]
            speed = a.round64(a.exact(exact_w[index], a.exact(history.acceleration, dt, "mul"), "add"))
            exact_w = tuple(F(speed) if i == index else F(0) for i in range(3))
        return AngularSupport(time, quaternion, saved.omega, exact_q, exact_w)
    saved = state.torques[path].support
    if saved is None:
        raise ReferenceError("source_admission", "Independent prescribed rotation has no zero witness")
    quaternion = saved.quaternion
    omega = ZERO
    exact_q, exact_w = saved.exact_quaternion, (F(0),) * 3
    action_path = state.claims.get((path, "orientation"))
    if action_path is not None:
        action, active = reference.model.actions[action_path], state.actions[action_path]
        vector = constants(action.vector)
        elapsed = active.elapsed_at(time)
        a.guard(elapsed)
        if elapsed and any(vector):
            quaternion = quaternion_product((True, *vector), quaternion, a)
            exact_q = None
        if active.status == "running":
            omega = vector
            exact_w = tuple(F(value) for value in action.vector)
    return AngularSupport(time, quaternion, omega, exact_q, exact_w)


def frame_support(reference, path, time, state):
    """Follow the same authored ancestry, using only Boolean zero algebra."""
    a, model = reference.a, reference.model
    incoming, seen, visiting = reference._incoming(state), {}, set()

    def compose(parent, local_q, local_w=ZERO, *, exact_q=None, exact_w=(F(0),)*3):
        q = quaternion_product(parent.quaternion, local_q, a)
        rotated = rotate(parent.quaternion, local_w, a)
        w = tuple(x or y for x, y in zip(parent.omega, rotated))
        new_q = (exact_axis.product(parent.exact_quaternion, exact_q, a)
                 if parent.exact_quaternion is not None and exact_q is not None else None)
        new_w = None
        if parent.exact_omega is not None and exact_w is not None:
            values = (exact_w if not any(exact_w) else
                      exact_axis.rotated(parent.exact_quaternion, exact_w, a)
                      if parent.exact_quaternion is not None else None)
            if values is not None:
                new_w = tuple(exact_axis.nearest_grid(a.exact(x,y,"add"),a)
                              for x,y in zip(parent.exact_omega,values))
                w = constants(new_w)
        return AngularSupport(time, constants(new_q) if new_q is not None else q, w, new_q, new_w)

    def visit(frame):
        a.tick()
        if frame == "world":
            return AngularSupport(time, IDENTITY, ZERO, (F(1),F(0),F(0),F(0)), (F(0),)*3)
        if frame in seen:
            return seen[frame]
        if frame in visiting or len(visiting) >= 128:
            raise ReferenceError("unsupported", "Independent angular zero witness has a cyclic/deep source graph")
        visiting.add(frame)
        stem = frame.removesuffix(".frame")
        if stem in model.sites:
            site = model.sites[stem]
            value = compose(visit(site.owner + ".frame"), constants(site.pose.rotation),
                            exact_q=exact_axis.rotation(site.pose.rotation,a))
        elif stem in incoming:
            kind, relation = incoming[stem]
            if kind == "follow":
                follow = model.follows[relation]
                value = compose(visit(follow.parent), constants(follow.offset.rotation),
                                exact_q=exact_axis.rotation(follow.offset.rotation,a))
            else:
                joint = model.joints[relation]
                value = visit(joint.parent + ".frame")
                if joint.kind == "hinge":
                    coordinate, rate = reference._coordinate(relation, time, state, ideal=False)
                    a.guard(coordinate, rate)
                    axis = constants(joint.axis)
                    local_q = (True, *axis) if coordinate else IDENTITY
                    local_w = axis if rate else ZERO
                    value = compose(value, local_q, local_w,
                        exact_q=None if coordinate else (F(1),F(0),F(0),F(0)),
                        exact_w=tuple(a.exact(component,rate,"mul") for component in joint.axis))
                # Sliders and fixed/grip transforms contribute no angular
                # velocity; inverse fixed quaternion has the same support.
                child_q = exact_axis.rotation(model.sites[joint.child].pose.rotation,a)
                child_q = (child_q[0], *(-value for value in child_q[1:]))
                value = compose(value, constants(child_q), exact_q=child_q)
        else:
            value = root_support(reference, stem, time, state)
        visiting.remove(frame)
        seen[frame] = value
        return value

    return visit(path)
