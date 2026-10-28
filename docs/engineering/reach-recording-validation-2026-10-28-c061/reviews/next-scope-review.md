# Proposed C062: screen shared ancestry descriptors inside independent phase setup

Reviewer: `/root/c061_collector`. This is a proposed future scope based on static source and C061 observations. It is not activated, implemented, executed, or scheduled. No further product request is authorized by this note.

## One concrete target

Investigate the repeated ordered ancestry reconstruction in `ReachReference._phase` → `_ancestry`, specifically whether a complete source-bound ancestry descriptor can be supplied from a bounded shared source graph without repeating each carrier's whole parent/joint walk. The descriptor includes root, ordered joints and exact source path; preserve the existing offsets result wherever the helper contract requires it.

This target is distinct from C061's rejected `_axial_derivatives` route. C061 observed 60 P11 and 24 L03 `_phase` calls, costing 6006 and 3300 operations respectively. After removing observed axial children, the unexplained phase bodies contain 6006 and 2924 operations. Those amounts are ceilings on the whole measured phase body, not measured ancestry cost or removable work.

The exact current `_ancestry` at `reach_reference.py` constructs fresh `offsets`, `joints`, `path` and `visited` containers for each call and charges every parent-loop visit. `_phase` calls it once and consumes root, joints and path. Its observed returned paths show shared prefixes/suffixes across nested carriers. For P11 the returned path lengths are one (three calls), three (18), five (24), and seven (15). For L03 they are one (four calls), three (eight), five (four), seven (four), and nine (four). These paths support a concrete repeated-walk hypothesis, not a cost or authority proof.

## Existing work that must not be rediscovered

- `_incoming` already caches the immutable relation map by the private model token and current grip set, after its existing charges. It does not cache an ordered ancestry descriptor for each carrier.
- `_source_basis` already shares numerical graph results per state and interval, with bounded `_basis_cache` storage, and caches constant/composition algebra in the arithmetic cache. A new generic source-basis cache is not the proposed work.
- `_joint_path` already caches its exact scalar law. Repeating that proposal or naming its current hits as new saving is invalid.
- `_phase_root_poses` already reuses admitted actual/ideal root pairs; `_phase_root_distance` already handles its supported equal-point case.
- `_phase` currently discards `_ancestry`'s offsets tuple. Removing list appends alone does not remove the charged parent-loop visits and is not an established operation saving.

## Finite decision sequence

1. Perform a source-only accounting/authority screen of this single ancestry-descriptor route. Enumerate complete native source fields, owner/dispatch checks, original callback boundaries, cache storage/invalidation and first-exception requirements. A source/state identity token alone is insufficient. Reject the route immediately if fresh authoritative admission must repeat at least all removable work or cannot preserve source/error behavior. Preserve a precise reason rather than creating a new runtime probe automatically.
2. Only if a positive, specific premise survives that screen, extend the separate diagnostic with an ancestry span inside `_phase`. Keep the already recorded phase boundary, exact original requests, neutral controls, counters, source identities and failure frontier. Observe the current relation-map/cache domain and returned root/joints/path using bounded detached native fields. Do not wrap charged arithmetic, replay a failed tail, mutate product source, or attribute the whole phase body to ancestry.
3. Allow one four-request control/capture round for P11 and L03 under a fresh exclusive execution window. Compute ancestry cost and any same-domain repeated descriptors offline. Stop if the measured opportunity is immaterial, already reused, or unable to fund its full live-source admission and cache effects.
4. Any implementation must be separately and explicitly selected after those results. It must preserve exact outputs, traversal/exception order, fresh callbacks, operand domains, the 256-entry limits and all original fixtures/settings. This proposal does not preauthorize another tuning loop or broaden into geometry, JSON parsing, root-pose arithmetic, producer code, or unrelated numerical families.

## Expected deliverable

Publish one evidence-backed accept/reject decision for source-bound ancestry-descriptor reuse, with exact current source bindings, gross and added costs, native authority analysis, negative-path requirements, and measured data only if the one attribution round was justified. A source-only NO-GO is an acceptable finite outcome. C061's axial rejection, all existing failures, held C035, rejected M1, and the full release obligations remain intact.

Source inspected: `ontokin/reach_reference.py`, 259473 bytes, SHA-256 `e17fb50c54f41e13b42ce5bc2c6464544c26992299b474032ad2b19e0485949f`. Evidence identities are recorded in the companion `measured-collector-review.md`.
