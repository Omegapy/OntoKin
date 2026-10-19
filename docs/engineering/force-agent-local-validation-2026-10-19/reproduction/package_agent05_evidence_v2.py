#!/usr/bin/env python3
"""Retain completed Agent/0.5 local-check attempts without altering their evidence.

Run only after an operator has observed the attempt's terminal process result.
The archive and member list are deterministic for identical source bytes.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def identity(data):
    return {"sha256": digest(data), "bytes": len(data)}


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Repeated JSON key: " + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON: " + value)))


def regular_read(root, name):
    relative = PurePosixPath(name)
    require(not relative.is_absolute() and relative.parts and ".." not in relative.parts,
            "Invalid retained relative path: " + name)
    path = root
    for part in relative.parts:
        path = path / part
        require(not path.is_symlink(), "Evidence symbolic link: " + str(path))
    require(path.is_file() and root.resolve() in path.resolve().parents,
            "Missing regular evidence file: " + str(path))
    return path.read_bytes()


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def inventory_hash(records):
    raw = json.dumps(records, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return digest(raw)


def test_execution(data):
    log = data.decode("utf-8")
    executions = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", log, re.MULTILINE)
    endings = re.findall(r"^(OK|FAILED)(?: \(([^\n]*)\))?$", log, re.MULTILINE)
    require(executions and endings, "Missing unittest completion in retained log")
    counts = {name.strip(): int(value) for name, value in re.findall(r"([a-z ]+)=(\d+)", endings[-1][1])}
    return {"tests_run": int(executions[-1][0]), "duration_seconds": float(executions[-1][1]),
            "unittest_status": endings[-1][0], "failures": counts.get("failures", 0),
            "errors": counts.get("errors", 0), "skips": counts.get("skipped", 0),
            "expected_failures": counts.get("expected failures", 0),
            "fixture_errors": re.findall(r"^ERROR: (setUpClass \([^\n]+\))$", log, re.MULTILINE)}


def audit_attempt(root, expected_head, expected_tree, expected_status, observed_exit, pip_bytes):
    members = {}
    def retain(name, expected=None):
        raw = regular_read(root, name)
        if expected is not None:
            for key, value in identity(raw).items():
                if key in expected:
                    require(value == expected[key], "Retained identity mismatch: " + name)
        members[name] = raw
        return decode(raw) if name.endswith(".json") else raw

    summary = retain("summary.json")
    require(summary.get("schema_version") == "ontokin.local-checks/0.1", "Wrong local-check schema")
    require(summary.get("status") == expected_status and expected_status in ("passed", "failed"),
            "The attempt is not complete with the expected terminal status")
    require(summary.get("finished_at") and summary.get("exit_code") == observed_exit,
            "Summary does not agree with the independently observed terminal exit")
    require((expected_status == "passed") == (observed_exit == 0), "Expected status and observed exit disagree")
    source = summary["git"]
    require(source.get("available") and (source["local_head"], source["local_tree"]) == (expected_head, expected_tree),
            "Summary has a different source commit/tree")
    require(source["tracked_worktree_status"] == "" and source["untracked_source_files"] == [],
            "This retention expects the identified clean source candidate")
    require(source["remote_head_verified"] is False, "Do not alter the driver's remote observation flag")
    for key in ("release_certified", "full_product_conformance_certified", "remote_checks_executed"):
        require(summary.get(key) is False, "Unexpected certification or hosted execution claim: " + key)
    require(summary.get("source_unchanged") is True, "Source inventory changed during the attempt")
    before = retain("source-before.json", summary["source_inventory"])
    after = retain("source-after.json")
    require(before == after, "The before/after input inventories differ")
    require(before["file_count"] == len(before["files"]) and before["sha256"] == inventory_hash(before["files"]),
            "The source inventory's own count/hash differs")
    require(summary["source_inventory"]["inventory_sha256"] == before["sha256"], "Summary inventory hash differs")
    source_files = {item["path"]: item for item in before["files"]}
    require(len(source_files) == len(before["files"]), "Duplicate source inventory members")
    workspace = root / "workspace"
    for name, declared in source_files.items():
        require(identity(regular_read(workspace, name)) == {key: declared[key] for key in ("sha256", "bytes")},
                "Isolated execution input differs from inventory: " + name)
    runtime_digest = hashlib.sha256()
    for name in sorted(n for n in source_files if n.startswith("ontokin/") and n.count("/") == 1 and n.endswith(".py")):
        runtime_digest.update(Path(name).name.encode() + b"\0" + regular_read(workspace, name) + b"\0")
    runtime_sha = "sha256:" + runtime_digest.hexdigest()
    if summary.get("workspace_git", {}).get("available"):
        require(summary.get("git_revision_unchanged") is True, "Final source revision was not stable")
        for key in ("workspace_git", "git_after"):
            require((summary[key].get("local_head"), summary[key].get("local_tree")) == (expected_head, expected_tree),
                    "Final source/workspace Git provenance differs: " + key)
        environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        environment.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                           GIT_CEILING_DIRECTORIES=str(workspace.parent), GIT_NO_REPLACE_OBJECTS="1")
        git = subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "HEAD", "HEAD^{tree}"],
                                      text=True, timeout=10, env=environment).splitlines()
        require(git == [expected_head, expected_tree], "Retained workspace Git objects differ from final provenance")
    steps = summary["steps"]
    require([s["id"] for s in steps] == summary["planned_steps"], "Missing or reordered planned steps")
    require(len({s["id"] for s in steps}) == len(steps), "Duplicate step identities")
    statuses, executions = {}, {}
    for step in steps:
        require(step["status"] in ("passed", "failed", "blocked", "unavailable"), "Nonterminal step")
        require(all(statuses.get(name) == "passed" for name in step["requires"]) or step["status"] == "blocked",
                "Failed prerequisite did not block dependent execution")
        statuses[step["id"]] = step["status"]
        log = retain(step["log"], step["log_identity"])
        for report in step["reports"]:
            retain(report["path"], report)
        if step["id"] in ("unit-tests", "force-agent-tests"):
            parsed = test_execution(log)
            require(parsed["tests_run"] == step["test_execution"]["tests_run"] and
                    parsed["skips"] == step["test_execution"]["skipped"], "Unittest counts differ from summary")
            if step["status"] == "passed":
                require(parsed["tests_run"] > 0 and parsed["unittest_status"] == "OK" and
                        not any(parsed[name] for name in ("failures", "errors", "skips", "expected_failures")),
                        "Incomplete cohort was marked passed")
            executions[step["id"]] = parsed
    require((all(s == "passed" for s in statuses.values())) == (expected_status == "passed"),
            "Overall result does not agree with the actual step outcomes")
    for directory in ("logs", "reports"):
        for path in sorted((root / directory).rglob("*")):
            if path.is_file():
                retain(path.relative_to(root).as_posix())
    workflow_name = "artifacts/force-agent-workflow/workflow.json"
    workflow = retain(workflow_name)
    base = "artifacts/force-agent-workflow/"
    for number, exchange in enumerate(workflow["exchanges"], 1):
        require(exchange["sequence"] == number, "Noncontiguous actual exchange trace")
        request = retain(base + exchange["request_file"], {"sha256": exchange["request_sha256"]})
        response = retain(base + exchange["response_file"], {"sha256": exchange["response_sha256"]})
        require(all(request[k] == response[k] for k in ("schema_version", "project_id", "request_id", "operation")),
                "Request/response identity mismatch")
    for snapshot in workflow["snapshots"]:
        retain(base + snapshot["bundle_file"], {"sha256": snapshot["bundle_sha256"]})
    unreferenced_files = []
    for directory in ("exchanges", "snapshots"):
        for path in sorted((root / base / directory).rglob("*")):
            if path.is_file():
                name = path.relative_to(root).as_posix()
                if name not in members:
                    unreferenced_files.append(name[len(base):])
                retain(name)
    sample_roles = sum("/sample/" in item["role"] for item in workflow["exchanges"])
    require(workflow["schema_version"] == "ontokin.force-agent-workflow/0.1" and
            workflow["protocol"] == "ontokin.agent/0.5", "Wrong retained Force workflow protocol")
    require(workflow["implementation"]["source_code_sha256"] == runtime_sha, "Runtime input identity differs")
    for field, name in (("writer_sha256", "tools/build_force_agent_demo.py"),):
        require(workflow[field] == source_files[name]["sha256"], "Workflow writer identity differs")
    for name, expected in workflow["fixture_inputs"].items():
        require(source_files["docs/language-design/force-v0.1/" + name]["sha256"] == expected, "Force fixture input differs")
    workflow_result = {"workflow_manifest_status": workflow["status"],
        "independent_semantic_schema_audit_status": statuses["force-agent-audit"],
        "workflow_sha256": digest(members[workflow_name]), "implementation": workflow["implementation"],
        "exchanges": len(workflow["exchanges"]), "source_snapshots": len(workflow["snapshots"]),
        "recorded_sample_exchanges": sample_roles, "recorded_pair_snapshot_hashes_checked": True,
        "unreferenced_files_retained": unreferenced_files, "force_projections_schema_checked": None}
    if statuses["force-agent-audit"] == "passed":
        force_audit = decode(members["reports/force-agent-audit.json"])
        require(workflow["status"] == "recorded" and statuses["force-agent-build"] == "passed" and
                not unreferenced_files, "Passing audit requires a completed workflow without unreferenced output")
        require(force_audit["status"] == "passed" and force_audit["workflow_sha256"] == digest(members[workflow_name]),
                "Independent audit does not bind the actual workflow")
        require(force_audit["full_force_release_complete"] is False and force_audit["destination_validated"] is False,
                "Force checkpoint cannot certify delivery or the full force release")
        require(workflow["implementation"] == force_audit["implementation"], "Audit runtime identity differs")
        require(len(workflow["exchanges"]) == workflow["exchange_count"] == force_audit["exchanges"] and
                len(workflow["snapshots"]) == workflow["snapshot_count"] == force_audit["source_snapshots"] and
                sample_roles == workflow["sample_count"] == force_audit["predetermined_samples"],
                "Completed Force workflow counts differ")
        require(force_audit["verifier_sha256"] == source_files["tools/verify_force_agent_workflow.py"]["sha256"],
                "Independent verifier identity differs")
        for name, expected in force_audit["schema_inputs"].items():
            require(source_files["docs/language-design/" + name]["sha256"] == expected, "Schema input differs")
        require(force_audit["fixture_inputs"] == workflow["fixture_inputs"], "Fixture bindings differ")
        workflow_result.update({key: force_audit[key] for key in ("source_cases", "predetermined_samples",
                                                                 "force_projections_schema_checked")})
        workflow_result["complete_workflow"] = True
    else:
        require(expected_status == "failed" and statuses["force-agent-build"] == "failed" and
                statuses["force-agent-audit"] == "blocked" and workflow["status"] == "failed" and
                "reports/force-agent-audit.json" not in members,
                "Partial workflow retention requires a failed builder and a blocked, absent independent audit")
        workflow_result.update(complete_workflow=False, failure=workflow["failure"],
            limitation="Only recorded pairs and snapshots have checked hash closure; the workflow is incomplete and the independent Force audit did not execute.")
    preflight = decode(members["reports/force-agent-tools.json"])
    requirements = regular_read(workspace, "tools/force-agent-verification-requirements.txt")
    require(identity(requirements) == preflight["requirements_identity"], "Pinned requirements preflight differs")
    pins = {}
    for line in requirements.decode().splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            name, version = line.split("==")
            pins[normalized(name)] = version
    observed = {normalized(d["name"]): d["installed"] for d in preflight["dependencies"]}
    pip_report = decode(pip_bytes)
    downloaded = {normalized(d["metadata"]["name"]): d["metadata"]["version"] for d in pip_report["install"]}
    require(preflight["status"] == "passed" and not preflight["errors"] and pins == observed == downloaded,
            "Prepared, installed and pinned dependency versions differ")
    require(preflight["python_executable"] == summary["environment"]["python_executable"] and
            preflight["python"] == summary["environment"]["python"] and
            summary["environment"]["python"].startswith(pip_report["environment"]["python_full_version"]),
            "Prerequisite installation and execution interpreters differ")
    audit = {"schema_version": "ontokin.local-evidence-retention/0.1", "retention_integrity": "passed",
             "attempt_status": expected_status, "observed_process_exit_code": observed_exit,
             "source_commit": expected_head, "source_tree": expected_tree, "source_inventory": before["sha256"],
             "source_file_count": before["file_count"], "source_inventory_bytes_checked_against_isolated_workspace": True,
             "driver_git_record": source, "workspace_git_record": summary.get("workspace_git"),
             "environment": summary["environment"], "selected_roles": summary["selected_roles"],
             "started_at": summary["started_at"], "finished_at": summary["finished_at"],
             "duration_seconds": summary["duration_seconds"], "step_statuses": statuses,
             "test_executions": executions, "pending_external_cases": summary["pending_external_cases"],
             "force_workflow": workflow_result,
             "shared_prerequisites": {"pip-install.json": identity(pip_bytes),
                 "force-agent-verification-requirements.txt": identity(requirements)},
             "excluded": ["workspace/ (including .git and implementation copies)",
                 "artifacts/force-agent-workflow/service-store/ (mutable SQLite)",
                 "installed dependencies and caches", "earlier historical recovery archive"],
             "limitations": ["Integrity verification preserves each attempt's result; it does not turn a failed attempt into success.",
                 "The raw driver reports remote_head_verified:false; independently observed remote revisions are supplemental evidence.",
                 "Only the recorded Python interpreter and selected roles were executed; other Python versions and platforms remain unverified.",
                 "These core/force-agent runs do not execute the full visual role, validate GLB/0.5, or certify F01-F12 or the complete product.",
                 "This packager checks identities and hash closure only. A retained semantic/schema audit is evidence only when its own runner step actually passed; a blocked audit supplies no projection or conformance result.",
                 "The pip report retains observed package download URLs and hashes; the packager does not download packages again."],
             "release_certified": False, "full_product_conformance_certified": False,
             "packager_sha256": digest(Path(__file__).read_bytes())}
    return members, audit, requirements


def archive_bytes(members):
    buffer = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=buffer, mode="wb", compresslevel=9, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, data in sorted(members.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def write_identical_or_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.is_file() and not path.is_symlink() and path.read_bytes() == data,
                "Refusing to replace different retained evidence: " + str(path))
        return
    with path.open("xb") as stream:
        stream.write(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-tree", required=True)
    parser.add_argument("--expected-status", choices=("passed", "failed"), required=True)
    parser.add_argument("--observed-exit-code", type=int, required=True)
    parser.add_argument("--pip-report", type=Path, required=True)
    parser.add_argument("--supplemental", type=Path, action="append", default=[])
    args = parser.parse_args()
    require(re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.label), "Unsafe evidence label")
    root, output = args.run_dir.resolve(), args.output_dir.resolve()
    require(root != output and root not in output.parents, "Retention output must be outside the original attempt")
    pip_bytes = args.pip_report.read_bytes()
    members, audit, requirements = audit_attempt(root, args.expected_head, args.expected_tree,
                                                args.expected_status, args.observed_exit_code, pip_bytes)
    supplemental = {}
    for path in args.supplemental:
        require(path.name not in supplemental and path.is_file() and not path.is_symlink(), "Invalid supplemental record")
        supplemental[path.name] = path.read_bytes()
        decode(supplemental[path.name])
    audit["supplemental_records"] = {name: identity(data) for name, data in sorted(supplemental.items())}
    audit_bytes = encode(audit)
    for name, data in members.items():
        require(regular_read(root, name) == data, "Evidence changed during retention: " + name)
    members["retention-audit.json"] = audit_bytes
    archive = archive_bytes(members)
    require(archive == archive_bytes(members), "Archive construction is not reproducible")
    member_records = [{"path": name, **identity(data)} for name, data in sorted(members.items())]
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as reopened:
        checked = []
        for member in reopened.getmembers():
            require(member.isfile() and not member.issym() and not member.islnk(), "Archive contains a nonregular member")
            data = reopened.extractfile(member).read()
            checked.append({"path": member.name, **identity(data)})
        require(checked == member_records, "Reopened archive member hashes differ")
    archive_name = args.label + ".tar.gz"
    manifest = {"schema_version": "ontokin.local-evidence-archive/0.1", "attempt_status": args.expected_status,
                "source_commit": args.expected_head, "source_tree": args.expected_tree,
                "archive": {"path": archive_name, **identity(archive)}, "member_count": len(member_records),
                "uncompressed_bytes": sum(m["bytes"] for m in member_records), "members": member_records,
                "deterministic_rebuild_verified": True, "reopened_archive_verified": True,
                "shared_prerequisites": audit["shared_prerequisites"], "supplemental_records": audit["supplemental_records"]}
    write_identical_or_new(output / "prerequisites/pip-install.json", pip_bytes)
    write_identical_or_new(output / "prerequisites/force-agent-verification-requirements.txt", requirements)
    for name, data in supplemental.items():
        write_identical_or_new(output / "supplemental" / name, data)
    write_identical_or_new(output / archive_name, archive)
    write_identical_or_new(output / (args.label + ".members.json"), encode(manifest))
    write_identical_or_new(output / (args.label + ".retention-audit.json"), audit_bytes)
    print(json.dumps({"archive": str(output / archive_name), **manifest["archive"],
                      "member_count": manifest["member_count"], "uncompressed_bytes": manifest["uncompressed_bytes"],
                      "attempt_status": args.expected_status, "source_commit": args.expected_head,
                      "step_counts": dict(Counter(audit["step_statuses"].values())),
                      "test_executions": audit["test_executions"]}, indent=2))


if __name__ == "__main__":
    main()
