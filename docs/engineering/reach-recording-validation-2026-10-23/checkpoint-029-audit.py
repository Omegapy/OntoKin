#!/usr/bin/env python3
"""Independently audit checkpoint 029 capture evidence; never run the product.

This standard-library reader checks the actual failed requests, original Git
inputs, neutral wrappers, independently decoded GLB clocks/groups, and census
accounting. A static unvisited tail remains a conditional model. Optional ZIP
checking verifies ordered parts, member hashes, CRCs, and exact expanded bytes.
Run from any checkout retaining the original source Git objects. Keep output
outside the evidence directory so that auditing cannot change its own inputs.
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
import re
import stat
import struct
import subprocess
import sys
import traceback
import zipfile


SOURCE = "91c28f839ae29881d0f8e1287b10bdafa2804361"
TREE = "c9c13c27c58f6e3a88a23cb54483c00d2baebebf"
FILE_COUNT = 1784
CAPTURE_SHA = "1f160b25e1f0f0d9b037332e8bfb73edccd1b392cb2a303ce70171085aa46282"
COMPARE_SHA = "f62b769b8d1d30b9b9cad159273e17b8fc01da81af6b50c570a6534c2e820a05"
NEUTRALITY_SHA = "beb1b458e8a34ffe9f7cc02c9751a02af04d8539b8fb8b4c246bf852ea63f03e"
PREDECESSOR_SHA = "693b0e03b8906710567c33f7f676cb3e29c57f78db84150e25fafaae49f3d487"
RUNNER_SHA = "ccb9fa0bd93bb692c401af9562251e3301694515c6fca3b8ccc3198dbb4fb5eb"
BASE = "docs/language-design/planar-reach-v0.1/"
HISTORY = "docs/engineering/reach-recording-validation-2026-10-23/"
STOCK = "execution/stock-p09-001/"
CAPTURE = "execution/capture-p09-001/"
OPTIONS = {"end": "3", "fps": 1.0, "helpers": False,
           "position_tolerance_m": .001, "rotation_tolerance_rad": .001,
           "time_tolerance_s": .000001}
WORK_LIMITS = {"max_operations": 100000, "max_elapsed_ms": 30000,
               "max_operand_bits": 32768, "max_cache_entries": 256}
CONSTRUCTION_LIMITS = {"max_objects": 1000, "max_operations": 100000,
                       "max_result_items": 1000, "max_elapsed_ms": 30000,
                       "max_value_entries": 100000}
NUMERIC_KEYS = tuple(sorted((
    "landmark_radius_m", "local_vertex_error_bound_m",
    "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
    "enclosing_carrier_speed_bound_m_per_s",
    "enclosing_carrier_acceleration_bound_m_per_s2",
    "enclosing_angular_speed_bound_rad_per_s", "max_endpoint_time_shift_s",
    "max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error",
    "stored_quaternion_arc_upper_rad", "source_numeric_position_bound_m",
    "source_numeric_rotation_bound_rad", "destination_numeric_position_bound_m",
    "destination_numeric_rotation_bound_rad", "unit_quaternion_difference_bound",
    "ideal_rotation_bound_rad", "ideal_position_bound_m", "carrier_position_bound_m",
    "total_position_bound_m", "total_rotation_bound_rad")))
ROW_KEYS = set(NUMERIC_KEYS) | {"left_key_index", "right_key_index", "carrier",
    "source_phase_indices", "h_authored_seconds", "h_stored_seconds"}
MINIMUM_ORDER = ("landmark_radius_m", "local_vertex_error_bound_m",
    "angular_speed_bound_rad_per_s", "carrier_acceleration_bound_m_per_s2",
    "enclosing_carrier_speed_bound_m_per_s", "enclosing_carrier_acceleration_bound_m_per_s2",
    "enclosing_angular_speed_bound_rad_per_s", "max_endpoint_time_shift_s",
    "max_endpoint_position_error_m", "max_endpoint_unit_quaternion_error",
    "stored_quaternion_arc_upper_rad", "source_numeric_position_bound_m",
    "source_numeric_rotation_bound_rad")
IDENTITIES = {"validate_export_restored", "flush_restored", "native_dispatch_preserved",
    "no_trace_hook", "no_profile_hook", "reader_owner_preserved",
    "reader_arguments_preserved", "reader_external_preserved", "reader_observer_restored",
    "same_callback_error_at_reader_exit", "external_callback_preserved",
    "native_callback_owner_preserved", "construction_check_preserved",
    "observer_restored_after_request", "callback_error_preserved",
    "work_limits_unchanged", "budget_limits_unchanged"}
FLUSH_IDENTITIES = {"work_preserved", "external_preserved", "observer_preserved_within_flush"}
STAGE_COUNTS = {"independent_retained_clock": 205,
    "independent_certificate_identity": 1224, "independent_certificate_member": 1224,
    "independent_certificate_group": 12, "independent_certificate_group_check": 11,
    "independent_certificate_term_admission": 10}
CENSUS_FALSE = {"imports_ontokin", "product_runtime_executed", "release_acceptance",
    "successful_export_claimed", "measured_full_cost_claimed", "measured_savings_claimed",
    "captured_source_minima_independently_certified",
    "operation_neutrality_certified_by_this_census"}
MAX_FILE = 64 * 1024 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result

    def reject(value):
        raise ValueError("Nonfinite JSON number: " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=reject)


def relative(value):
    path = PurePosixPath(value)
    if (type(value) is not str or not value or "\\" in value or "\0" in value
            or path.is_absolute() or str(path) != value
            or any(part in (".", "..") for part in path.parts)):
        raise ValueError("Noncanonical relative evidence path")
    return path


def exact_true(record, keys):
    return type(record) is dict and set(record) == set(keys) and all(value is True for value in record.values())


def exact_flags(record, expected):
    return (type(record) is dict and set(record) == set(expected)
        and all(record[key] is value for key, value in expected.items()))


def decimal(text):
    if type(text) is not str or len(text) > 10000 or not re.fullmatch(r"0|-?[1-9][0-9]*", text):
        raise ValueError("Invalid bounded canonical integer")
    negative = text.startswith("-")
    text = text[1:] if negative else text
    value = 0
    for offset in range(0, len(text), 1000):
        part = text[offset:offset + 1000]
        value = value * 10 ** len(part) + int(part)
    if value.bit_length() > 32768:
        raise ValueError("Captured integer exceeds original operand cap")
    return -value if negative else value


def rational(record):
    if type(record) is not dict or set(record) not in (
            {"numerator", "denominator"},
            {"numerator", "denominator", "numerator_bits", "denominator_bits"}):
        raise ValueError("Invalid rational record")
    numerator, denominator = decimal(record["numerator"]), decimal(record["denominator"])
    if denominator <= 0:
        raise ValueError("Nonpositive rational denominator")
    value = Fraction(numerator, denominator)
    if value.numerator != numerator or value.denominator != denominator:
        raise ValueError("Unreduced rational record")
    if "numerator_bits" in record and (record["numerator_bits"] != numerator.bit_length()
            or record["denominator_bits"] != denominator.bit_length()):
        raise ValueError("Incorrect rational field widths")
    return value


def number(value):
    if type(value) not in (int, float) or value < 0 or type(value) is float and not math.isfinite(value):
        raise ValueError("Invalid nonnegative native JSON scalar")
    if type(value) is int and value.bit_length() > 32768:
        raise ValueError("Numeric key exceeds original operand cap")
    return Fraction(value)


def same_number(first, last):
    return (type(first) is type(last) and (struct.pack(">d", first) == struct.pack(">d", last)
            if type(first) is float else first == last))


def work_valid(record):
    return (type(record) is dict and set(record) == {"operations", "counts", "cache_entries"}
        and type(record["operations"]) is int and record["operations"] >= 0
        and type(record["cache_entries"]) is int and 0 <= record["cache_entries"] <= 256
        and type(record["counts"]) is dict and 0 < len(record["counts"]) <= 512
        and all(type(key) is str and type(value) is int and value > 0 for key, value in record["counts"].items())
        and sum(record["counts"].values()) == record["operations"])


def frames(text):
    return [{"file": name, "line": int(line), "function": function.strip()}
        for name, line, function in re.findall(r'File "([^"]+)", line (\d+), in ([^\n]+)', text)]


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Naive execution timestamp")
    return result


class AuditFailure(Exception):
    pass


class Audit:
    def __init__(self, repo, evidence):
        self.repo, self.evidence = repo.resolve(), evidence.resolve()
        self.checks, self.inputs, self.source, self.source_bytes = [], {}, {}, {}
        self.details = {}

    def check(self, condition, label, details=None):
        row = {"check": label, "passed": bool(condition)}
        if details is not None:
            row["details"] = details
        self.checks.append(row)
        return bool(condition)

    def need(self, condition, label, details=None):
        if not self.check(condition, label, details):
            raise AuditFailure(label)

    def read_path(self, path, maximum=MAX_FILE):
        path = Path(path).absolute()
        for part in (path, *path.parents):
            if part.is_symlink():
                raise ValueError("Audit input uses a symlink: " + str(path))
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= maximum:
            raise ValueError("Nonregular or excessive audit input: " + str(path))
        raw = path.read_bytes()
        after = path.stat()
        if len(raw) != before.st_size or before.st_size != after.st_size or before.st_mtime_ns != after.st_mtime_ns:
            raise ValueError("Audit input changed while being read: " + str(path))
        identity = {"bytes": len(raw), "sha256": digest(raw)}
        key = str(path)
        if key in self.inputs and self.inputs[key] != identity:
            raise ValueError("Audit input changed between reads: " + key)
        self.inputs[key] = identity
        return raw

    def raw(self, name):
        return self.read_path(self.evidence / relative(name))

    def doc(self, name):
        return decode(self.raw(name))

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args])

    def source_inventory(self, inventories):
        first = inventories[0]
        self.need(all(value == first for value in inventories), "Four complete source inventories are identical")
        self.need(first.get("scope") == "all_tracked_repository_file_bytes"
            and first.get("git") == {"commit": SOURCE, "tree": TREE, "status": ""},
            "Inventories identify the original clean source commit and tree")
        rows = first["files"]
        names = [row["path"] for row in rows]
        self.need(len(rows) == len(set(names)) == FILE_COUNT and names == sorted(names),
            "Complete source inventory has 1784 unique sorted paths")
        commit = self.git("cat-file", "commit", SOURCE)
        self.need(hashlib.sha1(b"commit " + str(len(commit)).encode() + b"\0" + commit).hexdigest() == SOURCE
            and commit.splitlines()[0] == b"tree " + TREE.encode()
            and self.git("rev-parse", SOURCE + "^{tree}").decode().strip() == TREE,
            "Original Git commit object and root tree identities verify")
        tree = {}
        for entry in self.git("ls-tree", "-r", "-z", SOURCE).split(b"\0"):
            if not entry:
                continue
            header, filename = entry.split(b"\t", 1)
            mode, kind, blob = header.decode("ascii").split()
            name = filename.decode("utf-8")
            relative(name)
            if mode not in ("100644", "100755") or kind != "blob" or name in tree:
                raise ValueError("Unexpected Git tree entry")
            tree[name] = {"mode": mode, "blob": blob}
        self.need(set(tree) == set(names) and len(tree) == FILE_COUNT,
            "Snapshot path coverage exactly matches the observed Git tree")
        expected = {row["path"]: row for row in rows}
        retain = {"ontokin/reach_conformance.py", "ontokin/gltf.py", "ontokin/reach_numeric.py",
            "ontokin/reach_reference_plan.py", "tools/build_reach_source_artifacts.py",
            HISTORY + "checkpoint-028-manifest.json", HISTORY + "checkpoint-027-manifest.json",
            BASE + "p09.files.json", BASE + "sources/p09-principal-shoulder-wrap.ok",
            BASE + "libraries/reach-assets.ok", BASE + "libraries/reach-exterior.ok",
            BASE + "libraries/reach-parts.ok"}
        mismatches, total = [], 0
        process = subprocess.Popen(["git", "-C", str(self.repo), "cat-file", "--batch"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for name in names:
                blob = tree[name]["blob"]
                process.stdin.write((blob + "\n").encode()); process.stdin.flush()
                header = process.stdout.readline().decode("ascii").strip().split()
                if len(header) != 3 or header[:2] != [blob, "blob"]:
                    raise ValueError("Missing original source blob: " + name)
                size = int(header[2])
                if not 0 <= size <= MAX_FILE:
                    raise ValueError("Unexpected original source blob size")
                h1 = hashlib.sha1(b"blob " + str(size).encode() + b"\0")
                h256, remaining, collected = hashlib.sha256(), size, []
                while remaining:
                    part = process.stdout.read(min(1024 * 1024, remaining))
                    if not part:
                        raise ValueError("Truncated Git blob stream")
                    h1.update(part); h256.update(part); remaining -= len(part)
                    if name in retain:
                        collected.append(part)
                if process.stdout.read(1) != b"\n":
                    raise ValueError("Malformed Git blob delimiter")
                actual = {"path": name, "bytes": size, "sha256": "sha256:" + h256.hexdigest()}
                if h1.hexdigest() != blob or actual != expected[name]:
                    mismatches.append(name)
                self.source[name] = {**actual, **tree[name]}
                if name in retain:
                    self.source_bytes[name] = b"".join(collected)
                total += size
            process.stdin.close()
            errors = process.stderr.read()
            if process.wait() or errors:
                raise ValueError("Git blob reader did not complete cleanly")
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
        self.need(not mismatches, "Every original tracked file matches its Git blob, size and SHA-256",
            {"files": len(rows), "bytes": total, "mismatches": mismatches})
        self.details["source_inventory"] = {"commit": SOURCE, "tree": TREE, "files": len(rows), "bytes": total}

    def command(self, name, exit_code, cwd, script, arguments, executable, within=()):
        receipt = self.doc("commands/" + name + ".json")
        command = receipt["command"]
        self.need(type(command) is list and len(command) >= 2 and command[0] in (executable, Path(executable).name)
            and str(PurePosixPath(cwd) / command[1]) == str(PurePosixPath(script))
            and command[2:] == arguments and receipt["cwd"] == cwd
            and type(receipt["exit_code"]) is int and receipt["exit_code"] == exit_code,
            "Actual command, working directory and exit status: " + name)
        start, end = timestamp(receipt["started_at"]), timestamp(receipt["finished_at"])
        elapsed = receipt["elapsed_seconds"]
        self.need(type(elapsed) in (int, float) and math.isfinite(elapsed) and elapsed > 0
            and end >= start and abs((end - start).total_seconds() - elapsed) < 1
            and all(start <= timestamp(value) <= end for value in within),
            "Command timestamps bind execution and report: " + name)
        self.need(self.raw("commands/" + name + ".stderr.txt") == b"",
            "Retained command stderr is empty: " + name)
        return receipt, self.raw("commands/" + name + ".stdout.txt")

    def remap_identity(self, name):
        path = PurePosixPath(name)
        if path.is_relative_to(self.original_evidence):
            raw = self.raw(path.relative_to(self.original_evidence).as_posix())
            return len(raw), digest(raw)
        if path.is_relative_to(self.original_repo):
            row = self.source[path.relative_to(self.original_repo).as_posix()]
            return row["bytes"], row["sha256"].removeprefix("sha256:")
        if path.name == "request-result.json" and path.parts[-3:] == ("candidate-original28-001", "P09", "request-result.json"):
            raw = self.raw("historical/checkpoint028-P09-request-result.json")
            return len(raw), digest(raw)
        if re.fullmatch(r"analyze_p09_full_input(?:_v[0-9]+)?\.py", path.name):
            raw = self.raw("drivers/" + path.name)
            return len(raw), digest(raw)
        raise ValueError("Unmapped original audit input: " + name)

    def requests(self):
        baseline = self.doc(STOCK + "report.json")
        wrapped = self.doc(CAPTURE + "stock/report.json")
        before = self.doc(STOCK + "P09/request-result.json")
        after = self.doc(CAPTURE + "stock/P09/request-result.json")
        capture = self.doc(CAPTURE + "capture.json")
        snapshot_doc = self.doc(CAPTURE + "flush-snapshots.json")
        self.original_repo = PurePosixPath(baseline["working_directory"])
        self.original_evidence = PurePosixPath(capture["driver"]["path"]).parent.parent
        self.need(self.original_repo.is_absolute() and self.original_evidence.is_absolute(),
            "Original command/source locations are explicit absolute paths")
        inventories = [self.doc(prefix + filename) for prefix in (STOCK, CAPTURE + "stock/")
                       for filename in ("inputs-before.json", "inputs-after.json")]
        self.source_inventory(inventories)
        self.need(all(report["status"] == "failed" and report["deliveries"] == [row]
            and report["source_commit"] == SOURCE and report["source_tree"] == TREE
            and report["selected_cases"] == ["P09"] and report["inputs_stable"] is True
            and report["release_acceptance"] is False and report["complete_source_delivery_corpus"] is False
            and report["full_product_goal_completed"] is False
            and report["native_validation"] == report["browser_validation"] == "pending"
            for report, row in ((baseline, before), (wrapped, after))),
            "Both failed request reports bind source identity, raw rows and open release scope")
        equal = ("case_id", "source_files", "program_revision", "source_manifest", "options", "max_operations",
                 "operations", "work", "failure", "diagnostic")
        self.need(all(before[key] == after[key] for key in equal)
            and before["status"] == after["status"] == "failed" and before["case_id"] == "P09",
            "Complete request identity, work inventory, diagnostic and failure are equal")
        self.need(before["options"] == OPTIONS and before["options"]["helpers"] is False
            and before["max_operations"] == 100000 and before["operations"] == 100001
            and capture["original_request"] == {"case_id": "P09", **OPTIONS},
            "Original complete P09 settings, cap and 100001 shared refusal remain unchanged")
        diagnostic = before["diagnostic"]
        self.need(before["failure"] == {"type": "OntoKinError", "message": "Construction exceeded max_operations."}
            and diagnostic["code"] == "OKL-E-RESOURCE" and diagnostic["category"] == "resource_limit"
            and diagnostic["details"] == {"budget": "max_operations", "limit": 100000,
                "consumed": 100001, "profile": "planar-reach-0.1"},
            "Actual refusal is the original shared construction operation cap")
        self.need(work_valid(before["work"]) and before["work"]["operations"] == 95867
            and before["work"]["cache_entries"] == 256 and capture["work_after_request"] == before["work"]
            and capture["shared_operations_after_request"] == 100001
            and all(before["work"]["counts"].get(key) == value for key, value in STAGE_COUNTS.items()),
            "Complete reach categories, 95867 admitted charges, cache occupancy and failure-stage counters reconcile")
        self.need(capture["schema_version"] == "ontokin.p09-reader-input-capture/0.1"
            and capture["status"] == "captured_failed_request" and capture["product_request_status"] == "failed"
            and capture["accepted_artifact"] is False and capture["release_acceptance"] is False
            and capture["source_commit"] == SOURCE and capture["source_tree"] == TREE
            and capture["inputs_stable"] is True and capture["reader_calls"] == capture["flush_calls"] == 1,
            "Capture is explicitly one failed unvalidated request on the accepted source")
        self.need(exact_true(capture["identity_checks"], IDENTITIES)
            and capture["callbacks"] == {"external": {"module": "ontokin.construction",
                "qualname": "ConstructionBudget.tick", "bound_owner_type": "ConstructionBudget"},
                "construction_check": None, "observer_at_reader_entry": None, "observer_after_request": None},
            "Exact complete callback, owner, observer and restoration assertions are literal true")
        self.need(capture["work_limits"] == WORK_LIMITS and capture["budget_limits"] == CONSTRUCTION_LIMITS,
            "Every original reach and construction limit is retained")
        driver = self.raw("drivers/capture_p09_input_v1.py")
        self.need(digest(driver) == CAPTURE_SHA == capture["driver"]["sha256"]
            and len(driver) == capture["driver"]["bytes"]
            and PurePosixPath(capture["driver"]["path"]) == self.original_evidence / "drivers/capture_p09_input_v1.py",
            "Actual capture driver matches the independently reviewed immutable source")
        self.need(digest(self.raw("drivers/compare_capture.py")) == COMPARE_SHA
            and digest(self.raw("drivers/run_capture.py")) == RUNNER_SHA,
            "Retained comparator and command-capture drivers match original execution sources")
        bframes, aframes = frames(before["traceback"]), frames(after["traceback"])
        removed = [frame for frame in aframes if frame["file"] == capture["driver"]["path"]]
        remaining = [frame for frame in aframes if frame not in removed]
        self.need(len(removed) == 2 and [frame["function"] for frame in removed] ==
            ["capture_validate_export", "capture_flush"] and remaining == bframes
            and capture["exception"]["frames"] == aframes
            and capture["exception"]["type"] == before["failure"]["type"]
            and capture["exception"]["message"] == before["failure"]["message"]
            and before["traceback"].splitlines()[-1] == after["traceback"].splitlines()[-1]
            and capture["exception"]["cause"] is None and capture["exception"]["context"] is None
            and capture["exception"]["suppress_context"] is False,
            "Raw exception frames differ only by the two scoped wrappers; saved exception chain agrees")
        self.need([frame["function"] for frame in bframes[-11:]] ==
            ["flush", "_complete_inequality_values", "calculate", "mul", "op", "tick", "_tick", "charge", "tick", "exceeded", "fail"]
            and any(frame["function"] == "_complete_inequality_values" and frame["line"] == 557 for frame in bframes),
            "Underlying refusal remains the first authored-angle operation of group 11")
        executable = baseline["execution"]["executable"]
        self.need(baseline["execution"] == wrapped["execution"] == capture["execution"],
            "Both actual product requests used the same reported interpreter and platform")
        cwd, original = str(self.original_repo), self.original_evidence
        bc, stdout = self.command("stock-p09-001", 1, cwd,
            str(self.original_repo / "tools/build_reach_source_artifacts.py"),
            ["--output-dir", str(original / STOCK.rstrip("/")), "--case", "P09", "--fps", "1"], executable,
            (baseline["started_at"], before["started_at"], before["finished_at"], baseline["finished_at"]))
        self.need(stdout == b"P09: failed (100001 operations)\n", "Stock command stdout retains actual failed request")
        args = ["--repo", cwd, "--output-dir", str(original / CAPTURE.rstrip("/"))]
        cc, stdout = self.command("capture-p09-001", 1, cwd, capture["driver"]["path"], args, executable,
            (wrapped["started_at"], after["started_at"], after["finished_at"], wrapped["finished_at"], capture["created_at"]))
        lines = stdout.decode().splitlines()
        self.need(len(lines) == 2 and lines[0] == "P09: failed (100001 operations)"
            and decode(lines[1]) == {"capture_status": "captured_failed_request", "product_request_status": "failed",
                "shared_operations": 100001, "captured_bytes": capture["artifact"]["bytes"]}
            and capture["actual_driver_command"] == [executable, capture["driver"]["path"], *args]
            and capture["stock_api_call"] == {"callable": "tools.build_reach_source_artifacts.build",
                "output": str(original / (CAPTURE + "stock")), "cases": ["P09"], "fps": 1.0}
            and "synthesizes report.command" in capture["stock_report_command_note"],
            "Capture command stdout and real API invocation preserve failed status and correct provenance")
        self.need(timestamp(bc["finished_at"]) < timestamp(cc["started_at"]),
            "Original stock and capture executions were serialized")
        for prefix in (STOCK, CAPTURE + "stock/"):
            self.need(not any((self.evidence / (prefix + "P09/" + name)).exists()
                for name in ("scene.glb", "export-report.json")),
                "Failed exporter has no successful artifact/report: " + prefix)
        self.need(capture["artifact"]["path"] == "unvalidated-reader-input.glb", "Captured bytes use the unvalidated filename")
        raw = self.raw(CAPTURE + "unvalidated-reader-input.glb")
        self.need(len(raw) == capture["artifact"]["bytes"] and digest(raw) == capture["artifact"]["sha256"],
            "Actual immutable captured GLB bytes match the retained identity")
        self.need(snapshot_doc["schema_version"] == "ontokin.certificate-flush-capture/0.1"
            and len(snapshot_doc["snapshots"]) == 1, "Exactly one final flush snapshot is retained")
        snapshot = snapshot_doc["snapshots"][0]
        self.need(exact_true(snapshot["identity_checks"], FLUSH_IDENTITIES)
            and snapshot["ordinal"] == 1 and snapshot["thresholds_enabled"] is True
            and snapshot["restart_requested"] is False and snapshot["numeric_keys"] == list(NUMERIC_KEYS)
            and len(snapshot["groups"]) == 12
            and [group["ordinal"] for group in snapshot["groups"]] == list(range(1, 13)),
            "Bounded twelve-group flush has complete native ownership assertions and original field order")
        entry, initial = snapshot["work_at_entry"], capture["work_at_reader_entry"]
        self.need(work_valid(entry) and work_valid(initial)
            and (entry["operations"], snapshot["shared_operations_at_entry"]) == (95109, 99242)
            and (initial["operations"], capture["shared_operations_at_reader_entry"]) == (43637, 47770)
            and entry["counts"].get("independent_certificate_group") == 12
            and entry["counts"].get("independent_certificate_group_check", 0) == 0
            and entry["counts"].get("independent_certificate_term_admission", 0) == 0,
            "Reader/flush entry counters identify the observed unstarted twelve-group discharge")
        delta = {key: before["work"]["counts"].get(key, 0) - entry["counts"].get(key, 0)
            for key in set(before["work"]["counts"]) | set(entry["counts"])}
        delta = {key: value for key, value in delta.items() if value}
        self.need(all(value > 0 for value in delta.values()) and sum(delta.values()) == 758
            and before["work"]["operations"] - entry["operations"] == 758
            and before["operations"] - snapshot["shared_operations_at_entry"] == 759,
            "Observed flush prefix reconciles 758 admitted charges and one refused external callback")
        historical_raw = self.raw("historical/checkpoint028-P09-request-result.json")
        historical = decode(historical_raw)
        manifest = decode(self.source_bytes[HISTORY + "checkpoint-028-manifest.json"])
        expected = next(row for row in manifest["members"]
            if row["path"] == "execution/candidate-original28-001/P09/request-result.json")
        self.need(len(historical_raw) == expected["bytes"] and digest(historical_raw) == expected["sha256"]
            and all(historical[key] == before[key] for key in equal)
            and historical["status"] == "failed", "Historical comparison bytes bind to the original checkpoint 028 manifest")
        self.neutrality(before, after, capture, delta)
        self.details["actual_requests"] = {"product_status": "failed", "command_exit_codes": [1, 1],
            "shared_operations": 100001, "reach_operations": 95867, "cache_entries": 256,
            "flush_entry_shared": 99242, "flush_entry_reach": 95109,
            "completed_flush_prefix_operations": 758, "refused_external_callbacks": 1,
            "observed_flush_prefix_categories": delta, "captured_bytes": len(raw), "captured_sha256": digest(raw)}
        return capture, snapshot, raw, delta

    def neutrality(self, before, after, capture, delta):
        raw = self.raw("analysis/capture-neutrality-001.json")
        record = decode(raw)
        self.need(digest(raw) == NEUTRALITY_SHA and record["status"] == "passed"
            and record["check_count"] == len(record["checks"]) == 57
            and all(row["passed"] is True for row in record["checks"]),
            "Original 57-check neutrality report is preserved byte-for-byte")
        self.need(record["source_commit"] == SOURCE and record["source_tree"] == TREE
            and record["reach_work"] == before["work"] and record["shared_operations"] == 100001
            and record["failure_stage_counts"] == STAGE_COUNTS
            and record["product_request_status"] == "failed" and record["product_command_exit"] == 1
            and record["accepted_artifact"] is False and record["release_acceptance"] is False
            and record["full_cost_beyond_cap_known"] is False
            and "No elapsed neutrality claim" in record["scope"],
            "Original neutrality result agrees with actual failed request and limited scope")
        mismatches = []
        for name, item in record["inputs"].items():
            size, value = self.remap_identity(name)
            if {"bytes": size, "sha256": value} != item:
                mismatches.append(name)
        self.need(not mismatches, "Every original neutrality input hash resolves to preserved evidence", mismatches)
        receipt = self.doc("commands/capture-neutrality-001.json")
        historical_path = receipt["command"][receipt["command"].index("--historical") + 1]
        args = ["--baseline", str(self.original_evidence / STOCK.rstrip("/")),
            "--capture", str(self.original_evidence / CAPTURE.rstrip("/")),
            "--stock-receipt", str(self.original_evidence / "commands/stock-p09-001.json"),
            "--capture-receipt", str(self.original_evidence / "commands/capture-p09-001.json"),
            "--historical", historical_path,
            "--output", str(self.original_evidence / "analysis/capture-neutrality-001.json")]
        _, stdout = self.command("capture-neutrality-001", 0, str(self.original_repo),
            str(self.original_evidence / "drivers/compare_capture.py"), args,
            capture["execution"]["executable"], (record["created_at"],))
        self.need(decode(stdout) == {"status": "passed", "checks": 57, "failures": []}
            and self.remap_identity(historical_path)[1] == digest(self.raw("historical/checkpoint028-P09-request-result.json")),
            "Actual neutrality command/streams bind the original report and historical input")

    def receipts(self, snapshot):
        failures = []
        for group in snapshot["groups"]:
            ordinal, key, quantities = group["ordinal"], group["key"], group["quantities"]
            try:
                if len(key) != 21 or list(quantities) != list(NUMERIC_KEYS):
                    raise ValueError("numeric field coverage")
                q = {name: rational(value) for name, value in quantities.items()}
                if any(set(item) != {"type", "value"}
                       or item["type"] != type(item["value"]).__name__ or number(item["value"]) != q[name]
                       for name, item in zip(NUMERIC_KEYS, key)):
                    raise ValueError("grouping key decode")
                minima = group["minima"]
                if list(minima) != list(MINIMUM_ORDER) or group["minima_order"] != list(MINIMUM_ORDER):
                    raise ValueError("minimum coverage/order")
                for value in minima.values():
                    rational(value)
                t = group["thresholds"]
                if type(t) is not dict or t["enabled"] is not True or t["used"] is not (ordinal <= 6):
                    raise ValueError("threshold state")
                if len(t["fields"]) != 21 or any(rational(item) != q[name] for name, item in zip(NUMERIC_KEYS, t["fields"])):
                    raise ValueError("quantity receipt")
                if set(t["extent_fields"]) != {"width", "stored_width", "magnitude"} or set(t["minimum_fields"]) != set(minima):
                    raise ValueError("receipt field coverage")
                for name, item in t["extent_fields"].items():
                    if rational(item["fields"]) != rational(item["value"]) or rational(item["value"]) != rational(group[name]):
                        raise ValueError("extent receipt")
                for name, item in t["minimum_fields"].items():
                    if rational(item["fields"]) != rational(item["value"]) or rational(item["value"]) != rational(minima[name]):
                        raise ValueError("minimum receipt")
                if not set(t["domains"]).issubset(minima) or any(type(value) is not list or len(value) != 4
                    or any(type(bit) is not int or not 0 <= bit <= 32768 for bit in value)
                    for value in t["domains"].values()):
                    raise ValueError("discarded domain receipt")
            except (KeyError, TypeError, ValueError) as error:
                failures.append({"group": ordinal, "reason": str(error)})
        self.need(not failures, "All twelve grouping keys and threshold extent/minimum receipts agree", failures)
        self.need(rational(snapshot["position_tolerance"]) == Fraction(.001)
            and rational(snapshot["rotation_tolerance"]) == Fraction(.001)
            and rational(snapshot["max_position"]) == rational(snapshot["max_rotation"]) == 0,
            "Flush starts with original tolerances and zero accumulated bounds")

    def glb_groups(self, raw, snapshot, capture):
        if len(raw) < 28 or struct.unpack_from("<4sII", raw) != (b"glTF", 2, len(raw)):
            raise ValueError("Invalid complete GLB header")
        offset, chunks = 12, []
        while offset < len(raw):
            size, kind = struct.unpack_from("<II", raw, offset)
            offset += 8
            if size % 4 or offset + size > len(raw):
                raise ValueError("Invalid bounded GLB chunk")
            chunks.append((kind, raw[offset:offset + size])); offset += size
        self.need(len(chunks) == 2 and [kind for kind, _ in chunks] == [0x4E4F534A, 0x004E4942],
            "Captured GLB has complete JSON and embedded BIN chunks")
        document, binary = decode(chunks[0][1]), chunks[1][1]
        buffers = document["buffers"]
        self.need(len(buffers) == 1 and "uri" not in buffers[0]
            and 0 <= len(binary) - buffers[0]["byteLength"] <= 3
            and len(document["animations"]) == 1, "Captured byte census uses one embedded buffer and animation")
        animation = document["animations"][0]
        axes = []
        for index in sorted({sampler["input"] for sampler in animation["samplers"]}):
            accessor = document["accessors"][index]
            if (accessor["componentType"] != 5126 or accessor["type"] != "SCALAR"
                    or "sparse" in accessor or accessor.get("normalized", False)):
                raise ValueError("Unexpected actual clock accessor form")
            view = document["bufferViews"][accessor["bufferView"]]
            count, stride = accessor["count"], view.get("byteStride", 4)
            base, start = accessor.get("byteOffset", 0), view.get("byteOffset", 0)
            if (type(count) is not int or count != 205 or view["buffer"] != 0
                    or any(type(value) is not int or value < 0 or value % 4 for value in (stride, base, start))
                    or stride < 4 or base + (count - 1) * stride + 4 > view["byteLength"]
                    or start + view["byteLength"] > buffers[0]["byteLength"]):
                raise ValueError("Actual clock accessor exceeds its declared buffer")
            axes.append(tuple(struct.unpack_from("<I", binary, start + base + item * stride)[0] for item in range(count)))
        self.need(bool(axes) and all(axis == axes[0] for axis in axes), "Every animation sampler uses identical actual binary32 clock words")
        bits = axes[0]
        def binary32(word):
            if not 0 <= word < 0x7f800000:
                raise ValueError("Nonfinite or negative actual clock")
            exponent, mantissa = (word >> 23) & 255, word & 0x7fffff
            return (Fraction(mantissa, 1 << 149) if exponent == 0 else
                Fraction((1 << 23) | mantissa) * Fraction(2) ** (exponent - 150))
        stored = tuple(binary32(word) for word in bits)
        authored_records = animation["extras"]["ontokin"]["exact_times_seconds"]
        authored = tuple(rational(value) for value in authored_records)
        metadata = document["extras"]["ontokin"]
        quantization = metadata["reach_quantization"]
        self.need(len(authored) == len(quantization["retained_keys"]) == len(stored) == 205
            and authored[0] == stored[0] == 0 and authored[-1] == stored[-1] == 3
            and all(a < b for a, b in zip(authored, authored[1:]))
            and all(a < b for a, b in zip(stored, stored[1:])), "Original complete P09 has 205 increasing actual/authored clock endpoints")
        boundaries = (Fraction(0), Fraction(2), Fraction(3))
        clock_failures = []
        for index, (exact, value, word, row) in enumerate(zip(authored, stored, bits, quantization["retained_keys"])):
            lower = Fraction(0) if word == 0 else (binary32(word - 1) + value) / 2
            higher = Fraction(1 << 128) if word == 0x7f7fffff else binary32(word + 1)
            upper = (value + higher) / 2
            even = word % 2 == 0
            if not (set(row) == {"authored_seconds", "stored_seconds", "stored_binary32_bits", "semantic_boundary"}
                and row["authored_seconds"] == authored_records[index] and number(row["stored_seconds"]) == value
                and row["stored_binary32_bits"] == format(word, "08x")
                and type(row["semantic_boundary"]) is bool and row["semantic_boundary"] == (exact in boundaries)
                and (exact > lower or even and exact == lower) and (exact < upper or even and exact == upper)):
                clock_failures.append(index)
        self.need(not clock_failures, "Every retained clock label agrees with actual bits and exact ties-to-even cell", clock_failures)
        self.need(tuple(Fraction(row["source_seconds"]) for row in metadata["boundary_states"]) == boundaries
            and tuple(Fraction(value) for value in animation["extras"]["ontokin"]["boundary_times_seconds"]) == boundaries,
            "Supplied P09 phase labels retain boundaries zero, two and three")
        self.fixture_sources(metadata)
        nodes, identities = document["nodes"], {}
        for index, node in enumerate(nodes):
            info = node["extras"]["ontokin"]
            if info["kind"] != "object" or info["path"] != node["name"] or node["name"] in identities:
                raise ValueError("Unexpected or repeated carrier identity")
            identities[node["name"]] = (index, {"path": info["path"], "element_id": info["element_id"]})
        rows = {}
        for row in quantization["interval_certificates"]:
            if set(row) != ROW_KEYS:
                raise ValueError("Incomplete numeric certificate row")
            left, right, carrier = row["left_key_index"], row["right_key_index"], row["carrier"]
            if (type(left) is not int or type(right) is not int or not 0 <= left < 204 or right != left + 1
                    or carrier.get("path") not in identities):
                raise ValueError("Invalid certificate interval/carrier")
            node, identity = identities[carrier["path"]]
            if carrier != identity or (left, node) in rows:
                raise ValueError("Duplicate or changed carrier identity")
            ha, hs = authored[right] - authored[left], stored[right] - stored[left]
            if rational(row["h_authored_seconds"]) != ha or rational(row["h_stored_seconds"]) != hs:
                raise ValueError("Width label differs from actual decoded clocks")
            low, high = max(Fraction(0), min(authored[left], stored[left])), min(Fraction(3), max(authored[right], stored[right]))
            required = [index for index, (a, b) in enumerate(zip(boundaries, boundaries[1:])) if max(a, low) < min(b, high)]
            selected = row["source_phase_indices"]
            if (type(selected) is not list or any(type(index) is not int or index not in (0, 1) for index in selected)
                    or len(selected) != len(set(selected)) or not set(required).issubset(selected)
                    or any(max(low, boundaries[index]) > min(high, boundaries[index + 1]) for index in selected)):
                raise ValueError("Incorrect selected/required phase coverage")
            key = tuple(row[name] for name in NUMERIC_KEYS)
            q = {name: number(value) for name, value in zip(NUMERIC_KEYS, key)}
            rows[left, node] = {"ha": ha, "hs": hs, "key": key, "q": q,
                "member": {"left_key_index": left, "right_key_index": right, "carrier": carrier["path"],
                    "node_index": node, "selected_source_phases": selected,
                    "required_positive_overlap_phases": required}}
        self.need(len(nodes) == 6 and set(rows) == {(left, node) for left in range(204) for node in range(6)},
            "All 1224 actual carrier/interval rows have correct widths and complete identity/phase coverage")
        groups, mapping = [], {}
        for row_id in sorted(rows):
            row = rows[row_id]
            key = row["key"]
            if key not in mapping:
                mapping[key] = {"ordinal": len(groups) + 1, "key": key, "q": row["q"],
                    "ha": row["ha"], "hs": row["hs"], "members": [], "authored_widths": [], "stored_widths": []}
                groups.append(mapping[key])
            group = mapping[key]
            group["ha"], group["hs"] = max(group["ha"], row["ha"]), max(group["hs"], row["hs"])
            group["members"].append(row["member"])
            group["authored_widths"].append(row["ha"]); group["stored_widths"].append(row["hs"])
        self.need(len(groups) == 12, "Independent actual-byte grouping reconstructs exactly twelve first appearances")
        mismatches = []
        for group, captured in zip(groups, snapshot["groups"]):
            if (any(not same_number(value, item["value"]) or type(value).__name__ != item["type"]
                    for value, item in zip(group["key"], captured["key"]))
                or group["ha"] != rational(captured["width"]) or group["hs"] != rational(captured["stored_width"])
                or any(group["q"][name] != rational(captured["quantities"][name]) for name in NUMERIC_KEYS)):
                mismatches.append(group["ordinal"])
        self.need(not mismatches, "Independent group order, exact numeric keys and actual width maxima agree with flush snapshot", mismatches)
        self.details["byte_census"] = {"clock_count": 205, "carrier_count": 6, "certificate_count": 1224,
            "group_count": len(groups), "group_member_counts": [len(group["members"]) for group in groups],
            "json_chunk_sha256": digest(chunks[0][1]), "captured_minima_independently_certified": False}
        return groups, authored, stored, bits, digest(chunks[0][1])

    def fixture_sources(self, metadata):
        manifest = decode(self.source_bytes[BASE + "p09.files.json"])
        sources = metadata["program"]["sources"]
        entries = [manifest["entry"], *manifest["modules"]]
        by_filename = {row["filename"]: row for row in sources.values()}
        self.need(len(entries) == len(sources) == len(by_filename) == 4
            and metadata["program"]["revision"] == self.doc(STOCK + "P09/request-result.json")["program_revision"],
            "Supplied P09 program identity retains the original four-source bundle")
        failures = []
        for item in entries:
            path = BASE + relative(item["path"]).as_posix()
            if item["filename"] not in by_filename or by_filename[item["filename"]]["source_revision"] != self.source[path]["sha256"]:
                failures.append(path)
        entry = self.source_bytes[BASE + "sources/p09-principal-shoulder-wrap.ok"].decode()
        self.need(not failures and re.search(r"duration\s*=\s*3\[s\]\s*;", entry) is not None
            and re.search(r"reach_to\([^;]+,\s*2\[s\]\s*,\s*elbow_positive\)", entry) is not None
            and re.search(r"at\s+0\[s\]\s+sequence\s*\{\s*start\s+reach\s*;\s*\}", entry) is not None,
            "Captured source labels match original Git source bytes and inspected P09 action clocks", failures)

    def census(self, capture, snapshot, groups, authored, stored, bits, json_sha, delta):
        canonical = self.raw("analysis/P09-full-input-census.json")
        record = decode(canonical)
        driver_name = PurePosixPath(record["command"][1]).name
        self.need(re.fullmatch(r"analyze_p09_full_input(?:_v[0-9]+)?\.py", driver_name) is not None,
            "Canonical census names its actual frozen executed driver")
        driver = self.raw("drivers/" + driver_name)
        self.need(record["schema_version"] == "ontokin.p09-full-input-census/0.1"
            and record["status"] == "passed" and record["errors"] == [] and record["inputs_unchanged"] is True
            and all(record.get(key) is False for key in CENSUS_FALSE)
            and record["driver_sha256"] == digest(driver),
            "Executed census identifies its driver and explicitly excludes product execution, measured savings and release claims")
        parsed = ast.parse(driver)
        imports = []
        for node in ast.walk(parsed):
            if isinstance(node, ast.Import):
                imports.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append((node.module or "").split(".")[0])
        allowed = {"__future__", "argparse", "collections", "datetime", "fractions", "hashlib", "json",
                   "math", "pathlib", "re", "struct", "sys", "traceback"}
        dynamic = [node.func.id for node in ast.walk(parsed) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval", "__import__"}]
        self.need(set(imports).issubset(allowed) and not dynamic,
            "Census source imports only its declared standard-library modules and has no dynamic product execution")
        predecessor = self.raw("historical/analyze_quarter_operands.py")
        original_manifest = decode(self.source_bytes[HISTORY + "checkpoint-027-manifest.json"])
        original = next(row for row in original_manifest["members"] if row["path"] == "drivers/analyze_quarter_operands.py")
        self.need(record["predecessor_driver_sha256"] == digest(predecessor) == original["sha256"] == PREDECESSOR_SHA
            and len(predecessor) == original["bytes"], "Predecessor census bytes bind to checkpoint 027 without relabeling its execution")
        attempts, canonical_labels = [], []
        for path in sorted((self.evidence / "commands").glob("*.json")):
            receipt = self.doc(path.relative_to(self.evidence).as_posix())
            argv = receipt.get("command", [])
            if len(argv) < 2 or re.fullmatch(r"analyze_p09_full_input(?:_v[0-9]+)?\.py", PurePosixPath(argv[1]).name) is None:
                continue
            label, actual_args = path.stem, argv[2:]
            pairs = dict(zip(actual_args[::2], actual_args[1::2]))
            self.need(len(actual_args) == 6 and set(pairs) == {"--capture-dir", "--output", "--repo"}
                and pairs["--capture-dir"] == str(self.original_evidence / CAPTURE.rstrip("/"))
                and pairs["--repo"] == str(self.original_repo)
                and PurePosixPath(pairs["--output"]).parent == self.original_evidence / "analysis"
                and PurePosixPath(argv[1]).parent == self.original_evidence / "drivers",
                "Census command binds exact capture/source and a distinct retained output: " + label)
            output_name = PurePosixPath(pairs["--output"]).relative_to(self.original_evidence).as_posix()
            attempt_raw = self.raw(output_name)
            attempt = decode(attempt_raw)
            source_name = "drivers/" + PurePosixPath(argv[1]).name
            frozen = self.raw(source_name)
            self.need(attempt["command"] == [capture["execution"]["executable"], *argv[1:]]
                and attempt["driver_sha256"] == digest(frozen)
                and attempt["status"] in ("passed", "failed")
                and all(attempt.get(key) is False for key in CENSUS_FALSE),
                "Frozen driver, actual arguments and scope bind census attempt: " + label)
            failures, paths = [], set()
            for item in attempt["inputs"]:
                name = item["path"]
                size, value = self.remap_identity(name)
                if (name in paths or item["unchanged"] is not True or item["bytes"] != size
                    or item["bytes_after"] != size or item["sha256"] != value or item["sha256_after"] != value):
                    failures.append(name)
                paths.add(name)
            required_sources = {BASE + "p09.files.json", BASE + "sources/p09-principal-shoulder-wrap.ok",
                BASE + "libraries/reach-assets.ok", BASE + "libraries/reach-exterior.ok",
                BASE + "libraries/reach-parts.ok", "ontokin/gltf.py", "ontokin/reach_conformance.py",
                "ontokin/reach_numeric.py", "ontokin/reach_reference_plan.py"}
            required_inputs = {str(self.original_repo / item) for item in required_sources}
            required_inputs.update(str(self.original_evidence / (CAPTURE + item)) for item in (
                "capture.json", "flush-snapshots.json", "unvalidated-reader-input.glb",
                "stock/report.json", "stock/P09/request-result.json"))
            required_inputs.add(str(self.original_evidence / source_name))
            self.need(paths == required_inputs and not failures and attempt["inputs_unchanged"] is True,
                "Every actual census input resolves to stable preserved bytes: " + label, failures)
            _, stdout = self.command(label, 0 if attempt["status"] == "passed" else 1,
                str(self.original_repo), argv[1], actual_args, capture["execution"]["executable"],
                (attempt["started_at"], attempt["finished_at"]))
            result = attempt.get("census", {})
            self.need(decode(stdout) == {"status": attempt["status"], "output": pairs["--output"],
                "clock_count": result.get("clock_count"), "certificate_count": result.get("certificate_count"),
                "group_count": result.get("group_count"), "errors": attempt["errors"]}
                and ((attempt["status"] == "passed" and attempt["errors"] == [])
                    or (attempt["status"] == "failed" and bool(attempt["errors"]))),
                "Census attempt retains its real command outcome and stdout: " + label)
            if attempt_raw == canonical:
                canonical_labels.append(label)
            attempts.append({"label": label, "result": attempt, "receipt": receipt,
                             "source_sha256": digest(frozen), "output": output_name})
        self.need({"census-001", "census-002"}.issubset({item["label"] for item in attempts})
            and len(canonical_labels) == 1
            and canonical_labels[0] == attempts[-1]["label"],
            "Canonical census is byte-identical to one identified final executed result; earlier attempts remain separate")
        self.need(all(timestamp(first["receipt"]["finished_at"]) < timestamp(last["receipt"]["started_at"])
            for first, last in zip(attempts, attempts[1:])), "All retained census attempts were serialized")
        if len(attempts) > 1:
            final_events = record["census"]["static_remaining_work"]["events"]
            projection = [{key: item[key] for key in ("group", "site", "category")} for item in final_events]
            self.need(all([{key: item[key] for key in ("group", "site", "category")}
                    for item in attempt["result"]["census"]["static_remaining_work"]["events"]] == projection
                for attempt in attempts if attempt["result"]["status"] == "passed"),
                "Later census enrichment preserves every earlier successful static event/category and its identity")
        census = record["census"]
        self.need(census["source_commit"] == SOURCE and census["source_tree"] == TREE
            and census["case_id"] == "P09" and census["captured_request_status"] == "failed"
            and census["export_result_returned"] is False and census["clock_count"] == 205
            and census["carrier_count"] == 6 and census["certificate_count"] == 1224 and census["group_count"] == 12
            and census["numeric_keys"] == list(NUMERIC_KEYS)
            and census["artifact"] == {**capture["artifact"], "validation_status": "unvalidated_reader_input", "json_chunk_sha256": json_sha},
            "Census source, artifact, counts and unvalidated status match independently read evidence")
        clock_records = census["clocks"]
        self.need(len(clock_records) == 205 and all(row["index"] == index
            and rational(row["authored"]) == a and rational(row["stored"]) == b
            and row["binary32_bits"] == format(word, "08x") and rational(row["shift"]) == abs(a - b)
            and row["semantic_boundary"] is (a in (0, 2, 3))
            for index, (row, a, b, word) in enumerate(zip(clock_records, authored, stored, bits))),
            "All census clock records agree with independent binary32 decoding")
        differences = []
        for group, row, captured in zip(groups, census["groups"], snapshot["groups"]):
            q = group["q"]
            flags = {"exact_width_match": group["ha"] == group["hs"],
                "exact_angular_match": q["angular_speed_bound_rad_per_s"] == q["enclosing_angular_speed_bound_rad_per_s"],
                "exact_acceleration_match": q["carrier_acceleration_bound_m_per_s2"] == q["enclosing_carrier_acceleration_bound_m_per_s2"],
                "authored_width_dyadic": group["ha"].denominator.bit_count() == 1,
                "stored_width_dyadic": group["hs"].denominator.bit_count() == 1,
                "all_four_coefficients_zero": all(q[name] == 0 for name in (
                    "angular_speed_bound_rad_per_s", "enclosing_angular_speed_bound_rad_per_s",
                    "carrier_acceleration_bound_m_per_s2", "enclosing_carrier_acceleration_bound_m_per_s2"))}
            flags["exact_triple_match"] = flags["exact_width_match"] and flags["exact_angular_match"] and flags["exact_acceleration_match"]
            reconciliation = {"numeric_key_and_quantities_match": True, "actual_width_maxima_match": True,
                "threshold_receipts_match_when_present": True, "thresholds_used": captured["thresholds"]["used"],
                "thresholds_enabled": True, "observed_minima_independently_certified": False,
                "observed_magnitude_independently_certified": False}
            histograms = [[{"value": str(value), "count": count} for value, count in sorted(Counter(group[name]).items())]
                          for name in ("authored_widths", "stored_widths")]
            if (row["ordinal"] != group["ordinal"] or row["members"] != group["members"]
                or row["member_count"] != len(group["members"]) or row["first_appearance"] != group["members"][0]
                or row["last_appearance"] != group["members"][-1]
                or row["carriers"] != dict(Counter(member["carrier"] for member in group["members"]))
                or rational(row["maximum_authored_width"]) != group["ha"]
                or rational(row["maximum_stored_width"]) != group["hs"]
                or set(row["quantities"]) != set(NUMERIC_KEYS)
                or any(rational(row["quantities"][name]) != q[name] for name in NUMERIC_KEYS)
                or not exact_flags(row["features"], flags)
                or not exact_flags(row["snapshot_reconciliation"], reconciliation)
                or row["authored_width_histogram"] != histograms[0]
                or row["stored_width_histogram"] != histograms[1]
                or len(row["numeric_key"]) != len(NUMERIC_KEYS)
                or row["observed_reader_minima"] != captured["minima"]
                or row["observed_reader_magnitude"] != captured["magnitude"]):
                differences.append(group["ordinal"])
            for key, value in zip(row["numeric_key"], group["key"]):
                fields = {"type", "value", "exact"}
                if type(value) is float:
                    fields.update(("binary64_hex", "binary64_bits"))
                if (set(key) != fields or key["type"] != type(value).__name__ or not same_number(key["value"], value)
                        or rational(key["exact"]) != number(value)
                        or type(value) is float and (key["binary64_hex"] != value.hex()
                            or key["binary64_bits"] != struct.pack(">d", value).hex())):
                    differences.append(group["ordinal"])
        self.need(len(census["groups"]) == 12 and not differences
            and census["groups_11_and_12"] == census["groups"][-2:],
            "Every census group, carrier/phase member, coefficient, width and observation agrees with independently reconstructed data", sorted(set(differences)))
        self.static_ledger(census, delta, snapshot)
        self.details["census_driver"] = {"sha256": digest(driver), "command_label": canonical_labels[0],
            "standard_library_source_review": True, "product_execution_performed": False,
            "attempts": [{key: row[key] for key in ("label", "source_sha256", "output")} for row in attempts]}

    def static_ledger(self, census, delta, snapshot):
        model = census["static_remaining_work"]
        events = model["events"]
        self.need(type(events) is list and 758 < len(events) < 10000
            and all(set(event) in ({"group", "site", "category"},
                {"group", "site", "category", "operation", "operand_fields", "result_fields",
                 "operand_result_flags", "exact_identity_candidates"})
                and type(event["group"]) is int and 1 <= event["group"] <= 12
                and type(event["site"]) is str and event["site"]
                and type(event["category"]) is str and event["category"].startswith("independent_")
                for event in events)
            and [event["group"] for event in events] == sorted(event["group"] for event in events),
            "Conditional static ledger has bounded ordered group/category/site events")
        first = model["first_refused_static_event"]
        index = first["index"]
        prefix, tail = dict(Counter(event["category"] for event in events[:index])), dict(Counter(event["category"] for event in events[index:]))
        final = {"independent_bound_decode": 3, "independent_report_rounding": 3,
                 "independent_exact_compare": 3, "checkpoint": 1}
        projected = snapshot["shared_operations_at_entry"] + len(events) + 10
        self.need(type(index) is int and index == model["completed_flush_prefix_operations"] == 758
            and first == {"index": index, **events[index]}
            and {key: events[index][key] for key in ("group", "site", "category")} ==
                {"group": 11, "site": "authored.angle", "category": "independent_exact_mul"}
            and prefix == delta == model["observed_prefix_categories"] == model["modeled_prefix_categories"]
            and model["observed_prefix_category_and_work_totals_match"] is True
            and model["shared_refused_charge_accounting_matches"] is True
            and model["failed_attempt_is_not_counted_in_work_record"] is True,
            "Static model's entire visited prefix matches measured categories and the exact refused operation")
        self.need(model["kind"] == "conditional_static_estimate_not_measured_full_cost"
            and model["modeled_complete_flush_operations"] == len(events)
            and model["remaining_flush_operations_including_refused_attempt_once"] == len(events) - index
            and model["remaining_flush_categories"] == tail
            and model["conditional_final_report_and_return_categories"] == final
            and model["conditional_final_report_and_return_operations"] == 10
            and model["conditional_complete_shared_operations"] == projected
            and model["conditional_reduction_needed_for_100000"] == max(0, projected - 100000)
            and model["source_minima_and_final_source_admission_independently_certified"] is False
            and type(model["assumptions"]) is list and len(model["assumptions"]) >= 4,
            "Unvisited tail and projected total remain explicitly conditional arithmetic, with refusal counted once")
        screen = census["optimization_screen"]
        equal = [row["ordinal"] for row in census["groups"] if row["features"]["exact_triple_match"]]
        zero = [row["ordinal"] for row in census["groups"] if row["features"]["exact_triple_match"] and row["features"]["all_four_coefficients_zero"]]
        ceiling = len(zero) + 6 * (len(equal) - len(zero))
        self.need(screen["equal_triple_groups"] == equal and screen["equal_triple_zero_groups"] == zero
            and screen["equal_triple_incremental_omitted_operation_ceiling"] == ceiling
            and screen["ceiling_includes_new_overhead"] is False and screen["measured_savings"] is None
            and screen["ceiling_can_cover_conditional_remaining_deficit"] is (ceiling >= max(0, projected - 100000))
            and "no optimization implemented or accepted" in screen["selection_status"],
            "Optimization screen retains an overhead-exclusive ceiling and makes no measured savings or acceptance claim")
        self.need(exact_true(census["census_required_checks"], {
            "all_groups_reconcile_with_snapshot", "observed_flush_prefix_matches_independent_static_ledger",
            "shared_refused_charge_accounting_matches"}), "Census success requires all three explicit reconciliation checks")
        if "exact_scalar_identity_inventory" in census:
            self.scalar_sites(census["exact_scalar_identity_inventory"], events, index, max(0, projected - 100000))
        self.details["conditional_static_model"] = {"completed_observed_prefix": 758,
            "modeled_flush_operations": len(events), "modeled_unvisited_flush_operations": len(events) - index,
            "conditional_final_report_and_return_operations": 10, "conditional_complete_shared_operations": projected,
            "conditional_reduction_needed": max(0, projected - 100000),
            "tail_executed": False, "full_cost_measured": False,
            "scope": "Ledger consistency and observed-prefix agreement; no independent source-minimum certification or successful unvisited execution."}

    def scalar_sites(self, inventory, events, failure_index, deficit):
        classes = ("zero_multiplication", "zero_dividend", "multiplication_by_one",
                   "division_by_one", "addition_of_zero")
        selected = {name: [] for name in classes}
        zero_results, pairs, scalar_indices = set(), {}, set()
        failures = []
        for index, event in enumerate(events):
            if "operation" not in event:
                if event["category"] in {"independent_exact_add", "independent_exact_mul", "independent_exact_div"}:
                    raise ValueError("Enriched scalar inventory omits an arithmetic event")
                continue
            operation = event["operation"]
            if operation not in ("add", "mul", "div") or len(event["operand_fields"]) != 2:
                raise ValueError("Unsupported static scalar event")
            a, b = (rational(value) for value in event["operand_fields"])
            if operation == "div" and not b:
                raise ValueError("Zero denominator in conditional static scalar ledger")
            expected = a + b if operation == "add" else a * b if operation == "mul" else a / b
            flags = {"left_zero": a == 0, "right_zero": b == 0, "left_one": a == 1,
                     "right_one": b == 1, "result_zero": expected == 0, "result_one": expected == 1}
            candidates = {"zero_multiplication": operation == "mul" and (a == 0 or b == 0),
                "zero_dividend": operation == "div" and a == 0,
                "multiplication_by_one": operation == "mul" and (a == 1 or b == 1),
                "division_by_one": operation == "div" and b == 1,
                "addition_of_zero": operation == "add" and (a == 0 or b == 0)}
            if (rational(event["result_fields"]) != expected or not exact_flags(event["operand_result_flags"], flags)
                or not exact_flags(event["exact_identity_candidates"], candidates)
                or event["category"] != "independent_exact_" + operation):
                failures.append(index)
            for name, applicable in candidates.items():
                if applicable:
                    selected[name].append(index); scalar_indices.add(index)
            if operation in ("mul", "div") and expected == 0:
                zero_results.add(index)
            pairs.setdefault((event["group"], operation, a, b), []).append(index)
        self.need(not failures and bool(pairs),
            "Every enriched static scalar result and zero/one applicability flag is independently exact", failures)
        expected_classes = {}
        for name, indices in selected.items():
            expressions = {}
            for index in indices:
                event = events[index]
                item = expressions.setdefault(event["site"], {"site": event["site"], "category": event["category"],
                    "groups": [], "event_indices": [], "within_reconciled_prefix": 0, "unexecuted_tail": 0})
                item["groups"].append(event["group"]); item["event_indices"].append(index)
                item["within_reconciled_prefix" if index < failure_index else "unexecuted_tail"] += 1
            expected_classes[name] = {"sites": len(indices), "expressions": list(expressions.values())}
        duplicate_sites, duplicate_rows = set(), []
        for (group, operation, a, b), indices in pairs.items():
            if len(indices) < 2:
                continue
            duplicate_sites.update(indices[1:])
            row = {"group": group, "operation": operation,
                "operand_fields_after_native_decode": [
                    {name: value[name] for name in ("numerator", "denominator")}
                    for value in events[indices[0]]["operand_fields"]],
                "event_indices": indices, "sites": [events[index]["site"] for index in indices],
                "later_occurrence_sites": len(indices) - 1,
                "later_occurrences_not_already_scalar_identity_sites": sum(index not in scalar_indices for index in indices[1:])}
            duplicate_rows.append(row)
        extra, union = duplicate_sites - scalar_indices, duplicate_sites | scalar_indices
        group_rows = []
        for group in range(1, 13):
            indices = {index for index, event in enumerate(events) if event["group"] == group}
            group_rows.append({"group": group, "zero_result_mul_div_sites": len(indices & zero_results),
                "unique_scalar_identity_sites": len(indices & scalar_indices),
                "additional_exact_duplicate_sites": len(indices & extra),
                "combined_optimistic_omission_ceiling": len(indices & union)})
        self.need(inventory["classes"] == expected_classes
            and inventory["same_order_exact_operand_duplicates_within_group"] == duplicate_rows
            and inventory["zero_result_mul_div_sites"] == len(zero_results)
            and inventory["unique_scalar_identity_sites"] == len(scalar_indices)
            and inventory["additional_duplicate_sites_after_identity_overlap_removed"] == len(extra)
            and inventory["combined_optimistic_scalar_omission_ceiling"] == len(union)
            and inventory["per_group"] == group_rows,
            "Independent event sets reproduce scalar/duplicate omission ceilings without double counting")
        self.need(inventory["counts_are_measured_savings"] is False
            and inventory["new_guard_or_admission_overhead_included"] is False
            and inventory["existing_omitted_zero_quarter_and_borrowed_terms_excluded"] is True
            and inventory["class_counts_overlap"] is True and inventory["conditional_deficit"] == deficit
            and inventory["combined_optimistic_ceiling_can_cover_conditional_deficit"] is (len(union) >= deficit)
            and inventory["optimistic_margin_before_new_overhead"] == len(union) - deficit,
            "Potential scalar omission counts remain conditional ceilings before new overhead, not measured savings")
        self.details["scalar_proposal_screen"] = {"zero_result_mul_div_sites": len(zero_results),
            "unique_scalar_identity_sites": len(scalar_indices), "additional_exact_duplicate_sites": len(extra),
            "combined_optimistic_ceiling": len(union), "conditional_deficit": deficit,
            "margin_before_new_overhead": len(union) - deficit, "measured_savings": None}

    def archive(self, checkpoint_path, manifest_path):
        checkpoint = decode(self.read_path(checkpoint_path))
        manifest_raw = self.read_path(manifest_path)
        manifest = decode(manifest_raw)
        self.need(checkpoint["checkpoint"] == manifest["checkpoint"] == 29
            and checkpoint["release_acceptance"] is False and checkpoint["full_product_goal_completed"] is False,
            "Final checkpoint and manifest retain diagnostic-only scope")
        archive = checkpoint["archive"]
        parts = archive["parts"]
        self.need(type(parts) is list and 1 <= len(parts) <= 1000,
            "Archive identifies a bounded ordered part inventory")
        joined, names = bytearray(), []
        for index, item in enumerate(parts, 1):
            name = relative(item["path"]).as_posix()
            if name in names or not name.endswith(".part" + str(index).zfill(3)):
                raise ValueError("Archive part order/identity is invalid")
            names.append(name)
            part = self.read_path(checkpoint_path.parent / name)
            if len(part) != item["bytes"] or digest(part) != item["sha256"]:
                raise ValueError("Archive part bytes differ: " + name)
            joined.extend(part)
            if len(joined) > MAX_ARCHIVE:
                raise ValueError("Excessive joined archive")
        self.need(len(joined) == archive["bytes"] and digest(joined) == archive["sha256"],
            "Every ordered archive part and complete joined ZIP hash verify")
        member_rows = manifest["members"]
        expected = {relative(row["path"]).as_posix(): row for row in member_rows}
        evidence_files = {path.relative_to(self.evidence).as_posix() for path in self.evidence.rglob("*") if path.is_file()}
        self.need(len(expected) == len(member_rows) == archive["member_count"] and set(expected) == evidence_files,
            "Manifest exactly covers the complete expanded evidence tree without duplicate members")
        errors, uncompressed = [], 0
        with zipfile.ZipFile(io.BytesIO(joined)) as zf:
            infos = zf.infolist()
            self.need(len(infos) == len(expected) and {item.filename for item in infos} == set(expected)
                and all(not item.is_dir() and not stat.S_ISLNK(item.external_attr >> 16) and not item.flag_bits & 1 for item in infos),
                "ZIP membership is exact, unique, nonencrypted and free of symlink members")
            for item in infos:
                relative(item.filename)
                wanted = expected[item.filename]
                if item.file_size != wanted["bytes"] or item.file_size > MAX_FILE:
                    raise ValueError("Unexpected uncompressed member size")
                raw = zf.read(item)  # zipfile validates the CRC on complete read.
                if digest(raw) != wanted["sha256"] or raw != self.raw(item.filename):
                    errors.append(item.filename)
                uncompressed += len(raw)
                if uncompressed > MAX_ARCHIVE:
                    raise ValueError("Excessive expanded evidence archive")
            self.need(zf.testzip() is None and not errors,
                "Every ZIP CRC/member hash and full expanded file byte identity verify", errors)
        if "uncompressed_bytes" in archive:
            self.need(archive["uncompressed_bytes"] == uncompressed, "Declared expanded byte total matches all members")
        if "manifest_sha256" in checkpoint:
            self.need(checkpoint["manifest_sha256"] == digest(manifest_raw), "Checkpoint binds exact manifest bytes")
        self.need(self.raw("drivers/audit_p09_capture_evidence.py") == Path(__file__).resolve().read_bytes(),
            "Archive retains the exact independently executed auditor source")
        self.details["archive"] = {"parts": len(parts), "members": len(expected), "bytes": len(joined),
            "sha256": digest(joined), "uncompressed_bytes": uncompressed,
            "all_part_and_member_hashes_verified": True, "all_zip_crcs_verified": True,
            "exact_expanded_evidence_bytes_verified": True}

    def finish(self):
        changes = []
        for name, expected in self.inputs.items():
            path = Path(name)
            raw = path.read_bytes()
            if len(raw) != expected["bytes"] or digest(raw) != expected["sha256"]:
                changes.append(name)
        self.check(not changes, "Every actually consumed audit input remains byte-stable, including raw GLB", changes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args(argv)
    if (args.checkpoint is None) != (args.manifest is None):
        parser.error("--checkpoint and --manifest must be supplied together")
    output, evidence = args.output.resolve(), args.evidence.resolve()
    if output.exists() or output.is_relative_to(evidence):
        parser.error("Use a new output file outside the expanded evidence tree")
    audit = Audit(args.repo, evidence)
    result = {"schema_version": "ontokin.p09-capture-evidence-audit/0.1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
        "product_runtime_executed": False, "product_request_status": "failed",
        "product_command_exit_codes": [1, 1], "accepted_artifact": False,
        "release_acceptance": False, "full_product_goal_completed": False,
        "elapsed_neutrality_claimed": False, "measured_full_cost_claimed": False,
        "new_recording_pass_claimed": False, "captured_source_minima_independently_certified": False,
        "scope": "Independent source/evidence/byte audit of the single neutral captured P09 refusal and conditional census. No product run, tail execution, successful export, performance acceptance or release gate.",
        "errors": []}
    try:
        own = audit.read_path(Path(__file__).resolve())
        result["auditor"] = {"path": str(Path(__file__).resolve()), "bytes": len(own), "sha256": digest(own)}
        capture, snapshot, raw, delta = audit.requests()
        audit.receipts(snapshot)
        groups, authored, stored, bits, json_sha = audit.glb_groups(raw, snapshot, capture)
        audit.census(capture, snapshot, groups, authored, stored, bits, json_sha, delta)
        if args.checkpoint is not None:
            audit.archive(args.checkpoint.resolve(), args.manifest.resolve())
        audit.finish()
    except Exception as error:
        result["errors"].append({"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()})
    result.update(status="passed" if not result["errors"] and all(row["passed"] for row in audit.checks) else "failed",
        checks=audit.checks, check_count=len(audit.checks), findings=audit.details, inputs=audit.inputs,
        archive_requested=args.checkpoint is not None, finished_at=datetime.now(timezone.utc).isoformat())
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"status": result["status"], "checks": len(audit.checks),
        "failed_checks": [row["check"] for row in audit.checks if not row["passed"]],
        "errors": [{"type": row["type"], "message": row["message"]} for row in result["errors"]],
        "product_request_status": "failed", "archive_requested": args.checkpoint is not None}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
