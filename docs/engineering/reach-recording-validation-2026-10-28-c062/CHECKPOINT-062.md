# C062 source ancestry decision

## Result and scope

**Finite source-only NO-GO.** The examined ordinary descriptor-cache designs do not establish a safe positive operation saving. Independently, replacing the entire setup `ReachReference._ancestry` helper is too small to complete either original P11 or L03 request under unchanged downstream control, charge, admission and cache behavior.

No new original control/capture request, ancestry instrumentation, runtime optimization, numerical cache, fixture edit or resource-limit change was selected. The calculation uses the existing C061 observations. It neither executes OntoKin nor resumes the unvisited tail of a failed request.

The source baseline is C061 `e5e99b92e4efa541b434abcdda5c2ec31dda6a39`. Its runtime is identical to the executed C061 source `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`. Exact source/evidence inputs and the three additionally retrieved hostile-test sources are identified in [source-binding.json](source-binding.json). Reviews are preserved verbatim in [reviews/](reviews/).

## Two independent reasons to stop

First, model/state/token identity does not bind the mutable site, follow and joint fields read by the original walk. The existing independent-reader source batch begins after setup, so it is not already authority for the proposed setup descriptors. For the concrete design that keeps `_incoming` and freshly admits one source record per removed object visit, the original warm cost is `n + g + 1`: `n` visits, `g` grip visits and one incoming lookup. The proposed warm descriptor path costs at least `n + g + 2` after its additional descriptor lookup, before insertion, eviction, invalidation, displacement or fallback. This rejects that particular design; it is not a lower bound on every possible authority scheme.

Second, even an impossible zero-overhead replacement of the entire bounded ancestry helper leaves a necessary request cost above the existing cap. This conclusion does not depend on assuming expensive source admission. It is derived below.

Neither conclusion proves that all graph sharing, combined changes or algorithms affecting downstream work are impossible. A small beneficial increment could exist without being a complete repair; no such safe positive design was established in this scope.

## Source authority and original first errors

The current `_ancestry` implementation is at `ontokin/reach_reference.py:4207-4245`. It reads the incoming map, optional initial site, parent chain, relation fields, site owners, ordered joints, offsets and source path. Every parent-loop visit charges before cycle/depth checks. The returned path enters the `ReferencePhase` unchanged at lines 4822 and 4846.

The constructor deep-copies source records, but exposes the resulting mutable model through `reference.model`. The private incoming token separates cache domains; it is not a mutation generation. The read-only incoming relation map also does not freeze later site/joint/follow records. A changed joint kind can alter the returned joint list without changing that map's identity.

Discarded return values do not make source reads dispensable. For a follow-to-world edge, the original walk reads `follow.offset.position` before testing the world parent. Skipping that read can suppress an original attribute error and expose a later cancellation/resource failure first. A cache fallback must preserve ordered work and cannot repeat an already executed incoming-map callback for free.

The original depth test is `len(visited) > 128`; it can admit 129 distinct successful visits. A stricter failure condition changes behavior. Optional smaller storage bounds must select the ordinary path.

Phase tables and final endpoint phases execute at `reach_conformance.py:3555-3556`. The certificate routine is called at line 3598 and opens the existing source batch at line 3456. Extending that transaction over setup needs its own treatment of early failures, temporary mutation/restoration, cache publication, reentrant readers, ordinary phase callers and bounded receipt storage. No existing complete authority proof covers that extension.

## Recovering the actual size of the target

The C061 evidence contains 60 P11 and 24 L03 returned setup `_phase` spans. The calculator checks every retained path against an explicit expansion of the pinned original source definitions. Each counted frame belongs to a source object; these cases have no initial site-frame exception or follow-to-world termination. The paths contain 171 and 68 object visits respectively. Each visit corresponds to one original ancestry loop tick.

| Original source | Objects | Joints | Follows | Grips | Setup phase calls | Object visits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| P11 segmented character | 20 | 11 | 8 | 0 | 60 | 171 |
| L03 bench arm | 6 | 2 | 3 | 0 | 24 | 68 |

This is an inference from hash-verified source and retained outputs, not a newly measured ancestry span. The retained GLB metadata corroborates the expansion and key/carrier counts; those files remain unvalidated reader inputs.

## Complete incoming-map cost ceiling

`_incoming` at `reach_reference.py:2436-2459` charges one visit per active grip and one lookup. A miss additionally charges one visit per joint/follow and one insertion. The original grip sets are empty, giving:

- P11: one lookup plus 20 extra ticks on a miss.
- L03: one lookup plus six extra ticks on a miss.

The recorded native callback chain is `ConstructionBudget.tick` with no user construction check. Source inspection and the retained limits establish no operand-domain reset in this exact original setup path. This premise is specific to the retained runs and is not a generic safety rule for a future optimization.

For L03, granting a miss on every call suffices:

`68 + 24 + 24 * 6 = 236`.

For P11, the all-miss bound would be 1,431, so the fixed incoming key and original 256-entry least-recently-used cache provide a tighter conservative ceiling. Every incoming hit promotes the key and every miss inserts it as newest. Eviction after that access requires updates to 256 distinct later keys. Promotions count alongside insertions. Each relevant update has a preceding shared charge.

The source audit includes ordinary arithmetic lookup/remember and direct Cartesian-rotation promotion/insertion. The latter are charged at lines 1341 and 1386 before their updates at 1345-1346 and 1389-1392. Deferred pending-cursor publication, centered writers and source-batch discard are outside this setup call graph. The independent cache's sole reset requires an operand-cap change, which the original native path does not perform.

The interval from the first P11 phase entry to the last phase exit contains 6,084 shared ticks. Grant the first access a miss and use every intervening tick as a possible later cache update:

`misses <= 1 + floor(6084 / 256) = 24`.

Therefore:

`P11 complete setup ancestry work <= 171 + 60 + 24 * 20 = 711`.

This does not claim 24 observed misses. It deliberately overestimates the update pool and removal opportunity.

## Mandatory unvisited work

The raw key ledger, independent audit ledger, retained key count and carrier identities agree:

| Quantity | P11 | L03 |
| --- | ---: | ---: |
| Supplied keys | 52 | 178 |
| Entered keys, including partial failed key | 37 | 154 |
| Wholly unvisited keys | 15 | 24 |
| Carriers | 20 | 6 |
| Interval/carrier rows not yet traversed | 320 | 150 |

Every wholly unvisited key requires one `independent_key_pose` charge per carrier. Every remaining interval/carrier row requires three distinct charges: `independent_interval_claim`, `independent_sufficient_arc_domain` and `independent_certificate_member`. Their source locations are `reach_conformance.py:1957-1962,2136,2554-2558,3329-3331,3398-3441`.

The row set includes the interval ending at the partial key plus subsequent intervals. The key-pose term includes only wholly unvisited keys. These are separate events:

`P11 future selected ticks >= 15 * 20 + 320 * 3 = 1260`.

`L03 future selected ticks >= 24 * 6 + 150 * 3 = 594`.

Starting with the 100,000 already admitted ticks, grant free removal of the full target and add only those selected future events:

`P11 >= 100000 - 711 + 1260 = 100549`.

`L03 >= 100000 - 236 + 594 = 100358`.

Both exceed 100,000. The refused tick, remaining partial-key arithmetic, other future comparisons, clocks, source admission and finalization are omitted, so these are necessary-work lower bounds, not estimates of the complete cost.

## Exact limits of the result

The bounds assume exact setup outputs and unchanged downstream control paths, charges, source admission and cache effects. A combined optimization or a different cache interaction needs a new complete analysis. The reviewed lower bounds do not predict elapsed time or prove timing neutrality. No cache miss was newly observed, no ancestry span was newly measured, and no recording became valid.

The original 100,000-operation, 30,000-ms, 32,768-bit, 256-entry-cache and 64-update-cursor limits remain unchanged. Historical 24/28, rejected M1, held C035 and all finite reach release obligations remain open as recorded.

## Verification and publication

The [offline calculator](c062_ancestry_cost_screen.py) verifies its C061 archive and used member hashes, pinned source inputs, phase paths, callback/domain settings and raw/audited key-row census. The source control-flow and LRU premises are explicitly reviewed mathematical arguments; the script does not pretend to mechanically prove them.

[validation.json](validation.json) records the actual root command, script/input identity, stdout/stderr, exit status and runtime-check omissions. [documentation-gate.json](documentation-gate.json) records the unchanged documentation checker on its actual materialized inputs. [publication.json](publication.json) records remote byte readback and the draft dependency. A successful calculation is not a waived documentation gate, runtime acceptance or main integration.

