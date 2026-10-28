# C061 candidate: attribute independent-reader setup and screen one structural reuse change

**Status: proposed next scope; not yet started.** The owner's standing mandate covers routine continuation. Before beginning C061, reconcile current main, Issue #26, active scopes/leases and CI; declare the bounded scope, select an isolated branch and arrange an exclusive execution window under the current governance instructions. This document does not claim an active worker, scheduled job or integration lease.

## Objective and evidence

Identify one measurable, source-derived reduction in independent-reader work before the first retained-key comparison. Diagnose first; implement at most one candidate only if the measurements and semantic proof support it.

C060's original complete requests reached the reader, then failed at the unchanged 100,000 shared-operation cap. Its reader-entry to first-key-entry deltas are exact, disjoint intervals:

| C060 measurement | P11 | L03 |
| --- | ---: | ---: |
| All shared/Reach charges in reader setup | 23,171 | 17,185 |
| Generic `checkpoint` charges within that interval | 13,121 | 8,900 |
| First-key-entry shared count | 84,586 | 72,173 |
| Original failed key index | 36 | 153 |
| Planned keys / carriers | 52 / 20 | 178 / 6 |

Evidence: C060 `capture/capture.json` reader-entry counters and `capture/key-ledger.json` first-key entry for each case. Category deltas sum exactly to the shared and Reach deltas. The generic category is not a function profile: it mixes reference arithmetic with byte, materialization and geometry callbacks. Do not assign all 13,121/8,900 charges to reference construction or phase evaluation without new attribution.

The C060 pi screen excludes isolated shortening of the producer's 239-denominator recurrence as the sole fix: no cold producer pi in P11; at most 108 removed recurrence charges in L03 versus at least 144 admissions for its wholly unvisited keys. Keep that result and its unchanged-output/path conditions; do not reopen M1 or held C035, or generalize the screen to all algorithms.

## Static call map to measure

Locations below refer to the C060 runtime and must be reconciled at activation. `reach_numeric.ReachExecutionWork.tick` charges `checkpoint`. `reach_reference._Arithmetic.tick` calls that same work tick; its exact arithmetic, interval operations, graph visits and cache bookkeeping therefore share the generic category. Other callbacks below also reach `work.tick`.

| Setup segment | Exact source functions and responsibility |
| --- | --- |
| Supplied bytes and provenance | `gltf.read_glb` (445) calls `json_limits.measure_json` (41); `scene.program_metadata` (487) calls `values.bounded_data` (121). Their actual traversal callbacks produce generic checkpoints; text batches have separate named charges. |
| Independent state construction | `reach_reference.build_reference` (800) → `ReachReference.__init__` (2247), `_initialize`, `_build` (3331), event/anchor and H06 preflight helpers. Model capture, source arithmetic and ledger traversals use `_Arithmetic.tick`. |
| Complete source histories | `ReachReference.boundary_states` (4127) → `_boundary_projection` (4070), `_pose_map`, joint/reach observations and history accounting. Preserve both sides and incoming releases. |
| Independent geometry | `reach_conformance._geometry_bounds` (850) → `scene._source_surface_mesh` / `build_surface_mesh`; `gltf._validate_geometry` (699) → `_validate_surface`, `geometry_metadata` and bounded properties. Constructors and comparison loops have native callbacks; point checks also have named charges. |
| Independent phase bounds | `reach_conformance._phase_tables` (1241) → `ReachReference.phases` (4152) → `_phase` (4821); inclusive final endpoints use `point_phase` (4178). `_phase` calls `_ancestry`, `_phase_root_poses`, `_source_basis`, `_joint_path` and, when `basis.alpha` is nonzero, `_axial_derivatives` (4504). |
| Remaining admission before key 0 | `verify_numeric_bases`, `_verify_metadata`, `verify_retained_clocks`, `_boundary_allowances`, `_assert_projection`, then `_verify_certificates` identity checks, `_tracks`, and source-batch entry. Measure these explicitly or retain a named residual; do not lose them in the totals. |

The governing sequence is `reach_conformance.validate_reach_export` (3507). It completes the above before `_key_comparisons` begins.

## First hypothesis and bounded alternative

**Primary hypothesis: exact reuse of overlapping axial-derivative prefixes.** `_phase_tables` requests phases per carrier. Each `_axial_derivatives` call creates a fresh `found` map and reconstructs overlapping parent/site/joint paths, including `attached`, `joint_motion`, `_axis_transport` and attachment L1 radii. This is a concrete repeated-work opportunity, not an observed saving yet. Measure invocation counts, charged cost and repeated typed source operands for the same phase/domain. If substantial, reuse completed exact axial descriptors for identical admitted source inputs inside the existing bounded arithmetic cache, or prove a bounded shared traversal without changing first-visit/error order. Do not add another retained numeric cache.

**Alternative within the same target:** if whole-prefix admission is more expensive or unsafe, screen exact reuse of repeated attachment L1 radii/axis-transport results inside that walk. Fresh source admission and all original intermediate-width obligations remain necessary. Select at most one of these for implementation.

Do not propose already-present work as a new optimization: `_incoming` caches relation maps; `_joint_path` caches coordinate laws; `_source_basis` shares a per-state/interval graph; `_phase_root_poses` already reuses complete actual/ideal root pairs; `_phase_root_distance` already handles its proved equal-point case. Account for displacement of those entries by any new entries.

## Finite execution plan after activation

1. **Freeze inputs and instrumentation.** Extend the separate C060 diagnostic, not the stock harness. Use reviewed entry/return boundaries for the table above, with nested spans for `_phase` and `_axial_derivatives` only where needed. Bound observations, preserve original arguments/returns/exceptions, and restore every wrapper in `finally`. Read detached native counters and bounded source descriptors only; do not replace `charge`, callbacks, arithmetic, trace/profile hooks or validation. Recheck identity-sensitive dispatch before wrapping. Compute exclusive costs offline so nested spans are not counted twice.
2. **One attribution round: four exclusive requests.** Fresh control and capture for P11 and L03, sequentially. Preserve the original manifests, revisions, float `fps=1.0`, `helpers=false`, P11 `end=3`, L03 `end=4`, tolerances and shared work object. Require full control/capture work-category equality, exception graphs/product frames, input stability and byte-identical retained reader inputs. Record cache occupancy/categories at section boundaries and the original failure frontier. Stop on an observation or neutrality defect.
3. **Choose or stop.** Attribute the checkpoint pool; calculate the selected candidate's gross removable work minus fresh source admission, lookups, inserts, evictions and fallback costs. If the hypothesized path is absent, small, already reused, or cannot preserve source/error semantics, publish a finite NO-GO and stop. No opportunistic expansion into JSON, geometry, producer arithmetic or another runtime family in this task.
4. **Conditional implementation: one candidate, one paired round.** After a reviewed proof, implement the selected narrow change and run focused tests below. Then allow at most four original product requests, control/capture for each case, to establish candidate neutrality and measure matched semantic frontiers. Maximum eight product requests for this task; no automatic full-corpus rerun or further tuning loop. A need for more work becomes a new explicit task decision.

## Minimum proof and verification gates

- Derive every reused value exclusively from independently captured source topology and operands. Bind state/phase interval, axis/sign, live source ownership, precision and operand domain completely; do not use producer plans, certificates or decoded key values as a source oracle. Prove exact descriptor/phase equality, not merely a looser valid bound.
- Preserve fresh callback admission, cancellation exception identity, native error precedence, prospective operand widths, failed-publication behavior and domain-change fallback. A callback may mutate inputs, narrow/restore limits, replace owners or reenter the cache. State identity alone is not a numerical proof.
- Keep 100,000 operations, 30,000 ms, 32,768 operand bits, each existing 256-entry cache cap, and the 64-update cursor cap. Keep all original keys, carriers, clocks, geometry, source histories and certificate coverage. Preserve all numerical output bytes; permit only required, explicitly audited source/basis identity changes after a code revision.
- Recover and hash-verify any missing tracked tests before claiming their execution. Minimum existing coverage: `test_reach_reference_axial_derivatives.py`, `test_reach_reference_callback_domains.py`, `test_reach_reference_operand_caps.py`, `test_reach_reference_reuse.py`, and `test_reach_conformance.py`. Add focused comparisons for shared ancestry versus uncached reference, all axes and reversal/cancellation, noncoaxial/dynamic fallback, distinct phases and final endpoints, changed source with a warm cache, eviction, lowered caps and callback failure. Use the repository's test runner; run no Agent or SQLite work concurrently.
- Independently audit candidate work, retained bytes/clocks/certificates and input identity. Report operation changes at matched first-key and original-failure milestones, plus all actually observed later work. A later cap failure does not reveal the unobserved completion cost. Claim complete-request saving or acceptance only from completed, fully validated requests; prefix improvement alone is not proof that either case now fits the cap.

## Deliverable and stop state

Publish a compact evidence-backed decision: exact revisions and commands, partial/full-checkout disclosure, exclusive setup/function/category ledger, candidate proof and focused test results if implemented, whole-request outcomes, and an independent review. Finish as either a diagnostic NO-GO or one reviewable candidate with explicitly bounded claims. C061 does not activate broader delivery acceptance, reopen other failures, or acquire a merge lease.
