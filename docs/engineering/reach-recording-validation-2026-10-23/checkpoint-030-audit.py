#!/usr/bin/env python3
"""Audit checkpoint 030 evidence without importing or executing product code.

The auditor recomputes request accounting, output equivalence, timing screens,
test inventories and Git input binding. A failed product attempt remains failed;
an honest failed original recording suite is not an evidence-audit failure.
Without --checkpoint this performs an integrity preflight and selects no winner.
Reports aggregate successful checks by name by default. --verbose-checks also
retains every individual successful check; both modes execute identical checks.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import statistics
import struct
import subprocess
import sys
import traceback
import zipfile


BASELINE = "6afa8439a37f0b7387b77a13f174014963adca8c"
BASE = "docs/language-design/planar-reach-v0.1"
READER = "ontokin/reach_conformance.py"
SOURCE_CASES = tuple(f"P{n:02d}" for n in range(1, 24)) + ("P25", "P26", "L01", "L02", "L03")
PREFIX_CASES = ("P09", "P11", "L03")
MODES = ("decode_only", "compare_only", "combined")
DECODE, COMPARE = "independent_bound_decode", "independent_exact_compare"
DA, CA = "independent_certificate_decode_admission", "independent_certificate_compare_admission"
LIMITS = {"max_operations": 100000, "max_elapsed_ms": 30000,
          "max_operand_bits": 32768, "max_cache_entries": 256}
BUDGET_LIMITS = {"max_objects": 1000, "max_operations": 100000, "max_result_items": 1000,
                 "max_elapsed_ms": 30000, "max_value_entries": 100000}
CONTEXT = {"native_bound_budget_callback", "nested_budget_check_absent", "work_observer_absent",
           "trace_absent", "profile_absent"}
CHECKS = []


def check(condition, name, details=None):
    row = {"name": name, "passed": bool(condition)}
    if details is not None:
        row["details"] = details
    CHECKS.append(row)
    if not condition:
        raise ValueError(name)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized_hash(value):
    check(type(value) is str, "hash is a string")
    result = value.removeprefix("sha256:")
    check(re.fullmatch(r"[0-9a-f]{64}", result) is not None, "SHA-256 shape")
    return result


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError(f"Nonfinite JSON value: {value}")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def relative(name):
    check(type(name) is str and name and "\\" not in name and "\0" not in name,
          "relative path has native safe characters")
    path = PurePosixPath(name)
    check(not path.is_absolute() and str(path) == name and
          all(part not in ("", ".", "..") for part in path.parts), "normalized relative path")
    return path


def contained(root, name):
    path = root
    for part in relative(name).parts:
        path = path / part
        check(not path.is_symlink(), "no evidence symlink", name)
    check(path.is_file() and path.resolve().is_relative_to(root.resolve()), "contained regular evidence file", name)
    return path


def read(path):
    check(path.is_file() and not path.is_symlink(), "regular input", str(path))
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    check(len(raw) == before.st_size == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
          "input stable while read", str(path))
    return raw


def document(path):
    return decode(read(path))


def member(root, receipt):
    check(type(receipt) is dict and set(receipt) >= {"path", "bytes", "sha256"}, "complete file receipt")
    path = contained(root, receipt["path"])
    raw = read(path)
    check(type(receipt["bytes"]) is int and receipt["bytes"] == len(raw)
          and normalized_hash(receipt["sha256"]) == sha(raw), "file receipt matches bytes", receipt["path"])
    return raw


def finite_positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


class GitInputs:
    """Read identified Git objects; cache hashes without importing the checkout."""
    def __init__(self, repo):
        self.repo = repo
        self.trees, self.blobs, self.sources = {}, {}, {}

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args])

    def tree(self, commit):
        check(type(commit) is str and re.fullmatch(r"[0-9a-f]{40}", commit), "exact source commit identity")
        if commit in self.trees:
            return self.trees[commit]
        check(self.git("rev-parse", f"{commit}^{{commit}}").decode().strip() == commit,
              "source commit object exists", commit)
        tree = self.git("rev-parse", f"{commit}^{{tree}}").decode().strip()
        entries = {}
        for item in self.git("ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
            if not item:
                continue
            fields, name = item.split(b"\t", 1)
            mode, kind, blob = fields.decode().split()
            name = name.decode()
            relative(name)
            check(kind == "blob" and mode in ("100644", "100755") and name not in entries,
                  "source tree contains unique regular files", name)
            entries[name] = blob
        absent = sorted(set(entries.values()) - self.blobs.keys())
        if absent:
            process = subprocess.Popen(["git", "-C", str(self.repo), "cat-file", "--batch"],
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                for blob in absent:
                    process.stdin.write((blob + "\n").encode())
                    process.stdin.flush()
                    header = process.stdout.readline().decode().strip().split()
                    check(len(header) == 3 and header[:2] == [blob, "blob"], "Git blob header", blob)
                    size = int(header[2])
                    remaining, digest, git_digest = size, hashlib.sha256(), hashlib.sha1()
                    git_digest.update(b"blob " + str(size).encode() + b"\0")
                    while remaining:
                        block = process.stdout.read(min(remaining, 1024 * 1024))
                        check(bool(block), "Git blob stream complete", blob)
                        digest.update(block)
                        git_digest.update(block)
                        remaining -= len(block)
                    check(process.stdout.read(1) == b"\n" and git_digest.hexdigest() == blob,
                          "Git blob content identity", blob)
                    self.blobs[blob] = {"bytes": size, "sha256": "sha256:" + digest.hexdigest()}
            finally:
                process.stdin.close()
                process.wait()
                check(process.returncode == 0, "Git object reader completed")
        files = [{"path": name, **self.blobs[blob]} for name, blob in sorted(entries.items())]
        self.trees[commit] = {"tree": tree, "files": files, "blobs": entries}
        return self.trees[commit]

    def source(self, commit, name):
        relative(name)
        key = commit, name
        if key not in self.sources:
            tree = self.tree(commit)
            check(name in tree["blobs"], "source member belongs to exact commit", name)
            raw = self.git("cat-file", "blob", tree["blobs"][name])
            check(sha(raw) == self.blobs[tree["blobs"][name]]["sha256"].removeprefix("sha256:"),
                  "source read bound to Git object", name)
            self.sources[key] = raw
        return self.sources[key]


def current_checkout(git):
    before = {"commit": git.git("rev-parse", "HEAD").decode().strip(),
              "status": git.git("status", "--porcelain").decode().strip()}
    check(before["status"] == "", "current source checkout is clean before independent audit")
    tree = git.tree(before["commit"])
    names = [name.decode() for name in git.git("ls-files", "-z").split(b"\0") if name]
    check(len(names) == len(set(names)) and sorted(names) == [item["path"] for item in tree["files"]],
          "current tracked-file membership equals identified source tree")
    for item in tree["files"]:
        member(git.repo, item)
    after = {"commit": git.git("rev-parse", "HEAD").decode().strip(),
             "status": git.git("status", "--porcelain").decode().strip()}
    check(before == after, "current source identity and clean state remain stable while audited")
    return {**before, "tree": tree["tree"], "tracked_files_verified": len(names)}


def snapshots(run, report, git):
    before = document(run / "inputs-before.json")
    after = document(run / "inputs-after.json")
    check(before == after and report.get("inputs_stable") is True, "complete input inventories remained identical", run.name)
    check(before.get("scope") == "all_tracked_repository_file_bytes" and
          before["git"] == {"commit": report["source_commit"], "tree": report["source_tree"], "status": ""},
          "clean actual execution commit and tree", run.name)
    exact = git.tree(report["source_commit"])
    check(exact["tree"] == report["source_tree"] and before["files"] == exact["files"],
          "complete snapshot membership and every byte bind to exact Git tree", run.name)
    if "driver_sha256" in report:
        driver = read(run / "executed-driver.py")
        check(sha(driver) == normalized_hash(report["driver_sha256"]), "frozen executed driver identity", run.name)
        check(read(run.parent.parent / "drivers" / Path(report["command"][1]).name) == driver,
              "retained external driver source matches actual frozen execution bytes", run.name)
    else:
        check(report["schema_version"] == "ontokin.reach-source-delivery/0.1", "known stock driver schema")
        check(Path(report["command"][1]) == Path(report["working_directory"]) / "tools/build_reach_source_artifacts.py",
              "original source-recording command")
        git.source(report["source_commit"], "tools/build_reach_source_artifacts.py")


def command_receipts(evidence):
    result = {}
    for path in sorted((evidence / "commands").glob("*.json")):
        receipt = document(path)
        check(type(receipt.get("command")) is list and receipt["command"] and
              all(type(value) is str for value in receipt["command"]), "actual command argument vector", path.name)
        check(type(receipt.get("exit_status")) is int, "actual process exit retained", path.name)
        member(path.parent, receipt["stdout"])
        member(path.parent, receipt["stderr"])
        check(finite_positive(receipt["elapsed_seconds"]), "positive recorded command duration", path.name)
        check(path.stem not in result, "unique command attempt", path.stem)
        result[path.stem] = receipt
    check(set((evidence / "commands").glob("*.stdout.txt")) ==
          {contained(evidence / "commands", item["stdout"]["path"]) for item in result.values()},
          "every complete stdout has its command receipt")
    check(set((evidence / "commands").glob("*.stderr.txt")) ==
          {contained(evidence / "commands", item["stderr"]["path"]) for item in result.values()},
          "every complete stderr has its command receipt")
    return result


def bind_command(run, report, receipts):
    check(run.name in receipts, "execution has actual command receipt", run.name)
    receipt = receipts[run.name]
    check(report["working_directory"] == receipt["working_directory"]
          and Path(receipt["working_directory"]).is_absolute(),
          "report working directory exactly agrees with the captured absolute directory", run.name)
    launched_script = Path(receipt["command"][1])
    if not launched_script.is_absolute():
        launched_script = Path(receipt["working_directory"]) / launched_script
    check(Path(report["command"][1]).is_absolute()
          and str(launched_script.resolve()) == report["command"][1]
          and report["command"][2:] == receipt["command"][2:],
          "reported absolute script resolves from captured launch path with every option argument unchanged", run.name)
    check(report["status"] in ("passed", "failed") and
          receipt["exit_status"] == int(report["status"] != "passed"),
          "actual exit preserves report success or failure", run.name)
    check(datetime.fromisoformat(receipt["started_at"]) <= datetime.fromisoformat(report["started_at"])
          <= datetime.fromisoformat(report["finished_at"]) <= datetime.fromisoformat(receipt["finished_at"]),
          "actual subprocess capture encloses the reported attempt", run.name)


def test_attempt(run, report, git):
    tests = document(run / "tests.json")
    started, results = tests["started"], tests["results"]
    check(type(started) is list and len(started) == len(set(started)) == report["test_count"],
          "test starts have exact unique identities", run.name)
    check(all(row["test_id"] in set(started) for row in results) and
          {row["test_id"] for row in results} == set(started), "every started test has a retained outcome", run.name)
    counts = Counter(row["status"] for row in results)
    check(set(counts) <= {"passed", "failed", "error", "skipped"}, "known per-test result statuses")
    check((report["passed_count"], report["failures"], report["errors"], report["skips"]) ==
          (counts["passed"], counts["failed"], counts["error"], counts["skipped"]),
          "test summary derives from actual result rows", run.name)
    check(tests["expected_failures"] == tests["unexpected_successes"] == 0,
          "no hidden expected failures or unexpected successes", run.name)
    modules = set()
    for identity in started:
        parts = identity.split(".")
        check(len(parts) == 3, "explicit module/class/method test identity", identity)
        modules.add(parts[0])
        source = ast.parse(git.source(report["source_commit"], "tests/" + parts[0] + ".py"))
        klass = next((node for node in source.body if isinstance(node, ast.ClassDef) and node.name == parts[1]), None)
        check(klass is not None and any(isinstance(node, ast.FunctionDef) and node.name == parts[2]
                                       for node in klass.body), "executed test exists in exact source", identity)
    selected = [report["command"][i + 1] for i, value in enumerate(report["command"][:-1]) if value == "--test"]
    if selected:
        expected = set()
        check(len(selected) == len(set(selected)) and {name.split(".")[0] for name in selected} == modules,
              "declared selected test modules are complete")
        for name in selected:
            parts = name.split(".")
            check(1 <= len(parts) <= 3 and all(part.isidentifier() for part in parts),
                  "explicit test selection is a module, class or method", name)
            module = parts[0]
            source = ast.parse(git.source(report["source_commit"], "tests/" + module + ".py"))
            available = set()
            for klass in (node for node in source.body if isinstance(node, ast.ClassDef)):
                available.update(f"{module}.{klass.name}.{node.name}" for node in klass.body
                                 if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"))
            matches = {identity for identity in available if identity == name or identity.startswith(name + ".")}
            check(bool(matches), "declared test selection resolves to exact source methods", name)
            expected.update(matches)
        check(set(started) == expected, "complete declared test-method inventory", run.name)
    log = read(run / "tests.log")
    check(sha(log) == normalized_hash(report["test_log_sha256"]) and
          f"Ran {len(started)} tests".encode() in log, "complete hash-bound unittest log", run.name)
    passed = counts["passed"] == len(started) and not (counts["failed"] or counts["error"] or counts["skipped"])
    check(report["status"] == ("passed" if passed else "failed"), "independently derived test status", run.name)
    return {"kind": "tests", "status": report["status"], "test_count": len(started), **dict(counts),
            "unsuccessful_test_outcomes": [{"test_id": row["test_id"], "status": row["status"]}
                                           for row in results if row["status"] != "passed"],
            "source_commit": report["source_commit"], "source_tree": report["source_tree"]}


def expected_options(case, prefix=False):
    endpoint = "1/4" if prefix else {"P14": "4", "P16": "4", "P17": "2", "P26": "60",
                                    "L01": "4", "L02": "2", "L03": "4"}.get(case, "3")
    return {"end": endpoint, "fps": 4 if prefix else 1, "helpers": False,
            "position_tolerance_m": .001, "rotation_tolerance_rad": .001, "time_tolerance_s": .000001}


def source_identity(row, commit, git):
    case = row["case_id"]
    manifest = f"{BASE}/{'draft2-supplements/' if case.startswith('L') else ''}{case.lower()}.files.json"
    check(row["source_files"] == manifest, "original case source manifest", case)
    raw = git.source(commit, manifest)
    check(raw == git.source(BASELINE, manifest), "original source manifest bytes unchanged", case)
    check(row["source_manifest"] == {"path": manifest, "bytes": len(raw), "sha256": "sha256:" + sha(raw)},
          "request source manifest receipt", case)
    definition, units = decode(raw), []
    for item in [definition["entry"], *definition["modules"]]:
        name = posixpath.normpath(posixpath.join(posixpath.dirname(manifest), item["path"]))
        relative(name)
        raw = git.source(commit, name)
        check(raw == git.source(BASELINE, name), "original source unit bytes unchanged", name)
        source_id = "entry" if item is definition["entry"] else f"package:{item['package_id']}@{item['version']}"
        units.append({"source_id": source_id, "bytes": len(raw), "sha256": "sha256:" + sha(raw)})
    corpus_name = f"{BASE}/{'draft2-supplements/' if case.startswith('L') else ''}acceptance.json"
    corpus_raw = git.source(commit, corpus_name)
    check(corpus_raw == git.source(BASELINE, corpus_name), "original source acceptance bytes unchanged", case)
    corpus = decode(corpus_raw)
    frozen = [item for item in corpus["source_cases"] if item["id"] == case]
    check(len(frozen) == 1 and row["program_revision"] == frozen[0]["program_revision"],
          "program revision matches frozen source case", case)
    if row["status"] == "passed":
        check(row["source_units"] == units, "every delivered source unit matches exact Git bytes", case)
    return units


def request(run, row, commit, git, prefix):
    case = row["case_id"]
    check(case in SOURCE_CASES and row["options"] == expected_options(case, prefix),
          "unchanged actual request settings", row.get("name", case))
    source_identity(row, commit, git)
    if "work" in row or "operations" in row:
        counts = row["work"]["counts"]
        check(type(counts) is dict and all(type(k) is str and type(v) is int and v >= 0 for k, v in counts.items())
              and row["work"]["operations"] == sum(counts.values()), "complete reach operation categories reconcile")
        check(type(row["operations"]) is int and type(row["work"]["operations"]) is int
              and row["operations"] >= row["work"]["operations"] >= 0
              and type(row["work"]["cache_entries"]) is int
              and 0 <= row["work"]["cache_entries"] <= 256, "native work and cache inventory")
    else:
        check(not prefix and row["status"] == "failed", "only a failed original request can lack a completed compiler")
    check(finite_positive(row["elapsed_seconds"]), "positive recorded request duration")
    if prefix:
        check(row["limits"] == LIMITS and row["construction_budget"]["limits"] == BUDGET_LIMITS
              and row["construction_budget"]["operations"] == row["operations"], "unchanged shared request limits")
        check(set(row["entry_context"]) == CONTEXT and all(value is True for value in row["entry_context"].values()),
              "complete native callback and hook entry evidence")
        check(set(row["return_context"]) == CONTEXT | {"same_external_callback"} and
              all(value is True for value in row["return_context"].values()), "complete callback and hook return evidence")
        check(row["original_full_recording"] is False and row["request_kind"] == "complete_successful_prefix_control"
              and row["compile_level"] == "represented", "prefix evidence retains its limited scope")
    else:
        check(row["max_operations"] == 100000, "stock recording original operation allowance")
    if row["status"] == "passed":
        check(row["operations"] <= 100000 and row["work"]["operations"] <= 100000, "successful request respects operation cap")
        glb = member(run, row["artifact"])
        exported_raw = member(run, row["export_report"])
        exported = decode(exported_raw)
        check(len(glb) >= 20 and struct.unpack_from("<4sII", glb) == (b"glTF", 2, len(glb)), "actual complete GLB framing")
        check(exported["artifact"]["byte_length"] == len(glb) and
              normalized_hash(exported["artifact"]["sha256"]) == sha(glb), "export report identifies actual returned bytes")
        check(exported["target_contract"] == "ontokin.glb/0.6" and exported["validation"]["status"] == "passed"
              and exported["validation"]["failures"] == [], "actual export retains passed supplied-byte validation")
        check(exported["program_revision"] == row["program_revision"] and
              Fraction(exported["sampling"]["end_seconds"]) == Fraction(row["options"]["end"])
              and exported["sampling"]["requested_fps"] == row["options"]["fps"], "export source revision and sampled request bind")
        return glb, exported_raw
    check(row["status"] == "failed" and "failure" in row and "traceback" in row,
          "failed request retains its actual exception evidence")
    check("artifact" not in row and "export_report" not in row, "failed request publishes no accepted artifact")
    if "unclaimed_partial_artifact" in row:
        member(run, row["unclaimed_partial_artifact"])
    return None, None


def frozen_reader(run, report, git):
    receipt = document(run / "frozen-control.json")
    check(receipt == report["control"] and receipt["source_commit"] == BASELINE and
          receipt["source_tree"] == git.tree(BASELINE)["tree"] and receipt["source_path"] == READER,
          "control source identity remains original checkpoint 029")
    raw = member(run, receipt["retained_source"])
    check(raw == git.source(BASELINE, READER) and receipt["git_blob_sha1"] == git.tree(BASELINE)["blobs"][READER],
          "frozen original control reader binds byte-for-byte to Git")
    source = raw.decode()
    parsed = ast.parse(source)
    batch = next(node for node in parsed.body if isinstance(node, ast.ClassDef) and node.name == "_CertificateBatch")
    nodes = {node.name: node for node in batch.body if isinstance(node, ast.FunctionDef) and node.name in ("add", "flush")}
    nodes.update({node.name: node for node in parsed.body if isinstance(node, ast.FunctionDef)
                  and node.name == "_complete_inequality_values"})
    expected = {name: {"first_line": node.lineno, "last_line": node.end_lineno,
                       "source_sha256": sha(ast.get_source_segment(source, node).encode())} for name, node in nodes.items()}
    check(receipt["selected_function_bodies"] == expected and set(expected) == {"add", "flush", "_complete_inequality_values"},
          "exact selected original function bodies")
    check(receipt["untouched_baseline_checkout_execution"] is False and receipt["report_or_artifact_normalization"] is False,
          "control substitution and exact-output scope are explicit")


def timing_followup_protocol(evidence, git):
    protocol = document(evidence / "timing-followup-protocol.json")
    check(protocol["selected_transformation"] == "decode_only" and protocol["pairs_per_case"] == 20
          and protocol["cases"] == list(PREFIX_CASES) and protocol["maximum_median_ratio"] == 1.10
          and protocol["prior_same_runtime_attempt"] == "execution/decode-controls-002"
          and protocol["new_attempt"] == "execution/decode-controls-003"
          and protocol["excluded_observations"] == [] and protocol["limit_changes"] is False,
          "fixed follow-up preserves every observation and the original timing threshold")
    check(protocol["process_cpu_time"] == "diagnostic only; does not replace elapsed acceptance",
          "CPU timing is diagnostic only")
    check(type(protocol["source_commit"]) is str and re.fullmatch(r"[0-9a-f]{7,40}", protocol["source_commit"]),
          "timing protocol identifies a Git source commit")
    commit = git.git("rev-parse", f"{protocol['source_commit']}^{{commit}}").decode().strip()
    git.tree(commit)
    old = read(evidence / "drivers/measure_native_fields.py")
    new = read(evidence / "drivers/measure_native_fields_cpu.py")
    check(sha(old) == normalized_hash(protocol["original_driver_sha256"])
          and sha(new) == normalized_hash(protocol["new_driver_sha256"]),
          "timing protocol freezes both external driver versions")
    additions = (b"            cpu_started = time.process_time()\n",
                 b"                row[\"process_cpu_seconds\"] = time.process_time() - cpu_started\n")
    original = new
    for addition in additions:
        check(original.count(addition) == 1, "one explicit CPU diagnostic source addition")
        original = original.replace(addition, b"", 1)
    check(original == old, "follow-up driver differs only by CPU diagnostic reads")
    return protocol, commit


def performance_plan(run, report, git):
    count = report["pairs_per_case_mode"]
    check(type(count) is int and count in (5, 20), "declared fixed measurement sample count")
    check(report["timing_screen"] == {
        "maximum_candidate_to_control_median_ratio": 1.10,
        "timed_scope": "source loading, complete compilation and export; excludes output serialization",
        "alternation": "odd pairs control then candidate; even pairs candidate then control",
        "outlier_exclusion": False, "elapsed_speedup_claim": False},
        "unchanged complete-request elapsed timing protocol")
    arguments = report["command"]
    declared = [arguments[index + 1] for index, value in enumerate(arguments[:-1]) if value == "--pairs"]
    check((not declared and count == 5) or declared == [str(count)], "executed sample count agrees with declared plan")
    if count == 20:
        protocol, commit = timing_followup_protocol(run.parent.parent, git)
        check("execution/" + run.name == protocol["new_attempt"] and report["source_commit"] == commit
              and report["modes"] == ["decode_only"] and report["cases"] == list(PREFIX_CASES),
              "extended sample is the exact predeclared source and attempt")
        check(datetime.fromisoformat(protocol["created_at"]) < datetime.fromisoformat(report["started_at"]),
              "fixed timing follow-up protocol predates execution")
        check(normalized_hash(report["driver_sha256"]) == normalized_hash(protocol["new_driver_sha256"]),
              "extended attempt used the predeclared diagnostic driver")
    return count


def performance_attempt(run, report, git):
    frozen_reader(run, report, git)
    check(bool(report["modes"]) and set(report["modes"]) <= set(MODES)
          and len(report["modes"]) == len(set(report["modes"])) and bool(report["cases"])
          and set(report["cases"]) <= set(PREFIX_CASES)
          and len(report["cases"]) == len(set(report["cases"])), "declared mode and case inventory")
    pair_count = performance_plan(run, report, git)
    rows, outputs = {}, {}
    for path in sorted(run.glob("*/request-result.json")):
        row = document(path)
        check(row["name"] == path.parent.name and row["name"] not in rows, "unique actual request identity")
        rows[row["name"]] = row
        outputs[row["name"]] = request(run, row, report["source_commit"], git, True)
        if pair_count == 20:
            check(finite_positive(row["process_cpu_seconds"]), "follow-up retains positive CPU diagnostic per request")
    check(len(rows) == report["completed_request_count"] == len(report["requests"]) and
          {row["name"] for row in report["requests"]} == set(rows) and
          all(row == rows[row["name"]] for row in report["requests"]), "complete request inventory agrees with retained raw rows")
    ordered = sorted(rows.values(), key=lambda row: row["execution_sequence"])
    check([row["execution_sequence"] for row in ordered] == list(range(1, len(rows) + 1)),
          "actual execution sequence is complete and unique")
    expected_order = [(mode, case, index, arm) for mode in report["modes"] for case in report["cases"]
                      for index in range(1, pair_count + 1)
                      for arm in (("control", "candidate") if index % 2 else ("candidate", "control"))]
    check([(row["mode"], row["case_id"], row["pair_index"], row["arm"]) for row in ordered] == expected_order[:len(ordered)],
          "observed controls and candidates follow declared alternating order")
    summaries, pair_results, raw_comparisons = [], [], []
    for mode in report["modes"]:
        for case in report["cases"]:
            paired = []
            for index in range(1, pair_count + 1):
                names = {arm: f"{mode}-{case}-{index:02d}-{arm}" for arm in ("control", "candidate")}
                if not all(name in rows for name in names.values()):
                    continue
                control, candidate = rows[names["control"]], rows[names["candidate"]]
                a, b = control["work"]["counts"], candidate["work"]["counts"]
                delta = {key: a.get(key, 0) - b.get(key, 0) for key in sorted(a.keys() | b.keys())
                         if a.get(key, 0) != b.get(key, 0)}
                saved = control["operations"] - candidate["operations"]
                equivalent = outputs[names["control"]] == outputs[names["candidate"]] and outputs[names["control"]][0] is not None
                checks = {
                    "identical_complete_outputs": equivalent,
                    "identical_original_source_units": control["source_units"] == candidate["source_units"],
                    "positive_complete_shared_saving": saved > 0,
                    "complete_category_accounting": saved == control["work"]["operations"] - candidate["work"]["operations"] == sum(delta.values()),
                    "only_selected_scalar_work_changes": set(delta) <= {DECODE, COMPARE, DA, CA},
                    "same_numeric_cache_occupancy": control["work"]["cache_entries"] == candidate["work"]["cache_entries"],
                    "control_has_no_new_admissions": a.get(DA, 0) == a.get(CA, 0) == 0,
                    "decode_applicability": ((b.get(DA, 0) > 0 and delta.get(DECODE, 0) > 0) if mode != "compare_only"
                                             else b.get(DA, 0) == delta.get(DECODE, 0) == 0),
                    "comparison_applicability": ((b.get(CA, 0) > 0 and delta.get(COMPARE, 0) > 0) if mode != "decode_only"
                                                 else b.get(CA, 0) == delta.get(COMPARE, 0) == 0),
                }
                admissible = control["status"] == candidate["status"] == "passed" and all(checks.values())
                calculated = {"mode": mode, "case_id": case, "pair_index": index,
                    "shared_operations_saved": saved, "category_deltas_control_minus_candidate": delta,
                    "control_seconds": control["elapsed_seconds"], "candidate_seconds": candidate["elapsed_seconds"],
                    "complete_outputs_equal": equivalent, "all_pair_checks_passed": admissible}
                comparison = document(run / f"{mode}-{case}-{index:02d}-comparison.json")
                raw_comparisons.append(comparison)
                expected_comparison = {
                    "mode": mode, "case_id": case, "pair_index": index,
                    "control": names["control"], "candidate": names["candidate"],
                    "status": "passed" if admissible else "failed",
                    "glb_bytes_equal": outputs[names["control"]][0] == outputs[names["candidate"]][0],
                    "full_export_reports_equal": outputs[names["control"]][1] == outputs[names["candidate"]][1],
                    "source_units_equal": control["source_units"] == candidate["source_units"],
                    "shared_operations_saved": saved,
                    "reach_operations_saved": control["work"]["operations"] - candidate["work"]["operations"],
                    "category_deltas_control_minus_candidate": delta,
                    "gross_decode_omissions": delta.get(DECODE, 0), "gross_comparison_omissions": delta.get(COMPARE, 0),
                    "decode_admissions": b.get(DA, 0), "compare_admissions": b.get(CA, 0),
                    "control_seconds": control["elapsed_seconds"], "candidate_seconds": candidate["elapsed_seconds"],
                    "cache_occupancy_equal": checks["same_numeric_cache_occupancy"], "checks": checks,
                }
                check(comparison == expected_comparison,
                      "pair result independently reconstructed from bytes and counters", f"{mode}/{case}/{index}")
                paired.append(calculated)
                pair_results.append(calculated)
            if len(paired) != pair_count:
                continue
            left = [row["control_seconds"] for row in paired]
            right = [row["candidate_seconds"] for row in paired]
            ratio = statistics.median(right) / statistics.median(left)
            summary = {"mode": mode, "case_id": case, "pair_count": pair_count,
                "control_seconds": left, "candidate_seconds": right,
                "control_median_seconds": statistics.median(left), "candidate_median_seconds": statistics.median(right),
                "control_range_seconds": [min(left), max(left)], "candidate_range_seconds": [min(right), max(right)],
                "candidate_to_control_median_ratio": ratio,
                "timing_screen_passed": statistics.median(right) <= 1.10 * statistics.median(left),
                "shared_operation_savings": [row["shared_operations_saved"] for row in paired],
                "complete_outputs_equal": all(row["complete_outputs_equal"] for row in paired),
                "all_pair_checks_passed": all(row["all_pair_checks_passed"] for row in paired)}
            summaries.append(summary)
    check(report["summaries"] == summaries, "all timing medians and ranges independently recomputed", run.name)
    check(report["pairs"] == raw_comparisons and len(raw_comparisons) == len(pair_results)
          and len(list(run.glob("*-comparison.json"))) == len(raw_comparisons),
          "every completed pair retained exactly once in files and report", run.name)
    complete = len(ordered) == len(expected_order)
    passed = complete and bool(summaries) and all(row["timing_screen_passed"] and row["all_pair_checks_passed"] for row in summaries)
    check(report["status"] == ("passed" if passed else "failed"), "independently derived performance attempt status", run.name)
    return {"kind": "performance", "status": report["status"], "complete": complete,
            "requests": len(rows), "summaries": summaries, "pairs_per_case_mode": pair_count,
            "source_commit": report["source_commit"], "source_tree": report["source_tree"],
            "driver_sha256": report["driver_sha256"]}


def original_attempt(run, report, git):
    check(report["required_cases"] == list(SOURCE_CASES), "unchanged original 28-case source inventory")
    selected = report["selected_cases"]
    check(len(selected) == len(set(selected)) and set(selected) <= set(SOURCE_CASES), "unique selected original cases")
    rows = [document(run / case / "request-result.json") for case in selected]
    check(report["deliveries"] == rows and {path.parent.name for path in run.glob("*/request-result.json")} == set(selected),
          "complete original recording request inventory")
    for row in rows:
        request(run, row, report["source_commit"], git, False)
    failed = [row["case_id"] for row in rows if row["status"] != "passed"]
    check(report["status"] == ("failed" if failed else "passed") and
          report["complete_source_delivery_corpus"] is (not failed and set(selected) == set(SOURCE_CASES)),
          "original recording status honestly derives from every actual result")
    return {"kind": "original_recordings", "status": report["status"], "selected_cases": selected,
            "passed_count": len(rows) - len(failed), "failed_cases": failed,
            "operations": {row["case_id"]: row.get("operations") for row in rows},
            "source_commit": report["source_commit"], "source_tree": report["source_tree"]}


def pooled_timing(evidence, attempts, git):
    protocol, commit = timing_followup_protocol(evidence, git)
    names = [protocol["prior_same_runtime_attempt"], protocol["new_attempt"]]
    check(all(name in attempts for name in names), "both predeclared pooled attempts are present")
    prior, new = (attempts[name] for name in names)
    check(prior["source_commit"] == new["source_commit"] == commit
          and prior["source_tree"] == new["source_tree"] == git.tree(commit)["tree"]
          and prior["pairs_per_case_mode"] == 5 and new["pairs_per_case_mode"] == 20
          and prior["requests"] == 30 and new["requests"] == 120
          and prior["complete"] and new["complete"], "pool includes all five prior and twenty new pairs on identical source")
    check(normalized_hash(prior["driver_sha256"]) == normalized_hash(protocol["original_driver_sha256"])
          and normalized_hash(new["driver_sha256"]) == normalized_hash(protocol["new_driver_sha256"]),
          "pooled source attempts use the two protocol-frozen drivers")
    cases = []
    for case in PREFIX_CASES:
        previous = [row for row in prior["summaries"] if row["mode"] == "decode_only" and row["case_id"] == case]
        latest = [row for row in new["summaries"] if row["mode"] == "decode_only" and row["case_id"] == case]
        check(len(previous) == len(latest) == 1 and previous[0]["pair_count"] == 5 and latest[0]["pair_count"] == 20
              and previous[0]["all_pair_checks_passed"] and latest[0]["all_pair_checks_passed"],
              "every pooled pair independently passed exact output and complete-operation checks", case)
        left = previous[0]["control_seconds"] + latest[0]["control_seconds"]
        right = previous[0]["candidate_seconds"] + latest[0]["candidate_seconds"]
        fresh_medians = {"control": statistics.median(latest[0]["control_seconds"]),
                         "candidate": statistics.median(latest[0]["candidate_seconds"])}
        medians = {"control": statistics.median(left), "candidate": statistics.median(right)}
        cases.append({"case_id": case, "new_pairs": 20, "pooled_pairs": 25,
                      "new_medians_seconds": fresh_medians,
                      "new_median_ratio": fresh_medians["candidate"] / fresh_medians["control"],
                      "pooled_samples_seconds": {"control": left, "candidate": right},
                      "pooled_medians_seconds": medians,
                      "pooled_median_ratio": medians["candidate"] / medians["control"],
                      "passed": (fresh_medians["candidate"] <= 1.10 * fresh_medians["control"]
                                 and medians["candidate"] <= 1.10 * medians["control"])})
    expected = {"schema_version": "ontokin.native-field-pooled-timing/0.1",
                "protocol": "timing-followup-protocol.json", "attempts": names,
                "observations_excluded": 0, "maximum_median_ratio": 1.10, "cases": cases,
                "status": "passed" if all(row["passed"] for row in cases) else "failed",
                "source_commit": commit, "source_tree": git.tree(commit)["tree"]}
    check(document(evidence / "pooled-timing.json") == expected,
          "pooled timing receipt independently reconstructed from every raw request with no exclusions")
    return expected


def retained_decode_source(git, measured, published):
    """Prove the retained decode arm's complete active source is unchanged.

    The frozen decode driver disables _CertificateFieldComparisons.create.
    Only that unused comparison method and its five exact new alias statements
    may differ. Every other reader byte and other runtime/tool file must match.
    """
    before, after = git.tree(measured), git.tree(published)
    prefixes = ("ontokin/", "tools/")
    left = {name: blob for name, blob in before["blobs"].items() if name.startswith(prefixes) and name != READER}
    right = {name: blob for name, blob in after["blobs"].items() if name.startswith(prefixes) and name != READER}
    check(left == right, "retained decode source has identical remaining runtime and tool files")
    aliases = {
        "_FIELD_FRACTION_CLASS = Fraction",
        "_FIELD_NATIVE_TYPE, _FIELD_NATIVE_INT = type, int",
        "_FIELD_CLASS_READ, _FIELD_SLOT_READ = type.__getattribute__, object.__getattribute__",
        "_FIELD_GETTRACE, _FIELD_GETPROFILE = _term_sys.gettrace, _term_sys.getprofile",
        '_FIELD_FRACTION_ACCESS = tuple((name, saved) for kind, fields in _TERM_CLASS_FIELDS\n'
        '    if kind is Fraction for name, saved in fields\n'
        '    if name in (*_TERM_STORAGE, "numerator", "denominator", "_numerator", "_denominator"))',
    }
    records = []
    for commit in (measured, published):
        raw = git.source(commit, READER)
        source, lines = raw.decode(), raw.decode().splitlines(keepends=True)
        parsed = ast.parse(source)
        classes = [node for node in parsed.body if isinstance(node, ast.ClassDef)
                   and node.name == "_CertificateFieldComparisons"]
        check(len(classes) == 1, "one exact comparison context definition")
        methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == "compare"]
        check(len(methods) == 1 and not methods[0].decorator_list, "one direct comparison method definition")
        method = methods[0]
        replacements = [(method.lineno - 1, method.end_lineno, ["    # comparison method excluded from decode-only source binding\n"])]
        found = set()
        for node in parsed.body:
            segment = ast.get_source_segment(source, node)
            if isinstance(node, ast.Assign) and segment in aliases:
                check(segment not in found, "comparison-only alias statement occurs once")
                found.add(segment)
                replacements.append((node.lineno - 1, node.end_lineno, []))
        for start, end, replacement in sorted(replacements, reverse=True):
            lines[start:end] = replacement
        names = {"_CertificateFieldDecodes", "_certificate_fields_native", "_certificate_field_key",
                 "_certificate_term_native", "_certificate_raw_fields", "_certificate_fraction_fields",
                 "_term_function_state", "_CertificateBatch", "_complete_inequality_values"}
        unchanged = {node.name: sha(ast.get_source_segment(source, node).encode())
                     for node in parsed.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names}
        check(set(unchanged) == names, "all decode, gate and group-dispatch definitions are bound")
        records.append({"commit": commit, "tree": git.tree(commit)["tree"], "reader_sha256": sha(raw),
                        "comparison_method_sha256": sha(ast.get_source_segment(source, method).encode()),
                        "active_reader_sha256": sha("".join(lines).encode()),
                        "unchanged_definition_sha256": unchanged, "aliases": sorted(found)})
    check(not records[0]["aliases"] and set(records[1]["aliases"]) == aliases,
          "only the exact comparator-only native alias block was added")
    check(records[0]["active_reader_sha256"] == records[1]["active_reader_sha256"]
          and records[0]["unchanged_definition_sha256"] == records[1]["unchanged_definition_sha256"],
          "retained decode driver active source is byte-identical across measured and published cuts")
    return {"status": "passed", "measured_source": records[0], "published_source": records[1],
            "identical_other_runtime_and_tool_files": len(left),
            "scope": "Frozen decode-only driver disables comparison creation; all other reader bytes and runtime/tool files match."}


def recovered_core_log(run, summary, actual_output, named_log):
    """Keep the replaced named prefix and the producer's recovered bytes distinct."""
    recovery_path = run.parent / "recovery" / f"{run.name}-log-recovery.json"
    captured_path = run.parent / "recovery" / f"{run.name}-actual-unit-tests.log"
    recovery_raw = read(recovery_path)
    recovery, captured = decode(recovery_raw), read(captured_path)
    original = recovery["original"]
    check(recovery["method"] == "Opened only our test process regular output descriptor read-only; retained it across process completion; pread at zero never changes producer file offset"
          and recovery["core_process_finished"] is True and recovery["named_log_still_different_inode"] is True
          and recovery["product_process_modified"] is False,
          "recovery receipt retains its read-only observation scope and reported inode replacement")
    check(type(original["inode"]) is int and type(original["named_inode"]) is int
          and original["inode"] > 0 and original["named_inode"] > 0
          and original["inode"] != original["named_inode"]
          and original["target"] == str(actual_output / "logs/unit-tests.log") + " (deleted)",
          "recovery identifies the original producer log separately from the replaced named file")
    check(type(recovery["captured_bytes"]) is int and len(captured) == recovery["captured_bytes"]
          and sha(captured) == normalized_hash(recovery["sha256"])
          and type(original["bytes_at_open"]) is int and 0 < original["bytes_at_open"] <= len(captured),
          "recovered producer log matches its complete capture byte count and SHA-256")
    check(len(named_log) == original["named_bytes"] and len(named_log) < len(captured)
          and captured.startswith(named_log),
          "unchanged named log is verified separately as an exact prefix of recovered producer output")
    check(type(recovery["raw_tail"]) is str and bool(recovery["raw_tail"])
          and captured.endswith(recovery["raw_tail"].encode()), "recovery receipt tail matches actual retained bytes")
    check(datetime.fromisoformat(summary["started_at"]) <= datetime.fromisoformat(recovery["started_at"])
          <= datetime.fromisoformat(summary["finished_at"]) <= datetime.fromisoformat(recovery["finished_at"]),
          "recovery spans the actual core process completion")
    raw = captured.decode()
    check(not re.search(r"^Ran \d+ tests? in [0-9.]+s$", raw, re.MULTILINE)
          and not re.search(r"^(?:OK|FAILED)(?: \([^\n]*\))?$", raw, re.MULTILINE),
          "recovered producer output does not claim a completed unittest summary")
    markers = re.findall(r"^[ \t]*test\w* \(([^()\r\n]+)\)[^\r\n]* \.\.\. (FAIL|ERROR)$", raw, re.MULTILINE)
    outcomes = [{"test_id": identity, "status": {"FAIL": "failed", "ERROR": "error"}[status]}
                for identity, status in markers]
    check(len(outcomes) == 4 and Counter(item["status"] for item in outcomes) == {"failed": 3, "error": 1},
          "recovered partial output retains the four observed failure markers without inferring a suite total")
    return {"receipt": {"path": recovery_path.relative_to(run.parent).as_posix(), "bytes": len(recovery_raw), "sha256": sha(recovery_raw)},
            "recovered_log": {"path": captured_path.relative_to(run.parent).as_posix(), "bytes": len(captured), "sha256": sha(captured)},
            "named_log": {"path": run.name + "/logs/unit-tests.log", "bytes": len(named_log), "sha256": sha(named_log)},
            "named_log_is_exact_prefix": True, "full_regression_completed": False,
            "observed_failure_outcomes": outcomes, "historical_inode_values_are_receipt_evidence": True}


def core_local_attempt(run, receipts, git):
    """Audit the stock seven-step core profile as separate supplementary evidence."""
    summary = document(run / "summary.json")
    check(summary["schema_version"] == "ontokin.local-checks/0.1" and summary["profile"] == "core"
          and summary["selected_roles"] == ["core"] and summary["release_certified"] is False
          and summary["full_product_conformance_certified"] is False and summary["remote_checks_executed"] is False,
          "local core evidence retains its distinct limited role")
    receipt = receipts[run.name]
    args = receipt["command"]
    check(len(args) == 4 and Path(args[1]).name == "check_local.py" and args[2] == "--output-dir"
          and Path(args[3]).name == run.name and receipt["working_directory"] == summary["source_root"],
          "actual local command executes only the stock default core profile")
    script = Path(args[1]) if Path(args[1]).is_absolute() else Path(receipt["working_directory"]) / args[1]
    check(script == Path(summary["source_root"]) / "tools/check_local.py", "actual local driver belongs to the identified checkout")
    check(receipt["exit_status"] == summary["exit_code"] and summary["exit_code"] in (0, 1)
          and summary["status"] == ("passed" if summary["exit_code"] == 0 else "failed"),
          "local core actual exit and reported status agree")
    check(datetime.fromisoformat(receipt["started_at"]) <= datetime.fromisoformat(summary["started_at"])
          <= datetime.fromisoformat(summary["finished_at"]) <= datetime.fromisoformat(receipt["finished_at"]),
          "captured command encloses the complete local core run")
    metadata = summary["git"]
    check(metadata["available"] is True and metadata == summary["git_after"]
          and metadata["tracked_worktree_status"] == "" and metadata["untracked_source_files"] == []
          and summary["git_revision_unchanged"] is True and summary["source_unchanged"] is True,
          "local core reports unchanged clean source before and after")
    commit = metadata["local_head"]
    tree = git.tree(commit)
    check(tree["tree"] == metadata["local_tree"] and summary["workspace_git"]["available"] is True
          and summary["workspace_git"]["local_head"] == commit
          and summary["workspace_git"]["local_tree"] == tree["tree"], "local core and isolated workspace retain exact source identity")
    source = git.source(commit, "tools/check_local.py")
    constants = {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(source).body
                 if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                 and node.targets[0].id in {"SOURCE_DIRS", "ROOT_FILES", "IGNORED"}}
    def included(name):
        parts = PurePosixPath(name).parts
        return ((parts[0] in constants["SOURCE_DIRS"] or name in constants["ROOT_FILES"])
                and not any(part in constants["IGNORED"] or part == ".env" or part.startswith(".env.")
                            or part.endswith((".pyc", ".pyo")) for part in parts))
    def inventory(files):
        encoded = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        return {"sha256": "sha256:" + sha(encoded), "file_count": len(files), "files": files}
    # The stock core runner sorts Path objects, whose ordering is by component.
    expected = inventory(sorted((item for item in tree["files"] if included(item["path"])),
                                key=lambda item: PurePosixPath(item["path"])))
    check(document(run / "source-before.json") == document(run / "source-after.json") == expected,
          "complete local core source inventories independently match exact Git file bytes")
    member(run, summary["source_inventory"])
    check(summary["source_inventory"]["inventory_sha256"] == expected["sha256"]
          and summary["source_inventory"]["file_count"] == expected["file_count"]
          and summary["source_inventory"]["includes_untracked_source_files"] is True,
          "local core source receipt binds complete membership")
    workspace = document(run / "workspace-source-after.json")
    check(workspace == inventory(workspace["files"]), "retained post-run workspace inventory digest is independently reconstructed")
    exclusions = {"examples/visual/demo-data.js", "examples/visual/viewer.bundle.js", "examples/visual/THREE-LICENSE.txt",
                  *("examples/agent/" + name for name in ("workflow.json", "repaired.ok", "rejected-candidate.ok")),
                  *("examples/construction/" + name for name in ("workflow.json", "authoring.ok", "rejected-candidate.ok",
                       "main.ok", "hinges.ok", "program.bundle.json", "program.files.json"))}
    check(summary["workspace_generated_exclusions"] == {"files": sorted(exclusions),
          "patterns": ["examples/{visual,agent,construction}/*.{glb,export.json,reference.json}"],
          "scope": "Only the isolated workspace comparison; all original checkout example bytes are preserved and checked."},
          "workspace comparison uses only the stock runner's exact declared generated products")
    names = [item["path"] for item in workspace["files"]]
    check(names == sorted(set(names), key=PurePosixPath),
          "post-run workspace inventory has complete unique component-sorted member identities")
    for item in workspace["files"]:
        relative(item["path"])
        normalized_hash(item["sha256"])
        check(type(item["bytes"]) is int and item["bytes"] >= 0, "post-run workspace member has an actual byte count")
    def immutable(item):
        name = item["path"]
        return not (name in exclusions or (name.startswith(("examples/visual/", "examples/agent/", "examples/construction/"))
                    and name.endswith((".glb", ".export.json", ".reference.json"))))
    check([item for item in workspace["files"] if immutable(item)] == [item for item in expected["files"] if immutable(item)],
          "isolated workspace immutable source bytes independently remain unchanged")
    commands = {
        "unit-tests": ["-m", "unittest", "discover", "-s", "tests", "-v"],
        "source": ["-m", "ontokin", "conformance"], "agent": ["tools/run_agent_conformance.py"],
        "construction": ["-m", "tools.verify_construction_ci", "--external-evidence",
                         "docs/engineering/construction-validation/external-gate.json"],
        "surface": ["tools/run_surface_conformance.py", "--allow-pending"],
        "impulse": ["tools/run_impulse_conformance.py", "--allow-pending"],
        "documents": ["docs/maintenance/reorganization-2026-10-17/verify_reorganization.py"],
    }
    check(summary["planned_steps"] == [step["id"] for step in summary["steps"]] == list(commands)
          and summary["not_executed_steps"] == [], "all seven stock default core steps actually executed")
    actual_output = Path(args[3]) if Path(args[3]).is_absolute() else Path(receipt["working_directory"]) / args[3]
    pending, outcomes, test_count, completion, recovery = [], [], None, False, None
    for step in summary["steps"]:
        name = step["id"]
        extra = [] if name in ("unit-tests", "documents") else ["--output", str(actual_output / "reports" / f"{name}.json")]
        check(step["argv"][1:] == commands[name] + extra and step["requires"] == []
              and step["cwd"] == str(actual_output / "workspace"), "actual isolated core step matches default plan", name)
        log = member(run, {"path": step["log"], **step["log_identity"]})
        check(type(step["returncode"]) is int and step["status"] in ("passed", "failed")
              and (step["returncode"] == 0 or step["status"] == "failed"), "core step preserves actual subprocess exit", name)
        if name == "unit-tests":
            raw = log.decode()
            endings = re.findall(r"^(OK|FAILED)(?: \(([^\n]*)\))?$", raw, re.MULTILINE)
            executions = re.findall(r"^Ran (\d+) tests? in ([0-9.]+)s$", raw, re.MULTILINE)
            if executions and endings:
                counts = dict(re.findall(r"([a-z ]+)=(\d+)", endings[-1][1]))
                counts = {key.strip(): int(value) for key, value in counts.items()}
                test_count, skipped, expected_failures = int(executions[-1][0]), counts.get("skipped", 0), counts.get("expected failures", 0)
                passed = bool(test_count and not skipped and not expected_failures and endings[-1][0] == "OK" and step["returncode"] == 0)
                check(step["test_execution"] == {"tests_run": test_count, "skipped": skipped,
                    "expected_failures": expected_failures, "executed_without_skips": max(0, test_count - skipped),
                    "complete_regression_passed": passed} and step["status"] == ("passed" if passed else "failed"),
                    "actual full regression totals and completion independently derive from raw log")
                completion = True
            else:
                check(not executions and not endings and step["status"] == "failed" and step["returncode"] < 0
                      and step.get("reason") == "Exceeded 900 seconds" and step["duration_seconds"] >= 900,
                      "missing unittest summary is preserved only for the actual stock timeout and negative exit")
                check(step["test_execution"] == {"tests_run": 0, "skipped": 0, "expected_failures": 0,
                    "executed_without_skips": 0, "complete_regression_passed": False},
                    "stock zero parser sentinel records missing completion and is not treated as an actual test count")
                recovery = recovered_core_log(run, summary, actual_output, log)
        expected_reports = [] if not extra else [f"reports/{name}.json"]
        check([item["path"] for item in step["reports"]] == expected_reports, "every expected core report retained", name)
        for item in step["reports"]:
            data = decode(member(run, item))
            derived = {key: data[key] for key in ("status", "summary", "full_gate_complete", "implementation",
                       "full_force_release_complete", "destination_validated") if key in data}
            cases = [{"id": case.get("id"), "reasons": case.get("pending_reasons", [])}
                     for case in data.get("cases", []) if case.get("status") == "pending"]
            check(item["outcomes"] == derived and item["pending_cases"] == cases,
                  "core outcome and pending-case receipts match complete report bytes", name)
            pending.extend(dict(step=name, report=item["path"], **case) for case in cases)
        outcomes.append({"id": name, "status": step["status"], "returncode": step["returncode"],
                         "duration_seconds": step["duration_seconds"],
                         **({"reason": step["reason"]} if "reason" in step else {})})
    check(summary["pending_external_cases"] == pending
          and summary["status"] == ("passed" if all(step["status"] == "passed" for step in outcomes) else "failed"),
          "local core aggregate and external pending cases independently reconcile")
    return {"kind": "supplementary_local_core", "status": summary["status"], "unit_tests": test_count,
            "unit_test_completion": completion, "unit_log_recovery": recovery,
            "unit_test_count_scope": "completed unittest summary" if completion else "unknown; stock parser zero is only a missing-summary sentinel",
            "source_commit": commit, "source_tree": tree["tree"], "steps": outcomes,
            "pending_external_cases": pending, "full_raw_regression_log_retained": completion,
            "raw_unit_output_through_termination_retained": completion or recovery is not None,
            "stock_driver_sha256": sha(source), "release_certified": False}


def regression_failure_reproductions(attempts, core, git):
    names = ("execution/baseline-regression-failures-001", "execution/integrated-regression-failures-001")
    check(all(name in attempts for name in names), "both actual four-method failure reproductions are retained")
    baseline, integrated = (attempts[name] for name in names)
    observed = core["unit_log_recovery"]["observed_failure_outcomes"]
    key = lambda row: (row["test_id"], row["status"])
    for name, item in zip(names, (baseline, integrated)):
        check(item["kind"] == "tests" and item["status"] == "failed" and item["test_count"] == 4
              and item.get("passed", 0) == 0 and item.get("failed", 0) == 3
              and item.get("error", 0) == 1 and item.get("skipped", 0) == 0
              and sorted(item["unsuccessful_test_outcomes"], key=key) == sorted(observed, key=key),
              "four-method reproduction preserves the observed identities and three failures plus one error", name)
    check(baseline["source_commit"] == BASELINE and integrated["source_commit"] == core["source_commit"],
          "failure reproductions bind separately to unchanged baseline and actual published core source")
    modules = {item["test_id"].split(".")[0] for item in observed}
    for module in modules:
        path = "tests/" + module + ".py"
        check(git.source(BASELINE, path) == git.source(integrated["source_commit"], path),
              "reproduced test definition bytes are unchanged between baseline and published source", module)
    return {"status": "validated_failed_reproductions", "attempts": list(names), "outcomes": observed,
            "baseline_source_commit": BASELINE, "integrated_source_commit": integrated["source_commit"],
            "scope": "Only the four observed failure identities and statuses; no completed full-suite result or absence of further failures is inferred.",
            "full_regression_completed": False, "full_regression_accepted": False}


def selection(checkpoint, attempts, git, pooled, current, supplementary):
    keys = {"focused", "decode_controls", "compare_controls", "combined_controls", "related", "original_p09", "original28"}
    check(set(checkpoint["execution"]) >= keys, "checkpoint declares every accepted execution selection")
    selected = {}
    for key in sorted(keys):
        name = checkpoint["execution"][key]
        check(type(name) is str and relative(name).parts[0] == "execution" and len(relative(name).parts) == 2,
              "selected attempt is an explicit execution directory", key)
        check(name in attempts, "selected attempt exists and was independently audited", name)
        selected[key] = attempts[name]
    for key in ("focused", "related"):
        check(selected[key]["kind"] == "tests" and selected[key]["status"] == "passed"
              and selected[key].get("passed") == selected[key]["test_count"], "selected test requirement passed", key)
    for key, mode in (("decode_controls", "decode_only"), ("compare_controls", "compare_only"), ("combined_controls", "combined")):
        item = selected[key]
        check(item["kind"] == "performance" and item["status"] == "passed" and item["complete"], "selected measured transformation passed", key)
        summaries = [row for row in item["summaries"] if row["mode"] == mode]
        count = 20 if key == "decode_controls" else 5
        check(len(summaries) == 3 and {row["case_id"] for row in summaries} == set(PREFIX_CASES)
              and all(row["pair_count"] == count for row in summaries),
              "selected mode covers every case at its fixed predeclared sample count", mode)
    check(checkpoint["results"]["decode_controls"] == {
        "expected_pairs_per_case": 20, "pooled_timing": "pooled-timing.json"}
          and pooled is not None and pooled["status"] == "passed"
          and checkpoint["execution"]["decode_controls"] == pooled["attempts"][1],
          "extended decode selection passes both independent new and pooled timing requirements")
    p09, full = selected["original_p09"], selected["original28"]
    check(p09["kind"] == full["kind"] == "original_recordings" and p09["selected_cases"] == ["P09"]
          and full["selected_cases"] == list(SOURCE_CASES), "selected stock P09 and original28 are complete requests")
    check(checkpoint["results"]["original_p09"] == {"status": p09["status"], "operations": p09["operations"]["P09"]},
          "checkpoint P09 outcome matches actual request")
    check(checkpoint["results"]["original28"] == {"status": full["status"], "passed_count": full["passed_count"],
                                                 "failed_cases": full["failed_cases"]}, "checkpoint original28 outcome matches every row")
    published = checkpoint["published_source_commit"]
    published_tree = git.tree(published)
    for key in ("related", "original_p09", "original28"):
        check(selected[key]["source_commit"] == published,
              "integrated requirement executed on the exact published source commit", key)
    binding = lambda commit: {name: blob for name, blob in git.tree(commit)["blobs"].items()
                              if name.startswith(("ontokin/", "tools/", "tests/"))}
    final_bindings = binding(published)
    for key in keys - {"decode_controls"}:
        check(binding(selected[key]["source_commit"]) == final_bindings,
              "final selected role uses published runtime, tools and test bytes", key)
    check(binding(current["commit"]) == final_bindings,
          "current source retains the published runtime, tools and test bytes")
    decode_binding = retained_decode_source(git, selected["decode_controls"]["source_commit"], published)
    core = None
    if "core_local" in checkpoint["execution"]:
        name = checkpoint["execution"]["core_local"]
        check(name in supplementary and supplementary[name]["kind"] == "supplementary_local_core",
              "selected local core evidence remains a separate audited role")
        core = supplementary[name]
        check(core["source_commit"] == published and checkpoint["results"]["core_local"] == {
            "status": core["status"], "unit_tests": core["unit_tests"]},
              "checkpoint local core outcome and actual count bind to published source")
    commits = {item["source_commit"] for item in selected.values()}
    check(checkpoint["release_acceptance"] is False and checkpoint["full_product_goal_completed"] is False,
          "finite development evidence does not close release or full product goal")
    return {"status": "validated_selected_development_evidence", "selections": {key: checkpoint["execution"][key] for key in sorted(keys)},
            "source_commits": sorted(commits), "original_p09": checkpoint["results"]["original_p09"],
            "original28": checkpoint["results"]["original28"], "published_source_commit": published,
            "published_source_tree": published_tree["tree"], "retained_decode_source_equivalence": decode_binding,
            "supplementary_local_core": core}


def archive_evidence_inventory(evidence):
    """Inventory every retained file using only the packer's two exclusions."""
    files, excluded, pending = {}, [], [evidence]
    while pending:
        directory = pending.pop()
        for path in sorted(directory.iterdir()):
            name = path.relative_to(evidence).as_posix()
            relative(name)
            mode = path.lstat().st_mode
            check(not stat.S_ISLNK(mode), "archive evidence contains no symlink", name)
            if stat.S_ISDIR(mode):
                if name == "local-core-001/workspace" or path.name == "__pycache__":
                    excluded.append(name)
                else:
                    pending.append(path)
            else:
                check(stat.S_ISREG(mode) and name not in files,
                      "archive evidence contains unique regular files only", name)
                files[name] = path
    check(bool(files), "complete retained evidence inventory is nonempty")
    return files, sorted(excluded)


def archive_check(checkpoint, manifest_path, archive_base, evidence):
    retained, excluded = archive_evidence_inventory(evidence)
    manifest_raw = read(manifest_path)
    manifest = decode(manifest_raw)
    archive = checkpoint["archive"]
    if "manifest_sha256" in checkpoint:
        check(normalized_hash(checkpoint["manifest_sha256"]) == sha(manifest_raw), "checkpoint binds exact manifest bytes")
    parts, paths = [], []
    for index, part in enumerate(archive["parts"], 1):
        check(part["path"].endswith(f".part{index:03d}"), "ordered archive part numbering", part["path"])
        paths.append(part["path"])
        parts.append(member(archive_base, part))
    joined = b"".join(parts)
    check(paths and len(paths) == len(set(paths)) and len(joined) == archive["bytes"] and
          sha(joined) == normalized_hash(archive["sha256"]), "complete ordered archive size and digest")
    members = manifest["members"]
    expected = {}
    for item in members:
        relative(item["path"])
        check(item["path"] not in expected and type(item["bytes"]) is int and item["bytes"] >= 0,
              "unique archive manifest member with an actual byte count", item["path"])
        expected[item["path"]] = item
    check(set(expected) == set(retained),
          "archive manifest exactly covers every retained evidence file with only the two declared exclusions",
          {"retained_files": len(retained), "missing": sorted(set(retained) - set(expected)),
           "extra": sorted(set(expected) - set(retained)), "excluded_directories": excluded})
    with zipfile.ZipFile(io.BytesIO(joined)) as zipped:
        infos = zipped.infolist()
        check(len(infos) == len(expected) == archive["member_count"] and
              {info.filename for info in infos} == set(expected), "ZIP exact membership and no duplicate members")
        for info in infos:
            relative(info.filename)
            check(not info.is_dir() and stat.S_ISREG(info.external_attr >> 16), "regular safe ZIP member", info.filename)
            raw = zipped.read(info)
            item = expected[info.filename]
            check(len(raw) == info.file_size == item["bytes"] and sha(raw) == normalized_hash(item["sha256"]),
                  "ZIP member size, SHA-256 and CRC", info.filename)
            check(read(contained(evidence, info.filename)) == raw, "expanded evidence matches ZIP member exactly", info.filename)
        check(zipped.testzip() is None, "all ZIP CRCs valid")
    after, exclusions_after = archive_evidence_inventory(evidence)
    check(set(after) == set(retained) and exclusions_after == excluded,
          "complete retained evidence membership remains stable across archive verification")
    return {"parts": len(parts), "members": len(expected), "bytes": len(joined), "sha256": sha(joined),
            "membership_scope": "Every regular evidence file; only local-core-001/workspace and generated __pycache__ directories are excluded.",
            "retained_evidence_files": len(retained), "excluded_directories": excluded,
            "uncompressed_member_bytes": sum(item["bytes"] for item in members)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--archive-base", type=Path)
    parser.add_argument("--verbose-checks", action="store_true",
                        help="Also retain every individual successful check; default reports totals, named counts and every failure.")
    args = parser.parse_args()
    evidence, repo, output = args.evidence.resolve(), args.repo.resolve(), args.output.absolute()
    check(not output.exists() and not output.resolve().is_relative_to(evidence), "audit output is fresh and outside evidence")
    report = {"schema_version": "ontokin.native-fields-evidence-audit/0.1", "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(), "command": [sys.executable, *sys.argv],
        "auditor_sha256": sha(read(Path(__file__))), "product_code_imported_or_executed": False,
        "release_acceptance": False, "full_product_goal_completed": False, "attempts": {}, "supplementary_attempts": {},
        "selected_development_evidence": {"status": "pending_explicit_checkpoint_selection"}}
    try:
        git = GitInputs(repo)
        report["current_source"] = current_checkout(git)
        receipts = command_receipts(evidence)
        directories = sorted(path for path in (evidence / "execution").iterdir() if path.is_dir())
        for run in directories:
            item = document(run / "report.json")
            bind_command(run, item, receipts)
            snapshots(run, item, git)
            check(item.get("release_acceptance") is False and item.get("full_product_goal_completed") is False,
                  "attempt does not overstate release scope", run.name)
            schema = item["schema_version"]
            if schema == "ontokin.native-field-development-tests/0.1":
                result = test_attempt(run, item, git)
            elif schema == "ontokin.native-certificate-field-controls/0.1":
                result = performance_attempt(run, item, git)
            elif schema == "ontokin.reach-source-delivery/0.1":
                result = original_attempt(run, item, git)
            else:
                raise ValueError(f"Unknown execution schema: {schema}")
            report["attempts"]["execution/" + run.name] = result
        historical = report["attempts"]
        first, second = historical["execution/candidate-focused-001"], historical["execution/candidate-focused-002"]
        check(first["status"] == "failed" and first["test_count"] == 110 and first.get("passed") == 109 and
              first.get("error") == 1 and not first.get("failed", 0) and not first.get("skipped", 0),
              "actual first focused failure remains 109 passes and one error")
        check(second["status"] == "passed" and second["test_count"] == second.get("passed") == 110,
              "actual repaired focused run remains 110 passes")
        hook = historical["execution/candidate-hook-regression-001"]
        check(hook["status"] == "failed" and hook["test_count"] == 2 and hook.get("passed") == 1
              and hook.get("error") == 1 and not hook.get("failed", 0) and not hook.get("skipped", 0),
              "actual late-hook regression failure remains one pass and one error")
        final_focused = historical["execution/candidate-focused-005"]
        check(final_focused["status"] == "passed" and final_focused["test_count"] == final_focused.get("passed") == 115,
              "actual final focused run retains all 115 passes")
        failed_timing = historical["execution/decode-controls-001"]
        check(failed_timing["status"] == "failed" and failed_timing["requests"] == 30 and
              any(row["case_id"] == "P11" and not row["timing_screen_passed"] for row in failed_timing["summaries"]),
              "initial decode timing failure remains separately visible")
        if (evidence / "pooled-timing.json").is_file():
            report["pooled_timing"] = pooled_timing(evidence, historical, git)
        for run in sorted(evidence.glob("local-core-*")):
            if run.is_dir():
                report["supplementary_attempts"][run.name] = core_local_attempt(run, receipts, git)
        core = report["supplementary_attempts"].get("local-core-001")
        if core is not None and core["unit_test_completion"] is False:
            report["regression_failure_reproductions"] = regression_failure_reproductions(historical, core, git)
        if args.checkpoint:
            checkpoint = document(args.checkpoint)
            report["selected_development_evidence"] = selection(checkpoint, historical, git, report.get("pooled_timing"),
                                                                report["current_source"], report["supplementary_attempts"])
            if args.manifest or args.archive_base:
                check(args.manifest is not None and args.archive_base is not None, "complete archive audit inputs")
                report["archive"] = archive_check(checkpoint, args.manifest, args.archive_base.resolve(), evidence)
        else:
            check(args.manifest is None and args.archive_base is None, "archive audit requires checkpoint selection")
        report["preserved_failed_attempts"] = sorted(name for name, item in
            {**historical, **report["supplementary_attempts"]}.items() if item["status"] == "failed")
        report["source_commits"] = sorted(git.trees)
        check(git.git("rev-parse", "HEAD").decode().strip() == report["current_source"]["commit"]
              and git.git("status", "--porcelain").decode().strip() == "",
              "current source commit and clean state remain stable across the complete audit")
        report["status"] = "passed"
    except Exception as error:
        report.update(status="failed", failure={"type": type(error).__name__, "message": str(error)}, traceback=traceback.format_exc())
    named = {}
    for row in CHECKS:
        counts = named.setdefault(row["name"], {"passed": 0, "failed": 0, "total": 0})
        counts["passed" if row["passed"] else "failed"] += 1
        counts["total"] += 1
    report.update(finished_at=datetime.now(timezone.utc).isoformat(),
                  check_detail_mode="verbose" if args.verbose_checks else "compact",
                  total_checks=len(CHECKS),
                  passed_checks=sum(row["passed"] for row in CHECKS),
                  failed_checks=sum(not row["passed"] for row in CHECKS),
                  check_counts_by_name={name: named[name] for name in sorted(named)},
                  failed_check_details=[row for row in CHECKS if not row["passed"]])
    if args.verbose_checks:
        report["checks"] = CHECKS
    with output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: report.get(key) for key in ("status", "passed_checks", "failed_checks", "failure")}), flush=True)
    return int(report["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
