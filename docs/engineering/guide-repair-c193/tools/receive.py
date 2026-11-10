#!/usr/bin/env python3
"""Inspect actual C193 GLBs using the unchanged pinned C191 receiving tools."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tarfile
import time


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def command(label, argv, cwd, out, timeout):
    start = time.monotonic()
    receipt = {"argv": list(map(str, argv)), "cwd": str(cwd), "deadline_s": timeout,
               "started_utc": datetime.now(timezone.utc).isoformat(), "completed": False}
    write(out / "commands" / (label + ".json"), receipt)
    with (out / "commands" / (label + ".stdout.txt")).open("wb") as stdout, \
            (out / "commands" / (label + ".stderr.txt")).open("wb") as stderr:
        process = subprocess.Popen(receipt["argv"], cwd=cwd, stdout=stdout, stderr=stderr,
                                   start_new_session=True)
        try:
            receipt["returncode"] = process.wait(timeout=timeout)
            receipt["completed"] = True
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            receipt["returncode"] = process.returncode
            receipt["timed_out"] = True
    receipt["elapsed_s"] = time.monotonic() - start
    receipt["pass"] = receipt["completed"] and receipt["returncode"] == 0
    write(out / "commands" / (label + ".json"), receipt)
    if not receipt["pass"]:
        raise RuntimeError("Receiving command failed: " + label)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    entries = json.loads(args.manifest.read_text())
    write(out / "input-manifest.json", entries)
    expected_blender = "5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397"
    if digest(args.blender.resolve()) != expected_blender:
        raise RuntimeError("Pinned Blender executable hash differs")
    archive = repo / "docs/engineering/guided-contact-c191/qualification-evidence.tar.xz"
    prefix = "evidence/r2/coordinator/receiving/"
    dependencies = []
    with tarfile.open(archive) as source:
        for member in source.getmembers():
            if not member.isfile() or not (member.name.startswith(prefix + "indexer-view/three/")
                                           or member.name.startswith(prefix + "validator/")):
                continue
            name = member.name[len(prefix):]
            target = out / name
            if not target.resolve().is_relative_to(out):
                raise RuntimeError("Unsafe dependency path")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.extractfile(member).read())
            dependencies.append({"path": name, "bytes": target.stat().st_size, "sha256": digest(target)})
    (out / "tools").mkdir()
    for name in ("validate_glbs.cjs", "three_loader.mjs", "three_readback.mjs", "render_frames.py"):
        source = repo / "docs/engineering/guided-contact-c191/tools" / name
        target = out / "tools" / name
        shutil.copy2(source, target)
        dependencies.append({"path": str(target.relative_to(out)), "bytes": target.stat().st_size,
                             "sha256": digest(target), "unchanged_source": str(source.relative_to(repo))})
    write(out / "dependencies.json", {"archive": str(archive), "sha256": digest(archive),
                                     "files": dependencies})
    paths, playback, identities, render_jobs = [], [], [], []
    for entry in entries:
        identifier = entry["id"]
        if not identifier or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for c in identifier):
            raise ValueError("Unsafe case identifier")
        source = Path(entry["artifact"]).resolve()
        destination = out / "deliveries" / identifier
        destination.mkdir(parents=True, exist_ok=False)
        for name in ("raw.glb", "final.glb"):
            target = destination / name
            shutil.copy2(source / name, target)
            identity = {"path": str(target.relative_to(out)), "source": str(source / name),
                        "sha256": digest(target), "bytes": target.stat().st_size}
            if identity["sha256"] != digest(source / name):
                raise RuntimeError("Receiving copy differs")
            identities.append(identity)
            paths.append(identity["path"])
            playback.append({"id": identifier + "-" + name[:-4], "path": identity["path"],
                             "idealContactS": entry["contact_s"],
                             "expectedLeftFinalGapMm": entry["final_gap_mm"]})
        if entry.get("render", False):
            render_jobs.extend(["--job", identifier, str(destination / "final.glb"), str(entry["contact_s"])])
    write(out / "artifact-identities.json", identities)
    write(out / "glb-list.json", paths)
    write(out / "three-manifest.json", playback)
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node executable unavailable")
    commands = {}
    commands["khronos"] = command("khronos", [node, out / "tools/validate_glbs.cjs",
        out / "validator/package", out, out / "glb-list.json", out / "khronos.json"], repo, out, 120)
    commands["three"] = command("three", [node, "--experimental-loader", out / "tools/three_loader.mjs",
        out / "tools/three_readback.mjs", out, out / "three-manifest.json", out / "three.json"], repo, out, 120)
    if render_jobs:
        commands["blender"] = command("blender", [args.blender.resolve(), "--background", "--factory-startup",
            "--threads", "4", "--python-exit-code", "1", "--python", out / "tools/render_frames.py",
            "--", "--output", out / "renders", *render_jobs], repo, out, 300)
    reports = json.loads((out / "khronos.json").read_text())
    summary = {"pass_for_executed_receiving_checks": True, "visual_review_pending": True,
        "python": sys.version, "platform": platform.platform(), "glb_paths": len(paths),
        "distinct_glb_hashes": len({i["sha256"] for i in identities}),
        "khronos_errors": sum(r["report"]["issues"]["numErrors"] for r in reports.values()),
        "khronos_warnings": sum(r["report"]["issues"]["numWarnings"] for r in reports.values()),
        "khronos_infos": sum(r["report"]["issues"]["numInfos"] for r in reports.values()),
        "three_clips": len(paths), "three_poses": 3 * len(paths), "blender_import_jobs": len(render_jobs) // 4,
        "no_browser_or_gpu_claim": True, "commands": commands}
    write(out / "summary.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "commands"}, indent=2))


if __name__ == "__main__":
    main()
