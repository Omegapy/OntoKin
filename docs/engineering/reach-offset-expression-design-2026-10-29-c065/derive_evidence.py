#!/usr/bin/env python3
"""Reproduce C065's finite source and algebra audit without importing OntoKin."""
import argparse
import ast
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def add(a, b, sign=1):
    result = dict(a)
    for term, coefficient in b.items():
        result[term] = result.get(term, 0) + sign * coefficient
    return {term: coefficient for term, coefficient in result.items() if coefficient}


def multiply(a, b):
    result = {}
    for first, ac in a.items():
        for last, bc in b.items():
            term = tuple(sorted(first + last))
            result[term] = result.get(term, 0) + ac * bc
    return {term: coefficient for term, coefficient in result.items() if coefficient}


def polynomial(text, names):
    def visit(node):
        if isinstance(node, ast.Name):
            require(node.id in names, "Unknown symbolic variable")
            return names[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return {term: -coefficient for term, coefficient in visit(node.operand).items()}
        if isinstance(node, ast.BinOp):
            first, last = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return add(first, last)
            if isinstance(node.op, ast.Sub):
                return add(first, last, -1)
            if isinstance(node.op, ast.Mult):
                return multiply(first, last)
        raise ValueError("Unsupported symbolic expression")
    return visit(ast.parse(text, mode="eval").body)


def encoded(poly):
    return [{"factors": list(term), "coefficient": coefficient}
            for term, coefficient in sorted(poly.items())]


def functions(text):
    return {node.name: node for node in ast.parse(text).body
            if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def fraction_record(value):
    return {"numerator": value.numerator, "denominator": value.denominator}


def branch_counts(d, c, a, z):
    # This is a standalone mathematical cost model, not a runtime execution
    count = 0

    def product(first, last):
        nonlocal count
        if not first or not last:
            return Fraction(0)
        if last == 1:
            return first
        count += 1
        return -first if last == -1 else first * last

    def combined(first, last, subtract=False):
        nonlocal count
        if not first:
            if subtract and last:
                count += 1
                return -last
            return last
        if not last:
            return first
        count += 1
        return first - last if subtract else first + last

    original = (combined(product(d, z), product(c, a), True),
                combined(product(c, z), product(d, a)))
    original_count = count
    count = 0
    p, n, q, m = d * z, c * (-a), c * z, d * (-a)
    candidate = (combined(p, n), combined(q, m, True))
    require(candidate == original, "Branch model changes an exact floor argument")
    return {"original_right_arithmetic": original_count,
            "signed_right_arithmetic": count, "raw_reduction": original_count - count}


def derive(root):
    folder = Path(__file__).resolve().parent
    binding = json.loads((folder / "source-binding.json").read_text())
    checked = []
    for row in binding["inputs"]:
        data = (root / row["path"]).read_bytes()
        require(len(data) == row["bytes"], "Source length changed: " + row["path"])
        require(hashlib.sha256(data).hexdigest() == row["sha256"], "Source hash changed: " + row["path"])
        require(blob(data) == row["git_blob"], "Source blob changed: " + row["path"])
        checked.append(row)

    retained = json.loads((root / "docs/engineering/reach-source-reference-design-2026-10-29-c064/derived-evidence.json").read_text())
    parts = []
    for row in retained["verified_archive_parts"]:
        data = (root / row["path"]).read_bytes()
        require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"],
                "Retained archive part changed: " + row["path"])
        parts.append(data)
    archive_bytes = b"".join(parts)
    require(len(archive_bytes) == retained["archive"]["bytes"]
            and hashlib.sha256(archive_bytes).hexdigest() == retained["archive"]["sha256"],
            "Retained C061 archive identity changed")
    clocks_by_case = {}
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        for case in ("P11", "L03"):
            member = "evidence/round-001/" + case + "/capture/unvalidated-reader-input.glb"
            row = retained["verified_used_members"][member]
            data = archive.read(member)
            require(len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"],
                    "Retained GLB member changed: " + case)
            magic, version, total = struct.unpack_from("<4sII", data)
            size, kind = struct.unpack_from("<II", data, 12)
            require(magic == b"glTF" and version == 2 and total == len(data)
                    and kind == 0x4E4F534A and 20 + size <= len(data), "Invalid retained GLB envelope")
            document = json.loads(data[20:20 + size])
            clock_rows = document["animations"][0]["extras"]["ontokin"]["exact_times_seconds"]
            clocks = [Fraction(int(value["numerator"]), int(value["denominator"])) for value in clock_rows]
            require(len(clocks) == retained["cases"][case]["original_key_count"], "Retained key count changed")
            if case == "P11":
                require(clocks == [Fraction(i, 25) for i in range(50)] + [Fraction(2), Fraction(3)],
                        "Retained P11 clock sequence changed")
            clocks_by_case[case] = {"member": member, **row, "count": len(clocks),
                                   "exact_times_seconds": clock_rows,
                                   "successful_reader_validation_claimed": False}

    center = (root / "ontokin/reach_reference_center.py").read_text()
    nodes = functions(center)
    offset = nodes["_offset"]
    floor_calls = [node for node in ast.walk(offset) if isinstance(node, ast.Call)
                   and isinstance(node.func, ast.Attribute) and node.func.attr == "floor"]
    require(len(floor_calls) == 2, "Original offset no longer has two separate floors")
    product_calls = [node for node in ast.walk(offset) if isinstance(node, ast.Call)
                     and isinstance(node.func, ast.Name) and node.func.id == "product"]
    require(len(product_calls) == 4, "Original offset product structure changed")
    require('return diagonal, cross' in center and 'source is None' in center,
            "Existing coefficient route missing")

    assets = (root / "docs/language-design/planar-reach-v0.1/libraries/reach-assets.ok").read_text()
    for vector in ("vec3(-0.1[m], 0.05[m], 0.23[m])", "vec3(0.1[m], 0.05[m], 0.23[m])"):
        require(vector in assets, "Pinned eye vector missing")
    require('axis = vec3(0, 1, 0)' in assets, "Pinned head axis missing")
    l03 = (root / "docs/language-design/planar-reach-v0.1/draft2-supplements/sources/l03-completed-action-new-owner.ok").read_text()
    require('upper_length = 1[m]' in l03 and 'forearm_length = 1[m]' in l03,
            "Pinned L03 unit lengths changed")
    budget = (root / "docs/language-design/planar-reach-v0.1/budget-counting.md").read_text()
    require('Each new lookup, type/limit/claim check' in budget
            and 'copied logical value is still charged' in budget,
            "Adopted copied-value funding rule missing")

    names = {name: {(name,): 1} for name in ("D", "C", "A", "Z")}
    for name, expression in (("p", "D*Z"), ("n", "C*(-A)"),
                             ("q", "C*Z"), ("m", "D*(-A)")):
        names[name] = polynomial(expression, names)
    identities = []
    for original, candidate in (("D*Z-C*(-A)", "p-n"), ("C*Z+D*(-A)", "q+m"),
                                ("D*Z-C*A", "p+n"), ("C*Z+D*A", "q-m")):
        first, last = polynomial(original, names), polynomial(candidate, names)
        require(first == last, "Signed polynomial identity failed")
        identities.append({"original": original, "candidate": candidate,
                           "equal_unrounded_polynomial": encoded(first), "floor_location": "unchanged"})

    # Source literals pass through binary64 in the current admitted recipes
    # These controls do not substitute decimal fractions for those operands
    a, z = Fraction(float("0.1")), Fraction(float("0.23"))
    cases = []
    for label, d, c, expected in (("both_nonzero", Fraction(3, 5), Fraction(4, 5), 4),
                                 ("diagonal_zero", Fraction(0), Fraction(4, 5), 3),
                                 ("cross_zero", Fraction(3, 5), Fraction(0), 1),
                                 ("both_zero", Fraction(0), Fraction(0), 0)):
        result = branch_counts(d, c, a, z)
        require(result["raw_reduction"] == expected, "Wrong degenerate branch count")
        cases.append({"case": label, **result})
    scale = 1 << 128
    def floor128(value):
        return Fraction((value.numerator * scale) // value.denominator, scale)
    half = Fraction(1, 2 * scale)
    require(-floor128(half) != floor128(-half), "Expected floor/sign control failed")
    require(floor128(half) + floor128(half) != floor128(half + half),
            "Expected separate-floor control failed")

    return {
        "schema_version": "ontokin.c065-symbolic-derivation/0.1",
        "baseline_commit": binding["baseline_commit"], "baseline_tree": binding["baseline_tree"],
        "source_inputs_verified": checked,
        "audit_kind": "standard-library symbolic algebra and static source checks",
        "product_modules_imported": False, "product_requests_executed": 0, "product_suites_executed": 0,
        "retained_data": {"archive": retained["archive"], "parts_verified": len(parts),
                          "clock_metadata": clocks_by_case},
        "original_offset": {"floors_per_node": len(floor_calls), "product_call_sites_per_node": len(product_calls),
                            "floor_lines": sorted(node.lineno for node in floor_calls)},
        "polynomial_identities": identities,
        "illustrative_exact_source_operands": {"A": fraction_record(a), "Z": fraction_record(z)},
        "coefficient_controls_are_abstract_rationals_not_captured_centers": True,
        "branch_models_not_runtime_measurements": cases,
        "floor_noncommutation_controls": {"sign": True, "sum": True},
        "selected_detached_schedule": {
            "maximum_removed_arithmetic_per_completed_pair": 4,
            "bridge_definition": "All four producer copies completed; include partial consumer progress before a later failure",
            "new_producer_scalar_copies_per_completed_pair": 4,
            "charge_per_new_scalar_copy": 1,
            "net_upper_bound_before_all_other_added_work": 0,
            "complete_request_inequality": "sum(g(e)-4) - preparation - other_added - unsuccessful_attempt_work <= 0",
            "replay_independent": True, "decision": "reject selected detached-copy schedule",
            "generic_reference_only_graph_impossibility_claimed": False},
        "single_traversal_only": {"P11_supplied_keys": clocks_by_case["P11"]["count"],
                                  "gross_ceiling": 4 * clocks_by_case["P11"]["count"],
                                  "replay_or_fallback_total_not_inferred": True},
        "L03_source_review_conclusion": {
            "selected_offset_product_opportunity": 0,
            "basis": "Pinned unit offsets use distinct orientations; the original product helper skips multiplication by one",
            "runtime_measurement": False},
        "new_runtime_speedup_claimed": False, "release_acceptance": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    print(json.dumps(derive(args.repository.resolve()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
