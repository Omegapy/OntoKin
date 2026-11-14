#!/usr/bin/env python3
"""Finite CPU material checks bound to fresh authority and geometry admission.

Only check_materials is a public admission API. Synthetic or producer-declared
native observations cannot attest capture provenance or authorize a target.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import importlib.util
import json
import math
import os
from pathlib import Path
import stat
import sys


sys.dont_write_bytecode = True
_SPEC = importlib.util.spec_from_file_location(
    "ontokin_c234_geometry", Path(__file__).absolute().parents[1] / "second_target_c222/check_observations.py")
c222 = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(c222)
c221 = c222.c221

VERSION = "C234/0.1.0"
SCHEMA = "ontokin.c234.material-observations/0.1"
REPORT_SCHEMA = "ontokin.c234.material-comparison/0.1"
MAX_MATERIAL_OBSERVATION_BYTES = 256 * 1024
ALBEDO_STORAGE = "srgb-rgb-linear-alpha"
PARAMETER_LIMIT = 0.000002
_EXACT_LIMIT = Fraction(1, 500000)
_STAGES = ("admission", "geometry", "structure", "comparison")


class CheckError(ValueError):
    def __init__(self, code, message, stage="material_structure", report=None):
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.report = report


def require(condition, code, message, stage="material_structure"):
    if not condition:
        raise CheckError(code, message, stage)


def _fields(value, expected, label):
    require(type(value) is dict and set(value) == set(expected), "SCHEMA", label + ": exact fields required")


def _integer(value, label):
    require(type(value) is int and value >= 0, "INDEX", label + ": nonnegative integer required")
    return value


def _text(value, label):
    require(type(value) is str and 0 < len(value) <= 4096 and "\x00" not in value,
            "TEXT", label + ": bounded nonempty text required")
    return value


def _unit_number(value, label, stage="material_structure"):
    try:
        valid = type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1
    except OverflowError:
        valid = False
    require(valid, "PARAMETER", label + ": finite numeric value in [0, 1] required", stage)
    return value


def _read_material_observation(path):
    supplied = os.fspath(path)
    require(type(supplied) is str and "\x00" not in supplied and ".." not in supplied.split("/"),
            "PATH", "Unsafe material observation path", "material_read")
    absolute = Path(os.path.abspath(supplied))
    try:
        with c221.SafeRoot(absolute.parent) as parent:
            fd = os.open(absolute.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent.fd)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "FILE", "Material observation must be a regular file", "material_read")
                require(0 < before.st_size <= MAX_MATERIAL_OBSERVATION_BYTES,
                        "SIZE", "Material observation exceeds finite size bounds", "material_read")
                chunks, remaining = [], before.st_size + 1
                while remaining:
                    chunk = os.read(fd, min(65536, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
                after = os.fstat(fd)
                keys = ("st_dev", "st_ino", "st_size", "st_mode", "st_mtime_ns", "st_ctime_ns")
                require(len(raw) == before.st_size and all(getattr(before, k) == getattr(after, k) for k in keys),
                        "CHANGED", "Material observation changed while reading", "material_read")
                return raw
            finally:
                os.close(fd)
    except (OSError, c221.CheckError) as exc:
        raise CheckError("FILE", "Missing, unsafe or unreadable material observation", "material_read") from exc


def _source_materials(glb):
    """Decode source parameters; this internal seam does not admit a GLB."""
    materials = glb.get("materials")
    require(type(materials) is list and len(materials) == 2,
            "SOURCE_MATERIAL", "Exactly two source materials required", "source_materials")
    result = {}
    for index, material in enumerate(materials):
        require(type(material) is dict and set(material) <= {"name", "pbrMetallicRoughness", "doubleSided", "alphaMode"},
                "SOURCE_MATERIAL", "Unsupported source material fields", "source_materials")
        pbr = material.get("pbrMetallicRoughness")
        require(type(pbr) is dict and set(pbr) == {"baseColorFactor", "metallicFactor", "roughnessFactor"},
                "SOURCE_MATERIAL", "Complete finite source parameters required", "source_materials")
        color = pbr["baseColorFactor"]
        require(type(color) is list and len(color) == 4, "SOURCE_MATERIAL", "Source RGBA required", "source_materials")
        for value in color:
            _unit_number(value, "Source color", "source_materials")
        metallic = _unit_number(pbr["metallicFactor"], "Source metallic", "source_materials")
        roughness = _unit_number(pbr["roughnessFactor"], "Source roughness", "source_materials")
        sidedness = material.get("doubleSided", False)
        alpha_mode = material.get("alphaMode", "OPAQUE")
        require(type(sidedness) is bool and alpha_mode == "OPAQUE", "SOURCE_MATERIAL",
                "Finite source sidedness/opaque mode required", "source_materials")
        result[index] = {"linear_rgba": list(color), "metallic": metallic, "roughness": roughness,
                         "double_sided": sidedness, "alpha_mode": alpha_mode,
                         "cull_mode": "disabled" if sidedness else "back", "transparency_mode": "disabled"}
    return result


def _read_source(package_root):
    bindings, part_map = c221.load_authority()
    pin = bindings["items"][0]
    with c221.SafeRoot(package_root) as package:
        raw = package.read(pin["packagePath"], pin["bytes"], pin["sha256"], pin["mode"])
    glb, _ = c221.decode_glb(raw)
    materials = _source_materials(glb)
    parts = {}
    for planned in part_map["entries"]:
        node, mesh = planned["glbNode"], planned["glbMesh"]
        require(glb["nodes"][node]["mesh"] == mesh, "SOURCE_MATERIAL", "Source mesh association differs", "source_materials")
        surfaces = {}
        for primitive in planned["primitives"]:
            number = primitive["primitive"]
            actual = glb["meshes"][mesh]["primitives"][number]["material"]
            require(type(actual) is int and actual in materials and actual == primitive["material"],
                    "SOURCE_MATERIAL", "Source primitive/material association differs", "source_materials")
            surfaces[number] = actual
        parts[node] = {"planned": planned, "surfaces": surfaces}
    require(len(parts) == 18 and {i for p in parts.values() for i in p["surfaces"].values()} == {0, 1},
            "SOURCE_MATERIAL", "Complete source material associations required", "source_materials")
    return {"parts": parts, "materials": materials, "glb_sha256": pin["sha256"]}


def _validate_raw(raw):
    _fields(raw, ("albedo_storage", "albedo_rgb", "alpha", "metallic", "roughness", "cull_mode", "transparency_mode"), "Raw material")
    require(raw["albedo_storage"] == ALBEDO_STORAGE, "COLOR_SEMANTICS", "Only the predeclared sRGB RGB/linear alpha storage is supported")
    rgb = raw["albedo_rgb"]
    require(type(rgb) is list and len(rgb) == 3, "PARAMETER", "Exactly three raw albedo components required")
    for value in rgb:
        _unit_number(value, "Raw albedo")
    for key in ("alpha", "metallic", "roughness"):
        _unit_number(raw[key], "Raw " + key)
    require(type(raw["cull_mode"]) is str and raw["cull_mode"] in ("back", "front", "disabled"),
            "CULLING", "Unknown raw culling meaning")
    require(type(raw["transparency_mode"]) is str and raw["transparency_mode"] in ("disabled", "alpha", "alpha-scissor"),
            "OPACITY", "Unknown raw transparency meaning")


def _validate_structure(observation, geometry, geometry_report, authority):
    """Internal schema/association seam; no caller-provided report is admission."""
    _fields(observation, ("schema", "declared_origin", "accepted_program_revision", "glb_sha256", "geometry_observation", "parts"), "Material observation")
    require(observation["schema"] == SCHEMA, "SCHEMA", "Unsupported material observation schema")
    require(type(observation["declared_origin"]) is str and observation["declared_origin"] in ("synthetic", "unattested-native"),
            "SCHEMA", "Unsupported declared material origin")
    require(observation["accepted_program_revision"] == c221.ACCEPTED_REVISION and observation["glb_sha256"] == authority["glb_sha256"],
            "IDENTITY", "Material source/artifact claim differs")
    binding = observation["geometry_observation"]
    _fields(binding, ("sha256", "bytes"), "Geometry observation binding")
    require(_integer(binding["bytes"], "Geometry bytes") == geometry_report["observation_bytes"] and
            binding["sha256"] == geometry_report["observation_sha256"],
            "GEOMETRY_BINDING", "Material observations do not bind the exact checked geometry bytes")
    values = observation["parts"]
    require(type(values) is list and len(values) == 18, "COUNT", "Exactly 18 material-observed parts required")
    by_node = {part["gltf_node"]: part for part in geometry["parts"]}
    nodes, resources, rows = set(), {}, []
    for part in values:
        _fields(part, ("gltf_node", "gltf_mesh", "element_id", "source_path", "native_node_id", "surfaces"), "Material part")
        node, mesh = _integer(part["gltf_node"], "glTF node"), _integer(part["gltf_mesh"], "glTF mesh")
        require(node in authority["parts"] and node not in nodes, "IDENTITY", "Unexpected or duplicate material part")
        nodes.add(node)
        expected = authority["parts"][node]
        planned, seen_geometry = expected["planned"], by_node[node]
        require(mesh == planned["glbMesh"] and part["source_path"] == planned["sourcePath"] and
                c221.canonical(part["element_id"]) == c221.canonical(planned["elementId"]),
                "IDENTITY", "Material part identity disagrees with admitted node/mesh/source")
        native_id = _text(part["native_node_id"], "Native node label")
        require(native_id == seen_geometry["native_node_id"], "GEOMETRY_BINDING", "Material node label differs from bound geometry")
        surfaces = part["surfaces"]
        require(type(surfaces) is list and len(surfaces) == len(expected["surfaces"]), "COUNT", "Complete material primitive inventory required")
        geometry_surfaces = {s["gltf_primitive"]: s for s in seen_geometry["surfaces"]}
        primitives = set()
        for surface in surfaces:
            _fields(surface, ("gltf_primitive", "material_index", "native_material_id", "raw"), "Material surface")
            primitive = _integer(surface["gltf_primitive"], "glTF primitive")
            material = _integer(surface["material_index"], "Source material index")
            require(primitive in expected["surfaces"] and primitive not in primitives, "MATERIAL_BINDING", "Unexpected or duplicate material primitive")
            primitives.add(primitive)
            require(material == expected["surfaces"][primitive] and material == geometry_surfaces[primitive]["material_index"],
                    "MATERIAL_BINDING", "Material index differs from admitted primitive or bound geometry")
            resource = _text(surface["native_material_id"], "Native material resource label")
            _validate_raw(surface["raw"])
            resource_value = (material, c221.canonical(surface["raw"]))
            require(resource not in resources or resources[resource] == resource_value,
                    "RESOURCE_BINDING", "One declared material resource has conflicting source index or raw values")
            resources[resource] = resource_value
            rows.append({"gltf_node": node, "gltf_mesh": mesh, "gltf_primitive": primitive, "material_index": material,
                         "element_id": part["element_id"], "source_path": part["source_path"],
                         "native_node_id": native_id, "native_material_id": resource, "raw": surface["raw"]})
    require(nodes == set(authority["parts"]) and {r["material_index"] for r in rows} == {0, 1},
            "MATERIAL_BINDING", "Incomplete admitted part/material associations")
    return {"result": "PASS_MATERIAL_STRUCTURE", "parts": len(nodes), "surface_associations": len(rows),
            "source_materials": 2, "declared_native_resources": len(resources)}, sorted(rows, key=lambda r: (r["gltf_node"], r["gltf_primitive"]))


def _srgb_to_linear(value):
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _normalize_raw(raw):
    """Internal conversion seam; alpha is copied without a color transfer."""
    return {"linear_rgba": [_srgb_to_linear(v) for v in raw["albedo_rgb"]] + [raw["alpha"]],
            "metallic": raw["metallic"], "roughness": raw["roughness"],
            "cull_mode": raw["cull_mode"], "transparency_mode": raw["transparency_mode"]}


def _within_tolerance(actual, expected):
    # Compare the represented numeric values without subtraction-rounding slack.
    return abs(Fraction(actual) - Fraction(expected)) <= _EXACT_LIMIT


def _compare(rows, materials):
    result_rows, failures, maximum = [], [], 0.0
    for row in rows:
        normalized = _normalize_raw(row["raw"])
        expected = materials[row["material_index"]]
        actual_values = normalized["linear_rgba"] + [normalized["metallic"], normalized["roughness"]]
        expected_values = expected["linear_rgba"] + [expected["metallic"], expected["roughness"]]
        channels = ("red", "green", "blue", "alpha", "metallic", "roughness")
        deltas = [abs(a - e) for a, e in zip(actual_values, expected_values)]
        checks = {name: _within_tolerance(a, e) for name, a, e in zip(channels, actual_values, expected_values)}
        checks["culling"] = normalized["cull_mode"] == expected["cull_mode"]
        checks["opacity_mode"] = normalized["transparency_mode"] == expected["transparency_mode"]
        maximum = max(maximum, *deltas)
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            failures.append({"gltf_node": row["gltf_node"], "gltf_primitive": row["gltf_primitive"], "failed_checks": failed})
        result_rows.append({**row, "normalized": normalized, "source": expected,
                            "absolute_errors": dict(zip(channels, deltas)), "checks": checks})
    return {"result": "PASS_MATERIAL_PARAMETERS" if not failures else "FAIL_MATERIAL_PARAMETERS",
            "parameter_limit": PARAMETER_LIMIT, "parameter_limit_exact": "1/500000",
            "numeric_rule": "absolute difference of represented normalized/source numbers <= exact 1/500000; no epsilon",
            "color_mapping": "sRGB inverse: c/12.92 for c<=0.04045; ((c+0.055)/1.055)^2.4 otherwise; alpha unchanged",
            "numeric_components_compared": len(rows) * 6, "exact_mode_checks": len(rows) * 2,
            "maximum_absolute_error": maximum, "failed_associations": len(failures), "failures": failures, "rows": result_rows}


def _base_report():
    return {"schema": REPORT_SCHEMA, "version": VERSION, "result": "FAIL_CLOSED",
            **{stage: {"result": "NOT_RUN"} for stage in _STAGES},
            "limits": {"target_starts": 0, "native_version_starts": 0, "source_evaluations": 0,
                       "exports": 0, "imports": 0, "renders": 0, "scene_writes": 0,
                       "native_receiving_evidence": False, "native_mapping_attested": False,
                       "target_execution_authorized": False, "normal_values_compared": False, "poses_compared": False,
                       "meaning": "CPU parameter comparison of untrusted observations; no native capture, receiving acceptance or execution permission"}}


def check_materials(package_root, geometry_observation_path, material_observation_path):
    """Admit current authority and geometry bytes before checking materials."""
    report = _base_report()
    stage = "authority_admission"
    try:
        report["admission"] = c221.check_package(package_root)
        stage = "geometry_correspondence"
        geometry_report = c222.check_observations(package_root, geometry_observation_path)
        report["admission"] = geometry_report["admission"]
        raw_geometry = c222._read_observation(geometry_observation_path)
        require(len(raw_geometry) == geometry_report["observation_bytes"] and c221.digest(raw_geometry) == geometry_report["observation_sha256"],
                "GEOMETRY_CHANGED", "Geometry bytes changed after fresh C222 checking", "geometry_correspondence")
        geometry = c221.strict_json(raw_geometry, "Bound geometry observation")
        report["geometry"] = {"result": geometry_report["result"], "schema": geometry_report["schema"],
                              "observation_bytes": len(raw_geometry), "observation_sha256": c221.digest(raw_geometry),
                              "declared_origin": geometry_report["declared_origin"], "structure": geometry_report["structure"],
                              "corner_map_sha256": geometry_report["correspondence"]["corner_map_sha256"],
                              "native_receiving_evidence": False}
        stage = "source_materials"
        authority = _read_source(package_root)
        stage = "material_read"
        raw = _read_material_observation(material_observation_path)
        report["observation_bytes"] = len(raw)
        report["observation_sha256"] = c221.digest(raw)
        stage = "material_structure"
        observation = c221.strict_json(raw, "Material observation")
        report["structure"], rows = _validate_structure(observation, geometry, geometry_report, authority)
        report["declared_origin"] = observation["declared_origin"]
        stage = "material_comparison"
        report["comparison"] = _compare(rows, authority["materials"])
        require(not report["comparison"]["failures"], "MATERIAL_COMPARISON", "Observed material parameters or exact modes differ", stage)
        report["result"] = "PASS_CPU_MATERIALS"
        return report
    except (CheckError, c221.CheckError, c222.CheckError, OSError) as exc:
        effective_stage = exc.stage if isinstance(exc, CheckError) else stage
        report["error"] = {"code": getattr(exc, "code", "IO"), "stage": effective_stage, "message": str(exc)}
        if isinstance(exc, c222.CheckError):
            report["error"]["upstream_stage"] = exc.stage
        key = {"authority_admission": "admission", "geometry_correspondence": "geometry", "source_materials": "structure",
               "material_read": "structure", "material_structure": "structure", "material_comparison": "comparison"}.get(effective_stage)
        if key and report[key]["result"] == "NOT_RUN":
            report[key] = {"result": "FAIL_CLOSED"}
        raise CheckError(report["error"]["code"], str(exc), effective_stage, report) from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--geometry-observations", required=True)
    parser.add_argument("--material-observations", required=True)
    args = parser.parse_args(argv)
    try:
        report = check_materials(args.package_root, args.geometry_observations, args.material_observations)
    except CheckError as exc:
        print(json.dumps(exc.report, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 1
    print(json.dumps(report, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
