"""C057 metadata/source-identity audit. Does not import or execute OntoKin."""
from pathlib import Path
import ast
import base64
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[3]
PREFIX = BASE.relative_to(ROOT).as_posix()
PARENT = "8287be55a21c28320aa11895cadd29c68ae18f90"
TREE = "274acc026f2e0d5dee3eb4a754790cc420a354a0"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "git_blob": hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()}


checks = []


def check(name, valid, details):
    checks.append({"name": name, "passed": bool(valid), "details": details})


tree = read(HERE / "parent-tree.json")
index = {x["path"]: x for x in tree["tree"] if x["type"] == "blob"}
check("complete_parent_inventory", tree["sha"] == TREE and not tree["truncated"] and len(index) == 3059,
      {"tree": tree["sha"], "parent_files": len(index), "truncated": tree["truncated"]})

originals, additions, altered, invalid_scope = [], [], [], []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file():
        continue
    rel = path.relative_to(ROOT).as_posix()
    if rel in index:
        value = identity(path.read_bytes())
        originals.append({"path": rel, **value})
        if value["git_blob"] != index[rel]["sha"] or value["bytes"] != index[rel]["size"]:
            altered.append(rel)
    else:
        additions.append(rel)
        if not rel.startswith(PREFIX + "/checkpoint-057") and rel != PREFIX + "/HANDOFF-057.md":
            invalid_scope.append(rel)
check("original_bytes_and_addition_scope", not altered and not invalid_scope,
      {"materialized_originals": len(originals), "original_bytes": sum(x["bytes"] for x in originals),
       "altered_originals": altered, "out_of_scope_additions": invalid_scope})

documents = [p for p in index if Path(p).suffix.lower() in (".md", ".html")]
missing = [p for p in documents if not (ROOT / p).is_file()]
check("all_parent_narratives_present", len(documents) == 255 and not missing,
      {"parent_markdown_html": len(documents), "missing": missing})

binding = read(BASE / "checkpoint-057-source-binding.json")
accepted = read(HERE / "accepted-source-slice.json")
accepted_bytes = {x["path"]: base64.b64decode(x["content_base64"]) for x in accepted["files"]}
source_failures = []
for row in binding["paired_inputs"]:
    current = (ROOT / row["path"]).read_bytes()
    original = accepted_bytes[row["path"]]
    for key, raw in (("accepted", original), ("current", current)):
        if any(identity(raw)[field] != row[key][field] for field in ("bytes", "sha256", "git_blob")):
            source_failures.append([row["path"], key])
    if (current == original) != row["identical"]:
        source_failures.append([row["path"], "equality"])
check("separate_accepted_current_sources", len(binding["paired_inputs"]) == 8 and not source_failures,
      {"paired_inputs": len(binding["paired_inputs"]), "failures": source_failures})

budget_path = "docs/language-design/planar-reach-v0.1/budget-counting.md"
adoption = read(ROOT / "docs/language-design/planar-reach-v0.1/adoption.json")
budget_identity = identity((ROOT / budget_path).read_bytes())
normative = adoption["effective_normative_inputs"]
budget_rows = [x for x in adoption["frozen_inputs"] if x.get("path") == budget_path]
check("adopted_budget_identity", "budget-counting.md" in normative and len(budget_rows) == 1 and budget_rows[0].get("sha256") == budget_identity["sha256"],
      {"matched_normative_inputs": budget_rows, "actual": budget_identity})

derivation = "docs/engineering/reach-certificate-native-fields.md"
old = accepted_bytes[derivation].decode()
new = (ROOT / derivation).read_text()
check("derivation_append_only", new.startswith(old) and len(old.splitlines()) == 176 and len(new.splitlines()) == 186,
      {"accepted_lines": len(old.splitlines()), "current_lines": len(new.splitlines())})

def body(source, class_name, method):
    module = ast.parse(source)
    cls = next(x for x in module.body if isinstance(x, ast.ClassDef) and x.name == class_name)
    fn = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == method)
    return ast.dump(fn, include_attributes=False)

ref = "ontokin/reach_reference.py"
method_equal = {name: body(accepted_bytes[ref].decode(), "_Arithmetic", name) ==
                     body((ROOT / ref).read_text(), "_Arithmetic", name)
                for name in ("exact", "_atan_small", "pi")}
check("unchanged_contrast_method_bodies", all(method_equal.values()), method_equal)

held = read(HERE / "held-runtime-binding.json")
held_rows = held["comparison"]
check("held_runtime_identity", len(held_rows) == 65 and all(x["match"] and x["current_blob"] == x["held_blob"] and
      x["current_mode"] == x["held_mode"] and index[x["path"]]["sha"] == x["current_blob"] for x in held_rows),
      {"runtime_rows": len(held_rows), "held_commit": held["held_commit"], "current_commit": held["current_commit"]})

reviews = read(BASE / "checkpoint-057-reviews.json")
review_failures = []
for review in reviews["final_core_audits"]:
    audit_path = BASE / review["final_audit"]
    if identity(audit_path.read_bytes())["sha256"] != review["sha256"]:
        review_failures.append([review["role"], "audit_identity"])
    if not review["paused"] or review["unresolved_findings"] != 0:
        review_failures.append([review["role"], "audit_status"])
    for item in review["inputs"]:
        if identity((ROOT / item["path"]).read_bytes())["sha256"] != item["sha256"]:
            review_failures.append([review["role"], item["path"]])
check("frozen_core_review_bindings", len(reviews["final_core_audits"]) == 3 and not review_failures,
      {"roles": [x["role"] for x in reviews["final_core_audits"]], "failures": review_failures})

recovery = read(HERE / "recovered-inputs.json")
expected_rows = recovery["files"] if isinstance(recovery.get("files"), list) else recovery.get("inputs", [])
expected_names = {x["path"] for x in expected_rows}
actual_names = {x["path"] for x in originals}
check("recovery_manifest_closure", expected_names == actual_names,
      {"manifest_files": len(expected_names), "actual_originals": len(actual_names),
       "unrecorded": sorted(actual_names - expected_names), "missing": sorted(expected_names - actual_names)})

events = read(BASE / "checkpoint-057-event-funding.json")
conformance = (ROOT / events["file"]).read_text().splitlines()
ranges = {x["id"]: x["lines"] for x in events["events"] + events["full_gate_expansion"]}
expected = {"G2": [2762, 2799], "G3": [2800, 2814], "G4": [2815, 2828],
            "E03": [2993, 3004], "E04": [3005, 3012], "E05": [3013, 3017]}
check("corrected_source_range_bindings", all(ranges[k] == v for k, v in expected.items()) and
      "independent_certificate_compare_admission" in conformance[3028] and "except AttributeError" in conformance[3010],
      {"ranges": expected, "admission_line": 3029, "slot_exception_line": 3011})

private = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and
           (p.name.startswith("private-") or p.name.endswith(".signed.json"))]
check("no_private_transport_artifacts", not private, {"private_paths": private})

result = {"schema": "ontokin.checkpoint057-metadata-result/0.1", "status": "passed" if all(c["passed"] for c in checks) else "failed",
          "source_parent": PARENT, "source_tree": TREE, "checks": checks,
          "groups": len(checks), "failures": [x["name"] for x in checks if not x["passed"]],
          "product_imports": 0, "product_execution": False}
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["status"] == "passed" else 1)
