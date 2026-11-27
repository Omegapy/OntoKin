"""Recompute MC28's first half from the bound discovery documents (read only).

Usage: python3 -I -S -B check_discovery.py DISCOVERY_B BASELINE ADDITIONS CONFIG_DISCOVERY COMPARE OUT.json
"""
import collections, json, sys

b_path, base_path, add_path, cfg_path, cmp_path, destination = sys.argv[1:7]


def ids_of(document):
    for key in ("ids_in_discovery_order", "ids", "test_ids", "method_ids"):
        if isinstance(document.get(key), list):
            return document[key]
    for key, value in document.items():
        if isinstance(value, dict):
            for inner in ("ids", "test_ids"):
                if isinstance(value.get(inner), list):
                    return value[inner]
    raise SystemExit("no id list in " + ", ".join(document))


b = json.load(open(b_path, "rb"))
base = json.load(open(base_path, "rb"))
additions = json.load(open(add_path, "rb"))
cfg = json.load(open(cfg_path, "rb"))
compare = json.load(open(cmp_path, "rb"))
b_ids, base_ids, cfg_ids = ids_of(b), ids_of(base), cfg["method_ids"]
add_ids = additions.get("added") or additions.get("ids") or additions.get("added_ids")
if add_ids is None:
    for key, value in additions.items():
        if isinstance(value, list) and value and isinstance(value[0], str) and value[0].startswith("test_"):
            add_ids = value
            break
expected = set(base_ids) | set(add_ids)
report = {"b": {"count": len(b_ids), "unique": len(set(b_ids)), "state": b.get("state") or b.get("status")},
          "baseline": {"count": len(base_ids), "unique": len(set(base_ids))},
          "additions": {"count": len(add_ids), "unique": len(set(add_ids)), "overlap_with_baseline": len(set(add_ids) & set(base_ids))},
          "b_equals_baseline_plus_additions": set(b_ids) == expected and len(b_ids) == len(expected),
          "missing": sorted(expected - set(b_ids))[:10], "extra": sorted(set(b_ids) - expected)[:10],
          "config_discovery_equals_sorted_b": cfg_ids == sorted(set(b_ids)),
          "compare_record": {k: compare.get(k) for k in ("exact_match", "missing", "extra", "state") if k in compare},
          "b_keys": sorted(b)[:30]}
with open(destination, "x") as fh:
    json.dump(report, fh, indent=1)
    fh.write("\n")
print(json.dumps(report, indent=1)[:3000])
