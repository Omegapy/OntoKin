# Review decisions for OK-LANG-006 drafts 1–2

**No adoption decision has been made.** The original proposal was authored from force candidate `06cf8206a8e7205f1b5f87c37c3c12dff0f65b9a`; Draft 2 now depends on accepted main `59b937d16ec0c82c9bc1395bd0c9bcc63e597261` and complete F01–F12 evidence. This ledger preserves preparation corrections and identifies the later amendments. Fresh reconstructed files after the executor rollback receive their own hashes and checks; missing predecessor reports are not evidence for changed bytes.

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

## Draft 2: SLERP correction and concrete schema review

On October 20, 2026, the main integrator identified that draft 1's normalized-chord discussion did not describe glTF rotation `LINEAR`. [Khronos glTF 2.0 Appendix C.4](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc#c4-spherical-linear-interpolation) specifies spherical interpolation with the short endpoint path. Independent review of the replacement proof confirms that the source quaternion and endpoint SLERP each have second-derivative norm at most `W²/4`. Their zero-endpoint difference has norm at most `W²*h²/16`, giving rotation error at most `W²*h²/4` under `W*h<=pi/4`.

**D13:** Replace the interpolant and proof with SLERP; preserve the numerical bound, support limits and all 41 source/expected records. The original draft-1 preparation reports retain their exact original contract/input hashes; they do not become evidence for changed draft prose. Draft 2 remains proposed. Its new projection, operation, GLB metadata and quantization schemas are review inputs, not published runtime support or an adoption record.

## Effective Draft 2 amendments and recovery

The machine-readable [amendment record](draft2-amendments.json), [effective profile](profile-draft2.json) and [effective requirements](requirements-draft2.json) preserve the exact original six input identities. The [authoring script](author_draft2_amendments.py) deterministically reproduces them. Original D01–D13 and original corpus values remain reviewable. These additions complete the proposed contract; they do not adopt or implement it.

| ID | Decision | Required meaning |
| --- | --- | --- |
| D14 | Accepted force dependency | Use actual main 59b937d16ec0c82c9bc1395bd0c9bcc63e597261 with complete F01-F12 evidence and released integration lease; preserve manual-only default-false hosted policy. |
| D15 | Current state and terminal identity | Requested program, actual accepted head, candidate history and sampled run identity are distinct. Current outcomes are exactly pending/active/satisfied/interrupted. Failed admission changes no incoming projection. Terminal snapshots remain latched while physical joints may have another owner. |
| D16 | Failed-prefix publication and recovery | A failed boundary retains only the valid incoming prefix. Reset/re-evaluate supplies a new run; L04 requires a separate tenth Agent artifact exported through exactly 0.25 seconds with the fresh delivery run produced by export and unchanged L04 program revision; retain reset/evaluation run IDs separately. |
| D17 | Complete-response output budget | Q03 fixes P24, actual sampled t=1.5 after, selector.kind action, fields actions, limit128, all128 complete items without cursor. Measure the full canonical envelope N; N succeeds including constructor/intermediates and N-1 fails at final publication without effects. No adaptive smaller query or pagination exemption. |
| D18 | Actual root source authority | P13 to P20 repair follows the inspected initializer target to writable root rig and exact source span. Reject generated occurrence and property identities; preserve sibling and library bytes. |
| D19 | Both-moving lifecycle supplements | Add independently identified L01 pause/resume, L02 stopped/new-owner, L03 completed/new-owner, L04 failed handoff rollback and fixed LP01-LP05 protocol steps; original41 cases remain byte-identical. |
| D20 | Stored time, SLERP and incoming histories | Use direct exact-rational to binary32 ties-even clocks, normalized actual stored endpoint SLERP, all enclosing source phases, independently proved uniform numerical bounds and complete incoming release contributors/state/spans. Unknown error terms reject. |
| D21 | Diagnostic and canonical-limit order | Use inherited envelope codes with structured reach_code; establish correctly rounded selected targets before checking their closed canonical limits. Work/cancellation may interrupt every bounded phase. |
| D22 | Bounded numeric admission | Exact rational classification and algebraic signs plus outward interval proof at96/192/384/768/1536bits establish rounding cells and residual. Bound recurrence/work/operand sizes; unresolved precision is numeric failure, exhausted work is resource failure. |
| D23 | Complete numerical/interface/delivery release obligations | Add R10-R12 and Q13-Q22 and the provider-neutral release contract. Execute actual source, Agent, destination, browser, compatibility and inherited roles; preparation is not acceptance. |
| D24 | Distinct budget units | Distinguish semantic/source-value work, full Agent JSON, weighted source history and whole GLB JSON/bytes. Extend F05/H05 weights by complete reach maps and incoming releases before allocation; do not equate all100000 counters. |
| D25 | Series recurrence unit | The12000cap counts one atan-term iteration or one paired sin/cos iteration. Every constituent interval operation is charged separately to the100000cap and inherited remaining semantic budget; no additional program allowance. |
| D26 | Reconstruction provenance and stored bits | After the executor rollback, exact recovered files retain their recorded old identities at checkpoint1431e5f; reconstructed proof/schema/protocol/quantization files receive new hashes and fresh review. The retained clock row also exposes stored_binary32_bits, which must agree with actual bytes and exact conversion. No lost check is relabeled for new bytes. |
| D27 | Current source and historical run acceptance | Clarify reconstructed LP05.09 without changing the existing semantic rule: after the identical source is accepted, its current projection has candidate_only=false, while the retained earlier candidate run has immutable candidate_only=true. Name these two observations separately; preserve all 42 protocol steps and the original corpus. |

The reconstruction also states explicitly that ideal motion bounds use exact
canonical coordinate slopes with outward arithmetic. A rounded inspection rate
may understate the unrounded derivative and cannot be used as an upper bound
without accounting for that error. This clarifies the intended reference path;
it changes no source target, recorded tolerance or original expected sample.

## Remaining gates and execution boundary

| Gate | Concrete required result |
| --- | --- |
| Original and supplemental inputs | Original 41-case closure unchanged; exact recovered source identities distinguished from new lifecycle/protocol expectations; effective bindings identify every new hash. |
| Numerical proof | Fresh exact-cell/residual checks, independent math/corruption/resource probes and mathematical review of the bounded strategy; no universal host-libm claim. |
| Agent and recording contract | Strict existing-operation schemas, complete 128-action budget case, candidate/terminal identities, incoming-release maps and actual source repair authority reconciled. |
| Continuous recording proof | Independently reviewed normalized stored-endpoint SLERP, direct clock conversion, all touched phases, radius/vertex terms and uniform source/destination numerical obligations. |
| Combined fresh checks | One identified immutable input set, reproducible effective artifacts, raw commands/logs and every relevant pure check; prior reports apply only to their original hashes. |
| Separate adoption | Publish an exact-input adoption record and implementation ownership plan after review. Runtime remains unimplemented until that decision. |
| Actual finite release | Execute all R01–R12, Q01–Q22, source/Agent/native/browser/compatibility/inherited roles and resulting-main checks in [release-contract.md](release-contract.md). |

The next implementation work is typed/profile elaboration and bounded IK, atomic
simulator lifecycle/inspection, explicit Agent/0.6, controlled source kinematics,
curvature-aware recording and an independently hostile supplied-byte reader.
Actual Agent/SQLite, full suite and archive runs retain the exclusive-executor
rule. No hosted job dispatch, retry or paid execution is required. The full GOAL
and actual direct-tool authoring comparison remain open beyond this finite gate.
