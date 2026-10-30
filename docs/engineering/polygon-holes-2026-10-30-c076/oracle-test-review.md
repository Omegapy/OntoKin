# C076 independent geometry-test adequacy review

Reviewed candidate `15c45f3ee3ed39883188e71bbde0e4d1482f8757`, tree `1eda7611fdd1294aaf7d9764e881dfdd8f41725e`.

## Independence and scope

This review covers root-authored `tests/test_holes_oracles.py`, `tools/holes_oracles.py` and the geometry portion of `tools/run_holes_acceptance.py`. The reviewer authored `tests/test_holes_geometry.py` and the native geometry/delivery modules, so no independent-review claim covers those files. Their existing tests provide complementary implementation evidence, not independent approval by this reviewer.

No runtime test was executed for this review. File hashes and test method names are recorded in the accompanying JSON from immutable Git objects.

## Adequacy findings

The 20 oracle tests use a manually divided square plate with an opening. Four explicitly authored rectangular bands provide its cap triangles; no product compiler, exporter or triangulator constructs that control mesh. This is a useful independent positive control.

The negative controls address the relevant ways an incorrect hole mesh could pass superficial checks: a missing triangle; an equal-area duplicate cap; a cap crossing an opening despite a material-side centroid; reversed inner-wall geometry with correspondingly reversed normals; wrong outgoing-wall material with otherwise matching color; altered PBR color/roughness; a tilted unit normal; inconsistent repeated corners inside the usual position tolerance; nonauthored corners; reversed caps; and an unclosed wall.

Separate exact-overlap controls cover triangle containment, shared edges, and crossing triangles without containment. They address distinct clipping cases, rather than merely asserting agreement with the production graph algorithm. Destination controls require the explicit `.9` binding and reject static scale, matrix transforms, and animated scale/weights that local-position measurements alone would miss.

The acceptance runner checks the unchanged frozen input hashes, then runs every frozen source case against its declared expected outcome and diagnostic where specified. Its successful geometry paths use the independent decoded-byte checker for authored corners, exact boundary/coverage topology, cap overlap, outward walls, materials, analytic volume/surface area and motion poses. It separately compares reordered-declaration geometry, generated instances, exact accepted repair bytes, unchanged sibling geometry and pinned-module bytes. The runtime helper I authored is not imported by the independent geometry oracle.

The independent oracle deliberately supports the frozen identity and X-half-turn placements. Its source-bound coverage checks and error tolerances establish those finite fixtures; they should not be described as universal independent coverage for arbitrary placement angles or unseen geometric inputs. Native arbitrary-placement tests remain a separate implementation-test role.

## Conclusion

No new test-design blocker or concrete additional probe is identified for the declared C076 increment. The controls exercise the material geometry risks that motivated holes support, and they use independent expected geometry. Further broad or randomized testing is not requested by this review. Actual execution on the identified complete candidate, inherited checks and final integration verification remain necessary and separately attributed.
