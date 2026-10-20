# Review decisions for OK-LANG-006 draft 1

**No adoption decision has been made.** The language document and corpus were authored before runtime implementation from published force candidate `06cf8206a8e7205f1b5f87c37c3c12dff0f65b9a`. Peer review and reconciliation of PR #17 remain prerequisites. This file records proposals and preparation corrections, so implementation results cannot silently redefine the expected behavior.

## Proposed semantic decisions

| ID | Proposed decision | Reason and acceptance obligation |
| --- | --- | --- |
| D01 | One typed `reach_planar` builder returns an inherited Action; public source methods bind actual joint/site references | Reusable agent-facing capability, not fixture-specific host code or authored solved angles |
| D02 | Target frame is the exact shoulder-parent site frame; target is static in that local frame | Makes moving-base meaning explicit; coincident world or other site frames are not silently converted |
| D03 | Two prescribed +Z hinges, zero/identity child sites, +X link endpoint sites | Gives a finite verifiable kinematic model; unsupported geometry is diagnosed before motion |
| D04 | Explicit positive/negative elbow branch, principal shoulder interval `[-pi,pi)`, no shortest-arc rewrite | Makes branch/limits/path reproducible, including a long unwrapped shoulder motion |
| D05 | Exact canonical-input reachability, equal-link origin reported singular, closed unequal inner/outer boundaries supported | Distinguishes underdetermination, geometric failure and numerical error without epsilon expansion |
| D06 | Both coordinate claims, clocks and lifecycle effects are one atomic action | Prevents partial two-joint motion and preserves inherited whole-boundary rollback |
| D07 | Goal outcome is separately inspectable; failure belongs to the failed admission/request while accepted state stays intact | A completed transport or stopped pose cannot masquerade as a satisfied goal |
| D08 | Incoming release includes both joint rates and complete root lever transport | Completion's outgoing zero rates must not erase the actual incoming momentum |
| D09 | 32 bound chain identity tuples, 128 named actions, 32 running/paused; bounded source/history/output | Finite implementation and supplied-byte allocation obligations are fixed before implementation |
| D10 | Source 0.6, Agent/GLB0.6 explicit; old profiles/bundles retain their meanings | Avoids changing old source or accepting a new operation under an earlier profile |
| D11 | Curved carrier plus local landmark position bound and noncommuting quaternion bound | Angular alias prevention alone is insufficient for a moving articulated asset |
| D12 | Exact resolved target/coordinate binary64 values; pose comparison tolerance is separate | A multi-ULP error must not pass a correctly-rounded target or move an exact hard limit |

## Preparation review and corrections

An independent interface reviewer checked the draft chain/site/frame rules and atomic lifecycle for internal consistency, then inspected the prepared sources and expectations. The following issues were corrected before the first proposal commit:

1. Library transport initially used the document's draft suffix as a package version. Inherited `ontokin.bundle/0.1` accepts exact `major.minor.patch` versions, so the proposed packages now use `0.1.0` under `proposal.reach-*`. All pins, source units and program hashes were regenerated. No transport change is proposed.
2. The initial release target moved only one joint, and its follow-on expected position omitted non-X velocity components. P16 now moves both joints plus a translating/rotating root; complete incoming pose/velocity/omega and every-axis force/coast expectations are retained. This was an expected-input preparation defect, not an observed runtime failure.
3. P20 now repairs one explicitly assigned forearm length in P13's five-arm rack, preserving four real sibling arms and unchanged libraries. A comparison against an unrelated column would not exercise the intended sibling obligation.
4. Chain-count identity and named-action count are explicitly distinct. P23/N11 bind and start all 32/33 chains; P24/N13 bind 128/129 actions to one chain. Uncalled library method bodies are not secretly constructed actions.
5. Canonical target and coordinate equality is exact; `numeric_reference_tolerance_rad` applies only to derived pose comparisons. Source `deg` conversion uses inherited `Pi64/180`, while IK's mathematical `pi` is rounded only at the exposed target.

The reviewer also used an explicitly substituted in-memory baseline construction probe to catch inherited syntax/composition defects. The portable [probe](review_inherited_composition.py) replaces the proposed profile/enum/builder, recomputes substituted pins and calls only `level='constructed'`. Its result cannot establish new goal semantics. Any retained report identifies its own original input hashes; changed draft bytes require a fresh report before claiming the same construction check.

## Still unresolved before adoption

| Item | Required review result |
| --- | --- |
| Force dependency | Identify the actual accepted force implementation and complete F01–F12 record; reconcile imports, workflow policy and bounds |
| Scalar rounding evidence | Independently review the finite high-precision oracle, singular and hard-limit behavior; determine how runtime will establish canonical results without claiming unproved universal libm accuracy |
| Inspection shape | Adopt the final versioned JSON schema and operation mapping for accepted goal projections and failed-admission diagnostics, including nullability, byte/entry budgets and source spans |
| Sampling | Independently accept the carrier/quaternion/landmark derivation and explicit remaining error allocation for endpoint/time quantization |
| Actual execution roles | Adopt provider-neutral local Agent/GLB/release evidence contracts and corrupt-byte/cancellation probes before implementation acceptance; preserve inherited local-only hosted-job policy |
| Whole assets and held-outs | Confirm source-generated geometry, actual identities and independent expected endpoints cover reusable bench/character tasks and local repair |
| Input freeze | Publish a separate adoption record naming exact contract/corpus/member hashes and any changes from this draft; retain review history |

The next concrete step after review is a bounded implementation plan for the accepted semantics: typed/profile elaboration and source IK, atomic simulator lifecycle/inspection, explicit Agent service, curvature-aware writer and independently hostile reader, then actual source/Agent/destination/visual acceptance. No runtime work is authorized by the draft's mere presence; the main integrator will record the adoption decision separately.
