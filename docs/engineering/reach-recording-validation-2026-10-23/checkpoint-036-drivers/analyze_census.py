#!/usr/bin/env python3
"""Offline C036 neutrality and source-bound quaternion-proof census.

This program imports no OntoKin module and invokes no product callable. It
compares retained request evidence before interpreting the capture. Fractions
below are independent standard-library reconstructions after product failure.
"""
import argparse
import ast
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import struct
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
COMMIT = "4ca73909f861fe4bef9694787473621c1d21c140"
TREE = "87c949b238055af1ce368c694e1d5683c8aeacde"
REVISION = "sha256:7ee1fca89536d3618b0a9a39e39ea2286be9973ce14ae148d7d8806d973ff000"
MANIFEST = "docs/language-design/planar-reach-v0.1/p11.files.json"
MANIFEST_SHA256 = "f76b4f8350b7d0adbf6e0acc2c8d48d72fc2a7c12b1d3e4a48f633e548fc98f8"
MAX_BITS = 32768
MAX_JSON_BYTES = 16 * 1024 * 1024


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_equal(first, last):
    """JSON equality with exact native types and binary64 bits retained."""
    if type(first) is not type(last):
        return False
    if type(first) is dict:
        return first.keys() == last.keys() and all(strict_equal(first[k], last[k]) for k in first)
    if type(first) is list:
        return len(first) == len(last) and all(strict_equal(a, b) for a, b in zip(first, last))
    if type(first) is float:
        return struct.pack(">d", first) == struct.pack(">d", last)
    return first == last


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Nonfinite JSON constant: " + value)


def read_json(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing or non-regular evidence file: " + str(path))
    raw = path.read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("Evidence JSON exceeds declared analysis byte bound")
    value = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
    if type(value) is not dict:
        raise ValueError("Evidence root must be a JSON object")
    return value, {"path": str(path.resolve()), "bytes": len(raw), "sha256": digest(raw)}, raw


def write_json(path, value):
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError("Analysis output exceeds declared byte bound")
    with path.open("xb") as stream:
        stream.write(raw)


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, name, condition, detail=None):
        row = {"name": name, "passed": bool(condition)}
        if detail is not None:
            row["detail"] = detail
        self.rows.append(row)
        return bool(condition)

    @property
    def passed(self):
        return all(row["passed"] for row in self.rows)

    def report(self):
        return {"passed": self.passed, "checks": self.rows,
                "check_count": len(self.rows),
                "failed_checks": [row["name"] for row in self.rows if not row["passed"]]}


@dataclass(frozen=True)
class Opaque:
    class_name: str
    identity: str


@dataclass(frozen=True)
class Unavailable:
    reason: str = "Not retained in selected traceback locals"


UNAVAILABLE = Unavailable()


class NativeDecoder:
    """Read only the frozen driver's tagged native format; never eval()."""
    def __init__(self, bounds):
        self.bounds = bounds
        self.nodes = 0

    def integer(self, text):
        if type(text) is not str or len(text) > 2 + MAX_BITS // 4 + 2:
            raise ValueError("Invalid bounded hexadecimal integer")
        value = int(text, 16)
        if hex(value) != text or value.bit_length() > MAX_BITS:
            raise ValueError("Noncanonical or oversized hexadecimal integer")
        return value

    def decode(self, node, depth=0):
        self.nodes += 1
        if (type(node) is not dict or depth > self.bounds["depth"]
                or self.nodes > self.bounds["native_nodes"] * 4):
            raise ValueError("Tagged native shape exceeds the declared analysis bounds")
        kind = node.get("type")
        if kind == "unavailable":
            if set(node) != {"type"}:
                raise ValueError("Malformed unavailable value")
            return UNAVAILABLE
        if kind in ("NoneType", "bool", "str"):
            if set(node) != {"type", "value"}:
                raise ValueError("Malformed native scalar")
            value = node["value"]
            expected = {"NoneType": type(None), "bool": bool, "str": str}[kind]
            if type(value) is not expected or kind == "str" and len(value) > self.bounds["string_characters"]:
                raise ValueError("Wrong native scalar type or bound")
            return value
        if kind == "int":
            if set(node) != {"type", "hex"}:
                raise ValueError("Malformed integer tag")
            return self.integer(node["hex"])
        if kind == "float":
            if set(node) != {"type", "hex", "bits_be"} or len(node["bits_be"]) != 16:
                raise ValueError("Malformed binary64 tag")
            raw = bytes.fromhex(node["bits_be"])
            value = struct.unpack(">d", raw)[0]
            if not math.isfinite(value) or value.hex() != node["hex"]:
                raise ValueError("Nonfinite or inconsistent binary64 tag")
            return value
        if kind == "Fraction":
            if set(node) != {"type", "numerator_hex", "denominator_hex"}:
                raise ValueError("Malformed rational tag")
            n, d = self.integer(node["numerator_hex"]), self.integer(node["denominator_hex"])
            if d <= 0:
                raise ValueError("Rational denominator must be positive")
            value = Fraction(n, d)
            if (value.numerator, value.denominator) != (n, d):
                raise ValueError("Noncanonical captured Fraction storage")
            return value
        if kind in ("tuple", "list"):
            if set(node) != {"type", "items"} or type(node["items"]) is not list:
                raise ValueError("Malformed native sequence")
            if len(node["items"]) > self.bounds["container_items"]:
                raise ValueError("Native sequence count bound exceeded")
            items = [self.decode(value, depth + 1) for value in node["items"]]
            return tuple(items) if kind == "tuple" else items
        if kind == "dict":
            if set(node) != {"type", "entries"} or type(node["entries"]) is not list:
                raise ValueError("Malformed native mapping")
            if len(node["entries"]) > self.bounds["container_items"]:
                raise ValueError("Native mapping count bound exceeded")
            result = {}
            for row in node["entries"]:
                if type(row) is not list or len(row) != 2:
                    raise ValueError("Malformed native mapping pair")
                key, value = (self.decode(member, depth + 1) for member in row)
                if key in result:
                    raise ValueError("Duplicate decoded native mapping key")
                result[key] = value
            return result
        if kind == "opaque":
            if set(node) != {"type", "class", "identity"} or not all(type(node[k]) is str for k in ("class", "identity")):
                raise ValueError("Malformed opaque identity")
            return Opaque(node["class"], node["identity"])
        raise ValueError("Unknown native tag: " + str(kind))


def describe(value):
    """JSON description of independently reconstructed native values."""
    if isinstance(value, Unavailable):
        return {"type": "unavailable", "reason": value.reason}
    if isinstance(value, Opaque):
        return {"type": "opaque", "class": value.class_name, "identity": value.identity}
    if type(value) is Fraction:
        return {"type": "Fraction", "numerator": str(value.numerator),
                "denominator": str(value.denominator),
                "numerator_bits": value.numerator.bit_length(),
                "denominator_bits": value.denominator.bit_length()}
    if type(value) is float:
        n, d = value.as_integer_ratio()
        return {"type": "float", "hex": value.hex(), "bits_be": struct.pack(">d", value).hex(),
                "exact_numerator": str(n), "exact_denominator": str(d)}
    if value is None or type(value) in (bool, str, int):
        return {"type": type(value).__name__, "value": value}
    if type(value) in (tuple, list):
        return {"type": type(value).__name__, "items": [describe(x) for x in value]}
    if type(value) is dict:
        return {"type": "dict", "entries": [[describe(k), describe(v)] for k, v in value.items()]}
    raise ValueError("Foreign offline description type")


def source_signature(value, depth=-1):
    """Independent transcription of the exact selected source signature."""
    kind = type(value)
    if kind is Fraction:
        return ("fraction", value.numerator, value.denominator)
    if kind is tuple:
        if depth >= 3 or len(value) > (16 if depth == -1 else 8):
            raise ValueError("Source signature shape exceeds its own bound")
        return ("tuple", tuple(source_signature(item, depth + 1) for item in value))
    if kind is float:
        return ("float", value.hex())
    if value is None or kind in (str, int):
        return (kind.__name__, value)
    # The observed orientation payload has no Interval. Do not guess one from
    # an opaque identity or silently extend the admitted reconstruction domain.
    raise ValueError("Unsupported source-signature member in captured payload")


def same_recording_vector(first, last, size):
    return (type(first) in (tuple, list) and type(last) in (tuple, list)
            and len(first) == len(last) == size
            and all(type(a) is type(b) and a == b for a, b in zip(first, last)))


def vector_bits_equal(first, last):
    if type(first) not in (tuple, list) or type(last) not in (tuple, list) or len(first) != len(last):
        return False
    return all(type(a) is type(b) and (struct.pack(">d", a) == struct.pack(">d", b)
               if type(a) is float else a == b) for a, b in zip(first, last))


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args]).decode().strip()


def safe_member(root, name):
    if type(name) is not str or "\\" in name:
        raise ValueError("Invalid repository-relative input path")
    parsed = PurePosixPath(name)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        raise ValueError("Unsafe repository-relative input path")
    path = root.joinpath(*parsed.parts)
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("Input path is missing, a symlink, or outside execution checkout")
    return path


def validate_inventory(root, inventory, checks):
    checks.add("inventory exact source identity", inventory.get("commit") == COMMIT and inventory.get("tree") == TREE
               and inventory.get("status") == "")
    rows = inventory["files"]
    checks.add("inventory counts", type(rows) is list and type(inventory["file_count"]) is int
               and inventory["file_count"] == len(rows) and inventory["total_bytes"] == sum(x["bytes"] for x in rows))
    seen, mismatches = set(), []
    for row in rows:
        name = row["path"]
        if name in seen:
            raise ValueError("Duplicate inventory path")
        seen.add(name)
        raw = safe_member(root, name).read_bytes()
        git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        mode = "100755" if (root / name).stat().st_mode & 0o111 else "100644"
        if (type(row["bytes"]) is not int or len(raw) != row["bytes"] or digest(raw) != row["sha256"]
                or git_blob != row["git_blob"] or mode != row["mode"]):
            mismatches.append(name)
    tracked = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z"]).decode().split("\0")
    checks.add("complete actual tracked membership", seen == set(filter(None, tracked)))
    tree_raw = subprocess.check_output(["git", "-C", str(root), "ls-tree", "-r", "-z", "HEAD"])
    tree_map = {}
    for entry in tree_raw.decode().split("\0"):
        if not entry:
            continue
        metadata, name = entry.split("\t", 1)
        mode, kind, blob = metadata.split()
        if kind != "blob" or name in tree_map:
            raise ValueError("Unexpected or duplicate committed tree entry")
        tree_map[name] = {"git_blob": blob, "mode": mode}
    inventory_map = {row["path"]: {"git_blob": row["git_blob"], "mode": row["mode"]} for row in rows}
    checks.add("complete inventory blob and mode map equals committed HEAD tree",
               strict_equal(inventory_map, tree_map),
               {"git_ls_tree_sha256": digest(tree_raw), "committed_blob_count": len(tree_map)})
    checks.add("all inventory bytes and modes match actual execution checkout", not mismatches,
               {"files": len(rows), "bytes": inventory["total_bytes"], "mismatches": mismatches})
    checks.add("actual clean held candidate checkout", git(root, "rev-parse", "HEAD") == COMMIT
               and git(root, "rev-parse", "HEAD^{tree}") == TREE
               and git(root, "status", "--porcelain=v1", "--untracked-files=all") == "")
    manifest = next(row for row in rows if row["path"] == MANIFEST)
    checks.add("original P11 file manifest", manifest["sha256"] == MANIFEST_SHA256)


def command_fields(row):
    command = row["command"]
    if type(command) is not list or len(command) != 8 or any(type(x) is not str for x in command):
        raise ValueError("Unexpected frozen driver invocation shape")
    pairs = dict(zip(command[2::2], command[3::2]))
    if set(pairs) != {"--root", "--output", "--mode"}:
        raise ValueError("Unexpected frozen driver arguments")
    return command[:2], pairs


def source_snippets(root, files):
    result = {}
    for filename, names in files.items():
        path = safe_member(root, filename)
        raw, text = path.read_bytes(), path.read_text()
        tree = ast.parse(text)
        for qualified in names:
            nodes = tree.body
            found = None
            for part in qualified.split("."):
                matches = [node for node in nodes if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == part]
                if len(matches) != 1:
                    raise ValueError("Source snippet cannot be resolved uniquely: " + qualified)
                found = matches[0]
                nodes = found.body
            result[filename + ":" + qualified] = {
                "source_path": filename, "file_sha256": digest(raw),
                "first_line": found.lineno, "last_line": found.end_lineno,
                "source": "\n".join(text.splitlines()[found.lineno - 1:found.end_lineno]),
                "ast_sha256": digest(ast.dump(found, include_attributes=False).encode())}
    return result


def neutrality(control_dir, capture_dir, root):
    checks, evidence = Checks(), {}
    maps, raw_inputs = {}, []
    for label, directory in (("control", control_dir), ("capture", capture_dir)):
        maps[label] = {}
        for filename in ("start.json", "request-result.json", "inputs-before.json", "inputs-after.json"):
            value, meta, raw = read_json(directory / filename)
            maps[label][filename] = value
            evidence[label + "/" + filename] = meta
            if filename.startswith("inputs-"):
                raw_inputs.append(raw)
        start, row = maps[label]["start.json"], maps[label]["request-result.json"]
        forbidden = ("metadata_status", "metadata_error", "capture_error", "capture_failure",
                     "inventory_error", "unexpected_completion")
        present_errors = [key for key in forbidden if key in row]
        checks.add(label + " no metadata capture inventory or completion errors", not present_errors,
                   {"forbidden_fields_present": present_errors})
        checks.add(label + " immutable start fields", all(key in row and strict_equal(value, row[key]) for key, value in start.items()))
        checks.add(label + " correct declared mode", start["mode"] == row["mode"] == label)
        checks.add(label + " stable source and driver receipts", row.get("inputs_stable") is True and row.get("driver_unchanged") is True)
        checks.add(label + " counters and caches unchanged by post-failure observation",
                   row.get("observation_preserved_counters_and_caches") is True
                   and strict_equal(row["post_state"], row["post_observation_state"]))
        checks.add(label + " actual failed original request", row["status"] == "failed"
                   and row["failure"]["type"] == "OntoKinError"
                   and row["failure"]["message"] == "Construction exceeded max_operations."
                   and row["release_acceptance"] is False and row["original_exception_identity_preserved"] is True)
        checks.add(label + " immutable exact execution source", row["source_commit"] == COMMIT and row["source_tree"] == TREE)
        checks.add(label + " original source/program/contract", row["source_files"] == MANIFEST
                   and row["source_manifest_sha256"] == MANIFEST_SHA256
                   and row["program_revision"] == row["expected_program_revision"] == REVISION
                   and row["target_contract"] == "ontokin.glb/0.6")
        checks.add(label + " no profile or trace installed", row["profile_installed"] is False and row["trace_installed"] is False)
        op = row["options"]
        checks.add(label + " original full P11 request settings", strict_equal(op, {
                   "end": "3", "fps": 1, "helpers": False,
                   "position_tolerance_m": .001, "rotation_tolerance_rad": .001,
                   "time_tolerance_s": .000001}))
        state = row["post_state"]
        expected_limits = {"max_operations": 100000, "max_elapsed_ms": 30000,
                           "max_operand_bits": 32768, "max_cache_entries": 256}
        checks.add(label + " unchanged work limits", strict_equal(state["work_limits"], expected_limits))
        checks.add(label + " original operation cap refusal", type(state["shared_operations"]) is int
                   and state["shared_operations"] == 100001 and state["construction_limits"]["max_operations"] == 100000)
        work = state["reach_work"]
        checks.add(label + " exact category reconciliation", type(work["counts"]) is dict
                   and all(type(k) is str and type(v) is int and v >= 0 for k, v in work["counts"].items())
                   and sum(work["counts"].values()) == work["operations"]
                   and state["shared_minus_reach_operations"] == state["shared_operations"] - work["operations"])
        checks.add(label + " original frame inventory bounded", type(row["traceback_frames"]) is list
                   and len(row["traceback_frames"]) <= row["native_capture_bounds"]["frames"])
        executable, fields = command_fields(row)
        checks.add(label + " explicit command bindings", executable[0] == row["environment"]["executable"]
                   and Path(fields["--root"]).resolve() == root and Path(fields["--output"]).resolve() == directory
                   and fields["--mode"] == label and Path(row["cwd"]).resolve() == root)
        driver = Path(executable[1])
        checks.add(label + " driver byte identity", driver.is_file() and digest(driver.read_bytes()) == row["driver_sha256"])
        interpreter = Path(executable[0]).resolve()
        checks.add(label + " exact interpreter executable bytes", interpreter.is_file()
                   and digest(interpreter.read_bytes()) == row["environment"]["executable_sha256"])
        command_dir = directory.parent / (label + "-command")
        command_start, meta, _ = read_json(command_dir / "start.json")
        evidence[label + "-command/start.json"] = meta
        command_result, meta, _ = read_json(command_dir / "result.json")
        evidence[label + "-command/result.json"] = meta
        maps[label]["command-result"] = command_result
        checks.add(label + " outer command retained original start fields", all(
                   key in command_result and strict_equal(value, command_result[key]) for key, value in command_start.items()))
        checks.add(label + " outer command matches request invocation", command_result["command"] == [executable[0], "-B", *row["command"][1:]]
                   and command_result["cwd"] == row["cwd"] and command_result["driver_sha256"] == row["driver_sha256"])
        checks.add(label + " closed failed product command", type(command_result["exit_code"]) is int
                   and command_result["exit_code"] == 1 and not command_result.get("timed_out", False)
                   and command_result["driver_unchanged"] is True and command_result["timeout_seconds"] == 180)
        checks.add(label + " both raw streams listed exactly once", [x["path"] for x in command_result["streams"]] == ["stdout.txt", "stderr.txt"])
        for stream in command_result["streams"]:
            if stream["path"] not in ("stdout.txt", "stderr.txt"):
                raise ValueError("Unexpected command stream path")
            stream_path = command_dir / stream["path"]
            if stream_path.is_symlink() or not stream_path.is_file():
                raise ValueError("Command stream is not a regular file")
            raw = stream_path.read_bytes()
            checks.add(label + " closed " + stream["path"] + " identity", type(stream["bytes"]) is int
                       and len(raw) == stream["bytes"] and digest(raw) == stream["sha256"])
            evidence[label + "-command/" + stream["path"]] = {"path": str(stream_path), "bytes": len(raw), "sha256": digest(raw)}
        traceback_path = directory / "traceback.txt"
        traceback_raw = traceback_path.read_bytes()
        maps[label]["raw-traceback"] = traceback_raw
        evidence[label + "/traceback.txt"] = {"path": str(traceback_path), "bytes": len(traceback_raw), "sha256": digest(traceback_raw)}
        for external in [x for x in row["traceback_frames"] if x["scope"] == "external_driver"]:
            checks.add(label + " external traceback frame is frozen driver", Path(external["path"]).resolve() == driver.resolve()
                       and external["source_sha256"] == row["driver_sha256"])
        for frame in [x for x in row["traceback_frames"] if x["scope"] == "product"]:
            source = safe_member(root, frame["path"])
            lines = source.read_text().splitlines()
            checks.add(label + " product frame " + frame["qualname"], digest(source.read_bytes()) == frame["source_sha256"]
                       and type(frame["line"]) is int and 1 <= frame["line"] <= len(lines)
                       and lines[frame["line"] - 1] == frame["statement"])
    first, last = maps["control"]["request-result.json"], maps["capture"]["request-result.json"]
    checks.add("all four inventories are byte-identical", all(raw == raw_inputs[0] for raw in raw_inputs[1:]))
    checks.add("raw complete traceback bytes are identical", maps["control"]["raw-traceback"] == maps["capture"]["raw-traceback"])
    validate_inventory(root, maps["control"]["inputs-before.json"], checks)
    checks.add("pair shares one declared output root", control_dir.parent == capture_dir.parent)
    plan, meta, _ = read_json(control_dir.parent / "plan.json")
    evidence["pair-plan.json"] = meta
    pair_receipt, pair_meta, _ = read_json(control_dir.parent / "pair-command.json")
    evidence["pair-command.json"] = pair_meta
    checks.add("frozen pair plan and complete two-command receipt", pair_receipt["plan_sha256"] == meta["sha256"]
               and pair_receipt["requests_executed"] == 2 and plan["order"] == ["control", "capture"]
               and plan["requests_per_mode"] == 1
               and strict_equal(pair_receipt["commands"], [maps[label]["command-result"] for label in ("control", "capture")]))
    checks.add("predeclared original-request-only diagnostic plan", plan["source_commit"] == COMMIT and plan["source_tree"] == TREE
               and plan["driver_sha256"] == first["driver_sha256"]
               and strict_equal(plan["request"], {"case": "P11", "end": "3", "fps": 1, "helpers": False})
               and all(plan[key] is True for key in ("product_limits_unchanged", "no_live_instrumentation",
                       "no_timing_acceptance_threshold", "no_reruns_or_exclusions_in_this_plan",
                       "neutrality_required_before_census_interpretation")))
    inventory_sha256s = {row["sha256"] for row in maps["control"]["inputs-before.json"]["files"]}
    checks.add("actual source-unit hashes occur in exact checkout", all(
               unit["sha256"] in inventory_sha256s for unit in first["source_units"]))
    excluded = {"mode", "command", "started_at", "finished_request_at", "product_elapsed_seconds",
                "finished_receipt_at", "capture_status", "census_sha256"}
    common_first = {k: v for k, v in first.items() if k not in excluded}
    common_last = {k: v for k, v in last.items() if k not in excluded}
    checks.add("entire common result uses strict native JSON equality", strict_equal(common_first, common_last),
               {"excluded_only": sorted(excluded), "common_keys": sorted(common_first)})
    start_excluded = {"mode", "command", "started_at"}
    checks.add("entire common start uses strict native JSON equality",
               strict_equal({k: v for k, v in maps["control"]["start.json"].items() if k not in start_excluded},
                            {k: v for k, v in maps["capture"]["start.json"].items() if k not in start_excluded}))
    a_cmd, a_args = command_fields(first)
    b_cmd, b_args = command_fields(last)
    checks.add("command executable driver root identity", strict_equal(a_cmd, b_cmd) and a_args["--root"] == b_args["--root"])
    checks.add("capture completed only after failure", first["capture_status"] == "not_requested" and last["capture_status"] == "captured"
               and "capture_failure" not in last)
    checks.add("all product traceback frames agree without removal", strict_equal(
               [x for x in first["traceback_frames"] if x["scope"] == "product"],
               [x for x in last["traceback_frames"] if x["scope"] == "product"]))
    checks.add("external driver frames agree separately", strict_equal(
               [x for x in first["traceback_frames"] if x["scope"] == "external_driver"],
               [x for x in last["traceback_frames"] if x["scope"] == "external_driver"]))
    checks.add("complete failure diagnostic agreement", strict_equal(first["failure"], last["failure"])
               and strict_equal(first["diagnostic"], last["diagnostic"]))
    checks.add("all counters categories limits and cache occupancies agree", strict_equal(first["post_state"], last["post_state"]))
    report = checks.report()
    report.update({"comparison_rule": "Exact JSON native types, exact float bits, and complete key sets; no product frame removed",
                   "external_frames": {"control": [x for x in first["traceback_frames"] if x["scope"] == "external_driver"],
                                       "capture": [x for x in last["traceback_frames"] if x["scope"] == "external_driver"]},
                   "timing": {"control_product_seconds": first["product_elapsed_seconds"],
                              "capture_product_seconds": last["product_elapsed_seconds"],
                              "elapsed_neutrality_claimed": False, "performance_acceptance_claimed": False},
                   "post_state": first["post_state"],
                   "cache_note": "Work-cache and independent-arithmetic cache occupancies are distinct observations; both are compared"})
    return report, evidence, last


def reconstruct_proof(row, actual, expected, radius, claim, decoder):
    proof = decoder.decode(row["orientation_proof"])
    verdict = {"order": row["order"], "carrier": row["carrier"], "comparison_identity": row["comparison_identity"],
               "provenance": "Existing completed comparison record retained in this key's result map; read after failure",
               "predicate_checks_in_source_order": []}
    conditions = verdict["predicate_checks_in_source_order"]
    def gate(name, ok, details=None):
        entry = {"condition": name, "satisfied": bool(ok), "reached_by_original_predicate": all(x["satisfied"] for x in conditions)}
        if details is not None:
            entry["details"] = details
        conditions.append(entry)
    gate("proof is tuple of length 2", type(proof) is tuple and len(proof) == 2)
    if not conditions[-1]["satisfied"]:
        verdict.update(first_mismatch="unavailable_proof" if proof is None else "proof_shape",
                       proof=describe(proof), identical_completed_arithmetic_excluding_claim=False)
        return verdict
    payload, signature = proof
    gate("payload is tuple of length 7", type(payload) is tuple and len(payload) == 7)
    if not conditions[-1]["satisfied"]:
        verdict.update(first_mismatch="payload_shape", proof=describe(proof), identical_completed_arithmetic_excluding_claim=False)
        return verdict
    try:
        observed_signature = source_signature(payload)
        seal_equal, seal_error = observed_signature == signature, None
    except ValueError as error:
        observed_signature, seal_equal, seal_error = None, False, str(error)
    gate("source signature equals saved seal", seal_equal,
         {"saved": describe(signature), "reconstructed": describe(observed_signature), "reconstruction_error": seal_error})
    gate("actual quaternion has equal types and values", same_recording_vector(actual, payload[0], len(actual)),
         {"binary64_bits_equal_separate_observation": vector_bits_equal(actual, payload[0]),
          "source_predicate_compares_bits": False})
    gate("sign-selected expected center equals saved center", expected == payload[1])
    gate("orientation radius equals saved radius", radius == payload[2])
    gate("claim native type equals saved claim native type", type(claim) is type(payload[3]))
    gate("claim value equals saved claim value", claim == payload[3])
    gate("saved operand domain equals 32768", payload[6] == MAX_BITS)
    gate("completed error is Fraction", type(payload[4]) is Fraction)
    gate("completed magnitude is None or Fraction", payload[5] is None or type(payload[5]) is Fraction)
    labels = {2: "seal", 3: "actual_quaternion", 4: "expected_center", 5: "orientation_radius",
              6: "typed_claim", 7: "typed_claim", 8: "operand_domain", 9: "completed_error_type", 10: "completed_magnitude_type"}
    failed_index = next((i for i, item in enumerate(conditions) if not item["satisfied"]), None)
    verdict["first_mismatch"] = labels[failed_index] if failed_index is not None else None
    verdict["initial_predicate_satisfied"] = failed_index is None
    verdict["payload"] = {"actual": describe(payload[0]), "expected_center": describe(payload[1]),
                           "radius": describe(payload[2]), "typed_claim": describe(payload[3]),
                           "completed_error": describe(payload[4]), "magnitude": describe(payload[5]),
                           "operand_domain": describe(payload[6])}
    excluded_claim_indices = {6, 7}
    identical = all(item["satisfied"] for i, item in enumerate(conditions) if i not in excluded_claim_indices)
    verdict["identical_completed_arithmetic_excluding_claim"] = identical
    verdict["typed_claim_is_only_initial_predicate_blocker"] = identical and failed_index in excluded_claim_indices
    # Recompute only the candidate's already completed arithmetic. This does not
    # resume the current request or execute its unvisited tail.
    numerical_shape = (type(payload[0]) in (tuple, list) and len(payload[0]) == 4
                       and all(type(x) in (int, float) for x in payload[0])
                       and type(payload[1]) is tuple and len(payload[1]) == 4
                       and all(type(x) is Fraction for x in payload[1])
                       and type(payload[2]) is Fraction and type(payload[4]) is Fraction)
    if numerical_shape:
        earlier_l1 = sum((abs(Fraction(a) - b) for a, b in zip(payload[0], payload[1])), Fraction(0))
        earlier_error = 2 * (earlier_l1 + payload[2])
        verdict["completed_arithmetic_offline_check"] = {
            "scope": "Reconstruction of this record's already completed quaternion bound only",
            "l1": describe(earlier_l1), "orientation_error": describe(earlier_error),
            "matches_retained_completed_error": earlier_error == payload[4]}
        if identical and type(claim) in (int, float, Fraction):
            verdict["retained_error_vs_current_claim_offline"] = {
                "retained_completed_error": describe(payload[4]), "current_claim_exact": describe(Fraction(claim)),
                "less_than_or_equal": payload[4] <= Fraction(claim),
                "live_claim_check_executed_by_analyzer": False,
                "meaning": "Independent numerical comparison only; the original predicate still declines and any future reuse needs fresh claim checks"}
    verdict["conditional_post_hit_checks"] = {
        "executed_in_reconstruction": False,
        "source_steps": ["copy completed Fraction fields", "checked reuse admission tick", "payload operand-domain checks",
                         "second seal equality", "current owner/operand/domain check"],
        "meaning": "These follow a successful initial predicate. No missed proof's later callbacks or admission are inferred."}
    return verdict


def reconstruct_scalar_repetition(census, proofs, actual, expected, l1, failed_index, decoder):
    """Bounded comparison of corresponding visited quaternion components.

    A donor's ordinary l1 path is reconstructed only when it was pending in
    this key, returned a sealed centered proof, and every earlier completed
    candidate declined under the unmodified predicate. Its frame is no longer
    present; this is explicitly source-order reconstruction, not a call log.
    """
    report = {"scope": "Four corresponding quaternion components of earlier newly completed records in this key only",
              "provenance": "Offline source-order reconstruction from retained completed records and current l1 locals",
              "donor_paths": [], "repeated_completed_nonzero_decodes": [],
              "equal_zero_shortcuts_without_decode_charge": [],
              "whole_proof_equality_implied": False, "optimization_selected": False,
              "net_charge_saving_measured": False, "unvisited_current_components_analyzed": False}
    if failed_index is None:
        report["unknown"] = "The current l1 component index is ambiguous; no completed scalar repetition is inferred"
        return report
    order = census["carrier_order"]
    prior_pending = order["pending_before_current"]
    fallback = order["centered_fallback_before_current"]
    for donor in proofs:
        if donor["carrier"] not in prior_pending or donor["carrier"] in fallback:
            continue
        proof = decoder.decode(donor["orientation_proof"])
        if type(proof) is not tuple or len(proof) != 2 or type(proof[0]) is not tuple or len(proof[0]) != 7:
            continue
        payload, seal = proof
        if source_signature(payload) != seal:
            continue
        donor_actual, donor_expected, donor_radius, donor_claim = payload[:4]
        if (type(donor_actual) is not tuple or len(donor_actual) != 4
                or type(donor_expected) is not tuple or len(donor_expected) != 4
                or not all(type(x) in (int, float) for x in donor_actual)
                or not all(type(x) is Fraction for x in donor_expected)):
            continue
        predecessors = proofs[:donor["order"]]
        decisions = [reconstruct_proof(row, donor_actual, donor_expected, donor_radius, donor_claim, decoder)
                     for row in predecessors]
        declined = all(row["first_mismatch"] is not None for row in decisions)
        path = {"carrier": donor["carrier"], "completed_record_order": donor["order"],
                "pending_in_current_key_before_refusal": True,
                "sealed_completed_orientation_record": True,
                "predecessor_candidates_in_original_order": [
                    {"carrier": row["carrier"], "first_mismatch": row["first_mismatch"]} for row in decisions],
                "predecessor_without_orientation_proof_count": sum(row["first_mismatch"] == "unavailable_proof" for row in decisions),
                "predecessor_with_orientation_proof_count": sum(row["first_mismatch"] != "unavailable_proof" for row in decisions),
                "every_predecessor_declined": declined,
                "ordinary_quaternion_l1_completed_reconstructed": declined,
                "reason": "The source loop only appends a completed comparison after return; with every earlier reuse candidate declined, this donor completed its ordinary quaternion l1"}
        report["donor_paths"].append(path)
        if not declined:
            continue
        for index in range(failed_index + 1):
            current_raw, donor_raw = actual[index], donor_actual[index]
            equal = type(current_raw) is type(donor_raw) and (
                struct.pack(">d", current_raw) == struct.pack(">d", donor_raw)
                if type(current_raw) is float else current_raw == donor_raw)
            if not equal:
                continue
            base = {"donor_carrier": donor["carrier"], "current_carrier": order["current"],
                    "component_index": index, "component_axis": ("x", "y", "z", "w")[index],
                    "native_input": describe(current_raw)}
            if current_raw == 0:
                report["equal_zero_shortcuts_without_decode_charge"].append({**base,
                    "original_value_path": "Fraction(0) shortcut", "decode_charge_per_occurrence": 0,
                    "repeated_charged_decode_established": False})
                continue
            decoded = Fraction(current_raw)
            current_value = l1["value"] if index == failed_index else decoded
            donor_subtraction = Fraction(donor_raw) - donor_expected[index]
            current_subtraction = current_value - expected[index]
            current_error = l1["error"] if index == failed_index else abs(current_subtraction)
            denominator = math.lcm(donor_expected[index].denominator, expected[index].denominator)
            difference_numerator = (donor_expected[index].numerator * (denominator // donor_expected[index].denominator)
                                    - expected[index].numerator * (denominator // expected[index].denominator))
            report["repeated_completed_nonzero_decodes"].append({**base,
                "donor_decode_value_reconstructed": describe(decoded),
                "current_completed_decode_value": describe(current_value),
                "decode_values_equal": decoded == current_value,
                "donor_completion_provenance": "Source-order reconstruction: all preceding completed proofs declined; donor's sealed result returned after ordinary l1",
                "current_completion_provenance": ("Retained completed l1.value before the refused addition" if index == failed_index
                                                  else "Source-order prefix before the uniquely identified failed l1 component"),
                "original_decoder": "_Bounds.value", "original_charge_kind": "independent_bound_decode",
                "decode_charge_per_occurrence": 1,
                "donor_expected_component": describe(donor_expected[index]),
                "current_expected_component": describe(expected[index]),
                "expected_components_equal": donor_expected[index] == expected[index],
                "donor_minus_current_expected_reduced": describe(donor_expected[index] - expected[index]),
                "donor_minus_current_expected_common_denominator": {
                    "numerator": str(difference_numerator), "denominator": str(denominator)},
                "donor_subtraction_result_reconstructed": describe(donor_subtraction),
                "current_subtraction_result_reconstructed": describe(current_subtraction),
                "subtraction_results_equal": donor_subtraction == current_subtraction,
                "donor_absolute_error_reconstructed": describe(abs(donor_subtraction)),
                "current_completed_absolute_error": describe(current_error),
                "absolute_errors_equal": abs(donor_subtraction) == current_error,
                "scope_limit": "Only the typed scalar decode repeats. Neither an entire quaternion bound nor a net saving follows."})
    return report


def analyze_capture(census, request, root):
    checks = Checks()
    decoder = NativeDecoder(census["bounds"])
    key = {name: decoder.decode(value) for name, value in census["key"].items()}
    comparison = {name: decoder.decode(value) for name, value in census["comparison"].items()}
    l1 = {name: decoder.decode(value) for name, value in census["l1"].items()}
    actual, expected = comparison["quaternion"], comparison["expected"]
    radius, limits = comparison["rotation_radius"], comparison["limits"]
    checks.add("quaternion native dimensions", type(actual) is tuple and len(actual) == 4
               and all(type(x) in (int, float) for x in actual)
               and type(expected) is tuple and len(expected) == 4 and all(type(x) is Fraction for x in expected))
    checks.add("radius and claims captured", type(radius) is Fraction and type(limits) is tuple and len(limits) == 2)
    checks.add("captured current quaternion is l1 input", same_recording_vector(actual, l1["actual"], 4)
               and vector_bits_equal(actual, l1["actual"]) and expected == l1["expected"])
    checks.add("current key quaternion binds comparison", same_recording_vector(key["quaternion"], actual, 4)
               and vector_bits_equal(key["quaternion"], actual) and key["limits"] == limits)
    source_rotation = comparison["source_rotation"]
    axis = max(range(4), key=lambda index: abs(actual[index]))
    selected = (source_rotation[1], source_rotation[2], source_rotation[3], source_rotation[0])
    negated = actual[axis] < 0 < selected[axis] or actual[axis] > 0 > selected[axis]
    if negated:
        selected = tuple(-value for value in selected)
    checks.add("sign representative reconstructed from source rule", axis == comparison["axis"] and selected == expected)
    operation = census["attempted_operation"]
    operands = decoder.decode(operation["ordered_operands"])
    checks.add("refused add operands bind retained l1", operation["completed"] is False and operation["operation"] == "add"
               and operands == (l1["distance"], l1["error"])
               and operands == decoder.decode(operation["checked_args"])
               and operation["checked_result_available"] is False)
    component_candidates, prefix_rows = [], []
    prefix = Fraction(0)
    for index, (raw, point) in enumerate(zip(actual, expected)):
        value = Fraction(0) if raw == 0 else Fraction(raw)
        error = Fraction(0) if value == point else abs(value - point)
        match = (type(raw) is type(l1["raw"]) and (struct.pack(">d", raw) == struct.pack(">d", l1["raw"])
                 if type(raw) is float else raw == l1["raw"]) and point == l1["point"] and value == l1["value"]
                 and error == l1["error"] and prefix == l1["distance"] and bool(error) and bool(prefix))
        if match:
            component_candidates.append(index)
        prefix_rows.append({"index": index, "axis": ("x", "y", "z", "w")[index], "raw": describe(raw),
                            "point": describe(point), "value": describe(value), "error": describe(error),
                            "distance_before": describe(prefix)})
        if error:
            prefix = error if not prefix else prefix + error
    checks.add("refused component has an exact retained-local match", bool(component_candidates))
    unique_index = component_candidates[0] if len(component_candidates) == 1 else None
    attempt = {"provenance": "Operand values observed in retained l1/op frames; index reconstructed from source-order prefix equality",
               "component_index_candidates_zero_based": component_candidates,
               "unique_component_index": unique_index,
               "unique_component_axis": None if unique_index is None else ("x", "y", "z", "w")[unique_index],
               "index_ambiguity": len(component_candidates) != 1,
               "value": describe(l1["value"]), "point": describe(l1["point"]), "error": describe(l1["error"]),
               "distance_before_attempted_add": describe(l1["distance"]), "ordered_add_operands": describe(operands),
               "product_add_completed": False,
               "attempted_sum_offline_only": describe(operands[0] + operands[1]),
               "current_complete_orientation_error_computed": False,
               "prefix_through_refused_component": [] if unique_index is None else prefix_rows[:unique_index + 1]}
    order = census["carrier_order"]
    geometry, completed, pending = order["geometry"], order["completed"], order["pending_original"]
    checks.add("carrier source order is unique", len(geometry) == len(set(geometry)) and order["observed"] == geometry)
    checks.add("current carrier binds local fields", order["current"] == key["carrier"] and key["carrier"] in pending
               and key["carrier"] not in completed)
    checks.add("pending carrier prefix is exact", pending == order["pending_before_current"] + [order["current"]] + order["pending_after_current"])
    proofs = census["completed_orientation_proofs"]
    checks.add("all available completed records included in order", [p["carrier"] for p in proofs] == completed
               and [p["order"] for p in proofs] == list(range(len(proofs))))
    decisions = [reconstruct_proof(row, actual, expected, radius, limits[1], decoder) for row in proofs]
    scalar_repetition = reconstruct_scalar_repetition(census, proofs, actual, expected, l1, unique_index, decoder)
    checks.add("repeated scalar decodes match retained current values", all(
               row["decode_values_equal"] is True for row in scalar_repetition["repeated_completed_nonzero_decodes"]))
    checks.add("source loop reached ordinary l1 only after all available proofs declined",
               all(row["first_mismatch"] is not None for row in decisions))
    checks.add("retained completed proof errors independently reconstruct", all(
               row.get("completed_arithmetic_offline_check", {}).get("matches_retained_completed_error", True)
               for row in decisions))
    history = census["source"]["history"]
    times = [decoder.decode(row["time"]) for row in history]
    checks.add("native exact increasing source boundaries", all(type(x) is Fraction for x in times)
               and all(a < b for a, b in zip(times, times[1:])))
    phase = sum(time <= key["time"] for time in times) - 1
    current_state = history[phase]["after_state_identity"] if phase >= 0 else None
    context = key["recording_context"]
    matching_plans = []
    for row in census["batch_post_cleanup"]["plans"]:
        pc = decoder.decode(row["context"])
        target_paths = decoder.decode(row["targets"])
        if type(pc) is tuple and len(pc) == 4 and pc[0] == context and pc[2] == phase and pc[3] == "after":
            relevant_nodes = [node for node in row["nodes"] if decoder.decode(node["fields"]["path"]) == census["source_frame"]]
            matching_plans.append({"identity": row["identity"], "context": describe(pc),
                                   "registered_time": row["registered_time"], "state_identity": row["state_identity"],
                                   "matches_history_after_state": row["state_identity"] == current_state,
                                   "context_state_id_matches": row["context_state_id_matches"],
                                   "context_token_same_as_request": row["context_token_same_as_request"],
                                   "source_frame_is_target": census["source_frame"] in target_paths,
                                   "current_source_nodes": relevant_nodes,
                                   "cache_identity_matches_plan": row["cache_identity_matches_plan"]})
    checks.add("current phase has retained source-bound plan", bool(matching_plans)
               and all(row["matches_history_after_state"] and row["context_state_id_matches"] is True
                       and row["context_token_same_as_request"] is True for row in matching_plans))
    checks.add("captured source owner and context relationships agree", all(
               value is True for value in census["identity_relationships"].values()))
    matching_work = [row["carrier"] for row in decisions if row["identical_completed_arithmetic_excluding_claim"]]
    claim_only = [row["carrier"] for row in decisions if row.get("typed_claim_is_only_initial_predicate_blocker")]
    snippets = source_snippets(root, {
        "ontokin/reach_conformance.py": ["_same_recording_vector", "_recording_centered_comparison.reused",
                                        "_recording_centered_comparison.l1", "_Bounds.value", "_Bounds.op"],
        "ontokin/reach_reference.py": ["_recording_source_signature", "ReachReference._recording_centered_poses"],
        "ontokin/reach_reference_plan.py": ["_SourceBatch.__exit__"]})
    return {
        "checks": checks.report(),
        "observed": {"key": census["key"], "source_frame": census["source_frame"], "carrier_order": order,
                     "supplied_quaternion": describe(actual), "source_rotation_wxyz": describe(source_rotation),
                     "sign_selected_expected_xyzw": describe(expected), "orientation_radius": describe(radius),
                     "typed_rotation_claim": describe(limits[1]), "identity_relationships": census["identity_relationships"],
                     "batch_post_cleanup": census["batch_post_cleanup"], "source": census["source"]},
        "reconstructed": {"sign_choice": {"axis_index": axis, "negated_source_representative": negated},
                          "attempted_l1_addition": attempt,
                          "source_phase": {"index": phase, "side": "after", "time": describe(key["time"]),
                                           "interval_start": None if phase < 0 else describe(times[phase]),
                                           "interval_end": describe(times[phase + 1]) if phase + 1 < len(times) else None,
                                           "history_after_state_identity": current_state,
                                           "matching_plans_post_cleanup": matching_plans,
                                           "raw_process_ids_are_cross_run_identity": False},
                          "completed_proof_decisions": decisions,
                          "scalar_level_repetition": scalar_repetition},
        "finding": {"identical_completed_arithmetic_excluding_claim_carriers": matching_work,
                    "typed_claim_only_blocker_carriers": claim_only,
                    "completed_comparison_record_count": len(decisions),
                    "available_centered_orientation_proof_count": sum(row["first_mismatch"] != "unavailable_proof" for row in decisions),
                    "repeated_completed_nonzero_scalar_decode_count": len(scalar_repetition["repeated_completed_nonzero_decodes"]),
                    "no_repetition_is_a_valid_result": True,
                    "optimization_selected": False, "runtime_promoted": False,
                    "accepted_runtime": "d2f0088c4f3c1f570630334804a5a8f78e0105ac"},
        "source_bindings": snippets,
        "limitations": [
            "Completed reused() frames were not retained. Predicate decisions are offline source-order reconstructions from captured records.",
            "Proof candidates are the retained same-key result map only. No unavailable or evicted earlier history is inferred.",
            "Mutable batch, reference and plan observations describe post-cleanup state; detached immutable comparison operands retain their values.",
            "Typed actual-vector equality is the source rule; binary64 bit equality is reported separately and is not substituted for that rule.",
            "The final add was refused before its arithmetic, prospective guard and result. An offline sum does not mean the product completed it.",
            "A matching previous numerical bound does not authorize removing the current typed-claim predicate or bypassing fresh claim, callback, storage or domain checks.",
            "No failed request was resumed and no unvisited product tail, complete remaining cost, global hotspot or P11 success is inferred.",
            "The paired census establishes operation/path neutrality only, not elapsed neutrality or performance acceptance.",
            "The held candidate and 24/28 recording gate remain unchanged; all release obligations retain their separate status."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, control, capture, output = (getattr(args, name).resolve() for name in ("root", "control", "capture", "output"))
    if output.is_relative_to(root) or Path(__file__).resolve().is_relative_to(root):
        raise ValueError("Analysis driver and output must be outside the product checkout")
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "ontokin.checkpoint036-offline-analysis/0.1", "started_at": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]],
              "analyzer_sha256": digest(Path(__file__).read_bytes()),
              "source_commit": COMMIT, "source_tree": TREE, "ontokin_imported": False,
              "product_requests_executed": 0, "product_test_methods_executed": 0,
              "runtime_optimization_selected": False, "release_acceptance": False}
    try:
        neutral, inputs, request = neutrality(control, capture, root)
        report["neutrality"], report["inputs"] = neutral, inputs
        write_json(output / "neutrality.json", neutral)
        if not neutral["passed"]:
            report["status"] = "failed_neutrality_gate"
            report["census_analysis"] = {"executed": False, "reason": "Neutrality must pass before capture interpretation"}
        else:
            census, meta, raw = read_json(capture / "census.json")
            report["inputs"]["capture/census.json"] = meta
            if meta["sha256"] != request["census_sha256"]:
                raise ValueError("Census bytes do not match the closed request receipt")
            if not strict_equal(census["bounds"], request["native_capture_bounds"]):
                raise ValueError("Census bounds differ from predeclared request bounds")
            analysis = analyze_capture(census, request, root)
            report["census_analysis"] = analysis
            report["status"] = "passed" if analysis["checks"]["passed"] else "failed_census_consistency"
            write_json(output / "census-analysis.json", analysis)
        # Both gates describe read-only analysis of the frozen source. Recheck
        # source metadata and driver identity at closure; file bytes were bound
        # above against the complete recorded inventories.
        report["source_clean_at_end"] = (git(root, "rev-parse", "HEAD") == COMMIT
                                          and git(root, "rev-parse", "HEAD^{tree}") == TREE
                                          and git(root, "status", "--porcelain=v1", "--untracked-files=all") == "")
        report["analyzer_unchanged"] = digest(Path(__file__).read_bytes()) == report["analyzer_sha256"]
        if not report["source_clean_at_end"] or not report["analyzer_unchanged"]:
            report["status"] = "failed_changed_analysis_inputs"
    except Exception as error:
        report["status"] = "failed_analysis"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
        with (output / "analysis-error.txt").open("x") as stream:
            stream.write(traceback.format_exc())
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "report.json", report)
    print(json.dumps({"status": report["status"], "neutrality_passed": report.get("neutrality", {}).get("passed"),
                      "findings": report.get("census_analysis", {}).get("finding")}), flush=True)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
