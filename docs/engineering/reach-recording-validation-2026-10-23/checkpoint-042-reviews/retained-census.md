# C042 retained P23 constructor census

Reviewer: `/root/retained_census`. Date: October 26, 2026, America/Denver. Scope: read-only source inspection, exact retained-data recovery and count algebra. Parent C041: `b0ebdc318444ca97c729c11e0b29b19646096b34`, tree `a798a4c3f52f80e123fb54b65b3ac344bd8ea42b`.

No OntoKin module or archived driver was imported or executed. No product request, failed-tail continuation, new allowance, unit test, numerical replay, timing experiment or remote write belongs to this review. The local source copy is partial. The reviewer held the exclusive archive-read window for the selected recoveries, then released it to the coordinator.

## Finding

**The historical C020 trace supports a cold/warm constructor census that the prior summary did not extract. Its recording-sampling scope contains 62 cold noninverse constructors and 130 outer-cache hits, for 192 calls.** It contains no cold inverse constructor. The 62 noninverse constructors all miss the inner stationary-pose cache and all hit the normalized-rotation cache. Those counts are inferred from the exact source and complete scoped charge categories; they are not explicit hit/miss fields in the old log.

**The current retained C035 P23 request still lacks per-constructor cache attribution.** Its 103 request-wide `pose_stationary_check` occurrences give only a gross ceiling of 309 removable charges across completed eligible constructions in that failed prefix. They do not establish the actual eligible count, a positive saving after gates, the full original request cost or a recording pass.

## Exact evidence and source binding

The following retained observations were recovered as data from exact C041 archive parts. Every recovered part matches its Git blob and published SHA-256; every selected member matches its manifest length/SHA-256 and passes its ZIP CRC during reading. Required member spans were checked to lie wholly within recovered parts. Absent archive spans were zero-filled only for central-directory positioning and were never accepted as recovered member data. This was **not** a fresh whole-archive hash or all-member CRC verification.

| Observation | Source commit and tree | Exact retained member |
| --- | --- | --- |
| C020 constructor/sampling observer | `88473124cc058f7e2926a04d79ab38e340ab4407`; `02efa05c691ff31258e39c16b98044d2a47fda20` | `execution/p23-sampling-observer-001/P23.json`; SHA-256 `c147cc48d566a7b1b8781e757ed60e4bdf4cd08be8b54d52f7dda23d07d75a67` |
| Actual C020 observer code | Same observed source; driver is separately identified | `execution/p23-sampling-observer-001/executed-driver.py`; SHA-256 `bf13e4a04aa6f4d48917f129bfe5ec390ce15c37ea50f269736007b16d2d7ad0` |
| C035 original P23 failure | `4ca73909f861fe4bef9694787473621c1d21c140`; `87c949b238055af1ce368c694e1d5683c8aeacde` | `execution/original28-002/P23/request-result.json`; SHA-256 `fb0aac14420abe455e916997b640236574e2aca25b8d851e0dbcdbc4bb7ab5ed` |
| Complete C035 original28 report | Same held runtime | `execution/original28-002/report.json`; SHA-256 `aa95aeb40d91f106b84d1a166e146b93bcedf76d57b43871ff8461b132f89a77` |

C020 manifests and selected members are in `checkpoint-020-manifest.json` and archive parts 007/008. C035 members are in `checkpoint-035-manifest.json` and archive parts 007/014. Generic UTF-8 fetches rejected the initial binary requests; the supported `github_fetch_file` base64 option recovered the exact bytes. These acquisition failures and the resulting initial empty directory-read failures are retained separately in the recovery receipt. They are not product failures.

The C020 observer's before/after inventory is byte-identical, SHA-256 `991cf9d77d57aed7fa1c176268c47a83c24653d93b424b9fb29ff369b6eef996`. It preserves the earlier 37 omitted historical archives and does not establish complete release input closure. The C035 inventory is also byte-identical, SHA-256 `02bfe4d0e5b30993ff192a2350f670d5821502d14bee62aea37a0415d9672568`, covering 1,986 files / 442,072,108 bytes.

Exact historical runtime files were fetched at C020's known commit and verified against its actual input inventory. Current file hashes were verified against C035's inventory and the C041 tree. A separate recursive-tree comparison confirms that all 65 current `ontokin/` files have the same blob/mode identities as held `4ca73909`.

| File | C020 Git blob | C035/C041 Git blob | Applicability |
| --- | --- | --- | --- |
| `ontokin/reach_runtime.py` | `c6ef46f17b4cca8a13ba2cdff6483a7540b62f64` | `e7ccbb35c4f5aab7ff6431692bed80089fbf0cf0` | `_constant_pose` body is AST-identical; `_resolve_kinematics` differs. |
| `ontokin/reach_pose.py` | `d58dd633c052c53a201eb6bdb16dac68625b3961` | Same | Whole file is byte-identical, including `make`, `constant_pose`, `inverse_pose`, `_vector` and `_rotation`. |
| `ontokin/reach_numeric.py` | `f90908779ee43cda8806cba3892b0aa018618329` | `c552b085106a02b612a24a4884d8096f9733ee40` | `lookup` and `remember` bodies are AST-identical; `charge` differs. |
| `ontokin/reach_recording_fast.py` | `078d6292dca80c45cfefad64108e1e0844591c2a` | `c58d76692a79c1a1507a1185d1dfd15959de11cc` | `recording_float_excess` body is AST-identical; whole file differs. |

Matching helper bodies allow source interpretation of a historical measurement. They do not transfer historical invocation order, cache contents, hit rates, stage counts or costs to the changed current request.

## Historical cold/warm derivation

The observer records Python call/return events, scoped inclusive/self costs, and every `ReachExecutionWork.charge` category attributed to its nearest selected function. The `SELECTED` set includes `_constant_pose`, but not `make`, `_rotation`, `_vector`, `lookup`, `remember` or `inverse_pose`. Those constructor-internal charges therefore remain attributed to `_constant_pose`. Its scoped self and inclusive counts are equal. The retained report records no observer anomalies, no unreturned selected frames or work charges, matching original unobserved work/diagnostic/status/operation totals, and reconciled self totals.

The sampling row records:

| Charge category | Count |
| --- | ---: |
| `cache_lookup` | 316 |
| `cache_promote` | 192 |
| `pose_vector_domain` | 248 |
| `exact_decode` | 434 |
| `binary64_decode` | 434 |
| `pose_stationary_check` | 62 |
| `cache_insert` | 124 |
| `cache_evict` | 124 |
| **Total completed charges** | **1,934** |

These categories support the following source derivation for this observed native execution:

1. Each ordinary `make` reaches one stationarity charge; therefore 62 constructor executions reached that point. All returned normally in this scope: the request later refused during `recording_frames` position projection, outside `_constant_pose`, and every attributed constructor charge completed in both shared and reach counters.
2. Each call performs its outer lookup. Each constructor also looks up the normalized rotation and stationary pose. There is no `pose_rotation_reference` in this sampling row, so the make calls used raw quaternion inputs, not `RotationValue` inputs that would omit the rotation-cache lookup.
3. `316 - 192 - 62 - 62 = 0` leaves no inverse-result lookup. Thus there were zero cold inverse calls and 62 cold noninverse calls. The remaining `192 - 62 = 130` calls were outer-cache hits.
4. Zero quaternion-rescale categories imply all 62 normalized rotations were cache hits. Their 62 promotions plus 130 outer promotions account for all 192 promotions. No stationary-cache hit remains.
5. The 124 inserts and evictions reconcile as 62 stationary results plus 62 outer source-constant results. The 248 vector admissions and 434 exact/binary64 decodes independently reconcile as `4*62` and `7*62`.

The source constructor only offers three unconditional removable charges on each eligible cold construction. On this historical sampling sequence the gross target is **186**, before every added authority, guard, lookup, copy, retained entry, fallback and cleanup cost. It is not 576 from treating all 192 calls as cold, nor 1,934 from treating inclusive work as removable.

The same retained trace also permits this export-wide breakdown:

| Trace scope | Outer calls | Outer hits | Cold noninverse | Cold inverse | Stationary-cache hits | Stationary-cache misses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `advance:0:before` | 40 | 6 | 33 | 1 | 2 | 32 |
| `advance:0:after` | 3 | 3 | 0 | 0 | 0 | 0 |
| `advance:2:before` | 3 | 3 | 0 | 0 | 0 | 0 |
| `recording_sampling` | 192 | 130 | 62 | 0 | 0 | 62 |
| **Observed export total** | **238** | **142** | **95** | **1** | **2** | **94** |

For `advance:0:before`, the row contains 34 stationarity charges and 109 lookups. The equation `109 - 40 - 2*34 = 1` leaves one inverse-result lookup. The three conjugate and three position-negate units establish that inverse's calculation. There are 34 normalized-rotation hits, six outer hits and two stationary hits, reconciling 42 promotions. The 67 inserts are 34 outer, 32 stationary and one inverse result. This partition was independently checked by `/root/constructor_contract` against the actual observer and exact historical source.

The export trace starts after source construction; it is not a whole process call inventory. Its failed request remains at 100,001 shared / 80,033 completed reach operations. Its per-call retention threshold means individual cheap calls are not all saved, although scoped category totals are retained. No exact per-key temporal cache trace is claimed.

## Current retained P23 evidence

C035's original request preserves end `3`, integer fps `1`, helpers false, tolerances `0.001 m / 0.001 rad / 1e-6 s` and the unchanged 100,000-operation cap. It fails at **100,001 shared operations / 80,801 completed reach operations**. The actual traceback reaches:

`_sample_recording_nodes -> recording_frames -> _resolve_kinematics -> constant_pose -> _constant_pose -> work.lookup -> charge("cache_lookup") -> external_check`.

The external shared-budget check refuses before `lookup` reaches key membership. The refused call is therefore **unclassified**, not a recorded outer cache miss. The `cache_lookup=5,053` category counts completed lookups throughout the request and omits this refused reach charge; it cannot establish which lookup keys would have hit.

The raw work map has `pose_stationary_check=103`, `pose_vector_domain=1,137`, `cache_insert=1,219`, `cache_promote=4,190` and `cache_evict=768`. These counts combine planning, source observations, hinge/full-pose construction, sampling and multiple cache namespaces. They contain no caller/inverse/phase partition. A current cold/warm count cannot be obtained by substituting the historical 62 or by subtracting old planning totals from 103. The resolver and charge implementation changed, and the request fails at a different site.

For completed candidate-eligible constructions in this retained prefix, each offers at most one of the 103 recorded stationarity occurrences. Thus `m <= 103` and `3*m <= 309` is a conservative gross ceiling. It is not an equality, not the current sampling-only opportunity and not a complete-request ceiling after an optimization allows more work to run.

The exact missing datum is **current-source per-caller, per-cache-namespace constructor attribution**, including outer lookup hit/miss/refusal, the `inverse` argument, entry to `make`, inner normalized-rotation/stationary/inverse-cache hit/miss, and scope/phase. Current cache key or category totals alone do not reconstruct that information. A future diagnostic must be separately scoped, close the current source inputs, keep the untouched original P23 request/caps, execute exclusively, compare against the complete original failed control, and preserve every failure. This checkpoint does not schedule that replay.

## Larger distinct source-only target

The C020 trace also identifies `recording_float_excess`: 32 sampling calls and 960 attributed charges, comprising 32 domain admissions, 32 lookups, 320 adds, 448 multiplies, 64 comparisons, 32 inserts and 32 evictions. Its body is AST-identical to current source (historical lines 362–421; current lines 527–586). The current C035 map records 32 `recording_float_excess_domain` occurrences, but it does not supply the corresponding caller-attributed cost or key distribution.

This is a more substantial lead than the three-charge constructor target. A separate source-only review can examine factoring the repeated angular-envelope arithmetic from the position-dependent whole-result key, while preserving each caller's original source-bound admissions, exact arithmetic guards, comparison order, callbacks, cache/lifetime effects and first-failure semantics. Shared source structure alone does not establish repeated admitted keys. Current `(t,c,sq)` repetition and a complete positive charged bound remain unproved; no implementation or saving is selected here. The held P23 static-transfer route remains a separate rejected/held timing result.

## Review boundary

This review adds a source-derived historical census and a precise current evidence gap. It leaves C041's unconditional cache bypass and unchanged-key `RecordedTransform` substitution rejected. Original28 remains 24/28; P11/P16/P23/L03 remain capped; C035 remains held. All acceptance caps, fixtures, oracles, source schedules, independent predicates, compatibility/destination/Agent roles, release gates and the broader OntoKin goal are unchanged.
