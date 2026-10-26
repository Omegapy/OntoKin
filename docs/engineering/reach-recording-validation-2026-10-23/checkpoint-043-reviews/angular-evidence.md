# C043 independent retained-evidence review

Reviewer: `/root/angular_evidence`. Date: October 26, 2026, America/Denver. Scope: source, JSON and AST inspection only. Parent: `00606a16be62631179b50255d4de8daa34f8f196`, tree `9d9dd9f77b976c4b8b2076b8f5a0c4f87aa82342`.

## Decision

The historical evidence establishes **32 completed cold `recording_float_excess` calculations, all with `include_cell_radii=False` and `dynamic=False`, during the first captured sample at exact time `1/26`**. They cost 960 charged operations in total. This sharpens C042's historical census with selector and phase-placement facts.

It does **not** establish the exact angular tuples `(t,c,sq)`, spatial tuples `(l,m,sp)`, bound-to-frame sequence, or eligible angular repeat count. The current retained request records 32 domain charges but lacks the per-call records required to transfer the old cold/warm classification or close a new cache design. **No positive complete cost proof, runtime implementation, or new diagnostic is selected by this review.**

## Evidence and source binding

The primary retained records are under `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-042-retained/` in the parent tree:

| Record | Bytes | Git blob |
| --- | ---: | --- |
| `020/execution/p23-sampling-observer-001/P23.json` | 509,914 | `897e22e1ffc102a11f07e39b68533b6cd8f19013` |
| `020/execution/p23-sampling-observer-001/executed-driver.py` | 21,744 | `4afad6fdbe5a328bd25eb907ace6591746aec039` |
| `020/execution/p23-sampling-observer-001/inputs-before.json` | 471,178 | `56a5a048262d749209c9024014135a73cd8dee57` |
| `035/execution/original28-002/P23/request-result.json` | 15,341 | `189c533da3cabfc1d6d8d2a31533ed4d38b948cc` |
| `035/execution/original28-002/inputs-before.json` | 416,493 | `5bd4f79929632cfb02685aeec43e85f5378ace7c` |

Actual local bytes match these authenticated blob/size identities. The selected old runtime files additionally match SHA-256 and Git blob identities in the original C020 input inventory. Selected current runtime files match the C035 input inventory. The complete selected-file identities, exact source ranges and static checks are in the accompanying independent JSON record.

C020 names runtime `88473124cc058f7e2926a04d79ab38e340ab4407`, tree `02efa05c691ff31258e39c16b98044d2a47fda20`. C035's retained inventory names `4ca73909f861fe4bef9694787473621c1d21c140`, tree `87c949b238055af1ce368c694e1d5683c8aeacde`. Both requests used end `3`, integer fps `1`, helpers false, position/rotation tolerances `0.001`, time tolerance `0.000001`, and max operations 100,000. Their failures remain 100,001 shared operations; completed reach totals are 80,033 and 80,801 respectively.

The original inventory discloses 37 omitted historical archives. This review neither repairs that historical execution boundary nor claims to have revalidated complete original archives. It reads the exact selected members already retained by C042 and newly fetches two original source files by immutable commit. The latter match C020's own input inventory.

## Reconciliation of the historical 960 charges

The old observer selected `recording_float_excess`, but not its numeric `exact`, `compare`, lookup, remember or `_upper_float` subroutines. Consequently their work stays attributed to the selected function. The observer's nearest-selected-frame attribution and scope construction are explicit in `executed-driver.py`, lines 202–310.

The `stats` and sole `scoped_stats` row both report 32 calls and 960 inclusive/self request/reach operations in `recording_sampling`. The attributed `charge_stats` row is exactly:

| Category | Retained count | Per completed calculation |
| --- | ---: | ---: |
| `recording_float_excess_domain` | 32 | 1 |
| `cache_lookup` | 32 | 1 |
| `exact_add` | 320 | 10 |
| `exact_mul` | 448 | 14 |
| `exact_compare` | 64 | 2 |
| `cache_insert` | 32 | 1 |
| `cache_evict` | 32 | 1 |
| **Total** | **960** | **30** |

There are no attributed promotions. Under the original native `lookup` body, a present member attempts a promotion charge; no such path is represented here. All 32 whole-result lookups are therefore cold. The domain/lookups and complete arithmetic/publication counts agree, so the 960 operations cannot be treated as 960 removable arithmetic operations.

The original `exact` implementation charges, guards both operands, guards prospective numerator/denominator widths, executes the Fraction operation and guards its result. `compare` separately charges and guards operands/prospective cross-products. The function itself performs no local exception recovery. Its base cold route contains 24 exact arithmetic operations—10 adds and 14 multiplies—and two range comparisons.

The dynamic position branch would add three exact adds and one exact multiply. The retained totals leave no such additional work. Cell radii would invoke two `_upper_float` paths, each beginning with `recording_cell_radius_domain`; that helper is not separately selected by the observer, and the complete request has zero such domain charges. Thus every historical cold calculation used **both selectors false**. This is a source-reconciled historical deduction, not a sampled selector field in the old JSON.

All 32 insert and eviction charges completed. No promotion, refusal gap or extra dynamic/radius work is hidden in the attributed row: requested amount, shared increment and reach increment are all 960. The record has no observer anomalies and no unreturned selected frames or work charges. Its final failure is later in ordinary position projection at `work.charge("binary64_round")`, not in an envelope calculation.

## What is known about placement and order

The historical observer records one successful `begin_captured_phase`, 51 `_CapturedPhase.sample` calls and one completed `_CapturedPhase.finish`. It records no `_sample_planar_frames` invocation and no phase-restart charge. The first captured sample is retained individually:

- Call ID: 459229.
- Exact time: `1/26`.
- Shared operation window: 79,732 to 82,476.
- Reach operation window: 59,765 to 62,509.
- Returned value is non-None.

The captured phase starts with `self.excesses=None`. Its first sample loops through bound records, computes the per-frame excesses and stores one immutable mapping; later samples reuse that mapping. Those first-sample calls complete before the next sample. This places all 32 historical envelope calculations inside the recorded first-sample window. It does **not** recover a serial ID, exact start/end cost, actual frame name or exact bound fields for any one of the 32 calls.

The source loop fixes order relative to its captured `bound_records`, but that ordered list is not retained. Calling the same source mechanism 32 times does not reveal the missing list.

## Why the individual records cannot supply the tuples

The observer retains a selected function individually only when it is named in `DETAILED` or costs at least 128 request operations. `recording_float_excess` is absent from `DETAILED`; each completed historical call costs 30. There are **zero** entries for it in the individual `calls` list.

Even had a thresholded entry survived, `metadata()` copies only a narrow whitelist: `time`, `start`, `end`, `horizon`, `side`, `path`, `value`, `pose_only`, `recording`, `recording_proof`, and `inverse`, and only for supported scalar types. It does not serialize `bound`, its six fields, `include_cell_radii`, `dynamic`, cache keys or cache membership. The capture also stores aggregates rather than a complete ordered charge stream. The original observer cannot reconstruct the requested exact tuple sequence from data it never wrote.

## Applicability to current source

`recording_float_excess` is structurally unchanged: original lines 362–421 and current lines 527–586 have AST SHA-256 `1f8ad241fb956be654207b233d93c2e2f32e89fce793ec308f3ae0c373d27474`. `_CapturedPhase.__init__`, `.sample`, `.finish`, and `begin_captured_phase` are also structurally unchanged. The complete `reach_phase.py` bytes are identical across old and current inventories, blob `9bae69ea6bda16fbbd841480139443cdbfe63d6f`.

This is narrower than execution identity. `_sample_graph` changed, as did surrounding runtime and charge code identified in C042. Before an envelope lookup, graph execution has already performed shared-cache work. The target body and bound-builder identity therefore do not supply the current sequence of cache states.

Current P23 retains `recording_float_excess_domain=32` and `recording_fast_endpoint_allowance=32`. Its category map is request-wide, without function/scope attribution or ordered key entries. It does not contain the six numeric values or their bound-to-frame association. The current final failure is still the `_constant_pose` lookup's charge before membership, as C042 established; it is unrelated to an observed `recording_float_excess` cache classification.

The unchanged P23 fixture has 32 mounted arms, translated along y by exact quarter-meter steps, with similarly authored reach actions. That source vocabulary makes common angular inputs plausible. It is not a retained list of actual envelope calls. The phase-bound builder composes source, coordinate and error bounds and caches intermediate results. This review does not substitute an assumed identical angular signature, guessed `trig_count`/`product_count`, or a product-code numerical reconstruction for the absent tuple record.

## Exact gap and consequence

The missing datum is an **ordered current per-call record** binding each envelope calculation to:

1. Its source frame and phase, actual native `t` and `c`, and the exact numerator/denominator fields of `sq`, `l`, `m` and `sp`.
2. The two actual boolean selectors, current operand limit and whole-result cache key.
3. Lookup membership outcome or refusal, completion through original arithmetic/range guards, and publication outcome.
4. Relevant intervening shared-cache mutations and source/work/callback authority sufficient to assess a proposed reuse lifetime.

Without that record or an independently complete static proof of equivalent facts, the count of eligible repeated angular signatures remains unknown. `14*r` is conditional gross work only. The historical maximum `14*31=434` still assumes that one completed admitted angular result can serve all remaining calls; it is not measured saving or a current P23 bound. Thirty-two historical whole-result evictions also show that inserting extra shared-cache entries cannot be treated as free of effects on other reuse.

A future diagnostic would need a separately declared execution scope and current source closure, the untouched original P23 request/caps, neutral control/capture criteria, exclusive execution and preservation of every failure. This review schedules none. It performs no product import, request, runtime test, numerical replay, benchmark or changed-source execution.

## Static verification performed

The accompanying analysis-only script parsed JSON and Python ASTs, verified selected file lengths/Git blobs/SHA-256 values against authenticated trees and retained inventories, reconciled the arithmetic and charge counts, checked absence of individual entries, checked historical first-sample placement, and confirmed the explicitly listed old/current source relations. It passed **41 assertions**. These are evidence checks, not product tests. Review source and data remain separate from release acceptance.
