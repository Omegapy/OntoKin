---
project: OntoKin
document_id: OK-ENG-007
version: 0.2
date: 2026-10-19
status: implemented-component-complete-release-acceptance-pending
target_contract: ontokin.glb/0.5
source_profile: force-0.1
---

# Native force GLB recording

## Authority and finite scope

Implement explicit GLB/0.5 for actual source 0.5 / force-0.1 programs. The [adopted source semantics](../language-design/force-v0.1/ADOPTION.md), original and supplemental fixtures remain unchanged. Reuse native surface geometry, regional PBR materials, local placement and complete pinned source identity. All earlier GLB profiles retain their existing behavior. This contract specifies an adapter component, not complete F01–F12 acceptance or the full [GOAL](../../GOAL.md).

The adapter receives the compiled model. The caller must retain its authoritative .ok bundle. No hand-built asset geometry, silently downgraded profile or host-only force replaces source execution. Recorded GLB playback does not execute live physics.

## Requested prefix and temporal semantics

Only simulate through the requested export endpoint, inclusive of its after-side. Discover real source, action-completion and force-completion boundaries through that endpoint using the profile-specific evaluator. Do not preflight the complete scene or include future impulse magnitudes in prefix sampling bounds. A force ending later remains active in the final projection, with its original exact completion time. A failing requested prefix returns no artifact.

Preserve zero, the exact endpoint and every encountered boundary. Distinct exact rational boundaries that map to the same binary32 clock are rejected. A source-valid interval may remain undeliverable because of binary32 precision, inherited geometry limits or bounded recording work. Never clamp values or change source-time semantics to obtain success.

## Bounded sampling

For each real boundary interval, use the maximum canonical acceleration norm of its free dynamic spheres. Choose subdivisions before output allocation. Each interval's ideal linear chord error bound is A*h*h/8. Allocate at most one quarter of the requested position tolerance to this bound; the remaining error margin is not an automatic claim about encoded output. Include requested FPS and a conservative prefix-local angular bound, with angular steps no larger than pi/4 before quantization. Use exact rational products and integer ceiling operations so finite planning intermediates cannot silently overflow.

After binary32 timestamps are known, recheck time tolerance, no collapsed/reordered keys, and angular spacing. The serialized reader independently checks source clocks, the acceleration chord bound and actual decoded samples. Source/stored keys, quarter/mid/three-quarter interval probes and both sides of exact boundaries must satisfy the unchanged requested position, rotation and time tolerances. Geometry retains the independent maximum 0.00001 metre local-surface tolerance. These checks provide bounded analytical planning plus finite encoded-motion evidence, not a proof for arbitrary articulated trajectories or arbitrary destination playback.

Keep inherited caps: 10,000 keys, 250,000 baked poses, 1,000,000 validation poses, 250,000 aggregate occurrence vertices, 64 MiB GLB and 100,000 retained logical boundary entries. Force and impulse records count with nested source spans and IDs. Both construction and byte validation enforce the same prefix-local bound before copying output. Check cancellation through boundary discovery, exact summation, key planning, evaluation, geometry, serialization and validation. Preserve the original callback exception and publish no partial success.

Supplied-byte validation preflights every accessor declaration before decoded allocation. Aliased and unused declarations count separately. The derived aggregate ceiling is 4,760,000 scalar components: one maximum common key clock, seven components per maximum baked pose, and twelve per maximum occurrence vertex for positions, normals and primitive indices. Decoded component storage is also limited to 64 MiB. Declared key, pose and native geometry limits apply before accessor copies; forged artifact profile metadata cannot override the requested delivery contract.

## Retained meaning and independent checks

Every retained boundary includes complete after-side force and impulse projections for every object, including empty projections. Preserve exact source locations, force/target identities, sequence indices, activation/duration/completion clocks, canonical net force and acceleration, active keys, cumulative counts and latest changes. Retain mode-origin versus trajectory-anchor semantics. Validate these records against fresh source evaluation, not against the exporter report. Profile metadata must disclose COM-only world forces, absent continuous torque, disabled contacts and recorded-only delivery.

Predetermined component cases use the adopted original P01–P17 and P21–P22 where representable, plus source-valid extreme cases as explicit delivery failures. Tests must include overlapping/opposite/replacement/zero forces; gravity and off-center impulses; release at action completion; generated mass/force/duration edits with unchanged sibling geometry/materials; exact nondecimal completion clocks; a valid short prefix before future failure; float32 boundary collapse; insufficient key/history/byte budgets; callback cancellation; corrupt source identities/history/positions; and coarsened acceleration tracks.

Run the inherited regression and conformance checks without deleting test identities. Build actual force artifacts and independently examine geometry/winding/PBR/motion through the existing pinned Khronos and Three.js tools. Browser playback and inspected captures are separate required evidence for the full delivery gate. Execute fresh identified local validation under [OK-ENG-006](OK-ENG-006-local-validation-and-hosted-ci-policy.md), including the inherited regression, actual Agent transport, independent destination decoding and browser review. Hosted execution remains manual-only and opt-in; no paid hosted job is required for routine integration. Agent/0.5 is already integrated through PR #16. Advertise the Agent/CLI route only with its implemented adapter and verified delivery lifecycle.

## Versioned reconciliation and interface activation

This revision preserves the scope and numerical gates of [the original contract](https://github.com/Omegapy/OntoKin/blob/18cea63ba45fd6bc9989531cb97a3c88d923c524/docs/engineering/OK-ENG-006-native-force-glb-export.md). Its original branch and file remain unchanged. OK-ENG-007 resolves the identifier collision with the adopted local-validation policy; version 0.2 replaces the original hosted-CI prerequisite with that policy. Source semantics, source fixtures and tolerances are unchanged.

Implementing and verifying this adapter satisfies the conditional availability clause in [OK-AGENT-005](OK-AGENT-005-finite-force-program-workflows.md). Explicit Agent/0.5 and CLI GLB/0.5 delivery use the existing request, response, bundle and store shapes. Delivery preparation evaluates only the requested export endpoint; ordinary evaluated requests keep their existing full-horizon meaning. An omitted export endpoint means the authored duration. Failed preparation, cancellation or final-envelope limits cannot commit partial source, run or artifact success. Earlier bindings and defaults retain their existing behavior.

The source contract's adopted additive errata, including the P09 before-zero derivative correction, remain part of the acceptance inputs. New evidence must name their exact bytes and apply old-value preconditions; it must not overwrite the original fixture records.

The earlier regression method identities remain executable. Their unavailable-delivery guards now exercise generic delivery without a named target and unsupported general delivery/physics. Separate positive tests verify explicitly activated GLB/0.5; older-target rejection remains covered. This records the conditional interface transition without claiming that the earlier unavailable-adapter evidence established delivery success.

## Execution record

Implementation and measured results are tracked separately in STATUS and [the component pull request](https://github.com/Omegapy/OntoKin/pull/17). Its source-corpus and actual Agent-delivery preflights have passed independent native and browser checks, with identified visual reviews. Complete force release acceptance remains a separate, unfinished gate until its current execution and evidence audit pass. This contract alone does not establish a release or full-product result.
