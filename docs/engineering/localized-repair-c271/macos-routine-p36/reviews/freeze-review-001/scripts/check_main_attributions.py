"""Recompute main-derived attribution statements from main's retained baseline runs, and check TR2-03/TR2-04 (read only).

Usage: python3 -I -S -B check_main_attributions.py COLLECTOR R1_ATTR R2_ATTR CHECKS_DIR DISCOVERY OUT.json FREEZE
The two runs' temporary directories are read from the freeze's places (<tmp:resolved>, <tmp:default>).
"""
import collections, hashlib, importlib.util, json, os, sys

collector_path, r1_path, r2_path, checks, discovery_path, destination, freeze_path = sys.argv[1:8]
places = json.load(open(freeze_path, "rb"))["places"]
spec = importlib.util.spec_from_file_location("mr_unit_log_outcomes", collector_path)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
identity = lambda text: text
runs = {"main-8e847c15-resolved-tmpdir": ("main-8e847c15-tmpdir-20261125T2110Z", places["<tmp:resolved>"]),
        "main-8e847c15-default-tmpdir": ("main-8e847c15-default-20261125T2110Z", places["<tmp:default>"])}
readings = {}
for source, (directory, tmpdir) in runs.items():
    raw = open(os.path.join(checks, directory, "logs/unit-tests.log"), "rb").read()
    summary = json.load(open(os.path.join(checks, directory, "summary.json"), "rb"))
    reading = collector.collect_log(raw)
    rows = {row["id"]: row for row in reading["tests"] + reading["fixtures"]}
    readings[source] = {"rows": rows, "normalizer": collector.Normalizer(summary, [tmpdir]),
                        "not_passing": sorted(i for i, r in rows.items() if r["outcome"] in collector.NOT_PASSING or r["kind"] == "fixture"),
                        "log_sha256": hashlib.sha256(raw).hexdigest()}
discovery = json.load(open(discovery_path, "rb"))
ids = discovery.get("ids") or discovery.get("method_ids") or []
if not ids:
    for key, value in discovery.items():
        if isinstance(value, list) and value and isinstance(value[0], str) and value[0].startswith("test_"):
            ids = value
            break
counts = collections.Counter(ids)
report = {"logs": {k: v["log_sha256"] for k, v in readings.items()}, "discovery_ids": len(ids),
          "discovery_repeated": [i for i, n in counts.items() if n > 1], "rows": [], "tr2_04_problems": [], "tr2_03_problems": []}
for label, path in (("r1", r1_path), ("r2", r2_path)):
    rows = json.load(open(path, "rb"))["attributions"]
    seen = collections.Counter(row["id"] for row in rows)
    report["tr2_03_problems"] += [(label, i) for i, n in seen.items() if n > 1]
    for row in rows:
        outcome = collector.outcome_of(row["events"], row["failing_subtests"])
        if outcome != row["outcome"] or outcome not in collector.NOT_PASSING:
            report["tr2_04_problems"].append((label, row["id"], row["outcome"], outcome))
        if counts.get(row["id"], 0) > 1:
            report["tr2_03_problems"].append((label, row["id"], "repeated in discovery"))
        if row["source"] not in runs:
            continue
        reading = readings[row["source"]]
        observed = reading["rows"].get(row["id"])
        normalize = reading["normalizer"] if row["form"] == "normalized" else identity
        statement = collector.record_statement(observed, normalize) if observed else None
        expected = {key: row[key] for key in ("outcome", "occurrences", "events", "failing_subtests", "skipped_subtests")}
        report["rows"].append({"run": label, "id": row["id"], "source": row["source"], "form": row["form"],
                               "found": observed is not None, "equal": statement == expected})
for source, reading in readings.items():
    attributed = {r["id"] for r in report["rows"] if r["source"] == source}
    report.setdefault("baseline_not_passing_not_attributed", {})[source] = [i for i in reading["not_passing"] if i not in attributed]
report["summary"] = {"rows": len(report["rows"]), "equal": sum(r["equal"] for r in report["rows"]),
                     "found": sum(r["found"] for r in report["rows"]),
                     "tr2_04_problems": len(report["tr2_04_problems"]), "tr2_03_problems": len(report["tr2_03_problems"]),
                     "baseline_not_passing_counts": {k: len(v["not_passing"]) for k, v in readings.items()}}
with open(destination, "x") as fh:
    json.dump(report, fh, indent=1)
    fh.write("\n")
print(json.dumps(report["summary"], indent=1))
print("discovery ids", report["discovery_ids"], "repeated", report["discovery_repeated"][:5])
print("not equal:", [r["id"] for r in report["rows"] if not r["equal"]][:10])
print("baseline not-passing not attributed:", {k: v[:5] for k, v in report["baseline_not_passing_not_attributed"].items()})
