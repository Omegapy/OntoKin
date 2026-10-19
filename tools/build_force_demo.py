#!/usr/bin/env python3
"""Build actual source-driven GLB/0.5 cases and retain independent expectations.

This component recorder calls the compiler and exporter on immutable .ok
bundles. It supplies no host geometry, force state, or precomputed trajectories
to either. Agent transport acceptance remains a separate recorded workflow.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ontokin.agent import implementation_identity
from ontokin.bundle import ProgramBundle, SourceUnit, load_file_manifest
from ontokin.construction import compile_construction
from ontokin.diagnostics import OntoKinError
from ontokin.evaluator import evaluate_prefix
from ontokin.gltf import export_glb
from ontokin.scene import ExportOptions
from tools.force_oracles import (ACCEPTANCE_BYTES, ADOPTED_CASES, CASES, DELIVERY_CASES, FIXTURES, FIXTURE_INPUT_BYTES,
    HELD_OUT_CASES, case_spec, digest, expected_pose, fraction, oracle_for,
    sample_requests, seconds)

TARGET = "ontokin.glb/0.5"
FAILURE_CASES = ("P18", "P20", "P21-full-horizon", "float32-boundary-collapse", "position-key-budget")


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                               allow_nan=False) + "\n", encoding="utf-8")


def require(condition, reason):
    if not condition: raise AssertionError(reason)


def fixed_bundle(name):
    result = load_file_manifest(FIXTURES / CASES[name]["file_manifest"])
    require(result.program_revision == CASES[name]["program_revision"], "Frozen program revision changed: " + name)
    require(result.manifest()["units"] == CASES[name]["source_units"], "Frozen complete source closure changed: " + name)
    return result


def fixture_bundle(name):
    if name in CASES: return fixed_bundle(name)
    if name == "P21-full-horizon": return fixed_bundle("P21")
    if name == "position-key-budget": return fixed_bundle("P01")
    if name == "float32-boundary-collapse":
        original = fixed_bundle("P01")
        text = original.entry.text.replace("at 1[s]", "at 0.5[s]").replace("for 1[s]", "for 1e-9[s]")
        return ProgramBundle(SourceUnit("entry", original.entry.filename, text.encode()), original.modules)
    require(name in HELD_OUT_CASES, "Unknown component fixture: " + name)
    spec = case_spec(name)
    original = fixed_bundle("P01")
    header = original.entry.text[:original.entry.text.index("scene Demo")]
    units = lambda values, unit: ", ".join(f"{value}[{unit}]" for value in values)
    events = {}
    for item in spec["forces"]:
        line = (f'force {item["target"]} @ "{item["key"]}" using vector(world, '
                f'{units(item["vector_n"], "N")}) for {float(item["duration_seconds"])}[s];')
        events.setdefault(item["start_seconds"], []).append((item["sequence_index"], line))
    for item in spec["impulses"]:
        line = (f'impulse {item["target"]} using vector(world, {units(item["vector_n_s"], "N*s")}) '
                f'at point({item["target"]}.frame, {units(item["point_self_m"], "m")});')
        events.setdefault(item["time_seconds"], []).append((item["sequence_index"], line))
    blocks = "\n".join(f'    at {float(time)}[s] sequence {{\n' +
                       "\n".join("        " + line for _, line in sorted(items)) + "\n    }"
                       for time, items in sorted(events.items(), key=lambda pair: Fraction(pair[0])))
    source = header + f'''scene Demo @ "demo" {{
    duration = {spec.get("declared_duration_seconds", spec["end_seconds"])}[s];
    gravity = vector(world, {units(spec["gravity_m_per_s2"], "m/s^2")});
    object ball @ "ball": bodies.SphereProp {{
        body_mass = {spec["mass_kg"]}[kg];
        body_radius = {spec["radius_m"]}[m];
        placement = pose(world, vec3({units(spec["position_m"], "m")}), quat(1, 0, 0, 0));
        velocity = vector(world, {units(spec["velocity_m_per_s"] , "m/s")});
    }}
{blocks}
}}
'''
    return ProgramBundle(SourceUnit("entry", original.entry.filename, source.encode()), original.modules)


def retain_bundle(directory, bundle):
    units = []
    for unit in bundle.units:
        require(Path(unit.filename).name == unit.filename, "Retained source filenames must be basenames")
        (directory / unit.filename).write_bytes(unit.raw)
        units.append({"file": unit.filename, "source_id": unit.source_id,
                      "source_revision": unit.revision, "byte_length": len(unit.raw)})
    write_json(directory / "program.bundle.json", bundle.to_payload())
    write_json(directory / "source-manifest.json", bundle.manifest())
    return units


def near(actual, wanted, label, tolerance=1e-9):
    require(len(actual) == len(wanted) and all(math.isfinite(x) for x in actual), label + " must be finite")
    require(max((abs(a - b) for a, b in zip(actual, wanted)), default=0) <= tolerance, label + " differs")


def check_frozen(name, samples):
    if name not in CASES: return
    lookup = {(sample["time_seconds"], sample["side"]): sample for sample in samples}
    for wanted in ADOPTED_CASES[name]["expected_samples"]:
        actual = lookup[(seconds(wanted["time"]), wanted["side"])]["objects"][wanted["target"]]
        label = name + " " + seconds(wanted["time"]) + " " + wanted["side"]
        for field, expected in (("position_m", "position_m"), ("velocity_m_per_s", "velocity_m_s"),
                                ("angular_velocity_rad_per_s", "omega_world_rad_s")):
            near(actual[field], wanted[expected], label + " " + field)
        rotation = actual["orientation_wxyz"]
        error = min(max(abs(a - sign * b) for a, b in zip(rotation, wanted["orientation_wxyz"])) for sign in (-1, 1))
        require(error <= 1e-9, label + " orientation differs")
        forces = actual["forces"]
        require([item["force_key"] for item in forces["active"]] == wanted["active_keys"], label + " active keys differ")
        require({item["force_key"]: item["completion_time_seconds"] for item in forces["active"]} ==
                {key: seconds(value) for key, value in wanted["active_ends"].items()}, label + " exact completion clocks differ")
        for key in ("started_count", "completed_count"):
            require(forces[key] == wanted[key], label + " cumulative counts differ")
        near(forces["net_force_world_n"], wanted["net_force_world_n"], label + " net force")
        if wanted["acceleration_world_m_s2"] is None:
            require(forces["acceleration_world_m_per_s2"] is None, label + " nullable acceleration differs")
        else: near(forces["acceleration_world_m_per_s2"], wanted["acceleration_world_m_s2"], label + " acceleration")
        expected_clock = lambda key: None if wanted[key] is None else seconds(wanted[key])
        require(forces["last_change_time_seconds"] == expected_clock("last_boundary"), label + " latest force clock differs")
        require([{ "key": item["force_key"], "kind": item["kind"]} for item in forces["last_changes"]] ==
                wanted["last_changes"], label + " latest force changes differ")
        require(actual["pose_authority"].get("since_seconds") == expected_clock("dynamic_since"), label + " dynamic origin differs")
        require(actual["pose_authority"].get("trajectory_anchor_seconds") == expected_clock("anchor_time"), label + " trajectory anchor differs")


def record_reference(model, oracle):
    samples = []
    fields = ("element_id", "position_m", "orientation_wxyz", "velocity_m_per_s", "angular_velocity_rad_per_s",
              "forces", "impulses", "pose_authority", "own_mass_kg")
    for request in sample_requests(oracle["fixture"]):
        prefix = evaluate_prefix(model, request["time_seconds"], side=request["side"])
        if prefix["failure"] is not None: raise prefix["failure"]
        raw = prefix["last_valid_state"]
        sample = {"time_seconds": raw["time_seconds"], "side": raw["side"],
                  "objects": {path: {key: obj[key] for key in fields} for path, obj in raw["objects"].items()}}
        for object_ in oracle["shapes"] + oracle["empty_objects"]:
            position, rotation = expected_pose(object_, request["time_seconds"])
            actual = sample["objects"][object_["path"]]
            near(actual["position_m"], position, oracle["fixture"] + " independent source position")
            error = min(max(abs(a - sign * b) for a, b in zip(actual["orientation_wxyz"], rotation)) for sign in (-1, 1))
            require(error <= 1e-9, oracle["fixture"] + " independent source rotation differs")
        samples.append(sample)
    check_frozen(oracle["fixture"], samples)
    return samples


def git_identity():
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_OPTIONAL_LOCKS="0")
    def run(*args):
        return subprocess.run(["git", "-c", "core.fsmonitor=false", *args], cwd=ROOT, env=environment,
                              text=True, capture_output=True, check=True).stdout.strip()
    return {"head": run("rev-parse", "HEAD"), "tree": run("rev-parse", "HEAD^{tree}"),
            "worktree_changes": run("status", "--porcelain").splitlines()}


def build(output, selected=None):
    output = Path(output)
    require(not output.exists() or not any(output.iterdir()), "Use a new empty output directory")
    selected = list(selected or DELIVERY_CASES)
    require(len(selected) == len(set(selected)) and all(name in DELIVERY_CASES for name in selected), "Invalid fixture selection")
    output.mkdir(parents=True, exist_ok=True)
    identity = git_identity()
    fixtures, failures = [], []
    workflow = {"schema_version": "ontokin.force-destination-workflow/0.1", "status": "running",
                "started_at_utc": datetime.now(timezone.utc).isoformat(), "target_contract": TARGET,
                "implementation": implementation_identity(), "git_identity": identity,
                "builder_sha256": digest(Path(__file__).read_bytes()),
                "oracle_sha256": digest((ROOT / "tools/force_oracles.py").read_bytes()),
                "acceptance_manifest_sha256": digest(ACCEPTANCE_BYTES),
                "fixture_inputs": {key: digest(raw) for key, raw in FIXTURE_INPUT_BYTES.items()},
                "selected_fixtures": selected, "complete_component_corpus": selected == list(DELIVERY_CASES),
                "fixtures": fixtures, "delivery_failures": failures,
                "limits": ["This source/export component is not an Agent transport workflow or the complete F01-F12 release.",
                           "Independent destination validation and reviewed browser captures are separately executed roles.",
                           "Recorded GLB transforms do not execute live force, impulse, contact, or torque physics."]}
    try:
        for name in selected:
            directory = output / name; directory.mkdir()
            bundle, oracle = fixture_bundle(name), oracle_for(name)
            units = retain_bundle(directory, bundle)
            oracle["program_revision"] = bundle.program_revision
            write_json(directory / "oracle.json", oracle)
            model = compile_construction(bundle, level="constructed").model
            samples = record_reference(model, oracle)
            options = ExportOptions(end=oracle["end_seconds"], fps=oracle["specification"]["fps"], helpers=False)
            result = export_glb(model, options=options, target_contract=TARGET)
            require(result.report["validation"]["status"] == "passed", name + " binary self-validation failed")
            require(result.report["schema_version"] == "ontokin.glb-report/0.5", name + " changed delivery version")
            (directory / "scene.glb").write_bytes(result.data)
            write_json(directory / "scene.export.json", result.report)
            write_json(directory / "scene.reference.json", {
                "schema_version": "ontokin.force-native-reference/0.1", "program_revision": bundle.program_revision,
                "source_manifest": bundle.manifest(), "artifact_sha256": digest(result.data),
                "implementation": workflow["implementation"], "tolerances": result.report["tolerances"], "samples": samples})
            fixtures.append({"fixture": name, "directory": name, "program_revision": bundle.program_revision,
                             "artifact_sha256": digest(result.data), "glb_bytes": len(result.data),
                             "end_seconds": oracle["end_seconds"], "source_units": units, "fixed_samples": len(samples)})
        if workflow["complete_component_corpus"]:
            for name in FAILURE_CASES:
                directory = output / name; directory.mkdir()
                bundle = fixture_bundle(name); units = retain_bundle(directory, bundle)
                model = compile_construction(bundle, level="constructed").model
                options = ExportOptions(helpers=False, position_tolerance_m=1e-12 if name == "position-key-budget" else .001)
                try:
                    export_glb(model, options=options, target_contract=TARGET)
                except OntoKinError as error:
                    require(error.code in ("OKL-E-RESOURCE", "OKL-E-NUMERIC"), name + " failed for an unexpected reason")
                    record = {"fixture": name, "status": "expected_delivery_failure", "program_revision": bundle.program_revision,
                              "source_units": units, "artifact_written": False, "code": error.code,
                              "category": error.diagnostic.category, "message": str(error), "details": error.diagnostic.details}
                    write_json(directory / "delivery-failure.json", record); failures.append(record)
                else: raise AssertionError(name + " unexpectedly produced a deliverable artifact")
        workflow["git_identity_after"] = git_identity()
        require(workflow["git_identity_after"] == identity, "Source Git identity or worktree changed during recording")
        workflow["status"] = "built"
    except BaseException as error:
        workflow.update(status="failed", failure={"name": type(error).__name__, "message": str(error)})
        raise
    finally:
        workflow["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(output / "workflow.json", workflow)
    return workflow


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--fixture", choices=DELIVERY_CASES, action="append")
    args = parser.parse_args(); result = build(args.output_dir, args.fixture)
    print(json.dumps({"status": result["status"], "fixtures": len(result["fixtures"]),
                      "expected_delivery_failures": len(result["delivery_failures"]), "output_dir": str(args.output_dir)}, indent=2))


if __name__ == "__main__": main()
