"""Inspect draft source/document metadata only; execute no product or archive code."""
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote
import hashlib
import json
import posixpath
import re
import sys

BASE = Path(__file__).resolve().parents[2]
SOURCE = BASE / "source"
DOCS = SOURCE / "docs/engineering/reach-recording-validation-2026-10-23"
OUT = Path(__file__).resolve().parent
inputs = {}


def read(path):
    path = Path(path)
    data = path.read_bytes()
    inputs[str(path.relative_to(BASE))] = {
        "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()
    }
    return data


def load(path):
    return json.loads(read(path))


started = datetime.now(timezone.utc).isoformat()
read(__file__)
tree = json.loads(load(BASE / "acquisition/tree.json")["structuredContent"]["content"])
remote = {x["path"]: x for x in tree["tree"]}
planned = {p.relative_to(SOURCE).as_posix() for p in DOCS.rglob("*") if p.is_file() and (p.relative_to(DOCS).as_posix().startswith("checkpoint-048") or p.name == "HANDOFF-048.md")}
references = []
for path in sorted(DOCS.rglob("*.md")):
    rel = path.relative_to(SOURCE).as_posix()
    if rel not in planned:
        continue
    text = read(path).decode()
    for link in re.findall(r"\[[^\]\n]*\]\(([^)\s]+)\)", text):
        uri = urlsplit(link)
        if uri.scheme or link.startswith("//"):
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname(rel), unquote(uri.path))) if uri.path else rel
        references.append({"kind": "markdown", "source": rel, "link": link, "target": target, "anchor": uri.fragment, "present_in_base_tree_or_planned": target in remote or target in planned})
for name in ("checkpoint-048-next-scope.json", "checkpoint-048-reviews.json", "checkpoint-048.json", "checkpoint-048-source-binding.json"):
    data = load(DOCS / name)
    paths = data.get("required_reads", []) + ([x["path"] for x in data["reviews"]] if "reviews" in data else []) + ([data["next_scope"]] if "next_scope" in data else []) + ([data["source_inventory"]] if "source_inventory" in data else [])
    for path in paths:
        target = posixpath.normpath(posixpath.join(DOCS.relative_to(SOURCE).as_posix(), path))
        references.append({"kind": "json_reference", "source": name, "path": path, "target": target, "present_in_base_tree_or_planned": target in remote or target in planned})
ledger = load(DOCS / "checkpoint-048-cost-ledger.json")
validation = load(DOCS / "checkpoint-048-validation.json")
review_index = load(DOCS / "checkpoint-048-reviews.json")
review_bindings = []
for row in review_index["reviews"]:
    digest = hashlib.sha256(read(DOCS / row["path"])).hexdigest()
    review_bindings.append({"path": row["path"], "sha256": digest, "matches_index": digest == row["sha256"]})
source_bindings = []
for rel in ("ontokin/reach_reference.py", "ontokin/reach_reference_center.py", "docs/language-design/planar-reach-v0.1/budget-counting.md", "docs/language-design/planar-reach-v0.1/ADOPTION.md"):
    data = read(SOURCE / rel)
    digest = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    source_bindings.append({"path": rel, "git_blob_sha1": digest, "sha256": hashlib.sha256(data).hexdigest(), "matches_recorded_base_tree": digest == remote[rel]["sha"]})
read(BASE / "reviews/evidence/result.json")
checks = {
    "all_relative_markdown_and_structured_references_resolve": all(x["present_in_base_tree_or_planned"] for x in references),
    "no_relative_fragment_requires_unperformed_anchor_validation": all(not x.get("anchor") for x in references),
    "all_three_prior_review_files_match_index": len(review_bindings) == 3 and all(x["matches_index"] for x in review_bindings),
    "all_four_reviewed_source_contract_files_match_base_tree": len(source_bindings) == 4 and all(x["matches_recorded_base_tree"] for x in source_bindings),
    "no_runtime_selection_or_execution_in_ledger": ledger["runtime_candidate_selected"] is False and ledger["runtime_execution"] is False and ledger["release_acceptance"] is False,
    "validation_is_explicitly_pending_in_reviewed_draft": validation["status"] == "pending final scoped validation",
    "all_consumed_input_bytes_remain_stable": all((BASE/path).stat().st_size == record["bytes"] and hashlib.sha256((BASE/path).read_bytes()).hexdigest() == record["sha256"] for path, record in inputs.items()),
}
result = {
    "schema": "ontokin.c048-independent-final-source-review/0.1",
    "reviewer": "/root/bundle_audit",
    "status": "source_math_and_scoped_claims_accepted_pending_root_final_metadata_validation" if all(checks.values()) else "metadata_issue_found",
    "prior_roles": "Portable-bundle integrity audit and independent retained-data audit in C048. This reviewer did not propose the affine algebra or author the root proposal. It read the two other reviewers' reports, so this review is separate but not blind.",
    "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
    "command": [sys.executable, str(Path(__file__).resolve())],
    "scope": "Pure source/text/JSON/hash inspection. No product import, numerical candidate replay, tests, archive operations, archived-code execution, or GitHub mutations.",
    "manual_source_findings": {"coefficient_equations":"sound on genuine factorial domain", "charge_formulas":"4D+3 original; 3D+4 affine; D-1 gross", "fixed_domain_width_bound":"sound with original admission and every actual guard preserved", "arbitrary_cached_tuple_division_origin":"not established by type or tuple shape", "active_Guard_original_observer":"source proves hooks-None admission excludes target", "two_NO_GO_conclusions":"correct only for the named checkpoint-preserving and fresh-divisibility-audited designs"},
    "metadata_check_groups": checks,
    "metadata_check_groups_passed": sum(checks.values()),
    "relative_markdown_references": sum(x["kind"] == "markdown" for x in references),
    "structured_path_references": sum(x["kind"] == "json_reference" for x in references),
    "references": references,
    "recorded_base_tree": tree["sha"],
    "planned_addition_count_at_review": len(planned),
    "source_bindings": source_bindings, "review_bindings": review_bindings,
    "input_count": len(inputs), "inputs": inputs,
    "publication_followup": "The reviewed handoff anticipates a recorded incomplete/failed full documentation checker gate. Root acknowledged that its actual command/result is still pending and must be written before publication; otherwise wording must explicitly say not run/unverified. This review grants no documentation-checker pass.",
    "limitations": ["Mathematical conclusions are manual source proofs, not candidate execution or timing evidence.","Link validation checks the 11 relative Markdown links and 12 explicit structured path references against the recorded base tree plus 22 planned additions; it does not replace the repository documentation checker or fetch external URLs.","Root must bind final metadata validation, later edits, publication identities and ownership closure independently.","No complete checkout, runtime acceptance, positive candidate net saving, L03 success, or full release is certified."],
}
(OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status":result["status"],"metadata_check_groups_passed":result["metadata_check_groups_passed"],"metadata_check_groups_total":len(checks),"relative_markdown_references":result["relative_markdown_references"],"structured_path_references":result["structured_path_references"],"input_count":len(inputs),"failed_checks":[name for name,ok in checks.items() if not ok]},indent=2))
raise SystemExit(0 if all(checks.values()) else 1)
