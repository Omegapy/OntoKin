# C271 P08 independent intake reconciliation

Reviewer: `/root/implementation_review`. Scope: intake only, before the Director's P08 early-save confirmation. No implementation review, project-code import, runtime preparation, Node/ldd, product test, Git operation, publication or integration occurred.

## Decision

**PASS_INTAKE. No intake blocker found.** `INTAKE-VERIFICATION.json` records 20 passing verification groups. The supplied ZIP is 957,300 bytes, SHA-256 `be774f33019e41fc65011fe3a1014edd36ac3298181b04236583f4e39b88d675`. The separate terminal receipt matches supplied SHA-256 `08a569cbd069ce009c028e54a146b80fee817d59c7fc9915762dcfd65c7058e1`.

The archive has 261 safe unique regular-file entries and 260 manifest payloads. Every payload's byte count, SHA-256 and archived mode matches. The supplied extraction is byte-exact and has the exact inventory. All 144 source descriptors match their retained bytes and Git blob content identities: 142 branch snapshots at `a5622f7fdd5ffb40a387d860e41c2ebbe5291d6f`, plus two explicitly labelled observed-main snapshots at `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`.

The frozen checkpoint's `save_pending` state is historical. The separate receipt and current canonical `P07-DELIVERY.json` agree on confirmed `complete_partial_delivery`. The canonical delivery bytes match their receipt descriptor at `c99f44aaec10445b96deb2b451b1a860a1027401`. All differences between frozen source snapshots and the current local tree fall within the terminal receipt's declared publication paths. The nine adopted P07 payloads are unchanged and match adoption hashes. P07's independent acceptance record matches its adopted hash.

Current branch/main/PR/issue ownership is the Director's independently observed state, not a new live Git observation by this reviewer. No main lease or integration authority is assigned. R01/R02 remain done; R03/R04/R05 remain not_done; P02 and parent C271 remain in_progress. PR #274 and issue #273 remain open under the supplied state.

## Required P08 implementation acceptance

The adopted `HI` stage permits only the new `prototypes/static_tray_v01/current_host_inspection_v01.py`, focused `tests/test_current_host_inspection_v01.py`, and corresponding phase documentation/evidence. Nested records left abstract by P07 may receive concrete closed shapes as implementation detail; this cannot weaken their required bindings or change existing P06 schemas/consumers.

1. Separate the externally supplied approved plan digest from observed content. Strictly decode the executable inspection-plan schema, all required closed shapes, absolute normalized paths, descriptor types and finite bounds. Reject the nonexecutable P07 design plan and any self-approval/template fields. Static mode must consume no fresh observation paths and start no Node/ldd/checker.
2. Bind the module's canonical source, clean commit/tree and complete source inventory, approved Python/runtime/metadata/Git inputs, exact retained Node candidate/archive, 24-file dependency inventory, platform/boot and finite inspector/ELF/loader closure. Only the existing five bounded Git source reads may occur during static validation. Unsupported or unexplained loader semantics must refuse.
3. Implement the strict bounded `ldd` parser and exact path/SONAME/interpreter/vDSO-set checks. Parsing cannot authorize a newly observed library.
4. Implement observation flow for later use, exercised here through explicitly labelled mocks only: two fixed commands once each, fixed five-variable environment, five-second total allowance with three-second active work and two-second cleanup reserve, unchanged supervisor, pre/postflight revalidation, no retry. Preserve actual process records and attached exceptions.
5. Implement immutable no-replace evidence publication and exact owned-path/ancestor checks. Keep durable intent/start/outcome/failure history; an unresolved launch has exact count null and a retained lower bound, never invented zero. Lost final receipts, cleanup uncertainty, publication races and failed evidence writes must block success and the next command.
6. Emit exact P06-compatible inspection/HOST closed objects only after complete successful mocked control paths; candidate HOST remains `OBSERVED_UNAPPROVED` in sidecars. Reconciliation is read-only and never relaunches or infers success from PID absence. No bootstrap `validate_selection` call with a fabricated HOST.
7. Freeze independent positive/refusal control selection before author execution. Identify precise source/test/fixture/mocking boundaries and preserve failures. Candidate-specific independent review must resolve mandatory findings. Applicable workflow/documentation checks and verified saved partial delivery remain required; the full routine is explicitly deferred by this phase.

## Protected boundaries

Keep the P05 adopted contract and all P06 consumer/provider/probe/schema/preparer, original supervisor/coordinator logic, exact original seven methods and both shared helper bodies unchanged. Preserve scientific JavaScript, reference construction, seven Python pins, 24 dependency bytes, selected Node build, original process/source/data budgets, twelve structural manifest slots and absence of `unused-native-schedule`. No new generic wrapper/installer, source exclusion, loader substitute or supported-platform expansion.

Stop before H0 runtime preparation, actual H1 observations, H2 operational freeze, H3 Gate H, the original seven methods, P06-H01/H02/H03, Gate R full routine, main integration or parent closure. Focused filesystem and mocked process controls cannot establish any of those outcomes.

## Failures and uncertainty retained

`INTAKE-ATTEMPTS.json` preserves two reviewer-script assumptions and their corrections. Attempt 001 wrongly interpreted embedded terminal evidence as repository paths and stopped with FileNotFoundError. Attempt 002 wrongly required observed-main snapshots to use the branch revision and reported one false blocker. The original scripts and second result are retained. Corrected attempt 003 passed all 20 groups; no supplied input was changed.

Historical C270 broad-driver completion remains unknown. Global prior-process termination remains unestablished. The receipt lists no current P07 unknown operation; this intake does not prove any global process state.

Next reviewer action: await the Director's confirmed P08 early save, then freeze controls independently and review the exact implementation candidate when assigned.
