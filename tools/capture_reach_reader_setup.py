#!/usr/bin/env python3
"""Capture bounded independent-reader setup and original P11/L03 endpoints.

The C060 envelope wrappers retain gltf.validate_export, _key_comparisons and
recording_stage. Eighteen additional higher-level boundaries cover reader setup.
Each wrapper invokes its saved original exactly once.
Observations use detached native fields, never charged cache/source helpers.
The scoped diagnostic runner retains the actual failed request and exit status.
C061 retains the C060 request/key collector and adds reader-only setup spans.
All setup wrappers are removed at the first key entry and in final cleanup.
Nested function costs and repeated typed inputs are observations, not reuse proof.
Tracked omissions are explicit; this does not execute the complete stock harness.
Collector-specific JSON and binary output is written after the product request has ended.
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys
import traceback
from types import FunctionType, MethodType


def ratio(value):
    assert type(value) is Fraction
    numerator = object.__getattribute__(value, "_numerator")
    denominator = object.__getattribute__(value, "_denominator")
    assert type(numerator) is int and type(denominator) is int and denominator > 0
    assert max(abs(numerator).bit_length(), denominator.bit_length()) <= 32768
    return {"numerator": numerator, "denominator": denominator}


def decimal(value):
    """Convert bounded diagnostic integers after execution, without global changes."""
    if not value:
        return "0"
    sign, value = ("-", -value) if value < 0 else ("", value)
    chunks = []
    while value:
        value, remainder = divmod(value, 10 ** 1000)
        chunks.append(remainder)
    return sign + str(chunks[-1]) + "".join(f"{part:01000d}" for part in reversed(chunks[:-1]))


def serializable(value):
    if type(value) is dict:
        if set(value) == {"numerator", "denominator"} and all(type(v) is int for v in value.values()):
            return {name: decimal(number) for name, number in value.items()}
        return {name: serializable(item) for name, item in value.items()}
    if type(value) in (list, tuple):
        return [serializable(item) for item in value]
    if type(value) is int and abs(value).bit_length() > 4096:
        return {"integer_decimal": decimal(value)}
    return value


def write_json(path, value):
    raw = (json.dumps(serializable(value), indent=2, allow_nan=False) + "\n").encode()
    assert len(raw) <= 64 * 1024 * 1024
    with Path(path).open("xb") as stream:
        stream.write(raw)


def descriptor(path):
    raw = Path(path).read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def callable_name(value):
    if value is None:
        return None
    if type(value) is MethodType:
        fn, owner = value.__func__, type(value.__self__).__qualname__
    else:
        fn, owner = value, None
    assert type(fn) is FunctionType
    return {"module": fn.__module__, "qualname": fn.__qualname__, "bound_owner_type": owner}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--case", choices=("P11", "L03"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.repo.resolve(), args.output_dir.resolve()
    assert not output.exists() and not output.is_relative_to(root)
    assert all(not path.is_symlink() for path in (args.output_dir.absolute(), *args.output_dir.absolute().parents))
    output.mkdir(parents=True)
    sys.path.insert(0, str(root))
    from tools.probe_reach_recording_work import build
    from ontokin import gltf, reach_conformance as rc, reach_reference as rr, scene
    from ontokin import reach_export as exporter
    from ontokin import reach_reference_center as center, reach_reference_plan as plans
    from ontokin.construction import ConstructionBudget
    from ontokin.reach_numeric import ReachExecutionWork

    assert sys.gettrace() is None and sys.getprofile() is None
    validate_original, key_original = gltf.validate_export, rc._key_comparisons
    stage_original = exporter.recording_stage
    stage_events = []
    dispatch = [(gltf, "export_glb", gltf.export_glb),
                (ConstructionBudget, "tick", ConstructionBudget.tick),
                (ConstructionBudget, "exceeded", ConstructionBudget.exceeded)]
    for owner, names in (
        (ReachExecutionWork, ("charge", "tick", "lookup", "remember", "guard_bits", "record")),
        (rc._Bounds, ("add", "mul", "div", "square", "op", "bits", "tick", "value", "compare", "total")),
        (rr._Arithmetic, ("exact", "tick", "lookup", "remember", "sincos", "_series_coefficients")),
        (rr.ReachReference, ("_recording_centered_poses", "recording_pose_enclosures", "_state_at")),
        (center, ("evaluate", "_orientation", "_offset", "_seed", "_coefficients")),
        (center._Guard, ("checked", "original", "exact", "lookup", "remember")),
    ):
        dispatch.extend((owner, name, getattr(owner, name)) for name in names)
    frozen_fields = {
        center._CenteredCursor: ("witness", "axis", "rate", "clock", "orientation", "radius", "increment", "steps", "seal"),
        center._CenteredPose: ("position", "orientation", "position_radius", "orientation_radius", "axis", "seal"),
        center._CenteredNode: ("vector", "position_radius", "identity_offset", "coefficient_source", "seal"),
        rr._RecordingBodyRate: ("axis", "rate", "moving", "witness", "path", "zero_origin", "identity_relative", "coordinate_rate"),
        plans._Node: ("path", "kind", "parent", "body", "relation", "axis", "stationary", "source_stationary"),
    }

    def frozen(value, depth=0, tally=None):
        """Copy only native primitive fields; never call a source helper/getter."""
        tally = [0] if tally is None else tally
        tally[0] += 1
        assert depth <= 24 and tally[0] <= 16384
        kind = type(value)
        if value is None or kind in (bool, str, float):
            if kind is str:
                assert len(value) <= 4096
            return value
        if kind is int:
            assert abs(value).bit_length() <= 32768
            return value
        if kind is Fraction:
            return ratio(value)
        if kind is object:
            return {"opaque_object_id": id(value)}
        if kind is rr.Interval:
            return {"interval": {name: frozen(object.__getattribute__(value, name), depth + 1, tally)
                                 for name in ("lo", "hi")}}
        if kind in (tuple, list):
            assert len(value) <= 4096
            return tuple(frozen(item, depth + 1, tally) for item in value)
        if kind is dict:
            assert len(value) <= 1024 and all(type(key) in (str, int) for key in value)
            return {key: frozen(item, depth + 1, tally) for key, item in value.items()}
        if kind in frozen_fields:
            own = object.__getattribute__(value, "__dict__")
            assert type(own) is dict
            return {"type": kind.__name__, **{name: frozen(own[name], depth + 1, tally)
                                             for name in frozen_fields[kind]}}
        raise TypeError("Unsupported native observation type: " + kind.__name__)

    retained = {"reader_calls": 0, "key_calls": 0}
    ledger, observation_errors, failure_frames = [], [], []
    source_boundaries, geometry_rows, track_rows = [], [], []

    def observe(label, function, *arguments):
        # An observation defect must never mask an original product exception.
        try:
            return function(*arguments)
        except Exception as error:
            observation_errors.append({"boundary": label, "type": type(error).__name__, "message": str(error)})
            return None

    def record(work):
        assert type(work) is ReachExecutionWork
        own = object.__getattribute__(work, "__dict__")
        assert type(own["counts"]) is dict and len(own["counts"]) <= 512
        assert all(type(name) is str and type(value) is int for name, value in own["counts"].items())
        assert type(own["_cache"]) is OrderedDict and len(own["_cache"]) <= 256
        return {"operations": own["operations"], "counts": dict(own["counts"]),
                "cache_entries": len(own["_cache"])}

    def source_state(reference, arithmetic):
        assert type(reference) is rr.ReachReference and type(arithmetic) is rc._Bounds
        work, source = arithmetic.work, reference.a
        assert work is retained["work"] and type(source) is rr._Arithmetic and source.work is work
        assert type(source.cache) is dict and len(source.cache) <= 256
        categories, cursors = {}, []
        for key, value in source.cache.items():
            assert type(key) is tuple and key and type(key[0]) is str
            category = key[0]
            if category == "reference_pose" and len(key) > 3 and type(key[3]) is str:
                category += ":" + key[3]
            categories[category] = categories.get(category, 0) + 1
            if type(value) is center._CenteredCursor:
                cursors.append({"key": frozen(key), "value": frozen(value)})
        batch = reference._recording_batch
        batch_record = None
        if batch is not None:
            assert type(batch) is plans._SourceBatch and type(batch.plans) is dict and len(batch.plans) <= 16
            assert type(batch.cursors) is dict and len(batch.cursors) <= 256
            batch_record = {"active": batch.active, "prepared": batch.prepared, "depth": batch.depth,
                "plans": [{"cache_identity": frozen(identity), "context": frozen(plan.context),
                           "targets": frozen(plan.targets), "remaining": frozen(plan.remaining),
                           "registered_time": ratio(time), "node_paths": tuple(node.path for node in plan.nodes)}
                          for identity, (plan, time) in batch.plans.items()],
                "cursor_ledger_entries": len(batch.cursors), "receipt_entries": len(batch.receipts)}
        return {"shared_operations": retained["budget"].operations, "reach": record(work),
                "source_cache_entries": len(source.cache), "source_cache_categories": categories,
                "source_cursors": cursors, "source_batch": batch_record}

    def capture_inputs(reference, geometry, tracks):
        assert type(reference.boundaries) is tuple and len(reference.boundaries) <= 10000
        assert type(geometry) is dict and 0 < len(geometry) <= 64
        assert type(tracks) is dict and tracks.keys() == geometry.keys()
        source_boundaries.extend(ratio(value) for value in reference.boundaries)
        for carrier, item in geometry.items():
            assert type(carrier) is int and type(item) is dict and type(item["frame"]) is str
            geometry_rows.append({"carrier": carrier, "frame": item["frame"], "identity": frozen(item["identity"])})
            channel = tracks[carrier]
            assert type(channel) is dict and set(channel) == {"translation", "rotation"}
            translated, rotated = channel["translation"], channel["rotation"]
            assert type(translated) in (list, tuple) and type(rotated) in (list, tuple)
            assert len(translated) == len(rotated) and 0 < len(translated) <= 256
            assert len(translated) * len(geometry) <= 250000
            for values, size in ((translated, 3), (rotated, 4)):
                assert all(type(row) in (list, tuple) and len(row) == size and
                           all(type(value) in (float, int) for value in row) for row in values)
            track_rows.append({"carrier": carrier,
                "translation": tuple(tuple(row) for row in translated),
                "rotation": tuple(tuple(row) for row in rotated)})

    def selected_failure_locals(error):
        rows, seen = [], set()
        current = error.__traceback__
        traversed = 0
        while current is not None:
            traversed += 1
            assert traversed <= 512
            frame, code = current.tb_frame, current.tb_frame.f_code
            filename, function = code.co_filename, code.co_name
            local = frame.f_locals
            selected = {}
            if filename == center.__file__:
                names = {
                    "_orientation": ("node", "body", "time", "context", "axis", "rate", "clock", "key", "previous",
                                     "advance", "old_clock", "old_rate", "old_rotation", "old_radius", "old_increment",
                                     "increment", "steps", "elapsed", "product", "delta"),
                    "_offset": ("parent", "vector", "identity_only", "coefficient_source", "q", "radius", "axis",
                                "order", "x", "y", "z", "w", "s", "diagonal", "cross"),
                    "product": ("first", "last"),
                    "combined": ("first", "last", "subtract"),
                    "evaluate": ("time", "node", "recipe", "vector", "maximum_radius", "parent", "key"),
                }.get(function, ())
                selected = {name: frozen(local[name]) for name in names if name in local}
                if function == "evaluate":
                    if type(local.get("frames")) is dict:
                        selected["completed_frames"] = tuple(local["frames"])
                    pending = local.get("pending")
                    if type(pending) is plans._PendingCursors:
                        assert len(pending.values) <= 32
                        selected["pending_values"] = [{"key": frozen(key), "value": frozen(value),
                                                       "previous": frozen(previous)}
                                                      for key, value, previous in pending.values]
            elif filename == rc.__file__ and function == "_key_comparisons":
                selected = {name: frozen(local[name]) for name in ("index", "time", "previous_time") if name in local}
                selected["result_carriers"] = tuple(local.get("result", {}))
                selected["candidates"] = frozen(local.get("candidates", ()))
                for name in ("pending", "observed"):
                    values = local.get(name, ())
                    assert type(values) in (list, tuple) and len(values) <= 64
                    selected[name] = [{"carrier": value[0], "frame": value[1]["frame"],
                                       "position": frozen(value[2]), "quaternion": frozen(value[3]),
                                       **({"same": value[4], "limits": frozen(value[5])} if name == "observed"
                                          else {"limits": frozen(value[4])})} for value in values]
            elif filename == rr.__file__ and function in ("exact", "_series_coefficients", "_series_integer"):
                names = ("a", "b", "kind") if function == "exact" else (
                    ("common", "odd", "index", "degree", "exponent", "denominator", "lane", "coefficient", "packed")
                    if function == "_series_coefficients" else ("a", "b", "kind"))
                selected = {name: frozen(local[name]) for name in names
                            if name in local and type(local[name]) in (str, int, float, Fraction, bool)}
            if selected:
                identity = (id(frame), current.tb_lineno)
                if identity not in seen:
                    rows.append({"file": filename, "line": current.tb_lineno, "function": function, "locals": selected})
                    seen.add(identity)
            current = current.tb_next
        return rows

    # The original request/key observations above remain intact. Additional
    # wrappers exist only while the native reader initializes; low-level
    # arithmetic, charged callbacks and native admission dispatch are untouched.
    MAX_SETUP_SPANS = 4096
    setup_spans, setup_stack, setup_targets, setup_restorations = [], [], [], []
    setup = {"active": False, "disabled": False, "cutoff": None,
             "entry": None, "installations": 0, "recursive_forwards": {},
             "reference": None, "restored_before_first_key": False, "event_counter": 0}

    def next_setup_event():
        value = setup["event_counter"]
        setup["event_counter"] += 1
        return value

    def typed_setup(value, depth=0, tally=None):
        """Detach bounded native operands with their exact Python type tags."""
        tally = [0] if tally is None else tally
        tally[0] += 1
        assert depth <= 8 and tally[0] <= 512
        kind = type(value)
        if value is None:
            return {"type": "NoneType"}
        if kind is bool:
            return {"type": "bool", "value": value}
        if kind is int:
            assert abs(value).bit_length() <= 32768
            return {"type": "int", "value": value}
        if kind is float:
            return {"type": "float", "hex": value.hex()}
        if kind is str:
            assert len(value) <= 4096
            return {"type": "str", "value": value}
        if kind is Fraction:
            return {"type": "Fraction", "value": ratio(value)}
        if kind is rr.Interval:
            own = object.__getattribute__(value, "__dict__")
            assert type(own) is dict
            return {"type": "Interval", "lo": typed_setup(own["lo"], depth + 1, tally),
                    "hi": typed_setup(own["hi"], depth + 1, tally)}
        if kind in (tuple, list):
            assert len(value) <= 128
            return {"type": kind.__name__,
                    "items": tuple(typed_setup(item, depth + 1, tally) for item in value)}
        raise TypeError("Unsupported setup operand type: " + kind.__name__)

    def setup_cache(reference):
        if reference is None:
            return None
        assert type(reference) is rr.ReachReference
        own = object.__getattribute__(reference, "__dict__")
        arithmetic = own["a"]
        assert type(arithmetic) is rr._Arithmetic
        arithmetic_own = object.__getattribute__(arithmetic, "__dict__")
        assert arithmetic_own["work"] is retained["work"]
        cache = arithmetic_own["cache"]
        assert type(cache) is dict and len(cache) <= 256
        categories = {}
        for key in cache:
            category = key[0] if type(key) is tuple and key and type(key[0]) is str else "<other-native-key>"
            assert len(category) <= 4096
            categories[category] = categories.get(category, 0) + 1
        sizes = {}
        for name in ("_targets", "_poses", "_phase_cache", "_basis_cache"):
            value = own.get(name)
            if value is not None:
                assert type(value) is dict and len(value) <= 256
                sizes[name] = len(value)
        return {"reference_identity": id(reference), "arithmetic_identity": id(arithmetic),
                "arithmetic_bits": arithmetic_own["bits"],
                "operand_limit_field": object.__getattribute__(retained["work"], "__dict__")["max_operand_bits"],
                "arithmetic_entries": len(cache), "arithmetic_categories": categories,
                "other_existing_cache_entries": sizes}

    def setup_snapshot(*, full=False, reference=None):
        work = retained["work"]
        assert type(work) is ReachExecutionWork and type(retained["budget"]) is ConstructionBudget
        own = object.__getattribute__(work, "__dict__")
        budget_own = object.__getattribute__(retained["budget"], "__dict__")
        counts = own["counts"]
        assert type(counts) is dict and len(counts) <= 512
        assert all(type(key) is str and type(value) is int and value >= 0 for key, value in counts.items())
        result = {"shared_operations": budget_own["operations"],
                  "reach_operations": own["operations"], "checkpoint": counts.get("checkpoint", 0)}
        assert all(type(value) is int and value >= 0 for value in result.values())
        if full:
            result["counts"] = dict(counts)
            assert type(own["_cache"]) is OrderedDict and len(own["_cache"]) <= 256
            result["work_cache_entries"] = len(own["_cache"])
            result["reference_cache"] = setup_cache(reference if reference is not None else setup["reference"])
        return result

    def setup_input(label, positional, keywords):
        if label in ("reference._phase", "reference._axial_derivatives"):
            assert len(positional) == 5 and not keywords
            reference, carrier, start, end, state = positional
            assert type(reference) is rr.ReachReference and type(state) is rr._State
            assert type(carrier) is str
            own = object.__getattribute__(reference, "__dict__")
            return {"reference_identity": id(reference), "state_identity": id(state),
                    "model_identity": id(own["model"]), "carrier": carrier,
                    "start": typed_setup(start), "end": typed_setup(end),
                    "arithmetic_bits": object.__getattribute__(own["a"], "__dict__")["bits"],
                    "operand_limit_field": object.__getattribute__(retained["work"], "__dict__")["max_operand_bits"]}
        if label == "reference._l1":
            assert len(positional) == 2 and not keywords and type(positional[0]) is rr.ReachReference
            return {"reference_identity": id(positional[0]), "vector": typed_setup(positional[1])}
        if label == "reference._axis_transport":
            assert len(positional) == 3 and not keywords and type(positional[0]) is rr.ReachReference
            return {"reference_identity": id(positional[0]), "rotation": typed_setup(positional[1]),
                    "axis": typed_setup(positional[2])}
        return None

    def setup_result(label, result):
        if label == "reference._axial_derivatives":
            if result is None:
                return {"type": "NoneType"}
            assert type(result) is rr._AxialDerivative
            own = object.__getattribute__(result, "__dict__")
            assert type(own) is dict
            return {"type": "_AxialDerivative", **{name: typed_setup(own[name])
                    for name in ("speed", "acceleration", "axis", "rate")}}
        if label == "reference._phase":
            assert type(result) is rr.ReferencePhase
            own = object.__getattribute__(result, "__dict__")
            assert type(own) is dict
            return {"type": "ReferencePhase", **{name: typed_setup(own[name])
                    for name in ("start", "end", "carrier", "speed", "acceleration", "angular_speed", "path")}}
        if label in ("reference._l1", "reference._axis_transport"):
            return typed_setup(result)
        return None

    def enter_setup_span(label, nested, positional, keywords):
        assert len(setup_spans) < MAX_SETUP_SPANS and len(setup_stack) < 64
        reference = positional[0] if positional and type(positional[0]) is rr.ReachReference else None
        row = {"id": len(setup_spans), "parent": setup_stack[-1]["id"] if setup_stack else None,
               "label": label, "nested": nested, "outcome": "entered", "depth": len(setup_stack),
               "entry_event": next_setup_event(),
               "positional_count": len(positional), "keyword_names": tuple(keywords),
               "entry": setup_snapshot(full=not nested, reference=reference)}
        if nested:
            row["input"] = setup_input(label, positional, keywords)
        setup_spans.append(row)
        setup_stack.append(row)
        return row

    def leave_setup_span(row, nested, positional, keywords, saved):
        reference = positional[0] if positional and type(positional[0]) is rr.ReachReference else None
        row["exit"] = (setup["cutoff"] if not setup["active"] and setup["cutoff"] is not None
                       else setup_snapshot(full=not nested, reference=reference))
        work_own = object.__getattribute__(retained["work"], "__dict__")
        external = work_own["external_check"]
        row["identity_checks"] = {
            "positional_objects_preserved": len(positional) == len(saved["positional"]) and
                all(value is prior for value, prior in zip(positional, saved["positional"])),
            "keyword_objects_preserved": tuple(keywords) == tuple(saved["keywords"]) and
                all(keywords[name] is value for name, value in saved["keywords"].items()),
            "work_owner_preserved": retained["work"] is saved["work"],
            "external_callback_preserved": external is saved["external"],
            "callback_owner_preserved": type(external) is MethodType and
                external.__self__ is retained["budget"] and external.__func__ is ConstructionBudget.tick,
            "work_observer_preserved": work_own["_source_after_charge"] is saved["observer"],
        }
        row["exit_event"] = next_setup_event()
        row["clipped_at_first_key"] = not setup["active"] and setup["cutoff"] is not None
        assert setup_stack and setup_stack[-1] is row
        setup_stack.pop()

    def make_setup_wrapper(original, label, *, nested=False, axial_only=False):
        def capture_setup_span(*positional, **keywords):
            if not setup["active"] or setup["disabled"]:
                return original(*positional, **keywords)
            if axial_only and not any(row["label"] == "reference._axial_derivatives" for row in setup_stack):
                return original(*positional, **keywords)
            # Recursive _assert_projection work belongs to its outermost span.
            if not nested and any(row["label"] == label for row in setup_stack):
                setup["recursive_forwards"][label] = setup["recursive_forwards"].get(label, 0) + 1
                return original(*positional, **keywords)
            if len(setup_spans) >= MAX_SETUP_SPANS:
                setup["disabled"] = True
                observation_errors.append({"boundary": "setup_span_limit", "type": "ObservationLimit", 
                                           "message": "Bounded setup span allowance exhausted"})
                return original(*positional, **keywords)
            row = observe("setup_entry:" + label, enter_setup_span, label, nested, positional, keywords)
            if row is None:
                setup["disabled"] = True
                return original(*positional, **keywords)
            work_own = object.__getattribute__(retained["work"], "__dict__")
            saved = {"positional": positional, "keywords": dict(keywords), "work": retained["work"],
                     "external": work_own["external_check"], "observer": work_own["_source_after_charge"]}
            try:
                result = original(*positional, **keywords)
            except BaseException:
                row["outcome"] = "raised"
                raise
            else:
                row["outcome"] = "returned"
                if label == "reference.build_reference":
                    if type(result) is rr.ReachReference:
                        setup["reference"] = result
                    else:
                        observation_errors.append({"boundary": "reference_result", "type": "ObservationType",
                                                   "message": "Reference constructor returned an unexpected type"})
                if nested:
                    row["result"] = observe("setup_result:" + label, setup_result, label, result)
                return result
            finally:
                observe("setup_exit:" + label, leave_setup_span, row, nested, positional, keywords, saved)
        return capture_setup_span

    def install_setup():
        assert setup["installations"] == 0 and not setup["active"] and not setup_targets
        assert all(getattr(owner, name) is value for owner, name, value in dispatch)
        setup["native_dispatch_before_install"] = True
        specifications = [
            (gltf, "read_glb", "gltf.read_glb", False, False),
            (gltf, "_validate_geometry", "gltf._validate_geometry", False, False),
            (scene, "program_metadata", "scene.program_metadata", False, False),
            (rr, "build_reference", "reference.build_reference", False, False),
            (rc, "verify_numeric_bases", "reader.verify_numeric_bases", False, False),
            (rc, "_verify_metadata", "reader._verify_metadata", False, False),
            (rc, "verify_retained_clocks", "reader.verify_retained_clocks", False, False),
            (rc, "_geometry_bounds", "reader._geometry_bounds", False, False),
            (rc, "_phase_tables", "reader._phase_tables", False, False),
            (rc, "_boundary_allowances", "reader._boundary_allowances", False, False),
            (rc, "_assert_projection", "reader._assert_projection", False, False),
            (rc, "_tracks", "reader._tracks", False, False),
            (rr.ReachReference, "boundary_states", "reference.boundary_states", False, False),
            (rr.ReachReference, "point_phase", "reference.point_phase", False, False),
            (rr.ReachReference, "_phase", "reference._phase", True, False),
            (rr.ReachReference, "_axial_derivatives", "reference._axial_derivatives", True, False),
            (rr.ReachReference, "_l1", "reference._l1", True, True),
            (rr.ReachReference, "_axis_transport", "reference._axis_transport", True, True),
        ]
        setup["entry"] = setup_snapshot(full=True)
        setup["entry_event"] = next_setup_event()
        for owner, name, label, nested, axial_only in specifications:
            original = getattr(owner, name)
            assert type(original) is FunctionType
            wrapper = make_setup_wrapper(original, label, nested=nested, axial_only=axial_only)
            setup_targets.append((owner, name, original, wrapper, label, nested, axial_only))
            setattr(owner, name, wrapper)
        setup["installations"] += 1
        setup["active"] = True

    def restore_setup(boundary):
        checks = []
        for owner, name, original, wrapper, label, _, _ in reversed(setup_targets):
            current = getattr(owner, name)
            checks.append({"label": label, "expected_dispatch": current is wrapper or current is original,
                           "was_wrapper": current is wrapper, "was_original": current is original})
            setattr(owner, name, original)
            checks[-1]["restored"] = getattr(owner, name) is original
        setup_restorations.append({"boundary": boundary, "checks": checks})

    def close_setup():
        if setup["cutoff"] is not None:
            return
        assert setup["active"] and setup["installations"] == 1
        setup["cutoff"] = setup_snapshot(full=True)
        setup["first_key_entry_event"] = next_setup_event()
        setup["native_dispatch_at_cutoff"] = all(getattr(owner, name) is value for owner, name, value in dispatch)
        setup["open_spans_at_cutoff"] = tuple(row["id"] for row in setup_stack)
        setup["active"] = False
        restore_setup("first_key_entry")
        setup["restored_before_first_key"] = all(getattr(owner, name) is original
            for owner, name, original, _, _, _, _ in setup_targets)

    def capture_recording_stage(*positional, **keywords):
        row = {"ordinal": len(stage_events), "name": positional[0] if positional else keywords.get("name")}
        stage_events.append(row)
        def state():
            work = keywords.get("work")
            assert type(work) is ReachExecutionWork
            external = work.external_check
            assert type(external) is MethodType and external.__func__ is ConstructionBudget.tick
            return {"shared_operations": external.__self__.operations, "reach": record(work)}
        row["entry"] = observe("producer_stage_entry", state)
        try:
            result = stage_original(*positional, **keywords)
        except BaseException:
            row["outcome"] = "raised"
            raise
        else:
            row["outcome"] = "returned"
            return result
        finally:
            row["exit"] = observe("producer_stage_exit", state)

    def capture_validate_export(*positional, **keywords):
        retained["reader_calls"] += 1
        def enter():
            assert retained["reader_calls"] == 1 and len(positional) == 2 and type(positional[0]) is bytes
            assert len(positional[0]) <= 64 * 1024 * 1024
            work, external = keywords["work"], keywords["work"].external_check
            assert type(work) is ReachExecutionWork
            assert type(external) is MethodType and external.__func__ is ConstructionBudget.tick
            budget = external.__self__
            assert type(budget) is ConstructionBudget
            retained.update(data=positional[0], model=positional[1], options=keywords["options"],
                work=work, check=keywords["check"], external=external, observer=work._source_after_charge,
                budget=budget, construction_check=budget.check, work_at_reader_entry=record(work),
                shared_operations_at_reader_entry=budget.operations, budget_limits=dict(budget.limits),
                work_limits={name: getattr(work, name) for name in
                             ("max_operations", "max_elapsed_ms", "max_operand_bits", "max_cache_entries")},
                reader_keyword_names=tuple(keywords), reader_keywords=dict(keywords))
        observe("reader_entry", enter)
        observe("setup_install", install_setup)
        try:
            return validate_original(*positional, **keywords)
        except BaseException as error:
            retained["error"] = error
            raise
        finally:
            setup["active"] = False
            observe("setup_restore_reader_exit", restore_setup, "reader_exit")
            def leave():
                work = retained["work"]
                retained["reader_identity_checks"] = {
                    "reader_owner_preserved": keywords["work"] is work,
                    "reader_arguments_preserved": (positional[0] is retained["data"] and
                        positional[1] is retained["model"] and keywords["options"] is retained["options"] and
                        keywords["check"] is retained["check"] and tuple(keywords) == retained["reader_keyword_names"] and
                        all(keywords[name] is value for name, value in retained["reader_keywords"].items())),
                    "reader_external_preserved": work.external_check is retained["external"],
                    "reader_observer_restored": work._source_after_charge is retained["observer"],
                    "same_callback_error_at_reader_exit": retained.get("error") is work.callback_error,
                }
            observe("reader_exit", leave)

    def capture_key_comparisons(*positional, **keywords):
        if retained["key_calls"] == 0:
            observe("setup_first_key", close_setup)
        retained["key_calls"] += 1
        row = {"ordinal": retained["key_calls"], "outcome": "entered"}
        ledger.append(row)
        saved = {}
        def enter():
            assert len(positional) == 6 and len(ledger) <= 256
            reference, geometry, tracks, time, index, arithmetic = positional
            assert type(reference) is rr.ReachReference and type(index) is int and 0 <= index < 256
            assert type(geometry) is dict and len(geometry) <= 64 and type(arithmetic) is rc._Bounds
            source = reference.a
            saved.update(reference=reference, arithmetic=arithmetic, work=arithmetic.work,
                source=source, source_check=source.check, source_observer=source._recording_after_tick,
                external=arithmetic.work.external_check, observer=arithmetic.work._source_after_charge,
                original_positional=positional, original_keywords=dict(keywords))
            row.update(index=index, time=ratio(time), previous_time=None if keywords.get("previous_time") is None
                       else ratio(keywords["previous_time"]), geometry_count=len(geometry),
                       previous_carriers=tuple(keywords["previous"]) if keywords.get("previous") is not None else (),
                       previous_available=keywords.get("previous") is not None,
                       recording_context=frozen(keywords.get("recording_context")),
                       positional_count=len(positional), keyword_names=tuple(keywords))
            row["entry"] = source_state(reference, arithmetic)
            if len(ledger) == 1:
                capture_inputs(reference, geometry, tracks)
                retained["source_reference"] = reference
            assert record(arithmetic.work) == row["entry"]["reach"]
            assert retained["budget"].operations == row["entry"]["shared_operations"]
        observe("key_entry", enter)
        try:
            result = key_original(*positional, **keywords)
        except BaseException as error:
            row.update(outcome="raised", failure_type=type(error).__name__)
            retained["key_error"] = error
            frames = observe("key_failure_locals", selected_failure_locals, error)
            if frames is not None:
                failure_frames.extend(frames)
            raise
        else:
            row.update(outcome="returned", result_carriers=tuple(result) if type(result) is dict else None)
            return result
        finally:
            def leave():
                reference, arithmetic = saved["reference"], saved["arithmetic"]
                source, work = saved["source"], saved["work"]
                row["exit"] = source_state(reference, arithmetic)
                row["identity_checks"] = {
                    "positional_arguments_preserved": len(positional) == len(saved["original_positional"]) and
                        all(current is prior for current, prior in zip(positional, saved["original_positional"])),
                    "keyword_arguments_preserved": tuple(keywords) == tuple(saved["original_keywords"]) and
                        all(keywords[name] is value for name, value in saved["original_keywords"].items()),
                    "work_owner_preserved": arithmetic.work is work and work is retained["work"],
                    "source_owners_preserved": reference.a is source and reference.p.a is source and source.work is work,
                    "source_check_preserved": source.check is saved["source_check"],
                    "source_observer_restored": source._recording_after_tick is saved["source_observer"],
                    "external_preserved": work.external_check is saved["external"],
                    "work_observer_preserved": work._source_after_charge is saved["observer"],
                    "no_trace_hook": sys.gettrace() is None, "no_profile_hook": sys.getprofile() is None,
                }
            observe("key_exit", leave)

    report = driver_error = None
    try:
        exporter.recording_stage = capture_recording_stage
        gltf.validate_export = capture_validate_export
        rc._key_comparisons = capture_key_comparisons
        report = build(output / "diagnostic", (args.case,), 1.0)
    except BaseException as error:
        driver_error = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
    finally:
        exporter.recording_stage = stage_original
        gltf.validate_export = validate_original
        rc._key_comparisons = key_original
        setup["active"] = False
        observe("setup_restore_final", restore_setup, "final_cleanup")

    # The unchanged capped request has now ended. No observations below can
    # change its work counters, cache order, exception choice or elapsed checks.
    result = {"schema_version": "ontokin.reach-recording-work-capture/0.1", "case_id": args.case,
        "created_at": datetime.now(timezone.utc).isoformat(), "status": "capture_failed",
        "product_request_status": report.get("status") if report else "driver_failed",
        "accepted_artifact": False, "release_acceptance": False,
        "scope": "Unvalidated reader input and endpoint observations from the original failed request.",
        "reader_calls": retained["reader_calls"], "key_calls": retained["key_calls"],
        "driver": descriptor(Path(__file__).resolve()),
        "actual_driver_command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "diagnostic_api_call": {"callable": "tools.probe_reach_recording_work.build", "output": str(output / "diagnostic"),
                           "cases": [args.case], "fps": 1.0},
        "complete_stock_harness": False,
        "provenance": "C061 extends the source-bound C060 collector with reader-only setup spans; the original C060 file is unchanged.",
        "execution": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
        "identity_checks": {"validate_export_restored": gltf.validate_export is validate_original,
            "key_comparisons_restored": rc._key_comparisons is key_original,
            "recording_stage_restored": exporter.recording_stage is stage_original,
            "setup_dispatch_restored": all(getattr(owner, name) is original
                for owner, name, original, _, _, _, _ in setup_targets),
            "setup_restored_before_first_key": setup["restored_before_first_key"],
            "native_dispatch_preserved": all(getattr(owner, name) is value for owner, name, value in dispatch),
            "no_trace_hook": sys.gettrace() is None, "no_profile_hook": sys.getprofile() is None},
        "observation_errors": observation_errors,
        "opaque_identity_note": "opaque_object_id and integer state identities bind only objects within this execution; they are not source identities or cross-run equivalence claims."}
    if driver_error:
        result["driver_error"] = driver_error
    if report:
        result.update(source_commit=report.get("source_commit"), source_tree=report.get("source_tree"),
                      inputs_stable=report.get("inputs_stable"))
    if retained.get("data") is not None:
        raw, work, budget = retained["data"], retained["work"], retained["budget"]
        with (output / "unvalidated-reader-input.glb").open("xb") as stream:
            stream.write(raw)
        result.update(artifact={"path": "unvalidated-reader-input.glb", "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
            work_at_reader_entry=retained["work_at_reader_entry"],
            shared_operations_at_reader_entry=retained["shared_operations_at_reader_entry"],
            work_after_request=record(work), shared_operations_after_request=budget.operations,
            budget_limits=retained["budget_limits"], work_limits=retained["work_limits"],
            original_request={"case_id": args.case, **(report["deliveries"][0]["options"]
                              if report and report.get("deliveries") else {})},
            callbacks={"external": callable_name(work.external_check), "construction_check": callable_name(budget.check),
                "observer_at_reader_entry": callable_name(retained["observer"]),
                "observer_after_request": callable_name(work._source_after_charge)})
        result["identity_checks"].update(retained.get("reader_identity_checks", {}))
        result["identity_checks"].update(external_callback_preserved=work.external_check is retained["external"],
            native_callback_owner_preserved=work.external_check.__self__ is budget,
            construction_check_preserved=budget.check is retained["construction_check"],
            observer_restored_after_request=work._source_after_charge is retained["observer"],
            callback_error_preserved=retained.get("error") is work.callback_error,
            key_reader_exception_identical=retained.get("key_error") is retained.get("error"),
            work_limits_unchanged=all(getattr(work, name) == value for name, value in retained["work_limits"].items()),
            budget_limits_unchanged=budget.limits == retained["budget_limits"])
    graph, visited = [], {}
    queue = [retained["error"]] if retained.get("error") is not None else []
    while queue:
        error = queue.pop(0)
        if id(error) in visited:
            continue
        assert len(visited) < 16
        ordinal = len(visited)
        visited[id(error)] = ordinal
        causes = [error.__cause__, error.__context__]
        queue.extend(value for value in causes if value is not None and id(value) not in visited)
        graph.append({"error_object_id": id(error), "ordinal": ordinal, "type": type(error).__name__,
            "message": str(error), "cause_object_id": None if causes[0] is None else id(causes[0]),
            "context_object_id": None if causes[1] is None else id(causes[1]),
            "suppress_context": error.__suppress_context__,
            "frames": [{"file": frame.filename, "line": frame.lineno, "function": frame.name}
                       for frame in traceback.extract_tb(error.__traceback__)]})
    if graph:
        result["exception"] = graph[0]
    write_json(output / "key-ledger.json", {"schema_version": "ontokin.source-endpoint-ledger/0.1", "case_id": args.case,
        "scope": "Detached boundary observations; returned keys remain provisional until full source admission.",
        "source_boundaries": source_boundaries, "geometry": geometry_rows, "tracks": track_rows, "keys": ledger, "producer_stages": stage_events})
    write_json(output / "failure-locals.json", {"schema_version": "ontokin.source-endpoint-failure-locals/0.1",
        "case_id": args.case, "snapshot_boundary": "_key_comparisons exception exit before source-batch cleanup",
        "scope": "Passive copies from an existing exception traceback, without trace/profile hooks or execution of source helpers.",
        "frames": failure_frames, "exception_graph": graph})
    if (report and report.get("status") == "failed" and report.get("inputs_stable") and not driver_error
            and not observation_errors and retained["reader_calls"] == 1 and ledger
            and ledger[-1]["outcome"] == "raised" and all(row["outcome"] == "returned" for row in ledger[:-1])
            and all(result["identity_checks"].values())
            and all(row.get("identity_checks") and all(row["identity_checks"].values()) for row in ledger)):
        result["status"] = "captured_failed_request"
    setup_result_record = {
        "schema_version": "ontokin.reach-reader-setup-capture/0.1", "case_id": args.case,
        "source_commit": result.get("source_commit"), "source_tree": result.get("source_tree"),
        "driver": result["driver"], "actual_driver_command": result["actual_driver_command"],
        "status": "captured_setup" if (not observation_errors and setup["cutoff"] is not None
                    and not setup["disabled"] and setup["restored_before_first_key"]
                    and not setup_stack and setup.get("open_spans_at_cutoff") == ()
                    and setup.get("native_dispatch_before_install") is True
                    and setup.get("native_dispatch_at_cutoff") is True
                    and all(row["outcome"] == "returned" and "exit" in row and
                            all(row.get("identity_checks", {}).values()) for row in setup_spans)) else "setup_capture_failed",
        "scope": "Reader entry through first key entry only; exact charged spans, not elapsed-time profiling.",
        "exclusive_costs": "Compute offline from child spans; inclusive nested spans must not be summed.",
        "typed_operand_note": "Exact native operand copies and repeated values are observations, not a source authority or reuse proof.",
        "opaque_identity_note": result["opaque_identity_note"],
        "max_spans": MAX_SETUP_SPANS, "disabled": setup["disabled"],
        "installations": setup["installations"], "entry": setup["entry"],
        "first_key_entry": setup["cutoff"], "entry_event": setup.get("entry_event"),
        "first_key_entry_event": setup.get("first_key_entry_event"),
        "event_count": setup["event_counter"], "open_spans_at_cutoff": setup.get("open_spans_at_cutoff"),
        "recursive_forwarded_calls": setup["recursive_forwards"],
        "spans": setup_spans, "restorations": setup_restorations,
        "targets": [{"label": label, "name": name, "original": callable_name(original),
                     "source_file": original.__code__.co_filename, "source_first_line": original.__code__.co_firstlineno,
                     "nested": nested, "only_during_axial": axial_only}
                    for _, name, original, _, label, nested, axial_only in setup_targets],
        "observation_errors": observation_errors,
        "identity_checks": {"restored_before_first_key": setup["restored_before_first_key"],
            "all_targets_restored": all(getattr(owner, name) is original
                for owner, name, original, _, _, _, _ in setup_targets),
            "all_recorded_restore_checks": all(item["expected_dispatch"] and item["restored"]
                for row in setup_restorations for item in row["checks"]),
            "native_dispatch_preserved": result["identity_checks"]["native_dispatch_preserved"],
            "native_dispatch_before_install": setup.get("native_dispatch_before_install", False),
            "native_dispatch_at_cutoff": setup.get("native_dispatch_at_cutoff", False)},
        "product_request_status": result["product_request_status"],
        "accepted_artifact": False, "release_acceptance": False,
        "timing_neutrality_claimed": False, "optimization_saving_claimed": False}
    write_json(output / "reader-setup.json", setup_result_record)
    result["reader_setup"] = {"path": "reader-setup.json", "status": setup_result_record["status"],
                              "span_count": len(setup_spans)}
    write_json(output / "capture.json", result)
    print(json.dumps({"case_id": args.case, "capture_status": result["status"],
        "product_request_status": result["product_request_status"],
        "shared_operations": result.get("shared_operations_after_request"),
        "key_calls": len(ledger), "observation_errors": len(observation_errors)}), flush=True)
    return 0 if report and report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
