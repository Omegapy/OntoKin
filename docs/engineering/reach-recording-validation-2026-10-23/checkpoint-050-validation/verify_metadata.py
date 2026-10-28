#!/usr/bin/env python3
"""Check C050 source identities and declared evidence; never import OntoKin."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RECORD = HERE.parent
checks = []


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def identity(path):
    data = path.read_bytes()
    return {
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest(),
    }


def check(name, ok, detail):
    checks.append({"name": name, "passed": bool(ok), "detail": detail})


tree = read(HERE / "base-tree.json")
entries = {row["path"]: row for row in tree["tree"] if row["type"] == "blob"}
commit = read(HERE / "base-commit.json")
check("base_identity", not tree["truncated"] and len(entries) == 2748
      and tree["sha"] == "574c75e870d50aed5e5e96b34b454389074350fe"
      and commit["sha"] == "e828ee2d54b3c2a5a82bb332327fdce982a0f7f2"
      and commit["tree"]["sha"] == tree["sha"], {"files": len(entries), "tree": tree["sha"]})

recovered = read(HERE / "recovered-inputs.json")
bad = []
for row in recovered:
    actual = identity(ROOT / row["path"])
    if (actual != {key: row[key] for key in actual}
            or actual["git_blob"] != entries[row["path"]]["sha"]
            or actual["size"] != entries[row["path"]]["size"]):
        bad.append(row["path"])
check("recovered_base_stability", len(recovered) == 959 and not bad,
      {"files": len(recovered), "bytes": sum(row["size"] for row in recovered), "mismatches": bad})

held = read(HERE / "held-runtime-binding.json")
bad = [row["path"] for row in held["files"]
       if not row["matches_held_C035"] or identity(ROOT / row["path"])["git_blob"] != row["git_blob"]]
check("held_runtime_preserved", len(held["files"]) == 65 and not bad,
      {"modules": len(held["files"]), "held_tree": held["tree"], "mismatches": bad})

parsed = []
for path in sorted(RECORD.rglob("*.json")):
    if path.name.startswith("checkpoint-050") or "checkpoint-050-" in path.as_posix():
        read(path)
        parsed.append(path.relative_to(ROOT).as_posix())
check("new_json_parse", bool(parsed), {"files": parsed})

review_counts = {}
bad = []
for role in ("authority", "cost", "alternative"):
    result = read(RECORD / "checkpoint-050-reviews" / role / "result.json")
    rows = result.get("inputs", result.get("inspected_inputs", []))
    review_counts[role] = len(rows)
    for row in rows:
        actual = identity(ROOT / row["path"])
        size = row.get("bytes", row.get("size_bytes"))
        if (actual["size"] != size or actual["sha256"] != row["sha256"]
                or actual["git_blob"] != row["git_blob"]
                or actual["git_blob"] != entries[row["path"]]["sha"]):
            bad.append({"review": role, "path": row["path"]})
check("independent_review_source_bindings", review_counts == {"authority": 21, "cost": 16, "alternative": 28}
      and not bad, {"counts": review_counts, "mismatches": bad})

ledger = read(RECORD / "checkpoint-050-cost-ledger.json")
interval = ledger["captured_interval"]
h2 = ledger["H2"]
check("declared_charge_arithmetic", sum(interval["original_complete_helpers"]) == 269
      and sum(interval["affine_complete_helpers_before_admission"]) == 213
      and 269 - 213 == interval["gross_sum"] == 56
      and h2["D14_new_check_floor"] == 3 * 14 + 4 == 46
      and h2["D14_net_upper_bound"] == 61 - (48 + 46) == -33
      and h2["corresponding_prefix"]["net_upper_bound"] == 30 - (26 + 25) == -21,
      "Integer arithmetic over source-derived ledger counts only; no numerical candidate replay.")

next_scope = read(RECORD / "checkpoint-050-next-scope.json")
validation = read(RECORD / "checkpoint-050-validation.json")
limits = {"shared_operations": 100000, "elapsed_ms": 30000, "operand_bits": 32768,
          "cache_entries": 256, "cursor_updates": 64}
check("scope_and_limits", ledger["preserved_limits"] == limits == next_scope["preserved_limits"]
      and next_scope["next_checkpoint"] == "C051"
      and next_scope["gross_only"]["whole_request_net"] is None
      and ledger["whole_request"]["status"] == "unknown; no positive complete bound"
      and validation["runtime"]["runtime_tests"] == 0
      and validation["runtime"]["original_requests"] == 0
      and not validation["runtime"]["candidate_selected"]
      and not validation["release"]["merged_to_main"],
      {"limits": limits, "scope": "source-only; unknown whole-request outcome; no release acceptance"})

new_paths = []
unexpected = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT).as_posix()
    if rel in entries:
        continue
    new_paths.append(rel)
    if not rel.startswith("docs/engineering/reach-recording-validation-2026-10-23/") or not (
            "/checkpoint-050" in rel or rel.endswith("/HANDOFF-050.md")):
        unexpected.append(rel)
check("owned_additions_only", not unexpected, {"new_files": len(new_paths), "unexpected": unexpected})

summary = {
    "schema": "ontokin.checkpoint050-metadata-result/0.1",
    "status": "passed" if all(row["passed"] for row in checks) else "failed",
    "grouped_metadata_checks": len(checks),
    "checks": checks,
    "source_inputs": len(recovered),
    "runtime_modules": len(held["files"]),
    "runtime_tests": 0,
    "candidate_replays": 0,
    "scope": "source/artifact identities and declared count arithmetic, not runtime behavior",
}
print(json.dumps(summary, indent=2))
sys.exit(0 if summary["status"] == "passed" else 1)
