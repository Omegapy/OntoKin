# Reuse of bounded source surface construction

This is a scoped implementation record for repeated native surface recipes in
GLB/0.6 recording. It preserves all source occurrences, actual buffer checks,
the original 100,000-operation request budget and its existing 256-entry cache.
The complete P23 recording and release gates require separate execution.

## Repeated construction in the frozen P23 source

The unchanged [P23 source](../language-design/planar-reach-v0.1/sources/p23-maximum-chain-count.ok)
instantiates 32 arms from the [shared library](../language-design/planar-reach-v0.1/libraries/reach-parts.ok).
Each arm has two equal one-meter [Segment recipes](../language-design/planar-reach-v0.1/libraries/reach-exterior.ok).
Each three-section, 16-facet, flat-capped Segment has 96 triangles and 288
duplicated flat-shaded vertices. With helpers disabled, the complete source
still has **97 object occurrences**: the rack, 32 empty arm assemblies and 64
surface segments. Its aggregate vertex count is **18,456**, including the rack's
24 vertices. Geometry reuse never reduces these occurrence counts.

Static inspection of the existing constructor yields 360 callbacks per
Segment: one initial triangulation callback, three section rings, 32 lateral
facets, 32 cap facets, two palette groups, one triangulation return, 288 local
vertex transforms and one mesh return. Avoiding 63 repeated constructions in a
pass removes 22,680 such callbacks before key and cache bookkeeping. This is a
static cost derivation, not a measured end-to-end saving. The recording writer
and independent supplied-byte reader previously each performed those repeated
constructions.

## Complete immutable constructor inputs

The [source-mesh helper](../../ontokin/scene.py) takes a bounded snapshot of every
geometry-defining input: the complete section sequence and its names, stations,
centers, radii and regions; the complete regional palette and PBR values; facets
and cap mode; and the optional local position and rotation. It preserves exact
integer types and binary64 bit patterns, including signed zero. Exact built-in
tuples, bounded section/material counts and bounded names make the cache key
finite. Mutable or unusual host values follow the existing uncached constructor
and its original validation.

Only a successfully constructed immutable `SurfaceMesh` enters the cache. The
constructor validates the exact frozen snapshot associated with its key, so a
later equal key identifies the same validated inputs. A changed section,
material, local placement or numeric type cannot obtain the earlier result.
Copying the constructor inputs also prevents a caller-owned dictionary from
changing the meaning of an already retained key.

Each key, section and material inspection uses the original work object.
Lookup, promotion, insertion and eviction use its existing charged methods;
the implementation creates no work object, cache or enlarged limit. The
remaining vertex allowance is checked again on every hit, and construction or
cache-publication cancellation propagates the caller's original exception.

## Independent reader and per-occurrence obligations

The writer and [independent reader](../../ontokin/reach_conformance.py) use
distinct cache namespaces. The reader's first source reconstruction therefore
cannot use a mesh produced in the writer namespace. It subsequently reuses only
its own pure source-construction result.

Every object/carrier is still traversed and charged. Source identity, ownership,
metadata and provenance are checked for each occurrence. Each occurrence still
consumes all of its vertices from the original aggregate allowance. Actual
accessor lengths, every actual source-to-binary32 vertex comparison, topology,
normals, regional materials and material provenance retain their existing
checks. Owned sites extend each occurrence's radius independently, and frames,
world transforms and animation certificates remain outside this reuse.

No actual-buffer-validation result is cached by this change. The surface
encoder still writes its original per-occurrence accessors and materials;
geometry identity does not become occurrence identity. Legacy callers without
an explicit work object retain their original construction path. The reach
writer must pass its existing `work` into `_nodes` to enable this scoped reuse.

## Actual focused verification

The [regressions](../../tests/test_reach_source_mesh_reuse.py) compare complete
export bytes with reuse enabled, require an independent reader reconstruction,
change geometry/PBR/local placement and reject invalid variants, check reduced
aggregate allowances and cache capacity, preserve cancellation and operation
limits, corrupt the last sibling's actual vertex/normal/index/material/provenance,
and construct all 97 frozen P23 source objects while counting all 18,456 vertices.

All **eight tests passed** on clean implementation
`960d192156c92d0d1818ca3fda0f059cdb431fbe`, tree
`0743693187a3d481188ff8c5c275914bce7ed927`, under CPython **3.12.14**. The
command was `python3 -m unittest discover -s tests -p 'test_reach_source_mesh_reuse.py' -v`.
The [raw log](reach-source-mesh-validation/tests.txt) records 1.466 seconds; the
[execution receipt](reach-source-mesh-validation/tests.json) records the exact
interpreter and source identities. All tracked inputs remained stable.

Two separate actual requests on the same clean implementation constructed the
unchanged P23 source and all requested source nodes, with helpers disabled.
The [baseline](reach-source-mesh-validation/p23-baseline.json) selected `_nodes`'
original uncached constructor path; the
[candidate](reach-source-mesh-validation/p23-candidate.json) supplied the same
compiler's original work object. Both requests used the original
100,000-operation limit and 256-entry cache. Neither reset or replaced its work
after compilation.

| Actual P23 stage | Original construction | Source-mesh reuse |
| --- | ---: | ---: |
| Source construction | 35,913 | 35,913 |
| Complete node construction | 23,547 | 1,379 |
| Total shared operations | 59,460 | 37,292 |
| Surface materializations | 64 | 1 |
| Source object occurrences | 97 | 97 |
| Aggregate occurrence vertices | 18,456 | 18,456 |

The measured saving is **22,168 shared operations**. The 512 new key/cache
operations are included in the candidate total. Complete serialized node data
has the same SHA-256 in both requests:
`38338f03f70692122ffe91b1aabf4a85ada639dd861b178d5bcb4c7dd41ca42f`.
The separate native-surface regression also establishes identical complete GLB
bytes with source reuse enabled. This does not yet establish complete P23
recording, its independent motion/certificate validation or a release pass.

The three raw execution directories are `source-mesh-tests-001`,
`source-mesh-p23-baseline-001` and `source-mesh-p23-candidate-001` under the
continuation's `reach-checks` evidence root. They retain all tracked input hashes
before and after, the exact [measurement script](reach-source-mesh-validation/measurement.py),
logs and receipts. Their combined durable archive remains pending a separately
granted archive window. The committed raw receipts retain these exact hashes:

| Record | SHA-256 |
| --- | --- |
| Test execution receipt | `277a1933aafc1788cfc64732a0abc9a49d9768822f14d7f3c1e401b42a1f80df` |
| Test log | `629da4e80f9f5829f91a82896464faf0e6ee0cc988880d4c8b9c6817cac285ed` |
| P23 baseline receipt | `6706bcc617da4c72172385d8788e700756858d32b9f8bd3d5ff1b4a7a806e69f` |
| P23 reuse receipt | `5cd403484e8eef8a51e548a91f940d86f7c046a341dff1e3ad12efc5f5e80280` |
| Measurement script | `6e926487b7aac060ffe2277c665780f0fdd18b3691be0311ac8cb1aa9bae811b` |
