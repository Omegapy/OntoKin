# OntoKin continuation: HANDOFF-039

Checkpoint: October 25, 2026, America/Denver.  
Coordination: [Issue #26](https://github.com/Omegapy/OntoKin/issues/26).  
Owner: `interactive-reach06-ordering-proof-feasibility-20261025-c039`.  
Owned branch: `work/reach06-ordering-proof-feasibility-20261025-c039`.

**C039 completed the source-only ordering-proof feasibility review. The mathematical implication is valid, but the existing reader does not retain fresh authority for the current axis, and cell membership alone does not preserve the original adjacent-comparison operand guards. Newly scanning the order, copying the whole axis, or checking eligibility on every row cannot provide positive charged savings. No runtime implementation is selected. A private immutable axis retained at the reader's original materialization site remains a possible broader design with unresolved lifetime and complete cost. Original recordings remain 24/28.**

## 1. Resume from live authority

Read current AGENTS, GOAL, STATUS, root/docs READMEs, adopted reach/release contracts, HANDOFF-038, this handoff, Issue #26 and current draft PRs. Re-observe actual heads, worker ownership, CI and any main integration lease. Older shared overviews retain older checkpoints; use identified evidence and closing comments without rewriting historical results.

Use a new isolated branch from the actual C039 publication. Its enclosing Git commit and closing Issue #26 comment identify the final SHA/tree. C039 is based on C038's draft PR #35 and owns only new checkpoint-039 evidence in the existing recording evidence directory. Do not advance another owner's branch or edit shared overviews.

| Identity | Bound state |
| --- | --- |
| C039 documentation parent | `30eb22e5df3bc2e70d9af1375cb6b4a8e829724f` |
| Parent tree | `54be3fad596de24927482c74c8e22fab9e2426b3` |
| Held runtime reviewed | `4ca73909f861fe4bef9694787473621c1d21c140` |
| Held runtime tree | `87c949b238055af1ce368c694e1d5683c8aeacde` |
| Held-candidate evidence | [Draft PR #32](https://github.com/Omegapy/OntoKin/pull/32), unchanged |
| Accepted reach runtime | `d2f0088c4f3c1f570630334804a5a8f78e0105ac`, unchanged |
| Main observed at C039 startup | `2bb4588e121fcfe99b4d42c734b15b38362f3642` |

No main integration lease belongs to C039. PRs 27-35 were open drafts at startup. The root coordinator owns evidence recovery, checks and publication; three independent reviewers inspected mathematics, provenance/lifetime and accounting without running product code.

## 2. What C039 establishes

The [derivation](checkpoint-039-ordering-feasibility.md), [cost ledger](checkpoint-039-cost-ledger.json), [reviews](checkpoint-039-reviews.json), [source binding](checkpoint-039-source-binding.json) and [checkpoint](checkpoint-039.json) contain the complete result.

### Exact theorem

Distinct increasing finite nonnegative binary32 values have strictly ordered direct-rounding cells. Adjacent cells share a midpoint, but ties-to-even assigns it to only one cell. Exact authored values independently proved to occupy those cells must therefore increase strictly. The proof covers positive zero, subnormals, exponent changes and the largest finite cell; negative zero, nonfinite/negative words and repeated cells are ineligible. A singleton has no adjacent saving.

Increasing arbitrary Python floats are insufficient: native binary64 values `1` and `1 + 2**-52` both pack to binary32 `1`. A custom reader can therefore present increasing Python values with repeated cells and duplicate authored values. The original helper still rejects those authored duplicates.

### Missing reader authority

`read_glb` checks order on a temporary list at `gltf.py:577-579`. It returns a mutable `DecodedGLB`, whose document/accessor/clock caches and returned clock lists can change. `verify_retained_clocks` later obtains its axis through `decoded.clock`, after callback-bearing work. Class identity or a historical successful read is insufficient.

Reader order is checked through channels, while the helper selects the first sampler and checks all samplers. A future proof must bind the actual selected input and every current equality, including ordinary fallback for an unproved input. It must retain independent source/semantic checks and ordinary direct/custom-reader behavior.

### Missing pairwise domain proof

`_Bounds.compare` guards prospective rational cross products after its charge. Successful cell and shift checks do not imply those pairwise limits, even at the default 32,768-bit maximum. The derivation gives algebraic counterexamples with per-row work within the limit but a 40,023-bit adjacent comparison, and a corresponding 1,500-bit lowered-domain example. They were derived from source, not executed.

A sufficient envelope is at most 1,024 bits in each authored numerator/denominator under stable native full-domain work, giving at most 2,048-bit pair guards. The existing integer-cell route checks this envelope but does not retain its proof-path identity for the caller.

### Named cost rejections

The ordering loop costs exactly `N-1` comparison charges. With C038's 206 rows, the gross opportunity is 205 sites; only 160 actually completed before the refusal.

| Proposed additional work | Most favorable complete saving, before all other overhead |
| --- | ---: |
| Fresh scalar stored-order scan: at least 205 new comparisons | At most 0 |
| Additional immutable snapshot: at least 206 copied logical values | At most -1 |
| New per-row small-field admission: at least 206 checks | At most -1 |
| Fresh per-row binding to a historical axis: at least 206 checks | At most -1 |

These reject the named routes. They are not measured results and do not prove all possible reader designs impossible.

## 3. The broader possibility remains unresolved

An immutable axis could potentially be constructed at the reader's existing materialization site, avoiding an **additional** full-axis copy. It must be consumed through a private, current-invocation path without changing the ordinary list-return behavior or producing list/tuple equality errors. Creating an additional tuple by copying an unchanged list reintroduces the `N`-value copying cost. Retaining a tuple that replaces an existing reader materialization still requires sound binding to the helper's consumed axis.

An aggregate operand-domain proof is also mathematically possible. Every successful rational cell fallback executes an upper-midpoint `independent_exact_div`; the integer route requires the 1,024-bit envelope. An authentic unchanged monotone division counter across all completed rows therefore proves that all used the integer route. Counter/storage/native admission, snapshots and readback still require charges. Exact dictionary type alone does not exclude hostile keys, mutation or reentrancy.

A scoped receipt invalidated only on the existing slow-cell branch is another possible design, with its own publication, ownership, fallback and cleanup obligations. Neither route exists in the current implementation or has a closed positive ledger.

For a proposed reader-origin design, saving is only the prospective expression `(N-1)-H`, where `H` is **all** added work, including native gates, type/limit/claim checks, lookups, copies, storage/publication, failed admissions and retirement. `H` may depend on sampler/category counts. No bound `H < 205` is established. No full P16 deficit or pass follows from this clock-stage opportunity.

## 4. Verification and recovery

Fresh complete recursive Git-tree metadata reconstructs the parent and runtime trees. All 1,986 runtime-candidate file identities/modes agree with the parent; the parent adds 142 evidence files. The locally retrieved source and complete documentation/link dependencies are individually Git-blob-verified. This is a documentation-complete subset of the 2,128-file parent, not a full execution checkout.

The original C038 archive recovered successfully: 3 parts, 1,536,774 joined bytes and 73 exact members, with all hashes, safe paths, ZIP CRCs and extracted hashes verified. The original failed requests and the two distinct analyzer attempts remain untouched. See [recovery](checkpoint-039-validation/c038-recovery.json).

[C039 validation records](checkpoint-039-validation) bind the actual documentation command, checked source, stable input inventory and publication verification. Read their closed statuses before treating any check as passed. An initial snapshot preflight identified one generated documentation-reader bytecode file outside the parent tree; that failed preflight is retained, and the generated file was removed before final verification. It was not a product failure or a tracked-source change.

Direct Git transport lacked local private-repository authentication. Connector raw/base64 reads could not return some large historical files. GitHub-provided temporary download URLs supplied the remaining documentation dependencies; every downloaded file was checked against the observed parent blob identity. Temporary URL credentials are omitted from evidence and were removed after use.

No product request, runtime test, numerical analyzer, timing cohort, full original28 run or regression run belongs to C039. No new implementation, cache, source allowance, fixture, oracle, tolerance, workflow, shared-overview change, hosted/paid job, other-owner ref change, force update or merge belongs to this scope.

## 5. Exact next bounded task

[The next-scope record](checkpoint-039-next-scope.json) selects **one concrete private immutable reader-axis design with a complete charged lifetime**, subject to fresh ownership reconciliation. This is source architecture/cost work; implementation is not yet selected.

1. Specify an immutable axis at an existing reader materialization site, current selected-accessor authority and a private helper route that preserves ordinary public/direct behavior and every common-sampler check.
2. Choose one authored-domain witness. Define either authentic aggregate counter evidence or fully scoped fallback-only invalidation. Prove every omitted input/prospective guard and smaller-domain fallback.
3. Name the complete native dispatch/storage/MRO, source/work ownership and callback/observer/reentrancy boundaries. No stale receipt, exposed flag or class identity may grant authority.
4. Derive every positive and unsuccessful-route charge, including creation, publication, lookup, type/limit/claim checks, copies, storage and retirement. State dependencies on `N`, sampler count and category count. Require a complete generic positive bound, including `H < 205` for the observed P16 opportunity.
5. Preserve original row-error precedence and the endpoint/order/semantic/tolerance sequence. Every callback/resource failure retains its identity; every exit retires the receipt.
6. Obtain independent mathematics, provenance and cost agreement on the same concrete design before selecting implementation. An unclosed cost or missing authority is a stop condition; record a scoped no-go rather than claiming a saving.

Do not repeat the completed census or theorem. Keep P11 component reuse, L03 reseeding and P23 producer sampling separate. Preserve 100,000 shared operations / 30,000 ms / 32,768 operand bits / 256 existing numerical-cache entries and the separate 512-category metadata bound. No fixture/key/schedule specialization, relaxed tolerance, resumed failed tail or removed independent check is permitted.

## 6. Remaining acceptance and copyable continuation

The latest complete original suite remains C035's **24/28**, with **P11/P16/P23/L03** capped. C035 remains held, including adverse L03 timing. Its historical 29 focused methods, 3,093 regression methods and 7/7 local checks retain their original execution identities. Accepted reach runtime and main remain unchanged.

Even a future 28/28 recording result would leave actual Agent delivery and ten retrieved artifacts, independent rates/source acceptance, CPython 3.11/3.12/3.13, native/browser/visual and hostile/inherited roles, formal input closure, every R01-R12/Q01-Q22 requirement and resulting-main verification. The complete language/product GOAL remains open.

> Continue authorized Omegapy/OntoKin development from HANDOFF-039. Reconcile live authority, Issue #26, heads, draft PRs and ownership before editing. C039 completed source-only feasibility against held 4ca73909: the distinct actual binary32 cell-order theorem is valid, but current mutable reader state supplies no fresh axis authority, and per-row membership does not imply omitted pairwise operand guards. Fresh scalar scanning, an extra full snapshot and new per-row eligibility/binding cannot save charged work against 205 gross sites. This is not a universal impossibility result: immutable-at-origin reader storage with a domain witness remains unimplemented and uncosted. Next reserve a separate concrete private reader-axis lifetime design and close all native/current-axis/source/work/callback/domain/fallback obligations plus the complete charge H; require H < N-1, including H <205 for P16, before implementation selection. Recover/verify C038 only if needed; do not repeat product requests or resume failed work. Preserve all failures and caps. Original28 remains24/28; C035 remains held; accepted d2f0088c and main2bb4588e are unchanged. No shared-overview edit, other-owner ref change, main lease, hosted/paid CI, force update, merge or release claim is authorized by this scope.
