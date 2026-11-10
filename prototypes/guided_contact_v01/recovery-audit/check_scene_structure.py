#!/usr/bin/env python3
"""Supplemental C191-R2 complete saved-scene envelope checks.

These direct-validator probes are structural checks, not native re-simulations
or transaction qualification. The independent reviewer covers atomic rejection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixtures(data):
    first_size = struct.unpack_from("<i", data, 16)[0]
    end_offset = len(data) - 24
    negative = bytearray(data)
    struct.pack_into("<i", negative, 16, -1)
    overrun = bytearray(data)
    struct.pack_into("<i", overrun, 16, len(data))
    wrong_end = bytearray(data)
    struct.pack_into("<i", wrong_end, end_offset + 4, 1)
    missing_dna = bytearray(data)
    offset = 12
    while offset < len(data):
        code, size, _, _, _ = struct.unpack_from("<4siQii", data, offset)
        if code == b"DNA1":
            missing_dna[offset:offset + 4] = b"DATA"
        offset += 24 + size
    return {
        "valid-scene": (data, None),
        "header-only": (data[:12], "C191_E_NATIVE_RESULT"),
        "header-plus-one-byte": (data[:13], "C191_E_NATIVE_RESULT"),
        "truncated-block-header": (data[:20], "C191_E_NATIVE_RESULT"),
        "truncated-block-payload": (data[:12 + 24 + first_size - 1], "C191_E_NATIVE_RESULT"),
        "missing-end-block": (data[:end_offset], "C191_E_NATIVE_RESULT"),
        "truncated-end-block": (data[:-1], "C191_E_NATIVE_RESULT"),
        "trailing-data": (data + b"x", "C191_E_NATIVE_RESULT"),
        "negative-block-size": (bytes(negative), "C191_E_NATIVE_RESULT"),
        "block-size-overrun": (bytes(overrun), "C191_E_NATIVE_RESULT"),
        "nonempty-end-block": (bytes(wrong_end), "C191_E_NATIVE_RESULT"),
        "missing-dna-block": (bytes(missing_dna), "C191_E_NATIVE_RESULT"),
        "header-and-end-only": (data[:12] + data[end_offset:], "C191_E_NATIVE_RESULT"),
    }


def run(repo, seed, output):
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo))
    from prototypes.guided_contact_v01.common import Budget, Failure, load_contract
    from prototypes.guided_contact_v01.native_validation import validate_scene_artifact
    from prototypes.guided_contact_v01.source import Source

    source = repo / "docs/language-design/guided-contact-v0.1/examples/A.ok"
    original = seed.read_bytes()
    records = []
    for name, (data, expected) in fixtures(original).items():
        directory = output / name
        directory.mkdir()
        scene = directory / "scene.blend"
        scene.write_bytes(data)
        budget = Budget(1000000, 80000)
        contract = load_contract()
        context = Source(source, source.read_bytes(), budget, contract).parse().validate()
        actual = None
        message = None
        try:
            validate_scene_artifact(scene, context, budget, contract)
        except Failure as error:
            actual, message = error.code, error.message
        records.append({"case": name, "input_sha256": digest(data), "input_bytes": len(data),
                        "expected_code": expected, "actual_code": actual, "message": message,
                        "pass": expected == actual, "cost": budget.cost()})
    revision = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              check=True, capture_output=True, text=True).stdout.strip()
    return {"version": "C191-R2-author-saved-scene-structure-audit-1", "implementation_revision": revision,
            "validator_sha256": digest((repo / "prototypes/guided_contact_v01/native_validation.py").read_bytes()),
            "script_sha256": digest(Path(__file__).read_bytes()), "seed_sha256": digest(original),
            "method": "Direct structural validator; no native solve or transaction assertion",
            "cases": records, "passed": sum(row["pass"] for row in records), "total": len(records),
            "pass": all(row["pass"] for row in records)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.repo.resolve(), args.seed.resolve(), args.output.resolve())
    (args.output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"],
                      "cases": [{k: row[k] for k in ("case", "expected_code", "actual_code", "pass")}
                                for row in report["cases"]]}, indent=2))
    raise SystemExit(0 if report["pass"] else 1)
