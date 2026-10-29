# C062 independent ancestry cost review

Review scope: source-only examination of ordered ancestry sharing inside `ReachReference._phase -> _ancestry`. Source baseline is final C061 `e5e99b92e4efa541b434abcdda5c2ec31dda6a39`; the unchanged runtime and frozen diagnostic evidence identify executed tooling `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`. This review imports no OntoKin module and executes no product request or test.

## Decision

The present evidence does not establish a specific safe, positive-net-cost descriptor cache. The straightforward design that retains `_incoming` and re-admits one bounded native source record per original object visit has no positive warm-hit operation saving, before insertion, eviction, displacement, invalidation or fallback costs.

An independent conditional ceiling also rules out **isolated replacement of all setup `_ancestry` work as a complete repair of either original recording**, when exact setup outputs and all downstream control paths, charges, source admission and cache effects remain unchanged. Even granting free removal of the complete bounded target yields necessary-work lower bounds of **100,549 for P11** and **100,358 for L03**, both above 100,000.

These are separate conclusions. A complete-remedy ceiling does not prove that no small beneficial increment or combined algorithm exists. The review does not claim a universal lower bound on every conceivable source-authority scheme, or measured ancestry timing, cache misses, speedup or complete request costs.

## Original charged work

`ontokin/reach_reference.py:4207–4245` calls `_incoming` once, then charges one `a.tick()` per object-loop visit at line 4220. The initial site frame, if present, adds an offset and path member before that loop. A follow to world terminates without adding an object-root visit. The retained P11 and L03 paths exercise neither exception: every phase starts at an independently enumerated object frame, alternates object frames with known relations and ends at `rig.frame`.

The `_phase` result stores the ancestry path unchanged (`reach_reference.py:4822,4846`). Its other numerical work is outside this target. Removing unused offsets list appends does not remove the charged loop visits.

The frozen C061 `reader-setup.json` members contain 60 P11 and 24 L03 returned phase spans. Their paths imply respectively **171 and 68 original object-loop visits**. This is a source-derived census from already recorded outputs, not a new `_ancestry` measurement. The measured phase bodies total 6,006 and 3,300 operations and contain considerable other work.

### Pinned source expansion

The source counts are explicit expansions of the unchanged `.ok` definitions, with each source byte hash checked by the offline calculator:

| Case | Source construction | Objects | Joints | Follows | Grips |
| --- | --- | ---: | ---: | ---: | ---: |
| P11 | One rig; five three-object PlanarArms; one head; three eyes | 20 | 11 | 8 | 0 |
| L03 | One BenchArm rig, column, arm, upper, forearm and tool | 6 | 2 | 3 | 0 |

Sources: `libraries/reach-assets.ok:10–40,42–70,73–125`, `libraries/reach-parts.ok:9–58`, `sources/p11-complete-segmented-character.ok`, and `draft2-supplements/sources/l03-completed-action-new-owner.ok`, beneath `docs/language-design/planar-reach-v0.1/`. P11 has two arms and three legs, each with two hinges and one follow; the head contributes one hinge; its three eyes contribute three follows. L03 has two hinges, the arm mounting follow and the column/tool follows. Neither source introduces a grip or release event. The retained GLB object/relation metadata is corroboration only; those bytes remain unvalidated reader inputs.

## Bounding `_incoming` completely

`reach_reference.py:2436–2459` charges `g` grip visits, one cache lookup, and on a miss one visit for every joint/follow plus one insertion. With the original empty grip sets, its cost is:

- Hit: 1.
- Miss: `1 + joints + follows + 1`.

Thus P11 has 20 additional ticks per miss; L03 has 6. This includes the original insertion charge. Allocation of the native mapping proxy adds no separate charge in this source. Cache-cap synchronization can add a tick only if the operand domain changes (`reach_reference.py:99–105`). The original recorded domain has the native callback chain, no user construction check and the unchanged 32,768-bit cap. It therefore contributes no reset to this particular original-run ceiling.

For L03, even assuming **every** call misses gives:

`68 + 24 + 24 * 6 = 236`.

For P11, an all-miss bound of 1,431 is unnecessarily loose. The fixed private-model token and empty grip set select the same incoming key throughout these original setup calls. Every lookup hit promotes that key; a miss inserts it as newest. A 256-entry LRU cache can evict it again only after at least 256 distinct later updates to other keys, counting promotions as well as insertions. This is **not** a claim that 256 new insertions are required.

The entire recorded interval from first phase entry to last phase exit costs 6,084 shared ticks. Granting the first call a miss, without relying on its initial LRU position, bounds later misses by `floor(6084 / 256)`. Thus at most 24 misses need be allowed:

`171 + 60 + 24 * 20 = 711`.

This is an upper bound, not an observation that 24 misses occurred. It deliberately counts all phase work and gaps as potential cache-update budget, even though most of those operations cannot update the cache.

### Cache-write and reset audit

The source premise for that LRU calculation is narrow and checkable:

- `_Arithmetic.lookup` and `remember` charge before their promotion/insertion (`reach_reference.py:340–362`); each modifies at most one LRU entry.
- The direct Cartesian rotation cache paths preserve the same charge before one promotion/insertion (`reach_reference.py:1337–1346,1383–1392`).
- `_Arithmetic.cache` is initialized once at line 79 and cleared by the live-operand-cap change at lines 99–105. The fixed original callback chain has no source that mutates that cap. `ReachExecutionWork.charge` calls the captured construction budget, whose `check` is null in both original captures (`reach_numeric.py:71–97`, `construction.py:75–87`).
- `_phase` calls ancestry, identity/root poses, source basis, optional axial derivatives, coordinate paths and root distances (`reach_reference.py:4821–4846`). This setup call graph does not enter the recording pose-plan or centered-cursor machinery. Consequently the deferred precharged writes in `_PendingCursors.publish` (`reach_reference_plan.py:341–354`) and the source-batch discard path are not hidden uncharged updates inside this interval. The centered reader's direct cache writer is also outside this graph; its ordinary updates have their own preceding charge (`reach_reference_center.py:282–315`).
- Model identity tokens and grip sets remain fixed for the original pinned sources and native callback execution. This premise is not a safe generic admission rule for a future optimization: hostile callbacks or replaced owners require explicit guards/fallback.

## Mandatory remaining work and no double counting

The calculator checks the preserved `key-ledger.json`, independent `work-ledger.json`, retained key count and geometry carrier identities. P11 entered keys 0–36 and returned 0–35. Fifteen keys were wholly unvisited. Its 51 total intervals contain 1,020 carrier rows, with 700 traversed and 320 remaining. L03 entered keys 0–153 and returned 0–152. Twenty-four keys were wholly unvisited. Its 177 intervals contain 1,062 carrier rows, with 912 traversed and 150 remaining.

The reader performs the complete next key comparison before any interval row for that key (`reach_conformance.py:3398–3416`). Therefore the remaining rows include the interval ending at the partial key plus every wholly unvisited later interval. No partial-key pose charge is counted below.

Distinct mandatory events are:

| Event | Source | P11 minimum | L03 minimum |
| --- | --- | ---: | ---: |
| One `independent_key_pose` per carrier at each wholly unvisited key | `reach_conformance.py:1957–1962` | 15 × 20 = 300 | 24 × 6 = 144 |
| One `independent_interval_claim` per remaining row | `reach_conformance.py:3329–3331,3414–3416` | 320 | 150 |
| One `independent_sufficient_arc_domain` per remaining row | `reach_conformance.py:2136,3426` | 320 | 150 |
| One `independent_certificate_member` per remaining row | `reach_conformance.py:2554–2558,3441` | 320 | 150 |
| Selected mandatory future ticks | Separate events | **1,260** | **594** |

Starting from the 100,000 admitted ticks, ignoring the refused tick, all other partial-key work, other future arithmetic and final admission:

`P11 >= 100000 - 711 + 1260 = 100549`.

`L03 >= 100000 - 236 + 594 = 100358`.

These bounds grant zero replacement overhead and free removal of every operation in the bounded ancestry target. They require unchanged downstream execution and cache effects. A design that changes those effects needs a new complete analysis; this result supplies no saving estimate for it.

## Added-cost and authority screen

The straightforward safe warm-descriptor proposal retains `_incoming` to obtain the relation map, then freshly admits one native bounded source record for each original object visit, then performs its new descriptor lookup. The original cost is `g + 1 + n` on an incoming hit. Fresh per-record admission alone costs `n` in the existing `_recording_capture` convention (`reach_reference.py:2624–2633`). Keeping `_incoming` and adding the descriptor lookup costs at least `g + 1 + n + 1`; it is already one tick worse before insertion, eviction/displacement, typed comparisons, original failure-path fallback or bounded-storage work. This rejects that concrete design, not every possible representation.

Eliminating `_incoming` as well requires proving the incoming relation domain, including added or redirected edges that could change a supposed root. The existing source-plan builder captures all relation endpoints for that reason (`reach_reference_plan.py:620–657`). It cannot be treated as already available setup authority: phase tables and endpoint phases execute at `reach_conformance.py:3555–3556`, while the complete source batch starts only inside `_verify_certificates` at line 3456, reached later at line 3598.

An amortized immutable graph could be a different design, but present private state/model identity does not establish immutability against callbacks. Moving source admission earlier or deferring it across setup changes its lifecycle and first-error obligations. There is no concrete reviewed positive premise for doing so in this scope. Measurements of repeated paths would not resolve that missing authority proof.

## Reproducible artifacts

- `c062_ancestry_cost_screen.py`: standard-library offline calculator; reads only the verified C061 parts and named nested members. It checks input hashes, explicit source expansion, every recorded phase path, original callback settings, key/row census and arithmetic. It imports no product modules.
- `c062-cost-screen.json`: actual output of that calculation. It lists exact input member names/hashes, all variables and both conditional bounds. Runtime premises are explicit; the script does not pretend to mechanically prove source control flow or the LRU lemma.

Both original failed requests remain failures. No new runtime behavior, source fixture, budget, numerical cache or release acceptance is selected by this review.
