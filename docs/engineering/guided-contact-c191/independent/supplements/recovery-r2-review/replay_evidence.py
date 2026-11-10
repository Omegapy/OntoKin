#!/usr/bin/env python3
"""Read-only offline replay of a relocated C191 formal evidence directory.

Use the original frozen checkers. Original summaries retain their original
absolute paths; a temporary view supplies relocated paths to the recovered-batch
audit. This script never rebuilds or repairs a native scene.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import platform
import sys
import tempfile

HERE = Path(__file__).resolve().parent
INDEPENDENT = HERE.parents[1]
CHECKER = INDEPENDENT / "checker"
sys.path.insert(0, str(CHECKER))
from audit_mapping import audit
from audit_recovered_batch import run as audit_recovered_batch
from measure_c191 import measure
from qualify import run as qualify_controls


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inside(root, relative):
    require(not Path(relative).is_absolute(), "Expected relative artifact path: " + relative)
    path = (root / relative).resolve()
    require(path.is_relative_to(root.resolve()), "Artifact path escapes its directory: " + relative)
    return path


def verify_freezes(contract):
    records = []
    for name, key in (("SEMANTIC-FREEZE.json", "input_manifest"),
                      ("CHECKER-FREEZE.json", "files"), ("SOURCE-FREEZE.json", "files")):
        path = INDEPENDENT / "frozen" / name
        record = json.loads(path.read_text())
        for relative, expected in record[key].items():
            require(digest(inside(INDEPENDENT, relative)) == expected, "Frozen file changed: " + relative)
        records.append({"seal": name, "sha256": digest(path), "entries_verified": len(record[key])})
    manifest = json.loads((INDEPENDENT / "frozen/adopted-contract-hashes.json").read_text())
    for relative, expected in manifest["files"].items():
        require(digest(inside(contract, relative)) == expected, "Adopted contract changed: " + relative)
    approval = json.loads((INDEPENDENT / "supplements/pre-admission-and-lexical/C191-A1-INDEPENDENT-APPROVAL.json").read_text())
    require(digest(contract / "amendments/C191-A1.md") == approval["amendment_sha256"], "Admission amendment changed")
    return {"seals": records, "contract_entries_verified": len(manifest["files"]),
            "admission_amendment_verified": True,
            "historical_C190_result_bytes_replayed": False}


def run(formal, contract):
    seals = verify_freezes(contract)
    summary_path = formal / "summary.json"
    original_summary_bytes = summary_path.read_bytes()
    original = json.loads(original_summary_bytes)
    require(original["pass"] and len(original["builds"]) == 9, "Formal batch did not establish nine passing builds")
    require(digest(formal / "INPUT-LOCK.json") == original["input_lock_sha256"], "Formal input lock changed")
    expected_labels = [f"{case}-{repeat}" for case in "ABCD" for repeat in (1, 2)] + ["E-1"]
    require([f"{row['case']}-{row['repeat']}" for row in original["builds"]] == expected_labels,
            "Formal case/repetition inventory differs")
    relocated = copy.deepcopy(original)
    reports = []
    paths = {}
    native_records = {}
    for original_row, row in zip(original["builds"], relocated["builds"]):
        label = f"{row['case']}-{row['repeat']}"
        directory = formal / label
        store = directory / "store"
        state = json.loads((store / "state.json").read_text())
        artifacts = inside(store, state["artifact_directory"])
        row["artifact_directory"] = str(artifacts)
        paths[label] = artifacts
        require(state["accepted_revision"] == row["source_sha256"], label + ": accepted source identity")
        require(digest(artifacts / "manifest.json") == state["manifest_sha256"], label + ": artifact manifest changed")
        manifest = json.loads((artifacts / "manifest.json").read_text())
        for relative, expected in manifest["files"].items():
            path = inside(artifacts, relative)
            require(path.stat().st_size == expected["bytes"] and digest(path) == expected["sha256"],
                    label + ": manifest artifact changed: " + relative)
        for relative, expected in row["artifacts"].items():
            path = inside(artifacts, relative)
            require(path.stat().st_size == expected["bytes"] and digest(path) == expected["sha256"],
                    label + ": formal artifact changed: " + relative)
        case = "A" if row["case"] == "E" else row["case"]
        fixture = INDEPENDENT / "source-fixtures" / ("E-rename-reorder.ok" if row["case"] == "E" else case + ".ok")
        require((artifacts / "source.ok").read_bytes() == fixture.read_bytes(), label + ": frozen source differs")
        require((artifacts / "canonical-input.json").read_bytes() ==
                (INDEPENDENT / "source-fixtures" / (case + "-canonical.json")).read_bytes(),
                label + ": independently derived canonical input differs")
        require(digest(artifacts / "canonical-input.json") == state["canonical_input_sha256"], label + ": canonical state identity")
        playback = measure(artifacts / "final.glb", case)
        require(playback["pass"], label + ": final playback: " + playback.get("reason", "failure"))
        mapping = audit(artifacts / "raw.glb", artifacts / "final.glb", artifacts / "native-transforms.json")
        require(mapping["passed"], label + ": raw/final mapping failed")
        native = json.loads((artifacts / "native-transforms.json").read_text())
        reopened_path = directory / "reopen/native-transforms.json"
        reopened = json.loads(reopened_path.read_text())
        require(native == reopened and len(native) == 481, label + ": reopened native samples differ")
        require(digest(reopened_path) == original_row["reopen"]["native_trace_sha256"], label + ": reopened trace hash differs")
        reopen_summary = json.loads((directory / "reopen/summary.json").read_text())
        require(reopen_summary["pass"] and reopen_summary["cache_clear_completed"] and
                not reopen_summary["reconstructed_or_repaired"], label + ": saved-scene receipt differs")
        native_records[label] = native
        scene_validation = artifacts / "native-scene-validation.json"
        if scene_validation.is_file():
            scene = json.loads(scene_validation.read_text())
            require(scene["scene_sha256"] == digest(artifacts / "scene.blend") and
                    scene["bytes_checked"] == (artifacts / "scene.blend").stat().st_size,
                    label + ": structural saved-scene receipt differs")
        reports.append({"case": row["case"], "repeat": row["repeat"], "pass": True,
            "manifest_entries_verified": len(manifest["files"]),
            "final_glb_sha256": playback["sha256"], "recording": playback["recording"],
            "clearance": playback["clearance"], "gaps": playback["gaps"], "contact": playback.get("contact"),
            "speeds": playback["speeds"],
            "maximum_continuous_mapping_mm": mapping["maximumContinuousRawToFinalVertexDeviationBoundMm"],
            "maximum_native_sample_mapping_mm": mapping["maximumNativeSampleToFinalVertexDistanceMm"],
            "all_481_reopened_native_samples_equal": True})

    repeats = []
    for case in "ABCD":
        equal = {name: digest(paths[case + "-1"] / name) == digest(paths[case + "-2"] / name)
                 for name in ("canonical-input.json", "final.glb", "raw.glb", "native-transforms.json")}
        require(equal["canonical-input.json"] and equal["final.glb"], case + ": mandatory repeat equality failed")
        repeats.append({"case": case, "equality": equal})
    identity = {name: digest(paths["A-1"] / name) == digest(paths["E-1"] / name)
                for name in ("canonical-input.json", "final.glb")}
    require(all(identity.values()) and digest(paths["A-1"] / "source.ok") != digest(paths["E-1"] / "source.ok"),
            "Rename/reorder control changed physical input/output or lost source identity")
    invariants = ("base", "left_stop", "right_carriage", "right_shoe", "right_stop")
    causal = {name: all(a["matrices_blender_m"][name] == d["matrices_blender_m"][name] and
                       a["bounds_gltf_mm"][name] == d["bounds_gltf_mm"][name]
                       for a, d in zip(native_records["A-1"], native_records["D-1"]))
              for name in invariants}
    require(all(causal.values()), "Disabled collider changed unrelated native trajectories")

    with tempfile.TemporaryDirectory(prefix="c191-relocated-readback-") as temporary:
        view = Path(temporary)
        (view / "summary.json").write_text(json.dumps(relocated, indent=2) + "\n")
        for label in expected_labels:
            (view / label).symlink_to(formal / label, target_is_directory=True)
        recovered = audit_recovered_batch(view, contract)
        require(recovered["pass"], "Recovered source/frame/raw-pose audit failed")
        controls = qualify_controls(view / "analytic-controls")
        require(controls["pass"], "Frozen analytic checker controls failed")
        sealed = json.loads((INDEPENDENT / "frozen/controls-manifest.json").read_text())
        projected = [{key: row[key] for key in sealed[0]} for row in controls["controls"]]
        require(projected == sealed, "Regenerated analytic control bytes differ from sealed manifest")
    require(summary_path.read_bytes() == original_summary_bytes, "Original formal summary was modified")
    return {"version": "C191-R2-portable-independent-evidence-replay-1", "pass": True,
            "implementation_revision": original["implementation_revision"],
            "original_formal_summary_sha256": digest(summary_path),
            "original_absolute_path_summary_unchanged": True,
            "relocation_method": "Resolve immutable artifacts from each copied store state; use a temporary relocated summary and symlinked case directories for the existing recovered-batch audit.",
            "python": platform.python_version(), "checker_sha256": digest(__file__),
            "freeze_verification": seals, "builds": reports, "repeat_checks": repeats,
            "identity": identity, "causal_invariant_parts": causal,
            "recovered_source_frame_raw_pose_audit_pass": recovered["pass"],
            "analytic_controls": {"positive": controls["positive_controls"], "negative": controls["negative_controls"],
                                  "swept_slabs": len(controls["swept_slabs"]), "sealed_bytes_match": True},
            "limits": ["This is offline replay of recorded evidence, not a fresh Blender solve or reopen.",
                       "Khronos, Three.js, visual receiving-application review and legacy compatibility are separate checks.",
                       "No direct Bullet impulse, unrecorded substep, general-contact or production-backend claim."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("Use a new output path; existing evidence is immutable")
    result = run(args.formal.resolve(), args.contract.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"pass": result["pass"], "builds": len(result["builds"]),
                      "original_summary_unchanged": result["original_absolute_path_summary_unchanged"]}, indent=2))
