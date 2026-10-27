"""Read retained JSON/text only; never import or execute OntoKin or archive code."""
from pathlib import Path
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
RESTORED = ROOT / "c047-restored"
CAPTURE = RESTORED / "c047-execution/capture-001"
OUT = Path(__file__).resolve().parent
started = datetime.now(timezone.utc).isoformat()
inputs = {}
checks = []


def read(path):
    path = Path(path)
    data = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = {
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
    }
    return data


def load(path):
    return json.loads(read(path))


def check(name, condition):
    checks.append({"name": name, "passed": bool(condition)})


read(__file__)
manifest = load(ROOT / "source/docs/engineering/reach-recording-validation-2026-10-23/checkpoint-047-evidence-manifest.json")
members = {row["path"]: row for row in manifest["members"]}
capture = load(CAPTURE / "capture.json")
ledger = load(CAPTURE / "key-ledger.json")
failure = load(CAPTURE / "failure-locals.json")
comparison = load(RESTORED / "c047-independent-comparison/result.json")
comparison_command = load(RESTORED / "c047-independent-comparison/command.json")
census = load(RESTORED / "c047-lifetime-review/census-001/coefficient-census.json")
census_result = load(RESTORED / "c047-lifetime-review/census-001/result.json")
read(RESTORED / "c047-lifetime-review/review.md")
bindings = load(RESTORED / "c047-lifetime-review/census-001/source-bindings.json")
source = read(ROOT / "source/ontokin/reach_reference.py")
binding = next(x for x in bindings if x["path"] == "ontokin/reach_reference.py")
blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
current_tree = json.loads(load(ROOT / "acquisition/tree.json")["structuredContent"]["content"])
original_tree = load(RESTORED / "c047-recovery/remote-tree.json")
check("exact current source matches original source binding", len(source) == binding["bytes"] and hashlib.sha256(source).hexdigest() == binding["sha256"] and blob == binding["git_blob"])
check("source blob agrees with current and original recorded Git trees", all(next(x for x in tree["tree"] if x["path"] == binding["path"])["sha"] == blob for tree in (current_tree, original_tree)))
lines = source.splitlines(keepends=True)
check("all nine source symbol byte ranges match original binding", len(binding["symbols"]) == 9 and all(hashlib.sha256(b"".join(lines[x["start"] - 1:x["end"]])).hexdigest() == x["sha256"] for x in binding["symbols"]))
check("stored independent comparison is passed with 61593 recorded checks", comparison["status"] == "passed" and comparison["checks_passed"] == len(comparison["checks"]) == 61593 and all(x["passed"] is True for x in comparison["checks"]))
check("stored comparison command exited zero with stable inputs", comparison_command["exit_code"] == 0 and comparison_command["inputs_stable"] is True and comparison_command["product_code_imported_or_executed"] is False)
check("source identities agree across retained records", all(x["source_commit"] == "48b5d381a0f86d9706a109b78e2ce52eb0d287f0" and x["source_tree"] == "33ac0caa77528432d18132a1e606d1e4fbd7ab80" for x in (capture, comparison, census_result, manifest)))
check("capture is explicitly failed boundary-only evidence", capture["product_request_status"] == "failed" and capture["accepted_artifact"] is False and capture["boundary_only"] is True and capture["intra_key_lookup_publication_eviction_events"] is None and capture["observation_errors"] == [])
check("all 18 outer identity assertions are true", len(capture["identity_checks"]) == 18 and all(x is True for x in capture["identity_checks"].values()))
check("raw callback metadata is native and endpoint work observers are absent", capture["callbacks"] == {"external": {"module": "ontokin.construction", "qualname": "ConstructionBudget.tick", "bound_owner_type": "ConstructionBudget"}, "construction_check": None, "observer_at_reader_entry": None, "observer_after_request": None})
check("original operation time bit and cache limits are retained", capture["budget_limits"]["max_operations"] == 100000 and capture["budget_limits"]["max_elapsed_ms"] == 30000 and capture["work_limits"] == {"max_operations": 100000, "max_elapsed_ms": 30000, "max_operand_bits": 32768, "max_cache_entries": 256})

keys = ledger["keys"]
check("154 consecutive keys retain original outcomes", [x["index"] for x in keys] == list(range(154)) and all(x["outcome"] == "returned" for x in keys[:-1]) and keys[-1]["outcome"] == "raised")
check("all 154 groups of 12 per-key identity assertions are true", all(len(x["identity_checks"]) == 12 and all(v is True for v in x["identity_checks"].values()) for x in keys))
snapshots = {}
snapshot_bytes = 0
descriptor_ok = True
domain_ok = True
shape_ok = True
failed_key = ("series_coefficients", 32768, 129, 14)
failed_occurrences = 0
snapshot_descriptors = capture["ordered_cache_snapshot_files"]
for descriptor in snapshot_descriptors:
    data = read(CAPTURE / descriptor["path"])
    descriptor_ok &= len(data) == descriptor["bytes"] and hashlib.sha256(data).hexdigest() == descriptor["sha256"] and descriptor["status"] == "written"
    snapshot_bytes += len(data)
    snap = json.loads(data)
    rows = snap["ordered_rows"]
    domain_ok &= snap["source_domain"] == {"bits": 128, "scale": 340282366920938463463374607431768211456, "_cache_operand_limit": 32768} and snap["work_operand_limit"] == 32768
    shape_ok &= [x["ordinal"] for x in rows] == list(range(len(rows)))
    for row in rows:
        key = row["key"]
        if key and key[0] == "series_coefficients":
            shape_ok &= len(key) == 4 and key[1] == 32768 and all(type(x) is int for x in key[1:]) and row["series_value"]["native_immutable_integer_tuple_shape"] is True
            failed_occurrences += tuple(key) == failed_key
    snapshots[descriptor["path"]] = snap
check("311 unique snapshots have exact descriptor bytes and hashes", len(snapshots) == len(snapshot_descriptors) == 311 and snapshot_bytes == 122526082 and descriptor_ok)
check("snapshot directory has precisely the declared membership", {x.name for x in (CAPTURE / "ordered-cache-boundaries").glob("*.json")} == {Path(x).name for x in snapshots})
check("all snapshot domains and coefficient key shapes agree", domain_ok and shape_ok)
check("failed coefficient key absent from all 311 snapshots", failed_occurrences == 0)

derived = {}
occupancy = []
losses = []
last_keys = set()
ledger_agrees = True
for row in keys:
    for side in ("entry", "exit"):
        ref = row[side]["source_cache_ordered_snapshot_file"]
        snap = snapshots[ref["path"]]
        series = {tuple(x["key"]) for x in snap["ordered_rows"] if x["key"] and x["key"][0] == "series_coefficients"}
        occupancy.append(len(snap["ordered_rows"]))
        ledger_agrees &= row[side]["source_cache_entries"] == occupancy[-1] and row[side]["source_cache_categories"]["series_coefficients"] == len(series)
        if last_keys - series:
            losses.append({"index": row["index"], "side": side, "keys": sorted(last_keys - series)})
        last_keys = series
        for key in series:
            if key not in derived:
                derived[key] = {"key": list(key), "first_boundary": {"index": row["index"], "side": side}, "boundary_observations": 0}
            derived[key]["boundary_observations"] += 1
            derived[key]["last_boundary"] = {"index": row["index"], "side": side}
check("raw 308 boundary census exactly matches stored census", sorted(derived.values(), key=lambda x:x["key"]) == sorted(census, key=lambda x:x["key"]))
check("ledger occupancy and coefficient counts agree with raw snapshots", ledger_agrees)
expected = {(50,17):(0,"entry"), (52,16):(0,"entry"), (53,13):(0,"entry"), (127,16):(0,"entry"), (128,2):(0,"entry"), (128,13):(0,"entry"), (128,16):(0,"entry"), (129,7):(1,"exit"), (129,8):(1,"exit"), (129,13):(66,"exit"), (129,17):(66,"exit"), (129,16):(88,"exit")}
actual = {key[2:]:(value["first_boundary"]["index"], value["first_boundary"]["side"]) for key,value in derived.items()}
check("all twelve exact keys have the stated first boundary", actual == expected)
check("boundary occupancy ranges 112 through 165 without decrease or fullness", occupancy[0] == 112 and occupancy[-1] == 165 and min(occupancy) == 112 and max(occupancy) == 165 and all(a <= b for a,b in zip(occupancy, occupancy[1:])))
check("no coefficient disappears between recorded boundaries", losses == [])
frames = {row["function"]: row for row in failure["frames"]}
co = frames["_series_coefficients"]["locals"]
integer = frames["_series_integer"]["locals"]
orientation = frames["_orientation"]["locals"]
check("raw coefficient miss is degree14 exponent129 index7 before division", co["key"] == list(failed_key) and co["cached"] is None and co["degree"] == 14 and co["exponent"] == 129 and co["index"] == 7 and co["odd"] == 15 and len(co["coefficients"]) == 7 and integer["kind"] == "div" and integer["a"] == co["common"] and integer["b"] == co["factorials"][15])
check("traceback points to leading tick before division", frames["_series_integer"]["line"] == 437 and lines[436].strip() == b"self.tick()" and failure["exception_graph"][0]["message"] == "Construction exceeded max_operations.")
check("failed key and required retirement facts agree", keys[-1]["time"] == {"numerator":"244","denominator":"89"} and orientation["node"]["path"] == "rig.arm.forearm.frame" and orientation["previous"]["steps"] == 64 and orientation["advance"] is False and orientation["old_clock"] == {"numerator":"243","denominator":"89"})
check("failed key leaves published cursor lists unchanged", keys[-1]["entry"]["source_cursors"] == keys[-1]["exit"]["source_cursors"])
check("three failure snapshots equal the final boundary bytes", all(next(x for x in snapshot_descriptors if x["path"] == frames[name]["locals"]["source_cache_ordered_snapshot_file"]["path"])["sha256"] == keys[-1]["exit"]["source_cache_ordered_snapshot_file"]["sha256"] for name in ("_series_dyadic","_series_coefficients","_series_integer")))
check("failure locals do not record internal source observer values", all(not any("observer" in name for name in row["locals"]) for row in failure["frames"]))
check("captured refusal counts remain unchanged", capture["shared_operations_after_request"] == 100001 and capture["work_after_request"]["operations"] == 95767 and len(capture["work_after_request"]["counts"]) == 288)
retained = {path: record for path, record in inputs.items() if path.startswith("c047-restored/")}
check("every consumed retained file matches the published member manifest", all(record["bytes"] == members[path.removeprefix("c047-restored/")]["bytes"] and record["sha256"] == members[path.removeprefix("c047-restored/")]["sha256"] for path, record in retained.items()))
check("all consumed input bytes remain stable", all((ROOT/path).stat().st_size == record["bytes"] and hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == record["sha256"] for path,record in inputs.items()))

result = {
    "schema": "ontokin.c048-independent-retained-data-review/0.1",
    "status": "passed" if all(x["passed"] for x in checks) else "failed",
    "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
    "command": [sys.executable, str(Path(__file__).resolve())],
    "python": sys.version, "platform": platform.platform(),
    "reviewer": "/root/bundle_audit",
    "prior_role": "Earlier in C048 this reviewer checked the uploaded portable bundle against its local hash manifest. It did not acquire the C047 archive, author the proposed coefficient simplification, or execute the C047 product pair.",
    "scope": "Fresh pure JSON/text/hash checks of retained C047 evidence and the relevant source. No product import, product execution, numerical candidate replay, archived-code execution, archive operation, or GitHub mutation.",
    "source_commit": capture["source_commit"], "source_tree": capture["source_tree"],
    "publication_tree_observed_in_root_acquisition": current_tree["sha"],
    "grouped_metadata_checks_passed": sum(x["passed"] for x in checks),
    "grouped_metadata_checks_total": len(checks), "checks": checks,
    "input_count": len(inputs), "retained_files_checked_against_manifest": len(retained), "inputs": inputs,
    "snapshot_count": len(snapshots), "snapshot_bytes": snapshot_bytes,
    "coefficient_census": sorted(derived.values(), key=lambda x:x["key"]),
    "failed_key_snapshot_occurrences": failed_occurrences,
    "failure": {"key_index":153,"clock":"244/89","coefficient_index":co["index"],"cached":co["cached"],"integer_operation":integer["kind"],"division_executed":False},
    "authority_limits": ["Outer observer metadata and per-key restoration checks are boundary observations; they do not prove source observers absent inside coefficient construction.","Failure locals do not record either source observer value.","The no-eviction conclusion additionally relies on C047's source-bound mutation/control-flow proof; occupancy snapshots alone are insufficient."],
    "optimization_evidence": {"candidate_executed":False,"verified_operation_saving":None,"full_request_saving":None,"successful_failed_tail_cost":None,"positive_net_bound_established_by_this_review":False},
    "interpretation": "Twelve resident keys are a boundary census, not an intra-key event trace. Numerical payload equality, exact hit counts, publication order, seed attribution, and generic callback authority cannot be inferred from it. The two-operation endpoint ceiling is a source proposal, not a measured or admitted saving.",
}
(OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status":result["status"],"grouped_metadata_checks_passed":result["grouped_metadata_checks_passed"],"grouped_metadata_checks_total":len(checks),"input_count":len(inputs),"retained_files_checked_against_manifest":len(retained),"snapshot_count":len(snapshots),"snapshot_bytes":snapshot_bytes,"failed_checks":[x["name"] for x in checks if not x["passed"]]},indent=2))
raise SystemExit(0 if result["status"] == "passed" else 1)
