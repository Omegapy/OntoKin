# C069 rejected existing-list receipt design

Design identity: `OK-DESIGN-PRODUCER-RECEIPT-069/0.1.0`. Status: **REJECTED FOR THIS ROUTE; NOT ADOPTED OR IMPLEMENTED**. This record refines C068's unadopted proposal enough to expose the missing authority and lifetime. It does not create a new host restriction or accounting rule.

## Concrete retained layout

The considered subject record has exactly 24 slots. Each holds one reference, scalar or flag; no slot silently contains an uncharged scan or copied collection. A referenced dispatch manifest would require its own explicit entries and costs. No complete authenticated manifest is claimed here.

| Slot | Field | Fact needed before publication/use |
| --- | --- | --- |
| 0 | request_work | The existing request's actual work owner. |
| 1 | construction_budget | Its original shared construction payer. |
| 2 | native_tick | Authenticated bound construction callback, not just a saved callable. |
| 3 | nested_check | Actual absence of a custom construction check on the original source path. |
| 4 | observer | Actual absence of the optional work observer. |
| 5 | operand_bits | Current full 32,768-bit domain; retained guards still execute. |
| 6 | max_operations | Same current shared allowance, never raised. |
| 7 | max_elapsed_ms | Same current time allowance, never reset. |
| 8 | max_cache_entries | Same bounded numerical cache, never enlarged. |
| 9 | decoder | Actual decoder for the supplied bytes. |
| 10 | binary | Retained immutable binary chunk and authenticated association. |
| 11 | document | Current interpretation of the supplied accessors and primitive. |
| 12 | accessor_index | Actual POSITION accessor for this occurrence. |
| 13 | stored_list | The same cached list whose current contents and interval are justified. |
| 14 | stored_count | Exact covered list length, with a maintained stability guarantee. |
| 15 | source_mesh | Actual independent producer result, including authenticated cache-hit provenance. |
| 16 | source_positions | Retained native immutable source tuple from that result. |
| 17 | source_count | Actual relevant source coverage. |
| 18 | source_recipe_key | Actual independently established recipe identity. |
| 19 | dispatch_manifest | Reference to separately funded authenticated code/storage dependencies. |
| 20 | lifetime_owner | Owner able to prevent or observe every relevant mutation, currently absent. |
| 21 | lifetime_version | That owner's justified version, not the unrelated numerical generation. |
| 22 | invocation | This cold invocation only; cannot authorize retries or later occurrences. |
| 23 | phase | Issuing, complete, consumed or invalid; every reached write is paid. |

The separate four-slot seed record would hold `seed_index`, `seed_row`, `lower_bound` and `pending`. It is published only after authorized paid seed preparation. The lower bound never becomes the returned radius. The future seed must be included and the original state synchronized before retirement.

## Issuance and paid use

The layout cannot be truthfully completed by the decoder alone. Slots 0–14 become subjects at different points of the actual request; source slots 15–18 become available at independent production or an authenticated hit. Slots 19–21 are the failed obligations: current source supplies neither an independent root for the manifest nor an owner covering the cached list's actual alias interval.

Under the proposed C068 units, allocation is one `C`; each populated slot is one `W`. This declared 24-slot record therefore requires **25 proposed units for allocation and one write per slot alone**. The four-slot seed record analogously requires five. Actual field capture is additional `R` work, each predicate is a separate `T`, binding claims use `B` only after passive storage is established, and every repeated read/write pays again. A fixed allocation does not populate its fields for free. These counts are illustrative for this design under unadopted units, not an accepted meter implementation or a complete cost.

Every consumer must pay the actual subject reads and tests it reaches. If each of the 24 fields were read once and subjected to one independent predicate, those bodies alone would add 48 proposed units; some facts need several predicates or a separate manifest. This example does not establish that those predicates suffice, or that all fields must be checked in exactly that schedule. It cannot repair slots 19–21.

The unit catalogue is not recursively applied to the native meter's administration. Authenticating that meter is still additional work. Existing charges cannot be reassigned to new optional checks after they have been consumed. No later charge funds an earlier foreign inspection or changes the first ordinary exception.

## Event and outcome map

[funding.json](funding.json) supplies the fixed event categories, payer, ordering, repetition and refusal behavior. All costs use the existing request's remaining allowance. Unknown bodies remain explicitly unresolved.

| Event | Required order and payment | Outcome |
| --- | --- | --- |
| R0 trusted entry | Before the first optional lookup/inspection/charge; every new bounded body must be funded by authenticated native work | **No current authority root. Route rejected here.** |
| R1 decoder fact issuance | Only after actual completed decode/finite proof; preserve association with actual binary and document | A birth fact covers that completed production, not future list contents. |
| R2 source fact issuance | Only after actual independent producer completion or authenticated retained completion on hit | Writer caches and nominal recipe equality are insufficient. |
| R3 interval maintenance | From decoder publication through intervening work, topology and the charged wrapper lookup; continue while omissions depend on the seed | **No owner covers direct list aliases.** Every proposed maintenance transition would need its own funded body. |
| R4 cold admission | After the original wrapper effects, bind actual invocation, cap, source, current list and coverage | A mismatched receipt can decline only before any dependent omission and without replacing the original pending exception. |
| R5 seed preparation | Paid row/leaf access and any non-reused type/domain checks; three absolute values, two additions and two downward-nextafter bodies; paid state publication | Never perform a future Fraction decode or expose its original error early. |
| R6 pending scan | Preserve every original point/conversion/error/guard event; charge every reached strict screen and pending-identity test | Omit only proven exact folds. Comparisons remain `S`/`I`, not also an `A` category. |
| R7 retirement | After actual seed inclusion and proved synchronization; pay phase/state/reference actions | An expired receipt supplies no later authorization. Foreign finalization cannot be silently suppressed. |
| R8 fallback/retry | Retain all reached added work; pay any reconstruction/replay/repeated admission once per occurrence | An exception/refusal is not a false predicate and cannot be refunded. After omission, ordinary continuation alone is not restoration. |
| W warm hit | Preserve the original warm verification and charges; do not create a seed schedule | No receipt from another invocation or request is reused. |

The whole-request terms in [C069](CHECKPOINT-069.md) are disjoint. R0 contributes to `A_router`; R1/R2 to `A_producer`; R3 to `A_lifetime`; R4 to `A_admit`; R5 to `A_seed`; R7 to `A_retire`. New comparisons at R6 are `S` and `I`. R8 restoration events enter `F` only when not already counted; repeated R0–R7 events stay in their original categories. Unchanged operations remain original work, not funding for new work.

On charge refusal, stop at the actual event and preserve counters, exception and diagnostic state. Construction increments before its over-limit check; reach calls the external payer before its own count check/increment. These are different retained orders. A partially issued receipt never becomes complete, an interrupted attempt retains its costs, and a new request receives no inherited receipt authority. Cold retries caused by recipe/cap/cache changes pay actual repeated events. Cache eviction or a numerical-generation change does not certify POSITION freshness.

## Rejected invalidation rules and possible different boundary

An epoch maintained only by `DecodedGLB.accessor` misses list item/slice writes and mutators. An epoch copied from `ReachExecutionWork` tracks different storage. Polling a list checksum or rescanning it is another paid current-content proof; it still needs authenticated execution and a stable interval after inspection. Installing a hook is not proof of exclusive ownership.

A separately designed native process could use a trusted launcher and a precisely constrained interface. It would need authenticated code/runtime/import state, explicit hooks/threads/signals/extensions rules, paid request setup and clear routing that preserves existing direct/custom/Agent behavior. No such implementation or semantic decision exists in this checkpoint. Merely asserting that host mutation is unsupported would silently change the question.

Because this route fails R0 and R3, a finite executable complete-cost schedule is unavailable. The known 25/5/48 layout counts do not fill those gaps. Instrumentation cannot supply missing authority, so no observation is scheduled.
