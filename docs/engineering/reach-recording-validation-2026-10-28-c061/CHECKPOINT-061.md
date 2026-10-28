# C061 measured decision

## Outcome and scope

**Finite NO-GO for isolated independent-reader axial-ancestry reuse and its attachment-helper fallback.** C061 completed the single four-request attribution round specified by C060. No runtime candidate, fixture change, budget change, counter reset, failed-tail replay or full-corpus run followed. The proposed path is absent in P11 setup and small in L03 setup. A source-derived lower bound independently explains why removing only that observed L03 work cannot complete the unchanged downstream request.

The full evidence and source manifest are indexed by [README](README.md). The executed revision is `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`, tree `037157a58442ba1956597d32e1e540802f9ed896`, on the explicit C060 dependency `00533b953ed345cbf5fa13eaa56aafa3a2f052a8`. The source input is a verified partial checkout: 491 files, 9,527,653 bytes, with 2,890 other tracked entries explicitly omitted. All 65 runtime files needed by these requests were materialized and unchanged.

## Instrumentation and audit boundary

The new collector is a separate diagnostic driver derived from the unchanged C060 collector. It installs 18 bounded high-level setup wrappers only inside the admitted reader, restores them before the first original `_key_comparisons` call, and restores again on reader exit and in `finally`. It does not replace the low-level work charge, native arithmetic dispatch, callbacks, Fraction implementation, tracing or profiling machinery. The original C060 three wrapper names remain intact for its tightly delimited traceback comparison.

At coarse boundaries, the collector reads detached native shared/Reach counters, all Reach categories, request cache occupancy and the existing independent reference cache. Nested `_phase`, `_axial_derivatives`, and axial-only `_l1`/`_axis_transport` spans contain shared/Reach/checkpoint scalars and bounded typed descriptors. There is a 4,096-span and 64-depth observation bound. Full category attribution is available at coarse boundaries only; nested per-category maps are not inferred.

The new standard-library auditor imports the exact unchanged C060 auditor, verifies its hash, and preserves its source, command, exception, work, byte and census checks. It adds balanced event replay, scalar inclusive/exclusive reconciliation, typed input validation, setup cache checks and explicit residual accounting. It never imports product modules or continues a failed request.

| Component | Bytes | SHA-256 |
| --- | ---: | --- |
| New collector | 50,678 | `b90854f1a73053a3f9f9ebd7b67662d27b788f478a39a36cbc95abad2429183e` |
| New auditor | 41,586 | `ef322586e7693647f07f6901737611c82c844e2a6ed98578f499ac49bf994602` |
| Unchanged C060 auditor dependency | 71,385 | `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf` |

## One original round, four failed product requests

Root alone ran P11 control, P11 capture, its offline audit, then L03 control, L03 capture and its offline audit during the declared exclusive window. Every collaborator had explicitly paused before execution. Both pairs pass the independent audit with zero observation errors: 381,009 assertions for P11 and 677,251 for L03. The four actual product processes all exit 1 at the unchanged cap.

Input hashes before and after each request are identical. Within each pair, the complete admitted work-category totals and original exception/product traceback agree; all three retained reader-input copies are byte-identical. The final shared count is 100,001 because the refused shared tick occurs before a corresponding Reach category increment. The audit keeps that distinction instead of assigning a fictitious category to the refusal.

The requests retain the original revisions, float `fps=1.0`, `helpers=false`, P11 `end=3`, L03 `end=4`, tolerances, keys, carriers, geometry, clocks and certificate coverage. The operation cap remains 100,000, elapsed cap 30,000 ms, operand cap 32,768 bits, existing caches 256 entries each and cursor cap 64 updates. Observational equality on this execution is not a guarantee about future runs or elapsed time.

| Frontier | P11 | L03 |
| --- | ---: | ---: |
| Construction shared work | 7,391 | 4,499 |
| Reader entry | 61,415 | 54,988 |
| First key entry | 84,586 | 72,173 |
| Entered / provisionally returned key calls | 37 / 36 | 154 / 153 |
| Partial key index | 36 | 153 |
| Wholly unvisited keys | 15 | 24 |
| Carriers | 20 | 6 |
| Provisionally traversed interval/carrier rows | 700 | 912 |
| Interval/carrier rows not yet traversed | 320 | 150 |

The source batch has not completed final admission at refusal. A provisionally returned key or traversed row is not an accepted result. Complete request cost and all unexecuted tail costs remain unknown.

## Disjoint setup ledger

The following coarse stages are disjoint. The residual retains unwrapped certificate identity and source-batch admission work rather than assigning it to a guessed function. Nested rows in the next table overlap their parents and must not be added to this table.

| Coarse stage | P11 shared operations | P11 checkpoints | L03 shared operations | L03 checkpoints |
| --- | ---: | ---: | ---: | ---: |
| Supplied GLB read | 3,857 | 1,196 | 2,299 | 641 |
| Numeric basis verification | 199 | 0 | 199 | 0 |
| Source program metadata | 48 | 48 | 15 | 15 |
| Independent reference construction | 2,815 | 2,815 | 2,589 | 2,589 |
| Complete boundary states | 1,530 | 1,530 | 1,761 | 1,761 |
| Metadata verification | 18 | 5 | 13 | 0 |
| Retained clock verification | 768 | 0 | 2,504 | 0 |
| Independent geometry bounds | 5,559 | 1,350 | 2,342 | 540 |
| Geometry validation | 111 | 111 | 30 | 30 |
| Source phase tables | 4,856 | 4,836 | 3,053 | 3,047 |
| Final endpoint point phases | 1,230 | 1,230 | 277 | 277 |
| Boundary allowances | 18 | 0 | 18 | 0 |
| Projection assertion | 1,095 | 0 | 1,004 | 0 |
| Retained track preparation | 40 | 0 | 12 | 0 |
| Explicit unwrapped residual | 1,027 | 0 | 1,069 | 0 |
| **Total** | **23,171** | **13,121** | **17,185** | **8,900** |

| Nested source function | P11 calls | P11 inclusive / exclusive | L03 calls | L03 inclusive / exclusive |
| --- | ---: | ---: | ---: | ---: |
| `_phase` | 60 | 6,006 / 6,006 | 24 | 3,300 / 2,924 |
| `_axial_derivatives` | 0 | 0 / 0 | 4 | 376 / 174 |
| `_l1`, observed only inside axial calls | 0 | 0 / 0 | 22 | 132 / 132 |
| `_axis_transport`, observed only inside axial calls | 0 | 0 / 0 | 14 | 70 / 70 |

All nested operations in this table are checkpoint charges. P11 has 93 completed spans / 188 endpoint events; L03 has 83 / 168. No span is left open at the first-key cutoff. The generic setup checkpoint pool was therefore not evidence that all of it belonged to the proposed axial path.

## What repeats, and what that does not establish

L03 has two axial calls in each of `[0,2]` and `[2,3]`, for `rig.arm.forearm.frame` and `rig.tool.frame`. Each pair costs 188 operations in total. The two phase states have distinct process-local identities. Within the four axial calls, `_l1` observes float vectors `(0,0,0)`, `(1,0,0)` and `(0,1,0)` 12, 6 and 4 times respectively, each costing six operations. `_axis_transport` observes the float identity quaternion and integer axis 2 fourteen times, each costing five operations. Each typed group has one observed result variant.

These are bounded within-run observations. They do not prove immutable source equality, valid reuse across phases, preserved cancellation/error precedence or cache admission authority. They do not describe helper calls outside the axial walk. Source admission, lookup, insertion, eviction, displacement and fallback costs remain unmeasured because no cache was implemented.

For the specific hypothetical fresh lazy helper cache using the existing `_Arithmetic.lookup` and `remember` on all four observed typed groups, the most optimistic repeated-only gross saving is `202 - (3*6 + 5) = 179`. The 36 lookups and four first inserts alone cost at least 40 ticks in the unchanged arithmetic API, so its optimistic saving is at most 139 before other required work. This is a screen for that exact design, not a measured saving or a bound on all possible algorithms. The broader isolated axial-path screen below is sufficient to stop C061.

## Conditional source-derived lower bound for the isolated L03 target

The raw ledger and retained byte census establish 24 wholly unvisited keys, six carriers and 150 interval/carrier rows not yet traversed at the original refusal. The unchanged [reader implementation](../../../ontokin/reach_conformance.py) requires distinct future charges:

| Mandatory future charge | Source location / order | Minimum count |
| --- | --- | ---: |
| `independent_key_pose` | `_key_comparisons`, once per carrier for each wholly unvisited key | `24 * 6 = 144` |
| `independent_interval_claim` | `_IntervalCertificateClaims.check`, before its local shortcuts | 150 |
| `independent_sufficient_arc_domain` | `_certified_stored_arc`, before its local shortcuts | 150 |
| `independent_certificate_member` | `_CertificateBatch.add`, unconditionally for each row | 150 |
| **Selected mandatory future ticks** | These are separate events, not overlapping estimates | **594** |

Assume an isolated setup change preserves exact setup outputs and all downstream control paths, charge behavior, source admission and cache effects, while removing at most the complete 376 observed axial-setup charges. Starting from the 100,000 successfully admitted ticks, even the impossible best case of deleting all those charges with zero replacement overhead requires at least:

`100000 - 376 + 144 + 150 + 150 + 150 = 100218`.

This exceeds the original cap. It ignores the refused tick, the rest of the partial key, all other future arithmetic, clocks, comparisons, final source admission and flush work. It therefore does not estimate the complete cost. The 150 rows include the interval whose right endpoint is the partial key, plus 24 later intervals; they do not duplicate the 144 wholly unvisited key admissions.

This conditional screen rules out the isolated setup target as a complete L03 remedy. It does not rule out an algorithm that changes downstream work, another structural target, combined changes or a future separately proved cache effect. P11 needs no such bound for this candidate: it executed zero axial setup calls.

## Negative evidence controls and review

Two fresh offline audit invocations consumed deliberately changed setup files while all original product inputs remained untouched. P11 duplicated one setup event and was rejected with `Duplicate or out-of-scope setup event`. L03 changed a coarse checkpoint scalar without changing the category map and was rejected with `Setup checkpoint scalar differs from the full category map`. Each actual audit exits 1. Both original files were restored in `finally` and their original byte hashes rechecked. The archive retains the originals, altered copies, actual error output, command receipts and restoration receipts.

Independent static reviews cover source/dispatch behavior, measured costs and the lower-bound assumptions, typed descriptor scope, original evidence integrity, negative controls and the proposed next scope. Their exact files and hashes are preserved in the evidence archive and review copies beside this checkpoint. The external command runners are also preserved; their hashes alone would not make the actual invocations reproducible.

## Stop state

C061 stops at a reviewed diagnostic NO-GO, with four product requests used out of a maximum eight. No conditional candidate round was justified. The twelve unavailable historical archive payloads still block the unchanged documentation gate. A draft dependent PR is reviewable but not accepted into main. See [handoff](HANDOFF-061.md) for the exact remaining work and [next task](NEXT-TASK.md) for the separate proposed continuation.
