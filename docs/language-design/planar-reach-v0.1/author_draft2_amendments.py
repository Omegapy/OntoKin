#!/usr/bin/env python3
"""Reproduce separately identified Draft 2 amendments; preserve original proposal inputs."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ORIGINAL = {
    "profile.json": "0893976f738d280f2dcc1dcbb33fbbfe9ece1baf4716d59ecdde2ab80e18dfb7",
    "requirements.json": "57f982233af32a3d68f2fd5e50505a16cf348005dd522aa2ca62d76dee6ebaa7",
    "repair-briefs.md": "eaf976ec774f9f60ed7d5646adf0e9c9298ec0718b6f7d936c98b6a6cd70ae3e",
    "acceptance.json": "1f0cf3e947f900d6de4a638cf486c78f3d1403ad5490ab19abd1b1c1c2df8195",
    "generated-members.json": "a5ee10a3917bc9646041aa57dc031642f09315157fa05aedc1ab3fc709d54bca",
    "oracle.py": "a556ddc0f23958f62e035bfe997bc0fbbdc432b7899fab8021ebefd713e99c07",
}
DECISIONS = [
    ("D14", "Accepted force dependency", "Use actual main 59b937d16ec0c82c9bc1395bd0c9bcc63e597261 with complete F01-F12 evidence and released integration lease; preserve manual-only default-false hosted policy."),
    ("D15", "Current state and terminal identity", "Requested program, actual accepted head, candidate history and sampled run identity are distinct. Current outcomes are exactly pending/active/satisfied/interrupted. Failed admission changes no incoming projection. Terminal snapshots remain latched while physical joints may have another owner."),
    ("D16", "Failed-prefix publication and recovery", "A failed boundary retains only the valid incoming prefix. Reset/re-evaluate supplies a new run; L04 requires a separate tenth Agent artifact exported through exactly 0.25 seconds with the fresh delivery run produced by export and unchanged L04 program revision; retain reset/evaluation run IDs separately."),
    ("D17", "Complete-response output budget", "Q03 fixes P24, actual sampled t=1.5 after, selector.kind action, fields actions, limit128, all128 complete items without cursor. Measure the full canonical envelope N; N succeeds including constructor/intermediates and N-1 fails at final publication without effects. No adaptive smaller query or pagination exemption."),
    ("D18", "Actual root source authority", "P13 to P20 repair follows the inspected initializer target to writable root rig and exact source span. Reject generated occurrence and property identities; preserve sibling and library bytes."),
    ("D19", "Both-moving lifecycle supplements", "Add independently identified L01 pause/resume, L02 stopped/new-owner, L03 completed/new-owner, L04 failed handoff rollback and fixed LP01-LP05 protocol steps; original41 cases remain byte-identical."),
    ("D20", "Stored time, SLERP and incoming histories", "Use direct exact-rational to binary32 ties-even clocks, normalized actual stored endpoint SLERP, all enclosing source phases, independently proved uniform numerical bounds and complete incoming release contributors/state/spans. Unknown error terms reject."),
    ("D21", "Diagnostic and canonical-limit order", "Use inherited envelope codes with structured reach_code; establish correctly rounded selected targets before checking their closed canonical limits. Work/cancellation may interrupt every bounded phase."),
    ("D22", "Bounded numeric admission", "Exact rational classification and algebraic signs plus outward interval proof at96/192/384/768/1536bits establish rounding cells and residual. Bound recurrence/work/operand sizes; unresolved precision is numeric failure, exhausted work is resource failure."),
    ("D23", "Complete numerical/interface/delivery release obligations", "Add R10-R12 and Q13-Q22 and the provider-neutral release contract. Execute actual source, Agent, destination, browser, compatibility and inherited roles; preparation is not acceptance."),
    ("D24", "Distinct budget units", "Distinguish semantic/source-value work, full Agent JSON, weighted source history and whole GLB JSON/bytes. Extend F05/H05 weights by complete reach maps and incoming releases before allocation; do not equate all100000 counters."),
    ("D25", "Series recurrence unit", "The12000cap counts one atan-term iteration or one paired sin/cos iteration. Every constituent interval operation is charged separately to the100000cap and inherited remaining semantic budget; no additional program allowance."),
    ("D26", "Reconstruction provenance and stored bits", "After the executor rollback, exact recovered files retain their recorded old identities at checkpoint1431e5f; reconstructed proof/schema/protocol/quantization files receive new hashes and fresh review. The retained clock row also exposes stored_binary32_bits, which must agree with actual bytes and exact conversion. No lost check is relabeled for new bytes."),
    ("D27", "Current source and historical run acceptance", "Clarify reconstructed LP05.09 without changing the existing semantic rule: after the identical source is accepted, its current projection has candidate_only=false, while the retained earlier candidate run has immutable candidate_only=true. Name these two observations separately; preserve all 42 protocol steps and the original corpus."),
]


def original_inputs() -> list[dict]:
    rows = []
    for name, expected in ORIGINAL.items():
        raw = (HERE / name).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError("original input changed: " + name)
        rows.append({"path":name,"bytes":len(raw),"sha256":actual})
    return rows


def build_profile() -> dict:
    p = json.loads((HERE / "profile.json").read_text())
    p.update(schema_version="ontokin.proposed-planar-reach-profile/0.2",
             proposal_version="0.1.0-draft.2", reconstruction="2026-10-20-recovery-14",
             original_profile="profile.json", effective_amendments="draft2-amendments.json")
    p["accepted_dependency"] = {"main":"59b937d16ec0c82c9bc1395bd0c9bcc63e597261",
        "force_implementation":"c7db6520e172b2b38591969a4bdf75f97a993dbb",
        "force_main_merge":"e74dd14bd90bfd0ef7b11d9a939292bb9e5dda4c",
        "finite_force_release_complete":True,"whole_goal_complete":False}
    p["hard_limits"].update({"construction_semantic_operations":100000,
        "construction_logical_source_values":100000,"agent_logical_json_entries":100000,
        "agent_json_depth":128,"inherited_source_history_counting_unit":"weighted_state_records",
        "whole_glb_json_entries":67108864,"interval_certificates":100000,
        "elapsed_work_ms":30000,"numeric_precision_bits":[96,192,384,768,1536],
        "numeric_series_recurrence_steps_per_admission":12000,
        "numeric_interval_operations_per_admission":100000,"numeric_rational_component_bits":32768,
        "numerical_work_is_additional_program_allowance":False})
    del p["hard_limits"]["inherited_semantic_work_and_logical_entries"]
    p["numerical_meaning"]["correct_rounding_evidence"] = (
        "Independent exact rational/outward dyadic rounding-cell and real forward-residual proof; "
        "finite corpus certificates validate predetermined bits, while runtime must apply the bounded method to arbitrary supported inputs.")
    p["numerical_meaning"].update({"canonical_limit_order":"prove selected rounded coordinate pair, then compare canonical closed limits",
        "numeric_contract":"numeric-admission.md","counter_clarification":"numeric-counter-units.md",
        "precision_unresolved":"reach_numeric","work_exhausted":"reach_resource",
        "cancellation":"interruption, never a geometric outcome"})
    projection = p["goal_projection"]
    projection["status"] = "concrete proposed JSON schema and actual-operation mapping; not runtime evidence"
    projection["schema"] = "schema-drafts/reach-projection.schema.json"
    projection["operation_mapping"] = "agent-operations.md"
    projection["always_required"] = [
        "requested program revision and complete source-unit hashes", "context_origin and actual service accepted-head/candidate fields or explicit source-recording nulls",
        "action occurrence identity and source unit/hash/UTF-8 span", "ordered shoulder/elbow/tip occurrence identities",
        "typed canonical target and exact frame identity", "selected ReachBranch and canonical duration",
        "current availability; sampled lifecycle and separate goal outcome only when actual observation exists"]
    projection["pending_null_fields"] = ["resolved_joint_targets_rad","start_coordinates_rad","start_time_seconds",
        "elapsed_seconds","completion_time_seconds","current_residual_m","terminal_result"]
    projection["accepted_goal_outcomes"] = ["pending","active","satisfied","interrupted"]
    projection["terminal_outcomes"] = ["satisfied","interrupted"]
    projection["failed_admission_outcome"] = "failure only in request/boundary diagnostic; incoming current projection unchanged"
    projection["unavailable_current"] = {"available":False,"reason":"run_required","value":None}
    projection["observation_contexts"] = {
        "run_sample":"actual nonempty run_id and matching immutable program revision",
        "constructed_initial":"explicit before-zero constructed observation, null run_id; not a fabricated unsampled run",
        "recorded_prefix":"identified immutable source recording, null Agent run/acceptance fields"}
    projection["physical_and_action_rates"] = "joint rates describe current physical state; own action rates are zero pending/paused/stopped/completed even when another owner moves the joints"
    projection["terminal_snapshot_policy"] = "latched terminal time/coordinates/tip/residual never overwritten by later owners; current physical residual may change"
    projection["candidate_history_policy"] = "requested candidate, actual accepted head, ever-accepted history and immutable old run/receipt identities remain distinct; after the identical source is accepted, current projection candidate_only is false while a retained earlier candidate run keeps candidate_only true (LP05.09, D27)"
    table = {
        "reach_type":("OKL-E-TYPE","invalid","rejected",["type"]),
        "reach_frame":("OKL-E-REACH","invalid","rejected",["elaboration"]),
        "reach_chain":("OKL-E-REACH","unsupported","rejected",["support"]),
        "reach_domain":("OKL-E-REACH","unsupported","rejected",["support"]),
        "reach_claim_conflict":("OKL-E-REACH","invalid","rejected",["admission"]),
        "reach_unreachable":("OKL-E-REACH","invalid","rejected",["admission"]),
        "reach_singular":("OKL-E-REACH","invalid","rejected",["admission"]),
        "reach_limit":("OKL-E-REACH","invalid","rejected",["admission"]),
        "reach_numeric":("OKL-E-NUMERIC","numerical_failure","failed",["admission","evaluation"]),
        "reach_resource":("OKL-E-RESOURCE","resource_limit","failed",["support"]),
    }
    for row in p["diagnostics"]:
        row["source_semantic_phase"] = row.pop("phase")
        code, category, status, phases = table[row["reach_code"]]
        row.update(envelope_code=code,category=category,validation_status=status,envelope_phases=phases)
    p["diagnostic_precedence"] = ["inherited syntax/types/references","immutable frame, chain and scalar domains in source argument order",
        "inherited current motion mode and coordinate claim conflicts","exact geometric reachability, then singularity",
        "bounded proof of selected canonical coordinate pair","selected-branch closed canonical limits","certified rounded-pair residual and completion residual"]
    p["work_and_cancellation_precedence"] = "Check/precharge throughout all phases; a first exhausted budget or observed cancellation interrupts without claiming later mathematical classification."
    p["budget_and_cancellation_policy"] = "budget-counting.md defines distinct units, conservative preflight, full response/intermediate guards and actual-work bounded caching; all numerical work consumes remaining inherited work."
    p["recorded_delivery"] = {"quantization_contract":"quantization.md","metadata_schema":"schema-drafts/glb-metadata.schema.json",
        "quantization_schema":"schema-drafts/quantization.schema.json","clock_conversion":"binary32_rne_ties_to_even_from_exact_rational",
        "clock_bits_must_match_actual_accessor":True,"all_touching_phases_required":True,"unknown_uniform_numeric_error":"reject",
        "history_maps":["joint_states_before","joint_states_after","action_states_before","action_states_after",
            "pose_authorities_before","pose_authorities_after","impulse_states_before","impulse_states_after","force_states_before","force_states_after",
            "reach_states_before","reach_states_after","incoming_releases"],
        "failed_prefix_recovery":"reset, evaluate a fresh L04 run through0.25, actually export/retrieve under the unchanged L04 program revision"}
    p["release_contract"] = "release-contract.md"
    return p


def build_requirements() -> dict:
    r = json.loads((HERE / "requirements.json").read_text())
    r.update(schema_version="ontokin.proposed-planar-reach-requirements/0.2",proposal_version="0.1.0-draft.2",
             reconstruction="2026-10-20-recovery-14",original_requirements="requirements.json",
             effective_amendments="draft2-amendments.json",release_contract="release-contract.md")
    for row in r["requirements"]:
        if row["id"] == "R07":
            row["draft2_supplemental_cases"] = ["L01","L02","L03","L04"]
            row["actual_evidence_required"] += ["both moving joints share exact pause/resume elapsed clock",
                "stopped and completed old actions retain latched terminal snapshots while new owners change physical coordinates/rates/residual",
                "failed stop/start handoff rolls back the whole boundary, including the old action's claims"]
        if row["id"] == "R08":
            row["draft2_protocol_cases"] = ["LP01","LP02","LP03","LP04","LP05"]
            row["actual_evidence_required"] += ["follow inspected initializer_target to actual writable root rig; reject generated/property authority",
                "candidate-only unsampled inspection versus actual before-zero observations",
                "retained candidate failed runs and old operation receipts stay immutable after later acceptance; LP05.09 current projection candidate_only is false while retained run candidate_only remains true",
                "same-project actual L04 to L02 source edit then retained L04 run/new L02 revision mismatch rejection"]
    r["requirements"] += [
        {"id":"R10","requirement":"Establish canonical targets by bounded independent rounding-cell and residual proof, with honest numeric/resource/cancellation outcomes.",
         "cases":[f"P{i:02d}" for i in range(1,27)]+["N01","N02","N03","N06"],
         "independent_oracle":"interval_oracle.py and rounding-certificates.json independently check the original54 target coordinates; original oracle/acceptance bits remain unchanged.",
         "actual_evidence_required":["runtime exact canonical targets and rational interpolation","finite numeric precision/work/operand counters and precharge","corrupt-cell probes fail","correct closed-limit ordering","cancellation and bounded cache preserve all per-action authority checks"]},
        {"id":"R11","requirement":"Execute the complete proposed Agent/0.6 operation, revision, budget and failure-recovery contract with exact retrieved bytes.",
         "cases":["P01","P11","P13","P20","P24","N06","P10","L01","L02","L03","L04"],
         "independent_oracle":"agent-operations.md, schema-drafts and all42 fixed LP01-LP05 protocol steps plus separately required recovery/stale-source probes.",
         "actual_evidence_required":["twelve actual inherited operation routes","strict request/response/diagnostic schemas","default and lowered complete-response budgets","failed-prefix run/status/history and actual reset/re-evaluation/export","immutable candidate/accepted/run/receipt identities","actual artifact retrieval equals identified exported bytes"]},
        {"id":"R12","requirement":"Certify actual stored carrier/landmark motion over whole intervals and reject semantic corruption in supplied GLB bytes.",
         "cases":["P01","P05","P09","P11","P16","P17","P18","P19","L01","L02","L03","L04","Q16-nonbinary-boundaries"],
         "independent_oracle":"quantization.md exact source/stored time, nonzero-endpoint SLERP proof, geometry and phase bounds; actual numerical kernel derivations remain mandatory.",
         "actual_evidence_required":["source and actual destination uniform numerical proofs","direct rational binary32 clock bits","all touched phase bounds and complete interval coverage","native geometry/PBR/radius/vertex validation","source-built and Agent-retrieved independent native/browser checks","actual visual review and allQ13-Q22 hostile cases"]},
    ]
    q = {row["id"]:row for row in r["predetermined_execution_probes"]}
    q["Q03"].update(operation="actual complete P24 action inspection at t=1.5 after; selector.kind=action, fields=[actions], limit128, no cursor",
        expected="default full128-item success; measure complete envelope logical entries N; max_value_entries=N succeeds including cumulative constructor/intermediates; N-1 fails specifically at final publication with inherited OKA-E-RESOURCE and effects false; tiny success budget still returns bounded failure receipt",
        forbidden_substitutes=["max_bytes request field","result.items-only count","smaller query","partial action groups","adaptive pagination","preemptive constructor failure offered as final-publication proof"])
    q["Q07"].update(operation="from valid P16 GLB mutate complete $.extras.ontokin.boundary_states[].reach_states_before or incoming_releases at release; separately corrupt later released trajectory",
        expected="the first probe rejects missing/wrong incoming two-joint/root derivative history; the second rejects the independently decoded full world trajectory; an unrelated parse/hash failure satisfies neither")
    extra = [
        ("Q13","P05","understate actual normalized endpoint position/quaternion error while preserving otherwise valid clocks/geometry","independent recomputation rejects understated endpoint bound"),
        ("Q14","P05","replace source numerical method/proof by unknown or zero unproved bound","uniform numerical evidence rejection; sampled maxima/unused tolerance cannot pass"),
        ("Q15","P11","change destination numeric implementation/version/derivation identity without changing poses","destination identity and uniform-bound rejection"),
        ("Q16","Q16-nonbinary-boundaries","use separately identified source with pause0.50000002/resume1.50000002 and exact completion3+2^-53; remove only preceding moving phase from valid stored post-pause forearm certificate","reject phase omission: stored[0.5,1] covers moving width180143985/9007199254740992 before exact pause; originalL01 binary-exact clocks cannot substitute"),
        ("Q17","P11","understate complete carrier-local native geometry radius or actual vertex conversion error","reject independently from all source occurrence vertices/sites after visual placement"),
        ("Q18","P01","retain authored nonsemantic exact clock1+2^-24+2^-80 and supply double-rounded bits3f800000 instead of direct3f800001","reject exact conversion mismatch on otherwise valid artifact; ordinary tolerance or float64 cast cannot mask it"),
        ("Q19","P09","supply zero quaternion, inconsistent short-path lift, or nonunit endpoint exceeding the proved actual normalization/interpolation bounds","reject intended quaternion/numeric violation; ordinary correctly converted binary32 nonunit endpoints remain supported when fully bounded"),
        ("Q20","P11","remove or duplicate exactly one required carrier/adjacent-key interval certificate","reject complete coverage mismatch before acceptance"),
        ("Q21","L03","overwrite A's latched satisfied terminal snapshot with later B-owned physical coordinates/residual","reject lost terminal history while independently accepting changed current physical state"),
        ("Q22","L04-to-L02-same-project","create/evaluate accepted L04 to failed boundary; atomically replace that same project's inspected reach_b action expression with exact L02 text using current source/revision/span preconditions; request retained oldL04 run using newL02 revision","reject program/run mismatch; preserve oldL04 descriptor and request receipt exactly; cross-project or second create is not this probe"),
    ]
    r["predetermined_execution_probes"] = list(q.values()) + [dict(id=i,source=s,operation=o,expected=e) for i,s,o,e in extra]
    r["separately_required_agent_recovery_artifact"] = {"source":"L04","protocol_position":"after LP01 reset and fresh0.25-second evaluation",
        "export_end_seconds":"0.25","must_execute_actual_export_and_retrieval":True,"program_revision":"unchanged L04",
        "run_id":"fresh delivery run produced by export; reset/evaluation identities remain separately retained","artifact_ordinal":"tenth mandatory Agent artifact beyond nine ordinary deliveries",
        "already_executed_by_42_protocol_steps":False}
    r["protocol_inventory"] = {"LP01":9,"LP02":9,"LP03":5,"LP04":7,"LP05":12,"total_steps":42,
        "extra_recovery_and_Q22_are_separate":True,"reconstruction_does_not_assert_original_missing_bytes":True}
    r["release_preconditions"] = [
        "Complete fresh contract review, exact input closure and separate published adoption record before runtime implementation.",
        "Accepted force main59b937d16ec0c82c9bc1395bd0c9bcc63e597261 and original41-case closure preserved.",
        "Concrete proposed Agent/GLB0.6 schemas, operations, diagnostic mapping, numerical proof and quantization obligations reconciled.",
        "Freeze literal actual requirement-to-test mapping before complete release executions.",
        "Execute every mandatory role of release-contract.md with current identified implementation and stable input hashes.",
        "Preserve no-payment local policy, manual-only default-false hosted jobs and all inherited regression obligations.",
        "Whole GOAL and actual unseen-variant direct-tool authoring comparison remain separately open."]
    return r


def build() -> dict[str, dict]:
    inputs = original_inputs()
    amendments = {"schema_version":"ontokin.planar-reach-draft-amendments/0.2","document_id":"OK-LANG-006",
        "proposal_version":"0.1.0-draft.2","status":"proposed_not_adopted","implementation_status":"not_implemented",
        "reconstruction":"2026-10-20-recovery-14","original_inputs":inputs,
        "preservation":"Original files remain byte-identical; these independently named effective views do not overwrite them.",
        "effective_files":["profile-draft2.json","requirements-draft2.json"],
        "decisions":[{"id":i,"title":title,"decision":decision} for i,title,decision in DECISIONS],
        "fresh_evidence_required":True,"lost_checks_apply_to_new_bytes":False,"whole_goal_complete":False}
    return {"draft2-amendments.json":amendments,"profile-draft2.json":build_profile(),"requirements-draft2.json":build_requirements()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    args = parser.parse_args(); args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, value in build().items():
        raw = (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode()
        (args.output_dir / name).write_bytes(raw)
        rows.append({"path":name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()})
    print(json.dumps({"status":"prepared_not_executed","original_inputs_verified":len(ORIGINAL),"generated":rows},indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
