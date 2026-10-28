#!/usr/bin/env python3
"""Append actual C044 validation and independent audit evidence without changing core."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil

BASE=Path(__file__).resolve().parent.parent
DOC=BASE/"OntoKin-publication/docs/engineering/reach-recording-validation-2026-10-23"
DEST=DOC/"checkpoint-044-validation"
assert not DEST.exists()
shutil.copytree(BASE/"c044-validation",DEST)
extra=DEST/"publication"
extra.mkdir()
for name in [
 "core-blob-upload.json","packaging-receipt.json","packaging.stdout","packaging.stderr",
 "restore-roundtrip.json","restore-roundtrip.stdout","restore-roundtrip.stderr",
 "restore-verify.stdout","restore-verify.stderr","root-window-close.json",
 "validation-command.stdout","validation-command.stderr",
 "import_published_commit.py","build_validation_appendix.py"
]:
 shutil.copyfile(BASE/"c044-publication"/name,extra/name)
def read(p):
 return json.loads(p.read_bytes())
def binding(p):
 b=p.read_bytes()
 return {"path":str(p.relative_to(DOC)),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()}
doc=read(DEST/"attempt-001/receipt.json")
ind=read(DEST/"independent-review/attempt-003/result.json")
closure=read(DEST/"independent-review/closure.json")
assert doc["status"]==ind["status"]=="passed"
assert closure["sole_reviewer_window_released"] is True
manifest=read(DOC/"checkpoint-044-evidence-manifest.json")
summary={
 "schema":"ontokin.checkpoint044-validation/0.1",
 "recorded_utc":datetime.now(timezone.utc).isoformat(),
 "status":"passed for qualified census, exact evidence and published-core documentation; product remains failed",
 "product_source":{"commit":"96b22349997b7d0d52262ea2f4cf4262b50365fd","tree":"d8c3a88f7a3017fedef667e217af76271068f560","files":2265,"bytes":477942773},
 "published_core":{"commit":doc["source_commit"],"tree":doc["source_tree"],"files":doc["source_file_count"],"bytes":doc["source_bytes"],"new_files":17,"all2265parent_files_preserved":True},
 "documentation":doc["documentation"],
 "complete_input_inventories_identical":doc["complete_input_inventories_identical"],
 "core_validation_started_utc":doc["started_utc"],
 "core_validation_finished_utc":doc["finished_utc"],
 "independent_archive_review":{"status":ind["status"],"finished_utc":ind["finished_utc"],"result":binding(DEST/"independent-review/attempt-003/result.json"),"closure":binding(DEST/"independent-review/closure.json"),"two_audit_preparation_failures_preserved":True},
 "archive":{"parts":len(manifest["archive"]["parts"]),"bytes":manifest["archive"]["bytes"],"sha256":manifest["archive"]["sha256"],"members":manifest["member_count"],"member_bytes":manifest["member_bytes"],"all_crc_member_hashes_paths_modes_verified":True,"actual_restoration_hash_mode_mtime_ns_verified":True},
 "analysis_results":{"source_input_neutrality_checks":81,"angular_author_checks":1587,"independent_angular_checks":242,"independent_root_census_checks":242,"full_cache_events_reconciled":46721,"completed_cache_mutations_reconciled":6177,"source_review_records":8},
 "product_requests":{"count":2,"stock":{"status":"failed","exit_code":1,"shared_operations":100001,"completed_reach_operations":80801,"product_elapsed_seconds":2.303072429999702},"capture":{"status":"failed","exit_code":1,"shared_operations":100001,"completed_reach_operations":80801,"product_elapsed_seconds":10.730872985000133},"all222category_totals_equal":True,"complete_recorded_post_state_and_failure_frames_equal":True,"compared_cache_state_equal":True,"untraversed_other_numerical_payloads":True},
 "census":{"completed_cold_calls":32,"exact_angular_groups":1,"spatial_groups":32,"native_t":2,"native_c":15,"all_sq_exact_pairs_equal":True,"original_envelope_charges":960,"shared_window_charges":991,"intercall_charges":31,"conditional_gross_repeated_sites":434,"net_saving_bound":None,"candidate_cache_retention":None,"complete_P23_cost":None},
 "qualifications":[
  "Actual17:25:13.341049Z launch preceded the mistakenly declared17:26:00Z start; both requests completed before the nominal start. Required source closure, exact reviews and recorded pause commitments preceded actual execution, but the nominal start condition was not met. Original comment/correction/receipts remain unchanged.",
  "No elapsed or general-path instrumentation neutrality is claimed. The measured failed producer prefixes agree in the compared source/request/path/accounting/cache fields.",
  "Other numerical cache payloads were not traversed. Raw process identities remain retained beside explicit normalization.",
  "The final lookup refused before membership, even though replay separately finds an equal retained key.",
  "The original whole-entry retention does not establish hypothetical angular-entry retention, lifetime safety or displacement cost.",
  "The51times list is a schedule, not evidence all later samples completed;31gap attribution is source-reconciled inference.",
  "434 is conditional gross repeated arithmetic, not measured or proved net saving, full request cost or P23 acceptance.",
  "Complete checkout recovery and documentation/metadata validation do not close the separately defined formal release input-closure role.",
  "The unknown partial archive retains unknown origin and exact bytes/mode/time; historical and current cleanup qualifications remain explicit.",
  "The final appendix contains only new JSON, logs and audit/helper code. The actual documentation test names the immutable published core; no new runtime or product test is inferred for the appendix.",
  "A final containing commit cannot be embedded in its own bytes; use the verified owned branch/PR and Issue26 closure for final publication identity."
 ],
 "retained_failures":[
  "Both original product requests failed at the unchanged operation cap.",
  "All recorded recovery/capture-preparation failures and the initial external driver remain in the core archive.",
  "A large local base64 read exceeded the exec output limit; an exact length gate rejected it before upload. Verified chunked reads and exact remote Git blob checks succeeded.",
  "Independent audit attempt001 used an overly literal wording assertion; original script/log/failure retained.",
  "Independent audit attempt002 used Pathlib ordering instead of Git complete-path byte ordering; original script/log/failure retained. The verified file maps already matched and final canonical order comparison passed."
 ],
 "retained_records":[binding(p) for p in sorted(DEST.rglob("*")) if p.is_file()],
 "next_task":"C045 source-only conditional angular-reuse feasibility and complete positive charged bound with independent authority review before a later implementation scope.",
 "continuing_status":{"original28_latest_complete":"24/28","capped":["P11","P16","P23","L03"],"C035":"held including adverse L03 timing","accepted_reach":"d2f0088c4f3c1f570630334804a5a8f78e0105ac","main":"2bb4588e121fcfe99b4d42c734b15b38362f3642","main_lease_acquired":False},
 "runtime_changes":False,"original_suite_rerun":False,"full_regression_run":False,"candidate_numerical_replay":False,"failed_tail_resumed":False,"hosted_jobs_dispatched":False,"merge_performed":False,"release_acceptance":False,"full_goal_completed":False
}
(DOC/"checkpoint-044-validation.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps({"status":"prepared","retained_records":len(summary["retained_records"]),"core_commit":doc["source_commit"],"independent_review":ind["status"]}))
