# C066: exact radius candidates for cold native spheres

## Decision

**NO-GO for implementing the selected unrestricted eight-index shortcut on the present proof.** The ideal lattice has a small set of maxima, but that does not establish the exact maximum of the actual rounded binary64 vertices. A conditional subnormal witness demonstrates how ordinary final-coordinate rounding defeats the ideal-only argument. A restricted error-enclosure theorem remains valid, but its constructor premise, authority, exception order and positive complete-request accounting are not established.

This is a finite source-design decision. It does not reject every shortlist, every normal-radius restriction or every actual-coordinate screen. No OntoKin runtime file is changed. No product request, runtime suite, sphere generation, native trigonometric evaluation, instrumentation, benchmark or hosted job is executed by this checkpoint.

The baseline is actual main `b7357df3bc296cc1cd728bdf52dbeaf2697da85b`, tree `9a49a2bfb5144774bb7d8fe89532e947395b3af8`. [Source recovery](RECOVERY.md) explains how every indexed source byte was recovered and verified without claiming a fresh verification of the missing original C065 portable ZIP. [Source bindings](source-binding.json) identify the exact files used below.

## What the radius means

The independent supplied-byte reader reconstructs the source mesh and checks every supplied binary32 vertex against it. Its radius is the largest exact rational value of `abs(x)+abs(y)+abs(z)` over the actual source vertices. This L1 radius bounds the mesh for later motion-error calculations. It is not the source sphere parameter, the Euclidean radius, or an ideal radius multiplied by the square root of three.

`sphere_mesh` uses 32 longitude segments and 16 latitude bands for an ordinary native sphere. Two poles and 15 rings of 32 positions produce **482 vertices**. Angle expressions, native trigonometric results, component multiplication and radius multiplication determine the actual binary64 coordinates. Ideal symmetry does not promise identical floating-point magnitudes in different quadrants.

The cold reader retains one geometry-point charge per vertex, validates its three source-to-binary32 conversions, computes an upward float screen and checks an existing repeated-maximum witness. A point that still could increase the maximum receives an exact sum. Component conversion errors are accumulated separately; their final exact result and all later site-radius additions remain part of the baseline.

## The selected proposal

The natural ideal-lattice maxima lie at latitude labels 5 and 11 and longitude labels 4, 12, 20 and 28. With the constructor's top pole at index zero, the corresponding eight indices are:

`133, 141, 149, 157, 325, 333, 341, 349`.

The reviewed proposal would perform exact radius sums only at those points, in their original traversal positions, while preserving every vertex conversion, error update and geometry charge. It would keep all eight actual points rather than assume equal rounded sums. Eligibility and selection would need a concrete bounded representation; no free index tracking, new cache or bulk-copy exemption is assumed.

An eager version that computes those exact sums before earlier supplied vertices are checked is separately unsafe without a supported restriction. It can make a callback or arithmetic exception precede an earlier geometry mismatch. The in-order version avoids that particular reordering, but still needs native/passive authority and an unchanged fallback for unsupported cases.

## What the mathematics proves

For the **ideal** 32-by-16 unit lattice, exact half-angle identities give selected L1 sums greater than 1.73 and excluded L1 sums less than 1.71. The [mathematics review](reviews/math.md) supplies the symmetry and unimodality argument; [the standalone derivation](math_derivation.py) verifies its rational radical bounds by squaring positive quantities. It does not call a native trigonometric function.

A useful conditional theorem follows. For any positive radius `r`, suppose every actual coordinate differs from its ideal scaled coordinate by at most `r/1000`. Each L1 sum then differs by at most `3r/1000`. Selected actual sums exceed `1.727r`, and excluded actual sums are below `1.713r`. Under that premise, every actual maximizer belongs to the eight indices. Computing those eight **actual** sums exactly would return the required radius.

The premise is not supplied by the current constructor. Its `math.sin` and `math.cos` calls are not a source-bound enclosure for the complete sequence of angle rounding, transcendental evaluation, component products and final scaling. The correctly rounded language built-ins and the host calls inside this mesh constructor are distinct mechanisms. Excluding subnormal radii removes the particular witness below but does not establish the required enclosure, authority or cost.

### Conditional underflow witness

Let `mu = 2^-1074`, the smallest positive binary64 value, and let the radius be `r = 2*mu`. Assume the **actual normal-component magnitudes** meet these broad intervals:

- All three components at each of the eight selected points are strictly between `1/4` and `3/4`.
- At excluded index 69, latitude 3 and longitude 4, x and z are in that same interval and y is strictly between `3/4` and `1`.

The ideal trigonometric normal factors satisfy these intervals with wide margins. Actual native factor membership was **not measured or certified** in this session; it is an explicit condition of this source witness.

Multiplication by `2*mu` maps the first interval into the open rounding cell `(mu/2, 3*mu/2)`, so each selected coordinate magnitude becomes `mu`. The second y interval maps above `3*mu/2` and below `2*mu`, so the excluded point becomes `(mu, 2*mu, mu)` in magnitude. Thus each selected exact L1 sum is `3*mu`, while index 69 has `4*mu`. The full maximum is at least `4*mu`; the shortlist would return the wrong radius under the stated conditions. The strict intervals avoid midpoint ties.

This is an exact conditional arithmetic counterexample, not an executed native-mesh failure. Its purpose is to reject the unrestricted ideal-only proof and expose a boundary that a repaired implementation must cover. It does not establish the exact maximum on a particular unexecuted platform.

The source domain does permit this radius. Core numeric rules allow finite subnormals. Literal conversion reports underflow but retains positive results. The visible `sphere` check requires positivity; the positive-inertia rule belongs to `sphere_body`, and visible geometry may use `no_body`. The exact terminating decimal for `2^-1073` has 1,075 characters, below the 4,096-character limit. Binary32 conversion to zero is permitted, while the reader retains the tiny source-to-stored error. These facts establish the inspected authoring/radius/conversion gates, not a successful complete export.

## Cost: actual candidates, not all vertices

Each existing float point that reaches the exact fold incurs three `independent_bound_decode` and three `independent_exact_add` charges. `_Bounds.total` receives a generator, so its tuple-only zero-elision route does not apply. A completed original candidate therefore costs **six numerical charge calls**, subject to its original callbacks and guards.

Let `B` be the actual baseline candidate count after the existing float and repeated-maximum screens. Let `K` be the proposed retained exact-candidate count, `L` all new selection work, `A` other admission/setup/copy/publication work, and `F` extra fallback or repeated work. A completed scan has the conditional accounting:

`net saving = 6*(B-K) - L - A - F`.

This is an equality only if all other events are genuinely unchanged; otherwise it is an optimistic upper bound. The source contains 482 vertices, but **B is not established as 482**. Current geometry counters mix retained work with candidate arithmetic and cannot supply the missing count.

There is also a feedback effect. In the proposed shortlist-only scan, skipped early candidates do not raise the running radius. It stays zero until the first selected index, 133. Even a zero coordinate triple has a positive upward `nextafter` screen, so at least **134 proposed-screen selection decisions** occur through that point. Selection count cannot be replaced by the baseline candidate count. Adding an ordinal to the current unindexed loop adds work; retaining eight point identities avoids that particular mechanism but adds bounded setup and authority work.

With a favorable one-charge membership mechanism and no hidden per-vertex index work, the necessary inequality is `6*(B-K) > 134 + A + F`; later selection can make the requirement larger. This does not prove every shortlist unprofitable. It identifies the missing counts and schedule. The [cost review](reviews/cost.md) covers rejected admissions, interrupted folds, direct rescans, cache eviction, replay and producer work without a consumer. Warm extrema reuse already avoids cold arithmetic and supplies no new saving to pay for setup.

## Authority and first exceptions

The cold helper receives source positions, stored positions and work. It receives no sphere recipe or producer receipt, and also serves other primitives, helpers and surfaces. The primitive cache binds typed radius and role namespace, but not the historical constructor and transcendental dispatch that produced a mesh. Exact tuples of native float triples are stable values; their shape alone does not prove their origin.

The [authority review](reviews/authority.md) distinguishes immutable value stability from mutable work/dispatch state. It records conditional source witnesses for eager future arithmetic, omitted foreign callbacks, narrowed operand limits and a changed constructor restored before consumer inspection. None was executed as a product test or attributed to an original recording failure.

A valid restricted optimization may change native budget checkpoints when it removes real work. Identical native callback counts are not imposed here. Foreign callbacks, changed dispatch and narrowed domains still need their original path or a separately justified live restriction. Existing native-field checks are a possible list of concerns, not a free geometry certificate. The unresolved C057 comparison-accounting/passive-authority issue is neither waived nor treated as a universal prohibition.

## Actual checks and integration boundary

The source recovery verifies all 3,547 baseline source files, 621,703,468 bytes, the complete tree and the actual raw final commit. The C064 packet and its original ZIP passed the unchanged verifier after separately retained preparation corrections. The original full C065 packet and ZIP were unavailable and were not relabeled as verified.

The C066 derivation verifies the bound source inputs and actual AST structure, derives the 482-point count and eight indices, checks the six-charge fold and the unchanged conversion/error order, and reproduces the conditional rational mathematics and cost identities. It imports no OntoKin module, generates no mesh and invokes no native trigonometry. Independent mathematics, authority and cost reviews are retained with their exact hashes. [Validation](validation.json) records actual execution separately from the source arguments.

Documentation preservation/link checks must be performed on the exact published candidate, actual merge and final main. Their receipts identify their own source commits and inventories; they cannot establish a new runtime speedup or recording success.

## Preserved obligations

All 65 runtime files, original fixtures, tests, helpers, horizons, frame rates, equations, independent oracles, tolerances, defaults and workflows remain unchanged. Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and 64 cursor updates.

Historical original recordings remain **24/28, failed**, with **P11/P16/P23/L03 unresolved**. M1 remains rejected. C035 remains held, including adverse timing. C057, complete reach acceptance and historical Git LFS payload migration remain open. C066 establishes no runtime improvement, complete positive request-cost premise or release acceptance.

The [next task](NEXT-TASK.md) must avoid assuming an ideal-lattice maximum and begin with a concrete, funded actual-coordinate premise. It remains proposed until separately claimed after fresh repository reconciliation. The full [GOAL](../../../GOAL.md), including every unfinished modeling, dynamics, movement, domain and engine-delivery requirement, remains authoritative.
