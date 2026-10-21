# Independent reach reference continuation

This work continues the independent reader/reference gate described in the
[reach review checkpoint](reach-release-review/README.md). The complete
[release contract](../language-design/planar-reach-v0.1/release-contract.md)
still governs acceptance. The original 100,000-operation request budget and
frozen source/expected bytes are unchanged.

## Bounded reuse

The independent arithmetic context now retains pure normalization, rotation,
Hamilton product, constant-pose, composition and inverse results in its existing
256-entry cache. Exact immutable interval operands and precision identify each
result. Cache lookup and insertion call the original shared work callback;
hits can be cancelled and do not replenish the request allowance. Least-recent
replacement avoids leaving the cache permanently full of early source values.
The pi helper returns its calculated enclosure safely after saturation.

Exact zero vectors, zero scaling, unit scaling and either scalar unit-quaternion
representative have explicit algebraic paths. They omit arithmetic whose exact
answer is known. General interval operations and prospective operand guards
remain in the independent implementation. No production solver, controlled
pose evaluator, recording planner or certificate generator supplies an expected
answer. Source graph traversal, ownership, lifecycle, boundary history weights
and complete outgoing records retain their separate checks.

Full pose cache keys contain derivative operands. Equal positions with changed
angular or linear rates therefore do not share a full kinematic result.
Independent uniform-basis lookups avoid reconstructing an already captured
immutable state's relation graph when the requested carrier is cached.

## Recording-only expectations

`ReachReference.recording_pose_enclosure(carrier, time, side="after", ideal=True)`
returns only independent position and orientation intervals. It uses exactly
the full resolver's position and orientation expressions, which do not depend
on spatial derivative output. Only the selected carrier's ancestry is resolved.
The internal derivative-free graph has a distinct cache namespace, and its
public return type has no velocity or angular-velocity fields. Full snapshots,
incoming releases, impulse histories and point/phase bounds continue to use
the full derivative path.

The returned intervals concern one exact clock and side. They do not establish
continuous interpolation accuracy or supply a missing whole-phase bound.
Independent certificate inequalities, actual stored key checks, all boundary
histories, destination/native/browser execution and visual review remain
separate required evidence.

## Executed checkpoints

On CPython 3.12.14, commit `0f20876cb7a09e18a4b19cd2a10a4864381d44f6`
passed all 29 methods in `test_reach_reference_reuse`, `test_reach_reference`
and `test_reach_source_rates`, with no failures, errors or skips. The first
attempt retained one failure in a newly added exact antipodal-identity test;
the subsequent algebraic shortcut corrected it without changing an allowance.
Raw logs are retained by the continuation's execution collector.

That result predates the recording-only API added above. Its two new comparison
and invalid-selection methods require their own identified execution. This
document does not count authored tests as passing, adopt the proposed
[rate criterion](reach-rate-acceptance.md), or close any full release role.
