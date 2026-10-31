# Independent C079 fixture authoring

Author: `/root/pocket_fixtures`, a separate worker from the runtime and geometry authors. Source baseline: `50998106fe468e6630f17c79d88f7810da81bc32`. The final freeze records the separately published OK-LANG-012 decision and its complete byte hash.

The author read the source-language contracts, C078 handoff, earlier frozen source examples and their external expectation formats. No OntoKin product module, constructor, parser, triangulator, delivered-mesh checker or runtime was imported or executed. No new production implementation was read. The generator uses Python's standard library to write ordinary source and compute boundary-derived measures. Reading an earlier example supplies syntax context; it does not supply a measured answer for the new pocket geometry.

## Measures and arithmetic

The exterior and every pocket are independently authored planar polygons. Signed shoelace sums use exact rational values of their canonical binary64 coordinates. Boundary lengths use independent Euclidean segment lengths. For exterior area A0/perimeter P0, height H, pocket areas Ai/perimeters Pi and actual effective depths Di, the volume is `A0*H-sum(Ai*Di)` and area is `2*A0+P0*H+sum(Pi*Di)`.

The pocket floor calculation first converts H and authored d to exact binary64 rationals. It computes b=H-d, compares b to the exact binary64 0.001-meter endpoint and rounds the completed b once to the stored floor f. Effective geometric depth is the exact value H-Fraction(f). Each valid expectation preserves the exact base and effective depth as reduced decimal-string numerator/denominator objects. `effective_depth_value_m` is only a convenient rounded numeric display of that exact value.

The `minimum-base` case uses H=0.002 and d=0.001. Their exact binary64 difference equals the minimum endpoint. The `below-minimum-base` negative increases d by one binary64 step; its exact base is below the endpoint. The `rounded-floor` case uses H=0.3 and d=0.1 and records the actual rounded floor instead of assuming the written decimal difference. The independent `ANALYTIC-CONTROLS.json` retains these arithmetic facts.

For n0 exterior vertices, p pockets and N total boundary vertices, the domain counts are n0−2 bottom, N+2p−2 top, N−n0−2p floor and 2N wall triangles. The total is 4N−4 triangles, 12N−12 flat corners and 2N logical positions. The max-count case has eight exterior vertices plus eight seven-vertex pockets: N=64, 252 triangles and 756 flat corners. It does not assume that these boundary formulas prove the correctness of any later triangulation.

The rectangular reference independently gives 24−1=23 m³ and 24+28+3=55 m². An exact source edit to 0.75 meter depth gives 22.5 m³ and 56.5 m². The five precision cases separately establish that certain distinct source coordinates map to the same binary32 position. In the floor case, translated coordinates 16384.001 and 16384.002 both become 16384.001953125. That future export must fail for actual geometry/precision under its explicit sufficient resource request.

## Source identity and composition

Logical identities follow the decision's four-part namespace: exterior `outer/outer/vertex/lower-or-top`; pocket `pocket/pocket-key/vertex/lower-or-top`. The valid `pocket-key-outer` case ensures that a user pocket named `outer` remains distinct from the exterior. Keys, explicit orders and values remain the same in the declaration-reordering pair. Derived faces can be compared by their actual fields; whole-GLB bytes can differ because source revisions differ.

The reusable module exposes `pocket_depth` as a public length parameter. Each importing entry binds the same exact library bytes. The assembly changes only the first instance override; the sibling receives the unchanged default. The generated example uses depth values 0.25, 0.5 and 0.75 meter and distinct following offsets. All motion is the carrier's prescribed translation, never geometry-owned motion or implicit physics.

## Refusals and evidence boundaries

Source negatives isolate counts, keys/orders, point topology, winding, containment, material ownership, types/units and height/depth/base admission. Penetrating or bottom-reaching depths require `OKL-E-POCKETS-DEPTH`; a positive nonpenetrating depth leaving an insufficient exact base requires `OKL-E-POCKETS-BASE`. Earlier declaring source rejects .12 types and constructors, without predetermining a parser-versus-type phase.

The expectation documents distinguish valid source, intended delivery and executed evidence. No fixture-authoring result establishes an actual source pass, an Agent operation, a complete inherited regression, native/browser playback, visual disposition, Unreal import or live physics. Each must have a later actual result on identified implementation bytes.

## Reproduction

`generate_fixtures.py` is a standard-library authoring helper. Run it only against a new external output directory, supplying the recorded decision commit and decision file when creating a new manifest. It refuses an output directory that already contains `acceptance-freeze.json`. The frozen corpus itself is immutable; no regeneration is needed to run acceptance.

The reproduction helper computes no triangles and contains no product import. Its retained recipe data, source formatting and numeric controls make author choices inspectable. Topology checks and source/binary32 delivery checks remain independent executable obligations for the implementation and acceptance reader.
