"""Retain a recording plan from the Agent's one checked source-prefix replay.

This transient adapter keeps the original request's model, numerical work and
source observations. It does not publish Agent identity into recording data,
replay future events, reset budgets, or replace the supplied-byte validator.
"""
from __future__ import annotations

import copy
from fractions import Fraction


class ReachDeliveryCapture:
    """Internal evaluate_prefix observer with preflight before every retention."""

    def __init__(self, model, end, *, work):
        self.model = model
        self.end = Fraction(end)
        self.work = work
        self.times = []
        self.phases = []
        self.states = []
        self.records = []
        self.before = None
        self.final_state = None
        self.simulator = None

    def before_capture(self, simulator, time, side):
        from .reach_numeric import ReachAdmissionError

        try:
            self._before_capture(simulator, time, side)
        except ReachAdmissionError as error:
            simulator._numeric_error(error, time=time)

    def _before_capture(self, simulator, time, side):
        from . import reach_export
        from .reach_runtime import boundary_history_bound
        from .scene import MAX_KEYFRAMES

        if simulator.model is not self.model or simulator.work is not self.work:
            raise ValueError("A recording capture must share the source request context.")
        if self.simulator is None:
            reach_export.recording_stage("planning", work=self.work)
            self.simulator = simulator
        if self.times and self.times[-1] == time:
            return
        if side != "before" or (self.times and time <= self.times[-1]):
            raise ValueError("Recording captures must retain both sides in increasing source time.")
        self.work.charge("recording_boundary_preflight")
        if len(self.times) >= MAX_KEYFRAMES:
            reach_export._fail("OKE-E-KEYFRAME-BUDGET", "Semantic boundaries exceed the recording key budget.",
                               model=self.model, kind="resource")
        boundary_history_bound(self.model, [*self.times, time], horizon=self.end, check=self.work.tick)
        self.times.append(time)

    def after_capture(self, simulator, time, side, sample):
        from .reach_numeric import ReachAdmissionError

        try:
            self._after_capture(simulator, time, side, sample)
        except ReachAdmissionError as error:
            simulator._numeric_error(error, time=time)

    def _after_capture(self, simulator, time, side, sample):
        from . import reach_export

        if side == "before":
            self.before = sample
            return
        if self.before is None or len(self.records) != len(self.times) - 1:
            raise ValueError("A recording after-state requires its actual checked before-state.")
        self.records.append(reach_export._boundary_record(
            time, self.before, sample, simulator.incoming_releases_at(time)))
        self.before = None
        self.work.charge("recording_phase_anchor")
        if time == self.end:
            self.final_state = copy.deepcopy(simulator.state)
            return
        following = simulator._next_boundary()
        stop = self.end if following is None or following > self.end else following
        if stop <= time:
            reach_export._fail("OKE-E-PHASE-COVERAGE", "The validated prefix did not advance to a later boundary.",
                               model=self.model)
        reach_export.recording_stage("planning_phase", work=self.work)
        source = reach_export.recording_phase_bounds(simulator, time, stop)
        carriers = {path: reach_export.MotionBound(value.carrier_speed_upper_m_per_s,
                                                  value.carrier_acceleration_upper_m_per_s2,
                                                  value.angular_speed_upper_rad_per_s)
                    for path, value in source.items()}
        self.phases.append(reach_export.ReachPhase(time, stop, carriers, source))
        self.states.append(copy.deepcopy(simulator.state))

    def finish(self):
        """Expose only a complete successful prefix to the explicit exporter."""
        from .reach_export import ReachPrefixPlan

        if (self.final_state is None or self.before is not None or not self.times
                or self.times[0] != 0 or self.times[-1] != self.end
                or len(self.records) != len(self.times)
                or len(self.phases) != len(self.times) - 1
                or len(self.states) != len(self.phases)):
            raise ValueError("An incomplete or failed source prefix cannot authorize a recording plan.")
        return ReachPrefixPlan(tuple(self.times), tuple(self.phases), tuple(self.states), self.final_state,
                               tuple(self.records), self.simulator)
