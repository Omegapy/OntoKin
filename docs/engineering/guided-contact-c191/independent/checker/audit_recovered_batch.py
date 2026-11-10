#!/usr/bin/env python3
"""Supplement the original C191 batch with source/frame/raw-pose checks.

This recovery audit was written after inspecting the first recovered candidate.
It adds checks for existing contract obligations; it does not replace any frozen
fixture, alter a physical tolerance, or claim pre-candidate independence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from c190_glb_difference import decode, states


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check(condition, message):
    if not condition:
        raise ValueError(message)


def check_configuration(configuration, backend, canonical, mapping, source_hash):
    """Bind recorded objects and mapping rows to the already adopted model."""
    objects = configuration["objects"]
    identity = np.eye(4).tolist()
    rows = {row["native_object"]: row for row in mapping["rows"]}
    check(len(rows) == len(mapping["rows"]) == 13, "Mapping row inventory")
    check(set(rows) == set(objects), "Mapping/native object inventory")
    check(mapping["axis_mapping"] == backend["axis_mapping"], "Mapping frame declaration")
    check(mapping["source_sha256"] == source_hash, "Mapping source revision")
    check(mapping["source_colliders"] == canonical["colliders"], "Source collider mapping")
    check(mapping["moving_mass_total_kg"] == 2, "Moving mass total")
    check(sum(row["mass_contribution_kg"] for row in rows.values()) == 2, "Mass contribution sum")
    checked = []
    for declaration in backend["native_objects"]:
        name = declaration["name"]
        obj, row = objects[name], rows[name]
        part, body, collider = (declaration.get(key) for key in ("source_part", "source_body", "source_collider"))
        occurrence = "/".join((canonical["module_key"], canonical["scene_key"], part or body))
        expected = {"source_part": part, "body_id": body, "collider_id": collider,
                    "source_occurrence": occurrence, "source_revision": source_hash,
                    "role": declaration["kind"], "native_parent": declaration.get("parent"),
                    "geometry_derivation": declaration["geometry"], "frame_derivation": declaration["frame"],
                    "mass_contribution_kg": declaration.get("mass_count_kg", 0),
                    "native_initial_matrix_m": obj["matrix_world"], "native_local_translation_m": obj["location"]}
        for key, value in expected.items():
            check(row[key] == value, name + ": mapping " + key)
        check(obj["properties"]["source_occurrence"] == occurrence, name + ": exact occurrence")
        check(obj["properties"]["helper_role"] == declaration["kind"], name + ": helper role")
        check(obj["rotation_quaternion_wxyz"] == [1, 0, 0, 0], name + ": initial rotation")
        check(obj["scale"] == [1, 1, 1], name + ": initial scale")
        check(obj["matrix_parent_inverse"] == identity, name + ": parent inverse")
        matrix = np.asarray(obj["matrix_world"])
        check(np.array_equal(matrix[:3, :3], np.eye(3)) and np.array_equal(matrix[3], [0, 0, 0, 1]),
              name + ": initial world orientation")
        if declaration["kind"] == "constraint":
            lane = body.split(".")[1]
            car = objects[lane + "_carriage"]
            check(obj["matrix_world"] == car["matrix_world"] and obj["location"] == car["location"],
                  name + ": constraint must use initial carriage frame")
            joint = obj["constraint"]
            check(joint["use_motor_ang"] is False, name + ": angular motor")
            kind = "generic" if name.endswith("_generic") else "motor"
            defaults = backend["inactive_constraint_defaults"][kind]
            if kind == "generic":
                for key, value in defaults.items():
                    check(joint[key] == value, name + ": inactive setting " + key)
            else:
                for axis in "xyz":
                    for coordinate in ("lin", "ang"):
                        check(joint["use_limit_" + coordinate + "_" + axis] is False,
                              name + ": motor has an extra limit")
                        family = "linear" if coordinate == "lin" else "angular"
                        for side in ("lower", "upper"):
                            check(joint["limit_" + coordinate + "_" + axis + "_" + side] == defaults["all_" + family + "_" + side],
                                  name + ": inactive motor bound")
            check(row["native_shape"] is None and not row["native_absent"], name + ": constraint mapping")
        elif declaration["kind"] == "hidden_compound_child":
            car = objects[declaration["parent"]]
            check(obj["matrix_world"] == car["matrix_world"], name + ": helper world frame")
            check(obj["location"] == [0, 0, 0], name + ": helper local frame")
        if collider:
            contact = canonical["colliders"][collider]
            check(row["native_absent"] == (not contact["enabled"]), name + ": collider enablement mapping")
            check(row["native_shape"] == ("BOX" if contact["enabled"] else None), name + ": collider shape mapping")
            check(contact["owner"] == (body or "world"), name + ": collider owner")
        checked.append(name)
    return {"objects_checked": checked, "all_source_and_native_mappings_match": True,
            "exact_constraint_and_helper_frames": True, "inactive_constraint_settings_checked": True,
            "moving_mass_kg": 2}


def check_source_manifest(artifacts, contract):
    manifest = json.loads((artifacts / "source-manifest.json").read_text())
    adopted = json.loads((contract / "CONTRACT-FILES.json").read_text())["files"]
    amendment = contract / "amendments/C191-A1.md"
    expected = adopted + [{"path": "amendments/C191-A1.md", "bytes": amendment.stat().st_size,
                           "sha256": digest(amendment)}]
    check(manifest["dependency_closure"] == expected, "Dependency closure differs from adoption plus amendment")
    for entry in expected:
        path = contract / entry["path"]
        check(path.stat().st_size == entry["bytes"] and digest(path) == entry["sha256"], "Dependency changed: " + entry["path"])
    check(manifest["contract_manifest_sha256"] == digest(contract / "CONTRACT-FILES.json"), "Contract manifest identity")
    check(manifest["canonical_input_sha256"] == digest(artifacts / "canonical-input.json"), "Canonical manifest identity")
    raw = (artifacts / "source.ok").read_bytes()
    source_hash = hashlib.sha256(raw).hexdigest()
    keys = set()
    for occurrence in manifest["occurrences"]:
        check(occurrence["id"] not in keys, "Duplicate source occurrence")
        keys.add(occurrence["id"])
        check(occurrence["occurrence"] == "gauge/slide/" + occurrence["id"], "Incorrect occurrence identity")
        span = occurrence["span"]
        check(span["source_sha256"] == source_hash, "Occurrence source hash")
        literal = raw[span["start_byte"]:span["end_byte"]].decode("utf8")
        check(literal == '"' + occurrence["id"] + '"', "Occurrence span does not name its stable key")
    check(len(keys) == 15, "Source occurrence count")
    return {"dependency_files": len(expected), "source_occurrences": len(keys), "source_sha256": source_hash}


def check_raw_native_pose(artifacts):
    """Measure a direct raw/native pose comparison missing from the first audit.

    Native matrices and encoded quaternions are float32. The numerical rotation
    agreement bound is 32 float32 epsilons for conversion/normalization. It is a
    codec roundoff guard, not a replacement physical or projection tolerance.
    """
    document, binary = decode(artifacts / "raw.glb")
    native = json.loads((artifacts / "native-transforms.json").read_text())
    times = (np.arange(481) / 240).astype("<f4").astype(float)
    raw = states(document, binary, times)
    transform = np.asarray([[1., 0, 0, 0], [0, 0, 1., 0], [0, -1., 0, 0], [0, 0, 0, 1.]])
    roundoff = 32 * np.finfo(np.float32).eps
    results = {}
    for lane in ("left", "right"):
        name = lane + "_carriage"
        matrices = np.asarray([row["matrices_blender_m"][name] for row in native])
        expected = transform @ matrices @ transform.T
        observed = raw[name]["matrix"]
        basis_error = float(np.max(np.abs(expected[:, :3, :3] - observed[:, :3, :3])))
        translation_error = float(np.max(np.abs(expected[:, :3, 3] - observed[:, :3, 3])))
        check(basis_error <= roundoff, name + ": raw rotation is not the native rotation within float32 conversion roundoff")
        check(np.array_equal(expected[:, :3, 3].astype("<f4").astype(float), observed[:, :3, 3]),
              name + ": raw translation is not the native float32 translation")
        results[lane] = {"samples": 481, "maximum_basis_component_error": basis_error,
                         "maximum_translation_component_error_m": translation_error,
                         "raw_translation_equals_native_float32": True}
    return {"lanes": results, "basis_roundoff_bound": float(roundoff), "basis_roundoff_basis": "32 * float32 epsilon",
            "unrecorded_substep_pose_claimed": False}


def run(formal, contract):
    batch = json.loads((formal / "summary.json").read_text())
    backend = json.loads((contract / "backend.json").read_text())
    check(batch["pass"], "Original formal batch did not pass")
    results = []
    for build in batch["builds"]:
        artifacts = Path(build["artifact_directory"])
        reopen = formal / (build["case"] + "-" + str(build["repeat"])) / "reopen"
        result = {"case": build["case"], "repeat": build["repeat"], "pass": False}
        try:
            original = json.loads((artifacts / "native-transforms.json").read_text())
            reopened = json.loads((reopen / "native-transforms.json").read_text())
            check(original == reopened, "Reopened native trace differs from original at a recorded sample")
            canonical = json.loads((artifacts / "canonical-input.json").read_text())
            mapping = json.loads((artifacts / "mapping.json").read_text())
            check(mapping["canonical_input_sha256"] == digest(artifacts / "canonical-input.json"), "Mapping canonical identity")
            result["source"] = check_source_manifest(artifacts, contract)
            configuration = json.loads((reopen / "configuration-before.json").read_text())
            result["configuration"] = check_configuration(configuration, backend, canonical, mapping, result["source"]["source_sha256"])
            result["raw_native_pose"] = check_raw_native_pose(artifacts)
            result["reopened_all_481_native_samples_equal"] = True
            result["pass"] = True
        except (ValueError, OSError, KeyError, TypeError, AssertionError) as error:
            result["failure"] = str(error)
        results.append(result)
    return {"version": "C191-recovery-supplemental-delivery-audit-1", "formal_summary_sha256": digest(formal / "summary.json"),
            "implementation_revision": batch["implementation_revision"], "checker_sha256": digest(__file__),
            "written_after_recovered_candidate_inspection": True, "frozen_thresholds_changed": False,
            "builds": results, "pass": len(results) == 9 and all(row["pass"] for row in results)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.formal.resolve(), args.contract.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"pass": result["pass"], "builds": len(result["builds"]),
                      "failures": [row for row in result["builds"] if not row["pass"]]}, indent=2))
    raise SystemExit(0 if result["pass"] else 1)
