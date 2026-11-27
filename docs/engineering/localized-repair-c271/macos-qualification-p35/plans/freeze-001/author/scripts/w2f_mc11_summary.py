"""W2 freeze author: a read-only summary of an MC11 scan record (stdlib; -I -S -B). Prints to stdout."""
import collections
import json
import sys

with open(sys.argv[1], "rb") as stream:
    scan = json.loads(stream.read())
print("inputs", json.dumps(scan["inputs"], sort_keys=True))
print("totals", scan["totals"], "unresolved", scan["unresolved_relative_specifiers"])
print("frozen", json.dumps(scan["frozen_rule"], sort_keys=True))
for key, entry in scan["files"].items():
    dyn = collections.Counter((row["pattern"], row.get("classification"), row.get("context"), row.get("view"))
                              for row in entry["dynamic"])
    calls = [(row["pattern"], row["line"], row["column"], row.get("receiver", "")[-30:], row.get("context"))
             for row in entry["process_call_names"]]
    specs = [(row["pattern"], row["line"], row["specifier"], row["resolution"], row.get("view")) for row in entry["specifiers"]]
    fr = entry["frozen_rule"]["found"]
    print("==", key, entry["role"], entry["kind"], entry["sha256"][:12], "lines", entry["lines"],
          "pc", len(entry["process_creation"]), "calls", len(calls), "dyn", len(entry["dynamic"]),
          "specs", len(specs), "| frozen dyn", len(fr["dynamic"]), "frozen specs", len(fr["static_specifiers"]))
    for item, count in sorted(dyn.items(), key=lambda x: str(x)):
        print("   dyn", item, count)
    for call in calls:
        print("   call", call)
    for spec in specs:
        print("   spec", spec)
    if len(sys.argv) > 2:
        for kind, line in fr["dynamic"]:
            print("   frozen-dyn", kind, line[:140])
        print("   frozen-specs", fr["static_specifiers"])
