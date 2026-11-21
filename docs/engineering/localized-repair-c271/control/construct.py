#!/usr/bin/env python3
"""Construct/check C271 source deletions and a specification-derived oracle.

This script never imports an OntoKin parser, observer, evaluator, exporter,
historical test, or outcome log. Its only imports are Python standard-library
modules. --write refuses to overwrite different existing fixture/oracle bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys


CONTROL = Path(__file__).resolve().parent
REPO = CONTROL.parents[3]
CONTROL_PATH = "docs/engineering/localized-repair-c271/control"
PROOF = "docs/engineering/semantic-export-c210/evidence/proof"
SCOPE_REVISION = "c27609ebab7c86ff20d7bd288994b49e3dd3c7e1"
MAIN_REVISION = "e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d"
PINS = {
    "before.main.ok": (1708, "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123"),
    "after.main.ok": (1708, "443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a"),
    "hinges.ok": (1911, "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"),
    "before.glb": (185276, "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534"),
    "after.glb": (185236, "05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8"),
}
CLAUSE = b'digest "sha256:1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"'
VALUE = b'"sha256:1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a"'
DELETIONS = {
    "missing_digest_clause": (217, 297, CLAUSE),
    "missing_digest_value": (224, 297, VALUE),
}
BASIS_PATHS = [
    "docs/engineering/localized-repair-c260/CONTRACT.md",
    "docs/engineering/localized-repair-c260/CONTROL-PLAN.md",
    "docs/engineering/localized-repair-c260/INPUTS.json",
    "docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md",
    "docs/language-design/construction-v0.1/ontokin-construction.ebnf",
    "docs/engineering/localized-repair-c269/COVERAGE.json",
]


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identity(path: str, raw: bytes) -> dict:
    return {"path": path, "bytes": len(raw), "sha256": sha(raw)}


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def candidate_program(main: bytes, hinges: bytes) -> dict:
    # OK-LANG-002 section 3.2: identity exists even when source is malformed.
    manifest = {
        "schema_version": "ontokin.bundle/0.1",
        "entry_source_id": "entry",
        "units": [
            {"source_id": "entry", "package_id": None, "version": None,
             "filename": "main.ok", "source_revision": "sha256:" + sha(main)},
            {"source_id": "package:example.hinges@1.0.0",
             "package_id": "example.hinges", "version": "1.0.0",
             "filename": "hinges.ok", "source_revision": "sha256:" + sha(hinges)},
        ],
    }
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf-8")
    return {"manifest": manifest,
            "revision": "sha256:" + sha(b"ontokin.bundle/0.1\0" + canonical)}


def baseline_semantics() -> dict:
    # Authored from the literal keyed helper/default and final second override.
    # These are source expectations, never fields copied from an observation.
    rows = []
    for root, keys in [("first", ["lower", "middle", "upper"]),
                       ("second", ["bottom", "lower", "middle", "upper", "top"])]:
        for key in keys:
            owner = ["keyed-rack", "demo", root, "fingers", key]
            rows.append({
                "owning_object_id": owner,
                "joint_occurrence_id": owner + ["flex"],
                "parent_site_occurrence_id": owner + ["pivot"],
                "child_site_occurrence_id": owner + ["blade", "base"],
            })
    return {
        "derivation": "C260 sections 3 and 4; actual main.ok and hinges.ok declarations only",
        "object_count": 18,
        "hinge_count": 8,
        "unique_joint_definition_count": 1,
        "distinct_endpoint_site_count": 16,
        "joint_definition_id": ["package", "example.hinges", "hinges", "definitions", "finger", "flex"],
        "parent_site_definition_id": ["package", "example.hinges", "hinges", "definitions", "finger", "pivot"],
        "child_site_definition_id": ["package", "example.hinges", "hinges", "definitions", "blade", "base"],
        "joint_name": "flex",
        "joint_key": "flex",
        "kind": "hinge",
        "axis": [0, 0, 1],
        "limits_binary64_hex": ["-0x1.921fb54442d18p-1", "0x1.921fb54442d18p-1"],
        "initial_binary64_hex": "0x0.0p+0",
        "site_interface": "hinged.part",
        "site_size_metres_binary64_hex": "0x0.0p+0",
        "rows": rows,
        "row_order_significant": False,
        "endpoint_order_significant": True,
        "site_records_are_source_associations": True,
        "site_pose_evaluated": False,
    }


def expected_outcome(variant: str) -> dict:
    failed = variant != "baseline"
    result = {
        "outcome": "typed_refusal" if failed else "success",
        "refusal_code": "MALFORMED" if failed else None,
    }
    return {
        "source_observation": dict(result),
        "source_program_binding": dict(result),
        "hinge_comparison": dict(result),
        "returned_success_allowed": not failed,
        "qualified_partial_result_allowed": False,
        "qualified_hinge_set_allowed": not failed,
        "baseline_semantics_reference": None if failed else "#/baseline_semantics",
        "exact_refusal_message_required": False,
        "historical_admission_claim_allowed": False,
        "complete_language_validity_claim_allowed": False,
        "accepted_revision_claim_allowed": False,
    }


def build() -> tuple[dict[str, bytes], list[dict], list[dict]]:
    originals = {}
    inputs = []
    for name, (size, digest) in PINS.items():
        path = f"{PROOF}/{name}"
        raw = (REPO / path).read_bytes()
        if len(raw) != size or sha(raw) != digest:
            raise ValueError(f"historical input identity mismatch: {path}")
        originals[name] = raw
        inputs.append(identity(path, raw))

    contract_inputs = json.loads((REPO / BASIS_PATHS[2]).read_text(encoding="utf-8"))
    declared = {row["path"]: row for row in contract_inputs["files"]}
    for row in inputs:
        if row != {key: declared[row["path"]][key] for key in ["path", "bytes", "sha256"]}:
            raise ValueError(f"C260 input pin disagreement: {row['path']}")

    outputs = {}
    cases = []
    reconstruction = []
    for endpoint in ["before", "after"]:
        original_path = f"{PROOF}/{endpoint}.main.ok"
        original = originals[f"{endpoint}.main.ok"]
        for variant in ["baseline", *DELETIONS]:
            mutation = None
            if variant == "baseline":
                main = original
                main_path = original_path
            else:
                start, end, removed = DELETIONS[variant]
                if original.count(removed) != 1 or original[start:end] != removed:
                    raise ValueError(f"deletion target is not exact and unique: {endpoint}/{variant}")
                if original[end:end + 3] != b";\n\n":
                    raise ValueError("target suffix no longer preserves semicolon/newlines")
                main = original[:start] + original[end:]
                main_path = f"{CONTROL_PATH}/fixtures/{endpoint}.{variant}.main.ok"
                outputs[main_path] = main
                if main[:start] != original[:start] or main[start:] != original[end:]:
                    raise ValueError("non-target bytes changed")
                if main[:start] + removed + main[start:] != original:
                    raise ValueError("inverse deletion did not reconstruct the original")
                mutation = {
                    "operation": "delete_one_exact_contiguous_byte_range",
                    "original": identity(original_path, original),
                    "range_convention": "zero_based_half_open_utf8_bytes",
                    "start_byte": start,
                    "end_byte": end,
                    "removed_utf8": removed.decode("utf-8"),
                    "removed_bytes": len(removed),
                    "removed_sha256": sha(removed),
                    "replacement_utf8": "",
                    "all_other_entry_bytes_preserved": True,
                    "companion_source_unchanged": True,
                    "artifact_unchanged": True,
                }
                reconstruction.append({
                    "case_id": f"{endpoint}__{variant}",
                    "exact_unique_target": True,
                    "unchanged_prefix_and_suffix": True,
                    "inverse_deletion_matches_original": True,
                    "semicolon_and_surrounding_whitespace_preserved": True,
                })
            cases.append({
                "id": f"{endpoint}__{variant}",
                "endpoint": endpoint,
                "variant": variant,
                "source_files": {
                    "main.ok": identity(main_path, main),
                    "hinges.ok": identity(f"{PROOF}/hinges.ok", originals["hinges.ok"]),
                },
                "artifact": identity(f"{PROOF}/{endpoint}.glb", originals[f"{endpoint}.glb"]),
                "candidate_program": candidate_program(main, originals["hinges.ok"]),
                "mutation": mutation,
                "expected": expected_outcome(variant),
            })

    oracle = {
        "schema": "ontokin.c271.missing-import-digest-oracle/0.1",
        "task": "C271",
        "control": "H22.02",
        "author": "/root/control_author",
        "reported_published_scope_revision": SCOPE_REVISION,
        "reported_starting_main_revision": MAIN_REVISION,
        "observation_status": "not_run_by_oracle_author",
        "independence": {
            "basis": "Adopted rules and historical source bytes; no implementation or observed output supplies an expected result",
            "observer_test_product_code_read_or_executed": False,
            "prior_observer_outcome_logs_read": False,
            "public_code_spelling": "Director supplied only the public README mapping of malformed source to MALFORMED before construction",
            "c269_usage": "Only the H22.02 gap and its audit context identify the missing case; no historical output supplies the oracle",
        },
        "basis_files": [identity(path, (REPO / path).read_bytes()) for path in BASIS_PATHS],
        "baseline_semantics": baseline_semantics(),
        "cases": cases,
        "limits": [
            "Exactly two original endpoints and two digest-deletion variants per endpoint",
            "No runtime, observer, source grammar or adopted contract change",
            "No source evaluation, export, site-pose/motion qualification, or product-wide result",
            "A passing control does not complete H22, C260, or the parent task",
        ],
    }
    outputs[f"{CONTROL_PATH}/EXPECTED.json"] = json_bytes(oracle)
    return outputs, inputs, reconstruction


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    outputs, inputs, reconstruction = build()
    for relative, wanted in outputs.items():
        path = REPO / relative
        if args.write and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(wanted)
        if not path.is_file() or path.read_bytes() != wanted:
            raise ValueError(f"constructed output differs or is missing: {relative}")
    report = {
        "schema": "ontokin.c271.control-static-checks/0.1",
        "passed": True,
        "scope": "fixture reconstruction, exact bytes and independently authored oracle only",
        "command": "python3 " + str(Path(__file__).resolve().relative_to(REPO)) +
                   (" --write" if args.write else " --check") +
                   (" --report " + str(args.report) if args.report else ""),
        "python": sys.version,
        "platform": platform.platform(),
        "input_identities": inputs,
        "output_identities": [identity(path, raw) for path, raw in outputs.items()],
        "reconstruction_checks": reconstruction,
        "case_count": 6,
        "baseline_cases": 2,
        "missing_digest_cases": 4,
        "observer_invocations": 0,
        "product_parser_evaluator_exporter_invocations": 0,
    }
    if args.report:
        report_path = args.report.resolve()
        if not report_path.is_relative_to(CONTROL):
            raise ValueError("report must remain inside the assigned control directory")
        if report_path.exists() and report_path.read_bytes() != json_bytes(report):
            raise ValueError("refusing to replace an existing different static report")
        report_path.write_bytes(json_bytes(report))
    print(json.dumps({"passed": True, "cases": 6, "fixture_outputs": 4,
                      "oracle_sha256": sha(outputs[f"{CONTROL_PATH}/EXPECTED.json"]),
                      "observer_invocations": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
