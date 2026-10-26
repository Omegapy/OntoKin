"""Audit retained C033/C035 L03 facts without importing or running OntoKin.

This reads JSON, source text/ASTs and already restored evidence. It neither
replays numerical requests nor treats boundary snapshots as mutation events.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import sys


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def desc(path):
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha(path)}


def normsha(value):
    return value.removeprefix("sha256:")


def frames(request):
    result = []
    for file, function in re.findall(r'File "([^"]+)", line \d+, in ([^\n]+)', request["traceback"]):
        for folder in ("ontokin", "tools"):
            if "/" + folder + "/" in file:
                result.append((folder + "/" + file.split("/" + folder + "/", 1)[1], function.strip()))
                break
    return result


def key_id(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--c033", type=Path, required=True)
    parser.add_argument("--c035", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    repo, old, current = args.repo.resolve(), args.c033.resolve(), args.c035.resolve()
    records = repo / "docs/engineering/reach-recording-validation-2026-10-23"
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        if not condition:
            raise AssertionError(name)

    bindings = []
    archive_totals = []
    for number, restored in (("033", old), ("035", current)):
        manifest_path = records / f"checkpoint-{number}-manifest.json"
        checkpoint_path = records / f"checkpoint-{number}.json"
        checkpoint, manifest = read(checkpoint_path), read(manifest_path)
        check(f"C{number} manifest identity", sha(manifest_path) == checkpoint["manifest_sha256"])
        expected = {row["path"]: row for row in manifest["members"]}
        check(f"C{number} unique manifest members", len(expected) == len(manifest["members"]))
        actual = {str(p.relative_to(restored)) for p in restored.rglob("*") if p.is_file()}
        check(f"C{number} exact restored membership", actual == set(expected))
        check(f"C{number} every restored member", all(
            (restored / name).stat().st_size == row["bytes"] and sha(restored / name) == row["sha256"]
            and not (restored / name).is_symlink() for name, row in expected.items()))
        bindings.extend((desc(manifest_path), desc(checkpoint_path)))
        archive_totals.append({"checkpoint": int(number), "members": len(expected),
                               "member_bytes": sum(row["bytes"] for row in expected.values())})

    ledger_path = old / "capture-l03-001/key-ledger.json"
    failure_path = old / "capture-l03-001/failure-locals.json"
    capture_path = old / "capture-l03-001/capture.json"
    ledger, failure, capture = read(ledger_path), read(failure_path), read(capture_path)
    rows = ledger["keys"]
    check("historical complete retained key prefix", len(rows) == 154 and
          [row["index"] for row in rows] == list(range(154)))
    check("historical returned/failed boundaries", all(row["outcome"] == "returned" for row in rows[:-1])
          and rows[-1]["outcome"] == "raised")
    check("historical identity receipts", all(all(row["identity_checks"].values()) for row in rows)
          and all(capture["identity_checks"].values()) and capture["observation_errors"] == [])
    check("historical native callback shape", capture["callbacks"]["construction_check"] is None
          and capture["callbacks"]["observer_at_reader_entry"] is None
          and capture["callbacks"]["observer_after_request"] is None
          and capture["callbacks"]["external"]["qualname"] == "ConstructionBudget.tick")
    states = [row[boundary] for row in rows for boundary in ("entry", "exit")]
    check("all source-cache category sums", all(sum(s["source_cache_categories"].values()) ==
          s["source_cache_entries"] for s in states))
    check("all adjacent boundary snapshots", all(
        rows[i]["exit"][name] == rows[i+1]["entry"][name]
        for i in range(len(rows)-1)
        for name in ("source_cache_entries", "source_cache_categories", "source_cursors")))
    sizes = [s["source_cache_entries"] for s in states]
    check("historical observed reader-cache range", min(sizes) == 112 and max(sizes) == 165)
    check("distinct shared-work cache", all(s["reach"]["cache_entries"] == 256 for s in states))
    check("no observed boundary cardinality decrease", all(b >= a for a, b in zip(sizes, sizes[1:])))

    seeds, advances, category_changes = [], [], []
    for row in rows:
        entry = {key_id(item["key"]): item for item in row["entry"]["source_cursors"]}
        for item in row["exit"]["source_cursors"]:
            previous = entry.get(key_id(item["key"]))
            value = item["value"]
            if previous is not None and previous["value"] == value:
                continue
            event = {"key_index": row["index"], "time": row["time"],
                     "cursor_key": item["key"], "clock": value["clock"], "steps": value["steps"],
                     "previous_steps": previous["value"]["steps"] if previous else None,
                     "previous_clock": previous["value"]["clock"] if previous else None}
            if value["steps"] == 0:
                seeds.append(event)
            else:
                check(f"cursor advance at {row['index']} {len(advances)}", previous is not None and
                      value["steps"] == previous["value"]["steps"] + 1)
                advances.append(event)
        before = row["entry"]["source_cache_categories"].get("series_coefficients", 0)
        after = row["exit"]["source_cache_categories"].get("series_coefficients", 0)
        if before != after:
            category_changes.append({"key_index": row["index"], "entry": before, "exit": after})
    check("six published step-zero seeds", [e["key_index"] for e in seeds] == [1, 1, 66, 66, 88, 88])
    check("296 published cursor advances", len(advances) == 296)
    check("two published 64-step replacements", sum(e["previous_steps"] == 64 for e in seeds) == 2)
    check("three coefficient occupancy increases", category_changes == [
        {"key_index": 1, "entry": 7, "exit": 9}, {"key_index": 66, "entry": 9, "exit": 11},
        {"key_index": 88, "entry": 11, "exit": 12}])
    frame_names = [frame["function"] for frame in failure["frames"]]
    check("selected historical failure frames unique", len(frame_names) == len(set(frame_names)))
    locals_ = {frame["function"]: frame["locals"] for frame in failure["frames"]}
    orient, coeff, integer = (locals_[name] for name in ("_orientation", "_series_coefficients", "_series_integer"))
    check("historical failure key and time", locals_["_key_comparisons"]["index"] == 153 and
          locals_["_key_comparisons"]["time"] == {"numerator": "244", "denominator": "89"})
    check("historical prior cursor64", orient["previous"]["steps"] == 64 and orient["advance"] is False)
    check("historical coefficient locals", (coeff["exponent"], coeff["degree"], coeff["index"], coeff["odd"]) ==
          (129, 14, 7, 15) and integer["kind"] == "div" and integer["a"] == 8841761993739701954543616000000
          and integer["b"] == 1307674368000)
    pending_cursors = [item for item in locals_["evaluate"]["pending_values"]
                       if item["value"].get("type") == "_CenteredCursor"]
    check("historical one pending completed reseed", len(pending_cursors) == 1 and
          pending_cursors[0]["value"]["steps"] == 0 and pending_cursors[0]["previous"]["steps"] == 64)
    check("failed key publishes no cursor", rows[-1]["entry"]["source_cursors"] == rows[-1]["exit"]["source_cursors"])

    paths = [old / "stock-l03-001/L03/request-result.json", old / "capture-l03-001/stock/L03/request-result.json",
             current / "execution/complete-p11-l03-002/L03/request-result.json",
             current / "execution/original28-002/L03/request-result.json"]
    requests = [read(path) for path in paths]
    equal_fields = ("case_id", "status", "source_files", "program_revision", "options", "max_operations",
                    "source_manifest", "failure", "diagnostic", "operations", "work")
    for field in equal_fields:
        check("all four request fields: " + field, all(item[field] == requests[0][field] for item in requests[1:]))
    check("all four capped totals", all(item["status"] == "failed" and item["operations"] == 100001
          and item["work"]["operations"] == 95767 and len(item["work"]["counts"]) == 288
          and sum(item["work"]["counts"].values()) == 95767 for item in requests))
    check("same underlying27-frame route", len(frames(requests[0])) == 27 and
          all(frames(item) == frames(requests[0]) for item in requests[1:]))
    for directory in ("complete-p11-l03-002", "original28-002"):
        report = read(current / "execution" / directory / "report.json")
        check("current source identity " + directory, report["source_commit"] ==
              "4ca73909f861fe4bef9694787473621c1d21c140" and report["source_tree"] ==
              "87c949b238055af1ce368c694e1d5683c8aeacde" and report["inputs_stable"])
    old_inputs = read(old / "stock-l03-001/inputs-before.json")
    new_inputs = read(current / "execution/complete-p11-l03-002/inputs-before.json")
    old_files = {f["path"]: f for f in old_inputs["files"]}
    new_files = {f["path"]: f for f in new_inputs["files"]}
    runtime = [path for path in new_files if path.startswith("ontokin/") and path.endswith(".py")]
    check("65 current runtime modules", len(runtime) == 65)
    check("current runtime equals held C035", all((repo / path).stat().st_size == new_files[path]["bytes"]
          and sha(repo / path) == normsha(new_files[path]["sha256"]) for path in runtime))
    changed = [path for path in runtime if normsha(old_files[path]["sha256"]) != normsha(new_files[path]["sha256"])]
    check("two historical runtime file changes", sorted(changed) ==
          ["ontokin/reach_reference.py", "ontokin/reach_reference_center.py"])
    check("original request builder unchanged", normsha(old_files["tools/build_reach_source_artifacts.py"]["sha256"]) ==
          normsha(new_files["tools/build_reach_source_artifacts.py"]["sha256"]) ==
          sha(repo / "tools/build_reach_source_artifacts.py"))
    capture_source = records / "checkpoint-046-capture.py"
    tree = ast.parse(capture_source.read_text())
    check("prepared capture parses without import", isinstance(tree, ast.Module))
    forbidden = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and
                 isinstance(node.func, ast.Attribute) and node.func.attr in ("settrace", "setprofile", "set_events", "set_local_events")]
    check("prepared capture installs no trace/profile/monitor", not forbidden)
    bindings.extend(desc(path) for path in [ledger_path, failure_path, capture_path, *paths, capture_source])
    result = {"schema": "ontokin.checkpoint046-source-data-audit/0.1", "status": "passed",
              "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
              "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
              "checks_passed": len(checks), "checks_failed": 0, "checks": checks,
              "restored_archives": archive_totals, "input_bindings": bindings,
              "historical_published_seeds": seeds, "historical_published_advances": len(advances),
              "historical_pending_cursors": pending_cursors, "historical_reader_cache_range": [min(sizes), max(sizes)],
              "coefficient_category_boundary_changes": category_changes,
              "historical_coefficient_key_source_derived": ["series_coefficients", 32768, 129, 14],
              "current_failure_route": frames(requests[2]), "current_runtime_changes_from_C033": changed,
              "current_key_clock_cursor_and_coefficient_locals": None,
              "exact_lookup_publication_eviction_event_census": None,
              "source_inference_note": "The reviewed source binds both current traces to a completed lookup miss and a coefficient-construction division refusal; current local values are not retained.",
              "boundary_note": "Snapshots and their changes are not exact intra-key cache mutation events. Any historical no-eviction theorem requires the separate source/authority proof.",
              "product_requests": 0, "candidate_numerical_replay": False,
              "prepared_capture_executed": False, "release_acceptance": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "passed", "checks": len(checks), "members_verified": sum(x["members"] for x in archive_totals),
                      "product_requests": 0, "prepared_capture_executed": False}))


if __name__ == "__main__":
    main()
