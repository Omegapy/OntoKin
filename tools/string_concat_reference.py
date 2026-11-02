"""Independent C087 input, value and native-artifact reference readers.

Only the published, preimplementation byte inventory supplies expected answers.
This module imports no OntoKin parser, compiler, evaluator, Agent or exporter.
The unchanged predecessor byte/source readers are deliberately reused.
"""
from __future__ import annotations

import copy
import gzip
import json
from itertools import product
from pathlib import Path

from tools.texture_reference import (
    GLB, ReferenceError, SAMPLER, bundle_identity, canonical, decode_png, digest,
    exact_uv, f32, file_payload, loads, ordinary_path, repack_glb, require, sha,
)
from tools.keyed_zip_reference import (
    source_units, codes, walk, check_location, same_location, check_all_locations,
    expected_occurrences, check_geometry, check_images, check_motion,
    implementation_basis, json_differences, compact_json_bytes,
    check_raw_framing, near,
)
from tools.string_concat_source_reference import (
    canonical_probe_type, original_keyed_entries, inspect_member, semantic_value,
    check_keyed_membership, merge_location, exact_location, exact_public_location,
    intrinsic_locations, merge_source_shape, zip_source_shape, rekey_source_shape,
    check_transforms, check_reductions, check_filters, check_merges, check_zips,
    check_rekeys, enriched_zip_records, with_merge_side, diagnostic_anchor,
    check_origin_projection, _location_identity, _source_tokens, _closing_delimiter,
)

ROOT = Path(__file__).resolve().parents[1]
FREEZE_COMMIT = "cd8c7fa2f84922ff4855de20f67b4be8d8866d5d"
FREEZE_SHA256 = "b3a11de3aaaf4a6237e0526123b28da15e10ef5fa3a05353bd13885abb7187d4"
SPECIFICATION_SHA256 = "2c72d8c104d8c6db924b3b42291c05431011df3e575e11d6a85f4b6f78cd4432"
PROFILE = "string-concat-0.1"
PROTOCOL = "ontokin.agent/0.20"
TARGET = "ontokin.glb/0.20"
STORE_SCHEMA = "ontokin.string-concat-program-agent-store/0.1"
AMENDMENTS = ()
DEFAULT_POLICY = {"max_operations": 100000, "max_elapsed_ms": 30000}
HIGH_POLICY = {"max_operations": 400000, "max_elapsed_ms": 80000}
DELIVERED_CASES = frozenset({"panel-task", "panel-task-repaired", "panel-task-restored",
    "panel-task-reordered", "panel-task-inserted", "panel-task-removed", "panel-task-higher-budget"})


def panel_expectations(case):
    """Expand the frozen dimensional answers, never a produced GLB."""
    require(case["name"] in DELIVERED_CASES, "No geometry expected for refused source")
    times = case["times_seconds"]
    require(times == [0, .25, .5, .75, 1], "Frozen time grid differs")
    panels, marker = [], None
    for path, row in case["required_geometry"].items():
        w, h, d = (row[key] for key in ("width_m", "height_m", "depth_m"))
        corners = [list(point) for point in product((0, w), (0, h), (0, d))]
        require(row["raw_corner_set_m"] == corners and row["triangles"] == 12 and
                row["quaternion_wxyz"] == [1, 0, 0, 0], "Frozen prism facts differ")
        is_panel = "panels[" in path
        materials = {region: copy.deepcopy(row["side_material"] if region == "side" else
            row["cap_material"]) for region in ("bottom", "side", "top")} if is_panel else {
            region: copy.deepcopy(row["material"]) for region in ("bottom", "side", "top")}
        value = {"path": path, "element_id": copy.deepcopy(row["element_id"]), "width_m": w,
            "local_bounds_m": [[0, 0, 0], [w, h, d]], "raw_corner_set_m": corners,
            "triangle_count": 12, "volume_m3": w*h*d,
            "surface_area_m2": 2*(w*h+w*d+h*d),
            "region_triangle_counts": {"bottom": 2, "side": 8, "top": 2},
            "materials": materials,
            "poses": [{"time_s": t, "position_m": copy.deepcopy(point),
                "rotation_xyzw": [0, 0, 0, 1]} for t, point in zip(times, row["translation_samples_m"])]}
        require(len(value["poses"]) == len(times), "Missing authored pose sample")
        if is_panel:
            owner = path.split(".", 1)[0]
            key = json.loads(path.split("[", 1)[1][:-1])
            require(key == row["new_key"] and row["payload"] == row["old_key"] and
                    row["texture"]["sampler"] == SAMPLER and
                    row["texture"]["uv_formula"] == ["0.5*x", "1-0.5*y"],
                    "Frozen payload/UV/sampler facts differ")
            value.update(owner=owner, input_key=key, old_key=row["old_key"])
            panels.append(value)
        else:
            require(path == "marker" and marker is None, "Unexpected ordinary mesh")
            marker = value
    require(marker is not None, "Missing frozen marker")
    return {"panels": panels, "marker": marker, "times_seconds": times,
        "mapping": {"u_per_m": [.5, 0, 0], "v_per_m": [0, -.5, 0],
                    "origin_m": [0, 0, 0], "offset": [0, 1]},
        "object_count": len(panels)+3,
        "widths_m": {owner: {p["input_key"]: p["width_m"] for p in panels if p["owner"] == owner}
                     for owner in ("first", "sibling")}}


def load_fixtures(root=ROOT):
    """Verify all 546 exact frozen members, then expose immutable-case helpers.

    Accepts a repository root or its examples/string-concat directory for the
    inherited CLI convention. No aliases change any frozen on-disk JSON.
    """
    root = Path(root).resolve()
    repository = root.parent.parent if root.name == "string-concat" and root.parent.name == "examples" else root
    root = repository / "examples/string-concat"
    design = "docs/language-design/string-concat-v0.1/"
    raw = ordinary_path(repository, design+"freeze/INPUTS-MANIFEST.json").read_bytes()
    require(sha(raw) == FREEZE_SHA256, "Published C087 input manifest changed")
    require(sha(ordinary_path(repository, design+"SPECIFICATION.md").read_bytes()) == SPECIFICATION_SHA256,
            "Published C087 semantic specification changed")
    manifest = loads(raw); names, total = set(), 0
    for entry in manifest["files"]:
        name = entry["path"]
        require(name.startswith("examples/string-concat/") and name not in names, "Duplicate/outside frozen member")
        path = ordinary_path(repository, name); data = path.read_bytes()
        require(len(data) == entry["bytes"] and sha(data) == entry["sha256"], "Frozen member bytes differ: "+name)
        require(entry["mode"] == ("100755" if path.stat().st_mode & 0o111 else "100644"),
                "Frozen member mode differs: "+name)
        names.add(name); total += len(data)
    require(len(names) == 546 and total == 11313625, "Incomplete C087 frozen inventory")
    observed = {path.relative_to(repository).as_posix() for path in root.rglob("*") if path.is_file()}
    require(observed == names, "Undeclared or missing member in frozen input directory")
    core_raw = ordinary_path(root, "expected.json").read_bytes()
    agent_raw = ordinary_path(root, "agent/expected.json").read_bytes()
    expected, agent_expected = loads(core_raw), loads(agent_raw)
    core = {row["name"]: copy.deepcopy(row) for row in expected["cases"]}
    agents = {row["name"]: copy.deepcopy(row) for row in agent_expected["cases"]}
    require(len(core) == len(expected["cases"]) == 108 and len(agents) == 10 and not set(core)&set(agents),
            "Frozen case membership differs")
    require(sum(c["expected_outcome"] == "valid" for c in core.values()) == 72 and
            sum("explicit_c086_control" in c for c in core.values()) == 78,
            "Frozen core result/control inventory differs")
    require({name for name,c in agents.items() if c["expected_outcome"] == "valid"} == DELIVERED_CASES,
            "Frozen Agent delivery inventory differs")
    result = {"root": root, "core_root": root, "repository": repository, "agent_root": root/"agent",
        "manifest": manifest, "freeze": manifest, "expected": expected, "agent_expected": agent_expected,
        "core_cases": core, "agent_cases": agents, "cases": {**core, **agents}, "input_roots": {},
        "original_expected_sha256": sha(core_raw), "effective_expected_sha256": sha(core_raw),
        "agent_expected_sha256": sha(agent_raw), "amendments": []}
    for key, filename in (("workflows", "agent/workflows.json"), ("delivery", "agent/delivery-comparison.json"),
            ("budget", "agent/budget-expectations.json"), ("geometry", "agent/geometry-expectations.json"),
            ("adversaries", "agent/supplied-byte-adversaries.json"),
            ("agent_adversaries", "agent/agent-evidence-adversaries.json"),
            ("runtime_boundaries", "runtime-boundaries.json"), ("source_spans", "source-span-inventory.json"),
            ("negative_controls", "negative-controls.json"), ("interface", "interface-expectations.json")):
        result[key] = loads(ordinary_path(root, filename).read_bytes())
    require([r["id"] for r in result["workflows"]["workflows"]] == [f"A{i:02}" for i in range(1,12)],
            "Frozen Agent workflow membership differs")
    require(result["adversaries"]["expected_isolated_refusals"] == 75 and
            result["agent_adversaries"]["expected_isolated_refusals"] == 2, "Frozen hostile inventory differs")
    for name, case in result["cases"].items():
        if "bundle_identity" in case:
            case["canonical_manifest"] = copy.deepcopy(case["bundle_identity"])
        selected_root = result["agent_root"] if name in agents else root
        case["source"] = loads(ordinary_path(selected_root, case["file_manifest"]).read_bytes())["entry"]["path"]
        require(bundle_identity(case_payload(result, case)) == (case["program_revision"], case["canonical_manifest"]),
                "Frozen source bundle identity differs: "+name)
        if "explicit_c086_control" in case:
            control = case["explicit_c086_control"]
            if "bundle_identity" in control:
                control["canonical_manifest"] = copy.deepcopy(control["bundle_identity"])
            require(bundle_identity(case_payload(result, case, control=True)) ==
                    (control["program_revision"], control["canonical_manifest"]), "Frozen literal control identity differs: "+name)
        if name in agents:
            case["expected_protocol_outcome"] = ("valid" if case["expected_outcome"] == "valid" else
                "resource_limit" if case["expected_code"] == "OKL-E-RESOURCE" else "invalid")
            if case["expected_outcome"] == "valid":
                case["expected"] = panel_expectations(case)
    return result


def case_payload(fixtures, case, *, control=False):
    if isinstance(case, str):
        require(case in fixtures["cases"], "Unknown frozen source case")
        case = fixtures["cases"][case]
    require(isinstance(case, dict) and case.get("name") in fixtures["cases"], "Payload requires named frozen source")
    original = fixtures["cases"][case["name"]]
    require(case["file_manifest"] == original["file_manifest"], "Source file manifest changed")
    root = fixtures["agent_root"] if case["name"] in fixtures["agent_cases"] else fixtures["root"]
    if control:
        require("explicit_c086_control" in original, "Source lacks explicit .19 literal control")
        original = original["explicit_c086_control"]
    return file_payload(root, original["file_manifest"])


def input_lineage(fixtures):
    return {"frozen_input_commit": FREEZE_COMMIT, "frozen_manifest_sha256": FREEZE_SHA256,
        "specification_sha256": SPECIFICATION_SHA256,
        "original_expected_sha256": fixtures["original_expected_sha256"],
        "effective_expected_sha256": fixtures["effective_expected_sha256"],
        "agent_expected_sha256": fixtures["agent_expected_sha256"], "amendments": []}


def delivered_by_revision(fixtures):
    result = {}
    for name in sorted(DELIVERED_CASES):
        case = fixtures["agent_cases"][name]
        old = result.get(case["program_revision"])
        if old:
            require(case_payload(fixtures, old) == case_payload(fixtures, case) and
                    case_payload(fixtures, old, control=True) == case_payload(fixtures, case, control=True) and
                    old["expected"] == case["expected"], "Aliased Agent source revisions disagree")
        else:
            result[case["program_revision"]] = case
    return result


def read_private_json(path, limit=16777216):
    """Bounded full private observation; never silently accept a public truncation."""
    path = Path(path)
    with (gzip.open(path, "rb") if path.suffix == ".gz" else path.open("rb")) as stream:
        raw = stream.read(limit+1)
    require(len(raw) <= limit, "Private value observation exceeds its explicit bound")
    return loads(raw)


def check_private_value(actual, expected, fixtures):
    require(isinstance(actual, dict) and actual.get("type") == expected["type"], "Full private value type differs")
    kind = expected["type"]
    if kind.startswith("Keyed<"):
        entries = actual.get("entries")
        require(isinstance(entries, list) and len(entries) == len(expected["entries"]), "Full Keyed cardinality differs")
        require([r["key"] for r in entries] == expected["keys"] == sorted(expected["keys"]), "Full canonical Keyed keys differ")
        for got, wanted in zip(entries, expected["entries"]):
            require(got["key"] == wanted["key"], "Full Keyed leaf identity differs")
            value = wanted["value"]
            if not isinstance(value, dict):
                value = {"type": kind[6:-1], "value": value}
            check_private_value(got["value"], value, fixtures)
        return len(entries)
    value = actual.get("value")
    if kind == "String":
        require(isinstance(value, str), "String private payload absent or truncated")
        raw = value.encode("utf-8", errors="strict")
        require(len(raw) == expected["utf8_bytes"] and len(value) == expected["codepoints"] and
                sha(raw) == expected["sha256"], "Full String UTF-8/scalar/hash answer differs")
        for key, observed in (("literal", value), ("unicode_scalars", [ord(c) for c in value]), ("utf8_hex", raw.hex())):
            if key in expected:
                require(observed == expected[key], "Exact frozen String representation differs: "+key)
        if "literal_file" in expected:
            require(raw == ordinary_path(fixtures["root"], expected["literal_file"]).read_bytes(), "Full String literal bytes differ")
    else:
        require(value == expected["value"], "Full private scalar value differs")
    return 1


def check_artifact(raw, case, fixtures, control):
    from tools.string_concat_delivery_reference import check_artifact as read
    return read(raw, case, fixtures, control)


def check_inspection(actual, control, case, fixtures):
    from tools.string_concat_delivery_reference import check_agent_inspection
    require(case["name"] in fixtures["agent_cases"], "Core values use complete private read, not public truncation")
    return check_agent_inspection(actual, control, case, fixtures)


def check_panel_values(items, case, fixtures, units=None, *, control=False):
    from tools.string_concat_delivery_reference import check_panel_values as read
    return read(items, case, fixtures, units, control=control)


def panel_sources(case, fixtures, *, control=False):
    from tools.string_concat_delivery_reference import panel_sources as read
    return read(case, fixtures, control=control)


def check_program_metadata(glb, case, fixtures, *, control=False):
    from tools.string_concat_delivery_reference import check_program_metadata as read
    return read(glb, case, fixtures, control=control)
