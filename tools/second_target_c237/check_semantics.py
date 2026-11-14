#!/usr/bin/env python3
"""Compare the finite C210 semantic declarations and actually retained bytes.

This CPU checker admits original authority on every call. Observation provenance
is declared, never attested, and no source or native application is executed.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys

sys.dont_write_bytecode = True
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).absolute().parents[2]))
from tools.second_target_c221 import check_bindings as authority

SCHEMA = "ontokin.second-target.c237.report/0.1"
OBSERVATION_SCHEMA = "ontokin.second-target.c237.observations/0.1"
VERSION = "C237/0.1.0"
MAX_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 64
MAX_VALUES = 100000
MAX_STRING_BYTES = 1024 * 1024
RETAINED_KINDS = {
    "program_bundle": authority.INPUT_PATHS[1],
    "glb": authority.INPUT_PATHS[0],
    "semantic_sidecar": authority.INPUT_PATHS[2],
    "source_normal_payload": authority.INPUT_PATHS[3],
}
DESCRIPTIVE = ("imported_native", "independently_derived", "observer_copied", "retained_external")
COPIED = ("observer_copied", "retained_external")
FEATURE_RULES = {
    "source_closure": (("retained_external",), "retained_source"),
    "stable_identities": (DESCRIPTIVE, "descriptive_metadata"),
    "dimensions_units_frames": (DESCRIPTIVE, "descriptive_metadata"),
    "ownership": (COPIED, "descriptive_metadata"),
    "following": (COPIED, "descriptive_metadata"),
    "hinge_constraints": (COPIED, "descriptive_metadata"),
    "physical_declarations": (COPIED, "descriptive_metadata"),
    "materials": (DESCRIPTIVE, "descriptive_metadata"),
    "primitive_geometry": (DESCRIPTIVE, "approximated_representation"),
    "world_motion": (DESCRIPTIVE, "baked_playback"),
    "numeric_precision": (DESCRIPTIVE, "approximated_representation"),
    "action_execution": (("unsupported",), "unsupported"),
    "live_physics": (("unsupported",), "unsupported"),
    "source_reconstruction": (("unsupported",), "unsupported"),
}
ROOT_FIELDS = {"schema", "producer", "programRevision", "parts", "semantics", "features", "retainedFiles", "capabilities"}
PART_FIELDS = {"sourceNode", "sourceMesh", "elementId", "definitionId", "sourcePath", "destinationLabel"}
FEATURE_FIELDS = {"feature", "treatment", "reason", "required", "provenance", "capability"}
LIMITS = {
    "native_attestation": False, "destination_mapping_attestation": False,
    "source_execution": False, "native_execution": False, "aggregate_execution": False,
    "source_evaluations": 0, "exports": 0, "imports": 0, "target_starts": 0,
    "scene_writes": 0, "native_receiving_acceptance": False,
    "geometry_material_normal_pose_accuracy": False, "full_r07_acceptance": False,
    "meaning": "Finite declared-semantic equality and inspected retained bytes only; provenance labels are unattested claims",
}


class Refusal(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise Refusal(code, message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def fields(value, names, label):
    require(type(value) is dict and set(value) == set(names), "SHAPE", label + ": missing or unknown fields")


def string(value, label):
    require(type(value) is str and bool(value), "TYPE", label + ": expected a nonempty string")


def json_bounds(value):
    count = 0
    def visit(item, depth):
        nonlocal count
        count += 1
        require(count <= MAX_VALUES, "SIZE", "JSON value count exceeds finite limit")
        require(depth <= MAX_DEPTH, "DEPTH", "JSON nesting exceeds finite limit")
        if type(item) is dict:
            for key, child in item.items():
                visit(key, depth + 1)
                visit(child, depth + 1)
        elif type(item) is list:
            for child in item:
                visit(child, depth + 1)
        elif type(item) is str:
            require(len(item.encode("utf-8")) <= MAX_STRING_BYTES, "SIZE", "JSON string exceeds finite limit")
        elif type(item) is float:
            require(math.isfinite(item), "JSON", "Nonfinite number")
        else:
            require(item is None or type(item) in (int, bool), "JSON", "Unsupported JSON scalar")
    visit(value, 0)
    return count


def parse_json(raw, label):
    try:
        value = authority.strict_json(raw, label)
        json_bounds(value)
        return value
    except Refusal:
        raise
    except (authority.CheckError, UnicodeError, ValueError, RecursionError) as exc:
        raise Refusal(getattr(exc, "code", "JSON"), label + ": " + str(exc)) from exc


def read_observation(path):
    supplied = os.fspath(path)
    require(type(supplied) is str and supplied and "\x00" not in supplied and "\\" not in supplied,
            "PATH", "Invalid observation path")
    require(".." not in supplied.split("/"), "PATH", "Observation traversal is refused")
    absolute = os.path.abspath(supplied)
    parent, name = os.path.split(absolute)
    require(bool(name), "PATH", "Observation path must name a file")
    try:
        with authority.SafeRoot(parent) as root:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root.fd)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode), "FILE", "Observation must be a regular file")
                require(0 < before.st_size <= MAX_BYTES, "SIZE", "Observation byte size exceeds finite bounds")
                chunks, remaining = [], before.st_size + 1
                while remaining:
                    chunk = os.read(fd, min(1024 * 1024, remaining))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    remaining -= len(chunk)
                raw = b"".join(chunks)
                after = os.fstat(fd)
                named = os.stat(name, dir_fd=root.fd, follow_symlinks=False)
                keys = ("st_dev", "st_ino", "st_size", "st_mode", "st_mtime_ns", "st_ctime_ns")
                require(all(getattr(before, k) == getattr(after, k) == getattr(named, k) for k in keys),
                        "CHANGED", "Observation changed while reading")
                require(len(raw) == before.st_size, "CHANGED", "Observation read length changed")
                return raw, {"path": absolute, "bytes": len(raw), "sha256": digest(raw)}
            finally:
                os.close(fd)
    except OSError as exc:
        raise Refusal("FILE", "Observation is missing, unsafe or unreadable") from exc


def same_shape(expected, observed, path):
    require(type(expected) is type(observed), "TYPE", path + ": JSON type differs")
    if type(expected) is dict:
        require(set(expected) == set(observed), "SHAPE", path + ": fields differ")
        for key in expected:
            same_shape(expected[key], observed[key], path + "/" + key)
    elif type(expected) is list:
        require(len(expected) == len(observed), "COUNT", path + ": array length differs")
        for index, (left, right) in enumerate(zip(expected, observed)):
            same_shape(left, right, path + "/" + str(index))


def differences(expected, observed, path=""):
    rows = []
    if type(expected) is not type(observed):
        return [{"path": path, "expected": expected, "observed": observed}]
    if type(expected) is dict:
        for key in sorted(expected):
            rows.extend(differences(expected[key], observed[key], path + "/" + key.replace("~", "~0").replace("/", "~1")))
    elif type(expected) is list:
        for index, (left, right) in enumerate(zip(expected, observed)):
            rows.extend(differences(left, right, path + "/" + str(index)))
    elif canonical(expected) != canonical(observed):
        rows.append({"path": path, "expected": expected, "observed": observed})
    return rows


def typed_equal(expected, observed):
    try:
        same_shape(expected, observed, "equality")
    except Refusal:
        return False
    return not differences(expected, observed)


def keyed(rows, key, expected_keys, row_fields, label):
    require(type(rows) is list and len(rows) == len(expected_keys), "COUNT", label + ": wrong count")
    result = {}
    for row in rows:
        fields(row, row_fields, label)
        value = row[key]
        require(type(value) in (str, int), "IDENTITY", label + ": invalid key type")
        require(value not in result, "IDENTITY", label + ": duplicate identity")
        result[value] = row
    require(set(result) == set(expected_keys), "IDENTITY", label + ": missing or unknown identity")
    return result


def original_inputs(package_root):
    admission = authority.check_package(package_root)
    bindings, part_map = authority.load_authority()
    pins = {row["packagePath"]: row for row in bindings["items"]}
    loaded = {}
    with authority.SafeRoot(package_root) as root:
        for path in (authority.INPUT_PATHS[1], authority.INPUT_PATHS[2], authority.INPUT_PATHS[6]):
            pin = pins[path]
            raw = root.read(path, pin["bytes"], pin["sha256"], pin["mode"])
            loaded[path] = parse_json(raw, path)
    semantic = loaded[authority.INPUT_PATHS[2]]
    oracle = loaded[authority.INPUT_PATHS[6]]
    oracle_semantic = parse_json(oracle["semantic_canonical"].encode("utf-8"), "Frozen oracle semantics")
    require(typed_equal(semantic, oracle_semantic), "AUTHORITY", "Pinned semantic sidecar and independent oracle disagree")
    require({row["feature"] for row in semantic["features"]} == set(FEATURE_RULES),
            "AUTHORITY", "Unsupported original feature inventory")
    return admission, bindings, part_map, pins, loaded[authority.INPUT_PATHS[1]], semantic


def bundle_inspection(bundle):
    fields(bundle, {"schema_version", "entry", "modules"}, "Retained bundle")
    string(bundle["schema_version"], "Retained bundle schema")
    fields(bundle["entry"], {"filename", "source"}, "Retained entry")
    require(type(bundle["modules"]) is list and len(bundle["modules"]) == 1, "SOURCE", "Expected one retained dependency")
    module = bundle["modules"][0]
    fields(module, {"package_id", "version", "filename", "source"}, "Retained dependency")
    string(module["package_id"], "Package identity")
    string(module["version"], "Package version")
    units = []
    for source_id, package_id, version, unit in (
        ("entry", None, None, bundle["entry"]),
        ("package:" + module["package_id"] + "@" + module["version"], module["package_id"], module["version"], module),
    ):
        string(unit["filename"], "Source filename")
        require(type(unit["source"]) is str, "SOURCE", "Source text must be a string")
        raw = unit["source"].encode("utf-8")
        units.append({"source_id": source_id, "package_id": package_id, "version": version,
                      "filename": unit["filename"], "source_revision": "sha256:" + digest(raw),
                      "bytes": len(raw), "source": unit["source"]})
    manifest = {"schema_version": bundle["schema_version"], "entry_source_id": "entry", "units": [
        {k: row[k] for k in ("source_id", "package_id", "version", "filename", "source_revision")} for row in units
    ]}
    supported = bundle["schema_version"] == "ontokin.bundle/0.1"
    revision = "sha256:" + digest(b"ontokin.bundle/0.1\0" + canonical(manifest)) if supported else None
    return {"manifest": manifest, "units": units, "schema_supported": supported, "program_revision": revision}


def expected_parts(part_map):
    return [{"sourceNode": row["glbNode"], "sourceMesh": row["glbMesh"],
             "elementId": row["elementId"], "definitionId": row["definitionId"],
             "sourcePath": row["sourcePath"]} for row in part_map["entries"]]


def expected_capabilities(semantic):
    return {"liveFollowing": False, "liveHinges": False, "actionExecution": False,
            "livePhysics": False, "sourceReconstruction": False, "rigidBodyCount": 0,
            "controllerCount": 0, "representedBodyMassKg": 0.0,
            "motionAuthority": semantic["scene"]["motion_authority"]}


def admitted_report(observation, admission, bindings, part_map, pins, bundle, semantic):
    fields(observation, ROOT_FIELDS, "Observation")
    require(observation["schema"] == OBSERVATION_SCHEMA, "SCHEMA", "Unsupported observation schema")
    fields(observation["producer"], {"kind", "name"}, "Producer")
    require(observation["producer"]["kind"] in ("synthetic", "declared_destination"), "PROVENANCE", "Unsupported producer kind")
    string(observation["producer"]["name"], "Producer name")
    require(observation["programRevision"] == authority.ACCEPTED_REVISION, "IDENTITY", "Stale program revision")
    parts = expected_parts(part_map)
    by_part = keyed(observation["parts"], "sourceNode", [r["sourceNode"] for r in parts], PART_FIELDS, "Parts")
    part_rows = []
    for expected in parts:
        row = by_part[expected["sourceNode"]]
        string(row["destinationLabel"], "Destination label")
        actual = {k: row[k] for k in expected}
        require(typed_equal(expected, actual), "IDENTITY", "Complete part identity differs for node " + str(expected["sourceNode"]))
        part_rows.append({"expected": expected, "observed": row, "identityEqual": True, "destinationMappingAttested": False})
    capabilities = expected_capabilities(semantic)
    require(typed_equal(capabilities, observation["capabilities"]), "CAPABILITY", "Capability claims contradict the finite no_body profile")
    same_shape(semantic, observation["semantics"], "/semantics")
    semantic_losses = differences(semantic, observation["semantics"], "/semantics")
    original_features = {r["feature"]: r for r in semantic["features"]}
    by_feature = keyed(observation["features"], "feature", original_features, FEATURE_FIELDS, "Features")
    feature_rows, losses = [], [{"category": "semantic_value", **row} for row in semantic_losses]
    for name, expected in original_features.items():
        row = by_feature[name]
        actual = {k: row[k] for k in expected}
        same_shape(expected, actual, "/features/" + name)
        origins, capability = FEATURE_RULES[name]
        require(type(row["provenance"]) is str and row["provenance"] in origins and row["capability"] == capability,
                "PROVENANCE", name + ": provenance/capability combination is not supported")
        require(expected["treatment"] != "unsupported" or row["treatment"] == "unsupported",
                "CAPABILITY", name + ": unsupported source capability cannot be upgraded")
        matched = typed_equal(expected, actual)
        feature_rows.append({"feature": name, "expected": expected, "observed": row,
                             "sourceTreatmentEqual": matched, "provenanceAttested": False})
        if not matched:
            losses.append({"category": "source_feature_treatment", "feature": name,
                           "mismatches": differences(expected, actual, "/features/" + name)})
    retained = keyed(observation["retainedFiles"], "kind", RETAINED_KINDS, {"kind", "base64"}, "Retained files")
    retained_rows, decoded = [], {}
    for kind, path in RETAINED_KINDS.items():
        encoded = retained[kind]["base64"]
        require(type(encoded) is str, "ENCODING", kind + ": base64 must be a string")
        try:
            raw = base64.b64decode(encoded.encode("ascii"), validate=True)
        except (ValueError, UnicodeError, binascii.Error) as exc:
            raise Refusal("ENCODING", kind + ": malformed canonical base64") from exc
        require(base64.b64encode(raw).decode("ascii") == encoded, "ENCODING", kind + ": noncanonical base64")
        decoded[kind] = raw
        pin = pins[path]
        actual = {"bytes": len(raw), "sha256": digest(raw)}
        expected = {"packagePath": path, "bytes": pin["bytes"], "sha256": pin["sha256"]}
        matched = actual["bytes"] == pin["bytes"] and actual["sha256"] == pin["sha256"]
        status = "equal" if matched else ("absent" if not raw else "changed")
        retained_rows.append({"kind": kind, "expected": expected, "observed": actual, "bytesEqual": matched, "status": status})
        if not matched:
            losses.append({"category": "retained_bytes", "kind": kind, "status": status, "expected": expected, "observed": actual})
    expected_units = bundle_inspection(bundle)
    require(expected_units["program_revision"] == authority.ACCEPTED_REVISION and
            typed_equal(expected_units["manifest"], bindings["sourceManifest"]),
            "AUTHORITY", "Original inspected source manifest/revision differs")
    unit_check = {"expected": expected_units, "observed": None, "equal": False, "error": None}
    try:
        observed_units = bundle_inspection(parse_json(decoded["program_bundle"], "Decoded retained program bundle"))
        unit_check.update(observed=observed_units, equal=typed_equal(expected_units, observed_units))
    except (Refusal, UnicodeError, ValueError) as exc:
        unit_check["error"] = {"code": getattr(exc, "code", "SOURCE"), "message": str(exc)}
    if not unit_check["equal"]:
        losses.append({"category": "retained_source_units", "inspectionError": unit_check["error"]})
    return {
        "authority": admission, "producer": observation["producer"],
        "programRevision": authority.ACCEPTED_REVISION,
        "requiredFeatures": sorted(row["feature"] for row in semantic["features"] if row["required"]),
        "counts": {"parts": len(parts), "features": len(original_features), "retainedFiles": len(retained_rows),
                   "sourceUnits": len(expected_units["units"]), **{k: len(semantic[k]) for k in ("objects", "sites", "follows", "joints", "actions", "events", "collections")}},
        "partComparisons": part_rows, "featureComparisons": feature_rows,
        "retentionComparisons": retained_rows, "sourceUnitInspection": unit_check,
        "semanticComparison": {"shapeAdmitted": True, "equal": not semantic_losses,
                               "expectedCanonicalSha256": digest(canonical(semantic)),
                               "observedCanonicalSha256": digest(canonical(observation["semantics"])),
                               "mismatches": semantic_losses, "expected": semantic, "observed": observation["semantics"]},
        "capabilities": {"expected": capabilities, "observed": observation["capabilities"],
                         "representedMassBasis": "Declaration-derived zero: all 18 admitted parts are no_body; no native mass measurement"},
        "losses": losses,
    }


def base_report():
    return {"schema": SCHEMA, "version": VERSION, "passed": False,
            "result": "REFUSED", "resultClass": "structural_refusal", "limits": dict(LIMITS)}


def check_semantics(package_root, observation_path):
    """Return one finite pass/loss/refusal report after fresh C221 admission."""
    report = base_report()
    try:
        original = original_inputs(package_root)
        report["authority"] = original[0]
        raw, binding = read_observation(observation_path)
        report["observation"] = binding
        observation = parse_json(raw, "Observation")
        report.update(admitted_report(observation, *original))
        report["passed"] = not report["losses"]
        report["resultClass"] = "pass" if report["passed"] else "measured_loss"
        report["result"] = "PASS_CPU_SEMANTIC_RETENTION" if report["passed"] else "FAIL_MEASURED_SEMANTIC_RETENTION"
    except (Refusal, authority.CheckError, OSError, TypeError, ValueError) as exc:
        report["error"] = {"code": getattr(exc, "code", "INPUT"), "message": str(exc)}
    return report


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("ARGUMENT", message)


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__, add_help=False)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--observations", required=True)
    try:
        args = parser.parse_args(argv)
        report = check_semantics(args.package_root, args.observations)
    except Refusal as exc:
        report = base_report()
        report["error"] = {"code": exc.code, "message": str(exc)}
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False))
    return 0 if report["passed"] else (1 if report["resultClass"] == "measured_loss" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
