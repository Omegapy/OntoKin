"""Exact-clock COM force intervals for the explicit ``force-0.1`` profile.

This extends the inherited staged evaluator, not any earlier profile. Force
activation and completion are tentative until the complete boundary passes.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable

from .diagnostics import OntoKinError
from .evaluator import (
    MAX_OUTPUT_RECORDS, ZERO, _DynamicInitial, _Kinematics, _NumericFault,
    _RunState, _Simulator, _advance_orientation, _affine, _f, _round, time_text,
)
from .json_limits import JSONLimitError, MAX_JSON_BYTES, measure_json
from .model import Event, ForcePayload, SceneModel, Vec


@dataclass(frozen=True)
class _ActiveForce:
    target: str
    payload: ForcePayload
    activation: Fraction

    @property
    def completion(self) -> Fraction:
        return self.activation + self.payload.duration


@dataclass
class _ForceState:
    active: dict[str, _ActiveForce] = field(default_factory=dict)
    net: Vec = ZERO
    acceleration: Vec | None = None
    started_count: int = 0
    completed_count: int = 0
    last_time: Fraction | None = None
    last_changes: list[tuple[str, _ActiveForce]] = field(default_factory=list)


@dataclass
class _ForceRunState(_RunState):
    forces: dict[str, _ForceState] = field(default_factory=dict)


def _record(model: SceneModel, force: _ActiveForce) -> dict[str, Any]:
    payload = force.payload
    return {
        'force_key': payload.key,
        'force_element_id': [model.module_key, model.scene_key, 'force', payload.key],
        'target_path': force.target,
        'target_element_id': list(model.objects[force.target].element_id),
        'program_revision': model.program_revision,
        'source_location': dict(payload.source),
        'sequence_index': payload.sequence_index,
        'force_world_n': list(payload.force_world_n),
        'activation_time_seconds': time_text(force.activation),
        'duration_seconds': time_text(payload.duration),
        'completion_time_seconds': time_text(force.completion),
    }


def _resource(model: SceneModel, details: dict[str, Any]) -> OntoKinError:
    return OntoKinError(
        'OKL-E-RESOURCE', 'Complete force history exceeds the bounded output contract.',
        model.span, category='resource_limit', phase='inspection', blocks=[],
        rule_ids=['FOR-004'], details=details,
        repair='Use fewer force intervals or request a smaller certified prefix.')


def force_record_bound(model: SceneModel, *, constructing: bool = False,
                       horizon: Fraction | None = None, side: str = "after",
                       check: Callable[[], None] | None = None) -> int:
    """Bound complete active/latest histories without evaluating future physics.

    The sweep counts nested JSON entries on every occurrence. Equal clocks
    share a boundary, so an expiring record and its replacement are accounted
    for as one final active set and one latest change group.
    """
    base = 14 * len(model.objects)
    if constructing:
        return base
    horizon = model.duration if horizon is None else horizon
    boundaries: dict[Fraction, list[tuple[str, str, str, int]]] = {}
    for block in sorted(model.events, key=lambda block: block.time):
        if check is not None:
            check()
        if block.time > horizon or (block.time == horizon and side == "before"):
            break
        for event in block.events:
            if check is not None:
                check()
            if event.kind != 'force' or event.force is None:
                continue
            force = _ActiveForce(event.target, event.force, block.time)
            try:
                weight = measure_json(_record(model, force), check=check)['entries']
            except JSONLimitError as exc:
                raise _resource(model, exc.details) from exc
            boundaries.setdefault(block.time, []).append(('started', event.target, event.force.key, weight))
            if force.completion < horizon or (force.completion == horizon and side == "after"):
                boundaries.setdefault(force.completion, []).append(('completed', event.target, event.force.key, weight))
    active: dict[tuple[str, str], int] = {}
    latest: dict[str, int] = {}
    total_active = total_latest = maximum = 0
    for _, entries in sorted(boundaries.items()):
        changes: dict[str, int] = {}
        for kind, target, key, weight in entries:
            if check is not None:
                check()
            identity = (target, key)
            if kind == 'completed':
                total_active -= active.pop(identity)
            else:
                active[identity] = weight
                total_active += weight
            changes[target] = changes.get(target, 0) + weight + 1  # kind field
        for target, weight in changes.items():
            total_latest += weight - latest.get(target, 0)
            latest[target] = weight
        maximum = max(maximum, total_active + total_latest)
    return base + maximum


class ForceSimulator(_Simulator):
    """Profile-specific forces with the inherited release/impulse transaction."""

    def __init__(self, model: SceneModel, check: Callable[[], None] | None = None):
        super().__init__(model, check=check)
        self.state = _ForceRunState(**vars(self.state))
        for path, obj in model.objects.items():
            self._check()
            self.state.forces[path] = _ForceState(
                acceleration=model.gravity if obj.motion == 'dynamic' else None)

    def _check(self) -> None:
        if self.check is not None:
            self.check()

    def _acceleration(self, path: str, state: _ForceRunState) -> Vec:
        value = state.forces[path].acceleration
        # A just-released body has the inherited gravity until final force
        # aggregation; its saved incoming pose remains the trajectory anchor.
        return self.model.gravity if value is None else value

    def _dynamic_kinematics(self, path: str, time: Fraction, state: _ForceRunState) -> _Kinematics:
        self._check()
        anchor = state.dynamic[path]
        elapsed = time - anchor.time
        initial = anchor.state
        acceleration = self._acceleration(path, state)
        position = tuple(_round(_f(p) + _f(v) * elapsed + _f(a) * elapsed * elapsed / 2)
                         for p, v, a in zip(initial.position, initial.velocity, acceleration))
        return _Kinematics(position, _advance_orientation(initial.orientation, initial.omega, elapsed),
                           _affine(initial.velocity, acceleration, elapsed), initial.omega)

    def _next_boundary(self) -> Fraction | None:
        next_time = super()._next_boundary()
        for history in self.state.forces.values():
            self._check()
            for force in history.active.values():
                self._check()
                if next_time is None or force.completion < next_time:
                    next_time = force.completion
        return next_time

    @staticmethod
    def _change(history: _ForceState, time: Fraction, kind: str, force: _ActiveForce) -> None:
        if history.last_time != time:
            history.last_time = time
            history.last_changes = []
        history.last_changes.append((kind, force))

    def _event(self, event: Event, time: Fraction, state: _ForceRunState,
               incoming, dependencies, touched) -> None:
        if event.kind != 'force':
            super()._event(event, time, state, incoming, dependencies, touched)
            return
        self._check()
        obj = self.model.objects.get(event.target)
        if obj is None or event.force is None:
            raise OntoKinError('OKL-E-TYPE', 'A force requires a resolved object and source operands.',
                               event.span, phase='admission', time=time, rule_ids=['FOR-001'])
        if state.modes[event.target] != 'dynamic' or event.target in self._incoming(state):
            raise OntoKinError(
                'OKL-E-MOTION-MODE', 'A force requires a currently free dynamic sphere.', event.span,
                phase='admission', time=time, side='after', rule_ids=['FOR-002'],
                element_id=list(obj.element_id), related=[obj.span],
                details={'target_path': event.target, 'force_key': event.force.key,
                         'sequence_index': event.force.sequence_index, 'motion': state.modes[event.target]},
                repair='Release a prescribed sphere earlier in this sequence, or use a free dynamic sphere.')
        if obj.physical.get('kind') != 'sphere_body' or obj.mass <= 0 or obj.inertia is None or obj.inertia <= 0:
            raise OntoKinError('OKL-E-PHYSICAL-DOMAIN', 'A force requires positive own sphere mass and inertia.',
                               event.span, phase='admission', time=time, rule_ids=['FOR-002'])
        history = state.forces[event.target]
        force = _ActiveForce(event.target, event.force, time)
        history.active[event.force.key] = force
        history.started_count += 1
        self._change(history, time, 'started', force)

    def _projection(self, path: str, state: _ForceRunState) -> dict[str, Any]:
        history = state.forces[path]
        active = []
        for key in sorted(history.active):
            self._check()
            active.append(_record(self.model, history.active[key]))
        changes = []
        for kind, force in history.last_changes:
            self._check()
            changes.append({'kind': kind, **_record(self.model, force)})
        return {'active': active, 'net_force_world_n': list(history.net),
                'acceleration_world_m_per_s2': (list(history.acceleration)
                                               if history.acceleration is not None else None),
                'started_count': history.started_count, 'completed_count': history.completed_count,
                'last_change_time_seconds': (time_text(history.last_time)
                                             if history.last_time is not None else None),
                'last_changes': changes}

    def _bounded_projection(self, state: _ForceRunState) -> dict[str, dict[str, Any]]:
        result = {}
        entries = byte_count = 0
        for path in state.forces:
            self._check()
            projection = self._projection(path, state)
            try:
                size = measure_json(projection, max_entries=MAX_OUTPUT_RECORDS - entries,
                                    max_bytes=MAX_JSON_BYTES - byte_count, check=self.check)
            except JSONLimitError as exc:
                raise _resource(self.model, exc.details) from exc
            entries += size['entries']
            byte_count += size['bytes']
            result[path] = projection
        return result

    def _aggregate(self, path: str, time: Fraction, state: _ForceRunState) -> None:
        history = state.forces[path]
        if state.modes[path] != 'dynamic':
            history.acceleration = None
            return
        self._check()
        try:
            sums = [Fraction(0), Fraction(0), Fraction(0)]
            for key in sorted(history.active):
                self._check()
                for index, value in enumerate(history.active[key].payload.force_world_n):
                    sums[index] += _f(value)
            net = tuple(_round(value) for value in sums)
            mass = _f(self.model.objects[path].mass)
            acceleration = tuple(_round(_f(g) + _f(f) / mass)
                                 for g, f in zip(self.model.gravity, net))
            if acceleration != self._acceleration(path, state):
                anchor = state.dynamic[path]
                current = self._dynamic_kinematics(path, time, state)
                state.dynamic[path] = _DynamicInitial(time, current, anchor.since)
            history.net = net
            history.acceleration = acceleration
        except _NumericFault as exc:
            changes = sorted(history.last_changes if history.last_time == time else [],
                             key=lambda item: item[1].payload.key)
            records = []
            for kind, force in changes:
                self._check()
                records.append({'kind': kind, **_record(self.model, force)})
            primary = self.model.objects[path].span
            if changes:
                payload = changes[0][1].payload
                for block in self.model.events:
                    self._check()
                    match = next((e.span for e in block.events if e.force is payload or
                                  (e.force is not None and e.force.key == payload.key)), None)
                    if match is not None:
                        primary = match
                        break
            raise OntoKinError(
                'OKL-E-NUMERIC', str(exc), primary, category='numerical_failure', phase='evaluation',
                time=time, side='after', rule_ids=['FOR-002', 'FOR-003'],
                element_id=list(self.model.objects[path].element_id), blocks=['evaluated', 'delivered'],
                details={'target_path': path, 'operation': 'final_active_force_aggregation',
                         'changed_forces': records},
                repair='Use force intervals whose final canonical net force and acceleration are finite.') from exc

    def _process_boundary(self, time: Fraction) -> None:
        self._check()
        incoming, _ = self._kinematics(time, self.state)
        dependencies = {path: self._dependencies(self.model.sites[self.model.joints[path].child].owner, self.state)
                        for path in self.state.active_grips}
        staged = copy.deepcopy(self.state)
        for path, runtime in staged.actions.items():
            self._check()
            if runtime.status == 'running' and runtime.elapsed_at(time) == self.model.actions[path].duration:
                self._latch(path, time, staged, 'completed')
        for history in staged.forces.values():
            self._check()
            for key in sorted(history.active):
                self._check()
                force = history.active[key]
                if force.completion == time:
                    del history.active[key]
                    history.completed_count += 1
                    self._change(history, time, 'completed', force)
        has_source = self.event_index < len(self.events) and self.events[self.event_index].time == time
        if has_source:
            touched: set[tuple[str, str]] = set()
            for event in self.events[self.event_index].events:
                self._check()
                self._event(event, time, staged, incoming, dependencies, touched)
        for path in staged.forces:
            self._aggregate(path, time, staged)
        self._kinematics(time, staged)
        self._bounded_projection(staged)
        self._check()
        self.state = staged
        if has_source:
            self.event_index += 1
        self.zero_pending = False
        self.last_boundary = time
        self.boundaries.append(time_text(time))

    def _check_dynamic_extrema(self, start: Fraction, end: Fraction) -> None:
        for path, anchor in self.state.dynamic.items():
            self._check()
            for velocity, acceleration in zip(anchor.state.velocity, self._acceleration(path, self.state)):
                if acceleration:
                    extremum = anchor.time - _f(velocity) / _f(acceleration)
                    if start < extremum < end:
                        self._kinematics(extremum, self.state)

    def snapshot(self, time: Fraction, side: str) -> dict[str, Any]:
        result = super().snapshot(time, side)
        for path, projection in self._bounded_projection(self.state).items():
            result['objects'][path]['forces'] = projection
        return result
