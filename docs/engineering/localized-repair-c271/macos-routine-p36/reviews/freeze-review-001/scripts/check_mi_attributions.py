"""Recompute the MI-derived attribution statements from MI's retained per-module logs (read only).

Usage: python3 -I -S -B check_mi_attributions.py COLLECTOR R1_ATTR R2_ATTR MI_DIR OUT.json
Loads MR's reviewed collector from its committed path and calls its read-only collect_log and
record_statement; starts nothing; writes only OUT.json.
"""
import hashlib, importlib.util, json, os, re, sys

collector_path, r1_path, r2_path, mi_dir, destination = sys.argv[1:6]
spec = importlib.util.spec_from_file_location("mr_unit_log_outcomes", collector_path)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)
identity = lambda text: text

logs = {
    "test_current_host_readback_driver": "tests.test_current_host_readback_driver.txt",
    "test_current_host_readback_provider": "tests.test_current_host_readback_provider.txt",
    "test_current_host_inspection_v01": "tests.test_current_host_inspection_v01.txt",
    "test_current_host_required_images_v01": "tests.test_current_host_required_images_v01.txt",
    "test_current_host_rtld_paths_v01": "tests.test_current_host_rtld_paths_v01.txt",
    "test_static_tray_readback_v01": "tests.test_static_tray_readback_v01.txt",
}
collected, digests = {}, {}
for module, name in logs.items():
    raw = open(os.path.join(mi_dir, name), "rb").read()
    digests[module] = hashlib.sha256(raw).hexdigest()
    reading = collector.collect_log(raw)
    rows = {}
    for row in reading["tests"] + reading["fixtures"]:
        rows[row["id"]] = row
    collected[module] = {"rows": rows, "not_passing": sorted(i for i, r in rows.items() if r["outcome"] in collector.NOT_PASSING or r["kind"] == "fixture"),
                         "footer": reading["footer"]}


def mi_id(routine_id):
    match = re.fullmatch(r"(setUpClass|tearDownClass|setUpModule|tearDownModule) \((test_[^.)]+)(.*)\)", routine_id)
    if match:
        return "%s (tests.%s%s)" % match.groups(), match.group(2)
    return "tests." + routine_id, routine_id.split(".")[0]


report = {"logs": digests, "rows": [], "mi_not_passing_not_attributed": {}, "suspicious_reason_text": []}
attributed = set()
for label, path in (("r1", r1_path), ("r2", r2_path)):
    for row in json.load(open(path, "rb"))["attributions"]:
        if row["source"] not in ("D-18", "MI final-003", "MC22"):
            continue
        source_id, module = mi_id(row["id"])
        attributed.add((label, source_id))
        observed = collected[module]["rows"].get(source_id)
        statement = collector.record_statement(observed, identity) if observed else None
        expected = {key: row[key] for key in ("outcome", "occurrences", "events", "failing_subtests", "skipped_subtests")}
        equal = statement == expected
        texts = [e.get("reason_first_line") or "" for e in row["events"]] + \
                [s.get("reason_first_line") or "" for s in row["failing_subtests"]] + [s.get("subtest") or "" for s in row["failing_subtests"]]
        flags = [t for t in texts if re.search(r"tests\.test_|/Volumes/|/private/var|/var/folders|OntoKin|/Users/|\.venv|line \d+", t)]
        if flags:
            report["suspicious_reason_text"].append({"run": label, "id": row["id"], "texts": flags})
        report["rows"].append({"run": label, "id": row["id"], "source": row["source"], "mi_id": source_id, "found": observed is not None,
                               "equal": equal, "outcome": row["outcome"], "consistent": collector.outcome_of(row["events"], row["failing_subtests"]) == row["outcome"]})
for module, data in collected.items():
    missing = [i for i in data["not_passing"] if ("r1", i) not in attributed and ("r2", i) not in attributed]
    report["mi_not_passing_not_attributed"][module] = missing
report["summary"] = {"rows": len(report["rows"]), "equal": sum(r["equal"] for r in report["rows"]),
                     "found": sum(r["found"] for r in report["rows"]), "consistent": sum(r["consistent"] for r in report["rows"]),
                     "by_run_source": {}}
for r in report["rows"]:
    key = r["run"] + ":" + r["source"]
    report["summary"]["by_run_source"][key] = report["summary"]["by_run_source"].get(key, 0) + 1
with open(destination, "x") as fh:
    json.dump(report, fh, indent=1)
    fh.write("\n")
print(json.dumps(report["summary"], indent=1))
print("not equal:", [r["id"] for r in report["rows"] if not r["equal"]][:10])
print("MI not-passing not attributed:", json.dumps(report["mi_not_passing_not_attributed"], indent=1))
print("suspicious reasons:", len(report["suspicious_reason_text"]))
for s in report["suspicious_reason_text"][:12]:
    print("  ", s["run"], s["id"][:100], [t[:160] for t in s["texts"]])
