#!/usr/bin/env python3
"""Recheck C193 evidence offline, or explicitly run independent saved-scene replays.

Default mode never starts Blender. --blender explicitly requests the fourteen
fresh saved-scene resimulations; --formal and --replays accept directories or
their retained tar archives. Every output directory must be new.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time

from check_artifact import HERE, REPO, digest, require, review, verify_frozen
from audit_provenance import audit as provenance_audit


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def verify_review_freezes(repo):
    receipts = {}
    for name in ("CHECKER-FREEZE.json", "SUPPLEMENTAL-REVIEW-FREEZE.json"):
        document = json.loads((HERE / "frozen" / name).read_text())
        for row in document.get("files", document.get("review_files", [])):
            path = HERE / row["path"]
            require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "Independent frozen file differs: " + row["path"])
        for row in document.get("lifecycle_review", {}).get("files", []):
            path = repo / row["path_from_repo"]
            require(path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], "Lifecycle frozen file differs")
        receipts[name] = digest(HERE / "frozen" / name)
    return receipts


def materialize(path, temporary, marker):
    if path.is_dir():
        root = path
    else:
        root = temporary / path.name.replace(".", "_")
        root.mkdir()
        with tarfile.open(path) as archive:
            archive.extractall(root, filter="data")
    if marker == "reopens" and (root / "reopens").is_dir():
        return root / "reopens"
    matches = list(root.rglob(marker))
    require(len(matches) == 1, "Expected one " + marker + " in evidence input")
    return matches[0] if marker == "reopens" else matches[0].parent


def artifact_for(formal, row):
    run = formal / row["id"]
    if row["route"] == "python":
        artifact = run / "artifact"
    else:
        state = json.loads((run / "store/state.json").read_text())
        require(state["schema"] == "ontokin.c193.store/0.1", "Wrong accepted store namespace")
        artifact = run / "store" / state["artifact_directory"]
        require(artifact.resolve().is_relative_to((run / "store").resolve()), "Store artifact escaped its root")
        require(state["manifest_sha256"] == digest(artifact / "manifest.json"), "Accepted store manifest differs")
    require(artifact.is_dir(), "Missing formal artifact: " + row["id"])
    return artifact


def reopen(artifact, row, destination, blender, contract):
    script = HERE / "inspect_scene.py"
    source = artifact / ("source.py" if row["route"] == "python" else "source.ok")
    command = [str(blender), "--factory-startup", "-b", str(artifact / "scene.blend"), "-t", "2",
        "--python-exit-code", "1", "--python", str(script), "--", "--out", str(destination),
        "--backend", str(contract / "backend.json"), "--backend-sha256", digest(contract / "backend.json"),
        "--source-binding", "c193-experimental-0.1", "--source", str(source),
        "--canonical", str(artifact / "canonical-input.json"), "--case", row["case"], "--guide-frame", "carriage_center"]
    started = time.time()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        completed = subprocess.run(command, cwd=REPO, capture_output=True, timeout=80)
    except subprocess.TimeoutExpired as error:
        (destination.parent / (row["id"] + ".stdout.txt")).write_bytes(error.stdout or b"")
        (destination.parent / (row["id"] + ".stderr.txt")).write_bytes(error.stderr or b"")
        save(destination.parent / (row["id"] + ".command.json"), {"argv": command, "cwd": str(REPO),
            "started_unix_s": started, "elapsed_s": time.time() - started, "timed_out": True,
            "inspector_sha256": digest(script), "scene_sha256": digest(artifact / "scene.blend"),
            "blender_sha256": digest(blender), "deadline_s": 80})
        raise
    (destination.parent / (row["id"] + ".stdout.txt")).write_bytes(completed.stdout)
    (destination.parent / (row["id"] + ".stderr.txt")).write_bytes(completed.stderr)
    save(destination.parent / (row["id"] + ".command.json"), {"argv": command, "cwd": str(REPO),
        "started_unix_s": started, "elapsed_s": time.time() - started, "returncode": completed.returncode,
        "inspector_sha256": digest(script), "scene_sha256": digest(artifact / "scene.blend"),
        "blender_sha256": digest(blender), "deadline_s": 80})
    require(completed.returncode == 0, "Independent saved-scene replay failed: " + row["id"])


def execute(formal, replays, out, contract, candidate_review, blender, candidate_repo):
    initial = verify_frozen(candidate_repo)
    freezes = verify_review_freezes(candidate_repo)
    plan = json.loads((HERE / "frozen/QUALIFICATION-PLAN.json").read_text())
    approval = json.loads(candidate_review.read_text())
    manifest = json.loads((formal / "formal-builds.json").read_text())
    rows = manifest["runs"]
    require(manifest["all_builds_self_checked"] and all(r["build_successful"] for r in rows), "A formal build failed")
    require(len(rows) == manifest["planned_builds"] == plan["fresh_build_count"] == 14, "Formal build matrix count")
    required = sorted((r["case"], r["route"]) for r in plan["formal_builds"])
    require(sorted((r["case"], r["route"]) for r in rows) == required, "Formal case/route matrix differs")
    require(len({r["id"] for r in rows}) == 14, "Duplicate formal run identity")
    require(manifest["contract_manifest_sha256"] == approval["contract_manifest_sha256"], "Formal contract differs")
    require(manifest["backend_sha256"] == approval["backend_sha256"], "Formal backend differs")
    require(manifest["implementation_revision"] == approval["candidate_revision"], "Formal candidate revision differs")
    require(manifest["adoption_sha256"] == digest(formal / "adoption-receipt.md") ==
            "43914daa1d93ed8f5bad4645909b4af2ff14a0b44558c6dacf6ceb71ddb5fb69", "Retained adoption differs")
    require(manifest["input_lock_sha256"] == digest(formal / "INPUT-LOCK.json"), "Formal input lock differs")
    lock = json.loads((formal / "INPUT-LOCK.json").read_text())
    require(lock["implementation_revision"] == approval["candidate_revision"] and
            lock["adoption_sha256"] == manifest["adoption_sha256"], "Input lock revision/adoption differs")
    for name, item in lock["files"].items():
        path = candidate_repo / name
        require(path.stat().st_size == item["bytes"] and digest(path) == item["sha256"], "Formal locked source changed: " + name)
    if blender:
        require(digest(blender) == "5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397", "Wrong Blender executable")
    baseline_archive = candidate_repo / "docs/engineering/contact-comparison-c192/evidence.tar.xz"
    baseline_member = "c192-runs/python/reuse-build-01/artifact/native-transforms.json"
    with tarfile.open(baseline_archive) as archive:
        baseline_bytes = archive.extractfile(baseline_member).read()
    baseline = json.loads(baseline_bytes)
    results, originals = [], {}
    fresh_attempts = 0
    for row in rows:
        record = {"id": row["id"], "case": row["case"], "route": row["route"], "passed": False}
        folder = out / "reports" / row["id"]
        folder.mkdir(parents=True)
        try:
            artifact = artifact_for(formal, row)
            record["artifact_from_formal"] = str(artifact.relative_to(formal))
            for name, item in row["artifacts"].items():
                require(digest(artifact / name) == item["sha256"], "Formal recorded artifact hash differs: " + name)
            numerical = review(artifact, row["case"], contract / "backend.json", approval["backend_sha256"], "c193-experimental-0.1")
            save(folder / "numerical.json", numerical)
            require(numerical["passed"], "Independent numerical gate failed")
            provenance = provenance_audit(artifact, contract, candidate_review)
            save(folder / "provenance.json", provenance)
            require(provenance["passed"], "Independent provenance gate failed")
            expected_source = next(s for s in approval["source_rows"] if s["case"] == row["case"])
            expected_sha = expected_source["source_sha256" if row["route"] == "ok" else "direct_source_sha256"]
            require(provenance["source_sha256"] == row["source_sha256"] == expected_sha, "Formal authoring source differs from reviewed example")
            replay_dir = replays / row["id"]
            if blender:
                fresh_attempts += 1
                reopen(artifact, row, replay_dir, blender, contract)
            summary = json.loads((replay_dir / "summary.json").read_text())
            require(summary["pass"] and summary["cache_clear_completed"] and summary["configuration_unchanged"], "Replay receipt did not pass")
            require(not summary["reconstructed_or_repaired"], "Replay reconstructed or repaired the scene")
            require(summary["opened_scene_sha256"] == digest(artifact / "scene.blend"), "Replay used another scene")
            require(summary["inspector_sha256"] == digest(HERE / "inspect_scene.py"), "Replay used another inspector")
            require(summary["source_sha256"] == provenance["source_sha256"], "Replay used another source")
            require(summary["canonical_input_sha256"] == provenance["canonical_input_sha256"], "Replay canonical input differs")
            require(summary["backend_sha256"] == approval["backend_sha256"], "Replay backend differs")
            original = json.loads((artifact / "native-transforms.json").read_text())
            again = json.loads((replay_dir / "native-transforms.json").read_text())
            require(len(original) == len(again) == 481 and original == again, "Reopened native sample sequence differs")
            originals[row["id"]] = original
            mapping = numerical["mapping_measurements"]
            record.update(passed=True, artifacts={n: digest(artifact / n) for n in ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb", "scene.blend")},
                native_sample_max_mm=mapping["maximumNativeSampleToFinalVertexDistanceMm"],
                raw_sample_max_mm=mapping["maximumRecordedVertexDistanceMm"],
                continuous_mapping_bound_mm=mapping["maximumContinuousRawToFinalVertexDeviationBoundMm"],
                left_final_travel_mm=numerical["playback"]["parts"]["left_carriage"]["final_displacement_mm"][0],
                left_max_penetration_mm=numerical["playback"]["gaps"]["left"]["max_near_face_penetration_mm"],
                right_final_gap_mm=numerical["playback"]["gaps"]["right"]["final_mm"],
                replay_all_481_samples_identical=True, replay_trace_sha256=digest(replay_dir / "native-transforms.json"),
                replay_scene_sha256=summary["opened_scene_sha256"], replay_summary_sha256=digest(replay_dir / "summary.json"),
                replay_configuration_sha256=digest(replay_dir / "configuration-before.json"))
        except Exception as error:
            record["failure"] = type(error).__name__ + ": " + str(error)
        results.append(record)
        save(out / "progress.json", {"runs": results})
        print(json.dumps({"id": row["id"], "passed": record["passed"], "failure": record.get("failure")}), flush=True)
    passed = all(r["passed"] for r in results)
    equality = []
    invariant = {}
    if passed:
        for case in "ABCDEF":
            cohort = [r for r in results if r["case"] == case]
            hashes = {name: len({r["artifacts"][name] for r in cohort}) == 1 for name in
                      ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb")}
            equality.append({"case": case, "runs": [r["id"] for r in cohort], "equal": hashes, "passed": all(hashes.values())})
        for record in results:
            trace = originals[record["id"]]
            same = {name: all(a["matrices_blender_m"][name] == b["matrices_blender_m"][name]
                             and a["bounds_gltf_mm"][name] == b["bounds_gltf_mm"][name] for a, b in zip(baseline, trace))
                    for name in ("base", "right_carriage", "right_shoe", "right_stop")}
            invariant[record["id"]] = same
        passed = all(r["passed"] for r in equality) and all(all(row.values()) for row in invariant.values())
    result = {"version": "C193-independent-formal-evidence-review-1", "passed": passed, "runs": results,
        "formal_build_count": len(rows), "retained_native_replay_count": sum(r["passed"] for r in results),
        "fresh_saved_scene_resimulations": fresh_attempts, "fresh_native_constructions": 0,
        "mode": "fresh saved-scene replay and artifact audit" if blender else "recorded-only; no Blender execution",
        "repeat_and_route_equality": equality, "unrelated_native_parts_identical_across_all_runs": invariant,
        "unrelated_parts_baseline": {"archive_from_repo": str(baseline_archive.relative_to(candidate_repo)),
            "archive_sha256": digest(baseline_archive), "member": baseline_member,
            "member_sha256": hashlib.sha256(baseline_bytes).hexdigest(), "sample_count": len(baseline)},
        "frozen_inputs": initial, "review_freezes": freezes, "formal_manifest_sha256": digest(formal / "formal-builds.json"),
        "candidate_review_sha256": digest(candidate_review), "driver_sha256": digest(__file__),
        "maximum_native_sample_mm": max((r.get("native_sample_max_mm", 0) for r in results), default=0),
        "maximum_continuous_mapping_mm": max((r.get("continuous_mapping_bound_mm", 0) for r in results), default=0),
        "receiving_and_lifecycle": "Separate mandatory evidence; this numerical/native audit does not substitute for those roles."}
    save(out / "summary.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formal", type=Path, required=True)
    parser.add_argument("--replays", type=Path, default=HERE / "qualification-evidence.tar.xz")
    parser.add_argument("--contract", type=Path, default=REPO / "docs/language-design/guided-contact-v0.2")
    parser.add_argument("--candidate-repo", type=Path, default=REPO)
    parser.add_argument("--candidate-review", type=Path, default=HERE / "evidence/candidate-review.json")
    parser.add_argument("--blender", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="c193-recorded-replay-") as temporary:
        temporary = Path(temporary)
        formal = materialize(args.formal, temporary, "formal-builds.json")
        replays = args.out / "reopens" if args.blender else materialize(args.replays, temporary, "reopens")
        if args.blender:
            replays.mkdir()
        report = execute(formal, replays, args.out, args.contract, args.candidate_review, args.blender, args.candidate_repo)
    print(json.dumps({"passed": report["passed"], "runs": report["formal_build_count"],
        "fresh_resimulations": report["fresh_saved_scene_resimulations"], "evidence": str(args.out / "summary.json")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
