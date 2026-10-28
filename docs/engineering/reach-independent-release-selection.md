# Selected ancestry for independent release

Status: the identified candidate passes its 7-method differential cohort and
108-method combined cohort. Original P16 still exceeds the unchanged
100,000-operation limit. The worker starts from checkpoint015
`21ed7fc9f7ebd50ccc124a0742c9e615e4766fdb`; that baseline stops while building
the independent incoming ideal pose map. The candidate completes both incoming
maps and stops later in release's independent source-basis calculation. This
note records a bounded reduction of unused calculation, not a new recording pass.

## What release consumes

`ReachReference._release` obtains the actual and ideal incoming kinematics of
the grip child's object. Each pose contains position, orientation, linear
velocity, and angular velocity. The existing recursive `_pose_map` walker
constructs those fields from the complete dependency ancestry, including the
root, parent sites, follows or joints, coordinate laws, and inverse child-site
transform.

Previously both release calls requested every object and site frame, then
selected only the child's frame from the result. The other calculated values
did not contribute to the release anchor, its source allowances, or the saved
release record. The release clears the pose-map cache before returning.

The two calls now pass the child frame through the walker's existing `selected`
argument. They keep `pose_only=False` and calculate actual and ideal poses
separately. The complete spatial derivatives and all original arithmetic
remain required.

## Why the selected result is unchanged

For a fixed incoming state, time, and actual/ideal choice, the walker computes
a frame from its current source node and recursively computed parents. Its
dependencies do not include unrelated children or siblings. Restricting the
outer target loop therefore leaves the selected frame's equations and full
ancestry unchanged. The same ordinary numerical cache can supply previously
completed subexpressions. No recording recurrence, source producer result,
additional cache, or sampled trajectory is introduced.

The release's source-admission checks run before pose construction. Its grip
must be active, the child must be a prescribed physical sphere, and earlier
statements must not have changed any incoming dependency. Contributor
selection, complete materialization, source allowances, force processing,
history weights, and staged-state publication are unchanged. A later request
for another object or site still evaluates that object's complete ancestry.

Source admission does not depend on release incidentally visiting unrelated
frames. Construction resolves every object, site, joint and follow, then
validates the complete relation graph. Independent initialization still admits
every object's placement and every dynamic object's velocity and angular
velocity. Recording preparation retains complete source boundary kinematics
and the public finiteness checks for all frames, including unselected sites.
Destination validation requires every semantic object exactly once, then
checks every delivered carrier's source phase, endpoint and certificates.
Complete authority, force and impulse boundary histories remain required.
Calling `build_reference` on a manually corrupted private model alone is not
whole-graph source validation; an unrelated error may be deferred until its
frame is requested, as with the existing selected observation paths.

Skipping unrelated targets can change how many arithmetic/cache callbacks
occur. It cannot omit a callback required by an executed selected-ancestry
operation. Those operations retain the live operand cap and cancellation
checks. Failure during either actual or ideal calculation leaves the last
committed independent ledger unchanged.

## Verification obligations

The dedicated differential tests restore the preceding full-map behavior only
inside release, then compare complete before/after states, dynamic anchors,
release records, and source history. Cases cover original P16, a nonzero
rotated child site, two releases at one boundary, dependency conflicts,
duplicate release, cancellation, and a narrowed operand cap. Existing
transfer-bound and short-export tests remain necessary, including independent
rejection of an understated certificate.

Any measured reduction must use the original frozen source and settings. A
lower standalone reference count does not establish a complete P16 recording
pass. The full original 28-recording suite follows integration; later Agent,
compatibility, destination, browser, and release-audit gates remain open.

## Executed candidate evidence

All three runs identify source commit
`6cf9aa6b1193608bac1331af1f72e49a57ff51c0`, tree
`0ff6e241ba24f833f13807777c94ea0313c3e4a4`, CPython 3.12.14, and stable
before/after tracked inputs. The development driver is preserved with each
result; its SHA-256 is
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.

| Evidence directory | Actual result |
| --- | --- |
| `p16-selected-focused-001` | 7/7 passed; complete text log; no errors, failures or skips. |
| `p16-selected-combined-001` | 108/108 passed, including all 27 release-cell arithmetic, source-identity, transition and short-export methods; complete text log; no errors, failures or skips. |
| `p16-selected-original-001` | Original P16 failed at operation 100,001 in `_release` -> `_phase` -> `_source_basis` -> `relative_composition`. No GLB was accepted. |

P16 retains source program revision
`sha256:0487f3f410944484f0a6aad7bef37e1a59a1d13464b19af85661251c430388f7`,
end 4 seconds, 1 fps, helpers disabled, position and rotation tolerances 0.001,
and time tolerance 0.000001 seconds. The full work-category totals equal the
capped baseline; neither run measures the uncompleted whole request's cost.
The source snapshots explicitly disclose 37 unmaterialized historical binary
archives and do not establish the release input-closure role. The follow-up
to the tested source changes this engineering note only; runtime and test
bytes retain their tested identities.
