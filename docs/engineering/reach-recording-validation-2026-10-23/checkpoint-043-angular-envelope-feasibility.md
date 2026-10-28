# C043: Angular-envelope feasibility and exact evidence gap

Date: October 26, 2026, America/Denver. Owner: `interactive-reach06-angular-envelope-feasibility-20261026-c043-7302`. Scope: source and retained-evidence review only. Parent: C042 `00606a16be62631179b50255d4de8daa34f8f196`, tree `9d9dd9f77b976c4b8b2076b8f5a0c4f87aa82342`. [Ownership](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6420966195).

**C043 establishes the historical selectors and first-sample placement of 32 completed angular-envelope calculations, rejects one unconditional shared-cache design, and defines the missing current observation. No runtime implementation is selected.**

The latest complete original28 remains **24/28**. C035 remains held, including adverse L03 timing. The proposed design concerns `recording_float_excess`, which computes conservative additional recording errors; it is separate from held P23 whole-pose static transfer.

This review follows [AGENTS](../../../AGENTS.md), [GOAL](../../../GOAL.md), the [adopted reach contract](../../language-design/planar-reach-v0.1/ADOPTION.md), its [release obligations](../../language-design/planar-reach-v0.1/release-contract.md), and [budget-counting section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse). It preserves C038–C042's source and cost qualifications.

## 1. Source and retained evidence

All 65 current `ontokin/` blob/mode identities match held runtime `4ca73909f861fe4bef9694787473621c1d21c140`, tree `87c949b238055af1ce368c694e1d5683c8aeacde`. Accepted reach remains `d2f0088c4f3c1f570630334804a5a8f78e0105ac`. This is a remote source-identity comparison, not a new runtime execution or complete release-input closure.

C020's retained observation belongs to runtime `88473124cc058f7e2926a04d79ab38e340ab4407`, tree `02efa05c691ff31258e39c16b98044d2a47fda20`. C042 already retained its original observer, exact P23 JSON, input inventory and selected original source. C043 additionally retains the original `reach_recording_capture.py` and `reach_phase.py`, matched to C020's own input inventory. It does not rerun those files or claim a new whole-archive verification.

The target function's old/current ASTs are identical, as are the original arithmetic and native lookup/insertion bodies. The captured envelope initialization/sample/finish lifecycle is also structurally unchanged. The complete phase-bound source is byte-identical. However, the sampled graph and surrounding runtime/charge implementation differ. Those narrower identities explain old observations; they do not transfer the old cache sequence to current P23. See the [source binding](checkpoint-043-source-binding.json), [census](checkpoint-043-census.json), and [independent evidence review](checkpoint-043-reviews/angular-evidence.md).

Both original retained P23 requests use end `3`, integer fps `1`, helpers false and the original tolerances/caps. C020 failed at 100,001 shared / 80,033 completed reach operations. Current C035 P23 failed at 100,001 shared / 80,801 completed reach operations. These remain failed requests.

## 2. What C043 newly establishes about C020

The original observer attributes the following complete sampling row to `recording_float_excess`:

| Historical category | Total | Per completed cold calculation |
| --- | ---: | ---: |
| Domain admission | 32 | 1 |
| Whole-result lookup | 32 | 1 |
| Exact additions | 320 | 10 |
| Exact multiplications | 448 | 14 |
| Exact comparisons | 64 | 2 |
| Whole-result insertions | 32 | 1 |
| Evictions | 32 | 1 |
| **Total** | **960** | **30** |

All 32 whole-result calculations completed and were cold. There are no promotion charges. The arithmetic row contains exactly the ordinary 24 sites per call, so none executed the four additional dynamic position sites. The complete request contains no cell-radius domain charge. Consequently **all 32 calls used `dynamic=False` and `include_cell_radii=False`**. These are deductions from the original native source and exact attributed charges, not selector fields directly captured by the old observer.

The retained lifecycle further places all 32 calculations in the **first captured sample at exact time `1/26`**, call ID 459229, shared-operation window **79,732–82,476**. The captured phase begins with no stored excess map; its first sample computes and retains that map, and later samples reuse it. All 51 captured samples and their finish operation completed. There is no phase restart, scalar planar sampler invocation, observer anomaly or unreturned selected/work frame in this record. The actual budget refusal occurs later during ordinary position projection.

This places the batch. It does not provide a separate frame, angular tuple or start/end operation count for each of its 32 calls.

### Why the missing tuples cannot be recovered from the observer

The individual-call threshold was 128 operations. This function was not among the always-retained detailed functions, and each call cost 30. Its individual-call list is empty. Moreover, the observer's metadata whitelist excludes the six bound fields, both selectors and cache keys. Even an individually retained entry would not supply those omitted values.

The exact historical angular tuples `(t,c,sq)`, spatial tuples `(l,m,sp)`, bound-to-frame order and eligible repeated-signature count remain unknown. The 32 mounted source arms make repetition plausible; they are not a measured tuple sequence.

## 3. What remains unknown for current P23

Current retained P23 contains 32 `recording_float_excess_domain` occurrences, but only a request-wide category map. It does not establish current whole-result hit/miss/refusal classifications, exact bound tuples, selectors or temporal cache order. The changed sampled graph can change the shared cache before these lookups even though the target function itself is unchanged.

C042's final-refusal qualification remains: the current last `_constant_pose` lookup refuses in its lookup charge before membership. It is an unclassified lookup, not proof of a miss, and is not an observed envelope-cache outcome.

The missing datum is an ordered current record of each envelope call's exact inputs, originating frame/phase, selectors, whole-key classification, completed/refused arithmetic/publication points, and relevant intervening shared-cache activity. No current saving or P23 pass follows from the historical 960 total or current 32 domains.

## 4. The original arithmetic and failure contract

Static inspection confirms the selected angular work:

| Expression | Exact arithmetic sites | Original location |
| --- | ---: | --- |
| `source_leaves = c + 1` | 1 | Before position arithmetic |
| `e` | 4 | Before position arithmetic |
| `g` | 4 | Before position arithmetic |
| `q` | 4 | Before position arithmetic |
| `rotation_rad = 16*q` | 1 | After position arithmetic and successful range comparisons |

The ten ordinary position sites remain, including their angular subexpressions. Four further position sites remain when `dynamic=True`. Per-bound domain/width/selector admissions, whole-result cache operations, conditional range predicates, selected radii and return guards remain.

The first thirteen angular sites precede all position arithmetic. Position work precedes the `e` comparison; the `q` comparison runs only if `e <= 1/64`. The last angular multiplication follows both successful comparisons. Moving a cached range rejection or late multiplication earlier can change the first reported failure.

The original whole-result lookup remains first. Its warm branch guards three cached rational fields and returns. It does not run the cold branch's final 1,075-bit guard or late cap check. A new angular gate must not silently add those cold obligations to the existing warm route.

Each original `exact` call precharges work, guards both actual operands, guards unreduced prospective numerator/denominator widths, calculates the result, and guards it. Equal final values do not establish omitted intermediate guards. See the [independent contract review](checkpoint-043-reviews/angular-contract.md).

## 5. One concrete candidate: U-Angular

U-Angular preserves the original per-bound admissions and whole-result lookup. Only after a whole-result miss does it try an additional angular entry in the **same bounded numerical cache**. Its key binds method/cap, native integer snapshots of `t,c,sq`, and applicable constants. The record stores canonical integer pairs for the five completed values `source_leaves,e,g,q,rotation_rad`.

A hit can substitute the first four values only after a current native authority and intermediate-guard proof. Position work and both original conditional comparisons stay unchanged. Late rotation reuse is considered only at its original point after fresh authority and prospective guards; a declined late gate performs the original multiplication.

A miss performs the original calculation. It attempts angular publication only after the original whole-result insertion and final guards/cap check have succeeded. That new publication has its own callbacks and needs fresh return authority. It cannot acquire a separate cache capacity or request allowance.

This is a reviewed schedule, not an implemented algorithm. Its concrete authority/guard/copy proof remains incomplete. The negative cost result below grants those missing checks for free, which is deliberately optimistic.

## 6. Closed cost rejection for the unconditional schedule

For a native default `PhaseBound()`, with stable full limits, ordinary native dispatch, no external callback/observer, an empty cache and both selectors false, the original function costs 29 charges. Its exact inputs are `t=c=l=m=sp=sq=0`. The formulas give `e=2^-46`, `g=0`, `q=2^-42`, `p=2^-46` and `rotation_rad=2^-38`; both range comparisons and all widths pass.

U-Angular removes no arithmetic on this cold call and adds at least one lookup and one insertion:

| Static function-domain witness | Original cost | Candidate lower bound | Saving upper bound |
| --- | ---: | ---: | ---: |
| One cold call, empty cache | 29 | 31 | -2 |
| One cold call, unrelated full cache | 30 | 33 | -3 |
| 32 calls with distinct `product_count=0..31`, other fields zero, initially empty cache | 928 | 992 | -64 |

In the third witness, maximum `e=2^-41` and `q=2^-37`; the predicates pass. The candidate has only 64 distinct keys, below the unchanged 256-entry cap. No later useful access is displaced, so no uncertain cache effect is needed to close this counterexample.

**These are unexecuted algebraic function-domain witnesses. They are not reconstructed P23 inputs, an assertion of source reachability, a benchmark or measured product costs.** They disprove an unconditional positive worst-case saving claim for this explicit helper design. They do not rule out a separately proved conditional specialization.

The [cost ledger](checkpoint-043-cost-ledger.json) and [independent cost review](checkpoint-043-reviews/angular-cost.md) retain the full qualifications.

### Complete accounting required for any conditional design

Let `r13` count eligible completed prefix reuses and `r1 <= r13` eligible late rotation reuses. Let `A,K,C,B,D,L` respectively cover added admissions, keys, copies, cache operations, partial/declined/fallback work, and lifetime/retirement/cleanup. Let `Delta_other` be candidate minus original work elsewhere, including effects of the changed shared-cache sequence.

`saving = 13*r13 + r1 - A - K - C - B - D - L - Delta_other`.

The added direct terms are nonnegative. **The sign of `Delta_other` is unproved.** It cannot simply be dropped or assigned a favorable value. A failed-prefix ledger also cannot stand in for all newly reached tail work. The historical optimistic `14*31=434` assumes a shared admitted signature, surviving retention and successful late reuse; none is established.

## 7. Remaining authority obligations

The native dataclasses are shallowly frozen; their Fraction fields and global Fraction constants have mutable backing state. Key snapshots, stored integer pairs, fresh output reconstruction and their checks/copies need explicit charging. Native work type alone does not authenticate instance dispatch, callbacks, the observer, category-map keys or cache contents.

Surviving position/comparison callbacks separate the two reuse regions. Late reuse needs fresh authority. The new publication after the original final guards adds another callback boundary: native `remember` protects its pending insertion, but does not revalidate every existing result field or return authority. A declined optional insertion cannot justify returning a result changed by that callback. The design needs a proved nonmutating native interval or the required fresh final checks, with their costs and original exception identity.

Current cache-domain reset checks are already present; this review does not allege that the original native cache ignores changed operand limits. It identifies obligations introduced by the new partial reuse and publication schedule.

## 8. Next bounded task

[The next scope](checkpoint-043-next-scope.json) defines **C044: a separately scoped neutral current-P23 angular-input and cache census**, beginning with source-closure and instrumentation review. It is a diagnostic proposal, not an execution performed or scheduled by C043.

Use the untouched original request, a fresh complete identified checkout, original caps, exclusive execution, an uninstrumented control, and a separately retained capture. Establish neutrality of actual operations/categories, cache state, original failure/exception and source/callback authority; elapsed neutrality is not assumed. A changed observer or wrapper that disables native routes does not supply current product evidence.

Capture exact integer numerator/denominator fields, frame/phase/order, both selectors, whole-key outcomes including pre-membership refusal, completed omission sites and sufficient shared-cache events. Do not resume a failed tail, extend its allowance, change fixtures or fill absent values with a numerical reconstruction. If complete source closure or neutral instrumentation cannot be established, record that concrete preparation blocker without executing a partial substitute.

Only after an independently reviewed census can a new conditional design claim positive complete charged savings and reserve implementation. C041/C042 rejections and the other P11/P16/L03 scopes remain separate.

## 9. Verification and publication boundary

Three independent static reviews are indexed with exact byte identities in [the review index](checkpoint-043-reviews.json). The new metadata audit parses source and retained records; it does not import product code. The unchanged documentation preservation/navigation command is the applicable repository check.

Actual candidate identities, commands, environment, complete logs, input manifests and outcomes are appended in `checkpoint-043-validation.json` and its validation directory after execution. Read the containing publication commit and final Issue #26 closure. A source/documentation subset is not a complete execution checkout. Twelve historical binary link targets are unavailable locally; remote tree existence must remain separate from the actual local checker result.

C043 adds only its own evidence, reviews, metadata-validation and handoff files. It changes no runtime, fixture, oracle, tolerance, schedule, workflow, shared status or other-owner branch. It executes no product request, runtime test, recording run, numerical replay, benchmark, browser/native check, hosted job or merge.

The limits remain 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and the separate 512-category metadata bound. Even 28/28 still requires actual Agent delivery and ten retrieved artifacts, independent rates/source work, three Python roles, Khronos/Three/browser/native visualization, hostile/inherited roles, formal input closure, every R01–R12/Q01–Q22 gate, resulting-main verification and the larger GOAL.
