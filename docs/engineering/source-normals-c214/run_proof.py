#!/usr/bin/env python3
"""Produce the bounded C214 CPU proof and retain exact generated artifacts."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import platform
from pathlib import Path
import struct
import subprocess
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
spec = importlib.util.spec_from_file_location("c214_normal_prototype", HERE / "prototype.py")
prototype = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prototype)


def write_json(path: Path, value: object) -> None:
    with path.open("xb") as stream:
        stream.write(prototype.canonical_bytes(value) + b"\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    proof = REPO / "docs/engineering/semantic-export-c210/evidence/proof"
    input_paths = [proof / name for name in ("after.glb", "after.program.bundle.json", "after.semantic.json")]
    inputs = tuple(path.read_bytes() for path in input_paths)
    checks = []

    def check(name: str, passed: bool) -> None:
        checks.append({"name": name, "passed": bool(passed)})
        if not passed:
            write_json(output / "FAILED-CHECKS.json", checks)
            raise AssertionError(name)

    payload = prototype.build_payload(*inputs)
    write_json(output / "source-normal-payload.json", payload)
    roundtrip = prototype.load_json((output / "source-normal-payload.json").read_bytes())
    validation = prototype.validate_payload(roundtrip, *inputs)
    write_json(output / "payload-validation.json", validation)
    check("exact-payload-roundtrip", prototype.canonical_bytes(roundtrip) == prototype.canonical_bytes(payload))
    check("selected-source-size", validation["sourceCorners"] == 3024 and validation["instances"] == 18)
    records = []
    for instance in payload["instances"]:
        for corner in payload["corners"]:
            if corner["key"][0] == instance["mesh"]:
                records.append({"key": [instance["node"], *corner["key"]],
                                "normal": list(struct.unpack("<3f", bytes.fromhex(corner["normal_f32le"])))})
    observations = {"schema_version": prototype.OBSERVATIONS_SCHEMA,
                    "sourcePayloadSha256": validation["payloadSha256"],
                    "sourceFrame": prototype.FRAME, "kind": "synthetic-cpu",
                    "producer": "C214 run_proof.py exact CPU source-copy fixture; not native shading",
                    "records": records}
    write_json(output / "synthetic-exact-observations.json", observations)
    exact_report = prototype.build_loss_report(payload, observations, *inputs)
    write_json(output / "synthetic-exact-loss-report.json", exact_report)
    summary = exact_report["summary"]
    check("complete-instance-observations", summary["expected"] == summary["observed"] == 23400 and
          summary["missing"] == summary["invalid"] == 0)
    check("exact-synthetic-differences", summary["maximumComponentDifference"] == 0.0 and
          summary["maximumAngularDifferenceDegrees"] == 0.0)
    check("no-native-claim-from-exact-copy", exact_report["nativeFidelityEstablished"] is False and
          exact_report["receivingEvidence"] is False and exact_report["acceptanceTolerance"] is None and
          exact_report["shadingAcceptance"] == "NOT_EVALUATED")
    loss_observations = copy.deepcopy(observations)
    loss_observations["producer"] = "C214 run_proof.py deliberate synthetic loss/missing/invalid fixture; not native shading"
    loss_records = copy.deepcopy(records[:11])
    loss_records[1]["normal"] = [-value for value in loss_records[1]["normal"]]
    loss_records[2]["normal"] = [0.0, 1.0, 0.0]
    loss_records[3]["normal"] = [2.0 * value for value in loss_records[3]["normal"]]
    loss_records[4]["normal"] = [0.0, 0.0, 0.0]
    loss_records[5]["normal"] = [1.0, 0.0]
    loss_records[6]["normal"] = ["NaN", 0.0, 1.0]
    loss_records[7]["normal"] = [1e308, 0.0, 0.0]
    loss_records[8]["normal"] = [5e-324, 0.0, 0.0]
    loss_records[9]["normal"] = [-0.0, 0.0, -0.0]
    loss_records[10]["normal"] = [True, 0.0, 0.0]
    loss_observations["records"] = loss_records
    write_json(output / "synthetic-loss-observations.json", loss_observations)
    loss_report = prototype.build_loss_report(payload, loss_observations, *inputs)
    write_json(output / "synthetic-loss-report.json", loss_report)
    summary = loss_report["summary"]
    check("missing-invalid-denominator", summary["expected"] == 23400 and summary["observed"] == 6 and
          summary["invalid"] == 5 and summary["missing"] == 23389)
    check("opposite-direction-visible", summary["maximumAngularDifferenceDegrees"] == 180.0)
    check("magnitude-loss-visible", loss_report["corners"][3]["maximumComponentDifference"] == 1.0 and
          loss_report["corners"][3]["angularDifferenceDegrees"] == 0.0)
    check("extreme-directions-measured", loss_report["corners"][7]["status"] == "observed" and
          loss_report["corners"][8]["status"] == "observed")
    mutated = copy.deepcopy(payload)
    raw = bytearray.fromhex(mutated["corners"][0]["normal_f32le"])
    raw[11] ^= 0x80
    mutated["corners"][0]["normal_f32le"] = raw.hex()
    try:
        prototype.validate_payload(mutated, *inputs)
        rejected = False
    except prototype.ProfileError:
        rejected = True
    check("normal-sign-tamper-refused", rejected)
    try:
        native = dict(observations, kind="native")
        prototype.build_loss_report(payload, native, *inputs)
        rejected = False
    except prototype.ProfileError:
        rejected = True
    check("native-label-refused", rejected)
    # Git identity queries do not launch the source program or a destination
    revision = subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(REPO), "status", "--porcelain=v1"], text=True).splitlines()
    source_files = {str(path.relative_to(REPO)): {"sha256": prototype.digest(path.read_bytes()), "bytes": path.stat().st_size}
                    for path in (HERE / "prototype.py", HERE / "run_proof.py", HERE / "CONTRACT.md")}
    output_files = {path.name: {"sha256": prototype.digest(path.read_bytes()), "bytes": path.stat().st_size}
                    for path in sorted(output.iterdir()) if path.is_file()}
    receipt = {"schema": "ontokin.c214.cpu-proof/0.1", "status": "PASS", "recordedAtUtc": datetime.now(timezone.utc).isoformat(),
               "sourceRevision": revision, "sourceWorktreeStatus": dirty, "sourceFiles": source_files,
               "command": "python3 -IB docs/engineering/source-normals-c214/run_proof.py --output <new-output-directory>",
               "python": sys.version, "platform": platform.platform(),
               "inputs": {str(path.relative_to(REPO)): {"sha256": prototype.digest(data), "bytes": len(data)}
                          for path, data in zip(input_paths, inputs)},
               "outputs": output_files, "checks": checks, "checksPassed": len(checks),
               "sourceCorners": validation["sourceCorners"], "instances": validation["instances"],
               "exactSyntheticSummary": exact_report["summary"], "lossSyntheticSummary": loss_report["summary"],
               "nativeProcessesStarted": 0, "sourceProgramRuns": 0, "sourceExports": 0,
               "acceptanceTolerance": None, "receivingEvidence": False,
               "knownLimits": ["Only exact accepted C210 input triple", "Synthetic observations only",
                               "No receiving application or native shading validation", "No full product regression claim"],
               "handoffOutputPath": "evidence/c214/generated/"}
    write_json(output / "CPU-PROOF.json", receipt)
    print(json.dumps({"status": receipt["status"], "checksPassed": len(checks), "output": str(output),
                      "sourceCorners": validation["sourceCorners"], "observationCorners": summary["expected"]}))


if __name__ == "__main__":
    main()
