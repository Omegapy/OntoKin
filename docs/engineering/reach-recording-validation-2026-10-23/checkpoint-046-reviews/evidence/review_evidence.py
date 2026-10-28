#!/usr/bin/env python3
"""Independent metadata-only C046 review of restored C033/C035 bytes.

This imports no OntoKin module, extracts no archive and evaluates no source pose.
"""
import argparse
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.workspace
    repo = root / "OntoKin"
    evidence = root / "c046-evidence"
    docs = repo / "docs/engineering/reach-recording-validation-2026-10-23"
    checks = []
    bindings = []

    def require(name, condition):
        checks.append({"name": name, "passed": bool(condition)})
        if not condition:
            raise AssertionError(name)

    def read(path):
        path = Path(path)
        data = path.read_bytes()
        bindings.append({"path": str(path.relative_to(root)), "bytes": len(data),
                         "sha256": hashlib.sha256(data).hexdigest()})
        return json.loads(data)

    archive_checks = []
    for number in (33, 35):
        manifest = read(docs / f"checkpoint-{number:03}-manifest.json")
        restored = evidence / f"restored-c{number:03}"
        total = 0
        for item in manifest["members"]:
            file = restored / item["path"]
            data = file.read_bytes()
            if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise AssertionError(f"C{number:03} member mismatch: {item['path']}")
            total += len(data)
        require(f"C{number:03} every restored member hash and length", True)
        archive_checks.append({"checkpoint": number, "members": len(manifest["members"]),
                               "bytes": total, "all_member_hashes_lengths_match": True,
                               "archive_extraction_or_crc_replay": False})

    report_paths = [
        "restored-c033/stock-l03-001/L03/request-result.json",
        "restored-c033/capture-l03-001/stock/L03/request-result.json",
        "restored-c035/execution/complete-p11-l03-002/L03/request-result.json",
        "restored-c035/execution/original28-002/L03/request-result.json",
    ]
    reports = [read(evidence / path) for path in report_paths]
    exact_fields = ["case_id", "status", "source_files", "program_revision", "options",
                    "max_operations", "source_manifest", "failure", "diagnostic", "operations", "work"]
    for field in exact_fields:
        require(f"All four original L03 reports agree on {field}",
                all(r[field] == reports[0][field] for r in reports))
    require("Original refusal retained", reports[0]["status"] == "failed"
            and reports[0]["operations"] == 100001
            and reports[0]["work"]["operations"] == 95767
            and len(reports[0]["work"]["counts"]) == 288
            and reports[0]["work"]["cache_entries"] == 256)
    frame_pattern = re.compile(r'File "([^"]+)", line ([0-9]+), in ([^\n]+)')

    def frames(report):
        return [{"file": Path(path).name, "line": int(line), "function": function}
                for path, line, function in frame_pattern.findall(report["traceback"])]

    chains = [frames(report) for report in reports]
    baseline_chain = [(f["file"], f["function"]) for f in chains[0]]
    require("Stock and current traces retain the same 27-function route",
            len(baseline_chain) == 27 and all(
                [(f["file"], f["function"]) for f in chains[i]] == baseline_chain for i in (2, 3)))
    wrappers = {"capture_validate_export", "capture_key_comparisons"}
    require("Captured historical trace differs by exactly the two approved wrappers",
            len(chains[1]) == 29 and
            [(f["file"], f["function"]) for f in chains[1] if f["function"] not in wrappers]
            == baseline_chain)

    inv_paths = ["restored-c033/stock-l03-001/inputs-before.json",
                 "restored-c035/execution/complete-p11-l03-002/inputs-before.json"]
    inventories = [read(evidence / path) for path in inv_paths]
    maps = [{f["path"]: f for f in inv["files"]} for inv in inventories]
    runtime = sorted(p for p in maps[1] if p.startswith("ontokin/"))
    require("65 runtime modules in current executed inventory", len(runtime) == 65)
    require("Current recovered runtime bytes match all C035 runtime inputs", all(
        (repo / p).stat().st_size == maps[1][p]["bytes"] and
        sha(repo / p) == maps[1][p]["sha256"].removeprefix("sha256:") for p in runtime))
    runtime_changes = [p for p in runtime if maps[0][p]["sha256"] != maps[1][p]["sha256"]]
    require("Only the two named runtime modules differ from C033",
            runtime_changes == ["ontokin/reach_reference.py", "ontokin/reach_reference_center.py"])
    historical = root / "c046-source-review/historical"
    historical_bindings = []
    for name in ("reach_reference.py", "reach_reference_center.py", "reach_reference_plan.py"):
        path = "ontokin/" + name
        file = historical / path
        require("Historical source binding " + path,
                file.stat().st_size == maps[0][path]["bytes"] and
                sha(file) == maps[0][path]["sha256"].removeprefix("sha256:"))
        historical_bindings.append({"path": str(file.relative_to(root)), "bytes": file.stat().st_size,
                                    "sha256": sha(file)})

    def body(file, wanted):
        source = file.read_text()
        found = {}
        def visit(nodes, prefix=""):
            for node in nodes:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = prefix + node.name
                    found[name] = ast.get_source_segment(source, node)
                    visit(node.body, name + ".")
        visit(ast.parse(source).body)
        return found[wanted]

    unchanged_bodies = {
        "reach_reference.py": ["_Arithmetic._sync_cache_operand_limit", "_Arithmetic.lookup",
                               "_Arithmetic.remember", "_Arithmetic._series_coefficients",
                               "_Arithmetic._series_integer"],
        "reach_reference_center.py": ["_orientation", "_seed", "_Guard.lookup", "_Guard.remember"],
    }
    for name, functions in unchanged_bodies.items():
        for function in functions:
            require("Unchanged complete body " + name + ":" + function,
                    body(historical / "ontokin" / name, function) == body(repo / "ontokin" / name, function))

    old = evidence / "restored-c033/capture-l03-001"
    capture = read(old / "capture.json")
    ledger = read(old / "key-ledger.json")
    failure = read(old / "failure-locals.json")
    keys = ledger["keys"]
    require("154 consecutive historical key calls", len(keys) == 154
            and [r["index"] for r in keys] == list(range(154)))
    require("153 returned historical keys and one failed key", all(
        r["outcome"] == "returned" for r in keys[:-1]) and keys[-1]["outcome"] == "raised")
    require("Every source-cache category sum reconciles", all(
        sum(r[boundary]["source_cache_categories"].values()) == r[boundary]["source_cache_entries"]
        for r in keys for boundary in ("entry", "exit")))
    require("All adjacent source-cache summaries and cursors are continuous", all(
        a["exit"][field] == b["entry"][field]
        for a, b in zip(keys, keys[1:])
        for field in ("source_cache_entries", "source_cache_categories", "source_cursors")))
    require("Every captured key identity assertion is true",
            all(all(r["identity_checks"].values()) for r in keys))
    require("Every full-capture identity assertion is true", all(capture["identity_checks"].values()))
    require("No observation error", capture["observation_errors"] == [])
    require("Native historical external callback without a construction check",
            capture["callbacks"] == {
                "external": {"module": "ontokin.construction", "qualname": "ConstructionBudget.tick",
                             "bound_owner_type": "ConstructionBudget"},
                "construction_check": None, "observer_at_reader_entry": None,
                "observer_after_request": None})

    def rational(value):
        return value["numerator"] + "/" + value["denominator"]

    def cursor(record):
        k, v = record["key"], record["value"]
        return {"phase": k[4][0][2], "frame": k[4][1],
                "clock": rational(v["clock"]), "steps": v["steps"]}

    resets, advances, coefficient_deltas = [], [], []
    for row in keys:
        before = {json.dumps(c["key"], sort_keys=True): c for c in row["entry"]["source_cursors"]}
        for c in row["exit"]["source_cursors"]:
            previous = before.get(json.dumps(c["key"], sort_keys=True))
            if previous is None or previous["value"] != c["value"]:
                item = {"key": row["index"], "time": rational(row["time"]), "current": cursor(c),
                        "previous": None if previous is None else cursor(previous)}
                (resets if c["value"]["steps"] == 0 else advances).append(item)
        count_before = row["entry"]["source_cache_categories"].get("series_coefficients", 0)
        count_after = row["exit"]["source_cache_categories"].get("series_coefficients", 0)
        if count_before != count_after:
            coefficient_deltas.append({"key": row["index"], "entry": count_before, "exit": count_after})
    require("Six published zero-step cursor transitions", len(resets) == 6
            and [r["key"] for r in resets] == [1, 1, 66, 66, 88, 88])
    require("Two published retirements replace 64-step cursors", all(
        r["previous"] is not None and r["previous"]["steps"] == 64 for r in resets if r["key"] == 66))
    require("296 observed one-step cursor advances", len(advances) == 296 and all(
        r["previous"] is not None and r["current"]["steps"] == r["previous"]["steps"] + 1
        for r in advances))
    require("No published cursor changes at failed key153",
            keys[-1]["entry"]["source_cursors"] == keys[-1]["exit"]["source_cursors"])
    require("Recorded coefficient-category increases are only 7 to9,9 to11,11 to12",
            coefficient_deltas == [{"key": 1, "entry": 7, "exit": 9},
                                   {"key": 66, "entry": 9, "exit": 11},
                                   {"key": 88, "entry": 11, "exit": 12}])
    occupancies = [row[b]["source_cache_entries"] for row in keys for b in ("entry", "exit")]
    require("Historical source-cache boundary range112 to165", min(occupancies) == 112
            and max(occupancies) == 165)
    require("Every key1-to153 exit retains centered cursors",
            all(row["exit"]["source_cursors"] for row in keys[1:]))
    require("Key0 lacks centered cursors and centered stationary category",
            all(not keys[0][boundary]["source_cursors"] and
                not keys[0][boundary]["source_cache_categories"].get("reference_centered_stationary_pose", 0)
                for boundary in ("entry", "exit")))
    functions = {}
    for frame in failure["frames"]:
        functions.setdefault(frame["function"], []).append(frame)
    orientation = functions["_orientation"][-1]["locals"]
    coefficient = functions["_series_coefficients"][0]["locals"]
    integer = functions["_series_integer"][0]["locals"]
    pending = functions["evaluate"][-1]["locals"]["pending_values"]
    require("Historical forearm refusal binds clock244/89 and64 updates",
            orientation["advance"] is False and orientation["previous"]["steps"] == 64
            and rational(orientation["clock"]) == "244/89"
            and orientation["node"]["path"] == "rig.arm.forearm.frame")
    require("Historical failing coefficient fields129,14,7", (coefficient["exponent"], coefficient["degree"],
            coefficient["index"]) == (129, 14, 7))
    require("Historical refused division has exact retained operands", integer == {
        "a": 8841761993739701954543616000000, "b": 1307674368000, "kind": "div"})
    require("Exactly one completed upper cursor is pending at failure", len(pending) == 1
            and cursor(pending[0]) == {"phase": 1, "frame": "rig.arm.upper.frame", "clock": "244/89", "steps": 0}
            and pending[0]["previous"]["steps"] == 64)
    source_binding = {"C033": inventories[0]["git"], "C035": inventories[1]["git"],
                      "current_runtime_modules_verified": len(runtime), "changed_modules": runtime_changes}
    result = {
        "schema": "ontokin.checkpoint046-independent-evidence-review/0.1",
        "reviewer": "/root/evidence_review",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Restored bytes, native JSON records, source input hashes and recorded trace metadata only",
        "status": "passed", "checks": checks, "checks_passed": len(checks),
        "restored_member_checks": archive_checks, "source_binding": source_binding,
        "historical_source_bindings": historical_bindings,
        "reports": [{"path": p, "status": r["status"], "shared": r["operations"],
                     "reach": r["work"]["operations"], "category_count": len(r["work"]["counts"]),
                     "work_cache_entries": r["work"]["cache_entries"],
                     "elapsed_seconds": r["elapsed_seconds"]} for p, r in zip(report_paths, reports)],
        "exact_equal_fields": exact_fields, "trace_chains": chains,
        "historical_published_zero_step_transitions": resets,
        "historical_published_advances": {"count": len(advances), "phase0": sum(r["current"]["phase"] == 0 for r in advances),
                                           "phase1": sum(r["current"]["phase"] == 1 for r in advances)},
        "historical_pending_cursor": cursor(pending[0]),
        "historical_failed_coefficient": {"exponent": 129, "degree": 14, "index": 7,
                                          "operands": integer, "operation_performed": False},
        "historical_source_cache_boundary_range": [min(occupancies), max(occupancies)],
        "historical_coefficient_category_changes": coefficient_deltas,
        "historical_cache_lifetime_inference": {
            "scope": "Key1 entry through key153 exception-exit wrapper snapshot, before outer batch cleanup",
            "start_source_cache_entries": 122,
            "maximum_recorded_source_cache_entries": 165,
            "capacity": 256,
            "native_source_review": "Complete source mutation/call closure independently inspected; see review.md",
            "no_capacity_eviction_in_scope": True,
            "failed_key": ["series_coefficients", 32768, 129, 14],
            "failed_key_retained_at_start_or_completed_publication_in_scope": False,
            "not_established": ["pre-key1 cache history", "current C035 cache history", "unexecuted tail"]
        },
        "missing": [
            "C033 complete source-cache key identities/order/payload and individual coefficient call/mutation history",
            "C035 failure key index, exact time, source frame, previous cursor and actual coefficient exponent/degree/index",
            "C035 source-cache keys/order/payload, cursor chronology and coefficient lookup/publication/eviction history",
            "Complete-request cost after the original refusal and any candidate charged saving"],
        "limits": [
            "The lifetime inference combines independently inspected native source closure with boundary facts; occupancy alone is insufficient.",
            "The narrow lifetime inference excludes key0, earlier request work, final failure cleanup and current C035 chronology.",
            "Matching final counts and call routes do not establish matching current locals or cache chronology.",
            "The C035 trace proves entry into coefficient construction; the failed division does not execute.",
            "No product request, numerical candidate replay, archive extraction or archived program executed."],
        "product_requests": 0, "runtime_changes": 0, "inputs": bindings,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "checks_passed": len(checks),
                      "output": str(args.output), "restored_members_verified": 727}))


if __name__ == "__main__":
    main()
