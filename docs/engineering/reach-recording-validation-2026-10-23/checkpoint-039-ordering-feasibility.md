# C039: authored-clock ordering proof feasibility

Checkpoint: October 25, 2026, America/Denver. Scope: source-only feasibility review of the question selected in [HANDOFF-038](HANDOFF-038.md).

**The mathematical implication is valid, but the current reader does not retain the authority needed to use it. Fresh scalar scans, an additional complete-axis snapshot, and a new eligibility check for every row cannot provide positive charged savings. No runtime implementation is selected. An immutable axis retained at the reader's original materialization site remains a possible broader design, with unresolved proof lifetime and complete cost.**

The review closes the current feasibility question with distinct conclusions for the named alternatives. It does not assert that every possible equivalent-order proof is impossible. The [cost ledger](checkpoint-039-cost-ledger.json), [independent reviews](checkpoint-039-reviews.json), [checkpoint](checkpoint-039.json), [next scope](checkpoint-039-next-scope.json) and [handoff](HANDOFF-039.md) preserve those distinctions.

## 1. Source and evidence

| Identity | Verified reference |
| --- | --- |
| Documentation parent | `30eb22e5df3bc2e70d9af1375cb6b4a8e829724f` |
| Documentation parent tree | `54be3fad596de24927482c74c8e22fab9e2426b3` |
| Held runtime under review | `4ca73909f861fe4bef9694787473621c1d21c140` |
| Held runtime tree | `87c949b238055af1ce368c694e1d5683c8aeacde` |
| Accepted reach runtime | `d2f0088c4f3c1f570630334804a5a8f78e0105ac`, unchanged |
| Main observed at startup | `2bb4588e121fcfe99b4d42c734b15b38362f3642` |
| Owned branch | `work/reach06-ordering-proof-feasibility-20261025-c039` |
| Scope declaration | [Issue #26, C039 ownership](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6405276174) |

The complete recursive Git-tree metadata reconstructs both identified trees. Every one of the candidate's 1,986 file identities and modes agrees with the parent; the parent adds 142 evidence files, for 2,128 files total. Individually retrieved source and documentation files are separately checked against their Git blob identities. The local review snapshot is a documentation-complete subset, not a full execution checkout. No product was executed from that subset. See [source binding](checkpoint-039-source-binding.json).

The C038 archive was recovered into fresh paths with the unchanged [recovery verifier](checkpoint-032-recover.py). All three parts, the 1,536,774-byte joined archive, its 73 exact members, CRCs and extracted member hashes passed. [The recovery receipt](checkpoint-039-validation/c038-recovery.json) identifies the actual verification. The original failed control and capture, the first analyzer's parse failure, and the corrected analyzer result remain separate records; none was rerun or relabeled by C039.

The historical basis remains [C038's complete census](checkpoint-038-census.md) and [analysis](checkpoint-038-analysis.json): 206 authored/stored clock rows, 160 completed authored comparisons, and refusal at pair 160/161, exactly 3.10 to 3.12 seconds. Both original requests failed at shared count 100,001 under the 100,000 cap. The 205 adjacent pairs in a complete axis are potential omission sites, not measured savings or a completed baseline.

All implementation line references below refer to the unchanged held runtime. The primary source is [reach_conformance.py](../../../ontokin/reach_conformance.py), with reader provenance in [gltf.py](../../../ontokin/gltf.py) and callback/counter behavior in [reach_numeric.py](../../../ontokin/reach_numeric.py). Accounting follows [budget-counting section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse), adopted by [ADOPTION](../../language-design/planar-reach-v0.1/ADOPTION.md).

## 2. The exact implication

Let `v(k)` be the nonnegative finite binary32 value whose word is `k`, for `0 <= k <= 0x7f7fffff`. Increasing words in this domain give increasing values. For an interior word, its direct round-to-nearest cell has endpoints

`L(k) = (v(k-1) + v(k))/2` and `U(k) = (v(k) + v(k+1))/2`.

The existing checker includes a midpoint endpoint when `k` is even and excludes it when `k` is odd. Adjacent cells share one midpoint, but adjacent words have opposite parity, so that point belongs to exactly one cell. Therefore a value in the earlier cell is strictly less than a value in the later cell. Nonadjacent cells are ordered as well.

It follows that strictly increasing, distinct actual binary32 words, together with successful independent membership of each authored rational in its corresponding cell, imply strict authored order. This discharges the same numerical ordering predicate currently checked at `reach_conformance.py:664`. It does not automatically discharge that comparison's resource guards, callback behavior or provenance requirements.

| Edge case | Required treatment |
| --- | --- |
| Positive zero | The zero cell begins at zero; its upper midpoint is inclusive. The next word is odd, so the shared midpoint cannot belong to both cells. |
| Negative zero | Word `0x80000000` lies outside the accepted domain. Numerical equality with positive zero does not confer eligibility. |
| Subnormals and exponent boundaries | The proof uses actual neighboring centers, not an assumption of uniform spacing. |
| Largest finite binary32 | The existing checker uses virtual higher neighbor `2**128`; the largest finite word is odd and excludes its upper midpoint. |
| Infinity, NaN and negative values | They are ineligible under the reader and existing cell-domain checks. |
| A repeated word | Cell membership cannot establish strict order between two values in the same cell. |
| One retained row | There are no adjacent comparisons to omit. Endpoints, semantic coverage and tolerance still apply. |

These statements follow from the independent cell implementation at `reach_conformance.py:415-495`, including the integer grid at spacing `2**-150` and the rational fallback. They use no writer certificate or writer cache as authority.

### An increasing Python-float list is insufficient

A direct/custom reader could supply native binary64 values `[0, 1, 1 + 2**-52, 2]`. They increase, but the middle two values both pack to binary32 word `0x3f800000`. Authored values `[0, 1, 1, 2]` can satisfy those cell checks and sufficiently loose time tolerance while failing strict authored order. The helper's repacking at line 652 does not establish that an arbitrary supplied float was already an exact binary32 value.

This is a source-derived counterexample, not an executed product probe. It shows why exact binary32 provenance and distinct cells are necessary, even when every supplied Python value has native `float` type.

## 3. The current reader's proof is not reusable authority

`DecodedGLB` is a mutable dataclass. Its document, accessor cache, clock cache and callback are exposed storage. `clock()` creates and returns the cached mutable list (`gltf.py:260-288`).

The fresh reader checks finite accessor values at lines 491-501 and binary32 scalar input shape at lines 573-576. It then creates a temporary `times` list and checks its nonnegative strict order at lines 577-579. It returns `decoded` at line 589. It does not return the proven axis or a fresh invocation receipt tied to it.

`verify_retained_clocks` subsequently calls `decoded.clock()` at line 630 and again for each sampler at line 635. Its axis is therefore not the temporary object on which the reader established order. Native class identity, unchanged dictionary identity, or a historical successful `read_glb` call cannot establish the current contents.

There are also callback-bearing operations between `validate_reach_export`'s `read_glb` call at line 3520 and its clock-helper call at lines 3548-3549: supplied-end parsing, option handling, numerical-basis checks, source metadata, reference construction, boundary construction and metadata comparison. `ReachExecutionWork.charge` permits an external callback before the reach counter increments and an observer afterward (`reach_numeric.py:71-94`). Foreign code can mutate or reenter state across those boundaries.

The reader checks inputs reached through animation **channels**. The clock helper selects the first **sampler** and checks **all samplers**, including potentially unreferenced inputs. A future receipt must establish that the selected input actually received the reader's proof and must preserve every current common-sampler equality check. An unproved or changed input needs ordinary fallback.

### Obligations for a future private reader route

| Obligation | Required authority |
| --- | --- |
| Current axis | The exact immutable sequence actually consumed, its selected accessor and the same validation invocation. |
| Reader dispatch/storage | Original reader/accessor/clock functions and relevant code, defaults, globals, builtins, class MRO/descriptors and unshadowed instance storage. |
| Work/callback ownership | Same native work; original charge/tick/guard/resource methods; native counters; no foreign callback, observer, trace/profile or reentrant path. A native construction callback must itself have no nested custom check. |
| Source obligations | Existing source/model/end/boundary and lifecycle checks still execute. The receipt proves clock order only; it must not become a cross-model or writer-authorized cache. |
| Numeric domain | Every omitted input/prospective guard is independently justified under the current limit; smaller or changed domains take fallback. |
| Lifetime | Fresh publication and use within one invocation, retirement on success/fallback/exception, and no reusable authority retained for later requests. |
| Direct/custom helper calls | Ordinary behavior remains available. A public `trusted=True`, forged token, exact proof-class identity or old reader field is insufficient. |

The existing native gate at `reach_conformance.py:2697-2828` illustrates the breadth of dispatch/storage inspection. It neither establishes the new reader-order claim nor pays for new work executed at a different site.

## 4. Authored comparison guards are not implied by the cells

`_Bounds.compare` checks each Fraction field, charges one comparison, then guards the prospective cross-product widths before comparing (`reach_conformance.py:174-184`). Successful per-row parsing, cell membership and shift subtraction do not generally imply those pairwise limits.

Consider `D = 2**19999 + 1` and authored axis

`[0, a = 1 + 1/D, b = 1 + 2**-23 + 1/D, 2]`,

with actual binary32 axis `[0, 1, 1 + 2**-23, 2]`. The middle authored values lie in the correct distinct cells. Both reduced fields of `a` have 20,000 bits; both reduced fields of `b` have 20,023 bits. The relevant individual cell and source-minus-actual prospective bounds fit within 20,048 bits, while the adjacent authored comparison requires a 40,023-bit prospective cross product. The original default 32,768-bit domain therefore rejects that comparison. The canonical decimal labels remain below the 9,865-digit parser bound.

The same construction with `D = 2**999 + 1` gives fields of 1,000/1,023 bits, row bounds within 1,048 bits and a pair bound of 2,023 bits. A lowered 1,500-bit request domain distinguishes the same behaviors. These are algebraic source counterexamples, not measured executions.

Thus checking only that the work limit equals the default is insufficient. A sufficient generic envelope is at most 1,024 bits in every authored numerator and denominator, under stable native full-domain work: omitted individual bounds are then at most 1,024 and prospective pair bounds at most 2,048.

The existing integer-cell path already checks that envelope (`reach_conformance.py:426-429`). Its enclosing public helper returns only membership, without retaining which path established it. Adding a new eligibility check to each row would consume the complete saving opportunity.

## 5. Source-bound cost conclusions

Let `N` be the number of clocks and `G = N - 1`. The original ordering loop has exactly `G` scalar comparison charges. Its operands are already Fractions, so these sites incur no additional decode charge. C038's 206 rows give `G = 205`; only 160 charges completed in the failed product request.

The following bounds deliberately grant every other required protection for free. Any real added admission, publication, lookup, storage, copy, unsuccessful route or cleanup makes them less favorable.

| Specified route | Minimum new work in the named route | Most favorable complete saving |
| --- | ---: | ---: |
| Fresh scalar stored-order scan | `N - 1` scalar comparisons | At most `0` |
| Additional immutable snapshot of every current value | `N` copied logical values | At most `-1` |
| New small-Fraction eligibility admission on every authored row | `N` row admissions | At most `-1` |
| Bind every current value to a historical axis receipt | `N` fresh value-binding checks | At most `-1` |

For P16 those additions are at least 205 or 206 operations against 205 gross omission sites. They cannot provide positive charged saving. Snapshot plus rescan is worse. Failed admissions retain their actually performed work and then the ordinary path; no new allowance or negative charge is available.

These are proofs about the named designs. They are not measured performance, and they do not prove a universal per-row cost for every possible reader refactor.

### The immutable-at-origin exception

The reader already materializes temporary clock lists at `gltf.py:577`, and `clock()` later materializes another list at lines 268-271. A future private route might construct an immutable axis at an existing materialization site and retain that exact object. It need not introduce the **additional** `N`-value snapshot in the table.

That possibility must be assessed with its actual storage and interface. Merely retaining a tuple while continuing to iterate mutable caches is insufficient. Globally changing `clock()` from list to tuple changes its return behavior, and current list-versus-tuple equality rejects equal values of different container types. Creating an additional tuple by copying an unchanged list reintroduces the `N`-value copy cost. Retaining a tuple that replaces an existing reader materialization instead requires sound binding to the helper's consumed axis; its coexistence with an existing later list alone does not prove an added copy. No such route is implemented or selected here.

## 6. Aggregate domain evidence is possible, but its cost is open

There is a valid sufficient inference from native category accounting. A successful integer-cell return requires the 1,024-bit envelope. Every successful rational fallback unconditionally performs the upper-midpoint division at `reach_conformance.py:492`, including the zero and largest-finite cases. That operation increments `independent_exact_div` under native dispatch.

Therefore, if all rows finish successfully and an authentic monotone counter is unchanged between fresh pre-row and post-row observations, no row used that fallback. Every authored Fraction then satisfies the small envelope. Unrelated extra divisions only cause conservative fallback; they cannot produce a false positive while the counter is authentic and monotone.

This is a mathematical/control-flow proof, not a completed inexpensive implementation. It needs the same native work and counts dictionary, exact integer counts, native string keys, unchanged dispatch/domain and exclusion of mutation, callbacks and reentrancy. An exact `dict` can still contain hostile keys whose equality code runs during lookup. The existing native gate inspects up to 512 category entries, and C038 observed 266 after failure. A new equivalent scan and its type checks cannot simply be assigned zero cost or assumed to fit within 205 operations.

A separately specified scoped flag that becomes ineligible only on the existing rational fallback branch is another possible design. It could avoid new checks on successful integer rows, but only if its current-work ownership, publication, invalidation, native dispatch and retirement are all sound and charged. This state does not exist in the reviewed implementation. Neither counter nor flag design has a closed positive ledger.

For a broader reader-origin design the justified expression is only

`prospective net saving = (N - 1) - H`,

where `H` includes **all** newly executed admission, lookup, type/limit/claim, publication, storage, copy, fallback and retirement work. `H` may depend on sampler count or bounded metadata size; it must not be assumed constant. P16 requires a proved complete bound `H < 205` before implementation selection. That bound is not established by C039.

## 7. Failure order, fallback and limits

The original helper completes all row parsing, direct-rounding, label and shift checks before its final predicate. That predicate checks endpoints, authored order, semantic-boundary inclusion and time tolerance in that order (`reach_conformance.py:640-666`).

A future implementation must not raise an ordering error during the row loop before a later original malformed-label or rounding error. It must not consume optional proof authority before an endpoint failure that would otherwise short-circuit. It must preserve the large-width counterexamples through ordinary guards or fallback and retain semantic/tolerance checks independently.

Foreign callbacks, observers, custom readers, patched arithmetic or storage, active trace/profile hooks, smaller/changed domains, unproved inputs and missing/stale authority require ordinary behavior. Any actual new admission retains its resource/callback failures and charge. Native optimization can change the schedule of actual work; it cannot claim an identical foreign callback schedule while removing foreign-observable comparisons. Interrupted or failed requests publish no usable receipt and receive no fresh tail allowance.

The limits remain 100,000 shared operations, 30,000 ms, 32,768 operand bits and 256 entries in each existing numerical cache, with the separate 512-category metadata bound. No source fixture, independent oracle, tolerance, expected output, callback, workflow or shared overview changes in C039.

## 8. Decision and next bounded work

The current-reader shortcut is rejected for missing authority. The four newly scanning/copying/checking designs in section 5 are rejected for nonpositive charged-saving bounds. The exact rounding-cell theorem is retained as valid. Reader-origin immutable storage with aggregate domain evidence remains unresolved broader work; neither a positive implementation choice nor a universal impossibility claim is justified.

The [next scope](checkpoint-039-next-scope.json) asks for one concrete private reader-origin lifetime design and one domain witness, with a complete source-bound positive and fallback ledger. It must explicitly settle sampler/channel coverage, current-axis identity, native dispatch/storage, ownership, mutation/reentrancy, original error order, smaller domains and cleanup. A missing cost or unproved authority is a stop condition for implementation selection. This is new architecture work, not a repetition of the completed P16 census or the mathematical theorem.

No product request, runtime test, numerical analyzer or timing cohort ran for this review. Documentation/source verification and archive recovery have their own closed receipts. The latest complete original recording suite remains C035's **24/28**, with **P11/P16/P23/L03** capped. The held candidate remains held, including adverse L03 diagnostic timing. P11 component reuse, L03 reseeding and P23 producer sampling remain separate scopes.

Even a future clock-stage saving would not establish a complete P16 pass: downstream independent geometry, endpoint and certificate stages were unvisited in C038. Actual Agent delivery and ten retrieved artifacts, independent rates/source acceptance, CPython 3.11/3.12/3.13, native/browser/visual and hostile/inherited roles, formal input closure, every R01-R12/Q01-Q22 requirement and resulting-main verification remain open. The full language/product [GOAL](../../../GOAL.md) remains open.
