#!/usr/bin/env python3
"""Reproduce one explicitly synthetic C215 CPU workflow, never a native attempt."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import platform
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
spec = importlib.util.spec_from_file_location("_c215_adapter_proof", HERE / "adapter.py")
assert spec is not None and spec.loader is not None
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def descriptor(data: bytes) -> dict:
    return {"bytes": len(data), "sha256": adapter.digest(data)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = ROOT / "docs" / "engineering" / "semantic-export-c210" / "evidence" / "proof"
    glb = (inputs / "after.glb").read_bytes()
    bundle = (inputs / "after.program.bundle.json").read_bytes()
    semantic = (inputs / "after.semantic.json").read_bytes()
    payload = adapter.source.build_payload(glb, bundle, semantic)
    importer = b"C215 synthetic importer fixture: no installed importer or native execution\n"
    artifacts = {
        "receiver_source": b"C215 synthetic receiver fixture: no executable receiver or native execution\n",
        "importer_source": importer,
        "build_record": adapter.canonical_bytes({"application": "Blender", "version": [0, 0, 0],
            "executableSha256": adapter.digest(b"synthetic-executable-placeholder"),
            "buildHash": "SYNTHETIC_NOT_AN_INSTALLED_BUILD", "importerSourceSha256": adapter.digest(importer)}),
        "import_settings": adapter.canonical_bytes({"synthetic": True, "capture": "explicit-corner-directions"}),
        "scene": None,
    }
    lock = {"schema_version": adapter.LOCK_SCHEMA, "profile": adapter.PROFILE,
            "sourcePayloadSha256": adapter.digest(adapter.canonical_bytes(payload)),
            "sourceInputs": adapter.source.ACCEPTED_INPUTS, "receiverRevision": "0" * 40,
            "receiverDisposition": "synthetic-fixture",
            "artifacts": {name: descriptor(data) if data is not None else None for name, data in artifacts.items()}}
    by_triangle = {}
    for corner in payload["corners"]:
        by_triangle.setdefault(tuple(corner["key"][:3]), []).append(corner)
    objects = []
    for instance in reversed(payload["instances"]):
        triangles = []
        for ordinal, (key, corners) in enumerate(by_triangle.items()):
            if key[0] != instance["mesh"]:
                continue
            rotation = (ordinal % 3, (ordinal + 1) % 3, (ordinal + 2) % 3)
            positions, normals = [], []
            for corner_index in rotation:
                corner = corners[corner_index]
                x, y, z = struct.unpack("<3f", bytes.fromhex(corner["position_f32le"]))
                positions.append([x, -z, y])
                x, y, z = struct.unpack("<3f", bytes.fromhex(corner["normal_f32le"]))
                normals.append([x, -z, y])
            triangles.append({"nativeTriangle": 100000 - ordinal * 7,
                              "loops": [5000 + ordinal * 3 + corner for corner in range(3)],
                              "positions": positions, "normals": normals})
        objects.append({"nativeObject": "synthetic-object-" + str(instance["node"]),
                        "nativeMesh": "synthetic-mesh-" + str(instance["mesh"]),
                        "sourceNode": instance["node"], "sourceMesh": instance["mesh"],
                        "sourcePath": instance["path"], "elementId": instance["element_id"],
                        "triangles": list(reversed(triangles))})
    observations = {"schema_version": adapter.OBSERVATIONS_SCHEMA, "profile": adapter.PROFILE,
                    "kind": "synthetic-cpu", "inputLockSha256": adapter.digest(adapter.canonical_bytes(lock)),
                    "sourcePayloadSha256": lock["sourcePayloadSha256"], "frame": adapter.NATIVE_FRAME,
                    "phase": "synthetic", "producer": "C215 synthetic workflow; not a native capture", "objects": objects}
    report = adapter.build_report(payload, observations, glb, bundle, semantic, input_lock=lock, artifacts=artifacts)
    expected = sum(len(corners) for instance in payload["instances"] for key, corners in by_triangle.items() if key[0] == instance["mesh"])
    checks = [
        {"id": "P01", "topic": "Complete reordered and cyclic synthetic geometry maps", "passed": report["summary"]["observed"] == expected == 23400},
        {"id": "P02", "topic": "Exact synthetic directions have zero component and angular difference",
         "passed": report["summary"]["maximumComponentDifference"] == report["summary"]["maximumAngularDifferenceDegrees"] == 0.0},
        {"id": "P03", "topic": "Full denominator has no missing, ambiguous or invalid synthetic corners",
         "passed": all(report["summary"][name] == 0 for name in ("missing", "ambiguous", "invalid")) and report["nativeDiagnostics"] == []},
        {"id": "P04", "topic": "Exact synthetic copies establish no native provenance or receiving acceptance",
         "passed": all(report[name] is False for name in ("nativeFidelityEstablished", "receivingEvidence", "provenanceAuthenticated", "receiverExecutionVerified")) and
                   report["acceptanceTolerance"] is None and report["shadingAcceptance"] == "NOT_EVALUATED"},
        {"id": "P05", "topic": "Independent lock and original observation identities remain bound",
         "passed": report["inputLockSha256"] == adapter.digest(adapter.canonical_bytes(lock)) and
                   report["observationsSha256"] == adapter.digest(adapter.canonical_bytes(observations))},
    ]
    file_values = {"source-payload.json": payload, "input-lock.json": lock,
                   "synthetic-observations.json": observations, "loss-report.json": report}
    for filename, value in file_values.items():
        (output / filename).write_bytes(adapter.canonical_bytes(value) + b"\n")
    artifact_names = {"receiver_source": "receiver-source.txt", "importer_source": "importer-source.txt",
                      "build_record": "build-record.json", "import_settings": "import-settings.json"}
    for name, filename in artifact_names.items():
        (output / filename).write_bytes(artifacts[name])
    def git(*arguments: str) -> str:
        return subprocess.run(["git", "-C", str(ROOT), *arguments], check=True, capture_output=True, text=True).stdout.strip()
    result = {"schema": "ontokin.c215.cpu-proof/0.1", "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
              "revision": git("rev-parse", "HEAD"), "tree": git("rev-parse", "HEAD^{tree}"), "status": git("status", "--porcelain"),
              "python": sys.version, "platform": platform.platform(), "command": [sys.executable, "-IB", str(Path(__file__).resolve()), "--output", str(output)],
              "sourceInputs": adapter.source.ACCEPTED_INPUTS,
              "implementationFiles": {str(path.relative_to(ROOT)): descriptor(path.read_bytes()) for path in
                  [HERE / "adapter.py", HERE / "run_proof.py", HERE / "CONTRACT.md", adapter._source_path]},
              "files": {path.name: descriptor(path.read_bytes()) for path in sorted(output.iterdir()) if path.is_file()},
              "checks": checks, "passed": all(check["passed"] for check in checks), "summary": report["summary"],
              "nativeProcessesStarted": 0, "sourceProgramRuns": 0, "sourceExports": 0,
              "limits": "Synthetic smoke workflow only; independent controls and review are separate; no full regression or native acceptance"}
    (output / "CPU-PROOF.json").write_bytes(adapter.canonical_bytes(result) + b"\n")
    print(adapter.canonical_bytes({"passed": result["passed"], "checks": len(checks), "summary": report["summary"], "receipt": str(output / "CPU-PROOF.json")}).decode())
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
