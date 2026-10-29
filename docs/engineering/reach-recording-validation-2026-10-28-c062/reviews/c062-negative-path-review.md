# C062 independent authority and negative-path review

Source: `Omegapy/OntoKin` at `e5e99b92e4efa541b434abcdda5c2ec31dda6a39`, tree `fb17897b2de27b79cf1b9aa790c7c354e17855d3`. Runtime files were read from the verified C061 portable packet. This review performs no product request, test execution, source edit, new measurement, or external write.

## Decision

No concrete positive source-authority premise was established for a new C062 attribution run. The following finite candidates should stop at source review:

1. Reuse ancestry by state/model/token/grip identity without fresh source-field admission.
2. Treat the existing `_SourceBatch` as authority for the setup `_phase` calls.
3. Replace each reused parent visit with at least one fresh charged source-receipt admission, while adding descriptor/cache bookkeeping.

The first candidate lacks source authority; the second uses a transaction that has not started at the relevant call sites; the third has no positive operation saving under its stated per-node admission design. This is a finite rejection of these designs, not a proof that every shared-graph algorithm is impossible. A separately designed setup transaction remains an unproved architectural hypothesis. The entire measured `_phase` cost must not be attributed to ancestry.

## Proven source boundaries

`_ancestry` calls `_incoming` before even the world special case, resolves an optional initial site, and then executes one charged checkpoint before each parent-loop visit. It returns the root, offsets, ordered joints, and ordered source path. Site membership/owner/pose, relation membership/type, follow parent/offset, joint kind/parent/child, and parent/child site fields affect these results. Cycle/depth rejection occurs after the loop checkpoint. [`ontokin/reach_reference.py:4207-4245`]

`_phase` discards the returned offsets but still calls the original complete `_ancestry` helper. Removing offsets list appends alone removes no parent-loop charge, and skipping their source reads can change the first failure. [`ontokin/reach_reference.py:4821-4822`, `4207-4245`]

The existing incoming-graph cache captures active grips and uses a private model token. It holds a read-only relation mapping, not a complete ancestry descriptor. Later parent/site fields are still read by `_ancestry`. The source comment about private topology does not provide a checked mutation epoch for those mutable records. [`ontokin/reach_reference.py:2436-2459`]

Other existing caches are not a new saving: `_phase_cache` already reuses complete phases, `_source_basis` already shares source-bound numeric graph work by state/interval, `_joint_path` already caches coordinate laws, and `_phase_root_poses` already admits complete typed root pairs. [`ontokin/reach_reference.py:4152-4195`, `4247-4304`, `4625-4776`]

## Why the current source batch cannot fund setup reuse

The supplied-byte reader calculates all phase tables and final endpoint phases at `reach_conformance.py:3555-3556`. It calls `_verify_certificates` later, at line 3598. The existing `reference.recording_source_batch(...)` begins only inside `_verify_certificates`, at line 3456. Consequently, the setup ancestry calls do not run inside that source transaction.

The existing transaction has a precise and narrower contract:

- Its entry binds the model, five source maps, arithmetic/check/work owners, immutable boundary axis, history lists, and header. [`ontokin/reach_reference_plan.py:31-35`, `61-97`]
- It registers specific captured plans and actual receipts with caps of 16 plans and 1,024 receipts. [`ontokin/reach_reference_plan.py:23-27`, `106-132`]
- It precharges final receipt reads before the last checked callbacks, then performs complete callback-free source admission after report conversion. [`ontokin/reach_reference_plan.py:172-239`; `ontokin/reach_conformance.py:3443-3445`, `3455-3473`, `3560-3563`]
- It discards only its still-owned cursors on rejection and preserves independently completed nested replacements. [`ontokin/reach_reference_plan.py:139-170`, `241-258`]
- Only its own exact final-domain restart object permits ordinary replay; caller exceptions and source-identity failures retain their identity and precedence. [`ontokin/reach_conformance.py:3477-3492`; `ontokin/reach_reference_plan.py:202-223`]

Moving entry earlier or adding setup descriptors is therefore a new transaction design. It needs explicit coverage of setup outputs and their caches, source fields absent from endpoint plans, all intermediate callbacks, public `phases`/`point_phase` use outside the reader, reentrant readers, and setup failures before the certificate loop. The existing final admission cannot be assumed to cover these changes.

## Fresh-admission cost screen

Let `h` be the number of charged parent-loop visits a candidate intends to omit in one ancestry request. The original loop contributes exactly `h` checkpoints, independently of the unchanged `_incoming` work. [`ontokin/reach_reference.py:4219-4245`]

For the specific candidate that freshly admits each saved ancestry node with the existing source-receipt model, the added charged admissions are at least `h`. `_recording_capture` charges before reading a source record; a retained ordinary plan likewise charges before rereading each actual receipt. Thus the net saving is at most `h - h = 0` before additional capture, lookup, insertion, eviction/displacement, invalidation, and fallback costs. [`ontokin/reach_reference.py:2624-2633`; `ontokin/reach_reference_plan.py:379-400`]

This bound applies only to that per-node receipt design. It is not an exact P11/L03 ancestry count and does not rule out a different complete transaction or a separately proved admission scheme. No source evidence in this review establishes such a cheaper scheme.

## Required negative paths for any future positive design

| Case | Required behavior and supporting source/test contract |
| --- | --- |
| Equal model, source-map, or arithmetic-owner replacement | Rebind or reject; value equality does not authorize detached owners. `reach_reference_plan.py:31-35,85-97,369-399`; `test_reach_reference_phase_plan.py:371-433`. |
| Changed native dispatch, check owner, or observation hook | Establish live method/owner authority at the omission boundary; a familiar class name or cache key is insufficient. The existing partition observer explicitly checks `_Arithmetic.tick` dispatch and owner identities: `reach_reference_plan.py:544-579`; ordinary ticks call the live `check` and captured observer: `reach_reference.py:107-111`. |
| Changes within the same model/state identities | Recheck the actual source fields, including topology edits and site placement. `test_reach_reference_phase_plan.py:211-240`. |
| Transient mutation restored before final admission | Computation must consume detached immutable operands, so restored mutations cannot enter intermediate calculations. `test_reach_reference_source_batch.py:172-198`; `test_reach_reference_phase_roots.py:136-166`. |
| New or redirected relation outside a formerly selected path | Prove the absence/root relation against complete topology; checking only previously visited edges is insufficient for a new captured graph. Existing builder covers all relation endpoints and collection counts: `reach_reference_plan.py:620-657`. |
| Grip, phase, boundary-side, or history-slot change | Bind the current source domain and actual history slot; do not borrow another state's path. `reach_reference_plan.py:67-97,192-201`; `test_reach_reference_source_batch.py:146-170`. |
| Missing relation/site or cycle/depth failure | Preserve original traversal and first-failure precedence; avoid eagerly failing unrelated paths. `reach_reference.py:4213-4245`. |
| Callback cancellation or arbitrary exception | Preserve the original exception object and do not publish a partial descriptor/pose. `reach_numeric.py:71-94`; `test_reach_reference_source_batch.py:200-227`. |
| Source change together with cap narrowing | Reject source identity before considering optional domain replay. `reach_reference_plan.py:202-223`; `test_reach_reference_source_batch.py:269-279`. |
| Callback throws a private restart type | Do not reinterpret it as the optimization's own retry signal. `test_reach_reference_source_batch.py:431-448`. |
| Original arithmetic failure before a later cap restoration | Propagate the first failure; no replay to obtain success. `test_reach_reference_source_batch.py:450-471`. |
| Nested reader or cache eviction | Preserve completed nested writes, ordinary eviction, and the 64-step recurrence ceiling. Do not restore or retain hidden numeric cursors. `reach_reference_plan.py:139-170`; `test_reach_reference_source_batch.py:79-109,229-248`. |
| Unsupported/foreign domain or optional storage cap reached | Use the complete ordinary path on the same work context, with no counter reset or extra retained history. `test_reach_reference_source_batch.py:250-267,281-359`. |

A structural descriptor may retain bounded immutable source operands and paths. It must not become a second table of completed poses, coordinate laws, or evicted numeric cursors. Existing caches still require their charged lookups/inserts and current operand admission. [`docs/engineering/reach-reference-phase-plans.md:29-46`, `134-142`; `ontokin/reach_reference.py:340-362`]

## Test-source verification and limits

The portable packet omits the tests directory. The following three files were read at the exact C061 commit through the authenticated GitHub file API. Their returned UTF-8 bytes were independently hashed as Git blobs and matched the authoritative packet source index. No test was executed or added to the packet.

| File | Bytes | Verified Git blob |
| --- | ---: | --- |
| `tests/test_reach_reference_source_batch.py` | 27,994 | `5bccd52176f6d5bcb212f9f6b4d39d5dbdca84de` |
| `tests/test_reach_reference_phase_plan.py` | 27,763 | `8a079897b16d1c840fcf20c958906518681188c0` |
| `tests/test_reach_reference_phase_roots.py` | 16,667 | `be9c6af33821e64885aed471d8c084f7d907fc31` |

These tests constrain existing source-plan/root behavior and identify requirements for a proposed ancestry optimization. They do not demonstrate that the unimplemented ancestry candidate passes those requirements.

## Practical next distinct task

The nearest concrete engineering task is recovering the twelve exact historical archive objects, passing the unchanged documentation checker in a complete identified checkout, and reviewing the C060/C061 dependency for development integration. This advances a known unmet gate without reopening a rejected runtime target.

If further ancestry work is selected later, require a distinct design decision for a reader-owned setup source transaction before any new product instrumentation. Its acceptance question is whether a bounded complete immutable source graph and final admission can cover setup phase outputs while preserving original failure precedence and funding all capture/admission costs. That is an unproved alternative architecture, not a positive C062 premise or an authorized automatic continuation of this review.
