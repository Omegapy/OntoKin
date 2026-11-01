#!/usr/bin/env python3
"""Compare complete immediate-predecessor bytes with unchanged C083 evidence.

Only the independently recomputed source and destination numeric implementation
fingerprint leaves may differ. Source identities, provenance, all other JSON,
member order, padding, framing and the complete BIN chunk remain exact.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.keyed_filter_reference import (FREEZE_COMMIT, FREEZE_SHA256, GLB,
    SOURCE_DERIVATION, SOURCE_IMPLEMENTATION, check_raw_framing,
    compact_json_bytes, implementation_basis, json_differences, loads,
    ordinary_path, require, sha)

BASELINE_SUMMARY_SHA256 = "50febfae1cd813e2652c00bc6f70a58797b0774e2e916ab3b1a4377ae112bb50"
ALLOWED = {
    ("extras", "ontokin", "reach_quantization", "source_numeric_bound_basis", "implementation_sha256"),
    ("extras", "ontokin", "reach_quantization", "destination_numeric_bound_basis", "implementation_sha256"),
}


def read_json(root, relative):
    return loads(ordinary_path(root, relative).read_bytes())


def git_identity(root):
    def read(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    return {"commit": read("rev-parse", "HEAD"), "tree": read("rev-parse", "HEAD^{tree}"),
            "status": read("status", "--short")}


def implementation_inventory(root):
    paths = (*SOURCE_IMPLEMENTATION, *SOURCE_DERIVATION, "tools/reach_destination.mjs",
             "docs/engineering/reach-destination-numerics.md")
    return [{"path": name, "sha256": sha(ordinary_path(root, name).read_bytes())} for name in paths]


def packed_exact(document, binary):
    """Preserve insertion order and the existing complete padded BIN bytes."""
    raw = compact_json_bytes(document)
    padded = raw + b" " * (-len(raw) % 4)
    length = 12 + 8 + len(padded) + 8 + len(binary)
    return (struct.pack("<III", 0x46546c67, 2, length) +
            struct.pack("<II", len(padded), 0x4e4f534a) + padded +
            struct.pack("<II", len(binary), 0x004e4942) + binary)


def compare_glb(previous, current, old_basis, new_basis, *, target):
    """Independently bind fingerprints before permitting their two leaf deltas."""
    old, new = GLB(previous, target=target), GLB(current, target=target)
    old_frame, new_frame = check_raw_framing(old), check_raw_framing(new)
    require(old.binary == new.binary, "Immediate predecessor complete BIN chunk changed")
    for document, basis in ((old.document, old_basis), (new.document, new_basis)):
        quantization = document["extras"]["ontokin"]["reach_quantization"]
        require(quantization["source_numeric_bound_basis"] == basis["source"],
                "Numeric source fingerprint is not independently bound to its supplied source cut")
        for name, value in basis["destination"].items():
            require(quantization["destination_numeric_bound_basis"][name] == value,
                    "Numeric destination fingerprint is not independently bound to its supplied source cut")
    changes = json_differences(old.document, new.document)
    require(all(tuple(change["path"]) in ALLOWED for change in changes),
            "Immediate predecessor has an unpermitted JSON difference: " + str(changes[:4]))
    normalized = []
    for glb in (old, new):
        document = copy.deepcopy(glb.document)
        for path in sorted(ALLOWED):
            parent = document
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = "<independently-bound-" + path[-2] + ">"
        normalized.append(packed_exact(document, glb.binary))
    require(normalized[0] == normalized[1],
            "Immediate predecessor raw JSON member order, compact encoding, padding or framing changed")
    return {"status": "passed", "comparison": "exact" if previous == current else "fingerprint_only",
            "previous_sha256": sha(previous), "current_sha256": sha(current),
            "previous_bytes": len(previous), "current_bytes": len(current),
            "complete_bin_sha256": sha(old.binary), "complete_bin_bytes": len(old.binary),
            "normalized_full_glb_sha256": sha(normalized[0]), "normalized_full_glb_bytes": len(normalized[0]),
            "permitted_json_differences": changes,
            "previous_framing": old_frame, "current_framing": new_frame}


def artifact_inventory(directory, summary):
    result = {}
    for scope, rows in (("source", summary["cases"]), ("control", summary["controls"]),
                        ("agent", summary["agent_artifacts"])):
        for item in rows:
            if "glb" not in item:
                continue
            role = (scope, item.get("project_id", ""), item["name"])
            require(role not in result, "Duplicate predecessor artifact role")
            result[role] = {**item, "target": "ontokin.glb/0.15" if scope == "control" else "ontokin.glb/0.16"}
    publication = read_json(directory, "agent/publication-interruption.json")
    require(len(publication["prepared_only"]) == 1, "Missing exact interrupted-publication prepared artifact")
    result[("prepared", "c083-a08", "prepared-before-interruption")] = {
        **publication["prepared_only"][0], "target": "ontokin.glb/0.16"}
    require(Counter(role[0] for role in result) == Counter(source=5, control=5, agent=9, prepared=1),
            "Complete C083 source/control/Agent/prepared artifact inventory differs")
    return result


def artifact_bytes(directory, item):
    raw = ordinary_path(directory, item["glb"]).read_bytes()
    require(len(raw) == item["bytes"] and sha(raw) == item["sha256"],
            "Retained predecessor artifact differs from its actual summary identity")
    return raw


def compare(results, baseline_results, current_source, baseline_source):
    previous_raw = ordinary_path(baseline_results, "summary.json").read_bytes()
    require(sha(previous_raw) == BASELINE_SUMMARY_SHA256, "Original C083 producer summary differs from the authoritative recovered evidence")
    previous, current = loads(previous_raw), read_json(results, "summary.json")
    for summary in (previous, current):
        require(summary["status"] == "produced_as_expected" and not summary.get("failures"), "Predecessor producer did not complete")
        require(summary["frozen_input_commit"] == FREEZE_COMMIT and summary["frozen_manifest_sha256"] == FREEZE_SHA256,
                "Predecessor inputs differ from the unchanged published C083 freeze")
    current_git = git_identity(current_source)
    require(current_git == current["git"] and not current_git["status"],
            "Current predecessor evidence does not identify this exact clean supplied source cut")
    for scope in ("cases", "controls"):
        old_rows = {row["name"]: row for row in previous[scope]}
        new_rows = {row["name"]: row for row in current[scope]}
        require(len(previous[scope]) == len(old_rows) == len(current[scope]) == len(new_rows) and set(old_rows) == set(new_rows),
                "Complete predecessor source/control inventory changed")
        for name, before in old_rows.items():
            after = new_rows[name]
            for key in ("id", "name", "file_manifest", "program_revision", "delivered", "diagnostic_codes"):
                require(before.get(key) == after.get(key), "Predecessor source outcome/identity changed: " + name + "/" + key)
    old_artifacts, new_artifacts = artifact_inventory(baseline_results, previous), artifact_inventory(results, current)
    require(set(old_artifacts) == set(new_artifacts), "Predecessor artifact roles changed")
    old_basis, new_basis = implementation_basis(baseline_source), implementation_basis(current_source)
    report = {"schema_version": "ontokin.c084-immediate-predecessor-byte-comparison/0.1", "status": "running",
              "baseline_summary_sha256": sha(previous_raw), "current_summary_sha256": sha(ordinary_path(results, "summary.json").read_bytes()),
              "baseline_producer_git": previous["git"], "current_producer_git": current["git"],
              "baseline_supplied_source_git": git_identity(baseline_source), "current_supplied_source_git": current_git,
              "baseline_implementation_basis": old_basis, "current_implementation_basis": new_basis,
              "baseline_implementation_files": implementation_inventory(baseline_source),
              "current_implementation_files": implementation_inventory(current_source),
              "artifacts": [], "failures": [], "release_acceptance": False,
              "scope": "All5source,5explicit-control,9Agent and1prepared-positive GLBs; hostile supplied-byte refusals are checked separately by the unchanged full C083 readers."}
    for role in sorted(old_artifacts):
        try:
            before, after = old_artifacts[role], new_artifacts[role]
            require(before["target"] == after["target"], "Predecessor artifact target changed")
            require(before.get("program_revision") == after.get("program_revision"), "Predecessor artifact program identity changed")
            item = compare_glb(artifact_bytes(baseline_results, before), artifact_bytes(results, after), old_basis, new_basis, target=before["target"])
            report["artifacts"].append({"role": list(role), "previous_path": before["glb"], "current_path": after["glb"], **item})
        except Exception as error:
            report["failures"].append({"role": list(role), "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc()})
    report["counts"] = {"expected": len(old_artifacts), "compared": len(report["artifacts"]),
                        **dict(Counter(item["comparison"] for item in report["artifacts"]))}
    report["status"] = "failed" if report["failures"] else "passed"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--baseline-results", type=Path, required=True)
    parser.add_argument("--current-source", type=Path, default=ROOT)
    parser.add_argument("--baseline-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new report path")
    try:
        report = compare(*(getattr(args, key).resolve() for key in ("results", "baseline_results", "current_source", "baseline_source")))
    except Exception as error:
        report = {"schema_version": "ontokin.c084-immediate-predecessor-byte-comparison/0.1", "status": "failed",
                  "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc(), "release_acceptance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "counts", "reason") if key in report}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
