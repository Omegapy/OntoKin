#!/usr/bin/env python3
"""Prepare independent expectations for actual supplied GLB/0.6 bytes.

This is an offline verification role. It does not export an artifact, evaluate
production poses, certify Agent retrieval, or establish the runtime request's
100,000-operation gate. Geometry constructor reuse is explicit in the output.
The actual byte planner and the independent ReachReference supply separate
observation clocks and source expectations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontokin.bundle import load_file_manifest
from ontokin.construction import compile_construction
from ontokin.geometry import box_mesh, sphere_mesh
from ontokin.reach_reference import Interval, build_reference
from ontokin.scene import MAX_MESH_VERTICES, SurfaceMesh, build_surface_mesh

MAX_BYTES = 64 * 1024 * 1024
MAX_SAMPLES = 100000
MAX_OBSERVATIONS = 1000000
MAX_WORLD_VERTICES = 16000000
MAX_OFFLINE_CHECKS = 100000000
MAX_OFFLINE_SECONDS = 900
ORACLE_INPUTS = (
    "tools/build_reach_native_reference.py", "ontokin/reach_reference.py",
    "ontokin/bundle.py", "ontokin/construction.py", "ontokin/linker.py",
    "ontokin/geometry.py", "ontokin/scene.py", "ontokin/surface.py",
    "docs/language-design/planar-reach-v0.1/acceptance.json",
    "docs/language-design/planar-reach-v0.1/draft2-supplements/acceptance.json",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_bounded(path, maximum=MAX_BYTES):
    """Read a regular file without allocating from an unchecked length."""
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "Input must be a regular nonsymlink file")
    before = path.stat()
    require(0 <= before.st_size <= maximum, "Input exceeds its byte bound")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.stat()
    require(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
            "Input changed while being read")
    return raw


def decode_json(raw):
    def object_pairs(pairs):
        result = {}
        for name, value in pairs:
            require(name not in result, "Input JSON repeats an object key")
            result[name] = value
        return result

    def reject_constant(value):
        raise ValueError("Input JSON contains a nonfinite number")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs,
                      parse_constant=reject_constant)


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def write_new(path, raw):
    require(len(raw) <= MAX_BYTES, "Generated member exceeds its byte bound")
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": path.name, "sha256": sha(raw), "bytes": len(raw)}


class OfflineWork:
    """Finite aggregate verification work, distinct from production requests."""
    def __init__(self):
        self.operations = 0
        self.started = time.monotonic()

    def tick(self):
        self.operations += 1
        require(self.operations <= MAX_OFFLINE_CHECKS,
                "Independent offline verification exceeded its arithmetic-check cap")
        require(time.monotonic() - self.started <= MAX_OFFLINE_SECONDS,
                "Independent offline verification exceeded its elapsed-time cap")

    def record(self):
        return {"scope": "offline_native_reference_only", "arithmetic_checks": self.operations,
                "maximum_arithmetic_checks": MAX_OFFLINE_CHECKS,
                "maximum_elapsed_seconds": MAX_OFFLINE_SECONDS,
                "elapsed_seconds": time.monotonic() - self.started,
                "production_request_budget_unchanged": True}


def rational_text(value):
    value = Fraction(value)
    require(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= 32768,
            "Reference rational exceeds its operand bound")
    return f"{value.numerator}/{value.denominator}"


def intervals(values):
    require(isinstance(values, (list, tuple)) and len(values) in (3, 4),
            "A reference vector must have three or four components")
    require(all(isinstance(value, Interval) for value in values),
            "Native pose expectations must be independent Interval enclosures")
    return [[rational_text(value.lo), rational_text(value.hi)] for value in values]


def observation_time(sample):
    """Keep authored decimal boundary clocks distinct from stored binary clocks."""
    require(sample.get("side") in ("before", "after"), "Sample side is invalid")
    value = sample.get("time_seconds")
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "A finite nonnegative destination observation time is required")
    if "source_time_seconds" in sample:
        require(isinstance(sample["source_time_seconds"], str), "Source clock must be an exact string")
        return Fraction(sample["source_time_seconds"])
    return Fraction(value)


def extra_samples(case_id, revision, reference):
    """Retain frozen observations and explicitly sample each phase's neighbors.

    Arbitrary caller case IDs are supported, but a frozen P/N/L identity is
    used only when its exact source revision agrees. Prefix builds retain all
    fixed observations inside that prefix and record the excluded count.
    """
    rows, frozen = [], None
    for relative in ORACLE_INPUTS[-2:]:
        corpus = decode_json(read_bounded(ROOT / relative))
        for case in corpus["source_cases"]:
            if case["id"] == case_id:
                require(case["program_revision"] == revision,
                        "Frozen case ID and supplied source revision differ")
                frozen = (relative, case)
    if frozen:
        relative, case = frozen
        fixed = case.get("expected", case).get("samples", [])
        for index, sample in enumerate(fixed):
            time_value = Fraction(int(sample["time"]["numerator"]), int(sample["time"]["denominator"]))
            if time_value > reference.end:
                continue
            rows.append({"sample_id": f"fixture:{case_id}:fixed:{index}", "kind": "fixture",
                         "time_seconds": float(time_value), "source_time_seconds": rational_text(time_value),
                         "side": sample["side"]})
        provenance = {"case_id": case_id, "path": relative, "sha256": sha(read_bounded(ROOT / relative)),
                      "fixed_samples_in_prefix": len(rows), "fixed_samples_outside_prefix": len(fixed) - len(rows)}
    else:
        provenance = None
    fixed_count = len(rows)
    for index, (left, right) in enumerate(zip(reference.boundaries, reference.boundaries[1:])):
        offset = min(Fraction(1, 1000000), (right - left) / 16)
        for name, time_value in (("after_left", left + offset), ("before_right", right - offset)):
            rows.append({"sample_id": f"fixture:phase:{index}:{name}", "kind": "fixture",
                         "time_seconds": float(time_value), "source_time_seconds": rational_text(time_value),
                         "side": "after"})
    return rows, provenance, len(rows) - fixed_count


def expected_nodes(model, work):
    """Reuse only declared local geometry constructors, never carrier motion."""
    nodes, remaining, repeated_vertices = [], MAX_MESH_VERTICES, 0
    for path, obj in model.objects.items():
        work.tick()
        kind = obj.geometry["kind"]
        if kind == "empty":
            mesh = None
        elif kind in ("loft", "placed"):
            mesh = build_surface_mesh(obj.geometry, max_vertices=remaining, check=work.tick)
        elif kind == "box":
            mesh = box_mesh(obj.geometry["size"])
        elif kind == "sphere":
            mesh = sphere_mesh(obj.geometry["radius"])
        else:
            raise ValueError("Unsupported source native geometry: " + kind)
        geometry = None
        if mesh is not None:
            remaining -= len(mesh.positions)
            require(remaining >= 0, "Aggregate occurrence geometry exceeds its inherited vertex cap")
            if isinstance(mesh, SurfaceMesh):
                primitives = [{"indices": list(region.indices), "material": {
                    "region_key": region.key, "base_color": list(region.material.rgba),
                    "metallic": region.material.metallic, "roughness": region.material.roughness}}
                    for region in mesh.regions]
            else:
                primitives = [{"indices": list(mesh.indices), "material": {
                    "region_key": None, "base_color": list(obj.appearance),
                    "metallic": 0.0, "roughness": 0.7}}]
            repeated_vertices += len(mesh.positions) * len(primitives)
            geometry = {"positions": [list(point) for point in mesh.positions],
                        "normals": [list(normal) for normal in mesh.normals], "primitives": primitives}
        sites = [{"path": site.path, "position_m": list(site.pose.position)}
                 for site in model.sites.values() if site.owner == path]
        nodes.append({"path": path, "element_id": list(obj.element_id),
                      "geometry": geometry, "sites": sites})
    return nodes, repeated_vertices


def source_inputs():
    """Identify all parser/type/model and reference modules used by this role.

    Include every package module, conservatively, because source construction
    imports its helpers lazily. Only the disclosed geometry constructors and
    independent reference are called to generate native expectations.
    """
    names = sorted(set(ORACLE_INPUTS) | {str(path.relative_to(ROOT)) for path in (ROOT / "ontokin").glob("*.py")})
    return {name: sha(read_bounded(ROOT / name)) for name in names}


def git_identity():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    return {"source_commit": git("rev-parse", "HEAD"), "source_tree": git("rev-parse", "HEAD^{tree}"),
            "git_status": git("status", "--porcelain=v1", "--untracked-files=all")}


def build_case(*, source_manifest, artifact, plan_file, output, case_id, end,
               source_kind="source_component", position_tolerance=.001,
               rotation_tolerance=.001, time_tolerance=.000001):
    """Copy actual bytes and construct one independent native verifier case."""
    require(source_kind in ("source_component", "agent_retrieved_artifact"), "Unknown artifact provenance label")
    require(isinstance(case_id, str) and case_id and len(case_id) <= 256, "A bounded case ID is required")
    output = Path(output).resolve()
    require(not output.exists() and not output.is_relative_to(ROOT), "Use a fresh output directory outside the checkout")
    output.mkdir(parents=True)
    work, started = OfflineWork(), datetime.now(timezone.utc).isoformat()
    identity = git_identity()
    report = {"schema_version": "ontokin.reach-native-reference-build/0.1", "status": "running",
              "started_at": started, "case_id": case_id, "source_kind": source_kind, **identity,
              "execution": {"python": sys.version, "platform": platform.platform()},
              "release_acceptance": False, "runtime_budget_gate": "not_tested_by_this_role",
              "agent_transport_audited": False}
    try:
        require(not identity["git_status"], "Execute native reference evidence from a clean committed checkout")
        before = source_inputs()
        raw, plan_raw = read_bounded(artifact), read_bounded(plan_file)
        plan = decode_json(plan_raw)
        require(plan.get("schema_version") == "ontokin.reach-native-plan/0.1", "Unexpected actual-byte plan schema")
        require(plan.get("artifact_sha256") == sha(raw) and plan.get("artifact_bytes") == len(raw),
                "Plan does not identify the supplied artifact bytes")
        samples = plan.get("required_samples")
        require(isinstance(samples, list) and 0 < len(samples) <= MAX_SAMPLES, "Invalid bounded observation schedule")
        require(len({row["sample_id"] for row in samples}) == len(samples), "Duplicate observation identity")
        for row in samples:
            observation_time(row)
        bundle = load_file_manifest(source_manifest, check=work.tick)
        require(plan.get("program_revision") == bundle.program_revision, "Actual artifact and source bundle identities differ")
        compiler = compile_construction(bundle, level="constructed", check=work.tick)
        report["source_compilation_work"] = compiler.reach_work.record()
        horizon = Fraction(end)
        require(horizon > 0 and all(observation_time(row) <= horizon for row in samples),
                "Native observations exceed the requested independent source horizon")
        reference = build_reference(compiler.model, end=horizon, check=work.tick)
        additions, frozen, phase_neighbors = extra_samples(case_id, bundle.program_revision, reference)
        samples = samples + additions
        require(len(samples) <= MAX_SAMPLES and
                len(samples) * (len(compiler.model.objects) + len(compiler.model.sites)) <= MAX_OBSERVATIONS,
                "Dense source observation inventory exceeds the native verifier cap")
        nodes, repeated_vertices = expected_nodes(reference.model, work)
        require(len(samples) * repeated_vertices <= MAX_WORLD_VERTICES,
                "Dense repeated world vertices exceed the native verifier cap")
        tolerances = {"position_m": position_tolerance, "rotation_rad": rotation_tolerance,
                      "time_s": time_tolerance, "local_vertex_m": min(.00001, position_tolerance)}
        for name, cap in (("position_m", .001), ("rotation_rad", .001), ("time_s", .000001)):
            require(type(tolerances[name]) in (int, float) and 0 < tolerances[name] <= cap,
                    "Native tolerance is invalid or exceeds the adopted default")
        result = {"schema_version": "ontokin.reach-native-reference/0.1",
                  "program_revision": bundle.program_revision, "artifact_sha256": sha(raw),
                  "tolerances": tolerances,
                  "oracle": {"method": "independent_reach_reference",
                             "geometry_method": "Inherited box_mesh/sphere_mesh/build_surface_mesh produce canonical carrier-local arrays; rigid pose and sites use independent ReachReference enclosures.",
                             "inputs": before},
                  "frozen_fixture": frozen, "phase_neighbor_samples": phase_neighbors,
                  "source_boundary_times_seconds": [str(value) for value in reference.boundaries],
                  "expected_nodes": nodes, "samples": []}
        for row in samples:
            work.tick()
            sample_time, side = observation_time(row), row["side"]
            poses = {}
            for path in reference.model.objects:
                value = reference.pose_enclosure(path, sample_time, side, ideal=False)
                poses[path] = {"position_m": intervals(value.position),
                               "orientation_wxyz": intervals(value.orientation)}
            sites = {path: intervals(reference.pose_enclosure(path, sample_time, side, ideal=False).position)
                     for path in reference.model.sites}
            result["samples"].append({**row, "poses": poses, "sites": sites})
        require(source_inputs() == before and git_identity() == identity, "Source inputs or Git identity changed during reference generation")
        require(read_bounded(artifact) == raw and read_bounded(plan_file) == plan_raw,
                "Supplied artifact or plan changed during reference generation")
        artifact_member = write_new(output / "scene.glb", raw)
        plan_member = write_new(output / "native-plan.json", plan_raw)
        reference_member = write_new(output / "native-reference.json", encode(result))
        sources = []
        for index, unit in enumerate(bundle.units):
            descriptor = write_new(output / f"source-{index:02d}.ok", unit.raw)
            sources.append({"source_id": unit.source_id, **descriptor})
        item = {"case_id": case_id, "program_revision": bundle.program_revision,
                "artifact": artifact_member, "reference": reference_member, "sources": sources}
        manifest = {"schema_version": "ontokin.reach-native-input/0.1", "source_kind": source_kind,
                    "source_commit": identity["source_commit"], "source_tree": identity["source_tree"], "cases": [item]}
        manifest_member = write_new(output / "native-input.json", encode(manifest))
        report.update(status="passed", inputs=before, program_revision=bundle.program_revision,
                      observations=len(samples), carriers=len(nodes), sites=len(reference.model.sites),
                      frozen_fixture=frozen, phase_neighbor_samples=phase_neighbors,
                      repeated_world_vertices=len(samples) * repeated_vertices,
                      members=[artifact_member, plan_member, reference_member, manifest_member, *sources])
    except Exception as error:
        report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)})
    report.update(finished_at=datetime.now(timezone.utc).isoformat(), offline_work=work.record())
    write_new(output / "reference-build.json", encode(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifest", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--source-kind", choices=("source_component", "agent_retrieved_artifact"), default="source_component")
    parser.add_argument("--position-tolerance", type=float, default=.001)
    parser.add_argument("--rotation-tolerance", type=float, default=.001)
    parser.add_argument("--time-tolerance", type=float, default=.000001)
    args = parser.parse_args(argv)
    report = build_case(source_manifest=args.source_manifest, artifact=args.artifact, plan_file=args.plan,
                        output=args.output_dir, case_id=args.case_id, end=args.end,
                        source_kind=args.source_kind, position_tolerance=args.position_tolerance,
                        rotation_tolerance=args.rotation_tolerance, time_tolerance=args.time_tolerance)
    print(json.dumps({"status": report["status"], "case_id": args.case_id,
                      "output": str(args.output_dir), "failure": report.get("failure")}, allow_nan=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
