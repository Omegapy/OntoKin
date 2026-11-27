"""W2 (freeze 001): the IDs that a discovery document lists and main's resolved-directory log does not, by module.

Usage: python3 -I -S -B added_modules.py DISCOVERY MAIN_COLLECT OUTPUT

DISCOVERY is a runtime-discovery document (ontokin.c271.p35-runtime-discovery/2); MAIN_COLLECT is the MR
collector's record of main's resolved-directory unit log. It starts no process and writes only OUTPUT (absent).
"""
import json
import os
import sys
from collections import Counter

if not sys.flags.dont_write_bytecode:
    sys.stderr.write("refused: run with -B\n")
    raise SystemExit(2)
discovery_path, collect_path, output = sys.argv[1:4]
if os.path.lexists(output):
    sys.stderr.write("refused: output exists\n")
    raise SystemExit(2)
discovery = json.load(open(discovery_path, encoding="utf-8"))
collect = json.load(open(collect_path, encoding="utf-8"))
ids = discovery["ids_in_discovery_order"]
main_ids = [row["id"] for row in collect["tests"]]
main_set, ids_set = set(main_ids), set(ids)
added = [item for item in ids if item not in main_set]
removed = [item for item in main_ids if item not in ids_set]
by_module = Counter(item.split(".")[0] for item in added)
modules_main = Counter(item.split(".")[0] for item in main_ids)
document = {"schema": "ontokin.c271.p36-w2-freeze-added-ids/1", "discovery_count": len(ids), "main_count": len(main_ids),
            "added": len(added), "removed": len(removed), "removed_ids": removed,
            "added_by_module": dict(sorted(by_module.items())),
            "added_modules_absent_from_main": sorted(name for name in by_module if name not in modules_main),
            "added_modules_present_in_main": sorted(name for name in by_module if name in modules_main),
            "added_ids": added}
fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
with os.fdopen(fd, "w", encoding="utf-8") as stream:
    stream.write(json.dumps(document, indent=1, sort_keys=True) + "\n")
print(json.dumps({key: document[key] for key in ("discovery_count", "main_count", "added", "removed")}))
for name, count in sorted(by_module.items()):
    print(count, name, "(new module)" if name not in modules_main else "(module in main)")
