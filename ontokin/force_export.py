"""Geometry-free, exact-prefix motion bounds for recorded force delivery.

The writer and the byte reader each rebuild this plan from the source model.
Authored force magnitudes and future impulse records are deliberately absent
from the planner: interval bounds come from the canonical committed run state.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Callable

from .evaluator import time_text
from .force_runtime import ForceSimulator
from .model import SceneModel


def norm_upper(vector) -> Fraction:
    """Bound a finite canonical vector norm without binary64 intermediates."""
    squared = sum((Fraction(component) ** 2 for component in vector), Fraction(0))
    radicand = squared.numerator * squared.denominator
    floor = math.isqrt(radicand)
    return Fraction(floor + (floor * floor != radicand), squared.denominator)


@dataclass(frozen=True)
class ForceInterval:
    start: Fraction
    end: Fraction
    acceleration_bound: Fraction
    angular_speed_bound: Fraction


@dataclass(frozen=True)
class ForcePrefixPlan:
    boundaries: tuple[Fraction, ...]
    intervals: tuple[ForceInterval, ...]

    @property
    def angular_speed_bound(self) -> Fraction:
        return max((interval.angular_speed_bound for interval in self.intervals), default=Fraction(0))


class _PlanningSimulator(ForceSimulator):
    def snapshot(self, time: Fraction, side: str) -> dict[str, Any]:
        # advance() still checks every source transaction, interior extremum,
        # and the requested pose. Planning retains no copied output records.
        self._kinematics(time, self.state)
        return {}


def _motion_bounds(simulator: ForceSimulator, time: Fraction,
                   check: Callable[[], None] | None) -> tuple[Fraction, Fraction]:
    acceleration = Fraction(0)
    angular = Fraction(0)
    state, model = simulator.state, simulator.model
    incoming = simulator._incoming(state)
    for path in model.objects:
        if check is not None:
            check()
        if state.modes[path] == "dynamic" and path not in incoming:
            acceleration = max(acceleration, norm_upper(state.forces[path].acceleration))
            angular += norm_upper(state.dynamic[path].state.omega)
    # All primitive angular contributions are constant on this true-boundary
    # interval. Their sum bounds every active rigid chain, including helpers.
    # A released body's inherited canonical omega is already counted above.
    for path, runtime in state.actions.items():
        if check is not None:
            check()
        if runtime.status != "running":
            continue
        action = model.actions[path]
        if action.kind == "spin":
            angular += norm_upper(action.vector)
        elif action.kind == "tween" and model.joints[action.target].kind == "hinge":
            _, rate = simulator._coordinate(action.target, time, state)
            angular += abs(Fraction(rate)) * norm_upper(model.joints[action.target].axis)
    return acceleration, angular


def force_prefix_plan(model: SceneModel, end: Fraction, *,
                      check: Callable[[], None] | None = None) -> ForcePrefixPlan:
    """Validate only ``[0, end]`` and discover its actual inclusive boundaries.

    Each returned interval uses its start's committed after-side state. The
    endpoint is processed for validity and metadata, but its outgoing motion
    does not inflate the prefix bounds. No geometry or snapshots are retained.
    The caller validates the target, endpoint options, and allocation budgets.
    """
    if check is not None:
        check()
    simulator = _PlanningSimulator(model, check=check)
    start = Fraction(0)
    simulator.advance(start, "after")
    boundaries = [start]
    intervals = []
    while start < end:
        if check is not None:
            check()
        next_boundary = simulator._next_boundary()
        stop = end if next_boundary is None or next_boundary > end else next_boundary
        acceleration, angular = _motion_bounds(simulator, start, check)
        intervals.append(ForceInterval(start, stop, acceleration, angular))
        simulator.advance(stop, "after")
        boundaries.append(stop)
        start = stop
    return ForcePrefixPlan(tuple(boundaries), tuple(intervals))


def force_interval_violation(plan: ForcePrefixPlan, start: Fraction, end: Fraction, *,
                             position_tolerance_m: float,
                             angular_step_rad: float = math.pi / 4,
                             source_start: Fraction | None = None,
                             source_end: Fraction | None = None,
                             check: Callable[[], None] | None = None) -> dict[str, Any] | None:
    """Check a source or binary32 key gap against rebuilt interval bounds.

    For stored keys, pass their corresponding exact ``source_start`` and
    ``source_end``. These select the semantic interval; ``end - start`` is the
    actual stored duration. Source/stored-clock pose probes separately check
    the displacement caused by a quantized boundary. All products are exact.
    """
    start, end = Fraction(start), Fraction(end)
    logical_start = start if source_start is None else Fraction(source_start)
    logical_end = end if source_end is None else Fraction(source_end)
    width = end - start
    if width <= 0 or logical_end <= logical_start:
        return {"kind": "clock", "message": "Key times must be strictly increasing."}
    first = max(0, bisect_right(plan.boundaries, logical_start) - 1)
    for index in range(first, len(plan.intervals)):
        if check is not None:
            check()
        interval = plan.intervals[index]
        if interval.start >= logical_end:
            break
        if interval.end <= logical_start:
            continue
        chord = interval.acceleration_bound * width * width / 8
        angle = interval.angular_speed_bound * width
        kind = ("position" if chord > Fraction(position_tolerance_m) / 4 else
                "rotation" if angle > Fraction(angular_step_rad) else None)
        if kind is not None:
            return {"kind": kind,
                    "source_interval_seconds": [time_text(interval.start), time_text(interval.end)],
                    "key_interval_seconds": [time_text(start), time_text(end)],
                    "acceleration_bound_m_per_s2": str(interval.acceleration_bound),
                    "angular_speed_bound_rad_per_s": str(interval.angular_speed_bound),
                    "chord_error_bound_m": str(chord),
                    "angular_step_bound_rad": str(angle)}
    return None
