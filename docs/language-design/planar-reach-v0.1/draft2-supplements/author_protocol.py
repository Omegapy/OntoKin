"""NEW reconstruction of retained LP01-LP05 semantic requirements.

No requests are executed here. Symbolic bindings must be resolved from real
responses by the future acceptance driver. Historical row bytes were lost;
these are newly fixed, concrete requirements, not recovered execution logs.
"""
import copy
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def build(original, lifecycle):
    cases = {**original, **lifecycle}
    rev = lambda case: cases[case]["program_revision"]

    def request(group, number, operation, **fields):
        return {"schema_version": "ontokin.agent/0.6", "project_id": "reach-reconstruction-" + group.lower(),
                "request_id": group + "." + str(number).zfill(2), "operation": operation, **fields}

    def inspect(group, number, case, run=None, time=None, fields=None, selector=None, limit=128, **extra):
        values = {"program_revision": rev(case), "selector": selector if selector is not None else {"kind": "action"},
                  "fields": fields or ["actions"], "limit": limit, **extra}
        if run is not None:
            values["run_id"] = {"$binding": run}
        if time is not None:
            values["time"] = {"seconds": time[0], "side": time[1]}
        return request(group, number, "inspect", **values)

    def create(group, number, case, level):
        return request(group, number, "create", bundle={"$fixture_bundle": case},
                       expected_program_revision=None, requested_level=level)

    def patch(case, old, new, identity):
        base = HERE if case in lifecycle else PROPOSAL
        source = (base / cases[case]["entry_source"]).read_bytes()
        assert source.count(old.encode()) == 1, (case, old)
        start = source.index(old.encode())
        return {"source_id": "entry", "source_revision": sha(source), "element_id": identity,
                "start_byte": start, "end_byte": start + len(old.encode()), "expected_text": old, "replacement": new}

    def edited_bytes(case, change):
        base = HERE if case in lifecycle else PROPOSAL
        source = (base / cases[case]["entry_source"]).read_bytes()
        return source[:change["start_byte"]] + change["replacement"].encode() + source[change["end_byte"]:]

    root_id = ["planar-reach-fixture", "demo", "rig"]
    repair = patch("P13", 'arms["first"].forearm_length = 1[m];', 'arms["first"].forearm_length = 1.5[m];', root_id)
    limit_repair = patch("N06", "arm.elbow_high = 60[deg];", "arm.elbow_high = 90[deg];", root_id)
    limit_failure = patch("P10", "arm.elbow_high = 90[deg];", "arm.elbow_high = 60[deg];", root_id)
    for source, change, target in [("P13", repair, "P20"), ("N06", limit_repair, "P10"), ("P10", limit_failure, "N06")]:
        assert edited_bytes(source, change) == (PROPOSAL / cases[target]["entry_source"]).read_bytes()

    groups = []

    def group(identifier, name, scope, steps):
        output = {"id": identifier, "name": name, "scope": scope, "steps": []}
        for index, (title, req, expected, bindings) in enumerate(steps, 1):
            output["steps"].append({"id": identifier + "." + str(index).zfill(2), "name": title,
                "request_template": req, "expected": expected, "capture_bindings": bindings,
                "execution_status": "not_executed"})
        groups.append(output)

    def row(title, req, expected, **bindings):
        return title, req, expected, bindings

    group("LP01", "Failed handoff prefix, reset and new run", "L04 unchanged source throughout; no export in these nine steps", [
        row("Accept L04 construction", create("LP01", 1, "L04", "constructed"),
            {"status": "succeeded", "accepted_program_revision": rev("L04"), "admission_not_run": True}),
        row("Fail whole handoff boundary", request("LP01", 2, "evaluate", program_revision=rev("L04"), run_id=None, until_seconds="2"),
            {"status": "rejected", "run_status": "failed", "reach_code": "reach_unreachable", "valid_until_seconds": "0.5", "valid_until_side": "before", "no_new_artifact": True},
            failed_run="response.run_id", failure_receipt="complete immutable terminal response"),
        row("Inspect incoming failed boundary", inspect("LP01", 3, "L04", "LP01.failed_run", ("0.5", "before")),
            {"status": "succeeded", "expected_sample": "L04@0.5:before", "reach_a": "running with both original claims", "reach_b": "pending with null admission fields"}),
        row("Reject failed after-side", inspect("LP01", 4, "L04", "LP01.failed_run", ("0.5", "after")),
            {"status": "rejected", "diagnostic_code": "OKL-E-SAMPLE", "no_fabricated_state": True}),
        row("Reject later sample", inspect("LP01", 5, "L04", "LP01.failed_run", ("0.75", "after")),
            {"status": "rejected", "diagnostic_code": "OKL-E-SAMPLE", "no_fabricated_state": True}),
        row("Reject continuation of failed run", request("LP01", 6, "evaluate", program_revision=rev("L04"), run_id={"$binding": "LP01.failed_run"}, until_seconds="1"),
            {"status": "rejected", "diagnostic_code": "OKL-E-SAMPLE", "old_failure_unchanged": True}),
        row("Reset unchanged accepted L04", request("LP01", 7, "reset", program_revision=rev("L04")),
            {"status": "succeeded", "program_revision": rev("L04"), "old_run_preserved": True, "new_run_identity": True,
             "valid_until_seconds": "0", "valid_until_side": "before"}, reset_run="response.run_id"),
        row("Evaluate valid prefix on reset run", request("LP01", 8, "evaluate", program_revision=rev("L04"), run_id={"$binding": "LP01.reset_run"}, until_seconds="0.25"),
            {"status": "succeeded", "same_run_as": "LP01.reset_run", "program_revision": rev("L04"), "valid_until_seconds": "0.25", "valid_until_side": "after"}, prefix_run="response.run_id"),
        row("Inspect fresh prefix state", inspect("LP01", 9, "L04", "LP01.prefix_run", ("0.25", "after")),
            {"status": "succeeded", "expected_sample": "L04@0.25:after", "old_failure_unchanged": True}),
    ])

    wrong_generated = {**repair, "element_id": root_id + ["arms", "first"]}
    wrong_property = {**repair, "element_id": root_id + ["arms", "first", "forearm-length"]}
    repaired_request = request("LP02", 5, "edit", expected_program_revision=rev("P13"), patches=[repair], requested_level="evaluated")
    group("LP02", "Writable root initializer, retry and immutable history", "Exact P13 to P20 change; four untouched siblings and all library bytes preserved", [
        row("Create evaluated keyed rack", create("LP02", 1, "P13", "evaluated"), {"status": "succeeded", "accepted_program_revision": rev("P13")}, old_run="response.run_id"),
        row("Inspect actual initializer authority", inspect("LP02", 2, "P13", "LP02.old_run", ("1.5", "after"),
            fields=["identity", "source", "values"], selector={"path": 'rig.arms["first"].forearm_length'}),
            {"status": "succeeded", "initializer_target_available": True, "initializer_target_element_id": root_id,
             "rendered_path": 'arms["first"].forearm_length', "patch_source_id": "entry", "patch_source_revision": repair["source_revision"], "expected_patch": repair},
            writable_authority="actual returned source.initializer_target"),
        row("Reject generated occurrence authority", request("LP02", 3, "edit", expected_program_revision=rev("P13"), patches=[wrong_generated], requested_level="evaluated"),
            {"status": "rejected", "diagnostic_code": "OKL-E-REVISION", "category": "conflict", "phase": "edit", "accepted_program_revision": rev("P13"), "source_unchanged": True, "reason": "generated occurrence has no writable root initializer span"}),
        row("Reject property identity authority", request("LP02", 4, "edit", expected_program_revision=rev("P13"), patches=[wrong_property], requested_level="evaluated"),
            {"status": "rejected", "diagnostic_code": "OKL-E-REVISION", "category": "conflict", "phase": "edit", "accepted_program_revision": rev("P13"), "source_unchanged": True, "reason": "property inspection identity is not the writable root occurrence identity"}),
        row("Apply inspected root initializer repair", repaired_request,
            {"status": "succeeded", "accepted_program_revision": rev("P20"), "exact_target_fixture": "P20", "libraries_byte_identical": True,
             "authority_must_equal_actual_inspected_target": True}, new_run="response.run_id", edit_receipt="complete immutable terminal response"),
        row("Retry identical canonical request", copy.deepcopy(repaired_request),
            {"status": "succeeded", "canonical_request_identical_to": "LP02.05", "receipt_equals": "LP02.edit_receipt", "no_second_edit_or_run": True}),
        row("Recover outcome by status", request("LP02", 7, "status", target_request_id="LP02.05"),
            {"status": "succeeded", "target_terminal_response_equals": "LP02.edit_receipt", "no_second_edit_or_run": True}),
        row("Inspect retained original revision and run", inspect("LP02", 8, "P13", "LP02.old_run", ("1.5", "after"), fields=["identity", "source", "actions"]),
            {"status": "succeeded", "program_revision": rev("P13"), "accepted_program_revision": rev("P20"), "original_P13_values": True,
             "historical_run_unchanged": True, "four_sibling_values_and_ids_unchanged": True, "libraries_byte_identical": True}),
        row("Inspect repaired sampled rack", inspect("LP02", 9, "P20", "LP02.new_run", ("1.5", "after"), fields=["identity", "source", "actions"]),
            {"status": "succeeded", "program_revision": rev("P20"), "accepted_program_revision": rev("P20"), "exact_P20_targets_and_coordinates": True,
             "four_sibling_values_and_ids_unchanged": True, "libraries_byte_identical": True}),
    ])

    # Sibling/source preservation is already part of the retained LP02 scope.
    # Spell out its bounded evidence reads instead of assuming one oversized or
    # truncated all-records query can establish it. These are actual operations
    # to log within the corresponding semantic requirement, not new LP rows.
    for step_number, source_case, run_binding in [(8,"P13","LP02.old_run"),(9,"P20","LP02.new_run")]:
        step = groups[1]["steps"][step_number-1]
        evidence = []
        for n in range(1,5):
            sibling_path = 'rig.arms["part-' + str(n).zfill(2) + '"].forearm_length'
            query = inspect("LP02", step_number, source_case, run_binding, ("1.5","after"),
                            fields=["identity","source","values"], selector={"path":sibling_path}, limit=1)
            query["request_id"] += ".sibling-" + str(n)
            evidence.append({"request_template":query,"expected":{"status":"succeeded","returned_item_count":1,
                "canonical_length_m":1.0,"same_nominal_identity_across_edit":True,"source_library_revision_unchanged":True}})
        query = inspect("LP02", step_number, source_case, fields=["identity","source"], selector={"kind":"source"}, limit=4)
        query["request_id"] += ".sources"
        evidence.append({"request_template":query,"expected":{"status":"succeeded","returned_item_count":4,
            "exact_source_unit_identities":cases[source_case]["source_units"],"libraries_byte_identical":True}})
        step["required_evidence_reads"] = evidence

    group("LP03", "Accepted construction can fail admission and be repaired", "N06 accepted at constructed level; limit repair produces exact original P10", [
        row("Accept constructed N06", create("LP03", 1, "N06", "constructed"), {"status": "succeeded", "accepted_program_revision": rev("N06"), "admission_not_run": True}),
        row("Fail selected-branch limit at start", request("LP03", 2, "evaluate", program_revision=rev("N06"), run_id=None, until_seconds="3"),
            {"status": "rejected", "run_status": "failed", "reach_code": "reach_limit", "valid_until_seconds": "0", "valid_until_side": "before", "partial_claims": False},
            failed_run="response.run_id", failure_receipt="complete immutable terminal response"),
        row("Inspect original failure prefix", inspect("LP03", 3, "N06", "LP03.failed_run", ("0", "before")),
            {"status": "succeeded", "current_available": True, "lifecycle": "pending", "admission_fields_null": True, "candidate_only": False}),
        row("Repair limit with root authority", request("LP03", 4, "edit", expected_program_revision=rev("N06"), patches=[limit_repair], requested_level="evaluated"),
            {"status": "succeeded", "accepted_program_revision": rev("P10"), "exact_target_fixture": "P10", "libraries_byte_identical": True}, repaired_run="response.run_id"),
        row("Retain failed old revision history", inspect("LP03", 5, "N06", "LP03.failed_run", ("0", "before")),
            {"status": "succeeded", "program_revision": rev("N06"), "accepted_program_revision": rev("P10"), "old_failed_run_unchanged": True,
             "old_failure_receipt_unchanged": True, "candidate_only": False, "current_lifecycle": "pending"}),
    ])

    fixed_query = {"selector": {"kind": "action"}, "fields": ["actions"], "limit": 128,
                   "time": {"seconds": "1.5", "side": "after"}}
    group("LP04", "Complete P24 publication entry budget", "No adaptive smaller query, omitted projection or within-group pagination", [
        row("Accept P24 construction", create("LP04", 1, "P24", "constructed"), {"status": "succeeded", "named_action_count": 128}),
        row("Establish real sampled P24 run", request("LP04", 2, "evaluate", program_revision=rev("P24"), run_id=None, until_seconds="1.5"),
            {"status": "succeeded", "valid_until_seconds": "1.5", "valid_until_side": "after"}, sampled_run="response.run_id"),
        row("Measure complete default response", request("LP04", 3, "inspect", program_revision=rev("P24"), run_id={"$binding": "LP04.sampled_run"}, **fixed_query),
            {"status": "succeeded", "returned_action_count": 128, "complete_action_groups": True, "truncated": False, "next_cursor": None,
             "measurement": "N is recursive values/containers in the complete published response, including identities, cursor, implementation and progress; keys charge bytes only.",
             "record_intermediate_peak_and_cumulative_counts": True}, N="logical_json_entries(complete response)", default_response="complete response"),
        row("Publish same full query at N", request("LP04", 4, "inspect", program_revision=rev("P24"), run_id={"$binding": "LP04.sampled_run"}, budgets={"max_value_entries": {"$binding": "LP04.N"}}, **fixed_query),
            {"status": "succeeded", "returned_action_count": 128, "same_query_source_run_sample": True, "complete_response_entries": {"$binding": "LP04.N"}, "all_intermediate_budgets_preserved": True}),
        row("Reject N minus one at final publication", request("LP04", 5, "inspect", program_revision=rev("P24"), run_id={"$binding": "LP04.sampled_run"}, budgets={"max_value_entries": {"$binding_minus_one": "LP04.N"}}, **fixed_query),
            {"status": "failed", "protocol_error_code": "OKA-E-RESOURCE", "failure_stage": "final complete-response guard", "effects_committed": False,
             "earlier_intermediate_failure_does_not_satisfy": True, "all_intermediate_budgets_preserved": True, "new_request_identity_required": True}),
        row("Tiny output budget still yields bounded receipt", request("LP04", 6, "inspect", program_revision=rev("P24"), run_id={"$binding": "LP04.sampled_run"}, budgets={"max_value_entries": 1}, **fixed_query),
            {"status": "failed", "resource_failure_required": True, "bounded_failure_receipt_delivered": True, "global_json_limits_preserved": True, "effects_committed": False,
             "permitted_stage": "an actually exhausted intermediate resource guard or final publication guard; retain its exact inherited code and exhausted unit"}),
        row("Reject unsupported field without expanding work", request("LP04", 7, "inspect", program_revision=rev("P24"), run_id={"$binding": "LP04.sampled_run"}, selector={"kind": "action"}, fields=["unbounded_reach_dump"], limit=128, time={"seconds": "1.5", "side": "after"}),
            {"status": "rejected", "protocol_error_code": "OKA-E-REQUEST", "no_new_effects": True}),
    ])

    candidate_request = request("LP05", 2, "edit", expected_program_revision=rev("P10"), patches=[limit_failure], requested_level="evaluated")
    group("LP05", "Never-accepted candidate and immutable historical run marker", "Candidate failure remains candidate history even after identical source is later accepted", [
        row("Accept P10 construction", create("LP05", 1, "P10", "constructed"), {"status": "succeeded", "accepted_program_revision": rev("P10")}),
        row("Evaluated N06 edit fails without acceptance", candidate_request,
            {"status": "rejected", "program_revision": rev("N06"), "accepted_program_revision": rev("P10"), "reach_code": "reach_limit",
             "run_status": "failed", "candidate_only": True, "candidate_source_retained": True, "valid_until_seconds": "0", "valid_until_side": "before"},
            candidate_run="response.run_id", candidate_receipt="complete immutable terminal response"),
        row("Inspect unsampled candidate source", inspect("LP05", 3, "N06"),
            {"status": "succeeded", "current": {"available": False, "reason": "run_required", "value": None}, "candidate_only": True, "accepted_program_revision": rev("P10")}),
        row("Inspect actual candidate before-zero prefix", inspect("LP05", 4, "N06", "LP05.candidate_run", ("0", "before")),
            {"status": "succeeded", "current_available": True, "lifecycle": "pending", "admission_fields_null": True, "candidate_only": True, "accepted_program_revision": rev("P10")}),
        row("Reject ordinary candidate evaluate", request("LP05", 5, "evaluate", program_revision=rev("N06"), run_id=None, until_seconds="0.25"),
            {"status": "rejected", "diagnostic_code": "OKL-E-REVISION", "category": "stale", "never_accepted": True}),
        row("Reject ordinary candidate reset", request("LP05", 6, "reset", program_revision=rev("N06")),
            {"status": "rejected", "diagnostic_code": "OKL-E-REVISION", "category": "stale", "never_accepted": True}),
        row("Reject ordinary candidate export", request("LP05", 7, "export", program_revision=rev("N06"), destination="ontokin.glb/0.6", options={"end": "0.25"}),
            {"status": "rejected", "diagnostic_code": "OKL-E-REVISION", "category": "stale", "no_new_artifact": True}),
        row("Accept identical N06 at constructed level", request("LP05", 8, "edit", expected_program_revision=rev("P10"), patches=[limit_failure], requested_level="constructed"),
            {"status": "succeeded", "accepted_program_revision": rev("N06"), "identical_candidate_source_revision": True, "historical_run_candidate_only_still_true": True}),
        row("Inspect historical candidate run after acceptance", inspect("LP05", 9, "N06", "LP05.candidate_run", ("0", "before")),
            {"status": "succeeded", "accepted_program_revision": rev("N06"), "projection_candidate_only": False,
             "retained_run_candidate_only": True, "run_marker_is_historical": True, "old_run_unchanged": True}),
        row("Recover original candidate failure receipt", request("LP05", 10, "status", target_request_id="LP05.02"),
            {"status": "succeeded", "target_terminal_response_equals": "LP05.candidate_receipt", "historical_accepted_program_revision": rev("P10"), "historical_candidate_only": True}),
        row("Reject old candidate run continuation after acceptance", request("LP05", 11, "evaluate", program_revision=rev("N06"), run_id={"$binding": "LP05.candidate_run"}, until_seconds="0.25"),
            {"status": "rejected", "diagnostic_code": "OKL-E-SAMPLE", "category": "stale", "old_candidate_run_unchanged": True}),
        row("New reset after actual constructed acceptance", request("LP05", 12, "reset", program_revision=rev("N06")),
            {"status": "succeeded", "new_run_identity": True, "candidate_only": False, "old_candidate_run_unchanged": True,
             "valid_until_seconds": "0", "valid_until_side": "before", "admission_not_run": True}, accepted_reset_run="response.run_id"),
    ])
    assert [len(g["steps"]) for g in groups] == [9, 9, 5, 7, 12]
    for g in groups:
        for step in g["steps"]:
            if step["request_template"]["operation"] != "status":
                step["expected"].setdefault("no_unrequested_source_change", True)
    protocol = {"schema_version": "ontokin.proposed-reach-protocol-reconstruction/0.1", "proposal_version": "0.1.0-draft.2",
        "status": "new_expected_preparation_not_executed", "historical_row_bytes_recovered": False,
        "step_count_basis": "42 newly authored enumerated semantic requirements preserving the retained LP01-LP05 scope and counts; not exact recovery of lost row text.",
        "protocol_step_count": 42, "protocol_cases": groups,
        "binding_rules": {"$fixture_bundle": "Load exact entry/module bytes from the referenced case's file manifest into an ontokin.bundle/0.1 transport. Manifest filesystem paths are not wire source text.",
            "$binding": "Substitute the named value captured from an actual prior response, preserving type.",
            "$binding_minus_one": "Subtract one from the captured integer; do not change any query/source/run/sample field.",
            "retry": "LP02.06 submits byte-equivalent canonical request LP02.05 with its original request_id. Every other request has a fresh identity.",
            "asynchronous_receipts": "Wait for and retain each actual terminal receipt before using its output. Missing/interrupted/unknown outcomes do not become success.",
            "counting": "Setup polling/chunk retrieval and read-only evidence collection are real operations and must be logged, but do not create new LP semantic requirement rows."},
        "fixture_revisions": {name: rev(name) for name in ("L04", "P13", "P20", "N06", "P10", "P24")},
        "author_script_sha256": sha(Path(__file__).read_bytes()), "source_runtime_executed": False, "agent_sqlite_executed": False,
        "glb_or_destination_executed": False}

    old = "point(rig.arm.reach_frame, 8[m], 8[m], 0[m]), 1[s], elbow_positive"
    new = "point(rig.arm.reach_frame, 1[m], 1[m], 0[m]), 1[s], elbow_negative"
    handoff_patch = patch("L04", old, new, ["planar-reach-lifecycle", "demo", "reach-b"])
    assert edited_bytes("L04", handoff_patch) == (HERE / lifecycle["L02"]["entry_source"]).read_bytes()
    release = {"schema_version": "ontokin.proposed-reach-additional-release-probes/0.1",
        "status": "new_expected_preparation_not_executed", "included_in_original_42_protocol_steps": False,
        "probes": [{"id": "L04-tenth-agent-artifact", "prerequisite": "LP01.09 succeeds with unchanged accepted L04 and new successful prefix run",
            "request_template": {**request("LP01", "10", "export", program_revision=rev("L04"), destination="ontokin.glb/0.6", options={"end": "0.25"}), "request_id": "L04-release.01"},
            "expected": {"status": "succeeded", "program_revision": rev("L04"), "fresh_delivery_run_identity": True,
                "delivery_run_not_failed_LP01_run": True, "new_run_prefix": "0.25", "reset_does_not_change_source": True,
                "actual_artifact_chunks_retrieved_and_reassembled": True, "independent_byte_validation_required": True,
                "additional_to_nine_ordinary_agent_artifacts": True}, "execution_status": "not_executed"},
            {"id": "Q22-same-project-repair-and-stale-history", "prerequisite": "Same LP01 project retains accepted L04 and its failed run; capture actual failed run ID before edit",
             "edit_request_template": {**request("LP01", "11", "edit", expected_program_revision=rev("L04"), patches=[handoff_patch], requested_level="evaluated"), "request_id": "Q22.01"},
             "expected_edit": {"status": "succeeded", "accepted_program_revision": rev("L02"), "exact_entry_target": lifecycle["L02"]["entry_source"],
                "one_expression_patch": True, "libraries_unchanged": True, "same_project": True, "new_successful_run": True},
             "mismatch_request_template": {**inspect("LP01", 12, "L02", "LP01.failed_run", ("0.5", "before")), "request_id": "Q22.02"},
             "expected_mismatch": {"status": "rejected", "diagnostic_code": "OKL-E-SAMPLE", "category": "stale", "reason": "old L04 run cannot supply L02 program sample", "failed_create_is_not_a_substitute": True},
             "historical_control_request_template": {**inspect("LP01", 13, "L04", "LP01.failed_run", ("0.5", "before")), "request_id": "Q22.03"},
             "expected_historical_control": {"status": "succeeded", "program_revision": rev("L04"), "accepted_program_revision": rev("L02"), "old_failed_history_unchanged": True},
             "execution_status": "not_executed"}], "source_runtime_executed": False, "agent_sqlite_executed": False, "glb_or_destination_executed": False}
    return protocol, release
