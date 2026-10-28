# Independent repeated-geometry extrema

This optimization changes only the independent supplied-byte reader's repeated
pure geometry calculation. It does not change the source mesh, the recording
key plan, the 100,000-operation cap, operand limits, tolerances, or certificate
claims. It is not release acceptance evidence by itself.

## Exact reused result

For a complete source position tuple of native binary64 triples, the existing
scalar reader independently checks each actual vertex against exactly one
binary32 conversion of its source point. It derives the exact maximum source
L1 radius and the conservative norm of the maximum coordinate conversion
errors. These values depend only on that immutable source tuple once every
stored position has passed the conversion equality.

A successful scalar proof may therefore retain those two exact Fractions and
the immutable triples that satisfied the conversion check. The cache retains a
strong reference to the complete source tuple and only accepts exact tuple and
float types. A source identity cannot be recycled while that proof exists;
mutable or nonnative source representations use the scalar path. The identity
key deliberately excludes the mutable supplied accessor.

Every warm occurrence checks all current accessor rows. Bounded groups of at
most 128 native triples compare against the proved conversion, with a shared
operation charge and cancellation callback before each group. No group is
skipped and a mismatch invokes the original scalar diagnostic. Native equality
preserves the original acceptance of positive and negative zero. NaN cannot
equal a finite proved component. Neither an accessor identity nor a prior
occurrence's acceptance can hide a changed supplied vertex.

## Domain and resource behavior

The optimization requires the unchanged full 32,768-bit operand cap and at
least 128 positions. Smaller or narrowed-cap requests retain the scalar
algorithm. The cap is rechecked after cache lookup/promotion, every comparison
or proof block, and cache publication. A callback that narrows it forces a new
scalar calculation under the current cap. Both cached results' numerator and
denominator sizes are guarded before return. Callback exceptions propagate
unchanged; no partial result is published.

The proof occupies one entry in the existing request-local 256-entry LRU.
There is no additional numerical table. The existing complete mesh vertex
limit bounds a proof's retained immutable triples. Eviction causes complete
recalculation. During initial proof construction the actual rows are checked
again against the immutable source conversion, so a callback cannot bind the
completed scalar proof to unchecked replacement accessor values.

Every repeated source occurrence still consumes its full aggregate vertex
allowance. Source identity and provenance, topology, normals, material
partitions and PBR, helper roles, and owner-specific site radii retain their
separate checks. The independent source mesh cache remains separate from the
writer's cache. Neither recording generation nor independent source pose
arithmetic is called to establish this geometry proof.

## Verification obligations

The focused tests compare exact cold and warm results, actual mutation in each
block and the final vertex, signed zero, malformed/nonfinite rows, distinct and
mutable sources, nonnative fallback, narrowed caps, callback cap changes and
exception identity, mutation before publication, and eviction. The existing
source-mesh occurrence tests additionally check complete repeated vertex
allowances and actual last-sibling POSITION, NORMAL, index, material and
provenance tampering. Completed runtime results must be recorded separately
with their exact source identity; these tests are not a claim of a completed
28-artifact gate.
