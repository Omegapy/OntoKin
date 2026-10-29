# C064 source-plan identity-elision review

## Decision and scope

The selected structural identity-elision candidate has **zero eligible moving aliases in the retained P11 and L03 plan topologies**. It therefore has no positive complete-request operation premise for these two cases. This conclusion rejects this particular candidate before instrumentation or product execution; it is not a claim that other source-reference or geometry reductions are impossible.

This is a static review of baseline `3486829791629a5013599efceff9c98d7b369766`, using the read-only C063 packet. No OntoKin module was imported, no request or test was run, and no runtime file was modified. The original 100,000-operation, 30,000-ms, 32,768-bit, 256-entry and 64-cursor-update limits and original source/options remain the scope.

## Exact candidate

After the existing centered-plan preparation has completed, compile away an evaluation node only when all of the following are established from admitted source recipes: it is not a root; it is nonstationary; its centered local vector is exactly zero; it contributes no orientation change; and its output can be redirected to its already-evaluated parent without dropping source receipts, source-owner checks, output-carrier identity or independent comparisons. For a hinge, no orientation change requires `body.identity_relative is True`, not a zero sampled coordinate or zero coordinate slope. Existing numeric cache and cursor activity must remain identical.

This is a reduction of actual evaluated graph nodes. Merely removing the node's tick while continuing the same checks/evaluation would not implement the proposed algorithmic reduction. Stationary nodes are deliberately ineligible because they perform existing cache lookup/publication and affect the shared LRU and rejection ledger.

The relevant baseline is `ontokin/reach_reference_center.py`: preparation at 323–429; zero-vector return in `_offset` at 658–686; and evaluation at 689–775. A qualifying nonstationary alias currently has one per-node `a.tick()` at 712. Its zero vector performs no offset arithmetic, its identity orientation performs no orientation/cursor calculation, and its position tuple selects the parent's components without exact addition. There is no stationary lookup or remember. With preparation kept unchanged, **exactly one existing shared operation is removable per actual eligible node visit**. Added classification, redirection, bounded metadata, owner/seal checks and final source admission cannot be assumed free.

Let `A(p,k)` be the number of eligible evaluation nodes actually visited by plan `p` at key `k`, and let `C_added` include every newly required classification, redirection and authority/admission charge over the whole request, including fallback. Then the candidate's shared-operation saving is

`sum(A(p,k) for every actual plan/key visit) - C_added`.

The census below establishes `A(p,k) = 0` throughout the retained topologies, independently of visit count. Consequently the saving is `-C_added <= 0`; the required strictly positive premise fails even under the favorable lower bound `C_added = 0`. No unmeasured total-request operation count is asserted.

## What the retained evidence does and does not contain

`../derived-evidence.json`, produced by the separate evidence reviewer, derives the following from the C061 archive members `evidence/round-001/P11/capture/key-ledger.json` and `evidence/round-001/L03/capture/key-ledger.json`, at `entry/exit.source_batch.plans`:

| Case | Plan registration time | Phase | Nodes | Targets |
| --- | ---: | ---: | ---: | ---: |
| P11 | 0 | 0 after | 31 | 20 |
| P11 | 1/25 | 0 after | 16 | 6 |
| L03 | 0 | 0 after | 8 | 6 |
| L03 | 2/87 | 0 after | 7 | 3 |
| L03 | 2 | 1 after | 8 | 6 |
| L03 | 179/89 | 1 after | 7 | 3 |

These are **retained plan snapshots**, not independent executions per snapshot occurrence. They record `cache_identity`, `context`, `targets`, `remaining`, `registered_time`, and `node_paths`. They do not record full `_Node` bodies, centered recipes, stationary flags or `identity_relative` flags. All classifications below are therefore **source-derived**, not measured classifications. The first full plans also contain source rotations outside centered preparation's identity-rotation domain: P11's leg mounts and L03's column mount. Do not label every retained plan a successful centered plan.

## Source derivation

The pinned manifests are `docs/language-design/planar-reach-v0.1/p11.files.json` and `docs/language-design/planar-reach-v0.1/draft2-supplements/l03.files.json`. They select the corresponding entry source and the `reach-assets`, `reach-parts`, and `reach-exterior` libraries. Source locations below are relative to the first directory; the L03 copies are under `draft2-supplements/`.

`reach_reference_plan._build` constructs site nodes from the site's owner and local pose (741–759), follow nodes from their captured relation (760–777), and hinge nodes from the child-site pose (779–794). Its stationarity rule is: a root must have no running movement; every other node is stationary exactly when its parent is stationary and it is either not a hinge or has zero coordinate rate (833–841).

`reach_reference._recording_hinge_body` establishes `identity_relative` only for a zero child origin, identity child rotation and a coordinate law which is zero throughout the captured law (2885–2907). An active law must have **both initial and target zero**. The coordinate recipe gives such a law zero rate (2799–2803, 2828). Thus a zero-offset identity shoulder attached to a stationary pivot is necessarily stationary and excluded; otherwise that shoulder needs orientation evaluation and is excluded. This dichotomy avoids inventing unrecorded shoulder flags.

### P11: every warm-plan node

| Exact retained path | Source-derived reason it cannot be a removable moving alias |
| --- | --- |
| `rig.frame` | Root, with fixed placement `(0, 1.25, 0)` and no root action. Roots are excluded. |
| `rig.neck.frame` | Site offset `(0, 1, 0)`, nonzero; parent is the stationary root. |
| `rig.head.frame` | Hinge child-base offset `(0, -0.25, 0)`, nonzero. Centered preparation negates the child offset, retaining a nonzero translation. |
| `rig.arms["left"].frame` | Follow mount `(-0.35, 0.75, 0)`, nonzero and stationary. |
| `rig.arms["left"].pivot.frame` | Zero-offset site, but its mount and root are stationary. |
| `rig.arms["left"].upper.frame` | Zero-offset shoulder hinge with stationary pivot: if identity-relative, it is stationary; otherwise orientation evaluation is required. |
| `rig.arms["left"].upper.hinge_tip.frame` | Site offset `(0.75, 0, 0)`, nonzero. |
| `rig.arms["left"].forearm.frame` | Zero-offset elbow hinge, but its reach target requires a nonzero elbow coordinate; orientation evaluation is required. |
| `rig.arms["right"].frame` | Follow mount `(0.35, 0.75, 0)`, nonzero and stationary. |
| `rig.arms["right"].pivot.frame` | Zero-offset site, but its mount and root are stationary. |
| `rig.arms["right"].upper.frame` | Same stationary-pivot shoulder dichotomy as the left shoulder. |
| `rig.arms["right"].upper.hinge_tip.frame` | Site offset `(0.75, 0, 0)`, nonzero. |
| `rig.arms["right"].forearm.frame` | Same nonzero-elbow requirement as the left elbow. |
| `rig.head.eyes["brow"].frame` | Follow offset `(0, 0.16, 0.2)`, nonzero. |
| `rig.head.eyes["left"].frame` | Follow offset `(-0.1, 0.05, 0.23)`, nonzero. |
| `rig.head.eyes["right"].frame` | Follow offset `(0.1, 0.05, 0.23)`, nonzero. |

Locations: entry source 14–21; `libraries/reach-assets.ok` 42–69, 74–81, 95–124; `libraries/reach-parts.ok` 22–56; `libraries/reach-exterior.ok` 23–35. Both arms have lengths `0.75` and `0.5`, with targets `(0.75, +/-0.5, 0)`. A zero elbow would yield a straight reach distance `1.25`, whereas either target has squared distance `0.8125`, strictly less than `1.5625`. Therefore the authored target cannot have zero elbow angle, independently of any sampled pose or numerical approximation. The captured law's zero-both-endpoints condition cannot hold.

The full P11 plan adds exactly the five paths `.frame`, `.pivot.frame`, `.upper.frame`, `.upper.hinge_tip.frame`, `.forearm.frame` under each of `rig.legs["left"]`, `rig.legs["middle"]`, and `rig.legs["right"]`. Their source mounts are fixed, their root is fixed, and the entry source starts only head and arm actions. Both leg joint initial coordinates are zero. The stationarity rule therefore makes all 15 added paths stationary. Their mounts also have a nonidentity local rotation, outside this centered candidate. No moving alias is added by the full plan.

### L03: every warm-plan node, in both retained phases

| Exact retained path | Source-derived reason it cannot be a removable moving alias |
| --- | --- |
| `rig.frame` | Fixed root at `(0,0,0)`, no root action; excluded root. |
| `rig.arm.frame` | Follow mount `(0,1,0)`, nonzero and stationary. |
| `rig.arm.pivot.frame` | Zero-offset site under stationary mount/root. |
| `rig.arm.upper.frame` | Zero-offset shoulder at stationary pivot: identity-relative implies stationary; otherwise it requires orientation evaluation. |
| `rig.arm.upper.hinge_tip.frame` | Site offset `(1,0,0)`, nonzero. |
| `rig.arm.forearm.frame` | Zero-offset elbow hinge whose active source law has a nonzero elbow endpoint; requires orientation evaluation. |
| `rig.tool.frame` | Follow offset `(1,0,0)`, nonzero. |

Locations: L03 entry 14–26; `draft2-supplements/libraries/reach-assets.ok` 10–39; `reach-parts.ok` and `reach-exterior.ok` as above. With segment lengths 1 and 1, either zero-elbow pose has reach distance 2. The authored goals `(0,1,0)` and `(1,1,0)` have distances 1 and `sqrt(2)`, so neither law can satisfy zero initial and zero target elbow coordinates. At phase 1, the completed first reach also supplies a nonzero elbow initial value. No claim depends on a zero sampled angle.

Each full L03 plan adds `rig.column.frame`: a stationary follow with offset `(0,0.125,0)` and a fixed 90-degree rotation. It is ineligible both as a stationary node and as a nonzero translation; its rotation also excludes that full plan from this centered domain.

The captured failures do not contain later successful keys. The authored timelines nevertheless add no later attachment, release, root motion or action beyond the ones above. P11's three actions end at time 2 within its time-3 horizon. L03's second action ends at time 3 within its time-4 horizon. Before activation and after completion, the same relevant branches are stationary. Thus the uncovered tails provide no source-defined moving zero-offset identity alias either; this is an extension of the static source argument, not a claim that later plans or results were captured.

## Authority, numerical equality, cache and exception obligations

For an actually eligible node, the zero local vector and unchanged orientation make all five numerical `_CenteredPose` fields equal to its parent. This is numerical equality only. Output path/carrier identities must still be resolved separately, and independent stored-data comparisons must still run. Source receipts must remain complete and fresh at the existing source-batch admission gate (`reach_reference_plan._SourceBatch`, 172–240; `reach_reference_center.admit_source`, 432–449).

The stationary exclusion is essential: removing a stationary node would remove a lookup and possibly publication from the shared 256-entry LRU, altering downstream hits, eviction and rejection cleanup. Removing a nonidentity hinge would remove required cursor steps/reseeds and change numerical results. Neither is this candidate.

Even eligible alias elimination would need a bounded immutable redirection representation, all necessary live owner/seal protections, and an account of any removed callback boundaries. A frozen dataclass alone does not establish passive authority. The evaluator presently checks each recipe and watches live owners around callbacks (689–775 and `_Guard`); removing those checks without an equivalent funded protection could change the first real source-mutation or arithmetic exception. No such new protection has been implemented or credited as free. Because the finite eligibility result is zero, the candidate already fails its cost premise before those implementation obligations need resolution.

## Outcome

Preserve this as the rejected C064 source-plan direction. No new instrumentation, runtime edit or product request is justified by this candidate. The source-derived zero census is stronger than extrapolating P11/L03 aggregate counters, and narrower than a claim that all graph reductions fail. Any different candidate requires its own source-authority, numerical, callback/exception, cache and complete-request accounting argument.
