# C268 check-runner preparatory review

## Verdict

PASS for structural preparation after the two identified evidence-accounting corrections. The declared predecessor cohort, method arithmetic and main identity safeguards are structurally correct. The corrected runner includes the historical GLBs in its input identity inventory and reconciles the agreed C268 aggregate API-call outcomes. Both original findings and their resolutions are retained below.

This is a structural/preparatory review only. It does not approve an implementation candidate or claim that any cohort was executed.

## Reviewed identity and scope

- Reviewer: `/root/state_audit`, separate from the runner author and future implementation/control authors.
- Reviewed path: `docs/engineering/localized-repair-c268/evidence/run_checks.py` in `/workspace/scratch/c7dae94da130/OntoKin`.
- Initially reviewed bytes: 14,075; SHA-256 `b8d83ae52211bca993a1bd2a3f98e171673ff7241addd668be3bf24c4eedbf1b`.
- Corrected runner: 14,667 bytes; SHA-256 `9c6c67a2bb1ce9e7a238b53e185f34d25f794ce7a1bb6e17753d7a9c187b3a3a`, inspected 2026-11-19 14:20:31 UTC.
- This source was uncommitted when assigned. The initial identity remained stable through its first review; the Director subsequently made the two corrections and this worker reinspected those changed regions and parsed the corrected full source.
- Read the full new runner and compared its exact text with `docs/engineering/localized-repair-c267/evidence/run_checks.py`. Retained C260/C253 contract and corpus context from the earlier audit; no global instruction repetition or implementation review.
- Actual model configuration inherited; no override, external model runner or nested worker.

## Correct behavior observed in source

The runner schedules all required groups: C253 corpus; C255 oracle; C256 reader; C257 ownership; C258 follows; C261 raw hinge reader; C265 source hinges; C266 binding; C267 comparison; C268 endpoint; workflow; and documentation. This is 12 groups. C260 contributes the unchanged contract/input/control-plan records and has no separate executable suite in the declared cohort.

The fixed method subtotal is correct: 31 + 29 + 23 + 28 + 28 + 49 + 34 = 222. With unchanged C267's 25 methods, the required total is 247 + the final C268 method count. `--c268-methods` is required and checked against both unittest output and the new control receipt.

Each suite records the actual command, start/end time, duration, exit status, log identity and assertion outcomes. The receipt identifies the source Git commit/tree, clean tracked state, untracked status, Python version/platform, interpreter binary hash, runtime bundle and runner hash. Every group checks that commit/tree are unchanged and tracked files remain clean. A final before/after input inventory comparison contributes to the overall pass condition.

C253 checks require 14 bindings and three tasks. C266 retains the exact 748 = 28 + 720 call split. C267 retains its existing outcome-total assertion. Unittest success requires the expected method count and a plain `OK`, excluding success output with skips/expected failures. Missing/malformed control receipts produce a failed result rather than silent success. Timeout and subprocess failures preserve captured output; remaining checks remain visible. Full product/native/model/compatibility/hosted coverage is explicitly not claimed.

## Findings and resolutions

### RNR-01 — Historical GLBs omitted from explicit input inventory — resolved

Priority: mandatory evidence correction for this C268 runner.

`inputs()` selects top-level component `.py`, `.json` and `.md` files and expands the C253 corpus file table. It includes C260's `INPUTS.json` as a document but does not expand that document's `files` records. The C253 corpus does not list `before.glb` or `after.glb`, and these files live outside the selected component directories. Consequently, the historical endpoint GLBs are absent from the runner's explicit before/after size/hash inventory even though C268 consumes them.

Required correction: add every path in unchanged C260 `INPUTS.json.files` to the selected input set, including both historical GLBs. Deduplication through the existing set is suitable. Confirm the resulting receipt inventories the actual GLB files and that their recorded identities equal the fixed C260 pins. The Git tree still globally identifies tracked fixtures; this finding concerns incomplete explicit input accounting, not proof that the executed bytes changed.

Resolution inspected in the corrected source: `inputs()` reads C260 INPUTS and adds every `historical["files"]` path to the selected set. Both historical GLBs are consequently included. Confirming their emitted identities remains part of reviewing the actual execution receipt.

### RNR-02 — C268 API-call counts are reported without reconciliation — resolved

Priority: mandatory evidence correction once the independent control schema is final.

The C268 result branch reads `apiCalls`, `admittedCalls` and `typedRefusals` but makes no assertion relating them. A control receipt could therefore report contradictory totals while the runner accepts its `passed` flag and method count.

Required correction: assert the final schema's exact disjoint outcome accounting. If `apiCalls` counts only historical-wrapper calls, require `apiCalls == admittedCalls + typedRefusals`. If it also counts successful changed-input raw calls, explicitly include those through the agreed `successfulCalls` or `rawSuccessfulCalls` field. Preserve the historical admission count separately so raw success cannot be mislabeled as admission. When a per-call case list is provided, also reconcile its length and outcome totals rather than rely only on counters.

Do not invent a fixed C268 API-call count before the independent controls are complete. Supply the actual independently reviewed method count through `--c268-methods`.

Resolution inspected in the corrected source: the agreed schema now explicitly distinguishes `historicalCalls`, `rawCalls`, `admittedCalls`, `rawSuccessfulCalls`, `successfulCalls`, `typedRefusals` and `untypedExceptions`. The assertion requires `apiCalls == historicalCalls + rawCalls == successfulCalls + typedRefusals`, `successfulCalls == admittedCalls + rawSuccessfulCalls`, and zero untyped exceptions. This closes the aggregate runner-accounting gap. The future independent candidate review must still check the control author's actual per-call evidence rather than infer coverage from counters alone.

## Execution and provenance conditions

The runner permits untracked files and discloses them; it rejects only dirty tracked source. Before describing a result as an exact committed candidate, the Director must ensure implementation, controls, fixtures and runner are actually retained in that candidate, then run against its identified isolated checkout. Explicit input hashes can identify untracked bytes, but a clean tracked-state flag alone does not place them in the named commit.

The runner is hashed at start but is not separately part of the final explicit input comparison because it lives under `evidence/`. A tracked runner is covered by per-group tracked-state checks. If executing a runner outside the identified checkout, retain its exact bytes and avoid claiming it is part of that source revision without establishing equality.

These are concrete execution/provenance conditions, not requests to expand to a full product or hosted suite.

## Checks and Director response

Executed read-only source inspection, exact text diff, SHA-256 reads, Python AST parsing and fixed-count arithmetic. The initial and corrected source both parse successfully. No test runner, component code, product execution or filesystem-control behavior was executed.

The Director applied both corrections after agreeing the exact result fields with the independent control author. This worker observed the changed regions and corrected source identity, closing RNR-01 and RNR-02 structurally. The Director confirms no cohort was executed with the earlier runner. Preserve the corrected hash in the actual candidate/run evidence; re-review further runner changes if they affect these checks.

Only `/workspace/scratch/c7dae94da130/audit/RUNNER-REVIEW.md` was written. No code, Git index/refs, repository records or remote state was changed. No pending process or unknown operation remains.
