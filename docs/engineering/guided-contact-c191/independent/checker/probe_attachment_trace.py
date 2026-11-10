#!/usr/bin/env python3
"""Retain the native shoe-attachment validation regression without new solving."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(args.repo.resolve()))
    from prototypes.guided_contact_v01.common import Budget, Failure, load_contract
    from prototypes.guided_contact_v01.source import Source
    from prototypes.guided_contact_v01.native_validation import validate_native, write_native_evidence
    from prototypes.guided_contact_v01.glb import encode_raw, project, verify_mapping
    source = Path(__file__).resolve().parent.parent / "source-fixtures/A.ok"
    budget = Budget(1000000, 80000)
    contract = load_contract()
    context = Source(source, source.read_bytes(), budget, contract).parse().validate()
    native = json.loads(args.native.read_text())
    assert native["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    native["samples"][100]["matrices_blender_m"]["left_shoe"][0][3] += .00015
    for bound in native["samples"][100]["bounds_gltf_mm"]["left_shoe"]:
        bound[0] += .15
    path = args.out / "native-result.json"
    path.write_text(json.dumps(native, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
    report = {"version": "C191-independent-native-attachment-regression-1", "implementation_revision": args.revision,
        "valid_native_input_sha256": hashlib.sha256(args.native.read_bytes()).hexdigest(),
        "mutated_native_input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "mutation": "Frame100 only: left shoe world X +0.15mm and both X bounds +0.15mm; body, IDs and all other values unchanged",
        "frozen_attachment_limit_mm": .1, "frozen_mapping_limit_mm": .2,
        "expected_diagnostic": "C191_E_NATIVE_RESULT", "rejected": False, "pass": False,
        "native_solve_performed": False, "trusted_host_fault_probe": True}
    try:
        result = validate_native(path, context, budget, contract)
        report["malformed_native_trace_accepted"] = True
        write_native_evidence(args.out, result, context)
        encode_raw(args.out, result, context, budget, contract["backend"])
        project(args.out, budget)
        mapping = verify_mapping(args.out, result, context, budget)
        report["malformed_trace_passed_mapping"] = True
        report["mapping"] = mapping
    except Failure as error:
        report.update(rejected=True, diagnostic=error.code, message=error.message,
                      **{"pass": error.code == "C191_E_NATIVE_RESULT"})
    report["cost"] = budget.cost()
    (args.out / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in ("mapping", "cost")}, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
