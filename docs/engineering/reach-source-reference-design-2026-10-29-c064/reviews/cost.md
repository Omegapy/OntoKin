# C064 independent cost and retained-evidence review

## Scope and result

This review reads the C060/C061/C062 records and the complete C063 source snapshot. It executes no product request, imports no product module, changes no runtime source, and does not continue either failed request. The companion standard-library script `../derive_evidence.py` verifies the retained C061 archive, every archive member it uses, and the equality of named current source files with their frozen execution inputs. Its actual stdout is retained in `../derived-evidence.json`.

The evidence identifies the existing cost pools and plan membership. It does **not** retain complete centered-plan node flags or the source float64 vertex arrays. Those omissions limit what can be called observed, even when a separate source argument can establish a property.

A positive net saving over the **complete request** can justify a scoped implementation or experiment without already proving that the request will finish below 100,000 operations. That premise must bound all added work, later effects, fallbacks and cache consequences. A positive saving on the executed prefix alone is insufficient. The numerical reader ceilings below are the stronger conditions for successful completion with an unchanged producer.

## Original request accounting

All numbers are shared-operation counts, not elapsed times. The original last attempted tick is refused at 100,001 before its Reach category increment.

| Quantity | P11 | L03 |
| --- | ---: | ---: |
| Reader-entry shared count | 61,415 | 54,988 |
| Entire-reader allowance with unchanged producer | 38,585 | 45,012 |
| Reader setup | 23,171 | 17,185 |
| First-key-entry shared count | 84,586 | 72,173 |
| Allowance after unchanged setup | 15,414 | 27,827 |
| Entered key-call attempts, including refused tick | 10,286 | 19,498 |
| Work between entered keys | 5,129 | 8,330 |
| Supplied keys | 52 | 178 |
| Carriers | 20 | 6 |
| Full interval/carrier rows | 1,020 | 1,062 |
| Wholly unvisited keys at refusal | 15 | 24 |
| Interval/carrier rows not yet traversed | 320 | 150 |

The reader allowance is `100000 - reader_entry`. It must cover setup, all keys and rows, final source admission, report construction and finalization. The complete original request cost remains unknown.

The current mandatory key/row gates alone require `52*20 + 3*1020 = 4100` P11 charges and `178*6 + 3*1062 = 4254` L03 charges over a complete request. Selected still-mandatory work at the refusal is at least `15*20 + 3*320 = 1260` and `24*6 + 3*150 = 594`. These sums omit other work and are not estimates of the full tail. A design changing those paths needs its own accounting.

Sources: C060 `README.md`, disjoint partition and frontier tables; C060 `evidence/{P11,L03}/work-ledger.json`; C061 `CHECKPOINT-061.md` lines 31-75 and 85-103; C062 `CHECKPOINT-062.md` lines 69-99. Product gate locations: `ontokin/reach_conformance.py` lines 1957-1962, 2136, 2554-2558, 3329-3331 and 3398-3441.

## Reader setup and existing reuse

| Disjoint source-related span | P11 | L03 |
| --- | ---: | ---: |
| Independent reference construction | 2,815 | 2,589 |
| Complete boundary states | 1,530 | 1,761 |
| Source phase tables | 4,856 | 3,053 |
| Final endpoint phases | 1,230 | 277 |
| Independent geometry bounds | 5,559 | 2,342 |
| Separate geometry validation | 111 | 30 |

These are cost pools, not proven removal opportunities. The nested `_phase` totals of 6,006 and 3,300 overlap the phase rows above; they must not be added again or labeled ancestry work.

The admitted key-call category totals are 10,285 and 19,497, including 4,959 and 10,212 generic checkpoints. A typical warm P11 key costs 238 operations, including 101 checkpoints, fourteen stationary carrier comparisons and six centered moving comparisons. A typical warm L03 key costs 114, including 55 checkpoints and three stationary/three centered moving comparisons. Expensive boundaries and cursor seeds invalidate a simple warm-key extrapolation of the remaining tail.

The current reader already evaluates a pending subset, shares topological plans, reuses stationary results, and applies centered/previous-endpoint proofs. A proposal must account for those existing reductions. Relevant source: `reach_conformance.py` lines 1957-2057; `reach_reference_plan.py` lines 379-529.

## Geometry census

The pinned `.ok` definitions supply the geometry dimensions. The retained GLBs independently corroborate the accessor counts, but remain unvalidated reader inputs.

| Case | Geometry | Occurrences | Vertices each | Occurrence vertices |
| --- | --- | ---: | ---: | ---: |
| P11 | Placed loft | 11 | 288 | 3,168 |
| P11 | Sphere | 4 | 482 | 1,928 |
| P11 | Empty | 5 | 0 | 0 |
| P11 | Total | 20 | — | 5,096 |
| L03 | Placed loft | 3 | 288 | 864 |
| L03 | Sphere | 1 | 482 | 482 |
| L03 | Box | 1 | 24 | 24 |
| L03 | Empty | 1 | 0 | 0 |
| L03 | Total | 6 | — | 1,370 |

There are no visual helpers. Each loft has two material primitives sharing a single 288-position accessor; that accessor is counted once per occurrence.

P11 has five distinct loft descriptors: torso; upper arms of length 0.75 and width 0.06, twice; forearms of length 0.5 and width 0.06, twice; upper legs of length 0.6 and width 0.075, three times; and lower legs of length 0.5 and width 0.075, three times. The head sphere has radius 0.25, and three eye spheres have radius 0.05.

L03 has a column loft of length 0.875 and width 0.12, two identical arm lofts of length 1 and width 0.08, a tool sphere of radius 0.12, and a box of dimensions `(0.8, 0.25, 0.8)`.

The observed scalar admissions reconcile exactly with one cold scan per nonempty descriptor group: P11 `5*288 + 2*482 = 2404`; L03 `2*288 + 482 + 24 = 1082`. P11 records 23 cold proof blocks and 26 reuse blocks; L03 records ten and three. This is a source/evidence inference consistent with existing reuse, not newly measured per-mesh misses.

| Geometry-stage category | P11 | L03 |
| --- | ---: | ---: |
| `independent_geometry_point` | 2,404 | 1,082 |
| `checkpoint` | 1,350 | 540 |
| `independent_bound_decode` | 766 | 310 |
| `independent_exact_add` | 737 | 298 |
| `independent_exact_mul` | 21 | 11 |
| Whole geometry stage | 5,559 | 2,342 |

Decode and addition categories also include site-radius work; none of these full pools is a measured saving for a proposed vertex screen. The stored binary32 arrays do not establish which source float64 candidates would pass a new componentwise-domination test. The source float64 arrays and incumbent-radius sequence are absent from the capture. An exact hit count needs a separate source-bound derivation or explicitly scoped observation after the design premise passes.

Sources: `docs/language-design/planar-reach-v0.1/libraries/reach-assets.ok` lines 10-39, 42-69 and 73-108; `reach-exterior.ok` lines 6-19 and 40-47; `reach-parts.ok` lines 9-39. Existing extrema reuse and scalar path: `ontokin/reach_conformance.py` lines 728-847.

## Retained plan membership and alias-screen limits

The snapshots retain `cache_identity`, `context`, `targets`, `remaining`, `registered_time`, and `node_paths`. Full node objects, stationarity flags, all body identity flags, and centered recipes are absent. These records must be called retained plans; membership alone does not prove that a full plan successfully prepared a centered form.

| Retained plan | Registration clock | Targets | Node paths |
| --- | --- | ---: | ---: |
| P11 full | 0 | 20 | 31 |
| P11 moving subset | 1/25 | 6 | 16 |
| L03 first full | 0 | 6 | 8 |
| L03 first moving subset | 2/87 | 3 | 7 |
| L03 next full | 2 | 6 | 8 |
| L03 next moving subset | 179/89 | 3 | 7 |

All exact ordered paths, context IDs and targets are in the derived JSON. Opaque IDs are retained process identities, not reusable source authority.

P11 moving targets are the head, both arm forearms and three eyes. L03 moving targets are the upper arm, forearm and tool. Failure locals preserve only the current node: P11's right-eye follow has a nonzero centered local vector; L03's forearm has a zero local vector but `identity_relative=false`.

The obvious source zero-offset identity nodes are arm pivots (`reach-parts.ok` lines 27-30), whose parents are stationary mounts in these requests. Moving hinges have zero child-site offsets but nonidentity relative orientations. Neck/base, eye, tool and hinge-tip offsets are nonzero. This is a topology argument relevant to the proposed strict nonstationary identity-alias screen, not an observed census of every centered node flag. The separate design reviewer must bind any final exclusion to exact source control flow and phase authority.

## Prior finite rejections

C060's isolated producer pi recurrence, C061's isolated axial setup reuse, and C062's identity-only/per-node ancestry descriptors remain closed under their stated assumptions. Their rejected scopes do not prohibit a different complete-request net-positive increment. Conversely, the 6,006/3,300 phase totals do not enlarge the bounded ancestry opportunity of 711/236.

## Verification boundary

The offline derivation checks the exact C061 archive SHA-256 `417bc250d0028671ffd62c328b67f345d26f2cbce03eec453aeb25644a598f43`, its ten parts, member inventory and every used member's length/hash. It checks named source files against frozen archive copies, C060/C061 complete category maps and key costs, segment cost equality, and C061 published setup ledgers against raw archived analyses. The output identifies all input hashes.

The derivation is not a new product test, a proof of source semantics, a measured optimization saving, a complete-request cost observation, or release acceptance. No complete source-plan flags or omitted float64 geometry arrays are fabricated.
