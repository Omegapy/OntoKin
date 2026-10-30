# Final independent C076 acceptance review

**Static review approved for the bounded acceptance scope.** The reviewed repair is `32e03a8778370674b8eb6aa78be799cfe8591d8a`. Exact original and repaired source bindings are preserved in `acceptance-review.json` and `acceptance-review-final.json`. No product requests or tests were executed for this review.

## Closed findings

**AR-01: unintended destination scale.** The .9 independent decoder now rejects nonidentity static scales, matrix transforms, and animation channels outside translation and rotation. Two synthetic tests construct their own GLB envelopes and cover uniform, nonuniform and reflected scales, scale-bearing matrices, animated scale and weights. Native Three.js and browser observations now record world scale and require identity scale at every measured pose. These changes close the identified false-accept path in the reviewed source.

**AR-02: accepted pinned-library preservation.** After repair, the acceptance workflow now reads the accepted durable bundle with `service.read_program`. It compares the stored entry to the frozen repaired source and the stored module bytes to the original pinned library. The assertion therefore covers actual accepted source rather than only locally prepared expectations.

## Review scope and remaining execution

All 55 frozen source rows remain in the acceptance loop: 17 expected deliveries, 34 expected invalid programs and four source-valid destination rejections. The input freeze is checked before execution. Generated composition and the Agent-repaired assembly add two separately identified GLBs. Analytic checks cover authored rings, cap coverage and nonoverlap, closure, inner-wall orientation, outgoing material ownership, numeric geometry, materials and recorded motion. The Python checker uses no production triangulator.

The destination checker requires successful source acceptance, exact artifact hashes and source revisions, pinned tool versions and zero Khronos errors or warnings. Seven representative artifacts request fourteen browser captures; actual image review remains a separate role. Translation, rotation and scale are checked at all five fixed pose times.

Root must run the repaired oracle methods and final source, Agent and destination checks on the identified candidate. This source review does not convert earlier runs into evidence for the later checker and does not establish release acceptance.
