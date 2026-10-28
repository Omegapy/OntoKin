"""Independently inspect checkpoint 027 without importing product code.

Reads an existing multipart ZIP in memory, preserved raw evidence, and local
Git objects. It never extracts or creates an archive, runs tests, edits Git,
or makes a live network request. The sole output is the requested audit JSON.
"""
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import statistics
import subprocess
import traceback
import zipfile
import zlib


CONTROL = "f59da3cbca337cad2b436617b5a59f82348d223e"
CONTROL_TREE = "5172525992364999d02391575cda02cfbe98c19a"
CANDIDATE = "64e888a769b3ac7c4024b9fd96bd331b8e39087c"
CANDIDATE_TREE = "4603d083217173136f9b978bc9c4a3787e5c6d3e"
ACCEPTED = "327e778cece3bb292f3e64751506dff364e4ee87"
PUBLISHED = "03c8dc68f7c9c404704511e0c5e20742247dd418"
BASE = "docs/engineering/reach-recording-validation-2026-10-23"
SOURCE_BASE = "docs/language-design/planar-reach-v0.1"
CASES = [f"P{number:02d}" for number in range(1, 24)] + ["P25", "P26", "L01", "L02", "L03"]
FAILED = ["P09", "P11", "P16", "P23", "L03"]
PREFIX_COSTS = {"P09": (39606, 35473), "P11": (66762, 60039), "L03": (35660, 31427)}
RUNS = {
    "control-original28": (CONTROL, CONTROL_TREE, 1),
    "candidate-focused-001": (CANDIDATE, CANDIDATE_TREE, 0),
    "candidate-controls-001": (CANDIDATE, CANDIDATE_TREE, 1),
    "candidate-controls-other-001": (CANDIDATE, CANDIDATE_TREE, 1),
}
CHANGED = {"ontokin/reach_conformance.py", "tests/test_reach_certificate_second_quarter.py",
           "docs/engineering/reach-certificate-second-quarter.md"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def bare(value):
    return value.removeprefix("sha256:")


def object_digest(kind, raw):
    return hashlib.sha1(kind.encode() + b" " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError(f"Nonfinite JSON number: {value}")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


class Audit:
    def __init__(self):
        self.count = 0
        self.failures = []

    def check(self, condition, message):
        self.count += 1
        if not condition:
            self.failures.append(message)
            raise AssertionError(message)

    def relative(self, name):
        self.check(type(name) is str and bool(name) and "\\" not in name and "\0" not in name,
                   "Nonempty native relative path required")
        value = PurePosixPath(name)
        self.check(not value.is_absolute() and value.as_posix() == name
                   and all(part not in ("", ".", "..") and ":" not in part for part in value.parts),
                   f"Unsafe or unnormalized path: {name}")
        return value

    def regular(self, directory, name):
        path = directory
        for part in self.relative(name).parts:
            path = path / part
            self.check(not path.is_symlink(), f"Symlink evidence component: {path}")
        self.check(path.is_file() and path.resolve().is_relative_to(directory.resolve()),
                   f"Missing or escaping evidence file: {name}")
        return path


class GitObjects:
    """Hash each distinct blob once through the read-only batch interface."""
    def __init__(self, root, audit):
        self.root, self.audit = root, audit
        self.trees, self.blobs = {}, {}
        self.process = subprocess.Popen(["git", "-C", str(root), "cat-file", "--batch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args])

    def tree(self, commit):
        if commit not in self.trees:
            entries = {}
            for entry in self.git("ls-tree", "-r", "-z", commit).split(b"\0"):
                if not entry:
                    continue
                metadata, path = entry.split(b"\t", 1)
                mode, kind, oid = metadata.decode().split()
                name = path.decode()
                self.audit.relative(name)
                self.audit.check(kind == "blob" and mode in ("100644", "100755") and name not in entries,
                                 f"Nonregular or duplicate Git input: {name}")
                entries[name] = {"mode": mode, "oid": oid}
            self.trees[commit] = entries
        return self.trees[commit]

    def blob_identity(self, oid):
        if oid not in self.blobs:
            self.process.stdin.write((oid + "\n").encode())
            self.process.stdin.flush()
            header = self.process.stdout.readline().decode().strip().split()
            self.audit.check(len(header) == 3 and header[:2] == [oid, "blob"], f"Missing Git blob: {oid}")
            size = int(header[2])
            sha256 = hashlib.sha256()
            sha1 = hashlib.sha1(b"blob " + str(size).encode() + b"\0")
            remaining = size
            while remaining:
                part = self.process.stdout.read(min(remaining, 1024 * 1024))
                self.audit.check(bool(part), f"Truncated Git blob: {oid}")
                sha256.update(part)
                sha1.update(part)
                remaining -= len(part)
            self.audit.check(self.process.stdout.read(1) == b"\n", f"Missing Git blob terminator: {oid}")
            self.audit.check(sha1.hexdigest() == oid, f"Git blob content identity mismatch: {oid}")
            self.blobs[oid] = {"bytes": size, "sha256": sha256.hexdigest()}
        return self.blobs[oid]

    def file(self, commit, path):
        oid = self.tree(commit)[path]["oid"]
        raw = self.git("cat-file", "blob", oid)
        self.audit.check(object_digest("blob", raw) == oid, f"Read blob mismatch: {path}")
        return raw

    def close(self):
        self.process.stdin.close()
        self.process.stdout.close()
        self.process.stderr.close()
        self.process.wait()


def archive_members(root, evidence, summary, manifest, audit, result):
    archive = summary["archive"]
    parts = archive["parts"]
    audit.check(bool(parts), "Archive parts are absent")
    joined = []
    for number, part in enumerate(parts, 1):
        expected = f"checkpoint-027.zip.part{number:03d}"
        audit.check(part["path"] == expected, f"Noncontiguous or unordered archive part {number}")
        body = audit.regular(root / BASE, expected).read_bytes()
        audit.check(len(body) == part["bytes"] and digest(body) == bare(part["sha256"]), f"Part digest mismatch: {expected}")
        joined.append(body)
    joined = b"".join(joined)
    audit.check(len(joined) == archive["bytes"] and digest(joined) == bare(archive["sha256"]), "Joined archive identity mismatch")
    declared = {}
    for member in manifest["members"]:
        audit.relative(member["path"])
        audit.check(member["path"] not in declared, f"Duplicate manifest member: {member['path']}")
        declared[member["path"]] = member
    audit.check(manifest["checkpoint"] == 27 and archive["member_count"] == len(declared), "Manifest checkpoint/count mismatch")
    payloads = {}
    with zipfile.ZipFile(io.BytesIO(joined)) as zipped:
        infos = zipped.infolist()
        audit.check(len(infos) == len(declared), "ZIP member count differs from manifest")
        for info in infos:
            name = info.filename
            audit.relative(name)
            audit.check(name in declared and name not in payloads, f"Unknown or duplicate ZIP member: {name}")
            mode = info.external_attr >> 16
            audit.check(not info.is_dir() and stat.S_IFMT(mode) in (0, stat.S_IFREG)
                        and not (info.flag_bits & 1), f"Nonregular or encrypted ZIP member: {name}")
            body = zipped.read(info)
            row = declared[name]
            audit.check(len(body) == info.file_size == row["bytes"], f"Member length mismatch: {name}")
            audit.check((zlib.crc32(body) & 0xffffffff) == info.CRC, f"Member CRC mismatch: {name}")
            audit.check(digest(body) == bare(row["sha256"]), f"Member SHA256 mismatch: {name}")
            audit.check(audit.regular(evidence, name).read_bytes() == body, f"Archived bytes differ from raw evidence: {name}")
            payloads[name] = body
    actual = {path.relative_to(evidence).as_posix() for path in evidence.rglob("*")
              if path.is_file() and "__pycache__" not in path.relative_to(evidence).parts
              and path.suffix != ".pyc"}
    audit.check(actual == set(payloads), "Raw evidence inventory differs from archive members")
    audit.check(payloads["drivers/audit_checkpoint027.py"] == Path(__file__).read_bytes(), "Executed audit source differs from archived source")
    result["archive"] = {"bytes": len(joined), "sha256": digest(joined), "parts": len(parts),
        "members": len(payloads), "uncompressed_bytes": sum(map(len, payloads.values())),
        "part_member_hashes_and_crcs_verified": True, "safe_unique_regular_member_names": True,
        "all_archived_members_match_preserved_evidence": True}
    return payloads


def validate_receipt(run, report, payloads, objects, audit):
    commit, tree, exit_code = RUNS[run]
    prefix = f"execution/{run}/"
    before = decode(payloads[prefix + "inputs-before.json"])
    after = decode(payloads[prefix + "inputs-after.json"])
    audit.check(before == after and report["inputs_stable"] is True, f"Unstable input receipts: {run}")
    identity = before.get("git", {"commit": before.get("git_commit"), "tree": before.get("git_tree"),
                                  "status": before.get("git_status")})
    audit.check(identity == {"commit": commit, "tree": tree, "status": ""}, f"Unexpected clean Git identity: {run}")
    audit.check(report["source_commit"] == commit and report["source_tree"] == tree, f"Report source mismatch: {run}")
    audit.check(objects.git("rev-parse", commit + "^{tree}").decode().strip() == tree, f"Git tree mismatch: {run}")
    audit.check(before.get("omitted_historical_archives", []) == [], f"Missing historical inputs: {run}")
    files = before["files"]
    tree_files = objects.tree(commit)
    audit.check(len(files) == len(tree_files) == len({row["path"] for row in files})
                and {row["path"] for row in files} == set(tree_files), f"Incomplete tracked input inventory: {run}")
    for row in files:
        git_row = tree_files[row["path"]]
        actual = objects.blob_identity(git_row["oid"])
        audit.check(row["bytes"] == actual["bytes"] and bare(row["sha256"]) == actual["sha256"],
                    f"Receipt bytes/hash differ from exact Git blob: {run}/{row['path']}")
        if "git_blob_sha1" in row:
            audit.check(row["git_blob_sha1"] == git_row["oid"] and row["mode"] == git_row["mode"],
                        f"Receipt Git fields mismatch: {run}/{row['path']}")
    command = decode(payloads[f"execution/{run}.command.json"])
    audit.check(command["exit_code"] == exit_code and command["cwd"] == report["working_directory"], f"Command outcome/cwd mismatch: {run}")
    audit.check(Path(command["command"][1]).name == Path(report["command"][1]).name
                and command["command"][2:] == report["command"][2:], f"Actual command differs: {run}")
    audit.check(datetime.fromisoformat(command["started_at"]) <= datetime.fromisoformat(report["started_at"])
                <= datetime.fromisoformat(report["finished_at"]) <= datetime.fromisoformat(command["finished_at"]),
                f"Run timestamps are inconsistent: {run}")
    audit.check(f"execution/{run}.command.stdout.txt" in payloads
                and f"execution/{run}.command.stderr.txt" in payloads, f"Missing raw command output: {run}")
    environment = report.get("environment", report.get("execution"))
    audit.check(environment["python"].startswith("3.12.14 ") and environment["platform"].startswith("Linux-"),
                f"Unexpected execution environment: {run}")
    if "driver_sha256" in report:
        audit.check(digest(payloads[prefix + "executed-driver.py"]) == report["driver_sha256"], f"Executed driver identity mismatch: {run}")
    if "identity_helper_sha256" in report:
        audit.check(digest(payloads[prefix + "executed-identity-helper.py"]) == report["identity_helper_sha256"],
                    f"Executed identity helper mismatch: {run}")
    return {"commit": commit, "tree": tree, "tracked_files": len(files),
            "tracked_bytes": sum(row["bytes"] for row in files), "exit_code": exit_code, "inputs_complete_and_stable": True}


def descriptor(payloads, prefix, item, audit):
    audit.relative(item["path"])
    body = payloads[prefix + item["path"]]
    audit.check(len(body) == item["bytes"] and digest(body) == bare(item["sha256"]),
                f"Artifact/report identity mismatch: {prefix}{item['path']}")
    return body


def work_accounting(row, audit, label):
    work = row["work"]
    audit.check(all(type(value) is int and value >= 0 for value in work["counts"].values())
                and sum(work["counts"].values()) == work["operations"], f"Inconsistent actual work counters: {label}")
    audit.check(0 <= work["cache_entries"] <= 256, f"Numerical cache cap changed: {label}")


def validate_original(report, payloads, objects, audit, result):
    audit.check(report["status"] == "failed" and report["required_cases"] == report["selected_cases"] == CASES,
                "Original corpus was filtered or relabeled")
    audit.check(report["release_acceptance"] is False and report["complete_source_delivery_corpus"] is False,
                "Original failed corpus cannot establish acceptance")
    rows = report["deliveries"]
    audit.check([row["case_id"] for row in rows] == CASES, "Original request inventory mismatch")
    frozen = {}
    for path in (SOURCE_BASE + "/acceptance.json", SOURCE_BASE + "/draft2-supplements/acceptance.json"):
        for item in decode(objects.file(CONTROL, path))["source_cases"]:
            audit.check(item["id"] not in frozen, "Duplicate frozen source identity")
            frozen[item["id"]] = item
    failed, passed = [], []
    ends = {"P14": "4", "P16": "4", "P17": "2", "P26": "60", "L01": "4", "L02": "2", "L03": "4"}
    for row in rows:
        case = row["case_id"]
        prefix = "execution/control-original28/"
        audit.check(decode(payloads[prefix + case + "/request-result.json"]) == row, f"Original raw request differs: {case}")
        expected_options = {"end": ends.get(case, "3"), "fps": 1, "helpers": False,
            "position_tolerance_m": .001, "rotation_tolerance_rad": .001, "time_tolerance_s": .000001}
        audit.check(row["options"] == expected_options and row["max_operations"] == 100000,
                    f"Original settings changed: {case}")
        audit.check(row["program_revision"] == frozen[case]["program_revision"], f"Frozen program differs: {case}")
        manifest = objects.file(CONTROL, row["source_manifest"]["path"])
        audit.check(len(manifest) == row["source_manifest"]["bytes"]
                    and digest(manifest) == bare(row["source_manifest"]["sha256"]), f"Frozen source manifest differs: {case}")
        work_accounting(row, audit, case)
        audit.check(math.isfinite(row["elapsed_seconds"]) and 0 <= row["elapsed_seconds"] < 30,
                    f"Original elapsed limit failure: {case}")
        if row["status"] == "passed":
            passed.append(case)
            glb = descriptor(payloads, prefix, row["artifact"], audit)
            exported = decode(descriptor(payloads, prefix, row["export_report"], audit))
            audit.check(glb[:4] == b"glTF" and int.from_bytes(glb[4:8], "little") == 2
                        and int.from_bytes(glb[8:12], "little") == len(glb), f"Invalid retained GLB header: {case}")
            audit.check(exported["validation"]["status"] == "passed" and row["operations"] <= 100000,
                        f"Invalid passed recording: {case}")
        else:
            failed.append(case)
            audit.check(row["status"] == "failed" and row["operations"] == 100001, f"Unexpected original refusal: {case}")
            details = row["diagnostic"]["details"]
            audit.check(details["budget"] == "max_operations" and details["limit"] == 100000
                        and details["consumed"] == 100001, f"Original refusal diagnostics differ: {case}")
            audit.check("artifact" not in row and prefix + case + "/scene.glb" not in payloads,
                        f"Failed original request published an artifact: {case}")
    audit.check(len(passed) == 23 and failed == FAILED, "Original23/28 outcome mismatch")
    result["original28"] = {"source_commit": CONTROL, "passed": len(passed), "failed": failed,
        "all_original_settings_and_source_identities_verified": True, "all_five_refuse_at_100001": True,
        "candidate_original28_executed": False}


def validate_tests(report, payloads, objects, audit, result):
    prefix = "execution/candidate-focused-001/"
    tests = decode(payloads[prefix + "tests.json"])
    log = payloads[prefix + "tests.log"]
    audit.check(report["status"] == "passed" and report["test_count"] == report["passed_count"] == 55,
                "Dedicated result count mismatch")
    audit.check(tests["test_count"] == 55 and all(tests[key] == 0 for key in
        ("failures", "errors", "skips", "expected_failures", "unexpected_successes")), "Dedicated nonpassing result")
    audit.check(all(report[key] == 0 for key in ("failures", "errors", "skips")), "Dedicated report failure count")
    audit.check(report["test_log_complete"] is True and report["test_log_bytes"] == len(log)
                and report["test_log_sha256"] == digest(log), "Dedicated raw log identity mismatch")
    expected = set()
    for module in ("test_reach_certificate_term_reuse", "test_reach_certificate_second_quarter"):
        tree = ast.parse(objects.file(CANDIDATE, f"tests/{module}.py"))
        for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            for method in (node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")):
                expected.add(f"{module}.{cls.name}.{method.name}")
    actual = [row["test_id"] for row in tests["results"]]
    audit.check(len(expected) == len(actual) == len(tests["started"]) == 55
                and set(actual) == set(tests["started"]) == expected
                and all(row["status"] == "passed" for row in tests["results"]), "Dedicated methods incomplete or duplicated")
    text = log.decode()
    audit.check(re.search(r"Ran 55 tests in [0-9.]+s\n\nOK\n?$", text) is not None,
                "Dedicated log lacks complete successful footer")
    for name in expected:
        audit.check(text.count("(" + name + ")") == 1, f"Dedicated method log row absent/duplicated: {name}")
    result["dedicated_tests"] = {"source_commit": CANDIDATE, "passed": 55, "failures": 0, "errors": 0,
        "skips": 0, "unique_methods_and_raw_log_verified": True, "full_regression_claimed": False}


def validate_prefix(run, report, payloads, objects, audit):
    expected_cases = ["P09"] if run == "candidate-controls-001" else ["P11", "L03"]
    expected_failure = ("P09 requires an incremental complete-request saving" if len(expected_cases) == 1
                        else "No positive complete-request saving was measured")
    audit.check(report["status"] == "failed" and report["failure"] == {"type": "ValueError", "message": expected_failure},
                f"Zero-saving measurement failure relabeled: {run}")
    audit.check(report["original_complete_recording"] is False and report["release_acceptance"] is False
                and report["elapsed_speedup_claimed"] is False and report["measurement_drivers_stable"] is True,
                f"Measurement scope mismatch: {run}")
    audit.check(report["prefix_settings"] == {"end_seconds": "1/4", "fps": 4, "helpers": False}
                and report["repetitions_per_case"] == 5, f"Prefix settings/repetitions differ: {run}")
    definition = report["control_definition"]
    audit.check(definition["function"] == "checkpoint026_complete_inequality_values"
                and digest(objects.file(CANDIDATE, definition["path"])) == definition["sha256"]
                and report["control_checkpoint_commit"] == CONTROL, f"Prefix control identity mismatch: {run}")
    rows = report["rows"]
    expected_keys = {(case, repeat, mode) for case in expected_cases for repeat in range(1, 6)
                     for mode in ("control", "candidate")}
    keyed = {(row["case_id"], row["repetition"], row["mode"]): row for row in rows}
    audit.check(set(keyed) == expected_keys and len(rows) == len(expected_keys), f"Prefix raw request inventory mismatch: {run}")
    retained = {}
    prefix = f"execution/{run}/"
    for key, row in keyed.items():
        case, repeat, mode = key
        audit.check(row["directory"] == f"{case}-{repeat:02d}-{mode}" and row["status"] == "passed",
                    f"Prefix row status/path mismatch: {key}")
        audit.check(decode(payloads[prefix + row["directory"] + "/request-result.json"]) == row,
                    f"Raw prefix request differs from report: {key}")
        order = ["control", "candidate"] if repeat % 2 else ["candidate", "control"]
        audit.check(row["order"] == order and row["order_position"] == order.index(mode) + 1,
                    f"Prefix alternating order mismatch: {key}")
        work_accounting(row, audit, str(key))
        audit.check((row["shared_operations"], row["operations"]) == PREFIX_COSTS[case]
                    and row["operations"] == row["work"]["operations"], f"Unexpected raw prefix cost: {key}")
        audit.check(row["budget_limits"]["max_operations"] == 100000 and row["budget_limits"]["max_elapsed_ms"] == 30000,
                    f"Prefix shared limits changed: {key}")
        audit.check(math.isfinite(row["elapsed_ms"]) and 0 <= row["elapsed_ms"] < 30000, f"Invalid prefix elapsed: {key}")
        artifact = descriptor(payloads, prefix, row["artifact"], audit)
        exported = descriptor(payloads, prefix, row["export_report"], audit)
        audit.check(decode(exported)["validation"]["status"] == "passed", f"Prefix independent validation failed: {key}")
        retained[key] = (artifact, exported)
    derived = []
    comparisons = {item["case_id"]: item for item in report["comparisons"]}
    audit.check(set(comparisons) == set(expected_cases) and len(report["comparisons"]) == len(expected_cases),
                f"Prefix summary case inventory mismatch: {run}")
    for case in expected_cases:
        item = comparisons[case]
        audit.check(item["pair_count"] == 5 and item["includes_construction"] is True
                    and item["glb_bytes_identical"] is True and item["complete_reports_identical"] is True,
                    f"Prefix summary scope mismatch: {case}")
        audit.check(len(item["pairs"]) == 5, f"Missing retained comparisons: {case}")
        elapsed = {mode: [] for mode in ("control", "candidate")}
        for repeat, pair in enumerate(item["pairs"], 1):
            control, candidate = keyed[(case, repeat, "control")], keyed[(case, repeat, "candidate")]
            audit.check(retained[(case, repeat, "control")] == retained[(case, repeat, "candidate")],
                        f"Prefix GLB/full-report bytes differ: {case}/{repeat}")
            expected = {"repetition": repeat, "glb_bytes_identical": True, "complete_reports_identical": True,
                "control_shared_operations": control["shared_operations"], "candidate_shared_operations": candidate["shared_operations"],
                "saved_shared_operations": control["shared_operations"] - candidate["shared_operations"],
                "control_reach_operations": control["operations"], "candidate_reach_operations": candidate["operations"],
                "saved_reach_operations": control["operations"] - candidate["operations"],
                "control_elapsed_ms": control["elapsed_ms"], "candidate_elapsed_ms": candidate["elapsed_ms"]}
            audit.check(pair == expected and expected["saved_shared_operations"] == expected["saved_reach_operations"] == 0,
                        f"Prefix pair derived summary mismatch: {case}/{repeat}")
            for mode in elapsed:
                elapsed[mode].append(keyed[(case, repeat, mode)]["elapsed_ms"])
        for mode in elapsed:
            audit.check(item[f"{mode}_elapsed_ms"] == elapsed[mode]
                        and item[f"{mode}_median_elapsed_ms"] == statistics.median(elapsed[mode])
                        and item[f"{mode}_elapsed_range_ms"] == [min(elapsed[mode]), max(elapsed[mode])],
                        f"Prefix elapsed aggregate mismatch: {case}/{mode}")
        change = statistics.median(elapsed["candidate"]) - statistics.median(elapsed["control"])
        audit.check(item["median_elapsed_increase_ms"] == change
                    and math.isclose(item["median_elapsed_increase_percent"], 100 * change / statistics.median(elapsed["control"]), rel_tol=1e-12, abs_tol=1e-12)
                    and item["candidate_slower_pairs"] == sum(b > a for a, b in zip(elapsed["control"], elapsed["candidate"]))
                    and item["candidate_faster_pairs"] == sum(b < a for a, b in zip(elapsed["control"], elapsed["candidate"])),
                    f"Prefix paired elapsed summary mismatch: {case}")
        audit.check(item["saved_shared_operations"] == item["saved_reach_operations"] == 0
                    and item["control_shared_operations"] == item["candidate_shared_operations"] == PREFIX_COSTS[case][0]
                    and item["control_reach_operations"] == item["candidate_reach_operations"] == PREFIX_COSTS[case][1],
                    f"Prefix total summary mismatch: {case}")
        derived.append({"case_id": case, "pairs": 5, "shared_operations_each": PREFIX_COSTS[case][0],
            "reach_operations_each": PREFIX_COSTS[case][1], "saved_operations_each": 0,
            "glb_and_complete_report_bytes_identical": True,
            "control_median_ms": statistics.median(elapsed["control"]),
            "candidate_median_ms": statistics.median(elapsed["candidate"]),
            "slower_pairs": item["candidate_slower_pairs"], "faster_pairs": item["candidate_faster_pairs"]})
    return derived


def validate_sources(payloads, objects, summary, audit, result):
    cuts = decode(payloads["local-review-cuts/index.json"])["cuts"]
    audit.check(len(cuts) == 3 and len({cut["commit"] for cut in cuts}) == 3, "Expected three preserved source cuts")
    for cut in cuts:
        commit, tree, parent = cut["commit"], cut["tree"], cut["parent"]
        prefix = f"local-review-cuts/{commit}/"
        raw = payloads[prefix + "commit.raw"]
        audit.check(object_digest("commit", raw) == commit, f"Preserved commit identity mismatch: {commit}")
        audit.check(raw == objects.git("cat-file", "commit", commit), f"Preserved raw commit differs from Git: {commit}")
        audit.check(raw.startswith(("tree " + tree + "\n").encode()) and ("parent " + parent + "\n").encode() in raw.split(b"\n\n", 1)[0] + b"\n",
                    f"Preserved tree/parent mismatch: {commit}")
        audit.check(parent == CONTROL and decode(payloads[prefix + "identity.json"]) == cut, f"Preserved cut declaration mismatch: {commit}")
        changed = set(objects.git("diff", "--name-only", parent, commit, "--").decode().splitlines())
        audit.check(changed == {item["path"] for item in cut["files"]}, f"Preserved changed-file closure mismatch: {commit}")
        audit.check(payloads[prefix + "changes.patch"] == objects.git("diff", parent, commit, "--"), f"Preserved patch mismatch: {commit}")
        for item in cut["files"]:
            body = payloads[prefix + item["path"]]
            audit.check(len(body) == item["bytes"] and digest(body) == item["sha256"]
                        and object_digest("blob", body) == item["git_blob"] == objects.tree(commit)[item["path"]]["oid"],
                        f"Preserved source bytes mismatch: {commit}/{item['path']}")
    candidate_cut = next(cut for cut in cuts if cut["commit"] == CANDIDATE)
    audit.check(candidate_cut["tree"] == CANDIDATE_TREE and {item["path"] for item in candidate_cut["files"]} == CHANGED,
                "Candidate source scope differs")
    old = next(node for node in ast.parse(objects.file(CONTROL, "ontokin/reach_conformance.py")).body
               if isinstance(node, ast.FunctionDef) and node.name == "_complete_inequality_values")
    frozen = next(node for node in ast.parse(objects.file(CANDIDATE, "tests/test_reach_certificate_second_quarter.py")).body
                  if isinstance(node, ast.FunctionDef) and node.name == "_checkpoint026_complete")
    old.name = frozen.name
    audit.check(ast.dump(old, include_attributes=False) == ast.dump(frozen, include_attributes=False),
                "Frozen checkpoint026 calculation differs beyond its function name")
    source_review = decode(payloads["reviews/source-review-001.json"])
    tests_review = decode(payloads["reviews/tests-source-review.json"])
    control_review = decode(payloads["reviews/control-source-equivalence.json"])
    audit.check(source_review["runtime_git_blob"] == objects.tree(CANDIDATE)["ontokin/reach_conformance.py"]["oid"]
                and source_review["base_commit"] == CONTROL and source_review["result"] == "approved_for_runtime_verification"
                and source_review["runtime_executed_by_reviewer"] is False, "Arithmetic review source binding mismatch")
    audit.check(tests_review["test_git_blob"] == objects.tree(CANDIDATE)["tests/test_reach_certificate_second_quarter.py"]["oid"]
                and tests_review["result"] == "approved" and tests_review["runtime_executed_by_reviewer"] is False,
                "Test review source binding mismatch")
    audit.check(control_review["control_base_commit"] == CONTROL and control_review["ast_identical_except_function_name"] is True
                and control_review["test_file_sha256"] == digest(objects.file(CANDIDATE, "tests/test_reach_certificate_second_quarter.py")),
                "Control review source binding mismatch")
    publication = decode(payloads["publication/held-source-verification.json"])
    readback = decode(payloads["publication/held-source-readback.json"])
    audit.check(publication["published_commit"] == readback["published_commit"] == readback["remote_ref_readback"] == PUBLISHED
                and publication["published_tree"] == readback["published_tree"] == CANDIDATE_TREE
                and publication["executed_local_commit"] == CANDIDATE and publication["parent"] == CONTROL,
                "Captured remote source identity mismatch")
    audit.check(publication["complete_trees_identical"] is True and publication["integration_status"] == "held_outside_PR28"
                and publication["positive_complete_request_savings"] is False
                and publication["ref_update"] == {"expected_sha": CONTROL, "force": False}
                and readback["verified"] is True, "Captured held publication scope mismatch")
    audit.check({row["path"] for row in publication["files"]} == {row["path"] for row in readback["remote_file_readback"]} == CHANGED,
                "Captured remote changed-file inventory mismatch")
    for row in publication["files"]:
        expected = objects.tree(CANDIDATE)[row["path"]]["oid"]
        observed = next(item for item in readback["remote_file_readback"] if item["path"] == row["path"])
        audit.check(row["expected_blob"] == row["remote_blob"] == observed["sha"] == expected
                    and row["matched"] is True and observed["matched"] is True, f"Captured remote blob mismatch: {row['path']}")
    candidate = summary["candidate"]
    audit.check(candidate["commit"] == CANDIDATE and candidate["tree"] == CANDIDATE_TREE
                and candidate["integrated"] is False and candidate["original28_executed"] is False
                and candidate["outcome"] == "held" and candidate["dedicated_passed"] == 55
                and candidate["published_commit"] == PUBLISHED, "Checkpoint candidate outcome is not the observed held result")
    audit.check(summary["baseline_checkpoint"] == CONTROL and summary["accepted_implementation_commit"] == ACCEPTED
                and summary["release_acceptance"] is False and summary["full_product_goal_completed"] is False,
                "Checkpoint incorrectly changes accepted implementation or release scope")
    decision = decode(payloads["reviews/acceptance-decision.json"])
    audit.check(decision["status"] == "completed" and decision["candidate_decision"] == "held_not_integrated"
                and decision["positive_complete_request_savings_gate_passed"] is False,
                "Independent acceptance decision does not retain the failed savings gate")
    audit.check(decision["candidate"]["executed_local_commit"] == CANDIDATE
                and decision["candidate"]["published_isolated_commit"] == PUBLISHED
                and decision["candidate"]["tree"] == CANDIDATE_TREE
                and decision["candidate"]["integrated_into_PR28"] is False
                and decision["accepted_implementation_unchanged"] == ACCEPTED
                and decision["accepted_checkpoint_parent"] == CONTROL
                and decision["release_acceptance"] is False and decision["full_product_goal_completed"] is False,
                "Independent acceptance decision has incorrect source or integration identities")
    bindings = decision["input_bindings"]
    audit.check(bool(bindings) and len(bindings) == len({item["path"] for item in bindings}),
                "Independent acceptance inputs are empty or duplicated")
    for item in bindings:
        descriptor(payloads, "", item, audit)
    audit.check(decision["checks"] and all(item["passed"] is True for item in decision["checks"]),
                "Independent acceptance review contains a failed inspection check")
    result["source_and_publication"] = {"preserved_cuts": 3, "all_cut_commits_patches_and_blobs_verified": True,
        "frozen026_control_ast_independently_equal": True, "review_bindings_verified": True,
        "held_local_commit": CANDIDATE, "held_published_commit": PUBLISHED, "held_tree": CANDIDATE_TREE,
        "captured_remote_tree_and_blob_readbacks_bound": True, "live_remote_observation_by_auditor": False,
        "independent_held_decision_verified": True, "acceptance_input_bindings_verified": len(bindings),
        "integrated": False, "accepted_implementation_commit": ACCEPTED}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root, evidence, output = args.root.resolve(), args.evidence.resolve(), args.output.resolve()
    if output.exists() or output.is_relative_to(evidence):
        parser.error("Use a fresh audit output outside the preserved evidence directory")
    audit = Audit()
    result = {"schema_version": "ontokin.independent-checkpoint-archive-review/0.1", "checkpoint": 27,
        "reviewer": "/root/hostile_review", "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed", "blocking_findings": [],
        "method": "Independent standard-library in-memory ZIP, raw JSON/artifact/log comparisons, AST control comparison, and read-only Git-object hashing. No product imports, tests, archive extraction/creation, Git mutations or live network requests.",
        "audit_script_sha256": digest(Path(__file__).read_bytes()), "release_acceptance": False,
        "full_product_goal_completed": False}
    objects = None
    try:
        summary_bytes = audit.regular(root, BASE + "/checkpoint-027.json").read_bytes()
        manifest_bytes = audit.regular(root, BASE + "/checkpoint-027-manifest.json").read_bytes()
        summary, manifest = decode(summary_bytes), decode(manifest_bytes)
        result.update(summary_sha256=digest(summary_bytes), manifest_sha256=digest(manifest_bytes))
        payloads = archive_members(root, evidence, summary, manifest, audit, result)
        objects = GitObjects(root, audit)
        protected = ("ontokin", "tests", "tools", ".github/workflows")
        audit.check(not objects.git("diff", "--name-only", CONTROL, "--", *protected).strip(),
                    "Evidence checkout changes accepted runtime, tests, tools or workflows")
        result["evidence_checkout_scope"] = {"base_commit": CONTROL,
            "protected_paths": list(protected), "diff_empty": True}
        run_reports = {name: decode(payloads[f"execution/{name}/report.json"]) for name in RUNS}
        observed_reports = {name for name in payloads if re.fullmatch(r"execution/[^/]+/report\.json", name)}
        audit.check(observed_reports == {f"execution/{name}/report.json" for name in RUNS},
                    "Unexpected or omitted execution report; candidate original28 is not claimed")
        result["input_receipts"] = {name: validate_receipt(name, run_reports[name], payloads, objects, audit) for name in RUNS}
        validate_original(run_reports["control-original28"], payloads, objects, audit, result)
        validate_tests(run_reports["candidate-focused-001"], payloads, objects, audit, result)
        prefixes = []
        for name in ("candidate-controls-001", "candidate-controls-other-001"):
            prefixes.extend(validate_prefix(name, run_reports[name], payloads, objects, audit))
        result["prefix_controls"] = {"pairs": 15, "raw_completed_requests": 30, "cases": prefixes,
            "both_measurement_runs_failed_positive_saving_gate": True, "saved_operations_total": 0,
            "elapsed_speedup_claimed": False, "original_recording_gate_replacement": False}
        validate_sources(payloads, objects, summary, audit, result)
        result["status"] = "passed"
    except Exception as error:
        result["error"] = {"type": type(error).__name__, "message": str(error)}
        result["traceback"] = traceback.format_exc()
        if str(error) not in audit.failures:
            audit.failures.append(str(error))
    finally:
        if objects is not None:
            objects.close()
    result["checks_passed"] = audit.count - len(audit.failures)
    result["checks_attempted"] = audit.count
    result["blocking_findings"] = audit.failures
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "checks_passed": result["checks_passed"],
        "blocking_findings": result["blocking_findings"], "output": str(output)}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
