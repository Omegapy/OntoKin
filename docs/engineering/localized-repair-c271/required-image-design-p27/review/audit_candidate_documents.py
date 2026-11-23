"""Independent documentary cross-check for the P27 design, without product imports.

This verifies recorded identities and consistency. It does not execute the control
plan, materialize its synthetic fixtures, or qualify an operational input.
"""
from pathlib import Path
import datetime
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DESIGN = ROOT / "records/design"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate documentary key: " + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(), object_pairs_hook=pairs)


def identity(path):
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": digest(data)}


checks = []


def check(name, condition, detail=None):
    row = {"check": name, "passed": bool(condition)}
    if detail is not None:
        row["detail"] = detail
    checks.append(row)


decision = read_json(DESIGN / "DECISION.json")
control = read_json(DESIGN / "CONTROL-PLAN.json")
surface = read_json(DESIGN / "FUTURE-SURFACE.json")
sources = read_json(DESIGN / "SOURCE-EVIDENCE.json")
author_reads = read_json(DESIGN / "READ-SET.json")
raw_audit = read_json(HERE / "RETAINED-BYTE-AUDIT.json")
candidate_files = [identity(DESIGN / name) for name in (
    "DESIGN.md", "DECISION.json", "FUTURE-SURFACE.json", "CONTROL-PLAN.json",
    "SOURCE-EVIDENCE.json", "READ-SET.json")]

check("design-only authority", decision["implementation_performed"] is False
      and decision["product_execution_performed"] is False
      and control["executable"] is False and control["fixture_bytes_frozen"] is False
      and control["implementation_run_authority"] is False
      and control["expected_product_result_status"] == "NOT_RUN"
      and surface["executable"] is False)
check("same decision IDs", len({x["decision_id"] for x in (decision, control, surface, sources)}) == 1)
check("source file remains exact", identity(ROOT / "repo" / decision["source_file"]["path"])["sha256"]
      == decision["source_file"]["sha256"] == "eea3e6343ae34d9c930a810ca4f363cbcd4264a8d943731f927e41b213755d7a")

expected_names = {"libdl.so.2", "libm.so.6", "libpthread.so.0", "librt.so.1", "libutil.so.1"}
check("exact finite catalog", set(decision["catalog"]) == expected_names
      and set(decision["closed_shapes"]["subjects_exact_keys"]) == expected_names)
for observed in raw_audit["images"]:
    name = Path(observed["package_member"]).name
    row = decision["catalog"][name]
    data = (DESIGN / "sources/package-images" / (name + ".inert")).read_bytes()
    check("catalog equals independent byte audit: " + name,
          row["binding"] == {"sha256": observed["sha256"], "size_bytes": observed["bytes"], "mode": observed["package_mode"]}
          and row["package_member"] == observed["package_member"]
          and digest(data) == observed["sha256"] and len(data) == observed["bytes"])
    # Header fields and program-header kinds are inert data observations only.
    phoff = struct.unpack_from("<Q", data, 32)[0]
    phsize, phcount = struct.unpack_from("<HH", data, 54)
    interp_count = sum(struct.unpack_from("<I", data, phoff + i * phsize)[0] == 3 for i in range(phcount))
    f = observed["fields"]
    metadata = {"class": f["elf_class"], "endian": f["endian"], "machine": f["machine"],
                "type": f["type"], "interpreter": None, "needed": f["needed"],
                "soname": f["soname"][0], "rpath": f["rpath"], "runpath": f["runpath"]}
    check("literal actual metadata matches independent audit: " + name,
          interp_count == 0 and data[7] == row["observed_osabi"] and row["actual_fixture_metadata"] == metadata)
    expected_flags = [0, 8, 24] if name == "libm.so.6" else [0, 8]
    expected_flags1 = [0, 1, 9, 134217728, 134217729] if name == "librt.so.1" else [0, 1, 134217728, 134217729]
    check("separate exact tag and flag predicates: " + name,
          row["plt_tags"] == [1879048192, 1879048193, 1879048195] and row["each_tag_occurrences"] == 1
          and row["dt_flags"] == {"maximum_occurrences": 1, "absence_allowed": True, "allowed_values": expected_flags}
          and row["dt_flags_1"] == {"maximum_occurrences": 1, "absence_allowed": True, "allowed_values": expected_flags1})

cases = control["cases"]
ids = [c["id"] for c in cases]
by_id = {c["id"]: c for c in cases}
check("unique complete count", len(ids) == len(set(ids)) == control["count"])
check("all controls unrun and zero actual target starts", all(c["execution_status"] == "NOT_RUN" and
      c["target_starts"] == {"node": 0, "ldd": 0, "direct_loader": 0, "cpu_checker": 0} for c in cases))


def diagnostic_nodes(value):
    if isinstance(value, dict):
        if "code" in value and "reason" in value:
            yield value
        for child in value.values():
            yield from diagnostic_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from diagnostic_nodes(child)


selectors_checked = 0
for c in cases:
    for node in diagnostic_nodes(c["expected"]):
        rule = node.get("details", {}).get("rule_id")
        if rule in decision["new_diagnostics"]:
            expected = decision["new_diagnostics"][rule]
            check("literal new diagnostic: " + c["id"] + "/" + rule,
                  all(node.get(k) == v for k, v in expected.items()) and all(k in node for k in expected))
            selectors_checked += 1
check("libm lone static-TLS flag negative frozen", by_id["RI-N24"]["input"]["mutation"]["catalog_key"] == "libm.so.6"
      and by_id["RI-N24"]["input"]["mutation"]["dt_flags_entries"] == [16]
      and by_id["RI-N24"]["expected"] == decision["unchanged_diagnostics"]["flags"])

old = {
    "A": ("CHI-LOADER", "Missing or unknown object keys; expected ignored_kernel_rows, images, inspector_commands, loader_inputs, needed_edges, profile, rationale, search_directories", {}),
    "B": ("CHI-PLAN", "Missing or unknown origin-profile keys", {"stage": "profile_selection", "rule_id": "LP-CLOSED-SHAPE"}),
    "C": ("CHI-PLAN", "Missing or unknown origin-profile keys", {"stage": "profile_selection", "rule_id": "LP-CLOSED-SHAPE"}),
    "D": ("CHI-PLAN", "Missing or unknown origin-profile keys", {"stage": "profile_selection", "rule_id": "LP-CLOSED-SHAPE"}),
    "E": ("CHI-PLAN", "Invalid RTLD path model shape", {"stage": "rtld_paths", "rule_id": "RP-SHAPE", "path": None, "operation": "shape", "errno": None,
          "evidence": {"observations": [], "primary": None, "cleanup": []}}),
}
for suffix, (code, reason, details) in old.items():
    e = by_id["RI-L09" + suffix]["expected"]
    check("legacy closed-shape literal " + suffix, e == {"state": "REJECTED", "new_policy_dispatches": 0,
          "cause": None, "code": code, "reason": reason, "details": details})
check("single binding refusal precedence", control["binding_refusal_precedence"] == decision["binding_refusal_precedence"])
check("adapter rule permits the explicitly labelled prerequisite seams",
      "only independently identified unrelated prerequisite" not in control["adapter_rule"]
      and "named" in control["adapter_rule"] and "labelled" in control["adapter_rule"])
for control_id in ("RI-C04", "RI-C06"):
    case = by_id[control_id]
    seam = case["input"]["mock_contract"]["failure_seam"]
    expected_binding = {"sha256": "295fa521a03cd2faa99974f378c9e23dd622021ec7d32bcad4f8ea61aec8a872",
                        "size_bytes": 14408, "mode": "0o644"}
    altered_binding = {**expected_binding, "sha256": "0" * 64}
    expected_cause = {"code": "CHI-INSPECTOR", "reason": "Bound file identity differs: /required-images/libdl.so.2",
                      "state": "REJECTED", "details": {}, "cause": None}
    check("reachable literal _bound observation seam: " + control_id,
          seam["declared_expected_binding"] == expected_binding and seam["return_actual_binding"] == altered_binding
          and case["expected"]["cause_selector"] == expected_cause
          and case["expected"]["details"] == {"stage": "recheck", "rule_id": "LP-RECHECK"}
          and case["expected"]["state"] == "REJECTED")
check("future edit surface remains bounded", surface["production_edits"] == ["prototypes/static_tray_v01/current_host_inspection_v01.py"]
      and surface["new_test_adapter"] == ["tests/test_current_host_required_images_v01.py"]
      and surface["existing_test_fixture_oracle_edits_allowed"] is False
      and surface["other_product_edits_allowed"] is False and surface["new_dependencies"] == [])

references = []
for s in sources["source_ids"]:
    references.extend(s["evidence"])
references.extend(sources["supporting_file_identities"])
references.extend(sources["reproducible_excluded_inputs"])
references.extend(author_reads["read_entries"])
reference_keys = set()
for r in references:
    if "artifact_path" in r:
        path = DESIGN / r["artifact_path"]
    elif "repository_path" in r:
        base = ROOT / ("governance-main" if r.get("authority") == "governing-main" else "repo")
        path = base / r["repository_path"]
    elif "director_record" in r:
        path = ROOT / r["director_record"]
    else:
        check("recognized reference shape", False, r)
        continue
    key = (str(path), r.get("sha256"), r.get("bytes"))
    if key in reference_keys:
        continue
    reference_keys.add(key)
    actual = identity(path)
    check("source/read-set identity: " + str(path.relative_to(ROOT)), actual["bytes"] == r["bytes"] and actual["sha256"] == r["sha256"])
check("complete delivery set resolves", len(sources["delivery_files"]) == len(set(sources["delivery_files"]))
      and all((DESIGN / p).is_file() for p in sources["delivery_files"]))

result = {
    "schema": "ontokin.c271.p27-independent-document-audit/1",
    "recorded_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "passed": all(c["passed"] for c in checks),
    "reviewer": "/root/design_review",
    "execution": {"command": "python3 records/design-review/audit_candidate_documents.py",
                  "cwd": str(ROOT), "python_executable": sys.executable, "python_version": sys.version,
                  "script_sha256": digest(Path(__file__).read_bytes())},
    "candidate_files": candidate_files,
    "control_semantic_obligations": len(cases),
    "new_diagnostic_occurrences_checked": selectors_checked,
    "unique_source_identity_references_checked": len(reference_keys),
    "checks": checks,
    "product_imports_or_executions": 0,
    "controls_executed": 0,
    "host_input_observations": 0,
    "limits": "Documentary identity/consistency audit and retained ELF header observations only. No parser qualification, fixture execution, whole-source proof, signature or build reproduction claim."
}
(HERE / "CANDIDATE-DOCUMENT-AUDIT.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"passed": result["passed"], "checks": len(checks), "failed": [c for c in checks if not c["passed"]],
                  "controls_executed": 0, "report": "records/design-review/CANDIDATE-DOCUMENT-AUDIT.json"}))
sys.exit(0 if result["passed"] else 1)
