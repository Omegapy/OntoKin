#!/usr/bin/env python3
"""Rebuild exact submitted sources and independently inspect saved scenes.

Failed author deliveries stay failed. Verification establishes reproducibility
and configuration facts; it does not turn rejected recordings into accepted ones.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


def command(argv, cwd, out, name, timeout=100):
    out.mkdir(parents=True, exist_ok=True)
    record = {"argv": argv, "cwd": str(cwd), "started_unix_s": time.time()}
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=timeout)
    (out / (name + ".stdout.txt")).write_bytes(completed.stdout)
    (out / (name + ".stderr.txt")).write_bytes(completed.stderr)
    record.update(returncode=completed.returncode, elapsed_s=time.time() - record["started_unix_s"])
    (out / (name + ".command.json")).write_text(json.dumps(record, indent=2) + "\n")
    return completed


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--submissions", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--blender", type=Path, required=True)
    a = p.parse_args()
    scope = a.repo / "docs/engineering/contact-comparison-c192"
    from score_submission import score
    rows = json.loads(a.submissions.read_text())
    a.out.mkdir(parents=True, exist_ok=False)
    results = []
    for entry in rows:
        label = entry["id"]
        dest = a.out / label
        original = Path(entry["build"])
        original_score = score(a.repo, original, entry["case"], dest / "submitted-score")
        cases = [("submitted", original_score)]
        if entry.get("rebuild", True):
            delivery = json.loads((original / "delivery.json").read_text())
            rebuild = dest / "rebuild"
            completed = command([sys.executable, "-B", str(scope / "shared/build.py"),
                "--repo", str(a.repo), "--route", delivery["route"], "--source", delivery["source"],
                "--out", str(rebuild), "--blender", str(a.blender)], a.repo, dest, "rebuild")
            assert completed.returncode in (0, 1)
            rebuilt_score = score(a.repo, rebuild, entry["case"], dest / "rebuilt-score")
            for field in ("canonical-input.json", "native-transforms.json", "raw.glb", "final.glb"):
                assert original_score["hashes"][field] == rebuilt_score["hashes"][field], (label, field)
            assert original_score["build_successful"] == rebuilt_score["build_successful"]
            cases.append(("rebuilt", rebuilt_score))
        inspections = []
        for kind, report in cases:
            artifact = Path(report["artifact_directory"])
            source = artifact / ("source.ok" if report["route"] == "ok" else "source.py")
            output = dest / (kind + "-reopen")
            completed = command([str(a.blender), "--factory-startup", "-b", str(artifact / "scene.blend"),
                "-t", "2", "--python-exit-code", "1", "--python", str(scope / "shared/inspect_native_c192.py"),
                "--", "--repo", str(a.repo), "--case", entry["case"], "--contract",
                str(a.repo / "docs/language-design/guided-contact-v0.1"), "--source", str(source),
                "--canonical", str(artifact / "canonical-input.json"), "--out", str(output)],
                a.repo, dest, kind + "-reopen", 80)
            assert completed.returncode == 0, (label, kind, "native reopen failed")
            assert json.loads((artifact / "native-transforms.json").read_text()) == json.loads((output / "native-transforms.json").read_text())
            inspection = json.loads((output / "summary.json").read_text())
            assert inspection["configuration_unchanged"] and not inspection["reconstructed_or_repaired"]
            assert inspection["opened_scene_sha256"] == report["hashes"]["scene.blend"]
            inspections.append({"kind": kind, "all_481_samples_equal": True, "configuration_unchanged": True,
                                "scene_sha256": inspection["opened_scene_sha256"]})
        result = {"id": label, "submitted": original_score, "rebuild_exact": entry.get("rebuild", True),
                  "native_inspections": inspections, "verification_completed": True,
                  "experimental_delivery_pass": original_score["pass"]}
        results.append(result)
        (a.out / "results.json").write_text(json.dumps(results, indent=2) + "\n")
        print(json.dumps({"id": label, "delivery_pass": original_score["pass"], "reopens": len(inspections),
                          "verification_completed": True}), flush=True)


if __name__ == "__main__":
    main()
