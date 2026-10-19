#!/usr/bin/env python3
"""Retain and verify completed resulting-main evidence using the standard library.

Packaging requires --source-dir and --repository. Verification needs only the
archive, its manifest, and the plain verification record in --output-dir.
"""
from __future__ import annotations

import argparse
from datetime import datetime
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


def identity(data):
    return {"sha256": "sha256:" + hashlib.sha256(data).hexdigest(), "bytes": len(data)}


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


def safe_name(name):
    path = PurePosixPath(name)
    require(path.parts and not path.is_absolute() and ".." not in path.parts, "Unsafe relative path")
    require(not any(part in (".git", "__pycache__", "service-store") for part in path.parts),
            "Excluded mutable or secret store path")
    return path


def read_regular(root, name):
    path = root
    for part in safe_name(name).parts:
        path /= part
        require(not path.is_symlink(), "Symbolic link in retained evidence")
    require(path.is_file(), "Missing regular evidence file: " + name)
    data = path.read_bytes()
    require(not data.startswith(b"SQLite format 3\0"), "SQLite bytes cannot be retained")
    return data


def checked(members, name, expected):
    data = members[name]
    for key, value in identity(data).items():
        if key in expected:
            require(value == expected[key], "Hash or size mismatch: " + name)
    return decode(data) if name.endswith(".json") else data


def check_content(members):
    verification = decode(members["verification.json"])
    require(verification["record_type"] == "ontokin.agent05-resulting-main/0.1" and
            verification["status"] == "passed", "A completed passing resulting-main record is required")
    require(verification["working_tree_clean"] and verification["head_unchanged"] and
            verification["runtime_or_fixture_changes_since_tested_candidate"] is False,
            "Resulting-main input stability was not established")
    require(verification["release_certified"] is False and verification["full_force_release_complete"] is False,
            "Resulting-main checks do not certify the full release")
    for record in verification["inputs"].values():
        require(record["tested"] == record["main"], "Tested/main component input identities differ")
    expected_steps = ["runner-tests", "source", "agent", "force-workflow", "force-audit", "documents"]
    require([step["id"] for step in verification["steps"]] == expected_steps, "Unexpected resulting-main check set")
    for step in verification["steps"]:
        require(step["returncode"] == 0, "A resulting-main subprocess did not pass")
        checked(members, step["log"], step["log_identity"])
    for name, expected in verification["reports"].items():
        checked(members, name, expected)
    runner_log = members["logs/runner-tests.log"].decode()
    matches = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s\n\n(OK|FAILED)([^\n]*)$", runner_log, re.MULTILINE)
    require(len(matches) == 1 and matches[0][2:] == ("OK", "") and int(matches[0][0]) > 0,
            "Runner test log must complete without skips, failures, or expected failures")
    workflow_name = "workflow/workflow.json"
    workflow = decode(members[workflow_name])
    audit = decode(members["reports/force-audit.json"])
    require(workflow["status"] == "recorded" and audit["status"] == "passed" and
            audit["workflow_sha256"] == identity(members[workflow_name])["sha256"],
            "The actual independent audit does not bind a completed workflow")
    require(workflow["schema_version"] == "ontokin.force-agent-workflow/0.1" and
            workflow["protocol"] == "ontokin.agent/0.5", "Unexpected workflow protocol")
    require(audit["destination_validated"] is False and audit["full_force_release_complete"] is False,
            "The Force audit cannot certify a destination or the full release")
    require(workflow["implementation"] == audit["implementation"] and
            workflow["fixture_inputs"] == audit["fixture_inputs"], "Runtime or fixture bindings differ")
    required = {"verification.json", workflow_name}
    required.update(step["log"] for step in verification["steps"])
    required.update(verification["reports"])
    for sequence, exchange in enumerate(workflow["exchanges"], 1):
        require(exchange["sequence"] == sequence, "Actual exchange sequence is not contiguous")
        names = ["workflow/" + exchange[key + "_file"] for key in ("request", "response")]
        require(not any(name in required for name in names) and names[0] != names[1], "Repeated exchange member")
        request, response = [checked(members, name, {"sha256": exchange[key + "_sha256"]})
                             for name, key in zip(names, ("request", "response"))]
        require(all(request[key] == response[key] for key in ("schema_version", "project_id", "request_id", "operation")),
                "Actual request/response identity differs")
        required.update(names)
    for snapshot in workflow["snapshots"]:
        name = "workflow/" + snapshot["bundle_file"]
        require(name not in required, "Repeated snapshot member")
        checked(members, name, {"sha256": snapshot["bundle_sha256"]})
        required.add(name)
    require(required == set(members), "Missing or unreferenced retained output")
    samples = sum("/sample/" in item["role"] for item in workflow["exchanges"])
    require(len(workflow["exchanges"]) == workflow["exchange_count"] == audit["exchanges"] and
            len(workflow["snapshots"]) == workflow["snapshot_count"] == audit["source_snapshots"] and
            samples == workflow["sample_count"] == audit["predetermined_samples"] and
            len(workflow["source_fixtures"]) == audit["source_cases"], "Workflow counts differ")
    source = decode(members["reports/source.json"])["summary"]
    agent = decode(members["reports/agent.json"])["summary"]
    require(source["failed"] == agent["failed"] == 0 and source["passed"] == source["total"] and
            agent["passed"] == agent["total"], "Source or original Agent conformance did not pass")
    forbidden_keys = {"password", "access_token", "refresh_token", "authorization", "api_key", "private_key",
                      "cursor_secret", "client_secret", "secret", "secret_key", "token"}
    pagination_fields = 0
    def inspect(value):
        nonlocal pagination_fields
        if isinstance(value, dict):
            for key, item in value.items():
                require(key.lower() not in forbidden_keys, "Potential authentication or signing secret field")
                if key in ("cursor", "next_cursor") and item is not None:
                    pagination_fields += 1
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
    for name, data in members.items():
        safe_name(name)
        require(not data.startswith(b"SQLite format 3\0") and
                re.search(rb"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----|\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}", data) is None,
                "Potential database or authentication material")
        if name.endswith(".json"):
            inspect(decode(data))
    elapsed = (datetime.fromisoformat(verification["finished_at"]) -
               datetime.fromisoformat(verification["started_at"])).total_seconds()
    return {"checks_passed": len(expected_steps), "runner_tests": int(matches[0][0]),
        "runner_test_duration_seconds": float(matches[0][1]), "runner_test_skips": 0,
        "elapsed_seconds": elapsed, "source_cases": source["passed"], "source_assertions": source["assertions"],
        "original_agent_cases": agent["passed"], "force_workflow": {key: audit[key] for key in
            ("exchanges", "source_snapshots", "source_cases", "predetermined_samples", "force_projections_schema_checked",
             "implementation", "workflow_sha256")}, "non_null_protocol_pagination_fields": pagination_fields}


def deterministic_archive(members):
    output = io.BytesIO()
    with gzip.GzipFile(filename="", fileobj=output, mode="wb", compresslevel=9, mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, data in sorted(members.items()):
                info = tarfile.TarInfo(name)
                info.size, info.mode, info.mtime = len(data), 0o644, 0
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def reopen(raw):
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for item in archive.getmembers():
            safe_name(item.name)
            require(item.isfile() and not item.issym() and not item.islnk() and item.name not in members,
                    "Nonregular or duplicate archive member")
            require((item.uid, item.gid, item.mtime, item.mode, item.uname, item.gname) == (0, 0, 0, 0o644, "", ""),
                    "Noncanonical archive metadata")
            members[item.name] = archive.extractfile(item).read()
    return members


def git_bytes(repository, *args):
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update(GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
                       GIT_NO_REPLACE_OBJECTS="1", GIT_NO_LAZY_FETCH="1", GIT_CEILING_DIRECTORIES=str(repository.parent))
    return subprocess.check_output(["git", "-c", "core.fsmonitor=false", "-C", str(repository), *args],
                                   env=environment, timeout=10)


def check_source(repository, members):
    record = decode(members["verification.json"])
    main, tested = record["main_commit"], record["tested_code_commit"]
    require(all(re.fullmatch(r"[0-9a-f]{40}", revision) for revision in (main, tested)), "Malformed commit identity")
    require(Path(git_bytes(repository, "rev-parse", "--show-toplevel").decode().strip()).resolve() == repository,
            "The supplied source is not the actual repository root")
    require(git_bytes(repository, "rev-parse", main + "^{tree}").decode().strip() == record["main_tree"],
            "Recorded resulting-main commit tree differs")
    for name, identities in record["inputs"].items():
        for revision, key in ((main, "main"), (tested, "tested")):
            require(git_bytes(repository, "rev-parse", revision + ":" + name).decode().strip() == identities[key],
                    "Recorded source component tree differs")
    workflow = decode(members["workflow/workflow.json"])
    audit = decode(members["reports/force-audit.json"])
    for name, expected in (("tools/build_force_agent_demo.py", workflow["writer_sha256"]),
                           ("tools/verify_force_agent_workflow.py", audit["verifier_sha256"])):
        require(identity(git_bytes(repository, "show", main + ":" + name))["sha256"] == expected,
                "Recorded builder/verifier bytes differ from main")
    for prefix, records in (("docs/language-design/force-v0.1/", workflow["fixture_inputs"]),
                            ("docs/language-design/", audit["schema_inputs"])):
        for name, expected in records.items():
            require(identity(git_bytes(repository, "show", main + ":" + prefix + name))["sha256"] == expected,
                    "Recorded fixture/schema bytes differ from main")
    digest = hashlib.sha256()
    names = git_bytes(repository, "ls-tree", "-r", "--name-only", main, "ontokin").decode().splitlines()
    for name in sorted(name for name in names if name.count("/") == 1 and name.endswith(".py")):
        digest.update(Path(name).name.encode() + b"\0" + git_bytes(repository, "show", main + ":" + name) + b"\0")
    require("sha256:" + digest.hexdigest() == workflow["implementation"]["source_code_sha256"],
            "Recorded runtime digest differs from resulting main")


def write_identical_or_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.is_file() and not path.is_symlink() and path.read_bytes() == data,
                "Refusing to replace different retained evidence: " + str(path))
    else:
        with path.open("xb") as stream:
            stream.write(data)


def verify_saved(output):
    manifest = decode(read_regular(output, "resulting-main-manifest.json"))
    require(manifest["record_type"] == "ontokin.resulting-main-evidence-archive/0.1", "Unexpected archive manifest")
    raw = read_regular(output, manifest["archive"]["path"])
    require(identity(raw) == {key: manifest["archive"][key] for key in ("sha256", "bytes")}, "Archive identity differs")
    members = reopen(raw)
    expected = [{"path": name, **identity(data)} for name, data in sorted(members.items())]
    require(expected == manifest["members"] and len(expected) == manifest["member_count"], "Member manifest differs")
    require(sum(len(data) for data in members.values()) == manifest["uncompressed_bytes"], "Byte count differs")
    require(deterministic_archive(members) == raw, "Deterministic archive reconstruction differs")
    require(read_regular(output, "resulting-main-verification.json") == members["verification.json"], "Plain record differs")
    require(check_content(members) == manifest["retention_checks"], "Retained content verification differs")
    require(identity(Path(__file__).read_bytes())["sha256"] == manifest["packager_sha256"], "Exact packager is required")
    record = decode(members["verification.json"])
    require((manifest["main_commit"], manifest["main_tree"], manifest["tested_code_commit"]) ==
            (record["main_commit"], record["main_tree"], record["tested_code_commit"]), "Revision bindings differ")
    return {"status": "passed", "archive": manifest["archive"], "member_count": manifest["member_count"],
        "uncompressed_bytes": manifest["uncompressed_bytes"], "main_commit": manifest["main_commit"],
        "main_tree": manifest["main_tree"], "retention_checks": manifest["retention_checks"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    output = args.output_dir.resolve()
    if not args.verify_only:
        require(args.source_dir is not None and args.repository is not None, "Packaging requires source and repository")
        source = args.source_dir.resolve()
        require(source != output and source not in output.parents, "Output must be outside the observed run")
        members = {"verification.json": read_regular(source, "verification.json")}
        for directory in ("logs", "reports", "workflow/exchanges", "workflow/snapshots"):
            for path in sorted((source / directory).rglob("*")):
                if path.is_file():
                    name = path.relative_to(source).as_posix()
                    members[name] = read_regular(source, name)
        members["workflow/workflow.json"] = read_regular(source, "workflow/workflow.json")
        checks = check_content(members)
        check_source(args.repository.resolve(), members)
        for name, data in members.items():
            require(read_regular(source, name) == data, "Original evidence changed during retention")
        raw = deterministic_archive(members)
        require(reopen(raw) == members and deterministic_archive(reopen(raw)) == raw,
                "Archive reopening or deterministic reconstruction differs")
        record = decode(members["verification.json"])
        manifest = {"record_type": "ontokin.resulting-main-evidence-archive/0.1", "status": "retained",
            "main_commit": record["main_commit"], "main_tree": record["main_tree"],
            "tested_code_commit": record["tested_code_commit"], "source_objects_checked_at_packaging": True,
            "archive": {"path": "resulting-main.tar.gz", **identity(raw)}, "member_count": len(members),
            "uncompressed_bytes": sum(len(data) for data in members.values()),
            "members": [{"path": name, **identity(data)} for name, data in sorted(members.items())],
            "retention_checks": checks, "reopened_archive_verified": True, "deterministic_rebuild_verified": True,
            "packager_sha256": identity(Path(__file__).read_bytes())["sha256"],
            "security_and_scope": [
                "Exact protocol messages and snapshots are retained without redaction to preserve their original hashes.",
                "Protocol pagination cursors are reproducible local test records, not repository authentication credentials.",
                "The mutable workflow/service-store directory, SQLite database, signing secrets, Git metadata and caches are excluded.",
                "Selected JSON fields and common private-key/authentication-token patterns were checked; this is a bounded retention check, not a general secret-scanner certification.",
                "Only the recorded six resulting-main checks ran here; the 753-test complete regression remains separately retained on the identical code/input component trees.",
                "The retained semantic/schema audit was executed by the original process; packaging checks source identities, recorded results and hash closure without rerunning project tests.",
                "These checks do not certify GLB/0.5, F01-F12, external destination validation or the complete OntoKin goal."],
            "release_certified": False, "full_force_release_complete": False}
        write_identical_or_new(output / "resulting-main.tar.gz", raw)
        write_identical_or_new(output / "resulting-main-manifest.json", encode(manifest))
        write_identical_or_new(output / "resulting-main-verification.json", members["verification.json"])
    print(json.dumps(verify_saved(output), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
