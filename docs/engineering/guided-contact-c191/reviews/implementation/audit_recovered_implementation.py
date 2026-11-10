"""Read-only C191 recovery audit; no adapter import, native build or mutation.

Checks the actual current files against recorded formal inputs and outputs.
Physical acceptance/continuous geometry is reviewed separately by the fixture
reviewer; this audit establishes source, implementation and native authority
correspondence for the surviving evidence.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import struct
import subprocess
from pathlib import Path


BASE = "405422ba9e3de3b94258feaad742ede356d157f3"
MANIFEST_SHA = "bc85696002d641122322313cf5167f84eb1ae377599930112e3afd0f054b0137"
AMENDMENT_SHA = "c05699cdeec319b8f594c771cba7ef1ec8e7d7a4eb267569873171b8839d791e"
PARTS = ("base", "left_carriage", "left_shoe", "left_stop", "right_carriage", "right_shoe", "right_stop")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def require(value, message):
    if not value:
        raise AssertionError(message)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def tree(repo, revision):
    result = {}
    for row in git(repo, "ls-tree", "-rz", revision).split(b"\0"):
        if row:
            meta, name = row.split(b"\t", 1)
            mode, kind, blob = meta.decode().split()
            result[name.decode()] = {"mode": mode, "kind": kind, "blob": blob}
    return result


def identity(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": digest(path)}


def glb(path):
    raw = path.read_bytes()
    require(struct.unpack_from("<4sII", raw) == (b"glTF", 2, len(raw)), "Invalid GLB header")
    json_size, json_kind = struct.unpack_from("<I4s", raw, 12)
    require(json_kind == b"JSON", "Missing GLB JSON")
    model = json.loads(raw[20:20 + json_size])
    binary_size, binary_kind = struct.unpack_from("<I4s", raw, 20 + json_size)
    binary = raw[28 + json_size:]
    require(binary_kind == b"BIN\0" and len(binary) == binary_size, "Invalid GLB binary")
    return model, binary


def accessor(model, binary, index):
    item = model["accessors"][index]
    require(item["componentType"] == 5126, "Animation accessor not binary32")
    width = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}[item["type"]]
    view = model["bufferViews"][item["bufferView"]]
    start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    stride = view.get("byteStride", 4 * width)
    return [binary[start + stride * i:start + stride * i + 4 * width] for i in range(item["count"])]


def inspect_tracks(artifact, native):
    raw, raw_bin = glb(artifact / "raw.glb")
    final, final_bin = glb(artifact / "final.glb")
    require([n["name"] for n in raw["nodes"]] == list(PARTS), "Visible source IDs changed")
    require(raw["nodes"] == final["nodes"], "Raw/final hierarchy/frame change")
    require(raw["meshes"] == final["meshes"] and raw["materials"] == final["materials"], "Raw/final geometry/material change")
    require(len(raw["animations"]) == len(final["animations"]) == 1, "Animation inventory")
    expected_times = [struct.pack("<f", row["time_s"]) for row in native]
    tracks = {}
    for label, model, binary in (("raw", raw, raw_bin), ("final", final, final_bin)):
        for channel in model["animations"][0]["channels"]:
            sampler = model["animations"][0]["samplers"][channel["sampler"]]
            require(sampler["interpolation"] == "LINEAR", "Interpolation changed")
            times = accessor(model, binary, sampler["input"])
            require(times == expected_times, "Native frame/240 binary32 times changed")
            target = channel["target"]
            name = model["nodes"][target["node"]]["name"]
            tracks[label, name, target["path"]] = accessor(model, binary, sampler["output"])
            if target["path"] == "translation":
                expected_x = [struct.pack("<f", row["matrices_blender_m"][name][0][3]) for row in native]
                require([value[:4] for value in tracks[label, name, "translation"]] == expected_x, "Native X bytes changed")
    for lane in ("left", "right"):
        name = lane + "_carriage"
        require(("raw", name, "translation") in tracks and ("final", name, "translation") in tracks, "Missing carriage X track")
        require(("final", name, "rotation") not in tracks, "Unexpected final rotation")
    return {"native_x_binary32_bytes_exact": True, "native_time_binary32_bytes_exact": True,
            "common_key_count": len(native), "raw_sha256": digest(artifact / "raw.glb"),
            "final_sha256": digest(artifact / "final.glb")}


def inspect_authority(artifact, case, native):
    source = load(artifact / "canonical-input.json")
    result = load(artifact / "native-result.json")
    config = result["configuration"]
    objects, world = config["objects"], config["world"]
    require(len(objects) == 13, "Native object count")
    require(len(world["body_collection"]) == (8 if case == "D" else 9), "Native component count")
    require(world["frame_start"] == 0 and world["frame_end"] == 480 and world["fps"] == 240, "Cadence")
    require(world["fps_base"] == 1 and world["gravity"] == [0, 0, 0], "World units/gravity")
    require(world["substeps_per_frame"] == 10 and world["solver_iterations"] == 100, "Solver step settings")
    require(world["time_scale"] == 1 and world["use_split_impulse"] is True, "Solver world settings")
    roots = [key for key, value in objects.items() if value["rigid_body"] and value["rigid_body"]["type"] == "ACTIVE" and value["parent"] is None]
    require(set(roots) == {"left_carriage", "right_carriage"}, "Independent moving mass authorities")
    require(sum(objects[key]["rigid_body"]["mass"] for key in roots) == 2, "Moving mass count")
    require(config["scene_tags"]["source_sha256"] == digest(artifact / "source.ok"), "Scene source revision")
    require(config["scene_tags"]["canonical_input_sha256"] == digest(artifact / "canonical-input.json"), "Scene canonical input")
    mapping = load(artifact / "mapping.json")
    require(mapping["moving_mass_total_kg"] == sum(row["mass_contribution_kg"] for row in mapping["rows"]) == 2, "Mapping double-counts mass")
    for key, obj in objects.items():
        require(not obj["has_action"], "Unexpected transform action")
        if obj["rigid_body"]:
            rb = obj["rigid_body"]
            require(all(rb[field] == 0 for field in ("friction", "restitution", "linear_damping", "angular_damping", "collision_margin")), "Native contact law")
            require(rb["collision_collections"] == [True] + [False] * 19, "Native filter")
            require(not rb["kinematic"] and not rb["use_deactivation"], "Kinematic/deactivation")
    for lane, speed in (("left", 125), ("right", 150)):
        car = objects[lane + "_carriage"]
        shoe = objects[lane + "_shoe"]
        proxy = objects["_" + lane + "_carriage_collision"]
        require(car["rigid_body"]["collision_shape"] == "COMPOUND" and car["rigid_body"]["mass"] == 1, "Mass owner")
        require(shoe["parent"] == proxy["parent"] == lane + "_carriage", "Compound ownership")
        require(not car["drivers"] and not shoe["drivers"] and not proxy["drivers"], "Competing transform driver")
        require(proxy["mesh_vertices"] == car["mesh_vertices"] and proxy["location"] == [0, 0, 0], "Undeclared helper geometry/frame")
        require(car["properties"]["motion_authority"] == "solver" and car["properties"]["speed_mm_s"] == speed, "Motion authority")
        require((shoe["rigid_body"] is None) == (case == "D" and lane == "left"), "Disabled collider representation")
        guide = objects["_" + lane + "_generic"]["constraint"]
        motor_object = objects["_" + lane + "_motor"]
        motor = motor_object["constraint"]
        require(not guide["use_limit_lin_x"], "Timed/distance X stop")
        for axis in "yz":
            require(guide["use_limit_lin_" + axis] and guide["limit_lin_" + axis + "_lower"] == guide["limit_lin_" + axis + "_upper"] == 0, "Transverse guide")
        for axis in "xyz":
            require(guide["use_limit_ang_" + axis] and guide["limit_ang_" + axis + "_lower"] == guide["limit_ang_" + axis + "_upper"] == 0, "Rotation guide")
        for constraint in (guide, motor):
            require(constraint["object1"] == "base" and constraint["object2"] == lane + "_carriage", "Constraint ordering")
            require(constraint["disable_collisions"] and constraint["solver_iterations"] == 100, "Constraint configuration")
        require(motor["use_motor_lin"] and not motor["use_motor_ang"] and motor["motor_lin_max_impulse"] == 100000, "Motor bounds")
        require(abs(motor["motor_lin_target_velocity"] + speed / 1000) < 1e-7, "Source-to-motor target")
        driver, = motor_object["drivers"]
        variable, = driver["variables"]
        require(driver["expression"] == "-speed_mm_s / 1000.0", "Motor schedule")
        require(variable["target_id"] == lane + "_carriage" and variable["data_path"] == '["speed_mm_s"]', "Motor source ownership")
        x = [row["matrices_blender_m"][lane + "_carriage"][0][3] for row in native]
        require(abs((x[1] - x[0]) * 240000 - speed) < .5, "First interval source feed")
    return {"moving_mass_kg": 2, "native_objects": len(objects), "native_components": len(world["body_collection"]),
            "one_solver_authority_per_lane": True, "source_owned_motor_targets_verified": True,
            "hidden_geometry_declared_and_derived": True, "left_shoe_collider_enabled": case != "D"}


def run(repo, formal):
    head = git(repo, "rev-parse", "HEAD").decode().strip()
    old, current = tree(repo, BASE), tree(repo, head)
    differences = [key for key, value in old.items() if current.get(key) != value]
    require(not differences, "An inherited file changed: " + repr(differences))
    contract = repo / "docs/language-design/guided-contact-v0.1"
    require(digest(contract / "CONTRACT-FILES.json") == MANIFEST_SHA, "Adopted manifest changed")
    for row in load(contract / "CONTRACT-FILES.json")["files"]:
        path = contract / row["path"]
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "Adopted contract changed")
    require(digest(contract / "amendments/C191-A1.md") == AMENDMENT_SHA, "Amendment changed")
    summary = load(formal / "summary.json")
    require(summary["pass"] and len(summary["builds"]) == 9 and not summary["failures"], "Formal result not passing")
    package = repo / "prototypes/guided_contact_v01"
    current_code = {path.name: identity(path) for path in sorted(package.glob("*.py"))}
    reports = []
    natives = {}
    for row in summary["builds"]:
        label = f'{row["case"]}-{row["repeat"]}'
        directory = formal / label
        state = load(directory / "store/state.json")
        artifact = directory / "store" / state["artifact_directory"]
        require(artifact.resolve().is_relative_to((directory / "store").resolve()), "Store escape")
        require(digest(artifact / "manifest.json") == state["manifest_sha256"], "Artifact manifest changed")
        manifest = load(artifact / "manifest.json")
        for relative, expected in manifest["files"].items():
            path = artifact / relative
            require(path.resolve().is_relative_to(artifact.resolve()), "Artifact escape")
            require(path.stat().st_size == expected["bytes"] and digest(path) == expected["sha256"], "Artifact changed: " + relative)
        implementation = load(artifact / "implementation-manifest.json")
        require(set(implementation["files"]) == set(current_code), "Runtime inventory changed")
        for name, expected in implementation["files"].items():
            require(expected["bytes"] == current_code[name]["bytes"] and expected["sha256"] == current_code[name]["sha256"], "Executed/current runtime differs: " + name)
            require(digest(artifact / "implementation" / name) == expected["sha256"], "Retained runtime differs")
        require(implementation["worktree_status"] == "", "Dirty formal implementation")
        attempt = load(artifact / "attempt-context.json")
        command = load(artifact / "native-command.json")
        require(attempt["formal_native_qualification_run"] and not attempt["trusted_host_test_hooks"] and attempt["reopen_input"] is None, "Nonformal build substituted")
        require(not command["trusted_test_hooks"] and command["returncode"] == 0 and command["stop_reason"] is None, "Native failed/test process")
        require("--factory-startup" in command["argv"] and command["argv"][command["argv"].index("--python") + 1].endswith("/implementation/native_worker.py"), "Native executed different worker")
        native = load(artifact / "native-transforms.json")
        require(len(native) == 481 and all(value["frame"] == index and value["time_s"] == index / 240 for index, value in enumerate(native)), "Frame/time capture mismatch")
        require(native == load(artifact / "native-result.json")["samples"], "Trace/native envelope differ")
        reopened = load(directory / "reopen/native-transforms.json")
        require(native == reopened, "Independent reopened solve differs")
        receipt = load(directory / "reopen/summary.json")
        require(receipt["pass"] and receipt["cache_clear_completed"] and not receipt["reconstructed_or_repaired"], "Invalid reopen receipt")
        require(receipt["opened_scene_sha256"] == digest(artifact / "scene.blend"), "Wrong scene reopened")
        require(digest(directory / "reopen/native-transforms.json") == row["reopen"]["native_trace_sha256"], "Reopen trace changed")
        case = "A" if row["case"] == "E" else row["case"]
        authority = inspect_authority(artifact, case, native)
        tracks = inspect_tracks(artifact, native)
        natives[label] = native
        reports.append({"case": row["case"], "repeat": row["repeat"], "artifact_directory": str(artifact),
                        "manifest_files_verified": len(manifest["files"]), "executed_runtime_files_equal_current": len(current_code),
                        "independent_reopened_samples_equal": True, "authority": authority, "tracks": tracks,
                        "pass": True})
    invariants = ("base", "left_stop", "right_carriage", "right_shoe", "right_stop")
    require(all(a["matrices_blender_m"][key] == d["matrices_blender_m"][key]
                and a["bounds_gltf_mm"][key] == d["bounds_gltf_mm"][key]
                for a, d in zip(natives["A-1"], natives["D-1"]) for key in invariants), "Disabled control changed unrelated native motion")
    engineering = repo / "docs/engineering/guided-contact-c191"
    qualification = load(engineering / "evidence/native-qualification.json")
    archive_checks = []
    for row in qualification["archives"]:
        path = engineering / row["file"]
        require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "Archived evidence changed")
        archive_checks.append(identity(path))
    return {"schema": "c191-r3-author-implementation-audit/0.1", "pass": True,
            "completed_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "reviewed_head": head, "reviewed_tree": git(repo, "rev-parse", "HEAD^{tree}").decode().strip(),
            "historical_base": BASE, "inherited_paths_verified": len(old), "inherited_blob_or_mode_changes": differences,
            "added_paths": len(set(current) - set(old)), "contract_manifest_sha256": MANIFEST_SHA,
            "admission_amendment_sha256": AMENDMENT_SHA, "runtime_files": current_code,
            "formal_summary": identity(formal / "summary.json"), "formal_builds": reports,
            "causal_control_unrelated_native_parts_equal": list(invariants), "evidence_archives": archive_checks,
            "method": "Read-only actual byte/hash review and independent standard-library trace/configuration/GLB X-time correspondence. No adapter import, build, native solve, or source/evidence change.",
            "limits": ["Physical tolerance and continuous interval certification remain the independent fixture review's responsibility.",
                       "This rechecks preserved native evidence; it is not a newly executed Blender solve or saved-scene replay.",
                       "Development integration, exact main verification and complete legacy cohort failure accounting remain the coordinator's responsibility."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), "Use a new immutable output path")
    result = run(args.repo.resolve(), args.formal.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"pass": result["pass"], "reviewed_head": result["reviewed_head"],
                      "inherited_paths_verified": result["inherited_paths_verified"],
                      "builds": len(result["formal_builds"]), "runtime_files_per_build": len(result["runtime_files"]),
                      "output_sha256": digest(args.out)}, indent=2))
