"""Complete source-bound reach descriptions, samples and output accounting.

Service acceptance and run identities are deliberately absent here. Agent/0.6
binds only newly published projections at its atomic publication boundary.
"""
from __future__ import annotations

import copy
from dataclasses import asdict

from .diagnostics import seconds_text
from .json_limits import JSONLimitError, measure_json
from .reach_source import reach_error


def measure_reach_json(value, *, check=None, **limits):
    """Exact JSON accounting with the inherited bounded-data check batching.

    Every repeated value/container and byte is counted by measure_json. Work
    checkpoints consolidate its short-string callbacks into bounded batches;
    numerical arithmetic is never routed through this batching adapter.
    """
    pending = 0
    def checkpoint():
        nonlocal pending
        pending += 1
        if pending == 128:
            pending = 0
            check()
    result = measure_json(value, check=checkpoint if check is not None else None, **limits)
    if check is not None and pending:
        check()
    return result


def occurrence(model, path):
    collection = (model.actions if path in model.actions else
                  model.joints if path in model.joints else
                  model.sites if path in model.sites else model.objects)
    return {"path": path, "element_id": list(collection[path].element_id)}


def reach_projection(model, path, sample=None, *, check=None,
                     context_kind="recorded_prefix", current=None):
    """Return one complete projection from an actual current value or sample.

    Passing no sample/current is source-only inspection: it cannot manufacture
    pending state. The optional current argument is the simulator's already
    measured lifecycle value. A sample must contain its complete reaches map.
    """
    if check is not None:
        check()
    if sample is not None:
        if current is not None:
            raise ValueError("Supply either an actual sample or a current value.")
        result = copy.deepcopy(sample["reaches"][path])
        if result["current"]["available"]:
            result["current"]["value"]["observation"]["context_kind"] = context_kind
        return result
    action = model.actions[path]
    payload = action.reach
    if action.kind != "reach_planar" or payload is None or payload.base_frame is None:
        raise ValueError("A reach projection requires a fully bound named reach.")
    site = model.sites[payload.base_frame.removesuffix(".frame")]
    frame = {"path": payload.base_frame, "site_element_id": list(site.element_id)}
    value = copy.deepcopy(current)
    if value is not None:
        value["observation"]["context_kind"] = context_kind
        value["observation"]["run_id"] = None
    return {
        "kind": "reach_planar", "element_id": list(action.element_id),
        "description_identity": list(payload.description_identity),
        "program_revision": model.program_revision,
        "accepted_program_revision": None, "candidate_only": None,
        "context_origin": "source_recording", "source_location": asdict(payload.source_location),
        "channel": "joint_coordinates",
        "chain": {"shoulder": occurrence(model, payload.shoulder),
                  "elbow": occurrence(model, payload.elbow), "tip": occurrence(model, payload.tip),
                  "base_frame": frame, "lengths_m": list(payload.lengths_m),
                  "closed_limits_rad": {"shoulder": list(payload.limits_rad[0]),
                                        "elbow": list(payload.limits_rad[1])}},
        "target": {"type": "Point3", "frame": copy.deepcopy(frame),
                   "coordinates_m": list(payload.target_m)},
        "branch": payload.branch, "duration_seconds": seconds_text(action.duration),
        "current": {"available": value is not None, "reason": "run_required" if value is None else None,
                    "value": value},
    }


def _maximum_current(model, action):
    """A counting shape, never a claimed runtime observation.

    It deliberately combines all maximal fields, including claims and a terminal
    latch, although those cannot coexist. This is a conservative logical weight.
    """
    payload = action.reach
    pose = {"position_m": [0.0, 0.0, 0.0], "orientation_wxyz": [1.0, 0.0, 0.0, 0.0]}
    return {
        "observation": {"time_seconds": "0", "side": "before", "run_id": None,
                        "context_kind": "recorded_prefix"},
        "lifecycle": "completed", "goal_outcome": "satisfied",
        "resolved_joint_targets_rad": [0.0, 0.0], "start_coordinates_rad": [0.0, 0.0],
        "start_time_seconds": "0", "elapsed_seconds": "0", "completion_time_seconds": "0",
        "joint_coordinates_rad": [0.0, 0.0], "joint_rates_rad_per_s": [0.0, 0.0],
        "action_joint_rates_rad_per_s": [0.0, 0.0],
        "claimed_joint_ids": [list(model.joints[path].element_id) for path in (payload.shoulder, payload.elbow)],
        "current_residual_m": 0.0, "tip_pose_base": pose, "tip_pose_world": pose,
        "current_world_target_m": [0.0, 0.0, 0.0],
        "terminal_result": {"outcome": "satisfied", "time_seconds": "0", "position_residual_m": 0.0,
                            "joint_coordinates_rad": [0.0, 0.0], "tip_pose_base": pose},
    }


def reach_record_bound(model, *, check=None):
    """Preflight complete maximal R(t,side), including repeated identities."""
    count = 1  # The reaches map is a counted container even when empty.
    byte_count = 2
    for path, action in model.actions.items():
        if check is not None:
            check()
        if action.kind != "reach_planar":
            continue
        projection = reach_projection(model, path, check=check, current=_maximum_current(model, action))
        try:
            key_size = measure_reach_json(path, check=check)["bytes"] + 2
            measure = measure_reach_json(projection, max_entries=100000 - count,
                                         max_bytes=4 * 1024 * 1024 - byte_count - key_size, check=check)
        except JSONLimitError as error:
            raise reach_error("reach_resource", "Complete reach projections exceed the source output bound.",
                              action.span, phase="inspection", element_id=action.element_id,
                              details=error.details, blocks=[]) from error
        count += measure["entries"]
        byte_count += measure["bytes"] + key_size
    return count
