# Independent C076 acceptance review

Reviewed source: `c5d03f939bc26cde5b79c713958880cbca84a00e`. Exact reviewed file hashes are in `acceptance-review.json`. This review made no product requests or test executions.

## Findings

**AR-01 — Destination scale is not checked.** The inherited Python pose reader ignores static node scale and scale animation channels. The acceptance runner compares only translations and rotations. The Three.js and browser checks do the same, while native geometry is transformed by the inverse carrier matrix before comparison. An unintended uniform carrier scale of two can therefore retain the expected local vertices, material values, counts and motion observations while rendering doubled geometry. Require identity static/world scales, reject scale channels, and preserve an independent synthetic adversary that demonstrates rejection.

**AR-02 — The library assertion needs a stored-source read.** The acceptance runner builds its repaired expected bundle using the original local module tuple and then compares those two local tuples. That proves the expected data remained unchanged; it does not directly prove the accepted durable module stayed unchanged. Read `service.read_program` after the successful repair and compare the actual entry, revision and module bytes to the frozen expected bundle. The separate focused Agent test already checks this behavior.

## Supported checks

The runner traverses all 55 frozen source cases: 17 positive cases, 34 expected invalid cases, and four source-valid destination rejections. It verifies the frozen input hashes before executing. Composition and targeted repair retain separately specified expected geometry and source revisions.

The Python geometry checker imports no product triangulator. It combines unique authored-corner mapping, independent cap-domain and exact overlap checks, directed cap-boundary incidence, opposite mesh-edge incidence, inner-wall normals, per-edge materials, measured area, volume, perimeter and bounds. Its adversaries use a hand-divided plate rather than a product-generated control mesh.

The destination checker requires a passed acceptance record, matching artifact hashes and source revisions, pinned package versions, zero Khronos errors and warnings, and actual Three.js and browser playback. The seven selected browser artifacts request fourteen captures. Capture generation remains distinct from actual visual review.

This review requests the two changes above before using these checkers for final candidate evidence. It makes no release-acceptance claim.
