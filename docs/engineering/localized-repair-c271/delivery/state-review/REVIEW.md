# C271 delivery-state review

**Verdict: one material identity-binding correction required before execution.**

Reviewer: `/root/control_author`. Static review only; script not executed, no
repository or script edits, no behavioral tests or extra check suite.

Reviewed script: `/workspace/scratch/cce28e2b3ca4/finalize_c271_delivery.py`

SHA-256: `4a4a2e9962d576a614edda697446f27702827df3bcb1bbc04945b6cae9cbf110`

Candidate: `e0b73f7d6ce49631e598d1378a0ddba717726524`; tree
`9ab0d4dfcb21735fed4c019f85f8f450ebfaa7b4`.

## C271-DELIVERY-RV-001 — Bind saved files to the verified package

The upload gate checks three local file identities and counts two `.md`
entries. It does not require the two distinct prompt filenames/hashes recorded
in the package verification report. Two copies of one prompt, or two other
local Markdown files, satisfy those predicates. The receipt nevertheless sets
`standalone_prompts_match_zip` to true. This is a concrete gap in the intended
receipt assertion, not an observed failed upload.

Before any writes, require the exact unique upload file set and match each
filename, byte count and SHA-256 to the verified archive and the builder's two
`standalone_prompts`. Bind the builder report's source revision/tree and archive
identity to `SOURCE`/`TREE` and the fixed archive hash. Bind the independent
audit's reviewed archive/source identities to those same values; checking only
its `passed` boolean does not establish that join.

The inspected builder report identifies the expected archive hash
`9bdb8ec134fbf8facc1b1f52aa9b7171de16f35593ddf7ad61930e521f4495df`
and two different prompt identities. The normalized upload receipt and
independent audit were not yet present during this review. Their absence is
consistent with the declared later invocation gate; no saved-delivery claim is
made here.

## Remaining transition

No other material finding. The inspected task/CURRENT/PLAN/SESSION state agrees
with the intended transition: only P01 becomes done; parent remains
`in_progress`, R03–R05 and P02 remain `not_done`. Requirements are asserted
before modification. Existing handoffs are retained in the previous/older
records, and old PLAN/SESSION text remains as historical checkpoints.

Writes target a new `delivery/` directory, task/CURRENT records and appended
PLAN/SESSION text. No runtime, oracle, original evidence, frozen ZIP or prompts
are rewritten. No Git mutation, remote write, merge, issue closure or branch
deletion is performed. The receipt explicitly postdates the frozen ZIP and
preserves the retained draft PR274/open issue273 boundary. Conditional approval
can follow the single identity-binding correction; actual save, final receipt
publication and live readback remain Director responsibilities.
