# C065: signed nonzero offset sharing

## Decision

**Reject the selected detached four-product bridge.** Original P11 has real repeated arithmetic beyond the existing coefficient cache. A sign-aware expression graph can remove up to four numerical operations per paired eye visit while preserving the original floors. The selected conservative representation copies four completed exact scalar values into a guarded temporary bridge, charging each copied occurrence. Those four charges exhaust the best possible reduction before preparation, publication, consumer admission or fallback.

This is a finite rejection of that representation and its explicit accounting schedule. A representation that retains original result objects, uses immutable integers, or extends the coefficient record has not been proved impossible. It also has no funded live-authority proof in this checkpoint. No runtime implementation or product request is selected.

Baseline is `a7452d0063b785c1bfb02c45844ef341e3e0bf0b`, tree `f063d6c54b0bbca286353169f6d7505cfaa8ccb8`. The [declared C065 scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6508306091) follows the explicit C064 release. [Source bindings](source-binding.json), [mathematics](reviews/math.md), [authority](reviews/authority.md), [cost](reviews/cost.md) and [reproducible evidence](derived-evidence.json) separate the proof, design assumptions and historical observations.

## Actual source expressions

The independent centered evaluator projects a nonaxial attachment offset with exact coefficients `D=w*w-s*s` and `C=2*w*s`. For planar coordinates `(x,y)`, the original results are `floor128(D*x-C*y)` and `floor128(C*x+D*y)`. Here `floor128(v)` is `floor(v*2**128)/2**128`. The coordinate parallel to the rotation axis passes through unchanged. The baseline already reuses `D,C` for admitted repeated orientation sources; that earlier saving remains in the baseline.

P11's head rotates about Y. Its left and right eye offsets are `(-0.1,0.05,0.23)` and `(0.1,0.05,0.23)`. Their rotating plane is `(local z,local x)`, so the exact admitted coordinates are `(Z,-A)` and `(Z,+A)`. `A` and `Z` denote the actual source operands; the proof does not substitute the mathematical decimal fractions `1/10` and `23/100` for binary64-derived values.

Literal common-expression reuse identifies `D*Z` and `C*Z`, a ceiling of two removed multiplication calls per pair. The stronger signed schedule retains four left-eye results at their original evaluation positions:

| Retained exact value | Original expression |
| --- | --- |
| `p` | `D*Z` |
| `n` | `C*(-A)` |
| `q` | `C*Z` |
| `m` | `D*(-A)` |

The left eye remains `floor128(p-n), floor128(q+m)`. At the right eye's original evaluation point, the candidate uses `floor128(p+n), floor128(q-m)`. Native exact sign symmetry gives `C*A=-n` and `D*A=-m`, so these are exactly the original right floor arguments. The original right subtraction becomes addition, and its addition becomes subtraction. Both original floors remain; no rounding moves across a sum. Node visits, recipe and parent checks, coefficient reuse, axial coordinates, position additions, output identities and independent comparisons remain.

When both coefficients are nonzero, the pair removes four multiplication calls. The degenerate branches have raw reductions of three, one or zero. In particular, when `C=0`, the signed right second coordinate needs a negation that the original positive-product shortcut did not need. The [mathematics review](reviews/math.md) gives the exact branch table. These figures are source-derived arithmetic counts, not executed optimization measurements.

Original L03 has unit hinge-tip and tool offsets under distinct shoulder and forearm orientation sources. Its product helper already omits multiplication by one. Equal unit lengths neither create a missing multiplication nor merge source authority. The selected offset-product graph therefore supplies no corresponding L03 opportunity.

## Selected representation and complete cost proof

The selected graph uses a source-only pair descriptor and one bounded temporary bridge per matching pair within one key. It preserves the left product order. After each original left product returns, it constructs a detached exact scalar copy and admits that copied occurrence with an explicit charge. It does not evaluate or reject the right recipe early. The right node retains its original admission and uses the bridge only after fresh operand and result authority. At most four numerical values are live, and every rejection, exception and key completion discards them.

This choice follows the existing evaluator's use of detached values to protect against mutable Fraction aliases. The new four-copy schedule is explicit. The current `_Guard.freeze` has no separate tick; calling it four more times would not, by itself, fund four new logical copies. This checkpoint does not declare every Python assignment a semantic operation or invent a one-tick bulk exemption.

For every completed bridge `e`, let `g(e)` be the numerical work actually removed. The source branch analysis establishes `g(e)<=4`. Let `N` count completed bridges across the complete request, including replay, and let `C_other>=0` include all additional work beyond the four producer-copy charges:

`net saving <= sum(g(e)) - 4*N - C_other <= 0`.

`C_other` includes source-pair preparation, publication and selection, new type/limit/claim and dispatch checks, consumer copies if used, partial or rejected bridges, cleanup, fallback and finalization. A partial bridge can add work without earning a right-eye saving. No unknown cost is assigned a favorable negative value. The inequality therefore rejects the required strictly positive premise without guessing how often an unvisited tail would use the graph.

An extended coefficient-cache entry does not rescue this selected copy schedule. The left coefficient lookup or cold publication occurs before the vector-dependent products exist. A later product update and its new receipts require their own funding. The unchanged right coefficient lookup cannot be counted as a new saving or used as an unlimited allowance for added checks. This conclusion preserves the existing 256-entry cache, its eviction effects and every earlier coefficient optimization.

The rejection covers the selected detached representation. A reference-only graph or different funded bulk operation would need a concrete live lifetime, mutation, copy and accounting design. Relabeling the same four copies as free temporary storage does not supply that design. The existing C057 accounting/passive-authority concern remains open and is not treated as a blanket ban on all bounded numerical reuse.

## Authority and error order

Exact numerical equality is necessary but does not establish live authority. Each node receives a fresh `_Guard`; the right guard does not inherit all left-node result watches. Preparation-time source equivalence cannot replace the right recipe's original checks. Final source admission checks source receipts and cursors, not arbitrary new intermediate-product records.

The existing coefficient path separately checks native method dispatch and latches departures across callbacks. `_Guard.current` alone does not establish that all participating exact methods remain native. The [authority review](reviews/authority.md) gives two unexecuted conditional witnesses:

1. A left-eye callback installs custom arithmetic, a product completes through it, and a later callback restores native dispatch. A right-entry-only check can incorrectly authenticate that saved result.
2. At the existing right first-floor callback, custom exact dispatch is installed which raises `E` for subtraction and delegates multiplication/addition. The original second coordinate performs multiplication, multiplication, addition; the signed candidate calls subtraction. Without operation-local admission and a faithful original continuation, the candidate can introduce a new first exception.

These are source arguments about insufficient implementations. No such callback was executed as a product test, and neither witness is attributed to a historical P11 failure. They explain why a future representation must fund current producer and consumer authority, preserve callback error identity, and specify fallback at the correct original continuation point.

## Original requests and evidence limits

The retained C061 inputs contain 52 P11 clocks, `0,1/25,...,49/25,2,3`, and 178 L03 clocks. They are unvalidated reader inputs from failed requests. C065 verifies their archive/member identities and reads their JSON clock metadata; it does not validate their destination bytes or execute their later keys.

A single unchanged P11 certificate traversal calls the optional centered evaluator at most once per supplied key. Granting every key an eligible pair gives a generous `4*52=208` gross ceiling for that traversal. The certificate caller supports replay on the same allowance, so 208 is not a universal complete-request bound. The per-bridge rejection above remains valid across all attempts.

The historical reader allowances with unchanged producers are 38,585 operations for P11 and 45,012 for L03. Selected mandatory work still ahead of the historical refusals is at least 1,260 and 594 respectively, before other tail work. These are preserved completion constraints. A positive development increment need not alone complete a recording; this selected schedule fails even the smaller positive-saving requirement. No full-request total or timing is inferred.

## Actual verification

The original C064 ZIP matched its published 477,588,135-byte size and SHA-256, and its unchanged verifier passed including the ZIP comparison. It checked all 3,516 source files, 621,536,665 bytes, exact Git identities, original documentation receipts and unchanged-runtime claims. A first extraction verification detected an unlisted temporary file; that preparation failure and the isolated temporary were preserved before the successful check. Native Git reconstruction also preserved a failed default index attempt that omitted historically tracked ignored logs, and an untracked copy temporary. The corrected index exactly reproduces the original tree and commit. These preparation records do not represent product failures or new release successes.

The standalone [derivation](derive_evidence.py) imports only the Python standard library. It verifies 17 bound source inputs, all ten C061 archive parts and both used GLB members; proves four polynomial identities; checks the original two floor/four product call sites; and checks all four degenerate arithmetic branches and two floor noncommutation controls. The coefficient controls are illustrative exact rationals, not captured runtime centers. The zero L03 opportunity remains an explicitly labeled source-review conclusion. [Validation](validation.json) identifies actual commands and final reproduction results.

Independent mathematics, authority and cost reviews agree on the finite disposition. Exact published-candidate, actual-merge and final-main documentation checks are recorded separately at their actual source identities. No runtime test result is inferred from documentation or symbolic arithmetic checks.

## Preserved product state and next task

All 65 runtime files, source fixtures, equations, independent oracles, tolerances, defaults and workflows are preserved. The limits remain 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and 64 cursor updates. Historical original recordings remain **24/28, failed**, with **P11/P16/P23/L03 unresolved**. M1 remains rejected; C035 remains held including adverse timing; C057, complete reach acceptance and historical LFS payload migration remain open.

The [next proposed task](NEXT-TASK.md) examines cold exact L1-radius work for native sphere meshes, with every actual vertex conversion/error check preserved. It is a different source-bound algorithmic question, not a reopened identity alias or this detached eye bridge. No positive premise, implementation, next worker or schedule is established here. The complete [OntoKin goal](../../../GOAL.md) remains the governing product scope.
