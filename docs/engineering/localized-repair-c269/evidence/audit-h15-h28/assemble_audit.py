#!/usr/bin/env python3
"""Reproduce the C269 H15-H28 evidence inspection. No observer is imported or run.

Writes only beside this script. It reads retained results, checks their exact
identities, resolves assertion locations with ast, and emits the manually
assessed coverage map. The coverage judgments are data below, not test results.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BASE = "23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb"
EXEC_REV = "5084dd69312e8da5a49aadd33cf83ba56db7c058"
SCOPE_REV = "5e193e831e74483bccca67ea6cf8a1b8cec47491"
P = "docs/engineering/"
C = {n: P + f"localized-repair-c{n}/" for n in (253, 257, 260, 261, 265, 266, 267, 268)}
MAIN = C[268] + "evidence/finalization-a3de3dd23bbf/main-integration/"
SEEN = set()
CHECKS = []


def read(path):
    SEEN.add(path)
    return (ROOT / path).read_bytes()


def identity(path):
    raw = read(path)
    return {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def data(path):
    return json.loads(read(path))


def check(name, condition, **details):
    CHECKS.append({"check": name, "passed": bool(condition), **details})


def git_bytes(rev, path):
    r = subprocess.run(["git", "show", rev + ":" + path], cwd=ROOT, capture_output=True)
    if r.returncode:
        return None
    return r.stdout


def assertion(n, method, summary, filename=None):
    filename = filename or {261: "test_hinge_glb.py", 265: "test_source_hinges.py",
                            266: "test_hinge_binding.py", 267: "test_hinge_compare.py",
                            268: "test_endpoint_reader.py"}[n]
    path = C[n] + filename
    tree = ast.parse(read(path).decode())
    matches = [x for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == method]
    assert len(matches) == 1, (path, method)
    node = matches[0]
    return {"path": path, "method": method, "line_start": node.lineno,
            "line_end": node.end_lineno, "assertion": summary}


def lines(n, filename, start, end, summary):
    path = C[n] + filename
    assert 1 <= start <= end <= len(read(path).decode().splitlines())
    return {"path": path, "method": "module-level controls" if filename.endswith(".py") else "document section",
            "line_start": start, "line_end": end, "assertion": summary}


RUNS = {
    "c261-independent": {"result_path": C[261] + "evidence/independent/run-03/RESULTS.json",
        "array": "controls", "key": "name", "revision": "2c1ecf0649cc891fe0544eace2aab7ce9779bad5",
        "revision_note": "Original local scientific revision in SOURCE-BINDING.json; published equivalent a877b0a3b75595c66c321cf515c7138391af5ba2 has the same recorded scientific tree. Not a C269 execution.",
        "binding_receipt": C[261] + "evidence/independent/SOURCE-BINDING.json"},
    "c265-source": {"result_path": C[265] + "evidence/independent-controls/run-06/results.json",
        "array": "observations", "key": "test", "revision": None,
        "revision_note": "Original per-call run records exact source/test/dependency hashes, not a Git execution revision. The unchanged method suite separately ran on actual main 5084dd6; do not assign that revision to this earlier run.",
        "binding_receipt": MAIN + "CHECKS.json", "later_execution_revision": EXEC_REV,
        "later_execution_log": MAIN + "c265-source_hinges.log"},
    "c265-review": {"result_path": C[265] + "evidence/review/run-04/RESULTS.json",
        "array": "results", "key": "case", "revision": None,
        "revision_note": "Reviewer run records exact implementation/control hashes. REVIEW.json separately records observed local head 09dc3e9e270c4d164a7898dcd98d7638311d0884; this is not an assertion that the working files equaled that commit.",
        "binding_receipt": C[265] + "evidence/review/REVIEW.json"},
    "c265-boundaries": {"result_path": C[265] + "evidence/review/boundaries-02/RESULTS.json",
        "array": "results", "key": "case", "revision": None,
        "revision_note": "Original reviewer run is bound by exact implementation/control/dependency hashes and retained input files; no Git execution revision is embedded.",
        "binding_receipt": C[265] + "evidence/review/REVIEW.json"},
}
for n in (266, 267, 268):
    RUNS[f"c{n}-main"] = {"result_path": MAIN + f"c{n}-controls/results.json", "array": "cases", "key": "case",
        "revision": EXEC_REV, "revision_note": "Historical actual-main execution at the stated revision; inspected, not reexecuted, in C269.",
        "binding_receipt": MAIN + "CHECKS.json"}

for r in RUNS.values():
    r["result_identity"] = identity(r["result_path"])
    r["report"] = data(r["result_path"])
    read(r["binding_receipt"])


def execution(run, *selectors, indices=None):
    r = RUNS[run]
    rows = r["report"][r["array"]]
    if indices is None:
        indices = [i for i, row in enumerate(rows) if any(s in row.get(r["key"], "") for s in selectors)]
    assert indices, (run, selectors)
    selected = [rows[i] for i in indices]
    outcomes = Counter(str(x.get("outcome", x.get("observed", x.get("actual")))) for x in selected)
    codes = Counter(x["code"] for x in selected if "code" in x)
    return {"run_id": run, "result_path": r["result_path"], "checked_revision": r["revision"],
            "result_sha256": r["result_identity"]["sha256"], "case_array": r["array"],
            "case_indices": indices,
            "input_hash_binding": "The selected retained case entries contain exact available payload byte counts and SHA-256 identities. Missing/nonregular/symlink and injected-event cases retain their actual setup and availability rather than manufactured payload hashes. The runs registry in EXECUTION-INDEX.json binds checked code, environment, original command and any retained input archive.",
            "outcomes": dict(outcomes), "typed_codes": dict(codes)}


def sub(description, refs, executions, *, status="complete", gap=None, note=None):
    return {"description": description, "status": status, "source_assertions": refs,
            "execution_evidence": executions, "remaining_gap": gap, "boundary_note": note}


def a265(method, summary):
    return assertion(265, method, summary)


def a267(method, summary):
    return assertion(267, method, summary)


def a268(method, summary):
    return assertion(268, method, summary)


def e265(*methods):
    return execution("c265-source", *methods)


def e267(*methods):
    return execution("c267-main", *methods)


def e268(*methods):
    return execution("c268-main", *methods)


GROUPS = []


def group(h, description, subcases, reason, boundary):
    status = "complete" if all(x["status"] == "complete" for x in subcases) else "partial"
    plan_path = C[260] + "CONTROL-PLAN.md"
    rows = [(i+1, row) for i, row in enumerate(read(plan_path).decode().splitlines()) if row.startswith("| " + h + " |")]
    assert len(rows) == 1, h
    GROUPS.append({"id": h, "description": description, "status": status,
                   "frozen_requirement": {"path": plan_path, "revision": BASE, "line": rows[0][0], "control_plan_row": rows[0][1]},
                   "reason": reason, "interface_boundaries": boundary, "required_subcases": subcases})


group("H15", "Lexical self/direct-part endpoint access and visibility", [
    sub("self.SITE and self.PART.SITE resolve to the independently specified owning object/site identities",
        [a265("test_h01_complete_associations_are_independently_derived", "Asserts own pivot and private blade/public base site IDs, definitions and paths."),
         a267("test_original_before_after_exact_bytes", "accept() checks complete expected endpoint associations for both original byte tuples."),
         a267("accept", "Checks every expected source endpoint field, artifact path, owning object and definition; no direct artifact site identity is invented.")],
        [e265("test_h01_complete_associations"), e267("test_original_before_after")]),
    sub("A private own site and private ordinary part with public child site remain accessible within the defining class",
        [a265("test_h15_private_own_site_and_part_are_allowed", "Changes pivot visibility to private and requires expected hinge values."),
         a267("test_endpoint_access_and_unsupported_forms", "Private pivot fixture passes accept(), preserving complete independent site associations.")],
        [e265("test_h15_private_own"), e267("test_endpoint_access")]),
    sub("An external private site and private imported class refuse; omitted class visibility preserves the public default",
        [a265("test_h15_external_private_site_and_imported_class_refuse", "Separately changes base to private and imported Finger to private; requires whole typed refusal."),
         a265("test_h15_omitted_class_visibility_defaults_public", "Omitted class visibility returns the independently specified hinge values."),
         a267("test_endpoint_access_and_unsupported_forms", "Private external base refuses MALFORMED through comparator.")],
        [e265("test_h15_external", "test_h15_omitted"), e267("test_endpoint_access")])
], "All material H15 source-access clauses have identified assertions and retained outcomes, with comparator propagation.",
"Source lexical access and finite declaration association only; no endpoint pose or physical-access inference.")

group("H16", "Unsupported endpoint and joint source forms", [
    sub("Implicit origin, keyed traversal and deeper chains refuse as unsupported source forms",
        [a265("test_h16_unsupported_endpoint_expression_forms", "Actual results distinguish origin/keyed/deeper forms; shared helper forbids partial records."),
         a267("test_endpoint_access_and_unsupported_forms", "Comparator asserts exact UNSUPPORTED_SOURCE_FORM for origin, keyed and deeper forms.")],
        [execution("c265-source", indices=[62,63,64]), e267("test_endpoint_access")]),
    sub("A declared parameter, alias or computed SiteRef is refused as unsupported rather than silently substituted or dropped",
        [a265("test_h16_unsupported_endpoint_expression_forms", "Uses undeclared self.ref and site(self.pivot); allows either MALFORMED or UNSUPPORTED_SOURCE_FORM."),
         lines(265, "source_hinges.py", 518, 559, "Static path resolver requires a literal declared site; this is code inspection, not an executed typed SiteRef control.")],
        [execution("c265-source", indices=[66,67])], status="partial",
        gap="No independently authored, source-valid declared/computed SiteRef fixture and exact unsupported-form assertion was found. self.ref is undeclared and records MALFORMED; site(self.pivot) is not backed by a declared SiteRef producer. Do not count these as the missing typed/computed SiteRef control.",
        note="This is an evidence gap. The audit did not execute a new input or establish an implementation defect."),
    sub("Scene joint, non-hinge joint, inheritance, relation override and hidden/nested joint declarations refuse without omission",
        [a265("test_h16_nonhinge_scene_joint_and_inheritance_refuse", "Moves an actual declaration into a scene and changes hinge kind/inheritance; exact unsupported outcomes."),
         a265("test_h16_relation_override_and_nested_joint_refuse", "Actual relation override and nested declaration refuse."),
         lines(265, "evidence/review/run_review_controls.py", 48, 85, "Independent reviewer injects hidden joints into methods and scene action bodies."),
         lines(265, "evidence/review/run_review_controls.py", 103, 111, "Bare-CR hidden declaration refuses; CRLF retains complete original observations.")],
        [e265("test_h16_nonhinge", "test_h16_relation"), execution("c265-review", "nested_joint", "bare_cr", "ordinary_crlf")])
], "Origin/keyed/deeper/scene/non-hinge and declaration omission controls are supported; genuine declared/computed SiteRef refusal classification is unproven.",
"A valid language form outside this finite observer must remain distinguishable from malformed source. No source expansion or new control ran.")

group("H17", "Required fields, declaration ambiguity, collisions and shadowing", [
    sub("Each of the five source joint fields occurs exactly once; extra fields and missing explicit visibility refuse",
        [a265("test_h17_joint_fields_must_occur_exactly_once", "Loops through all five fields, independently deleting and duplicating each; adds unexpected field."),
         a265("test_h17_missing_joint_visibility_refuses", "Removes explicit joint visibility and requires refusal."),
         a265("refused", "Requires typed refusal, source identities and no qualified records.")],
        [e265("test_h17_joint_fields", "test_h17_missing")]),
    sub("Duplicated joint declarations and site/member name or key collisions refuse",
        [a265("test_h17_duplicate_names_keys_and_reserved_members_refuse", "Duplicates the declaration, collides joint lexical name and key with pivot, and shadows reserved members."),
         lines(265, "evidence/review/run_review_controls.py", 59, 62, "Independent part-key and implicit origin/frame member-key collisions."),
         lines(265, "evidence/review/run_review_controls.py", 77, 85, "Additional import/definition and root/action namespace collisions.")],
        [e265("test_h17_duplicate"), execution("c265-review", "joint_part_key_collision", "implicit_origin", "implicit_frame", "import_definition", "scene_root_action")]),
    sub("vec3/range constructors and resolver self/origin/frame names cannot be shadowed by consumed members or binders",
        [a265("test_h17_duplicate_names_keys_and_reserved_members_refuse", "Separately declares self, origin, frame, vec3 and range parameters."),
         lines(265, "evidence/review/run_review_controls.py", 59, 89, "Member vec3, imported range alias, nested vec3/self binders each independently refuse.")],
        [e265("test_h17_duplicate"), execution("c265-review", "constructor_member", "constructor_import", "nested_constructor", "nested_self")]),
    sub("Artifact missing/extra row fields and duplicate JSON fields refuse; absent/extra source-relative joint rows do not acquire agreement",
        [lines(261, "evidence/independent/independent_controls.py", 209, 212, "Deletes each actual joint field; extra direct definition field refuses."),
         lines(261, "evidence/independent/independent_controls.py", 270, 274, "Duplicate JSON key, duplicated initial field and duplicate ignored key refuse."),
         a267("test_complete_joint_set_and_duplicate_rows", "Missing/extra complete joint sets and duplicate IDs/paths refuse.")],
        [execution("c261-independent", "missing-joint-field", "extra-joint-field", "duplicate-joint-key", "duplicate-ignored-key"), e267("test_complete_joint_set")])
], "The source-field and namespace clauses are independently exercised; whole-set and artifact-field refusals corroborate the comparison boundary.",
"Source-only refusal produces no expected hinge set. Removing all joints from both otherwise supported inputs is a separately tested valid empty set, not an omission allowance.")

group("H18", "Site fields and source-only compatibility", [
    sub("Missing/duplicate pose, interface or size and extra site fields refuse",
        [a265("test_h18_site_required_fields_and_compatibility_refuse", "Deletes interface/size/pose, duplicates each, and adds an unexpected field.")],
        [e265("test_h18_site_required")]),
    sub("Empty/nonliteral interface, negative/parameterized/computed size, and unequal interfaces or sizes refuse",
        [a265("test_h18_site_required_fields_and_compatibility_refuse", "Independent literal and expression mutations require explicit whole typed refusal."),
         a267("test_source_compatibility_fields_refuse_when_unsupported_or_inconsistent", "Comparator propagates empty interface, negative/computed size, and unequal sizes before stale provenance can mask compatibility refusal.")],
        [e265("test_h18_site_required"), e267("test_source_compatibility")]),
    sub("Equal canonical lengths across cm/mm pass; pose expressions remain unevaluated source witnesses",
        [a265("test_h18_exact_length_conversion_and_pose_nonclaim", "12 cm and 120 mm have an independently calculated common size; pose flags remain false."),
         a267("test_nontrivial_source_site_pose_is_not_evaluated", "Nontrivial pose change passes independent expected hinge/site association checks without world claims.")],
        [e265("test_h18_exact_length"), e267("test_nontrivial_source_site_pose")])
], "Every material site field/compatibility and pose nonclaim clause has concrete assertion evidence.",
"Compatibility is literal interface and canonical size equality in source only. No artifact interface/size copy, pose evaluation or manufacturing fit is claimed.")

group("H19", "Actual keyed membership, opaque keys and invalid-key refusal", [
    sub("Nonempty membership reordering, insertion and deletion drive exact actual complete hinge identity sets",
        [a265("test_h19_actual_nonempty_membership_sets_and_opaque_keys", "Independently constructs expected IDs for reordered/deleted/inserted keys, not a fixed eight rows."),
         assertion(266, "test_changed_membership_and_opaque_keys", "Rebuilds independent complete object maps for four membership variants."),
         a267("test_membership_opaque_keys_rebinding_and_byte_offsets", "Changed complete source/artifact sets pass independent expected hinge maps.")],
        [e265("test_h19_actual_nonempty"), execution("c266-main", "test_changed_membership"), e267("test_membership_opaque")]),
    sub("Direct final owner override replaces the default; direct/helper default and helper override recipes remain distinct",
        [a265("test_h19_final_owner_override_controls_membership", "One direct final override yields only the independently named surviving key for the first owner."),
         assertion(266, "test_direct_helper_and_final_override_memberships", "Four independently authored membership recipes bind."),
         a267("test_membership_opaque_keys_rebinding_and_byte_offsets", "All four recipes compare with exact rebound provenance."),
         assertion(266, "test_duplicate_owner_override_remains_a_refusal", "Invalid duplicate same-scope override remains a separate negative control.")],
        [e265("test_h19_final_owner"), execution("c266-main", "test_direct_helper", "test_duplicate_owner"), e267("test_membership_opaque")]),
    sub("Dotted/underscored/hyphenated keys remain opaque and do not imply dotted path splitting or generator-order identity",
        [a265("test_h19_actual_nonempty_membership_sets_and_opaque_keys", "Checks opaque bracket rendering and full key-bearing IDs."),
         a267("test_membership_opaque_keys_rebinding_and_byte_offsets", "Uses one.a/two_a/three-a plus renamed modules, roots, classes and members; accept() checks full paths/IDs."),
         assertion(266, "test_full_input_entry_span_cannot_be_replaced_with_key_token", "Full keyed-entry witness cannot be replaced by key-only span.")],
        [e265("test_h19_actual_nonempty"), e267("test_membership_opaque"), execution("c266-main", "test_full_input_entry")]),
    sub("Empty input is unsupported; duplicated, Unicode, quote-containing, leading punctuation, space and overlength keys refuse",
        [a265("test_h19_empty_duplicate_and_invalid_keys_refuse", "Empty helper result asserts UNSUPPORTED_SOURCE_FORM; invalid input/declaration keys each refuse."),
         a265("test_h19_boundary_64_key_input_and_65_refusal", "64 keyed members admitted in a no-hinge fixture; 65 rejected as resource limit."),
         a265("test_h19_nested_membership_override_refuses", "Nested membership override refuses unsupported form."),
         a265("test_h19_private_membership_default_and_external_override", "Private internal default passes; external direct override refuses.")],
        [e265("test_h19_empty", "test_h19_boundary", "test_h19_nested", "test_h19_private")],
        note="The 64-key boundary fixture intentionally has no hinges/child parts to avoid the independent 128-object cap. It does not demonstrate 64 full historical Finger assemblies.")
], "Actual keys and override recipes drive independently specified source, object and comparison sets; invalid/empty boundaries are explicitly exercised.",
"No geometry from keyed values or helper arguments is evaluated. Original failed stale-reference/duplicate-override fixtures remain historical failures.")

group("H20", "Independence from unrelated source and ownership/follow/motion fields", [
    sub("Unrelated source geometry, original length and action/pose changes leave declared hinges unaffected",
        [a265("test_h20_h28_unrelated_geometry_length_pose_motion_do_not_supply_hinges", "Mutates geometry, length, frame parent, action and pose separately but uses field_projection(observer(original)) as the expected projection."),
         a267("test_original_before_after_exact_bytes", "Independent expected_joints recipe checks both actual original length-edit endpoints.")],
        [e265("test_h20_h28"), e267("test_original_before_after")], status="partial",
        gap="The standalone source geometry/action invariance expected projection is produced by the observer itself. Baseline H01 and original before/after comparisons supply independent baseline and length evidence, but no independently authored expected-field assertion was found for each changed geometry/action source control."),
    sub("Independent raw follow and motion metadata mutations retain exact supplied hinge fields",
        [lines(261, "evidence/independent/independent_controls.py", 67, 108, "Raw expected fields are independently decoded from actual bytes; all authority flags remain false."),
         lines(261, "evidence/independent/independent_controls.py", 247, 248, "Separate follows=[] and boundary_states=[] mutations preserve raw claims.")],
        [execution("c261-independent", "unrelated-follow-change", "unrelated-motion-change")]),
    sub("Unrelated ownership/follow/motion metadata is independently varied through comparison, with only explicit source-binding obligations allowed to refuse",
        [assertion(266, "test_unobserved_metadata_cannot_be_promoted_to_authority", "Bundled metadata mutation includes node owner/geometry and transforms; requires object binding only."),
         a267("test_absent_direct_provenance_and_unobserved_metadata", "Bundled comparison mutation uses meta['follow'] singular alongside owner, geometry, transforms and unrelated module/scene fields."),
         assertion(266, "test_nested_root_and_owner_paths_are_not_display_hints", "Actual consumed owner_path/root_path/generated ancestry mutations each refuse binding.")],
        [execution("c266-main", "test_unobserved_metadata", "test_nested_root"), e267("test_absent_direct")], status="partial",
        gap="No isolated comparison controls for the actual node owner, actual plural follows and actual motion fields were identified. Bundled owner mutation and singular follow field do not independently establish all three material nonclaim clauses. Raw follows/boundary_states controls remain valid raw evidence."),
    sub("Moving actual source ownership can refuse only on the consumed lexical endpoint/association requirement; no full-source or other-component pass is emitted",
        [a265("test_h20_h28_unrelated_geometry_length_pose_motion_do_not_supply_hinges", "Relocates blade away from the joint's direct owner and requires a typed refusal."),
         a267("accept", "All accepted comparisons retain false source-validity, pose, physical, rebuild and complete-C255 qualifications.")],
        [e265("test_h20_h28"), e267("test_absent_direct", "test_original_before_after")])
], "There is real source/raw/nonclaim evidence, but part of source invariance uses an implementation-derived expected projection and comparison metadata changes are not isolated on all actual fields.",
"A C266 binding success is not hinge agreement. A C261 raw success is not source truth. Full source/ownership/follow/motion validity stays unqualified.")

group("H21", "Complete joint/object sets and source association", [
    sub("Missing/extra/duplicate joint rows and crossed ID/path pairs refuse",
        [a267("test_complete_joint_set_and_duplicate_rows", "Remove one/all, add extra, wrong owner, duplicate ID and duplicate path; exact typed outcomes."),
         a267("test_complete_sets_do_not_hide_wrong_id_path_pairing", "Swaps IDs while retaining both complete sets; requires FIELD_MISMATCH.")],
        [e267("test_complete_joint_set", "test_complete_sets_do_not_hide")]),
    sub("Missing/extra/duplicate objects, incorrect class and wrong actual source spans refuse even when repeated artifact copies agree",
        [assertion(266, "test_missing_object_from_both_artifact_tables", "Deletes the same object from both artifact tables."),
         assertion(266, "test_extra_object_in_both_artifact_tables", "Adds a consistently repeated phantom object."),
         assertion(266, "test_duplicate_object_id_and_path", "Independent duplicate ID/path cases."),
         assertion(266, "test_every_repeated_provenance_leaf_node_program_and_both", "Mutates every independently expected leaf for root/generated/ordinary objects in either/both copies."),
         a267("test_binding_failure_cannot_be_hidden_by_equal_hinges", "Comparator refuses changed class/span, missing/duplicate objects despite equal hinges.")],
        [execution("c266-main", "test_missing_object", "test_extra_object", "test_duplicate_object", "test_every_repeated_provenance"), e267("test_binding_failure")]),
    sub("Joint-row, node and mapping reordering alone passes with exact relocated pointers",
        [a267("test_row_node_and_mapping_reordering_preserves_pointers", "Reverses rows/nodes/mapping insertion order; full independent expected comparison passes and first path moves to /joints/4/path."),
         lines(261, "evidence/independent/independent_controls.py", 197, 198, "Raw joint and node order are independently reversed in separate controls.")],
        [e267("test_row_node"), execution("c261-independent", "joint-order", "node-order")])
], "All required set/association and reorder subcases are independently constructed and executed; source-relative set agreement is established by the comparator, not the raw reader.",
"Raw zero/extra rows and C266 omitted hinges may be admitted only as untrusted/prerequisite results. Those nonclaim successes are not used as complete-set evidence.")

group("H22", "Source/program/repeated-provenance binding", [
    sub("Stale actual source hashes and stale import digest refuse; repinned changed source with stale artifact also refuses",
        [a265("test_h22_import_digest_must_bind_actual_companion_bytes", "Changed actual companion bytes require a new exact import pin."),
         assertion(266, "test_stale_source_bytes_and_dependency_pin", "Separately changes entry, leaf with stale pin, and repinned leaf with stale artifact."),
         a267("test_binding_failure_cannot_be_hidden_by_equal_hinges", "Stale source pin propagates INPUT_BINDING before any apparent hinge equality.")],
        [e265("test_h22_import"), execution("c266-main", "test_stale_source"), e267("test_binding_failure")]),
    sub("Missing actual import digest is explicitly controlled independently of general source truncation",
        [a265("test_h22_import_digest_must_bind_actual_companion_bytes", "This control changes leaf bytes and repins; it does not delete the import digest."),
         a265("test_h24_malformed_utf8_and_truncations_do_not_leak_host_exceptions", "Generic malformed/truncated source probes are not an isolated missing-digest case.")],
        [e265("test_h22_import", "test_h24_malformed")], status="partial",
        gap="No isolated source-import-digest removal control and retained outcome was found in inspected C257/C265/C266/C267/C268 tests/reviews. Static mandatory-digest parsing is not counted as an executed missing-digest control."),
    sub("Stale/missing/wrongly typed source/program entry IDs and revisions and all manifest/source-unit leaves refuse",
        [assertion(266, "test_entry_and_program_revisions_and_source_ids", "Each retained scalar gets stale, missing and wrong-type mutations."),
         assertion(266, "test_all_program_manifest_and_source_unit_claims", "Every independently constructed manifest/source-unit leaf is changed."),
         assertion(266, "test_sparse_and_unknown_program_manifest_source_units", "Every consumed dictionary member is removed; extra keys refuse."),
         assertion(266, "test_program_manifest_unit_order_is_canonical", "Reversed unit array refuses."),
         a265("test_h22_canonical_program_identity_comes_from_actual_bytes", "Canonical manifest and domain-separated revision are independently recomputed from supplied source bytes.")],
        [execution("c266-main", "test_entry_and_program", "test_all_program_manifest", "test_sparse_and_unknown_program", "test_program_manifest_unit"), e265("test_h22_canonical")]),
    sub("Repeated node/source mapping and definition claims must match source, including exact integer byte spans and complete dictionaries",
        [assertion(266, "test_every_repeated_provenance_leaf_node_program_and_both", "Both copies of each wrong expected leaf still refuse against source."),
         assertion(266, "test_every_mapping_member_is_required_in_each_copy", "Removes every nested mapping member from node/program/both."),
         assertion(266, "test_python_numeric_equality_does_not_admit_wrong_json_types", "Integral float span / integer-as-Boolean substitutions refuse."),
         assertion(266, "test_every_node_scalar_claim_against_source", "Node ID/path/class/revision cannot replace source authority."),
         assertion(266, "test_consistent_renaming_of_claimed_path_without_source_refuses", "Display-path agreement between artifact copies alone cannot authorize a rename.")],
        [execution("c266-main", "test_every_repeated_provenance", "test_every_mapping_member", "test_python_numeric", "test_every_node_scalar", "test_consistent_renaming")])
], "Extensive exact artifact/source-map and stale-pin evidence is present; a literal missing-import-digest source subcase is not identified, so the group is conservatively partial.",
"Top-level module/scene and program collections are explicitly unobserved by the retained interface and are not silently treated as verified fields. Generic malformed cases do not establish each targeted binding mutation.")

group("H23", "Absent direct artifact provenance remains absent", [
    sub("Original/raw artifact has no direct site table or joint/site definition/span fields; output never invents them",
        [lines(261, "evidence/independent/independent_controls.py", 67, 108, "Exact actual eight-field row and false direct-site/definition flags; no fabricated raw provenance."),
         a267("accept", "Every endpoint keeps source-only compatibility; artifactDefinitionId and artifactSpan absent; actual artifact origins resolve to supplied JSON."),
         a268("assert_semantics", "Historical wrapper also excludes artifactDefinitionId, artifactSpan and artifactPose.")],
        [execution("c261-independent", "original-before", "original-after"), e267("test_original_before_after"), e268("test_original_before_after")]),
    sub("Adding a direct site table or direct joint definition claim refuses rather than manufacturing authority",
        [lines(261, "evidence/independent/independent_controls.py", 209, 233, "Extra joint definition field and each selected sites-table location refuse."),
         a267("test_absent_direct_provenance_and_unobserved_metadata", "Added direct-site table refuses UNSUPPORTED_ARTIFACT_FORM."),
         a267("test_raw_glb_structural_duplicate_json_and_size_refusals", "Extra definition_id row field refuses.")],
        [execution("c261-independent", "extra-joint-field", "unsupported-direct-site"), e267("test_absent_direct", "test_raw_glb_structural")]),
    sub("Derived endpoint site IDs/definitions/spans remain labeled source facts even when site keys change without path change",
        [a267("test_site_names_and_derived_keys_remain_distinct", "Changed site keys retain artifact path authority but expose independently expected new source site IDs."),
         a267("accept", "source, artifactPath/artifactOrigin and bound object records remain separate.")],
        [e267("test_site_names_and_derived")])
], "Actual raw-claim assertions and source/comparison/historical nonclaim assertions support each absent-authority clause.",
"Absence refers to the finite consumed profile, not a proof that arbitrary unrelated GLB extensions contain no other data.")

group("H24", "Structural/resource refusals and whole-input failure", [
    sub("Truncated/misaligned/wrong-order GLB chunks, duplicate JSON keys, wrong JSON shapes and malformed UTF-8 refuse as typed outcomes",
        [lines(261, "evidence/independent/independent_controls.py", 262, 276, "Explicit header lengths/alignment/order, extra/missing BIN, duplicate keys and invalid JSON/UTF-8 cases."),
         a265("test_h24_malformed_utf8_and_truncations_do_not_leak_host_exceptions", "Malformed UTF-8/truncation in either source becomes Fault."),
         a267("test_raw_glb_structural_duplicate_json_and_size_refusals", "Raw structural and duplicate-key refusals propagate through comparator."),
         a267("refuse", "No qualified records; exact bounded available input hashes and byte counts survive refusal.")],
        [execution("c261-independent", "bad-glb", "bad-header", "missing-bin", "extra-bin", "bad-json", "duplicate-joint-key", "duplicate-ignored-key", "json-null", "invalid-utf8"), e265("test_h24_malformed"), e267("test_raw_glb_structural")]),
    sub("Excessive source bytes/tokens/depth/definitions, GLB/JSON bytes and JSON depth refuse before unbounded work",
        [a265("test_h24_source_bytes_tokens_depth_and_definitions_are_bounded", "Retained cases actually reach SOURCE byte, C257 TOKEN_LIMIT, SOURCE_DEPTH and DEFINITION_LIMIT guards."),
         lines(261, "evidence/independent/independent_controls.py", 277, 282, "JSON depth, JSON/GLB cap refusals and exact 2 MiB JSON admission."),
         a267("test_structural_source_and_numeric_bounds_propagate", "65537-byte source refuses and lacks an oversized diagnostic hash.")],
        [e265("test_h24_source_bytes"), execution("c261-independent", "json-depth", "json-byte-cap", "glb-byte-cap", "json-exact-cap"), e267("test_structural_source")]),
    sub("Too many source objects and hinge rows, and too many raw object/joint rows, produce resource refusals",
        [a265("test_h24_object_and_hinge_rows_are_bounded", "Actual results distinguish inherited OBJECT_LIMIT and the new 128-hinge guard."),
         lines(261, "evidence/independent/independent_controls.py", 203, 205, "0/1/127/128 raw joints admit; 129 refuses RESOURCE_LIMIT."),
         lines(261, "evidence/independent/independent_controls.py", 249, 251, "129 raw object rows refuse RESOURCE_LIMIT.")],
        [e265("test_h24_object_and_hinge"), execution("c261-independent", "changed-joint-count", "joint-count-129", "objects-129")]),
    sub("Exactly 128 hinges and 256 referenced source sites are admitted; an excessive-site input has its own retained refusal evidence",
        [a265("test_h24_exact_hinge_and_site_row_limits_are_admitted", "Independent 32-key/four-definition recipe asserts 128 unique hinges and 256 unique referenced sites."),
         lines(265, "source_hinges.py", 518, 543, "Static source-site cap exists, but is not an excessive-site execution."),
         lines(261, "hinge_glb.py", 239, 266, "At most 128 rows each contribute two endpoint path claims; site count cannot exceed 256 after the row guard.")],
        [e265("test_h24_exact_hinge")], status="partial",
        gap="No supplied input with more than 256 distinct referenced sites and its actual typed outcome was identified. The implemented 128-hinge/two-endpoint rule logically bounds sites, and the exact 256-site source admission is executed; neither is relabeled an executed excessive-site control. A future decision may accept this logical redundancy explicitly, or add a multi-limit 129-hinge/258-site refusal control without changing the contract."),
    sub("Text/identity limits, exact closure, recursion and wrong primitive/container types are bounded and typed",
        [a265("test_h24_exact_source_closure_and_bytes_only", "Missing/extra members and nonbyte source values refuse."),
         a265("test_h24_recursive_containment_and_consumed_text_refuse", "Recursive Finger containment and overlong/control/surrogate interfaces refuse."),
         lines(265, "evidence/review/run_boundaries.py", 58, 62, "Independent exact 32/33 site-ID and 512/513 rendered-path recipes."),
         lines(261, "evidence/independent/independent_controls.py", 217, 223, "Raw consumed text and identity boundaries, controls and surrogates."),
         assertion(266, "test_mapping_containers_require_their_actual_types", "Mapping/identity/path-step containers are independently mistyped.")],
        [e265("test_h24_exact_source", "test_h24_recursive"), execution("c265-boundaries", "site_identity", "site_path"), execution("c261-independent", "text-", "text-scalar", "identity-shape", "identity-32"), execution("c266-main", "test_mapping_containers")])
], "Structural and major resource guards have exact retained typed outcomes. The explicitly listed excessive-site control is not executed; the known mathematical redundancy is recorded separately.",
"No host-exception or partial-result claim extends beyond the actual controls. C257 bounds are credited only where the C265 run records the specific inherited guard reached.")

group("H25", "Bounded numeric lexemes, exponents, overflow and underflow", [
    sub("Long lexemes and explicit exponents beyond +/-400 refuse, including zero; raw 64-character boundary is admitted",
        [a265("test_h25_numeric_lexeme_and_explicit_exponent_limits", "65-character source token and 0/nonzero exponent +/-401 refuse RESOURCE_LIMIT."),
         a265("test_h25_adjusted_exponent_overflow_and_underflow", "0e400/0e-400 are admitted as exact zero."),
         lines(261, "evidence/independent/independent_controls.py", 283, 291, "Independent raw 64/65-character, large exponent and zero-boundary controls."),
         lines(265, "source_hinges.py", 116, 138, "Lexeme-length/exponent guards precede bounded Fraction construction and binary64 conversion."),
         lines(261, "hinge_glb.py", 80, 95, "JSON lexeme/exponent and adjusted bounds precede int/float conversion.")],
        [e265("test_h25_numeric", "test_h25_adjusted_exponent_overflow"), execution("c261-independent", "numeric-token-")]),
    sub("Adjusted exponent is enforced after the exact unit factor; finite upper values, overflow, subnormal and rounded-zero lower boundary follow policy",
        [a265("test_h25_adjusted_exponent_overflow_and_underflow", "1e-325 rad and 1e-323 deg refuse; 1e309 rad and 1.8e308 rad refuse; 1e-324 rad gives zero, 5e-324 gives smallest subnormal."),
         a265("test_h25_adjusted_exponent_applies_after_unit_factor", "1e309 deg limits and 1e310 mm sizes pass independently calculated scaled values."),
         lines(261, "evidence/independent/independent_controls.py", 283, 291, "Raw 1e308 and largest finite decimal pass; next overflowing decimal refuses; underflow edges are retained exactly.")],
        [e265("test_h25_adjusted"), execution("c261-independent", "numeric-token-")]),
    sub("The same literal policy is used by the comparator and no tolerance repairs a boundary disagreement",
        [a267("test_structural_source_and_numeric_bounds_propagate", "Long source numeric/exponent cases propagate RESOURCE_LIMIT."),
         a267("test_exact_deg_rad_negative_zero_and_adjacent_values", "Independent rational deg/rad expectations, adjacent binary64 and smallest subnormal mismatch controls.")],
        [e267("test_structural_source", "test_exact_deg_rad")])
], "Material length/exponent/adjusted-unit/finite-overflow/underflow cases have independent assertions and exact results; static guard ordering corroborates bounded conversion.",
"This is the declared literal/binary64 policy only. No benchmark, universal numeric accuracy, general computed expression or alternative Python/platform guarantee is inferred.")

group("H26", "Historical bounded file admission and I/O refusal", [
    sub("Missing input, wrong expected size and same-size wrong hash are rejected for every selected source/GLB file and endpoint",
        [a268("test_missing_each_selected_input", "Both endpoints and each required source/GLB path yield IO_ERROR/MISSING."),
         a268("test_wrong_size_each_input_is_refused_before_payload_read", "Short/long cases install an os.read spy; no payload read/hash occurs before INPUT_SIZE."),
         a268("test_same_size_changed_bytes_each_input", "Same-size byte changes yield HISTORICAL_BINDING/HASH with measured hash."),
         a268("test_no_comparison_before_all_historical_files_admitted", "Explicit comparison spy must remain uncalled for each failed admission.")],
        [e268("test_missing_each", "test_wrong_size_each", "test_same_size_changed", "test_no_comparison_before")]),
    sub("Symlink leaves, ancestor directories, root/above-root symlinks and leaf/ancestor loops refuse before outside bytes can authorize admission",
        [a268("test_symbolic_link_each_input_leaf_refuses_even_exact_target", "Each selected leaf links to exact outside bytes but still refuses INPUT_PATH/SYMLINK."),
         a268("test_symbolic_link_ancestor_inside_repository", "Fixed proof ancestor moved outside root and linked back refuses."),
         a268("test_symbolic_link_repository_root", "Symlink root refuses."),
         a268("test_symbolic_link_above_repository_root", "Symlink above root refuses."),
         a268("test_leaf_and_ancestor_symbolic_link_loops", "Actual self-referencing leaf and ancestor symlinks refuse.")],
        [e268("test_symbolic_link", "test_leaf_and_ancestor")]),
    sub("Escaping roots/selectors and path/resource-invalid arguments refuse with no file access",
        [a268("test_escape_invalid_root_types_and_resource_bounds_access_no_files", "Parent traversal, ambiguous roots, invalid Unicode/types and path caps use open/stat spies."),
         a268("test_invalid_endpoint_refuses_without_filesystem_access", "Invalid selector types and traversal strings cannot reach filesystem."),
         a268("test_overlong_endpoint_refuses_before_pin_lookup", "100006-character selector cannot reach pin lookup or filesystem."),
         lines(268, "endpoint_reader.py", 90, 119, "Static root/child component validation precedes descriptor traversal.")],
        [e268("test_escape_invalid", "test_invalid_endpoint", "test_overlong_endpoint")]),
    sub("Actual permission denial plus injected permission/read/stat failures normalize to typed whole-input outcomes",
        [a268("test_permission_refusal_with_explicit_oserror_injection", "Latest run reports actual mode-000 denial at UID1000; EACCES open/read injections separately assert IO_ERROR/PERMISSION."),
         a268("test_injected_fstat_and_read_oserrors_are_typed", "EIO injection separately exercises fstat/read translation."),
         a268("refuse", "Refusal has bounded diagnostics, no records or historicalAdmission, and bounded available identities.")],
        [e268("test_permission_refusal", "test_injected_fstat")],
        note="The actual permission outcome is /notes/0 of the identified latest result: actualPermissionDenial=true, effectiveUid=1000. Injection is distinguished from real OS denial."),
    sub("Reads stay bounded under wrong size, sparse oversize, shrink/growth and nonregular input; no ambient/network fallback or partial comparison",
        [a268("test_large_sparse_wrong_size_is_never_read_or_hashed", "Oversized sparse source/GLB paths refuse without payload read/hash."),
         a268("test_truncation_after_size_check_is_bounded_and_never_compared", "Injected shrink yields bounded short-read refusal and forbidden comparison."),
         a268("test_growth_after_size_check_is_bounded_and_never_compared", "Injected pre-read growth yields GROWN refusal and forbidden comparison."),
         a268("test_growth_after_read_is_detected_by_final_metadata_check", "Post-read growth also refuses."),
         a268("test_fifo_input_refuses_without_hanging", "Actual no-writer FIFO tested with a five-second subprocess deadline; nonregular refusal."),
         a268("test_nonregular_directory_at_each_input_path", "Each selected input replaced with directory refuses."),
         lines(268, "endpoint_reader.py", 147, 209, "Static nofollow descriptor-relative read uses exact size gate, one size+1 read, hash and final metadata check; no fallback path."),
         lines(268, "endpoint_reader.py", 252, 302, "Only fixed selected paths are captured before dependency capture and finite comparison; typed exception translation retains no qualified subset.")],
        [e268("test_large_sparse", "test_truncation_after", "test_growth_after", "test_fifo_input", "test_nonregular_directory")],
        note="POSIX/Linux execution only. Fresh dependency capture and per-call checks are wrapper prerequisites; no C257 historical reader or live filesystem snapshot authority is assumed.")
], "All named H26 missing/size/hash/symlink/loop/escape/permission cases have actual historical-reader results; additional read-race/nonregular controls and static access review support bounded refusal.",
"Original historical bytes only, exact captured dependency closure and finite comparator. Not accepted-revision authentication, restoration, source execution or platform-wide filesystem certification.")

group("H27", "Supported changed raw inputs preserve authority boundaries", [
    sub("Supported same-size paired axis and different-size paired initial changes are independently specified and inspectable through all first three APIs",
        [lines(268, "endpoint_control_fixtures.py", 134, 180, "Changes actual source/import pins/program provenance and actual GLB fields, then independently assigns expected axis or initial."),
         a268("exercise_changed_pair", "Calls source, artifact and comparison APIs; compares changed fields and complete independently specified associations."),
         a268("test_supported_same_size_paired_axis_change_stays_raw_only", "Executes same-size recipe."),
         a268("test_supported_different_size_paired_initial_change_stays_raw_only", "Executes different-size recipe.")],
        [e268("test_supported_same_size", "test_supported_different_size")]),
    sub("Raw historical flag and unrelated qualification flags remain absent/false; only the exact original historical reader can label admission",
        [a268("raw_call", "Every successful raw API has historicalInputsBound=false and no accepted/source-validity/pose/execution/complete-C255 authority."),
         a268("exercise_changed_pair", "Installs changed actual bytes and isolates failed historical admission at main, leaf and GLB stages."),
         a265("test_h27_changed_supported_inputs_never_gain_historical_authority", "Changed initial and keyed membership yield seven hinges with direct expected values and false nonqualification flags.")],
        [e268("test_supported_same_size", "test_supported_different_size"), e265("test_h27_changed")]),
    sub("Artifact-only supported field change remains a visible raw claim but comparison and historical authority refuse",
        [a268("test_artifact_only_initial_change_remains_visible_but_unbound", "Initial 0.5 is actually visible, FIELD_MISMATCH at raw comparison and historical HASH refusal are separately executed.")],
        [e268("test_artifact_only_initial")])
], "Changed supplied source/artifact bytes are tested through all three raw interfaces with independent expected values and explicit false authority; historical refusal is separate.",
"No accepted revision, source validity, pose evaluation, native/model trial, physical validity or complete-C255 qualification follows from changed-input comparison.")

group("H28", "Pose/geometry/motion remain outside declaration agreement", [
    sub("A nontrivial actual source pose change leaves independent hinge fields and endpoint associations equal while world/physical flags remain false",
        [a267("test_nontrivial_source_site_pose_is_not_evaluated", "Real source translation becomes (999,-123,0) and quaternion becomes (0,1,0,0); fixture rebinding changes actual source/provenance, while expected hinges remain independently authored."),
         a267("accept", "Complete equality and every pose/direct-authority/physical/world/rebuild nonclaim is asserted."),
         lines(265, "evidence/review/run_review_controls.py", 91, 94, "Separate reviewer retains a -length/3 plus 7m site pose witness without evaluating it.")],
        [e267("test_nontrivial_source_site_pose"), execution("c265-review", "nontrivial_unevaluated_pose")]),
    sub("Unrelated raw motion/geometry and comparison transforms never become measurements of world alignment or physical validity",
        [lines(261, "evidence/independent/independent_controls.py", 247, 248, "Actual raw boundary_states change keeps supplied hinge claims only."),
         a267("test_absent_direct_provenance_and_unobserved_metadata", "Changed geometry/translation remains outside finite agreement."),
         a268("test_comparison_records_and_nonclaims_preserved", "Historical wrapper preserves comparator records and all limits except the explicitly replaced historical-admission sentence.")],
        [execution("c261-independent", "unrelated-motion-change"), e267("test_absent_direct"), e268("test_comparison_records")],
        note="These are executed nonclaim controls, not tests validating physics or motion. H20's stricter independent-mutation completeness remains separately partial.")
], "An independently specified nontrivial source-pose comparison directly establishes the H28 declaration-only boundary; historical wrapper preserves that boundary.",
"No endpoint world alignment, physical validity, motion/cycle/action semantics, general geometry or full product qualification is claimed.")


def verify_retained():
    receipt = data(MAIN + "CHECKS.json")
    check("actual-main source revision", receipt["source_before"]["commit"] == EXEC_REV)
    check("actual-main source stable", receipt["source_before"]["commit"] == receipt["source_after"]["commit"] and receipt["input_identity_unchanged"])
    check("actual-main cohort recorded successful", receipt["passed"] and receipt["complete"])
    failures = []
    for row in receipt["input_files_before"]:
        raw = git_bytes(EXEC_REV, row["path"])
        if raw is None or len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
            failures.append(row["path"])
    check("historical receipt inputs against its execution Git revision", not failures,
          checked_files=len(receipt["input_files_before"]), failures=failures)
    failures = []
    for row in receipt["output_files"]:
        path = MAIN + row["path"]
        got = identity(path)
        if (got["bytes"],got["sha256"]) != (row["bytes"],row["sha256"]):
            failures.append(path)
    check("retained actual-main output identities", not failures, checked_files=len(receipt["output_files"]), failures=failures)
    critical = [C[257] + "ownership.py", C[260] + "CONTRACT.md", C[260] + "CONTROL-PLAN.md", C[260] + "INPUTS.json", C[253] + "corpus.json"]
    for n, names in {261: ("hinge_glb.py","test_hinge_glb.py"),265: ("source_hinges.py","test_source_hinges.py"),
                     266: ("hinge_binding.py","test_hinge_binding.py","binding_control_fixtures.py"),
                     267: ("hinge_compare.py","test_hinge_compare.py","comparison_control_fixtures.py"),
                     268: ("endpoint_reader.py","test_endpoint_reader.py","endpoint_control_fixtures.py")}.items():
        critical.extend(C[n]+name for name in names)
    for name in ("before.main.ok","after.main.ok","hinges.ok","before.glb","after.glb"):
        critical.append(P + "semantic-export-c210/evidence/proof/" + name)
    for path in critical:
        actual = read(path)
        check("exact reused scientific input", actual == git_bytes(BASE,path) == git_bytes(EXEC_REV,path), path=path)
    for run, r in RUNS.items():
        report=r["report"]
        rows=report[r["array"]]
        success=report.get("failed",0)==0 and report.get("failures",0) in (0,[]) and report.get("errors",0) in (0,[])
        check("retained execution success", success, run=run, cases=len(rows))
        if run == "c265-source":
            for path, expected in report["inputs"].items():
                got=identity(path)
                check("source run exact code binding", got["bytes"]==expected["bytes"] and got["sha256"]==expected["sha256"], path=path)
        if run.startswith("c265-") and run != "c265-source":
            source=identity(C[265]+"source_hinges.py")
            control=C[265]+"evidence/review/"+("run_boundaries.py" if run.endswith("boundaries") else "run_review_controls.py")
            check("review exact code binding",source["sha256"]==report["implementation_sha256"] and identity(control)["sha256"]==report["control_sha256"],run=run)
            failures=[]
            for row in rows:
                for name, expected in row["inputs"].items():
                    path=str(Path(r["result_path"]).parent / "inputs" / row["case"] / name)
                    got=identity(path)
                    if (got["bytes"],got["sha256"])!=(expected["bytes"],expected["sha256"]): failures.append(path)
            check("review retained input files",not failures,run=run,checked_files=2*len(rows),failures=failures)
        if run.endswith("-main"):
            for path, expected in report["implementationAndControlInputs"].items():
                got=identity(path)
                check("main-run exact code binding",(got["bytes"],got["sha256"])==(expected["bytes"],expected["sha256"]),run=run,path=path)
            archive_path=str(Path(r["result_path"]).parent / "inputs.zip")
            read(archive_path)
            with zipfile.ZipFile(ROOT/archive_path) as archive:
                check("input archive CRC", archive.testzip() is None, run=run)
                failures=[]
                for name in archive.namelist():
                    raw=archive.read(name)
                    if hashlib.sha256(raw).hexdigest()!=name.split('.')[0]: failures.append(name)
                check("input archive content-address hashes",not failures,run=run,members=len(archive.namelist()),failures=failures)
                witness_count=0
                def walk(v):
                    nonlocal witness_count
                    if isinstance(v,dict):
                        if "snapshot" in v and "bytes" in v and "sha256" in v:
                            raw=archive.read(v["snapshot"].split('!',1)[1]); witness_count+=1
                            assert (len(raw),hashlib.sha256(raw).hexdigest())==(v["bytes"],v["sha256"])
                        if "frozenReference" in v:
                            raw=read(v["frozenReference"]); witness_count+=1
                            assert (len(raw),hashlib.sha256(raw).hexdigest())==(v["bytes"],v["sha256"])
                        for x in v.values(): walk(x)
                    elif isinstance(v,list):
                        for x in v: walk(x)
                walk(rows)
                check("case input witnesses resolve",True,run=run,witnesses=witness_count,
                      note="Filesystem absence/symlink/FIFO/injected-event recipes are retained separately; they are not represented as stored file payloads.")
    binding=data(C[261]+"evidence/independent/SOURCE-BINDING.json")
    check("C261 independent exact source/control/result binding",
          identity(C[261]+"hinge_glb.py")["sha256"]==binding["readerSha256"] and
          identity(C[261]+"evidence/independent/independent_controls.py")["sha256"]==binding["controlsSha256"] and
          identity(C[261]+"evidence/independent/run-03/RESULTS.json")["sha256"]==binding["reportSha256"])
    notes=RUNS["c268-main"]["report"]["notes"]
    check("H26 actual OS permission denial retained",any(x.get("actualPermissionDenial") is True and x.get("effectiveUid")==1000 for x in notes),notes=notes)


def main():
    verify_retained()
    supplemental=["AGENTS.md","GOAL.md","ROLE.md","docs/workflow/PROTOCOL.md","docs/workflow/HANDOFF.md",
                  ".agents/skills/ontokin-delivery/SKILL.md", "docs/workflow/tasks/C269/REQUIREMENTS.md", "docs/workflow/tasks/C269/PLAN.md"]
    for n in (261,265,266,267,268):
        supplemental.extend(C[n]+x for x in ("README.md","RESULTS.md"))
    supplemental.extend([
        C[261]+"CONTROL-COVERAGE.md", C[261]+"evidence/independent/REVIEW.md",
        C[265]+"evidence/independent-controls/CONTROL-COVERAGE.json", C[265]+"evidence/review/REVIEW.md",
        C[265]+"evidence/review/REVIEW.json", C[266]+"CONTROL-COVERAGE.md", C[266]+"evidence/review/REVIEW.md",
        C[267]+"CONTROL-COVERAGE.md", C[267]+"REVIEW.md", C[268]+"CONTROL-COVERAGE.md", C[268]+"REVIEW.md",
        C[268]+"evidence/finalization-20261119/review/REVIEW.md",
        C[265]+"evidence/independent-controls/run-01/results.json", C[265]+"evidence/review/run-01/RESULTS.json",
        C[266]+"evidence/independent-controls/run-01/results.json",
        C[261]+"evidence/independent/run-01/RESULTS.json",
        C[257]+"test_ownership.py", C[266]+"evidence/review/review_c266.py",
    ])
    for path in supplemental: read(path)
    assertion_count=sum(len(s["source_assertions"]) for g in GROUPS for s in g["required_subcases"])
    execution_refs=sum(len(s["execution_evidence"]) for g in GROUPS for s in g["required_subcases"])
    check("complete assigned H-group inventory", [g["id"] for g in GROUPS]==[f"H{i:02}" for i in range(15,29)],groups=len(GROUPS))
    check("every complete subcase has assertion and retained execution references",all(s["source_assertions"] and s["execution_evidence"] for g in GROUPS for s in g["required_subcases"] if s["status"]=="complete"),assertion_references=assertion_count,execution_reference_sets=execution_refs)
    identities=[]
    for path in sorted(SEEN):
        row=identity(path)
        revision=SCOPE_REV if path.startswith("docs/workflow/tasks/C269/") else BASE
        raw=git_bytes(revision,path)
        row.update(revision=revision,git_blob_available=raw is not None,working_bytes_match_revision=raw==read(path),
                   inspection="Exact byte identity and relevant cited assertions/results or governing text inspected; not a claim every uncited line was semantically reviewed.")
        identities.append(row)
    check("inspected files match their immutable input revision",all(x["working_bytes_match_revision"] for x in identities),files=len(identities),
          failures=[x["path"] for x in identities if not x["working_bytes_match_revision"]])
    runs={}
    for key,r in RUNS.items():
        entry={k:v for k,v in r.items() if k!="report"}
        report=r["report"]
        entry.update({k:report[k] for k in ("command","python","platform","machine","startedAt","completedAt","createdUTC","observed_at","effectiveUid","inputs","implementationAndControlInputs","implementationSha256","implementation_sha256","control_sha256","dependency_sha256") if k in report})
        entry["retained_case_count"]=len(report[r["array"]])
        entry["execution_classification"]="historical retained execution; not run in C269"
        if key=="c261-independent":
            entry["original_command_from_review"]="python3 worker_results/independent-review/independent_controls.py OntoKin worker_results/independent-review/run-03"
            entry["input_retention"]="Original GLBs and deterministic fixture editor retained; per-mutant size/hash in results. Mutated GLB payloads are not separately stored and were not regenerated in this audit."
        elif key=="c265-source":
            entry["input_retention"]="Per-call source byte counts/hashes and exact recipe/test snapshots retained. Most generated source payloads are not separately stored in broad run-06; focused reviewer inputs are retained as files."
        runs[key]=entry
    summary={"schema":"ontokin.c269.h15-h28.audit-inspection/0.1","audit_input_revision":BASE,
             "created_utc":datetime.now(timezone.utc).isoformat(),"auditor":"/root/audit_h15_h28",
             "command":[sys.executable,"-B",str(Path(__file__).resolve())],"python":sys.version,"platform":platform.platform(),
             "behavioral_runs_executed":0,"checks":CHECKS,"passed":all(x["passed"] for x in CHECKS),
             "classification_counts":dict(Counter(g["status"] for g in GROUPS)),
             "unknown_operations":[],"boundary":"Read-only identity/result/AST/archive inspection only. No observer import, control rerun, implementation edit, source execution, exporter, native application or model trial."}
    outputs={"MAP.json":{"schema":"ontokin.c269.h15-h28.coverage-map/0.1","audit_input_revision":BASE,"contract_version":"0.1.0",
                         "classification_policy":"Complete means every material listed subcase has identified independent assertions and retained outcomes. This is an audit judgment, not newly executed qualification.",
                         "execution_registry":"EXECUTION-INDEX.json","groups":GROUPS},
             "INPUT-IDENTITIES.json":{"schema":"ontokin.c269.inspected-input-identities/0.1","audit_input_revision":BASE,"files":identities},
             "EXECUTION-INDEX.json":{"schema":"ontokin.c269.retained-execution-index/0.1","runs":runs},
             "INSPECTION-RESULTS.json":summary}
    for name,value in outputs.items():
        (OUT/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"passed":summary["passed"],"checks":len(CHECKS),"input_files":len(identities),"groups":summary["classification_counts"],"behavioral_runs_executed":0}))
    return 0 if summary["passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
