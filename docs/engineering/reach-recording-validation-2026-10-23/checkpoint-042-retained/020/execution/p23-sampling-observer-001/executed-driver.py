"""Neutral, cached-code attribution of original P23 sampling and source reference work.

This driver observes Python call/return events. It does not wrap source
functions, callbacks or budgets, change clocks, prime caches, or amend limits.
Inclusive costs can overlap; self costs subtract nested selected calls. Charge
attribution identifies the nearest selected function and current planning scope.
The original unobserved request is the work/diagnostic equivalence oracle.
"""
import argparse
import collections
from fractions import Fraction
import hashlib
import importlib.util
import json
import pathlib
import platform
import sys
import time
import traceback


SELECTED = {
    "gltf.py": {"export_glb", "_export_glb"},
    "scene.py": {"build_scene"},
    "reach_export.py": {
        "_build_reach_scene", "build_reach_scene", "reach_prefix_plan",
        "recording_phase_bounds", "plan_recording", "recording_stage",
        "_boundary_record", "capture", "matches", "after", "selected",
        "node_geometry_bounds", "reach_timeline", "interval_certificates",
        "_recording_lift_relation", "_endpoint_group_maxima", "_endpoint_group_maxima_exact",
        "_certificate_quantities", "_endpoint_rounding",
        "_sample_recording_nodes", "_check_object_pose", "snapshot",
    },
    "reach_runtime.py": {
        "__init__", "append", "_boundary_history_weight",
        "boundary_history_bound", "_incoming_release_bound",
        "_check_boundary_history_total", "advance", "_process_boundary",
        "_validate_staged", "_latch", "_aggregate", "_event",
        "_check_object_pose", "_kinematics", "_resolve_kinematics",
        "_terminal_static_kinematics", "_pose_slot", "_translated_source_slot",
        "_constant_pose", "_coordinate", "_pair", "_tip_base", "_world_target",
        "_physical_observation", "_current", "_reach_map",
        "_bounded_projection", "_force_components", "recording_boundary",
        "_snapshot_data", "incoming_releases_at", "recording_frames", "recording_moving_frames",
        "_dynamic_kinematics", "_advance_orientation",
    },
    "reach_projection.py": {
        "reach_record_bound", "reach_projection", "_maximum_current",
        "measure_reach_json",
    },
    "evaluator.py": {
        "__init__", "_records_per_sample", "_process_boundary", "advance",
        "_next_boundary", "_check_dynamic_extrema",
    },
    "force_runtime.py": {
        "__init__", "force_record_bound", "_projection", "_bounded_projection",
        "_force_components", "_process_boundary", "_validate_staged",
        "_aggregate", "_check_dynamic_extrema",
    },
    "reach_phase.py": {
        "phase_bounds", "materialize", "_materialize_phase_location", "node_bound", "compose",
        "compose_relative", "constant", "root", "dynamic", "instance",
        "frame", "joint_phase", "retain_angular", "joint_local",
        "current_recording_angular_witness", "_current_recording_angular_witness",
        "_recording_orientation_recipe", "_native_phase_key",
        "number", "add", "sub", "mul", "div", "absolute", "maximum", "l1",
        "rounding",
    },
    "reach_pose.py": {
        "ensure_finite", "_carry_finite_proof", "constant", "compose",
        "joint", "_project", "_unit_projection", "_projection",
        "parabolic", "affine", "recording_advance_orientation", "advance_orientation",
        "_recording_product", "multiply", "spin_rotation", "make_recording",
    },
    "reach_recording_finite.py": {
        "begin", "append", "complete", "matches", "_pose_fingerprint",
    },
    "reach_recording_fast.py": {
        "recording_dynamic_pose", "_ballistic_position", "_ballistic_law",
        "recording_advance_orientation", "recording_body_orientation", "_native",
        "_product", "_project_rotation", "_rotated_offset", "_domain", "_require_domain",
        "_immutable_scalar_domain", "_sample_planar_frames", "begin_bounded_phase",
        "recording_float_excess", "_bounded", "_certify_pose", "_certify_rotation",
    },
    "reach_recording_capture.py": {
        "_root_pose", "_dynamic_pose", "_capture", "_capture_classifier", "_dynamic_source",
        "_dynamic_inputs", "_sample_graph", "_sample_chain_graph", "sample", "finish",
        "admit", "_capacity", "read_cursor", "stage", "begin_captured_phase",
        "begin_mixed_captured_phase", "resolve", "constant", "source_constant",
    },
    "reach_reference.py": {
        "__init__", "_build", "_event", "_phase", "_release", "_source_basis",
        "_pose_map", "_root_pose", "_aggregate", "_recording_phase_poses",
        "relative_composition", "compose", "point", "add", "sub", "mul", "div",
        "sincos", "sqrt", "norm", "multiply", "spin", "rotate", "hinge", "quaternion",
    },
    "reach_conformance.py": {
        "verify_recorded_reach", "_verify_certificates", "_key_comparisons",
        "_recording_position_bound", "_recording_orientation_bound", "_assert_projection",
    },
    "json_limits.py": {"measure_json", "flush_text", "string_size"},
    "values.py": {"bounded_data"},
}

# Always retain per-call boundaries and observations, including cheap returns.
# Other selected calls remain in exact aggregate totals and are retained
# individually only when their inclusive request cost reaches 128 operations.
DETAILED = {
    "reach_prefix_plan", "recording_phase_bounds", "phase_bounds",
    "_boundary_history_weight", "boundary_history_bound", "_records_per_sample",
    "reach_record_bound", "force_record_bound", "recording_boundary",
    "_physical_observation", "_reach_map", "_snapshot_data", "bounded_data",
    "_validate_staged", "_process_boundary", "advance", "_bounded_projection",
    "_sample_recording_nodes", "node_geometry_bounds", "reach_timeline",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--baseline", required=True, type=pathlib.Path)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.output.resolve()
    baseline = args.baseline.resolve()
    if out.exists() or out.is_relative_to(root):
        parser.error("Use a new output directory outside the source checkout.")
    out.mkdir(parents=True)
    helper = pathlib.Path(__file__).resolve().parents[1] / "evidence/recovered/driver/reach_development_probe_v2.py"
    spec = importlib.util.spec_from_file_location("p23_sampling_identity_helper", helper)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    driver = pathlib.Path(__file__).read_bytes()
    (out / "executed-driver.py").write_bytes(driver)
    (out / "executed-identity-helper.py").write_bytes(helper.read_bytes())
    report = {
        "schema_version": "ontokin.reach-neutral-planning-diagnostic/0.1",
        "status": "running", "release_acceptance": False,
        "release_input_closure": False, "started_at": probe.utc(),
        "command": [sys.executable, *sys.argv],
        "environment": {"python": sys.version, "executable": sys.executable,
                        "platform": platform.platform()},
        "driver_sha256": hashlib.sha256(driver).hexdigest(),
        "baseline_directory": str(baseline),
        "interpretation": {
            "inclusive": "Selected callees are included and totals may overlap.",
            "self": "Subtract directly nested selected callees from each call.",
            "charge_owner": "Nearest selected call, without wrapping the work or callback.",
            "call_details": "All named boundaries/observations and all selected calls costing at least 128 request operations.",
            "returned_none": "A return event can represent a normal None return or an exception unwind.",
        },
    }
    probe.write(out / "report.json", report)
    before = None
    try:
        before = probe.identity(root)
        probe.write(out / "inputs-before.json", before)
        report.update(source_commit=before["git_commit"], source_tree=before["git_tree"])
        prior_inputs = json.loads((baseline / "inputs-before.json").read_text())
        prior_report = json.loads((baseline / "report.json").read_text())
        original = json.loads((baseline / "P23/request-result.json").read_text())
        prior_files = {r["path"]: r["sha256"] for r in prior_inputs["files"]}
        current_files = {r["path"]: r["sha256"] for r in before["files"]}
        report["baseline_source_commit"] = prior_inputs["git_commit"]
        report["baseline_source_tree"] = prior_inputs["git_tree"]
        report["baseline_report_sha256"] = hashlib.sha256((baseline / "report.json").read_bytes()).hexdigest()
        report["baseline_inputs_stable"] = prior_report.get("inputs_stable")
        report["input_differences_from_baseline"] = [
            {"path": path, "baseline_sha256": prior_files.get(path),
             "observed_sha256": current_files.get(path)}
            for path in sorted(prior_files.keys() | current_files.keys())
            if prior_files.get(path) != current_files.get(path)
        ]
        sys.path.insert(0, str(root))
        from ontokin.bundle import load_file_manifest
        from ontokin.construction import compile_construction
        from ontokin.gltf import export_glb
        from ontokin.scene import ExportOptions
        from tools.reach_delivery_inventory import source_files, settings, frozen_cases

        bundle = load_file_manifest(root / source_files("P23"))
        if bundle.program_revision != frozen_cases()["P23"]["program_revision"]:
            raise ValueError("The frozen original P23 source identity differs.")
        compiler = compile_construction(bundle, level="constructed")
        work = compiler.reach_work
        source_prefix = str(root / "ontokin") + "/"
        code_metadata = {}
        stack = []
        active_charges = {}
        calls, stages, samples, anomalies = [], [], [], []
        stats = collections.defaultdict(lambda: {"calls": 0, "request_operations": 0,
            "self_request_operations": 0, "reach_operations": 0, "self_reach_operations": 0})
        scoped_stats = collections.defaultdict(lambda: {"calls": 0, "request_operations": 0,
            "self_request_operations": 0, "reach_operations": 0, "self_reach_operations": 0})
        charge_stats = collections.defaultdict(lambda: {"calls": 0, "requested_amount": 0,
            "request_operations": 0, "reach_operations": 0, "kinds": collections.Counter()})
        stage = "export_preparation"
        serial = 0

        def metadata(frame):
            result = {}
            local_values = frame.f_locals
            for name in ("time", "start", "end", "horizon", "side", "path", "value",
                         "pose_only", "recording", "recording_proof", "inverse"):
                if name in local_values:
                    value = local_values[name]
                    if type(value) is Fraction:
                        result[name] = str(value)
                    elif type(value) in (bool, int, float, str, type(None)):
                        result[name] = value
            return result

        def profile(frame, event, arg):
            nonlocal stage, serial
            if event not in ("call", "return"):
                return
            code = frame.f_code
            cached = code_metadata.get(code)
            if cached is None:
                file = code.co_filename.rsplit("/", 1)[-1]
                charge = (file == "reach_numeric.py" and
                          code.co_qualname == "ReachExecutionWork.charge")
                selected = (code.co_filename.startswith(source_prefix) and
                            code.co_name in SELECTED.get(file, ()))
                cached = (file, code.co_name, file + ":" + code.co_qualname,
                          code.co_firstlineno, charge) if selected or charge else False
                code_metadata[code] = cached
            if cached is False:
                return
            file, name, key, line, charge = cached
            if charge:
                if frame.f_locals.get("self") is not work:
                    return
                if event == "call":
                    kind = frame.f_locals.get("kind", "checkpoint")
                    amount = frame.f_locals.get("amount", 1)
                    if kind.startswith("recording_stage_"):
                        stage = kind
                        stages.append({"kind": kind, "request_operations": compiler.budget.operations,
                                       "reach_operations": work.operations})
                    elif kind == "recording_sample":
                        parent = frame.f_back
                        while parent is not None and parent.f_code.co_name != "_sample_recording_nodes":
                            parent = parent.f_back
                        samples.append({"sample": len(samples), "request_operations": compiler.budget.operations,
                                        "reach_operations": work.operations,
                                        **(metadata(parent) if parent is not None else {})})
                    owner = stack[-1]["function"] if stack else "<unselected>"
                    scope = stack[-1]["scope"] if stack else "export_preparation"
                    active_charges[id(frame)] = (scope, owner, stage, kind, amount,
                                                  compiler.budget.operations, work.operations)
                else:
                    saved = active_charges.pop(id(frame), None)
                    if saved is not None:
                        scope, owner, at_stage, kind, amount, request_start, reach_start = saved
                        row = charge_stats[(scope, owner, at_stage)]
                        row["calls"] += 1
                        row["requested_amount"] += amount
                        row["request_operations"] += compiler.budget.operations - request_start
                        row["reach_operations"] += work.operations - reach_start
                        row["kinds"][kind] += amount
                return
            if event == "call":
                serial += 1
                values = metadata(frame)
                scope = stack[-1]["scope"] if stack else "export_preparation"
                if key == "reach_runtime.py:ReachSimulator.__init__":
                    scope = "planning_constructor"
                elif key == "reach_runtime.py:_BoundaryHistoryPreflight.append":
                    scope = "boundary_history_forecast:" + str(values.get("value"))
                elif file == "reach_runtime.py" and name in ("advance", "recording_boundary"):
                    scope = name + ":" + str(values.get("time")) + ":" + str(values.get("side"))
                elif file == "reach_phase.py" and name == "phase_bounds":
                    scope = "phase_bounds:" + str(values.get("start")) + ":" + str(values.get("end"))
                elif file == "reach_export.py" and name == "_sample_recording_nodes":
                    scope = "recording_sampling"
                stack.append({"frame_id": id(frame), "call_id": serial, "function": key,
                              "source_line": line, "stage_at_entry": stage, "scope": scope,
                              "parent": stack[-1]["function"] if stack else None,
                              "request_start": compiler.budget.operations,
                              "reach_start": work.operations, "child_request": 0, "child_reach": 0,
                              "parameters": values})
                return
            if not stack or stack[-1]["frame_id"] != id(frame):
                anomalies.append({"kind": "unmatched_selected_return", "function": key})
                return
            saved = stack.pop()
            request_cost = compiler.budget.operations - saved["request_start"]
            reach_cost = work.operations - saved["reach_start"]
            self_request = request_cost - saved["child_request"]
            self_reach = reach_cost - saved["child_reach"]
            for row in (stats[key], scoped_stats[(saved["scope"], key)]):
                row["calls"] += 1
                row["request_operations"] += request_cost
                row["self_request_operations"] += self_request
                row["reach_operations"] += reach_cost
                row["self_reach_operations"] += self_reach
            if stack:
                stack[-1]["child_request"] += request_cost
                stack[-1]["child_reach"] += reach_cost
            if name in DETAILED or request_cost >= 128:
                saved.pop("frame_id")
                saved.pop("child_request")
                saved.pop("child_reach")
                saved.update(request_end=compiler.budget.operations, reach_end=work.operations,
                             request_operations=request_cost, reach_operations=reach_cost,
                             self_request_operations=self_request, self_reach_operations=self_reach,
                             returned_none=arg is None)
                calls.append(saved)

        started = time.monotonic()
        row = {"case_id": "P23", "started_at": probe.utc(),
               "source_commit": before["git_commit"], "source_tree": before["git_tree"],
               "program_revision": bundle.program_revision, "max_operations": 100000,
               "constructed_operations": compiler.budget.operations,
               "constructed_reach_operations": work.operations, "options": settings("P23")}
        try:
            sys.setprofile(profile)
            result = export_glb(compiler.model,
                options=ExportOptions(**{**row["options"], "end": Fraction(row["options"]["end"])}),
                target_contract="ontokin.glb/0.6", work=work)
            row["status"] = result.report["validation"]["status"]
            row["artifact_sha256"] = hashlib.sha256(result.data).hexdigest()
        except Exception as exc:
            row.update(status="failed", failure={"type": type(exc).__name__, "message": str(exc)},
                       traceback=traceback.format_exc())
            if hasattr(exc, "diagnostic"):
                row["diagnostic"] = exc.diagnostic.to_dict(bundle.sources.get(
                    getattr(exc.diagnostic.node, "source_id", "entry"), bundle.entry.to_source()))
        finally:
            sys.setprofile(None)
        row.update(operations=compiler.budget.operations, work=work.record(),
                   elapsed_seconds=time.monotonic() - started, finished_at=probe.utc(),
                   stages=stages, samples=samples, calls=sorted(calls, key=lambda r: r["call_id"]),
                   stats=dict(stats), scoped_stats=[{"scope": scope, "function": key, **value}
                       for (scope, key), value in sorted(scoped_stats.items())],
                   charge_stats=[{"scope": scope, "function": key, "stage": at_stage, **value}
                       for (scope, key, at_stage), value in sorted(charge_stats.items())],
                   observer_anomalies=anomalies, unreturned_selected_frames=len(stack),
                   unreturned_work_charges=len(active_charges), classified_code_count=len(code_metadata))
        row["matches_unobserved_work"] = row["work"] == original["work"]
        row["matches_unobserved_diagnostic"] = row.get("diagnostic") == original.get("diagnostic")
        row["matches_unobserved_operations"] = row["operations"] == original["operations"]
        row["matches_unobserved_status"] = row["status"] == original["status"]
        row["self_request_total"] = sum(r["self_request_operations"] for r in stats.values())
        row["self_reach_total"] = sum(r["self_reach_operations"] for r in stats.values())
        row["self_request_reconciles"] = row["self_request_total"] == row["operations"] - row["constructed_operations"]
        row["self_reach_reconciles"] = row["self_reach_total"] == work.operations - row["constructed_reach_operations"]
        probe.write(out / "P23.json", row)
        report["result"] = {name: row[name] for name in (
            "case_id", "operations", "matches_unobserved_work", "matches_unobserved_diagnostic",
            "matches_unobserved_operations", "matches_unobserved_status", "self_request_reconciles",
            "self_reach_reconciles", "observer_anomalies", "unreturned_selected_frames",
            "unreturned_work_charges")}
        neutral = all(row[name] for name in (
            "matches_unobserved_work", "matches_unobserved_diagnostic", "matches_unobserved_operations",
            "matches_unobserved_status", "self_request_reconciles", "self_reach_reconciles"))
        report["status"] = "passed" if neutral and not (anomalies or stack or active_charges) else "failed"
    except Exception as exc:
        sys.setprofile(None)
        report.update(status="failed", failure={"type": type(exc).__name__, "message": str(exc)},
                      traceback=traceback.format_exc())
    if before is not None:
        try:
            after = probe.identity(root)
            probe.write(out / "inputs-after.json", after)
            report["inputs_stable"] = before == after
            if before != after:
                report["status"] = "failed"
        except Exception as exc:
            report.update(status="failed", input_failure=str(exc))
    report["finished_at"] = probe.utc()
    probe.write(out / "report.json", report)
    print(json.dumps({key: report[key] for key in ("status", "result", "inputs_stable", "failure")
                      if key in report}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
