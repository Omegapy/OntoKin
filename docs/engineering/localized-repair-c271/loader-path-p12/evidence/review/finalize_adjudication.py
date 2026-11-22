"""Freeze the independent N57 documentary adjudication; no product execution."""
from pathlib import Path
import ast
import copy
import datetime
import hashlib
import json

ROOT = Path(__file__).resolve().parent
DETAIL = ROOT / "n57-adjudication"

def identity(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()

def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False) + "\n")

initial = DETAIL / "ADJUDICATION.json"
record = json.loads(initial.read_text())
positive = json.loads((DETAIL / "sources/fixture_inputs/P01_nonselecting_base.json").read_text())
negative = json.loads((DETAIL / "sources/fixture_inputs/N57_source_variant_unknown.json").read_text())
normalized = []
for label, context in (("P01", positive), ("N57", negative)):
    logical = copy.deepcopy(context)
    del logical["variant_review"]["completeness"]
    raw = canonical(logical)
    path = DETAIL / (label + "-WITHOUT-SYNTHETIC-COMPLETENESS.json")
    with path.open("xb") as handle:
        handle.write(raw)
    normalized.append(identity(path))
assert normalized[0]["sha256"] == normalized[1]["sha256"] == "e33cb05c8e73031f7c720ecee68094ced82f5d3679af4bc1ebf95bca5b0eaa3c"

def logical_projection(context):
    review = context["variant_review"]
    return {
        "schema": {"fixed_operational_schema": "ontokin.current-host-readback-origin-variants/0.1.0"},
        "loader": {"synthetic_context_key": "variant_review.loader_identity", "synthetic_identity": review["loader_identity"], "actual_descriptor_supplied": False},
        "source_review": {"synthetic_context_key": "variant_review.source_review_identity", "synthetic_identity": review["source_review_identity"], "actual_descriptor_supplied": False},
        "suffixes": {"synthetic_context_key": "variant_review.suffixes", "value": review["suffixes"]},
    }

projection = {
    "schema": "ontokin.c271.p12-n57-logical-projection-evidence/1",
    "operational_keys": ["schema", "loader", "source_review", "suffixes"],
    "accepted_source": "DECISION.md:49",
    "is_an_operational_document": False,
    "purpose": "Compare the supplied logical evidence for each permitted operational field, without inventing absent descriptors or plan bytes.",
    "P01": logical_projection(positive),
    "N57": logical_projection(negative),
    "equal": logical_projection(positive) == logical_projection(negative),
    "absent_operational_selector": "completeness",
    "limitations": [
        "Synthetic loader and source-review identities are not actual descriptors; this evidence must not be parsed as an operational variant document.",
        "No operational plan or external expected digest is materialized or accepted by this comparison.",
    ],
}
write_json(DETAIL / "OPERATIONAL-SCHEMA-PROJECTION.json", projection)

digest_observations = {
    "schema": "ontokin.c271.p12-n57-external-binding-observations/1",
    "P01": positive["plan_selection"],
    "N57": negative["plan_selection"],
    "equal": positive["plan_selection"] == negative["plan_selection"],
    "actual_plan_bytes_supplied": False,
    "actual_external_expected_digest_supplied": False,
    "interpretation": "Both controls assert external_digest_matches, rationale_descriptor_matches and variant_descriptor_matches true. The entire plan_selection object is identical. This is equality of the frozen synthetic observations, not a claim to have calculated an operational plan digest.",
}
assert digest_observations["equal"] and all(positive["plan_selection"][key] is True for key in ("external_digest_matches", "rationale_descriptor_matches", "variant_descriptor_matches"))
write_json(DETAIL / "EXTERNAL-BINDING-OBSERVATIONS.json", digest_observations)

source_path = DETAIL / "sources/production-baseline.py"
source = source_path.read_text()
lines = source.splitlines()
tree = ast.parse(source)
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_check_resolution")
review_occurrences = [{"line": node.lineno, "context": type(node.ctx).__name__} for node in ast.walk(function) if isinstance(node, ast.Name) and node.id == "review"]
review_occurrences.sort(key=lambda row: (row["line"], row["context"]))
assert len(review_occurrences) == 3
assert {row["line"] for row in review_occurrences} == {853, 854}
source_evidence = {
    "schema": "ontokin.c271.p12-n57-rationale-semantics/1",
    "source": identity(source_path),
    "source_revision": record["reviewed_revision"],
    "function": "_check_resolution",
    "function_start": function.lineno,
    "function_end": function.end_lineno,
    "excerpt_first_line": 850,
    "excerpt_last_line": 855,
    "excerpt": "\n".join(lines[849:855]) + "\n",
    "review_variable_occurrences": review_occurrences,
    "method": "Static AST parse and source inspection only; production module was not imported or executed.",
    "observation": "The existing rationale path has descriptor validation, bounded file reading, a nonempty-byte and SHA256 condition, and descriptor binding. Its review bytes are not parsed for a completeness decision. The local review variable has one assignment and two loads in the nonempty/SHA256 condition, then is unused.",
    "limit": "This does not assert that no later reviewed design could establish an admission boundary. No such operational selector or review-result representation is adopted by the frozen control contract here.",
}
write_json(DETAIL / "RATIONALE-SOURCE-EVIDENCE.json", source_evidence)

materialization_path = ROOT / "MATERIALIZATION-RECEIPT.json"
materialization = json.loads(materialization_path.read_text())
assert materialization["status"] == "passed" and len(materialization["files"]) == 175
assert all(row["restored_verified"] for row in materialization["files"])
boundary_path = ROOT.parent / "checks/SOURCE-BOUNDARY.json"
boundary = json.loads(boundary_path.read_text())
assert boundary["files_checked"] == len(boundary["rows"]) == 942
assert all(row["passed"] for row in boundary["rows"])

record["schema"] = "ontokin.c271.p12-independent-n57-final-adjudication/1"
record["recorded_at_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
record["previous_record_preserved"] = identity(initial)
record["canonical_blocker"] = "P12-N57-POLICY-BINDING-001"
record["findings"][0]["prior_local_id"] = record["findings"][0]["id"]
record["findings"][0]["id"] = record["canonical_blocker"]
record["normalized_context_files"] = normalized
record["operational_schema_projection"] = identity(DETAIL / "OPERATIONAL-SCHEMA-PROJECTION.json")
record["external_binding_observations"] = identity(DETAIL / "EXTERNAL-BINDING-OBSERVATIONS.json")
record["existing_rationale_semantics"] = identity(DETAIL / "RATIONALE-SOURCE-EVIDENCE.json")
record["private_materialization"] = {
    "receipt": identity(materialization_path),
    "payloads": 146,
    "explicit_supports": 29,
    "cases": 97,
    "source_modes_and_hashes_verified": True,
    "original_paths_written": False,
    "payload_execution": False,
}
record["root_source_boundary_observation"] = {
    "receipt": identity(boundary_path),
    "observed_head": boundary["observed_head"],
    "files_checked": 942,
    "all_rows_passed": True,
    "new_focused_test_exists": boundary["new_focused_test_exists"],
    "candidate_manifest_unchanged": boundary["candidate_manifest_unchanged"],
    "qualification": "Root-authored static preservation record inspected by this reviewer; independent direct byte comparisons for the production module and both inherited test files are in current_source_observation.",
}
record["checks"].update({
    "normalized_context_files_equal": True,
    "permitted_field_logical_projection_equal": projection["equal"],
    "external_binding_observations_equal": digest_observations["equal"],
    "existing_rationale_no_completeness_parse": True,
    "private_corpus_materialized_exactly": True,
})
record["phase_disposition"] = {
    "technical_status": "blocked_before_implementation",
    "implementation_authored": False,
    "production_tests_run": False,
    "frozen_97_cases_changed": False,
    "inherited_175_tests_run": False,
    "implementation_success_claim": False,
    "parent_C271": "blocked",
    "R03_R05": "unmet",
    "next_step": "Finish documentary closure and verified partial handoff for this one phase. A separately declared and independently reviewed clarification is a future phase, not work adopted here.",
}
record["unknowns"] = [
    "No real loader suffix-completeness review or operational plan is supplied by P01/N57; portable positives remain synthetic.",
    "A new private policy constructor is proposed but not implemented. The adopted documents do not define a machine-observable result that maps the differing synthetic label to the normative N57 refusal without a new contract decision.",
    "Final documentary publication and final package/save verification have not been reviewed by this technical adjudication; they require their own later evidence.",
]
record["review_observation_errors"] = [
    {
        "event": "An overly broad display of root SOURCE-BOUNDARY.json was truncated by the tool output limit.",
        "recovery": "The exact retained file was subsequently parsed in full without printing rows; all 942 row results were checked and the complete file SHA256 was recorded.",
        "product_effect": "none",
    },
    {
        "event": "The independent materialization command's tool response was unavailable after context compaction.",
        "recovery": "The completed persisted receipt was read and its 175 verified rows inspected. The exclusive-create materializer was not rerun and its complete receipt is retained.",
        "product_effect": "none",
    },
]
write_json(ROOT / "ADJUDICATION.json", record)

report = """# P12 independent blocker adjudication

## Verdict and phase boundary

**P12-N57-POLICY-BINDING-001 blocks implementation under the frozen P11 contract.** N57 requires an unsupported-variant refusal, but its only difference from positive P01 is a synthetic completeness label. The accepted operational variant document excludes that label and leaves source completeness to independent review. A faithful production input or admission result for this difference has not been specified. Stop technical P12 and preserve the control unchanged. No replacement policy or expectation is adopted here.

This is a static design/control binding finding, not a failed runtime test. Production code and both inherited test files remain byte-identical to the accepted P11 terminal source. No focused test file exists. Neither the 97 controls nor the inherited 175 tests were executed. C271 remains blocked and R03–R05 remain unmet.

## Exact source and control

The reviewed source is commit `79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae`. The candidate004 manifest SHA256 is `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de`. Exact source copies and their hashes are bound by `ADJUDICATION.json` and `BASELINE-INPUTS.json`.

| Evidence | P01 positive | N57 negative |
| --- | --- | --- |
| Fixture SHA256 | `ffae051f6da02526bd8b5b52313d004063f900fa84ebe779f24aeb0df59d72de` | `85a0c7f2b1055f39328c42a3c95e405d474e67b6ba7e442eec4c271d018953a5` |
| `variant_review.completeness` | `synthetic_declared_complete` | `unsupported` |
| Every other parsed field | Identical | Identical |
| `plan_selection.external_digest_matches` | `true` | `true` |
| Variant and rationale descriptor-match observations | Both `true` | Both `true` |

After removing only the synthetic completeness key, each canonical logical context is 3,338 bytes with SHA256 `e33cb05c8e73031f7c720ecee68094ced82f5d3679af4bc1ebf95bca5b0eaa3c`. Both exact normalized files are retained. The same loader/review identities, suffix list, guards, image binding, subject, kernel observations and search directories remain. N57 also retains the synthetic positive assumptions; these do not provide a separately observable production distinction.

The frozen N57 oracle requires `CHI-UNSUPPORTED`, `stage=variant_review`, `rule_id=LP-VARIANT-SEMANTICS`, `state=REJECTED`, zero target starts and no host qualification. `CONTROL-CONTRACT.md` makes code, stage and rule ID normative and requires an adapter to show how each observation reaches actual production logic. Its portable context schema is explicitly nonoperational. [Sources: candidate004 `EXPECTATIONS.json`, `FIXTURE-MANIFEST.json`, `CONTROL-CONTRACT.md` paragraphs 15 and 25; exact records in the adjudication.]

## Missing operational binding

`DECISION.md` defines the separate variant document with exactly `schema`, `loader`, `source_review` and `suffixes`. The source review must explain the actual loader and justify a complete suffix union. Completeness remains an independent-review obligation; the tool checks the bound inventory and facts and does not infer loader semantics from a JSON assertion. The private immutable policy must be derived from source/plan binding. A caller-provided context flag is not admission proof. [Sources: candidate004 `DECISION.md`, paragraphs 49, 53, 55, 85 and 109.]

`n57-adjudication/OPERATIONAL-SCHEMA-PROJECTION.json` compares the logical evidence available for each permitted field. These projections are equal. They are **not operational documents**: the controls supply synthetic identities rather than actual loader and rationale descriptors. Likewise, equality of the digest-match flags is not a claim to have calculated an operational plan digest; neither actual plan bytes nor an external expected digest is supplied by these controls.

The existing `_check_resolution` validates the rationale descriptor, reads bounded bytes, requires nonempty content with the expected SHA256, and checks descriptor binding. It does not parse a completeness decision. Static AST inspection confirms the local `review` value is assigned once and read only for the nonempty/SHA256 condition. The exact source excerpt and observations are retained in `n57-adjudication/RATIONALE-SOURCE-EVIDENCE.json`; the full production source SHA256 is `0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612`. No module was imported to inspect it.

An unreviewed adapter could choose `policy=None` when it sees `unsupported`, directly raise the expected error, add a completeness/approval field, alter a descriptor or suffix list, or change the oracle. Each introduces a new decision or changes the frozen input. None proves that the adopted production boundary observes the specified N57 difference. This finding does not prohibit a future policy design; it identifies the absent contract needed to implement and test one faithfully.

## Preservation and limits

The independent materializer authenticated 146 candidate payloads and 29 explicitly bound support files, reconstructed the declared lossless transport envelope, and restored exact source bytes and modes under a fresh private root with mode `0700`. It preserved all 97 controls and the candidate manifest. Receipt: `MATERIALIZATION-RECEIPT.json`, 99,963 bytes, SHA256 `96382f1291ac7027c07a1efef061658281d16e0917b0cccee2281e1ffaf4c4c8`. No payload, checker or production test was executed; no original source path was written. This does not claim recursive restoration of every historical attempt.

Root's separate source-boundary record at documentary commit `74c9cdaeb7f92cc7d3e6957b8a92d798250b9e55` records all 942 protected files unchanged, the candidate manifest unchanged and no new focused test. This reviewer parsed all recorded rows; direct independent byte comparisons of the production module and both inherited test files are also retained. The root record SHA256 is `91d052696b9da296d8f56e4189916c61a88416361fbd5cd268a86bea87145b8d`.

The initial adjudication remains intact at `n57-adjudication/ADJUDICATION.json` with SHA256 `f13d9dadb7e2f93d8c0a8a6a63ab51fc896ca379470ba2596d551e601009171b`. Final machine-readable evidence records the local prior finding ID and the canonical blocker ID. Observation-only truncation/recovery events are recorded explicitly.

The remaining work in this phase is documentary closure and a verified partial handoff. A later independently reviewed clarification may define a source-review-to-policy boundary and faithful N57 mapping, or clarify its external-review status. That decision is not made here. Final publication and final package/save verification require later independent evidence and are not claimed by this report.
"""
with (ROOT / "REPORT.md").open("x", encoding="utf-8") as handle:
    handle.write(report)
print(json.dumps({"status": "finalized", "files": [identity(ROOT / "ADJUDICATION.json"), identity(ROOT / "REPORT.md"), identity(materialization_path)]}, indent=2))
