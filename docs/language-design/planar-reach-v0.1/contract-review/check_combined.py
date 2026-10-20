#!/usr/bin/env python3
"""Run fresh combined proposal checks with immutable input hashes and raw logs."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[4]
PROPOSAL = ROOT / "docs/language-design/planar-reach-v0.1"
ORIGINAL = "90ea94d7856ec545953549e3ab568bde61298cd7"
AMENDED_ORIGINAL_PATHS = {
    "docs/language-design/OK-LANG-006-reusable-planar-reach-actions.md",
    "docs/language-design/planar-reach-v0.1/README.md",
    "docs/language-design/planar-reach-v0.1/review-decisions.md",
    "docs/language-design/planar-reach-v0.1/sampling-bound.md",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def member(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path":str(path.relative_to(ROOT)), "bytes":len(raw), "sha256":sha(raw)}


def inputs() -> list[dict]:
    paths = []
    for path in PROPOSAL.rglob("*"):
        if not path.is_file() or path.suffix == ".pyc" or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(PROPOSAL)
        if len(rel.parts) > 1 and rel.parts[0] == "contract-review" and rel.parts[1].startswith("checks-"):
            continue
        paths.append(path)
    paths += [ROOT / "docs/language-design/OK-LANG-006-reusable-planar-reach-actions.md",
              ROOT / "docs/maintenance/reorganization-2026-10-17/verify_reorganization.py",
              ROOT / "tools/force-agent-verification-requirements.txt", ROOT / "ontokin/json_limits.py"]
    for name in ["agent-v0.5/request.schema.json", "agent-v0.5/response.schema.json",
                 "agent-v0.2/diagnostic.schema.json", "construction-v0.1/bundle.schema.json",
                 "force-v0.1/forces.schema.json", "impulse-v0.1/impulses.schema.json"]:
        paths.append(PROPOSAL.parent / name)
    return [member(path) for path in sorted(set(paths))]


def original_preservation() -> dict:
    paths = git("ls-tree", "-r", "--name-only", ORIGINAL, "--",
                "docs/language-design/OK-LANG-006-reusable-planar-reach-actions.md",
                "docs/language-design/planar-reach-v0.1").splitlines()
    if len(paths) != 103:
        raise ValueError("original proposal inventory changed")
    same, amended, changed = [], [], []
    for name in paths:
        original = subprocess.check_output(["git", "show", ORIGINAL + ":" + name], cwd=ROOT)
        current = (ROOT / name).read_bytes()
        row = {"path":name,"original_bytes":len(original),"original_sha256":sha(original),
               "current_bytes":len(current),"current_sha256":sha(current)}
        if current == original:
            same.append(row)
        elif name in AMENDED_ORIGINAL_PATHS:
            amended.append(row)
        else:
            changed.append(row)
    return {"original_commit":ORIGINAL,"original_file_count":len(paths),
            "byte_identical_count":len(same),"explicitly_amended_count":len(amended),
            "unexpected_changes":changed,"unchanged":same,"explicit_amendments":amended,
            "status":"passed" if not changed and len(same) == 99 and len(amended) == 4 else "failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir",type=Path,required=True)
    args = parser.parse_args(); output = args.output_dir.resolve()
    if output.exists():
        raise SystemExit("Refusing to overwrite prior combined evidence: " + str(output))
    if not output.is_relative_to(PROPOSAL / "contract-review") or not output.name.startswith("checks-"):
        raise SystemExit("Output must be a new contract-review/checks-* directory")
    output.mkdir(parents=True)
    before = inputs(); head = git("rev-parse", "HEAD"); tree = git("rev-parse", "HEAD^{tree}")
    started = now(); preservation = original_preservation()
    (output / "original-preservation.json").write_text(json.dumps(preservation,indent=2) + "\n")
    prefix = "docs/language-design/planar-reach-v0.1/"
    rebuilt = output / "amendments-rebuilt"
    steps = [
        ("amendment_reproduction", [prefix+"author_draft2_amendments.py", "--output-dir", str(rebuilt)]),
        ("original_fixtures", [prefix+"verify_fixtures.py"]),
        ("bounded_rounding", [prefix+"verify_rounding.py", "--output", str(output/"rounding.json")]),
        ("quantization_contract", [prefix+"verify_quantization_contract.py", "--output", str(output/"quantization.json")]),
        ("supplement_reproduction", [prefix+"draft2-supplements/author_supplements.py"]),
        ("lifecycle_protocol", [prefix+"draft2-supplements/verify_supplements.py"]),
        ("recording_probe_bindings", [prefix+"draft2-supplements/verify_recording_probes.py"]),
        ("agent_schemas", [prefix+"agent-review/check_schemas.py", "--output", str(output/"agent-schemas.json"),
                           "--supplements-dir", str(PROPOSAL/"draft2-supplements")]),
        ("documentation_preservation", ["docs/maintenance/reorganization-2026-10-17/verify_reorganization.py",
                                        "--json-output",str(output/"documentation.json")]),
    ]
    records = []
    for index, (name, arguments) in enumerate(steps, 1):
        command = [sys.executable, *arguments]
        start = now(); tick = time.monotonic()
        result = subprocess.run(command,cwd=ROOT,capture_output=True)
        logbase = output / f"{index:02d}-{name}"
        stdout, stderr = logbase.with_suffix(".stdout.log"), logbase.with_suffix(".stderr.log")
        stdout.write_bytes(result.stdout); stderr.write_bytes(result.stderr)
        validation_error = None
        if name == "amendment_reproduction" and result.returncode == 0:
            for filename in ["draft2-amendments.json","profile-draft2.json","requirements-draft2.json"]:
                if (rebuilt/filename).read_bytes() != (PROPOSAL/filename).read_bytes():
                    validation_error = "reproduced bytes differ: " + filename
                    break
        record = {"name":name,"command":command,"cwd":str(ROOT),"started_at":start,"finished_at":now(),
                  "elapsed_seconds":time.monotonic()-tick,"exit_code":result.returncode,
                  "post_execution_validation_error":validation_error,
                  "status":"passed" if result.returncode == 0 and validation_error is None else "failed",
                  "stdout":member(stdout),"stderr":member(stderr)}
        records.append(record)
        print(json.dumps({"stage":name,"status":record["status"],"exit_code":result.returncode}),flush=True)
    after = inputs(); final_head = git("rev-parse", "HEAD")
    passed = (preservation["status"] == "passed" and before == after and head == final_head
              and all(row["status"] == "passed" for row in records))
    report = {"schema_version":"ontokin.reach-combined-contract-check/0.2","status":"passed" if passed else "failed",
              "scope":"fresh reconstructed proposal checks, not adoption or runtime/release acceptance",
              "started_at":started,"finished_at":now(),"source_commit":head,"source_tree":tree,
              "source_head_after":final_head,"input_identity_stable":before==after,
              "python":sys.version,"executable":sys.executable,"platform":platform.platform(),
              "inputs":before,"input_count":len(before),"stages":records,
              "preservation_report":member(output/"original-preservation.json"),
              "schema_manifest_path_bases":{"members":"docs/language-design/planar-reach-v0.1/schema-drafts",
                  "inherited_inputs":"docs/language-design/planar-reach-v0.1"},
              "actual_runtime_agent_sqlite_export_browser_suite_or_archive_executed":False,
              "lost_checks_reused":False,"whole_goal_complete":False}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"stages_passed":sum(r["status"]=="passed" for r in records),
                      "stages":len(records),"inputs":len(before),"unchanged_original_files":preservation["byte_identical_count"],
                      "explicit_original_prose_amendments":preservation["explicitly_amended_count"],
                      "input_identity_stable":before==after,"report":str(output/"report.json")}),flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
