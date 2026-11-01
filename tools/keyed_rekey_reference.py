"""Independent C086 frozen-input and supplied-byte readers.

This module never imports an OntoKin parser, compiler, evaluator or exporter.
Expected answers are read or expanded from the exact preimplementation inputs;
a produced artifact is never used to author an expected source answer.
"""
from __future__ import annotations

import base64
import copy
from itertools import product
import json
from pathlib import Path
import re
import struct

from tools.texture_reference import (
    GLB, ReferenceError, SAMPLER, bundle_identity, canonical, decode_png, digest,
    exact_uv, f32, file_payload, loads, ordinary_path, repack_glb, require, sha,
)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_COMMIT = "02d767cdd1526470d6c119fdf0d6bacb772c8a97"
FREEZE_SHA256 = "ef60ddfa380f6d0be7ec02595dc1e5f4483b003974d852514532849d568ac998"
PROFILE = "keyed-rekey-0.1"
PROTOCOL = "ontokin.agent/0.19"
TARGET = "ontokin.glb/0.19"
STORE_SCHEMA = "ontokin.keyed-rekey-program-agent-store/0.1"
DELIVERED_CASES = frozenset({"panel-task", "panel-task-repaired", "panel-task-restored", "panel-task-higher-budget"})
AGENT_CASES = ("panel-task", "panel-task-repaired", "panel-task-restored", "panel-task-duplicate", "panel-task-invalid-width", "panel-task-higher-budget", "panel-task-ungranted-budget")
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
HIGH_POLICY = {"max_operations": 400000, "max_elapsed_ms": 80000}


def case_payload(fixtures, case, *, control=False):
    """Resolve an exact frozen core or Agent file manifest, accepting name or row."""
    if isinstance(case, str):
        require(case in fixtures["cases"], "Unknown frozen source case: " + case)
        case = fixtures["cases"][case]
    require(isinstance(case, dict) and case.get("name") in fixtures["cases"],
            "Case payload requires a named frozen input")
    named = fixtures["cases"][case["name"]]
    require(case["file_manifest"] == named["file_manifest"], "Case manifest differs from frozen row")
    root = fixtures["agent_root"] if case["name"] in fixtures["agent_cases"] else fixtures["root"]
    if control:
        require("explicit_c085_control" in named, "Frozen source has no explicit .18 control")
        manifest = named["explicit_c085_control"]["file_manifest"]
    else:
        manifest = named["file_manifest"]
    return file_payload(root, manifest)


def load_fixtures(root=ROOT / "examples/keyed-rekey"):
    """Verify every published frozen byte/mode before exposing independent inputs."""
    root = Path(root).resolve()
    repository = root.parent.parent
    design = "docs/language-design/keyed-rekey-v0.1/"
    raw = ordinary_path(repository, design + "INPUT-FREEZE.json").read_bytes()
    require(sha(raw) == FREEZE_SHA256, "Published C086 input freeze changed")
    freeze = loads(raw)
    names, size = set(), 0
    for entry in freeze["files"]:
        require(entry["path"] not in names, "Duplicate frozen path")
        path = ordinary_path(repository, entry["path"])
        data = path.read_bytes()
        require(len(data) == entry["size"] and sha(data) == entry["sha256"],
                "Frozen bytes changed: " + entry["path"])
        require(entry["mode"] == ("100755" if path.stat().st_mode & 0o111 else "100644"),
                "Frozen mode changed: " + entry["path"])
        names.add(entry["path"]); size += len(data)
    require(len(names) == freeze["file_count"] == 652 and size == freeze["total_bytes"],
            "Published freeze inventory is incomplete")
    expected_raw = ordinary_path(root, "expected.json").read_bytes()
    expected = loads(expected_raw)
    core = {case["name"]: case for case in expected["cases"]}
    require(len(core) == len(expected["cases"]) == expected["case_count"] == 177,
            "Frozen core source inventory differs")
    require(sum(case["expected_outcome"] == "valid" for case in core.values()) == 118,
            "Frozen literal control count differs")
    agent_root = ordinary_path(root, "agent/workflows.json").parent
    result = {"root": root, "repository": repository, "agent_root": agent_root,
              "freeze": freeze, "expected": expected, "core_cases": core,
              "agent_cases": {}, "cases": dict(core),
              "original_expected_sha256": sha(expected_raw),
              "effective_expected_sha256": sha(expected_raw), "amendments": []}
    for name, filename in (("workflows", "workflows.json"), ("delivery", "delivery-comparison.json"),
                           ("budget", "budget-expectations.json"), ("geometry", "geometry-expectations.json"),
                           ("adversaries", "supplied-byte-adversaries.json")):
        result[name] = loads(ordinary_path(agent_root, filename).read_bytes())
    result["acceptance"] = loads(ordinary_path(repository, design + "acceptance.json").read_bytes())
    require({row["id"] for row in result["workflows"]["workflows"]} == {f"A{i:02}" for i in range(1, 11)} and
            len(result["workflows"]["workflows"]) == 10, "Frozen Agent workflow inventory differs")
    require(result["adversaries"]["expected_isolated_refusals"] == 68,
            "Frozen supplied-byte inventory differs")
    for case in core.values():
        require(bundle_identity(file_payload(root, case["file_manifest"])) ==
                (case["program_revision"], case["canonical_manifest"]),
                "Frozen core bundle identity differs: " + case["name"])
        if "explicit_c085_control" in case:
            control = case["explicit_c085_control"]
            require(bundle_identity(file_payload(root, control["file_manifest"])) ==
                    (control["program_revision"], control["canonical_manifest"]),
                    "Frozen .18 literal bundle identity differs: " + case["name"])
    for name in AGENT_CASES:
        manifest = name + ".files.json"
        payload = file_payload(agent_root, manifest)
        revision, canonical_manifest = bundle_identity(payload)
        valid = name in DELIVERED_CASES
        case = {"id": "agent:" + name, "name": name, "file_manifest": manifest,
                "program_revision": revision, "canonical_manifest": canonical_manifest,
                "expected_outcome": "valid" if valid else "invalid",
                "expected_protocol_outcome": "valid" if valid else
                    "resource_limit" if name == "panel-task-ungranted-budget" else "invalid",
                "expected_stage": "delivered" if valid else "refused",
                "expected_code": "OKL-E-ID" if name == "panel-task-duplicate" else
                    "OKL-E-RESOURCE" if name == "panel-task-ungranted-budget" else None,
                "host_policy": dict(HIGH_POLICY if name == "panel-task-higher-budget" else DEFAULT_POLICY),
                "tags": ["independently_frozen_agent_source"],
                "source": loads(ordinary_path(agent_root, manifest).read_bytes())["entry"]["path"]}
        if valid:
            control_manifest = "control-" + manifest
            control_payload = file_payload(agent_root, control_manifest)
            control_revision, control_canonical = bundle_identity(control_payload)
            case["explicit_c085_control"] = {"file_manifest": control_manifest,
                "program_revision": control_revision, "canonical_manifest": control_canonical}
            case["expected"] = panel_expectations(name, result["geometry"])
        result["agent_cases"][name] = case
        result["cases"][name] = case
    return result


def input_lineage(fixtures):
    return {"frozen_input_commit": FREEZE_COMMIT, "frozen_manifest_sha256": FREEZE_SHA256,
            "original_expected_sha256": fixtures["original_expected_sha256"],
            "effective_expected_sha256": fixtures["effective_expected_sha256"], "amendments": []}


def delivered_by_revision(fixtures):
    result = {}
    for name in sorted(DELIVERED_CASES):
        case = fixtures["agent_cases"][name]
        previous = result.get(case["program_revision"])
        if previous:
            require(case_payload(fixtures, previous) == case_payload(fixtures, case) and
                    case_payload(fixtures, previous, control=True) == case_payload(fixtures, case, control=True) and
                    previous["expected"] == case["expected"], "Delivered revision aliases disagree")
        else:
            result[case["program_revision"]] = case
    return result


def panel_expectations(name, geometry):
    """Expand frozen source dimensions/poses into exact prism answers, without GLB."""
    require(name in DELIVERED_CASES, "No geometry answer for a refused source")
    times = geometry["times_seconds"]
    require(times == [0, .25, .5, .75, 1], "Frozen time grid changed")
    mapping = {"u_per_m": [.5, 0, 0], "v_per_m": [0, -.5, 0],
               "origin_m": [0, 0, 0], "offset": [0, 1]}
    panels, marker = [], None
    formulas = {
        ("-8", "0.5*t", "0"): ([-8, 0, 0], [0, .5, 0]),
        ("-4", "0.5*t", "0"): ([-4, 0, 0], [0, .5, 0]),
        ("2", "0", "0"): ([2, 0, 0], [0, 0, 0]),
        ("6", "0", "0"): ([6, 0, 0], [0, 0, 0]),
        ("0.25*t", "-3", "0"): ([0, -3, 0], [.25, 0, 0]),
    }
    for row in geometry["five_meshes"]:
        path = row.get("repaired_path", row["path"]) if name == "panel-task-repaired" else row["path"]
        width, height, depth = row["width_m"], row["height_m"], row["depth_m"]
        origin, velocity = formulas[tuple(row["translation_formula_m"])]
        is_panel = "panels[" in path
        owner = path.split(".", 1)[0] if is_panel else None
        key = json.loads(path.split("[", 1)[1][:-1]) if is_panel else None
        colors = {region: geometry["panel_side_rgba"] if region == "side" else
                  geometry["panel_top_bottom_rgba"] for region in ("bottom", "side", "top")} if is_panel else {
                  region: geometry["marker_rgba"] for region in ("bottom", "side", "top")}
        answer = {"path": path, "element_id": ["panel-task", "demo", owner, "panels", key] if is_panel else
                  ["panel-task", "demo", "marker"], "width_m": width,
                  "local_bounds_m": [[0, 0, 0], [width, height, depth]],
                  "raw_corner_set_m": [list(point) for point in product((0, width), (0, height), (0, depth))],
                  "triangle_count": 12, "volume_m3": width * height * depth,
                  "surface_area_m2": 2 * (width * height + width * depth + height * depth),
                  "region_triangle_counts": {"bottom": 2, "side": 8, "top": 2},
                  "materials": {region: {"color": list(color), "metallic": 0, "roughness": .7}
                                for region, color in colors.items()},
                  "poses": [{"time_s": t, "position_m": [x + t * v for x, v in zip(origin, velocity)],
                             "rotation_xyzw": [0, 0, 0, 1]} for t in times]}
        if is_panel:
            answer.update(owner=owner, input_key=key)
            panels.append(answer)
        else:
            marker = answer
    require(len(panels) == 4 and marker is not None, "Frozen five-prism inventory differs")
    return {"panels": panels, "marker": marker, "mapping": mapping, "object_count": 7,
            "times_seconds": times, "widths_m": {owner: {p["input_key"]: p["width_m"] for p in panels
                if p["owner"] == owner} for owner in ("first", "sibling")}}


# These unchanged predecessor helpers independently decode native byte streams
# and compare source-derived geometric quantities; they never import runtime.
from tools.keyed_zip_reference import (
    source_units, codes, walk, check_location, same_location, check_all_locations,
    expected_occurrences, check_geometry, check_images, check_motion, implementation_basis,
    json_differences, compact_json_bytes, check_raw_framing, near,
)
