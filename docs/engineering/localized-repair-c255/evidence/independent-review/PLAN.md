# C255 independent component review plan

Scope: review one inert offline observation checker against frozen C253/0.1.
This review neither launches native applications nor evaluates a model.

## Independent authority

Read raw `before.main.ok`, `after.main.ok`, `rejected-candidate.ok`, and
`hinges.ok`, plus C253 SCORING, PROTOCOL, corpus, RUN-PLAN, NEXT-TASK and
adopted core/construction specifications. Use those sources and hand equations
to construct controls. Historical expected.json and the C210 semantic sidecar
are corroboration, not generated expected-record authority. Do not use the
author's `expected_state` to generate successful test inputs.

The raw source defines two Rack roots; first has three keyed Finger parts,
second has five. Each Finger owns one Blade. Roots have entry Rack definition
identity; every Finger/Blade uses the same package definition identity.
Occurrence identity is root module/scene key + owner/collection/input key,
then `blade` for the child. Count is 2 + 8 + 8 = 18. Sites are 18 implicit
origins + 8 pivots + 8 bases = 34. There are eight follows and eight hinges;
ownership, following and hinges remain separate. All objects are massless.

For first-rack objects travel adds (0, 0.2t, 0). Its middle blade rotates by
(pi/4) min(t,1), with center shifted from its pivot by rotated (L/2,0,0).
The other seven blades have center + (0.3,0,0) from their own Fingers.
Quaternion is (cos(theta/2),0,0,sin(theta/2)); all other rotations are identity.
Use seven times 0, .25, .5, .75, 1, 1.5, 2. Two lengths .65 and .75 have
126 pose slots each. Source primitive dimensions retain 1e-12 m tolerance.

## Controls

1. Independently construct correct V1 (.75 m), V2 (.65 m), and N1 retained
   .65 m states. Verify every stable ID, definition ID, parent, primitive,
   relation and pose. Verify correct source/dependency binding.
2. Positive sign-equivalent quaternions and consistent legitimate revision,
   artifact digest and native index changes. Reordering should not change
   identity-based correspondence.
3. Inclusive/exclusive boundary pairs for source dimensions, reference
   positions/angles, delivery positions/angles/times. Reject tolerance inputs.
4. Mutate wrong target/length, shared default/library, sibling or unrelated
   object; changed site, hinge, follow, owner, mass, action, event, appearance.
5. Change units/frames, geometry, motion, transforms, reflection, scale/shear,
   nonfinite fields, zero/bad quaternion, missing/extra/duplicate IDs/times.
6. Corrupt source/dependency/artifact bindings and author-asserted acceptance;
   stale accepted parent/revision; undeclared rebuild input or changed rebuild.
7. N1 accepted/promoted transiently, route rejection absent/common-harness-only,
   or changed retained bytes. Explicit incompatible dimension diagnostic is
   required at staged acceptance boundary.
8. Missing/empty output, timeout, infrastructure incident and other started
   failure statuses must remain unsuccessful in the denominator; unavailable
   before admission has no attempted-task score. No inert pass becomes a real
   model-trial success or route-admission result.
9. Inspect imports and execution paths for runtime/native/model dependence.
   Bind approval to exact reviewed file hashes and preserve observed failures
   with a separately recorded correction and rerun.

## Limits

Separate caller-owned inert authority records can establish internal byte and
revision consistency, not that a trustworthy external harness or native reader
has executed. Future native readers, revision coordinator and runner remain
unqualified. A finite sample does not prove all-time motion or curved surface
accuracy. No comparison or advantage inference is admitted.
