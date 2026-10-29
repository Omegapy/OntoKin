# C064 independent authority review: structural identity elision

## Decision and boundary

**NO-GO for the selected structural identity-eliding centered-plan candidate.** The retained P11 and L03 source topologies provide no eligible moving alias under the candidate's necessary restrictions, so it has no positive complete-request operation-saving premise. Independently, deleting a nominal alias visit without replacing its live recipe and parent admission can suppress an original identity failure. These are conclusions about this exact candidate, not a proof against other graph or source-reference algorithms.

Reviewed baseline: commit `3486829791629a5013599efceff9c98d7b369766`, tree `6f49d22ddf1045a279f6991834b34674a6b07af7`, from the read-only C063 packet. This review read source, tests and existing evidence; it imported no product module, executed no request or test, and changed no runtime file. Line references below identify this baseline. The other source review is `source-design.md`; its retained-topology census is a source derivation, not a measurement of captured runtime flags.

The original 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries, 64 cursor updates, original source horizons/fps/helpers, independent comparisons and tolerances remain unchanged. No product experiment is justified by this candidate.

## 1. Exact candidate and actual opportunity

The candidate would remove an evaluation node after centered-plan preparation and redirect its output to an already evaluated parent. Eligibility requires all of the following:

- A non-root node in a successfully admitted centered plan.
- A nonstationary node, so it performs no stationary-pose cache lookup, promotion, insertion or rejection-ledger write.
- A zero centered local vector, established from its currently admitted recipe.
- No orientation contribution. For a hinge this requires `body.identity_relative is True`, not a zero sampled angle, zero angular rate or cancelling world rates.
- Every required output occurrence, source receipt, source-owner admission and independent stored-data comparison remains covered.

At `ontokin/reach_reference_center.py:658–663`, `_offset` returns a zero vector and `False` without arithmetic. The expression at 739–741 then selects existing parent position components without calling `guard.exact`. A nonidentity hinge would call `_orientation` at 732–734 and is excluded. A nonstationary node does not enter the lookup/remember branches at 719–728 and 748–753.

Consequently a qualifying node currently performs **one charged visit**, `guard.checked(a.tick)` at 712, and no offset arithmetic, orientation arithmetic or numeric-cache operation. There is no repeated exact pose calculation hidden in that body which this candidate can remove. Merely aliasing the final Python object while retaining the visit saves no explicitly charged operation. A genuine graph reduction must justify removing the visit and account for all classification, redirection and equivalent admission work.

For any complete request, let `V` be its actual eligible node visits and `C_added` all new semantic work, including preparation, rejection and fallback. With the existing preparation unchanged, the most favorable saving is `V - C_added`. No uncharged authority scan, new metadata structure or output omission is credited.

## 2. Why numerical identity is narrower than reusable authority

For an eligible node under stable admitted inputs, its five numerical pose fields equal its parent's fields: position, orientation, position radius, orientation radius and axis. This follows directly from the zero-offset return, the skipped orientation branch and the constructor at 742–744. That mathematical result does not establish that an old classification remains valid after callbacks, that an earlier parent's aliases remain unchanged, or that two output carrier identities can be merged.

The current code deliberately separates these responsibilities:

| Obligation | Baseline evidence | Consequence for elision |
| --- | --- | --- |
| Recipe type, bounded fields and seal | `reach_reference_center.py:701–708` checks `_CenteredNode`, its vector/radius/flags and `_integers(...) == recipe.seal`. | A cached zero-vector classification cannot replace the current check. |
| Detached numeric operands | `_Guard.freeze` at 164–172 saves the original integer fields and returns a new Fraction; `_Guard.pose` at 192–207 checks and copies the full parent pose. | Equal mutable Fraction aliases are not an adequate substitute for the detached representation. |
| Mutation across the node callback | `_Guard.current` at 209–235 rechecks owners, leaves, watched field identities and the latched numeric domain; `checked` at 237–241 invokes it after the operation. | Removing the visit removes an existing mutation observation boundary. |
| Source admission | `admit_source` at 432–448 checks source receipts and signatures; `_SourceBatch.admit` at `reach_reference_plan.py:188–224` checks binding, receipts and numeric domain. | Final source admission remains necessary, but covers different objects from the per-node recipe and transient-parent guards. |
| Numeric cursor admission and rollback | `_SourceBatch.admit` at 225–239 checks retained cursors; `discard_cursors` at 157–161 removes still-owned writes. | A source receipt is not authority for an arbitrary transient centered pose. |

The dataclasses are frozen at `reach_reference_center.py:20–44`, but their immutability is not treated as a complete authority boundary. `_integers` explicitly exists to protect against mutable Fraction aliases (93–106). Existing tests use `object.__setattr__` on a recipe flag and a parent pose or Fraction field: `tests/test_reach_centered_identity_offsets.py:265–314`. This review inspected those tests; it did not run them.

## 3. Specific conditional counterexample to skipping the guards

Consider a supported centered plan containing a node that met the candidate's predicate when a proposed redirection table was built. Let a preceding, retained node have its ordinary callback before evaluation reaches that alias. The callback holds the registered plan, as the existing mutation tests can obtain `reference._recording_phase_plan`.

1. After classification, the callback replaces the later alias recipe's zero vector with a native, bounded nonzero vector using `object.__setattr__`, leaving the old seal in place. It does not modify any source receipt, source model map, numeric cursor or arithmetic owner.
2. The preceding node's own guard need not reject this: it watches its own recipe and operands, not every later recipe in the plan.
3. The original evaluator reaches the later recipe. Its check at 701–708 detects the seal mismatch and raises `ReferenceError("identity", "Independent centered source recipe changed")` **before that node's tick**.
4. An elision based only on the earlier zero-vector flag skips this admission and supplies the parent pose. The final `admit_source` iterates `plan.receipts`; it does not inspect `plan.centered` recipes. The final numeric pass visits retained cache cursors, not this omitted nonstationary recipe. Under the stated otherwise benign conditions, those final passes do not discover the mutation.

This is an unexecuted source counterexample to an unsupported guard-skipping implementation. It is not a claim that unchanged P11 or L03 naturally contains an eligible alias or encounters this mutation. It also does not allege that persistent changes to actual source receipts escape the existing final gate: that gate explicitly rejects such changes.

A later replacement check is insufficient to claim unchanged first-exception behavior. The original stale-recipe error occurs before the next node tick; postponing it allows an intervening callback or resource refusal to become the first error. Equivalent timely admission therefore needs a concrete, funded design. Keeping each alias's current admission and tick removes the sole charged opportunity identified above.

A related alias risk is visible without inventing a new trust boundary. `_Guard.pose` presently returns a new pose populated with detached Fractions. Directly sharing the parent's pose object changes which later mutations affect multiple frame entries. Existing parent-radius and Fraction-mutation tests at 282–314 show why numerical equality and object identity are different obligations. A new redirection representation must specify how it retains current seals, detached values and per-carrier output checks.

## 4. Necessary exclusions cannot be relaxed to create opportunity

**A zero translation does not make a hinge an identity transform.** `_recording_hinge_body` at `reach_reference.py:2885–2907` requires zero child origin, identity child rotation and a coordinate law identically zero. For an active source law, both its initial and target coordinates must be zero. A paused or constant nonzero angle has zero rate but still rotates its child. A sampled angle of zero does not prove later clocks. The existing test at `test_reach_centered_identity_offsets.py:243–262` also distinguishes cancelling world rates from identity-relative orientation.

**Stationary aliases have real shared-cache effects.** Their lookup, promotion and possible remember/write at `reach_reference_center.py:719–728,748–753` influence the common LRU and rejection ledger. Removing those operations can alter downstream hits and reseeds. Including them would define a different algorithm requiring complete cache analysis; it is outside this candidate's cache-neutral premise.

**Root and output occurrences are separate obligations.** Root construction has its own preparation and source-state constraints (`prepare`, 336–362). Required carrier projections and supplied-data comparisons do not disappear because two poses are equal. The candidate cannot count those occurrences as omitted work without a separate proof.

## 5. Original-scope eligibility and complete-request cost

The source review derives zero eligible moving aliases for every node in the retained P11 and L03 plan topologies. I checked the decisive runtime rules independently: `_build` creates site/follow/hinge nodes at `reach_reference_plan.py:741–794`; it assigns stationarity at 833–841; centered preparation permits only identity local rotations at `reach_reference_center.py:364–394`; and hinge identity requires the complete zero source law at `reach_reference.py:2885–2907`.

The retained evidence provides node paths and phase bindings, not measured stationary or identity-relative flags. The classification is therefore explicitly source-derived. Nor is every retained full plan a successful centered plan: the fixed nonidentity leg/column mount rotations exclude the complete P11/L03 plans from this centered domain.

| Source structure | Why it yields no eligible alias |
| --- | --- |
| P11 arm pivots | Their zero offsets lie under fixed mounts and a stationary root. They are stationary. |
| P11 and L03 shoulders | A zero-offset identity-relative shoulder under a stationary pivot has zero coordinate rate and is stationary. A shoulder outside that case requires orientation evaluation. |
| P11 elbows | The two segment lengths are `0.75` and `0.5`; the target squared distance is `0.75² + 0.5² = 0.8125`, smaller than the straight-arm squared distance `1.25² = 1.5625`. Thus the captured reach target cannot have zero elbow angle, so the zero-both-endpoints identity condition fails. |
| L03 elbows, both phases | Segment lengths are 1 and 1; the two target distances are 1 and `sqrt(2)`, both smaller than the zero-elbow straight-arm distance 2. Neither captured law satisfies the required zero elbow endpoints. |
| Other moving P11/L03 attachments | Head base, upper hinge-tip sites, eyes and tool have nonzero local translations. |
| Full-plan additional legs and column | Fixed/stationary, with nonidentity mounts also outside centered preparation. |

The entry sources are `docs/language-design/planar-reach-v0.1/sources/p11-complete-segmented-character.ok:14–21` and `docs/language-design/planar-reach-v0.1/draft2-supplements/sources/l03-completed-action-new-owner.ok:14–26`. Their pinned libraries and each exact retained node path are enumerated in the separate source review. No sampled pose or rounded numerical endpoint is used to infer zero/nonzero identity.

Since `V = 0` on these retained topologies, the candidate's complete-request saving is at most `-C_added <= 0`, even granting the favorable assumption of zero new overhead. A positive prefix saving is not available to extend to a complete-request premise. This conclusion does not assert an unmeasured complete-request total, a new 100,000-operation impossibility bound, or that a different structural algorithm cannot save work.

## 6. Final disposition

Close this exact candidate before runtime changes, instrumentation or product requests. Preserve the original failed-gate status and all outstanding acceptance work. A future larger algorithm must identify actual repeated work, prove current source/recipe and operand authority, preserve required callbacks and first exceptions, account for cache effects, and establish a positive complete-request premise from its own evidence.

The separate geometry witness discussion does not change this decision. C057 is not treated here as a blanket prohibition on replacing an existing bounded comparison. Its documented concern is unfunded added/repeated authority work and unsupported passive-state assumptions. No geometry replacement, revised comparison model or transferable funding exemption is adopted by this review.
