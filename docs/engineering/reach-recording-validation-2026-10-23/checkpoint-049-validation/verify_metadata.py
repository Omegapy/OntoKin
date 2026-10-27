#!/usr/bin/env python3
"""Check C049 source/evidence identities and ledger arithmetic; never import OntoKin."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RECORDS = Path(__file__).resolve().parent.parent


def digest(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    checks = []
    def check(name, condition, detail=None):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})

    inventory = json.loads((RECORDS / "checkpoint-049-validation/recovery/source-inventory.json").read_text())
    changed = []
    before = {}
    for item in inventory["files"]:
        current = digest(ROOT / item["path"])
        before[item["path"]] = current
        if any(current[key] != item[key] for key in ("bytes", "sha256", "git_blob")):
            changed.append(item["path"])
    check("exact_recovered_base_files", not changed, {"files": len(before), "changed": changed})
    check("source_snapshot_counts", len(before) == 923 and sum(x["bytes"] for x in before.values()) == 128112412)
    runtime = sorted(path for path in before if path.startswith("ontokin/"))
    check("complete_runtime_source_inventory", len(runtime) == 65)
    check("all_original_documents_present", sum(Path(p).suffix.lower() in (".md", ".html") for p in before) == 214)

    calls = []
    class Calls(ast.NodeVisitor):
        def __init__(self, path):
            self.path, self.scope = path, []
        def visit_ClassDef(self, node):
            self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
        def visit_FunctionDef(self, node):
            self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
        def visit_Call(self, node):
            name = getattr(node.func, "attr", None)
            if name in ("_series_factorials", "_series_coefficients"):
                calls.append({"path": self.path, "line": node.lineno, "scope": ".".join(self.scope), "name": name})
            self.generic_visit(node)
    for path in runtime:
        Calls(path).visit(ast.parse((ROOT / path).read_text(), filename=path))
    check("explicit_runtime_call_sites", len(calls) == 2 and all(x["scope"] == "_Arithmetic._series_dyadic" for x in calls), calls)

    ledger = json.loads((RECORDS / "checkpoint-049-cost-ledger.json").read_text())
    screen = ledger["fresh_four_helper_screen"]
    subtotal = screen["charged_check_subtotal"]
    check("four_helper_screen_subtotal", sum(v for k, v in subtotal.items() if k != "total") == subtotal["total"] == 14)
    check("target_complete_and_prefix_bounds", screen["D14_complete_net_upper_bound"] == 13 - 14 == -1 and screen["D14_corresponding_prefix_net_upper_bound"] == 4 - 14 == -10)
    interval = screen["conditional_interval"]
    check("conditional_interval_bounds", sum(interval["completed_gross_savings"]) == 56 and 56 - 5 * 14 == interval["completed_net_upper_bound_before_other_costs"] == -14 and 60 - 6 * 14 == interval["including_partial_D14_net_upper_bound_before_other_costs"] == -24)
    migration = ledger["existing_table_recurrence_migration"]
    check("recurrence_count_bounds", 128 // 5 + 11 == migration["source_limit"] == 36 and 2 * 36 + 1 == migration["source_last"] == 73 and migration["restricted_through_29_factorial_multiplications"] == 29 - 1 and migration["full_through_73_factorial_multiplications"] == 73 - 1)
    check("negative_result_is_scoped", screen["partial_screen_only"] and not screen["safe_admission_complete"] and not screen["universal_impossibility"] and ledger["one_slot_protocol"]["complete_net_saving"] is None and not ledger["runtime_candidate_selected"])
    check("preserved_limits", ledger["preserved_limits"] == {"shared_operations": 100000, "elapsed_ms": 30000, "operand_bits": 32768, "cache_entries": 256, "cursor_updates": 64})

    old_failures = json.loads((RECORDS / "checkpoint-049-validation/recovery/initial-transport-limitations.json").read_text())["unavailable"]
    archives = []
    for item in old_failures:
        current = digest(ROOT / item["path"])
        archives.append({"path": item["path"], **current, "passed": current["git_blob"] == item["sha"] and current["bytes"] == item["size"]})
    check("historical_binary_inputs_restored", len(archives) == 12 and all(x["passed"] for x in archives) and sum(x["bytes"] for x in archives) == 74915834, archives)

    review_results = {}
    for role in ("numerical", "cost"):
        data = json.loads((RECORDS / f"checkpoint-049-reviews/{role}/result.json").read_text())
        items = data.get("inspected_inputs", data.get("reviewed_inputs", data.get("inputs", [])))
        if isinstance(items, dict):
            items = items.get("files", [])
        mismatches = []
        for item in items:
            current = digest(ROOT / item["path"])
            if current["sha256"] != item["sha256"] or current["bytes"] != item.get("bytes", item.get("size_bytes", current["bytes"])):
                mismatches.append(item["path"])
        review_results[role] = {"reviewed_inputs": len(items), "mismatches": mismatches, "status": data.get("status")}
        check(role + "_review_input_binding", bool(items) and not mismatches, review_results[role])

    held = json.loads((RECORDS / "checkpoint-049-validation/held-runtime-binding.json").read_text())
    check("held_C035_runtime_unchanged", held["all_equal"] and held["modules"] == 65 and held["held_tree"] == "87c949b238055af1ce368c694e1d5683c8aeacde")
    after_changes = [path for path, initial in before.items() if digest(ROOT / path) != initial]
    check("base_inputs_stable_during_metadata_audit", not after_changes, after_changes)
    result = {"schema": "ontokin.checkpoint049-metadata-audit/0.1", "status": "passed" if all(x["passed"] for x in checks) else "failed", "grouped_metadata_checks": len(checks), "stable_base_inputs": len(before), "checks": checks, "runtime_execution": False, "candidate_replay": False, "review_results": review_results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("status", "grouped_metadata_checks", "stable_base_inputs", "runtime_execution", "candidate_replay")}))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
