#!/usr/bin/env python3
"""Replay C192 recorded evidence without running a fresh Blender simulation."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--archive", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    extracted = a.out / "evidence"
    extracted.mkdir()
    with tarfile.open(a.archive) as archive:
        members = archive.getmembers()
        assert len({m.name for m in members}) == len(members)
        for member in members:
            name = PurePosixPath(member.name)
            assert member.isfile() and not name.is_absolute() and ".." not in name.parts and "\\" not in member.name
        manifest = json.load(archive.extractfile("MANIFEST.json"))
        assert {m.name for m in members} == set(manifest["files"]) | {"MANIFEST.json"}
        archive.extractall(extracted, filter="data")
    for name, expected in manifest["files"].items():
        path = extracted / name
        assert path.stat().st_size == expected["bytes"] and digest(path) == expected["sha256"], name

    scope = a.repo / "docs/engineering/contact-comparison-c192"
    sys.path.insert(0, str(scope / "tools"))
    from score_submission import score
    context = json.loads((extracted / "CONTEXT.json").read_text())
    scores = []
    for entry in context["participant_builds"]:
        row = score(a.repo, extracted / entry["build"], entry["case"], a.out / "scores" / entry["id"])
        assert row["pass"] is False and row["build_successful"] is False
        assert row["playback_pass"] is True and row["mapping_pass"] is False
        assert row["maximum_native_to_final_mm"] > .2
        assert row["hashes"]["final.glb"] == entry["final_sha256"]
        scores.append(row)

    sys.path.insert(0, str(scope / "shared"))
    from check_delivery import load
    measure, _ = load(a.repo)
    import make_controls
    targets = json.loads((scope / "frozen/targets.json").read_text())["cases"]
    make_controls.STOPS.update({row["id"]: row["left_stop_near_face_mm"] for row in targets})
    controls = json.loads((extracted / "c192-setup/controls/results.json").read_text())
    for control in controls:
        path = extracted / "c192-setup/controls" / (control["case"] + "-" + control["fault"] + ".glb")
        assert path.read_bytes() == make_controls.build(control["case"], control["fault"])
        measured = measure.measure(path, control["case"])
        assert measured["pass"] == control["expected_pass"] == control["pass"]

    # These receipts establish recorded equality, not a new native simulation.
    scenes = {digest(path): path for path in extracted.rglob("scene.blend")}
    reopens = []
    for summary_path in extracted.rglob("summary.json"):
        summary = json.loads(summary_path.read_text())
        if "opened_scene_sha256" not in summary:
            continue
        scene = scenes[summary["opened_scene_sha256"]]
        original = json.loads((scene.parent / "native-transforms.json").read_text())
        reopened = json.loads((summary_path.parent / "native-transforms.json").read_text())
        assert len(original) == len(reopened) == 481 and original == reopened
        assert summary["configuration_unchanged"] and not summary["reconstructed_or_repaired"]
        reopens.append(str(summary_path.relative_to(extracted)))

    for cohort in ("first-reproduction", "reuse-reproduction"):
        rows = json.loads((extracted / "c192-audit" / cohort / "results.json").read_text())
        for row in rows:
            if not row["fresh_rebuild_performed"]:
                assert row["rebuild_exact"] is None
                continue
            directory = extracted / "c192-audit" / cohort / row["id"]
            one = json.loads((directory / "submitted-score/score.json").read_text())
            two = json.loads((directory / "rebuilt-score/score.json").read_text())
            for name in ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb"):
                assert one["hashes"][name] == two["hashes"][name]
    for route in ("ok", "python"):
        edits = [row for row in scores if row["route"] == route and row["case"] == "edit"]
        assert len(edits) == 2
        for name in ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb"):
            assert edits[0]["hashes"][name] == edits[1]["hashes"][name]
    report = {"recorded_evidence_replay_pass": True, "experimental_deliveries_accepted": 0,
              "participant_builds_rechecked": len(scores), "analytic_controls_rechecked": len(controls),
              "recorded_reopen_receipts_rechecked": len(reopens), "manifest_files": len(manifest["files"]),
              "fresh_native_runs": 0, "archive_sha256": digest(a.archive),
              "scope": "Inventory, unchanged playback/mapping gates, controls and recorded native equality; no fresh solver or receiving-application execution"}
    (a.out / "REPLAY-RESULT.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
