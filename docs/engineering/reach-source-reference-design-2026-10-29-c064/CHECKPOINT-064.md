# C064 source/reference design decision

## Result and scope

Reject the proposed **elision of nonstationary, zero-offset, identity-orientation nodes from the centered independent evaluation plan** for original P11 and L03. The pinned source provides zero eligible node visits, and the proposed shortcut has unresolved recipe/parent authority obligations even on a hypothetical eligible graph. This is a finite decision about this candidate. It establishes neither a runtime improvement nor impossibility of other algorithmic reductions.

The review uses current-main baseline `3486829791629a5013599efceff9c98d7b369766`, tree `6f49d22ddf1045a279f6991834b34674a6b07af7`, after the explicit [C063 release](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6484917616). Its source identities are retained in [source-binding.json](source-binding.json). [The working scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6504104481) reserves only this engineering record and its documentation navigation entry; main integration uses a separate guarded lease.

## Proposed algorithm

Preserve existing centered-plan preparation and all original source receipts. Compile an alias only for a node that is not a root, is nonstationary, has an exactly zero centered local vector, and contributes no orientation change. A hinge must have `body.identity_relative is True`; a sampled zero angle or a zero rate does not establish identity over the source law. Redirect consumers to the already evaluated parent while retaining output-carrier identities and every independent supplied-byte comparison.

Stationary nodes are excluded because they perform actual lookup/publication in the bounded numerical cache. A hinge that changes orientation is excluded because it owns numerical cursor and seed work. The candidate must introduce no cache displacement, stale numeric reuse or changed result. The proposed graph transformation removes an evaluation occurrence; deleting an accounting tick while continuing the same evaluation would not implement it.

The numerical identity is straightforward: `_offset` returns its input zero vector without arithmetic; the position expression selects the parent's components; orientation, both radii and axis are unchanged. That equality is insufficient to establish live source/recipe authority or permission to remove an output occurrence. See [the authority review](reviews/authority.md).

## Complete-request cost premise

For an eligible node in `reach_reference_center.evaluate`, the original charged body has one node tick and no offset arithmetic, orientation arithmetic or stationary-cache operation. Existing preparation remains unchanged. Let `A(p,k)` count eligible visits of plan `p` at key `k`, and let `C_added` include every new classification, redirection, copy, type/claim check, bounded storage operation and fallback over the whole request.

`saving = sum(A(p,k)) - C_added`.

The source census below gives `A(p,k) = 0` for this candidate throughout both original timelines. Therefore `saving = -C_added <= 0`. Even the unrealistically favorable assumption that new authority and compilation are free does not give a strictly positive saving. No assumption about an unmeasured complete request cost is needed to reject the candidate.

This is separate from successful-request ceilings. With their producers unchanged, P11 has 38,585 operations available for the entire independent reader, and L03 has 45,012. A safe positive development increment need not already finish either request below the cap, but it must account for its effect on the complete request. The exact calculations and their boundaries are in [derived-evidence.json](derived-evidence.json) and [the cost review](reviews/cost.md).

## Source-bound eligibility census

The retained snapshots contain two distinct P11 plans and four L03 plans. Their exact paths and contexts are extracted by [derive_evidence.py](derive_evidence.py). They do not contain all stationary/identity flags or centered recipes. The classification is independently derived from the authored source and the current constructor rules; it is not attributed to the historical runtime measurement.

| Source case | Exclusion |
| --- | --- |
| Root frames | Roots are outside the candidate. Both originals have fixed roots. |
| Arm pivot sites | Their zero offsets lie under stationary mounts and are therefore stationary. |
| Shoulder hinges | Their pivots are stationary. If a shoulder is identity-relative, its zero coordinate law makes it stationary; otherwise its orientation must be evaluated. |
| Forearm hinges | The authored target distances require a nonzero elbow endpoint, so the entire source law is not identity-relative. |
| Neck, head base, hinge tips, eyes and tool | Their relevant local translations are nonzero. |
| Additional full-plan legs/column | These are stationary and add no eligible moving aliases. Their nonidentity mount rotations also prevent treating every retained full plan as a successful centered plan. |

For P11, segment lengths 0.75 and 0.5 have straight-arm squared reach 1.5625, while each authored target has squared distance 0.8125. For L03, lengths 1 and 1 have straight-arm squared reach 4, while the two goals have squared distances 1 and 2. Thus the elbow endpoint cannot be zero in the relevant laws. This argument uses the authored geometry rather than an approximate sampled angle.

The [complete path-by-path review](reviews/source-design.md) covers the 16-node P11 moving plan and both 7-node L03 moving plans. It also accounts for full plans and the remaining authored timelines. There are no later root motions, releases or new attachments creating a hidden moving alias in the uncaptured tail. The analysis makes no claim about newly measured future plan objects or successful final admission.

## Authority counterexample and first-error behavior

A source recipe and its parent pose are checked before and around the current node callback. Final source-batch admission checks captured source receipts and retained numeric cursors; it does not check every transient `plan.centered` recipe or recreate every earlier parent guard.

For a hypothetical eligible alias, a preceding callback can replace a later recipe field while leaving its recorded seal stale. The original evaluator rejects that recipe before its node tick. An eliding implementation relying only on an earlier classification and the final source receipts can miss that identity failure. Delaying the check also needs a proof that an earlier arithmetic/resource/callback exception does not change the first observed error. The review describes a source-level counterexample, not an executed mutation test and not a historical P11/L03 failure.

An immutable redirection representation and adequately funded live admission would require a separate design. Because the original cases offer zero removable visits, no speculative protection can rescue this candidate's positive-cost premise. No runtime implementation was warranted.

## Evidence and validation

C064 retrieves the complete C063 handoff and verifies its exact outer ZIP, inventory, every source blob, final tree/commit, original archives and recorded documentation receipts. The original archive failure histories remain unchanged. Local preparation discrepancies were preserved and corrected outside the source packet; they were not relabeled as successful attempts.

The standard-library derivation verifies C061's archive and parts, all 21 used members and 11 current source files against their frozen execution copies. It reconciles historical C060/C061 work maps and exposes original key, carrier, row, plan and geometry counts. Reproducing that output is an offline evidence calculation, not a product request. [Validation](validation.json) identifies actual commands and results; final publication and resulting-main receipts are identified separately in the portable handoff and coordination issue.

Three independent reviews cover source eligibility, authority/error order, and retained cost evidence. The unchanged documentation preservation/link checker is the applicable integration gate. No runtime test suite is claimed from this documentation and offline-calculation increment.

## Preserved obligations and next action

All 65 runtime files, original fixtures, independent oracles, numerical results, tolerances, defaults and manual-only workflows remain unchanged. Preserve the 100,000 shared-operation, 30,000-ms, 32,768-bit, 256-entry and 64-cursor-update limits. Historical original28 remains 24/28 failed; P11/P16/P23/L03 are unresolved. M1 remains rejected, C035 held including adverse timing, and all full reach and broader product obligations remain open. LFS migration is separate and unfinished.

Close this identity-elision candidate. The [next task](NEXT-TASK.md) targets actual nonzero offset arithmetic in the independent centered evaluator, with exact floor order, fresh authority and complete cost accounting. It must account for existing shared coefficients rather than assume they remain unoptimized. No next worker or future experiment is started by this record.
