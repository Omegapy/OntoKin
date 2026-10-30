# C077 independent fixture authoring

The fixture worker began at published decision `4d1b15f5859e7f08feb8041b67c112d9f1485174` on `work/polygon-lofts-fixtures-c077`. Scope is this examples directory. Authoring used Python's standard library and inspected the inherited source syntax. No OntoKin module was imported, no product request was executed, and no runtime outcome was used to choose expected results.

The initial 73-case authoring cut is retained as local commit `0d0a82a08d2bc6a3f518abc1f01bba27f7b12266`, tree `6ae5740e13c0a841fb86a6420cfe38afc86fa5ee`. Its freeze SHA256 is `3bdaa34c21cbc3d22710147aace141be909a85e9d2e1339a3c3da1cc6a515c64`. The additional changing-cap control below was requested during independent review before publication or runtime implementation. It is a prepublication expansion, not a changed expected outcome following a product failure.

## Preparation checks and correction

Seven prism/frustum/authority measurements agreed with independently written analytic formulas. An independent exact two-dimensional segment, winding and containment check passed all 62 authored sections in the initial valid and delivery-refusal cases. This checked fixture coordinates only; it was not product execution or a general three-dimensional surface certification. Exact repair substitutions produce the complete frozen repaired and invalid entry bytes; the four composition entries retain the pinned module SHA256. All initial freeze file sizes and SHA256 values matched.

A static comparison with inherited `placed` syntax caught an authoring error before the initial commit: the placement must be `placed(geometry, pose(self.frame, vec3(...), quat(...)))`. The generator originally used three placement arguments. This was corrected before freezing any source; it is a preparation correction, with no failed runtime attempt. The final source files use the inherited pose form.

Both count maxima independently satisfy SN=256, H=8, T=540 and 1,620 flat corners. The largest authored source is the invalid aggregate-count case at 32,886 bytes, with approximately 11,186 lexical pieces counted independently of the language lexer. Its explicit budget request preserves reachability of the count diagnostic; actual resource consumption remains unmeasured.

## Different endpoint cap diagonals

`changing-concave-cap-diagonal.ok` uses lower vertices `(0,0),(4,0),(1,1),(0,4)` at z=0 and upper vertices `(0,0),(1,2),(4,4),(0,4)` at z=3, with keys v0 through v3 in that order. The lower concave polygon admits diagonal v0-v2; v1-v3 lies outside. The upper concave polygon admits v1-v3; v0-v2 lies outside. Reusing either endpoint's cap triangles at the other end therefore fails coverage.

For relative height t in (0,1), the actual fixed-diagonal side cross-sections contain these points:

| Side | Ordered XY cross-section |
| --- | --- |
| v0-v1 | `(0,0)` → `(4-4t,0)` → `(4-3t,2t)` |
| v1-v2 | `(4-3t,2t)` → `(1,1+t)` → `(1+3t,1+3t)` |
| v2-v3 | `(1+3t,1+3t)` → `(4t,4)` → `(0,4)` |
| v3-v0 | Vertical boundary x=0, from y=4 to y=0 |

The first three sides lie in successive y bands `[0,2t]`, `[2t,1+3t]` and `[1+3t,4]`. Their boundaries meet only at their shared endpoints. The middle side stays at x≥1, away from the fourth side. Its two segments have turn determinant `-9t(1-t)`, so they do not overlap. The other two sides are simple within their bands. Each intermediate section of the actual triangles is therefore a simple closed polygon; every triangle has nonzero area, and the valid endpoint caps close the surface. This proves the control's surface validity without invoking either a product mesh routine or an assumed linearly interpolated polygon.

The expected volume and area still come from authored coordinates, cap shoelace areas and prescribed strip determinants. The fixture additionally names the two required internal cap diagonals. Implementation, exported-byte checks and destination results remain pending.
