#!/usr/bin/env python3
"""Create C036's closed-evidence archive and member manifest."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
import time
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--workspace", type=Path, required=True)
parser.add_argument("--destination", type=Path, required=True)
parser.add_argument("--receipt", type=Path, required=True)
args = parser.parse_args()
started_at = datetime.now(timezone.utc).isoformat()
started = time.monotonic()
workspace, destination = args.workspace.resolve(), args.destination.resolve()
analysis = json.loads((workspace / "c036-evidence/analysis-001/report.json").read_text())
assert analysis["status"] == "passed" and analysis["neutrality"]["passed"]
review = json.loads((workspace / "c036-observations/independent-census-review.json").read_text())
assert review["status"] == "passed"
pair = workspace / "c036-evidence/pair-001"
request = json.loads((pair / "capture/request-result.json").read_text())
assert request["capture_status"] == "captured" and request["status"] == "failed"
members, data = [], {}
for namespace, folder in (("execution", "c036-evidence"), ("observations", "c036-observations"), ("drivers", "c036-drivers")):
    for path in sorted((workspace / folder).rglob("*")):
        if path.is_dir():
            continue
        assert path.is_file() and not path.is_symlink() and "__pycache__" not in path.parts
        name = namespace + "/" + path.relative_to(workspace / folder).as_posix()
        parsed = PurePosixPath(name)
        assert not parsed.is_absolute() and ".." not in parsed.parts and name not in data
        raw = path.read_bytes()
        data[name] = raw
        members.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
members.sort(key=lambda row: row["path"])
manifest = {"schema_version": "ontokin.checkpoint036-members/0.1", "checkpoint": 36,
            "member_count": len(members), "members": members}
manifest_path = destination / "checkpoint-036-manifest.json"
write(manifest_path, manifest)
archive = io.BytesIO()
with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
    for member in members:
        info = zipfile.ZipInfo(member["path"], date_time=(2026, 10, 25, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        output.writestr(info, data[member["path"]])
joined = archive.getvalue()
parts = []
for offset in range(0, len(joined), 700000):
    raw = joined[offset:offset + 700000]
    name = "checkpoint-036-evidence.zip.part%03d" % (len(parts) + 1)
    with (destination / name).open("xb") as stream:
        stream.write(raw)
    parts.append({"path": name, "bytes": len(raw), "sha256": sha(raw)})
with zipfile.ZipFile(io.BytesIO(joined)) as check:
    assert check.testzip() is None
    assert check.namelist() == [row["path"] for row in members]
    for row in members:
        raw = check.read(row["path"])
        assert len(raw) == row["bytes"] and sha(raw) == row["sha256"]
state = request["post_state"]
checkpoint = {
    "schema_version": "ontokin.runtime-investigation-checkpoint/0.1", "checkpoint": 36,
    "owner": "interactive-reach06-p11-quaternion-census-20261025-c036",
    "branch": "work/reach06-p11-quaternion-census-20261025-c036",
    "starting_commit": "d485c9bc81a5bdc8500c93d70eeb6b738f1fba97",
    "starting_tree": "c146832a29d4d5be738ddd0128c88186cdef36b9",
    "execution_commit": request["source_commit"], "execution_tree": request["source_tree"],
    "accepted_runtime": "d2f0088c4f3c1f570630334804a5a8f78e0105ac",
    "disposition": "diagnostic_complete_runtime_unchanged_candidate_held",
    "runtime_optimization_selected": False, "release_acceptance": False,
    "request_pair": {"plan": "execution/pair-001/plan.json", "commands": "execution/pair-001/pair-command.json",
                     "control": "execution/pair-001/control/request-result.json",
                     "capture": "execution/pair-001/capture/request-result.json",
                     "census": "execution/pair-001/capture/census.json", "requests": 2,
                     "request_status": "failed", "unchanged_full_p11": True,
                     "shared_operations": state["shared_operations"], "reach_operations": state["reach_work"]["operations"],
                     "categories": len(state["reach_work"]["counts"]),
                     "work_cache_entries": state["reach_work"]["cache_entries"],
                     "reference_cache_entries_post_cleanup": state["independent_arithmetic_cache_entries_post_cleanup"]},
    "neutrality": {"status": "passed", "analyzer": "execution/analysis-001/report.json",
                   "analyzer_sha256": analysis["analyzer_sha256"],
                   "checks": analysis["neutrality"]["check_count"],
                   "independent_review": "observations/independent-census-review.json",
                   "independent_neutrality_assertions": review["neutrality"]["assertions"],
                   "independent_census_assertions": review["census_assertion_count"],
                   "elapsed_neutrality_claimed": False},
    "finding": {"key_index": 36, "exact_time_seconds": "36/25", "carrier": 7,
                "frame": "rig.arms[\"right\"].forearm.frame", "phase": 0,
                "attempted_operation": "Add completed z-error and completed w-error; charge refused before arithmetic",
                "completed_comparison_records": 16, "available_centered_orientation_proofs": 2,
                "first_misses": {"unavailable_proof": 14, "actual_quaternion": 2},
                "whole_orientation_match": False, "claim_only_miss": False,
                "identical_completed_scalar": "w decode 3feb04bc00000000 to 442671/524288, donor4 and current7",
                "scalar_decode_retained_separately_in_existing_proof": False,
                "complete_request_saving_established": False},
    "unchanged_prior_evidence": {"checkpoint": 35, "original_recordings_passed": 24,
                                  "original_recordings_total": 28, "failed_cases": ["P11", "P16", "P23", "L03"],
                                  "focused_methods_passed": 29, "full_regression_methods_passed": 3093,
                                  "default_local_checks_passed": 7, "rerun_by_c036": False},
    "report": "checkpoint-036-census.md", "handoff": "HANDOFF-036.md",
    "next_scope": "checkpoint-036-next-scope.json", "next_scope_kind": "source_only_feasibility_derivation",
    "manifest_sha256": sha(manifest_path.read_bytes()),
    "archive": {"format": "ZIP_DEFLATED", "parts": parts, "bytes": len(joined),
                "sha256": sha(joined), "member_count": len(members)},
    "receipt_policy": "Packaging/recovery/documentation/publication receipts live outside this archive to avoid circular hashes. The enclosing commit and closing Issue26 comment identify publication; execution remains the separate immutable candidate."
}
write(destination / "checkpoint-036.json", checkpoint)
receipt = {"schema": "ontokin.checkpoint036-packaging/0.1", "status": "passed",
           "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
           "started_at": started_at, "finished_at": datetime.now(timezone.utc).isoformat(),
           "elapsed_seconds": time.monotonic() - started,
           "packager_sha256": sha(Path(__file__).read_bytes()), "member_count": len(members),
           "manifest_sha256": checkpoint["manifest_sha256"], "archive": checkpoint["archive"],
           "exact_membership": True, "member_hashes": True, "zip_crc": True,
           "source_executions_repeated": False, "release_acceptance": False}
write(args.receipt, receipt)
print(json.dumps({"status": "passed", "members": len(members), "archive_bytes": len(joined),
                  "archive_sha256": sha(joined), "parts": len(parts)}), flush=True)
