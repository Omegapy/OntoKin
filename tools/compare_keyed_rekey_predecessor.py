#!/usr/bin/env python3
"""Compare every complete immediate-predecessor .18 stream with retained C085.

The default requires whole-byte equality. The explicit fingerprint-only mode
permits only the two inherited numeric implementation hash leaves, after
independently binding each value to its exact native source commit. Original
source identities, provenance, raw JSON member order, padding, framing, complete
BIN bytes and deliberate hostile suffixes remain exact. This comparison does
not replace the unchanged full .18 source, Agent, independent or native readers.
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
from tools.keyed_zip_reference import (FREEZE_COMMIT, FREEZE_SHA256, GLB,
    SOURCE_DERIVATION, SOURCE_IMPLEMENTATION, check_raw_framing,
    compact_json_bytes, digest, implementation_basis, json_differences, loads,
    ordinary_path, require, sha)

BASELINE_SUMMARY_SHA256 = "7797c7e26e01f6210878f8a275d41c9d073ec9fe2ed8ae27e4dcf94d0ddeb380"
BASELINE_PRODUCER_COMMIT = "6b895acf80466382c12340d1f68535c630fc1e63"
BASELINE_PRODUCER_TREE = "89848a8c851eac4bdb3cee398db57a6dd7b20b33"
ALLOWED = {
    ("extras", "ontokin", "reach_quantization", "source_numeric_bound_basis", "implementation_sha256"),
    ("extras", "ontokin", "reach_quantization", "destination_numeric_bound_basis", "implementation_sha256"),
}
IMPLEMENTATION_PATHS = (*SOURCE_IMPLEMENTATION, *SOURCE_DERIVATION,
    "tools/reach_destination.mjs", "docs/engineering/reach-destination-numerics.md")


def read_json(root, relative):
    return loads(ordinary_path(root, relative).read_bytes())


def git_read(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def git_identity(root):
    def read(*args):
        return git_read(root, *args).decode().strip()
    return {"commit": read("rev-parse", "HEAD"), "tree": read("rev-parse", "HEAD^{tree}"),
            "status": read("status", "--short")}


def implementation_inventory(root):
    return [{"path": name, "sha256": sha(ordinary_path(root, name).read_bytes())}
            for name in IMPLEMENTATION_PATHS]


def native_baseline_basis(repository):
    """Read original producer blobs without materializing another source tree.

    The supplied repository is an object source, not a claimed old checkout.
    Its current HEAD can be C086; each read is pinned to the exact C085 producer
    commit already bound by the immutable original summary and native tree ID.
    """
    require(git_read(repository, "cat-file", "-t", BASELINE_PRODUCER_COMMIT).strip() == b"commit",
            "Original C085 producer native commit is unavailable")
    require(git_read(repository, "rev-parse", BASELINE_PRODUCER_COMMIT + "^{tree}").decode().strip() == BASELINE_PRODUCER_TREE,
            "Original C085 producer native tree differs")
    raw_commit = git_read(repository, "cat-file", "commit", BASELINE_PRODUCER_COMMIT)
    entries = git_read(repository, "ls-tree", "-z", BASELINE_PRODUCER_COMMIT, "--", *IMPLEMENTATION_PATHS)
    files, inventory = {}, []
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        header, encoded_path = entry.split(b"\t", 1)
        mode, kind, object_id = header.split(b" ")
        name = encoded_path.decode("utf-8")
        require(name in IMPLEMENTATION_PATHS and name not in files and
                kind == b"blob" and mode in (b"100644", b"100755"),
                "Original numeric identity path is not an exact ordinary native blob")
        raw = git_read(repository, "cat-file", "blob", object_id.decode("ascii"))
        require(len(raw) <= 262144, "Original numeric identity component exceeds its finite bound")
        files[name] = raw
        inventory.append({"path": name, "mode": mode.decode(), "git_blob": object_id.decode(),
                          "bytes": len(raw), "sha256": sha(raw)})
    require(set(files) == set(IMPLEMENTATION_PATHS), "Original numeric identity native inventory is incomplete")

    def aggregate(paths):
        return digest(b"".join(name.encode() + b"\0" + sha(files[name]).encode() + b"\n" for name in paths))

    basis = {"source": {"name": "OntoKin controlled source poses", "version": "0.2",
        "implementation_sha256": aggregate(SOURCE_IMPLEMENTATION),
        "method": "ontokin.source-pose-projective-dyadic/0.2", "derivation_sha256": aggregate(SOURCE_DERIVATION)},
        "destination": {"implementation_sha256": digest(files["tools/reach_destination.mjs"]),
                        "derivation_sha256": digest(files["docs/engineering/reach-destination-numerics.md"])}}
    return basis, sorted(inventory, key=lambda item: item["path"]), {
        "commit": BASELINE_PRODUCER_COMMIT, "tree": BASELINE_PRODUCER_TREE,
        "raw_commit_sha256": sha(raw_commit), "raw_commit_bytes": len(raw_commit),
        "access": "Exact native commit/tree/blob reads; no recursive baseline checkout or modified predecessor inputs"}


def packed_exact(document, binary):
    """Preserve insertion order and the complete existing padded BIN bytes."""
    raw = compact_json_bytes(document)
    padded = raw + b" " * (-len(raw) % 4)
    length = 12 + 8 + len(padded) + 8 + len(binary)
    return (struct.pack("<III", 0x46546c67, 2, length) +
            struct.pack("<II", len(padded), 0x4e4f534a) + padded +
            struct.pack("<II", len(binary), 0x004e4942) + binary)


def compare_glb(previous, current, old_basis, new_basis, *, target,
                allow_fingerprint_only=False, deliberate_suffix=b""):
    """Compare full streams, retaining H12's exact intended framing fault."""
    old_raw, new_raw = previous, current
    if deliberate_suffix:
        require(previous.endswith(deliberate_suffix) and current.endswith(deliberate_suffix),
                "Original deliberate hostile suffix changed")
        old_raw, new_raw = previous[:-len(deliberate_suffix)], current[:-len(deliberate_suffix)]
    old, new = GLB(old_raw, target=target), GLB(new_raw, target=target)
    old_frame, new_frame = check_raw_framing(old), check_raw_framing(new)
    require(old.binary == new.binary, "Immediate predecessor complete BIN chunk changed")
    for document, basis in ((old.document, old_basis), (new.document, new_basis)):
        quantization = document["extras"]["ontokin"]["reach_quantization"]
        require(quantization["source_numeric_bound_basis"] == basis["source"],
                "Numeric source fingerprint is not independently bound to its native source cut")
        for name, value in basis["destination"].items():
            require(quantization["destination_numeric_bound_basis"][name] == value,
                    "Numeric destination fingerprint is not independently bound to its native source cut")
    changes = json_differences(old.document, new.document)
    require(all(tuple(change["path"]) in ALLOWED for change in changes),
            "Immediate predecessor has an unpermitted JSON difference: " + str(changes[:4]))
    if not allow_fingerprint_only:
        require(previous == current, "Strict immediate-predecessor whole-byte equality failed")
    normalized = []
    for glb in (old, new):
        document = copy.deepcopy(glb.document)
        for path in sorted(ALLOWED):
            parent = document
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = "<independently-bound-" + path[-2] + ">"
        normalized.append(packed_exact(document, glb.binary) + deliberate_suffix)
    require(normalized[0] == normalized[1],
            "Immediate predecessor raw JSON member order, compact encoding, padding, framing or hostile suffix changed")
    return {"status": "passed", "comparison": "exact" if previous == current else "fingerprint_only",
            "previous_sha256": sha(previous), "current_sha256": sha(current),
            "previous_bytes": len(previous), "current_bytes": len(current),
            "complete_bin_sha256": sha(old.binary), "complete_bin_bytes": len(old.binary),
            "normalized_full_stream_sha256": sha(normalized[0]), "normalized_full_stream_bytes": len(normalized[0]),
            "permitted_json_differences": changes,
            "deliberate_hostile_suffix_hex": deliberate_suffix.hex(),
            "previous_prefix_framing": old_frame, "current_prefix_framing": new_frame}


def artifact_inventory(directory, summary):
    result = {}
    for scope, rows in (("source", summary["cases"]), ("control", summary["controls"]),
                        ("agent", summary["agent_artifacts"])):
        for item in rows:
            if "glb" not in item:
                continue
            role = (scope, item.get("project_id", ""), item["name"])
            require(role not in result, "Duplicate predecessor artifact role")
            result[role] = {**item, "target": "ontokin.glb/0.17" if scope == "control" else "ontokin.glb/0.18"}
    publication = read_json(directory, "agent/publication-interruption.json")
    require(len(publication["prepared_only"]) == 1, "Missing exact interrupted-publication prepared artifact")
    result[("prepared", "c085-a08", "prepared-before-interruption")] = {
        **publication["prepared_only"][0], "target": "ontokin.glb/0.18"}
    require(Counter(role[0] for role in result) == Counter(source=5, control=5, agent=11, prepared=1),
            "Complete C085 positive source/control/Agent/prepared artifact inventory differs")
    for item in summary["hostile_glbs"]:
        role = ("hostile", item["case"], item["id"])
        require(role not in result, "Duplicate predecessor hostile role")
        result[role] = {**item, "glb": item["path"], "target": "ontokin.glb/0.18"}
    expected_hostile = {("hostile", case, f"H{i:02}")
                        for case in ("panel-task", "panel-task-repaired", "panel-task-higher-budget")
                        for i in range(1, 25)}
    require({role for role in result if role[0] == "hostile"} == expected_hostile,
            "Complete unchanged C085 72-hostile-stream inventory differs")
    return result


def artifact_bytes(directory, item):
    raw = ordinary_path(directory, item["glb"]).read_bytes()
    require(len(raw) == item["bytes"] and sha(raw) == item["sha256"],
            "Retained predecessor stream differs from its actual summary identity")
    return raw


def compare_summary_inventories(previous, current):
    for scope, count in (("cases", 254), ("controls", 160)):
        old_rows = {row["name"]: row for row in previous[scope]}
        new_rows = {row["name"]: row for row in current[scope]}
        require(len(previous[scope]) == len(old_rows) == len(current[scope]) == len(new_rows) == count and
                set(old_rows) == set(new_rows), "Complete predecessor source/control inventory changed")
        for name, before in old_rows.items():
            after = new_rows[name]
            for key in ("id", "name", "file_manifest", "program_revision", "delivered", "diagnostic_codes",
                        "expected_outcome", "expected_code", "expected_stage", "host_policy", "input_lineage", "producer_status"):
                require(before.get(key) == after.get(key), "Predecessor source outcome/identity changed: " + name + "/" + key)
    for key in ("amendments", "original_expected_sha256", "effective_expected_sha256", "profile",
                "agent_contract", "target_contract", "selected_section", "operation_inventory"):
        require(previous.get(key) == current.get(key), "Complete predecessor contract/operation inventory changed: " + key)
    require(current["selected_section"] == "all" and len(current["operation_inventory"]) == 12,
            "Immediate predecessor requires the full twelve-operation execution")
    old_workflows = {row["id"]: row for row in previous["workflows"]}
    new_workflows = {row["id"]: row for row in current["workflows"]}
    require(len(previous["workflows"]) == len(current["workflows"]) == len(old_workflows) == len(new_workflows) == 10 and
            set(old_workflows) == set(new_workflows), "Complete predecessor ten-workflow inventory changed")
    for workflow, before in old_workflows.items():
        after = new_workflows[workflow]
        for key in ("name", "project_id", "status"):
            require(before[key] == after[key], "Predecessor workflow outcome changed: " + workflow + "/" + key)
        for key in ("accepted_program_revision", "accepted_payload_sha256", "assets"):
            require(before["retained_state"].get(key) == after["retained_state"].get(key),
                    "Predecessor accepted source/asset state changed: " + workflow + "/" + key)
    old_positive = {row["case"]: row for row in previous["supplied_glb_positive_controls"]}
    new_positive = {row["case"]: row for row in current["supplied_glb_positive_controls"]}
    require(len(previous["supplied_glb_positive_controls"]) == len(current["supplied_glb_positive_controls"]) ==
            len(old_positive) == len(new_positive) == 3 and set(old_positive) == set(new_positive),
            "Complete unchanged supplied-byte positive-control inventory changed")
    require(all(row["status"] == "observed_as_expected" for row in new_positive.values()),
            "An unchanged supplied-byte positive control failed")


def compare(results, baseline_results, current_source, baseline_source, *, allow_fingerprint_only=False):
    previous_raw = ordinary_path(baseline_results, "summary.json").read_bytes()
    current_raw = ordinary_path(results, "summary.json").read_bytes()
    require(sha(previous_raw) == BASELINE_SUMMARY_SHA256,
            "Original C085 producer summary differs from the authoritative recovered evidence")
    previous, current = loads(previous_raw), loads(current_raw)
    for summary in (previous, current):
        require(summary["status"] == "produced_as_expected" and not summary.get("failures"), "Predecessor producer did not complete")
        require(summary["frozen_input_commit"] == FREEZE_COMMIT and summary["frozen_manifest_sha256"] == FREEZE_SHA256,
                "Predecessor inputs differ from the unchanged published C085 freeze")
    require(previous["git"] == {"commit": BASELINE_PRODUCER_COMMIT, "tree": BASELINE_PRODUCER_TREE, "status": ""},
            "Original C085 producer native identity differs")
    current_git = git_identity(current_source)
    require(current_git == current["git"] and not current_git["status"],
            "Current predecessor evidence does not identify this exact clean supplied source cut")
    compare_summary_inventories(previous, current)
    old_artifacts, new_artifacts = artifact_inventory(baseline_results, previous), artifact_inventory(results, current)
    require(set(old_artifacts) == set(new_artifacts), "Predecessor complete stream roles changed")
    old_basis, old_inventory, old_native = native_baseline_basis(baseline_source)
    new_basis = implementation_basis(current_source)
    report = {"schema_version": "ontokin.c086-immediate-predecessor-byte-comparison/0.1", "status": "running",
              "mode": "independently_bound_fingerprints_only" if allow_fingerprint_only else "strict_whole_byte_equality",
              "allowed_json_paths": [list(path) for path in sorted(ALLOWED)] if allow_fingerprint_only else [],
              "baseline_summary_sha256": sha(previous_raw), "current_summary_sha256": sha(current_raw),
              "baseline_producer_git": previous["git"], "current_producer_git": current["git"],
              "baseline_native_source": old_native, "current_supplied_source_git": current_git,
              "baseline_implementation_basis": old_basis, "current_implementation_basis": new_basis,
              "baseline_implementation_files": old_inventory,
              "current_implementation_files": implementation_inventory(current_source),
              "complete_outcomes": {"sources": 254, "controls": 160, "workflows": 10, "operations": 12,
                                    "hostile_streams": 72, "unchanged_positive_controls": 3},
              "artifacts": [], "failures": [], "release_acceptance": False,
              "scope": "All 94 retained complete GLB role streams: 5 source, 5 explicit-control, 11 Agent retrieval roles, 1 prepared-positive stream and 72 deliberately hostile streams. Repeated retrieval roles are not additional unique artifacts. Full unchanged .18 independent and native readers remain separate required evidence."}
    for role in sorted(old_artifacts):
        try:
            before, after = old_artifacts[role], new_artifacts[role]
            require(before["target"] == after["target"], "Predecessor stream target changed")
            require(before.get("program_revision") == after.get("program_revision"), "Predecessor stream program identity changed")
            if role[0] == "hostile":
                for key in ("mutation", "status", "diagnostic_codes", "actual_export_code", "exception"):
                    require(before.get(key) == after.get(key), "Predecessor hostile refusal changed: " + "/".join(role) + "/" + key)
            item = compare_glb(artifact_bytes(baseline_results, before), artifact_bytes(results, after), old_basis, new_basis,
                target=before["target"], allow_fingerprint_only=allow_fingerprint_only,
                deliberate_suffix=b"\0\0\0\0" if role[0] == "hostile" and role[2] == "H12" else b"")
            report["artifacts"].append({"role": list(role), "previous_path": before["glb"], "current_path": after["glb"], **item})
        except Exception as error:
            report["failures"].append({"role": list(role), "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc()})
    require(git_identity(current_source) == current_git, "Supplied current source changed during predecessor comparison")
    require(ordinary_path(results, "summary.json").read_bytes() == current_raw and
            ordinary_path(baseline_results, "summary.json").read_bytes() == previous_raw,
            "A supplied producer summary changed during comparison")
    report["counts"] = {"expected": len(old_artifacts), "compared": len(report["artifacts"]),
                        **dict(Counter(item["comparison"] for item in report["artifacts"])),
                        "role_streams_by_scope": dict(Counter(role[0] for role in old_artifacts)),
                        "previous_unique_complete_glb_sha256": len({item["sha256"] for item in old_artifacts.values()}),
                        "current_unique_complete_glb_sha256": len({item["sha256"] for item in new_artifacts.values()})}
    report["status"] = "failed" if report["failures"] else "passed"
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--baseline-results", type=Path, required=True)
    parser.add_argument("--current-source", type=Path, default=ROOT)
    parser.add_argument("--baseline-source", type=Path, default=ROOT,
                        help="Git object repository retaining the original C085 producer commit; no old working tree is required")
    parser.add_argument("--allow-implementation-fingerprint-deltas", action="store_true",
                        help="Explicitly allow only the two independently bound inherited implementation fingerprint leaves")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new report path")
    try:
        report = compare(*(getattr(args, key).resolve() for key in ("results", "baseline_results", "current_source", "baseline_source")),
                         allow_fingerprint_only=args.allow_implementation_fingerprint_deltas)
    except Exception as error:
        report = {"schema_version": "ontokin.c086-immediate-predecessor-byte-comparison/0.1", "status": "failed",
                  "exception": type(error).__name__, "reason": str(error), "traceback": traceback.format_exc(), "release_acceptance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in ("status", "mode", "counts", "reason") if key in report}))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
