"""Audit the checkpoint034 source premises and static models; never run OntoKin."""
from __future__ import annotations
import argparse
import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def git_blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def function(tree, name, owner=None):
    scope = tree
    if owner:
        scope = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == owner)
    return next(n for n in scope.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)

def has_call(node, method):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and n.func.attr == method for n in ast.walk(node))

def floor128(value):
    return Fraction((value.numerator << 128) // value.denominator, 1 << 128)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--baseline-inventory", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--captured-failure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Analysis output must be fresh")
    checks = []
    def require(label, condition, **details):
        checks.append({"name": label, "passed": bool(condition), **details})
        if not condition:
            raise ValueError(label)
    inventory = json.loads(args.baseline_inventory.read_bytes())
    source_paths = ["ontokin/reach_reference_center.py", "ontokin/reach_reference.py",
                    "ontokin/reach_numeric.py", "ontokin/reach_reference_plan.py",
                    "docs/engineering/reach-centered-coefficients.md",
                    "docs/language-design/planar-reach-v0.1/budget-counting.md",
                    "docs/language-design/planar-reach-v0.1/libraries/reach-assets.ok"]
    require("baseline_source_identity",
            inventory["source_commit"] == "336fd0c1b1ec094797328800ac623dfea7717e07"
            and inventory["tree"] == "a791352c48f324097f533bb802eadad57f840198")
    by_path = {e["path"]: e for e in inventory["files"]}
    inputs = []
    for name in source_paths:
        raw = (args.repo / name).read_bytes()
        require("source_blob:" + name, git_blob(raw) == by_path[name]["git_blob"])
        inputs.append({"path": name, "git_blob": git_blob(raw), "bytes": len(raw), "sha256": sha256(raw)})
    center_text = (args.repo / source_paths[0]).read_text()
    reference_text = (args.repo / source_paths[1]).read_text()
    center, reference = ast.parse(center_text), ast.parse(reference_text)
    exact = function(reference, "exact", "_Arithmetic")
    first = exact.body[0]
    require("exact_precharges_one_tick", isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Call)
            and ast.unparse(first.value.func) == "self.tick"
            and not first.value.args and not first.value.keywords)
    for name in ("lookup", "remember"):
        fn = function(center, name, "_Guard")
        first = fn.body[0]
        require(name + "_precharges_one_checked_tick",
                isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
                and ast.unparse(first.value.func) == "self.checked"
                and len(first.value.args) == 1
                and ast.unparse(first.value.args[0]) == "self.a.tick")
    remember = function(center, "remember", "_Guard")
    require("remember_has_existing_admission_argument",
            "admission" in [a.arg for a in remember.args.kwonlyargs])
    offset = function(center, "_offset")
    assignments = {n.targets[0].id: n.value for n in offset.body
                   if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)}
    required = {
        "first": "guard.floor(combined(product(diagonal, x), product(cross, y), True))",
        "last": "guard.floor(combined(product(cross, x), product(diagonal, y)))",
    }
    for name, expected in required.items():
        require("original_expression:" + name,
                ast.dump(assignments[name], include_attributes=False) ==
                ast.dump(ast.parse(expected, mode="eval").body, include_attributes=False))
    product = next(n for n in offset.body if isinstance(n, ast.FunctionDef) and n.name == "product")
    product_text = ast.unparse(product)
    require("existing_zero_positive_negative_identity_shortcuts",
            "not first" in product_text and "not last" in product_text
            and "last == 1" in product_text and "last == -1" in product_text)
    coefficients = function(center, "_coefficients")
    publications = [n for n in coefficients.body if isinstance(n, ast.Expr)
                    and isinstance(n.value, ast.Call)
                    and ast.unparse(n.value.func) == "guard.remember"]
    offset_coefficient_calls = [n for n in ast.walk(offset)
                                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                                and n.func.id == "_coefficients"]
    require("coefficient_publication_precedes_offset_products",
            len(publications) == 1 and isinstance(coefficients.body[-1], ast.Return)
            and publications[0].lineno < coefficients.body[-1].lineno
            and len(offset_coefficient_calls) == 1
            and offset_coefficient_calls[0].lineno < assignments["first"].lineno
            and assignments["first"].lineno < assignments["last"].lineno)
    recipe = next(n for n in center.body if isinstance(n, ast.ClassDef) and n.name == "_CenteredNode")
    fields = [n.target.id for n in recipe.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)]
    require("new_pair_recipe_is_not_implemented", fields == [
        "vector", "position_radius", "identity_offset", "coefficient_source", "seal"])
    ledger_raw = args.ledger.read_bytes()
    ledger = json.loads(ledger_raw)
    require("ledger_source_identity", ledger["source_commit"] == inventory["source_commit"]
            and ledger["source_tree"] == inventory["tree"])
    expected_costs = {"ordinary": (4, 0, 4, 0), "separate_bundled": (2, 3, 5, -1),
                      "known_donor_bundled": (2, 2, 4, 0), "separate_scalars": (2, 6, 8, -4),
                      "conditional_same_slot": (2, 1, 3, 1)}
    require("complete_unique_cost_cases",
            len(ledger["cases"]) == len(expected_costs)
            and {row["id"] for row in ledger["cases"]} == set(expected_costs))
    for row in ledger["cases"]:
        got = tuple(row[k] for k in ("product_charges", "added_lookup_publication_charges", "total", "saving"))
        require("static_cost:" + row["id"], got == expected_costs[row["id"]]
                and row["total"] == row["product_charges"] + row["added_lookup_publication_charges"]
                and row["saving"] == 4 - row["total"])
    require("ledger_makes_no_execution_or_saving_claim",
            not ledger["product_request_executed"] and not ledger["actual_saving_measured"]
            and ledger["measurement_kind"] == "static_source_charge_model")
    bits = ledger["prospective_bits"]
    require("prospective_numerator_bound", bits["product_numerator"] == 535 + 138 == 673)
    require("prospective_denominator_bound", bits["product_denominator"] == 516 + 129 == 645)
    require("full_domain_only", max(bits["product_numerator"], bits["product_denominator"]) < bits["required_domain"] == 32768)
    b, a, axial = Fraction.from_float(0.23), Fraction.from_float(0.1), Fraction.from_float(0.05)
    require("exact_original_b", b == Fraction(8286623314361713, 36028797018963968))
    arithmetic_examples = 0
    eligible_examples = 0
    for w in (Fraction(0), Fraction(1), Fraction(3,4), Fraction(-3,4), Fraction(2)-(Fraction(1,1<<128))):
        for s in (Fraction(0), Fraction(1,2), Fraction(-1,2), Fraction(1,1<<128)):
            d, c = w*w-s*s, 2*w*s
            p, q = d*b, c*b
            for axis in range(3):
                order = ((axis+1)%3, (axis+2)%3, axis)
                for y in (-a, a):
                    original = floor128(d*b-c*y), floor128(c*b+d*y), axial
                    shared = floor128(p-c*y), floor128(q+d*y), axial
                    result_a, result_b = [None]*3, [None]*3
                    for index, va, vb in zip(order, original, shared):
                        result_a[index], result_b[index] = va, vb
                    require("exact_example:" + str(arithmetic_examples), result_a == result_b)
                    arithmetic_examples += 1
                    eligible_examples += int(bool(d and c) and b not in (0,1,-1))
    capture_raw = args.captured_failure.read_bytes()
    capture = json.loads(capture_raw)
    offset_frame = next(f for f in capture["frames"] if f["function"] == "_offset")["locals"]
    evaluate_frame = next(f for f in capture["frames"] if f["function"] == "evaluate")["locals"]
    def fraction(value):
        return Fraction(int(value["numerator"]), int(value["denominator"]))
    require("archived_partial_key_has_original_b", fraction(offset_frame["x"]) == b)
    require("archived_partial_key_y_axis", offset_frame["axis"] == 1 and offset_frame["order"] == [2,0,1])
    require("archived_recipient_is_nonstationary",
            evaluate_frame["node"]["stationary"] is False
            and evaluate_frame["node"]["path"] == 'rig.head.eyes["right"].frame')
    require("archived_selected_products_have_nonzero_coefficients",
            bool(fraction(offset_frame["diagonal"])) and bool(fraction(offset_frame["cross"])))
    result = {
        "schema_version": "ontokin.checkpoint034-proof-audit/0.1",
        "status": "passed", "scope": "source-premise, static-ledger and exact-example audit",
        "source_commit": inventory["source_commit"], "source_tree": inventory["tree"],
        "python": sys.version, "platform": platform.platform(), "inputs": inputs,
        "ledger_sha256": sha256(ledger_raw), "captured_failure_sha256": sha256(capture_raw),
        "checks": checks, "analysis_assertions": len(checks),
        "exact_formula_examples": arithmetic_examples,
        "examples_with_two_original_multiplication_paths": eligible_examples,
        "ontokin_runtime_imported": False, "product_requests_executed": 0,
        "implementation_test_methods": 0, "actual_candidate_saving_measured": False,
        "complete_source_pair_eligibility_established": False,
        "candidate_disposition": ledger["disposition"],
        "limitations": [
            "Finite examples supplement the algebra; they do not prove all rational inputs.",
            "One archived recipient frame does not establish every donor/pair/source-selection premise.",
            "The conditional +1 is a source-derived local model, not an executed candidate or request.",
            "No implementation, hostile control, original recording or release gate is validated."
        ]
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k:result[k] for k in ("status","analysis_assertions","exact_formula_examples",
                                           "product_requests_executed","actual_candidate_saving_measured")}))
if __name__ == "__main__":
    main()
