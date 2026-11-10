#!/usr/bin/env python3
"""Check recovered C192 bytes after the documented recorded-evidence replay.

This review helper runs no participant, solver, or receiving application. It
supplements the unchanged formal checks; it does not change acceptance gates.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import platform
import struct
import subprocess
import sys
import tarfile

import numpy


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path):
    return {"bytes": path.stat().st_size, "sha256": sha(path)}


def glb(path):
    data = path.read_bytes()
    assert struct.unpack_from("<4sII", data) == (b"glTF", 2, len(data))
    size, kind = struct.unpack_from("<I4s", data, 12)
    assert kind == b"JSON"
    document = json.loads(data[20:20 + size])
    binary_size, kind = struct.unpack_from("<I4s", data, 20 + size)
    assert kind == b"BIN\0" and binary_size == len(data) - 28 - size
    return document, data[28 + size:]


def floats(document, binary, index):
    accessor = document["accessors"][index]
    assert accessor["componentType"] == 5126 and "sparse" not in accessor
    width = {"SCALAR": 1, "VEC3": 3}[accessor["type"]]
    view = document["bufferViews"][accessor["bufferView"]]
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    stride = view.get("byteStride", 4 * width)
    return [struct.unpack_from("<" + "f" * width, binary, start + i * stride)
            for i in range(accessor["count"])]


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def artifact(build):
    found = list(build.rglob("canonical-input.json"))
    assert len(found) == 1, (build, found)
    return found[0].parent


def main():
    if sys.flags.optimize:
        raise RuntimeError("Run verification without Python optimization")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, replay = args.repo.resolve(), args.replay.resolve()
    scope = repo / "docs/engineering/contact-comparison-c192"
    evidence = replay / "evidence"
    results = read(scope / "results.json")
    freeze = read(scope / "frozen/INPUT-FREEZE.json")
    for name, expected in freeze["files"].items():
        assert metadata(repo / name) == expected, name

    archive_record = read(scope / "evidence/archive.json")
    assert metadata(scope / "evidence.tar.xz") == {
        key: archive_record[key] for key in ("bytes", "sha256")}
    manifest = read(evidence / "MANIFEST.json")
    assert sha(evidence / "MANIFEST.json") == archive_record["manifest_sha256"]
    assert len(manifest["files"]) == archive_record["manifest_files"]
    assert sum(row["bytes"] for row in manifest["files"].values()) == archive_record["uncompressed_bytes"]
    for name, expected in manifest["files"].items():
        assert metadata(evidence / name) == expected, name

    phase1 = read(scope / "evidence/phase1-archive.json")
    assert metadata(scope / "phase1-evidence.tar.xz") == {key: phase1[key] for key in ("bytes", "sha256")}
    with tarfile.open(scope / "phase1-evidence.tar.xz") as archive:
        members = archive.getmembers()
        assert len({member.name for member in members}) == len(members)
        assert {member.name for member in members} == set(phase1["files"])
        for member in members:
            assert member.isfile()
            data = archive.extractfile(member).read()
            assert {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()} == phase1["files"][member.name]

    contexts = read(evidence / "CONTEXT.json")["participant_builds"]
    participants, summaries = {}, []
    for entry in contexts:
        build = evidence / entry["build"]
        place = artifact(build)
        delivery = read(build / "delivery.json")
        measured = read(replay / "scores" / entry["id"] / "score.json")
        case, route = entry["case"], delivery["route"]
        assert not delivery["successful"] and delivery["returncode"] == 1
        assert delivery["artifact_directory"] is None
        assert delivery["source_unchanged_during_build"]
        assert measured["source_localization_pass"] and measured["canonical_only_target_field_changed"]
        assert measured["playback_pass"] and not measured["mapping_pass"] and not measured["pass"]
        for key in ("maximum_native_to_final_mm", "maximum_continuous_raw_to_final_mm", "left_travel_mm"):
            assert measured[key] == results["cases"][case][key]
        assert measured["right_gap_mm"] == results["cases"][case]["right_final_clearance_mm"]
        assert measured["mapping_limit_mm"] == results["mapping_limit_mm"] == 0.2
        for name, expected in measured["hashes"].items():
            assert sha(place / name) == expected
        assert sha(place / "final.glb") == entry["final_sha256"]
        source_name = "source.ok" if route == "ok" else "source.py"
        source = scope / ("participants/ok/sources/" + ("01-edit.ok" if case == "edit" else "02-reuse.ok")
                          if route == "ok" else "participants/python/design-" + case + ".py")
        assert (place / source_name).read_bytes() == source.read_bytes()
        assert sha(source) == delivery["source_sha256"] == measured["source_sha256"]
        if route == "ok":
            transaction = read(place.parent / "result.json")
            assert not transaction["committed"] and transaction["accepted_revision"] is None
            assert not transaction["levels"]["exported"] and not transaction["levels"]["destination_validated"]
            assert [row["code"] for row in transaction["diagnostics"]] == ["C191_E_MAPPING"]
        participants[entry["id"]] = place
        summaries.append({"id": entry["id"], "route": route, "case": case,
                          "source_sha256": measured["source_sha256"], "hashes": measured["hashes"],
                          "playback_pass": True, "mapping_pass": False, "accepted": False})

    equal_fields = ("canonical-input.json", "native-transforms.json", "native-trace.csv", "raw.glb", "final.glb")
    equal_pairs = []
    for case in ("edit", "reuse"):
        a, b = participants[f"ok-{case}-build-01"], participants[f"python-{case}-build-01"]
        assert all((a / name).read_bytes() == (b / name).read_bytes() for name in equal_fields)
        equal_pairs.append({"kind": "cross_route", "case": case})
    for route, suffix in (("ok", "edit-regeneration-01"), ("python", "reuse-edit-regeneration-01")):
        a, b = participants[f"{route}-edit-build-01"], participants[f"{route}-{suffix}"]
        source_name = "source.ok" if route == "ok" else "source.py"
        assert all((a / name).read_bytes() == (b / name).read_bytes() for name in (*equal_fields, source_name))
        equal_pairs.append({"kind": "earlier_source_regeneration", "route": route})
    for cohort, case in (("first-reproduction", "edit"), ("reuse-reproduction", "reuse")):
        retained_rows = read(evidence / "c192-audit" / cohort / "results.json")
        for row in retained_rows:
            assert row in results["native_verification"]
            if not row["fresh_rebuild_performed"]:
                assert row["rebuild_exact"] is None
                continue
            assert row["rebuild_exact"] is True
            route = row["submitted"]["route"]
            a = participants[f"{route}-{case}-build-01"]
            b = artifact(evidence / "c192-audit" / cohort / row["id"] / "rebuild")
            source_name = "source.ok" if route == "ok" else "source.py"
            assert all((a / name).read_bytes() == (b / name).read_bytes() for name in (*equal_fields, source_name))
            equal_pairs.append({"kind": "recorded_fresh_rebuild", "route": route, "case": case})

    artifacts = [path.parent for path in evidence.rglob("implementation-manifest.json")]
    implementation_counts, sampler_counts = [], []
    for place in artifacts:
        implementation = read(place / "implementation-manifest.json")
        for name, expected in implementation["files"].items():
            assert metadata(place / "implementation" / name) == expected
            assert expected == freeze["files"]["prototypes/guided_contact_v01/" + name]
        implementation_counts.append(len(implementation["files"]))
        assert sha(place / "backend.json") == freeze["files"]["docs/language-design/guided-contact-v0.1/backend.json"]["sha256"]
        native = read(place / "native-transforms.json")
        assert len(native) == 481
        assert all(row["frame"] == i and row["time_s"] == i / 240 for i, row in enumerate(native))
        raw, raw_binary = glb(place / "raw.glb")
        final, final_binary = glb(place / "final.glb")
        times = [(f32(i / 240),) for i in range(481)]
        sampler_count = 0
        for document, binary in ((raw, raw_binary), (final, final_binary)):
            for sampler in document["animations"][0]["samplers"]:
                assert floats(document, binary, sampler["input"]) == times
                sampler_count += 1
        names = set()
        for channel in raw["animations"][0]["channels"]:
            if channel["target"]["path"] != "translation":
                continue
            name = raw["nodes"][channel["target"]["node"]]["name"]
            output = raw["animations"][0]["samplers"][channel["sampler"]]["output"]
            original = floats(raw, raw_binary, output)
            projected = floats(final, final_binary, output)
            expected = [(f32(row["matrices_blender_m"][name][0][3]),
                         f32(row["matrices_blender_m"][name][2][3]),
                         f32(-row["matrices_blender_m"][name][1][3])) for row in native]
            assert original == expected
            assert [row[0] for row in original] == [row[0] for row in projected]
            names.add(name)
        assert names == {"left_carriage", "right_carriage"}
        sampler_counts.append(sampler_count)

    scenes = {sha(place / "scene.blend"): place for place in artifacts}
    original_root = Path(read(evidence / "CONTEXT.json")["original_workspace"])
    reopens = []
    for path in sorted(evidence.rglob("summary.json")):
        summary = read(path)
        if "opened_scene_sha256" not in summary:
            continue
        original = scenes[summary["opened_scene_sha256"]]
        assert read(path.parent / "native-transforms.json") == read(original / "native-transforms.json")
        assert summary["samples"] == 481 and summary["pass"] and summary["cache_clear_completed"]
        assert summary["configuration_unchanged"] and not summary["reconstructed_or_repaired"]
        assert summary["canonical_input_sha256"] == sha(original / "canonical-input.json")
        source = original / ("source.ok" if (original / "source.ok").exists() else "source.py")
        assert summary["source_sha256"] == sha(source)
        relative = str(path.relative_to(evidence))
        group = "coordinator" if relative.startswith("c192-audit/") else "setup" if relative.startswith("c192-setup/") else "participant_optional"
        command_path = path.parent.with_suffix(".command.json")
        if group == "participant_optional":
            command_path = scope / "participants/ok/evidence/edit/edit-native-reopen-01.command.json"
        command = read(command_path)
        argv = command["argv"]
        opened = Path(argv[argv.index("-b" if "-b" in argv else "--background") + 1])
        assert evidence / opened.relative_to(original_root) == original / "scene.blend"
        assert command["returncode"] == 0 and "--python-exit-code" in argv
        if group != "participant_optional":
            assert "--factory-startup" in argv
        configuration = read(path.parent / "configuration-before.json")
        assert len(configuration["objects"]) == 13
        assert configuration["world"]["fps"] == 240
        assert configuration["world"]["substeps_per_frame"] == 10
        assert configuration["world"]["solver_iterations"] == 100
        assert all(row["action"] is None for row in configuration["objects"].values())
        reopens.append({"path": relative, "group": group, "scene_sha256": summary["opened_scene_sha256"],
                        "equal_sample_rows": 481, "recorded_command_returncode": 0,
                        "saved_configuration_checked": True})
    counts = {group: sum(row["group"] == group for row in reopens)
              for group in ("coordinator", "setup", "participant_optional")}
    assert counts == {"coordinator": 10, "setup": 2, "participant_optional": 1}
    report = {
        "version": "C192-recovery-numerical-verification-1", "pass": True,
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "reviewed_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip(),
        "runtime": {"python": sys.version, "executable": sys.executable, "numpy": numpy.__version__,
                    "platform": platform.platform(), "python_optimization": sys.flags.optimize},
        "command": [sys.executable, "-B", str(Path(__file__).resolve()), "--repo", str(repo),
                    "--replay", str(replay), "--out", str(args.out.resolve())],
        "review_helper_sha256": sha(Path(__file__)),
        "results_sha256": sha(scope / "results.json"),
        "frozen_files_verified": len(freeze["files"]),
        "freeze_sha256": sha(scope / "frozen/INPUT-FREEZE.json"),
        "main_archive": archive_record,
        "phase1_archive": {"sha256": phase1["sha256"], "bytes": phase1["bytes"], "files_verified": len(phase1["files"])},
        "documented_replay": read(replay / "REPLAY-RESULT.json"),
        "cases_recomputed_by_unchanged_formal_checker": results["cases"],
        "participant_scores_verified": summaries,
        "byte_equal_fields": list(equal_fields), "byte_equal_pairs": equal_pairs,
        "source_bytes_also_equal_for_same_route_rebuilds_and_regeneration": True,
        "frozen_implementation_artifacts": len(artifacts),
        "implementation_files_per_artifact": implementation_counts,
        "independent_stdlib_glb_field_decode": {"artifacts": len(artifacts),
            "raw_final_sampler_arrays": sum(sampler_counts), "samples_per_array": 481,
            "raw_native_xyz_equal_at_float32": True, "final_native_carriage_x_equal_at_float32": True,
            "all_native_raw_final_times_equal_at_float32": True},
        "recorded_reopens": reopens, "recorded_reopen_counts": counts,
        "fresh_native_runs": 0, "fresh_receiving_runs": 0, "participant_trials": 0,
        "accepted_deliveries": 0,
        "legacy_driver": {"status": "FAILED", "passed_methods": 4239, "not_run_methods": 13,
                          "freshly_rerun": False, "source": "STATUS.md C191 checkpoint"}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"pass": True, "manifest_files": len(manifest["files"]),
                      "phase1_files": len(phase1["files"]), "artifacts": len(artifacts),
                      "reopen_counts": counts, "accepted_deliveries": 0}))


if __name__ == "__main__":
    main()
