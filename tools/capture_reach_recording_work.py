#!/usr/bin/env python3
"""Capture original P11/L03 endpoint boundaries without replacing arithmetic.

Installed wrappers are gltf.validate_export, _key_comparisons and the existing
recording_stage boundary. Each invokes the saved original exactly once.
Observations use detached native fields, never charged cache/source helpers.
The scoped diagnostic runner retains the actual failed request and exit status.
The original C033 two-boundary collector is extended with producer stage markers.
Tracked omissions are explicit; this does not execute the complete stock harness.
All JSON and binary output is written after the product request has ended.
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
    from ontokin import gltf, reach_conformance as rc, reach_reference as rr
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
        try:
            return validate_original(*positional, **keywords)
        except BaseException as error:
            retained["error"] = error
            raise
        finally:
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
        "provenance": "Derived from unchanged historical C033 collector; separate materialized-input runner and producer-stage boundary wrapper.",
        "execution": {"python": sys.version, "executable": sys.executable, "platform": platform.platform()},
        "identity_checks": {"validate_export_restored": gltf.validate_export is validate_original,
            "key_comparisons_restored": rc._key_comparisons is key_original,
            "recording_stage_restored": exporter.recording_stage is stage_original,
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
    write_json(output / "capture.json", result)
    print(json.dumps({"case_id": args.case, "capture_status": result["status"],
        "product_request_status": result["product_request_status"],
        "shared_operations": result.get("shared_operations_after_request"),
        "key_calls": len(ledger), "observation_errors": len(observation_errors)}), flush=True)
    return 0 if report and report.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
