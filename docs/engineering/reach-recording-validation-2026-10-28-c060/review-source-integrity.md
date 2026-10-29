# C060 independent source and evidence integrity review

Date: October 28, 2026.

Reviewer scope: independent source, Git-object, command-receipt, JSON, file-hash and GLB-container inspection. The reviewer did not execute OntoKin, product requests, tests or collectors. The reviewer previously inspected source recovery and the proposed diagnostic tools and recommended input-closure and evidence-recording improvements; the reviewer did not author those tools or execute the four product requests. This is a source/evidence integrity review, not independent numerical or destination acceptance.

## Disposition

**Passed within the named source and evidence integrity scope.** The retained evidence establishes four failed requests, comprising a control and capture for each of original P11 and L03, on the identified C060 diagnostic candidate. Each pair retains identical original inputs, operation totals, complete reach work maps, resource diagnostic, underlying exception graph and reader bytes. No discrepancy was found in this review's scope.

The evidence root reviewed was `.evidence/c060-attempt001/`, with command receipts and raw streams under `commands/`, controls under `{P11,L03}/control/`, and captures under `{P11,L03}/capture/`. The attempt directory contained 40 evidence files at the reviewed point. Any later publication or packaging must identify its own containing commit and archive identities; this review does not invent those future identities.

## Exact source identities

| Identity | Reviewed value |
| --- | --- |
| Original main commit | `b37b39102aea67eb81bd9e38518352403a844e99` |
| Original main tree | `f556cd0e1eebe071a5354809425224e82b299bfd` |
| Executed C060 diagnostic candidate | `5170bb99bfb045c651e1aabb1ac5f24c9d2259dc` |
| Executed candidate tree | `ed848bced2c9f8cf4027ffd278b6bf9e0be606e6` |
| Candidate parent | `b37b39102aea67eb81bd9e38518352403a844e99` |

The exact bytes retained in `.recovery/candidate-commit.raw` hash to the executed candidate SHA and match the stored Git commit object. Its complete tree changes no original tracked path and adds exactly these two files:

- `tools/probe_reach_recording_work.py`
- `tools/capture_reach_recording_work.py`

All 65 runtime files retain their original-main blob identities. The four executions each record 36 loaded OntoKin modules. Their module names, source paths, byte lengths and SHA-256 hashes agree exactly between control and capture. The additional named import of `tools.probe_reach_recording_work` in the capture accounts for its different total recorded module count: 37 for each control and 38 for each capture. The control executes the probe as `__main__`.

The original recovery's recursive remote tree was not truncated. The reviewer independently reconstructed all 313 tree objects, including the root, and hash-verified the actual main commit and all stored tree/commit objects. The original index represented all 3,327 main-tree blobs. The local history was explicitly shallow; no synthetic source commit was substituted.

## Input stability and materialization at execution

All eight before/after input snapshots are recursively type-sensitively identical. Each records:

| Property | Exact value |
| --- | ---: |
| Materialized tracked files | 488 |
| Materialized bytes | 9,364,004 |
| Explicit omitted tracked paths | 2,841 |
| Total candidate tracked paths | 3,329 |

The 488 materialized files comprise 486 unchanged original-source files and the two committed diagnostic tools. The reviewer checked their actual lengths, SHA-256 values, Git blob identities and file modes against the candidate tree. The present and omitted inventories form an exact disjoint partition of that tree. At the time of this review, the omitted files were physically absent. These counts describe the execution and review snapshots; later documentation hydration does not retrospectively change them.

Every source input needed by the observed P11/L03 requests was present, including all runtime modules, the case manifests and four source units per case, frozen acceptance records, the numerical derivation files and `tools/reach_destination.mjs`. Independent static inspection closed the 17 literal inputs of `reach_pose.source_numeric_basis`, the 19 of `reach_conformance.verify_numeric_bases`, and the two of `reach_export.destination_numeric_basis`.

Before execution, the reviewer independently reconstructed the original bundle identities from exact source bytes and manifest metadata without importing OntoKin:

| Case | Source bytes across four units | Program revision |
| --- | ---: | --- |
| P11 | 11,597 | `sha256:7ee1fca89536d3618b0a9a39e39ea2286be9973ce14ae148d7d8806d973ff000` |
| L03 | 11,642 | `sha256:0d8e38f49425cf9a0e9b96f8aadb42d7baf1743208e152aaea8f2d58f759abc7` |

Both match the frozen acceptance records. The recorded request identities retain those values.

This establishes materialized-input stability on the declared partial checkout. It does not establish a full checkout or the stock harness's all-tracked-file input gate. The reports correctly retain `complete_checkout=false` and `complete_stock_harness=false`.

## Actual command provenance

All four command receipts and all eight raw stdout/stderr streams pass independent length and hash verification. The command intervals are serial and nonoverlapping. Every receipt records exit 1, `timed_out=false`, and empty stderr. Each report's time interval lies inside its corresponding command interval.

The recorded executable is `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3`, CPython 3.12.14, on `Linux-6.18.55-x86_64-with-glibc2.39`. The outer receipts retain the `-B` interpreter flag.

| Request | UTC process interval | Process elapsed seconds | Request elapsed seconds | Exit | stdout bytes | stderr bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| P11 control | 21:30:55.898215–21:30:58.924374 | 3.026156757 | 2.306479777 | 1 | 39 | 0 |
| P11 capture | 21:31:03.253603–21:31:06.680579 | 3.426973362 | 2.362017321 | 1 | 210 | 0 |
| L03 control | 21:31:18.073041–21:31:21.605645 | 3.532600119 | 2.859430527 | 1 | 39 | 0 |
| L03 capture | 21:31:30.896047–21:31:35.326276 | 4.430230143 | 2.663523416 | 1 | 211 | 0 |

All intervals are on October 28, 2026. Recorded process and request durations measure different boundaries and must not be conflated.

The embedded `report.command` omits `-B` because it is constructed from `sys.argv`. The outer command receipt supplies the complete invocation. The remaining command elements agree exactly. This representation difference does not indicate a different product request.

These records demonstrate serial execution of the four named commands. This review does not independently infer the state of unrelated processes from the absence of overlapping timestamps.

## Paired failure and work identity

Fifteen structured fields per pair were compared using recursive type-sensitive equality. They include case/status, source files, program revision, original options, maximum operations, source manifest, after-construction work, diagnostic, shared operations, the complete reach work object, construction/work limits, source units and accepted-artifact status. Type-sensitive comparison avoids treating integers, floating-point values and booleans as interchangeable.

| Observed result | P11 | L03 |
| --- | ---: | ---: |
| Shared operations, both arms | 100,001 | 100,001 |
| Reach operations, both arms | 93,277 | 95,767 |
| Reach category count | 279 | 288 |
| Sum of category values | 93,277 | 95,767 |
| Work-cache occupancy | 256 | 256 |
| Control traceback frames | 23 | 27 |
| Capture traceback frames | 25 | 29 |
| Captured key calls | 37 | 154 |
| Final key index, zero-based | 36 | 153 |
| Final key time | `36/25` | `244/89` |
| Observation errors | 0 | 0 |

Both pairs retain exact failure type `OntoKinError`, message `Construction exceeded max_operations.`, diagnostic code `OKL-E-RESOURCE`, original limit 100,000, consumed value 100,001, and profile `planar-reach-0.1`.

All construction limits agree between arms: 1,000 objects, 100,000 operations, 1,000 result items, 30,000 milliseconds and 100,000 source-value entries. All recorded work limits agree: 100,000 operations, 30,000 milliseconds, 32,768 operand bits and 256 numerical-cache entries. Fixture horizons, float fps 1.0, helpers=false, tolerances and frozen source revisions remain identical.

Both exception graphs contain one node, with null cause and context and `suppress_context=false`. The full graph and ordered underlying frames match after removing exactly these capture frames at their recorded locations:

- `tools/capture_reach_recording_work.py`, line 326, `capture_validate_export`.
- `tools/capture_reach_recording_work.py`, line 374, `capture_key_comparisons`.

No additional frame normalization was needed. All 19 capture-level identity checks per case and all ten checks on every captured key call are true. These are evidence/identity checks, not runtime-test counts.

The final refused shared charge precedes admission to the reach counter. Shared-versus-reach differences must not be recast as an independently observed construction-category map.

## Retained GLB identity and container checks

For each case, three copies agree byte for byte: the control's retained reader input, the capture diagnostic's retained reader input, and the collector's retained reader input.

| Case | Bytes | SHA-256 |
| --- | ---: | --- |
| P11 | 1,799,228 | `4ea1d4d90fd1942aa8a793892dfe1a72f7ae047b5725f9750ab5c7b330477c3d` |
| L03 | 1,657,840 | `12f78939fd6fb5e8a6dace1ed4469c4da90ae3e56a8f0e21dd2e73947ae567e5` |

Those hashes also match the historical C033 retained-byte identities. GLB magic, version 2, declared total byte length, chunk boundaries and exact final byte position were checked independently.

- P11 has a 1,652,848-byte JSON chunk and a 146,352-byte binary chunk.
- L03 has a 1,586,756-byte JSON chunk and a 71,056-byte binary chunk.

These checks establish byte equality and container integrity. They do not establish accepted source poses, independent numerical validity or successful delivery. Both requests failed, and all retained GLBs remain **unvalidated reader input**.

## Qualifications and unexecuted gates

The supported conclusion is that the capture preserves the observed operation totals, complete category maps, exact failure route, original inputs and reader bytes for these two requests on the identified candidate.

The probe observes `reach_work.record()` after construction and before export. The capture also performs pre-imports and passive boundary observations. The paired runs therefore establish no elapsed-time neutrality or performance benefit. A single pair cannot be treated as a timing benchmark, including where the capture happened to report a shorter request duration.

This review does not establish a successful P11 or L03 export, an original28 rerun, full regression tests, a complete checkout, the complete stock source-delivery harness, CPython 3.11/3.13 compatibility, independent pose acceptance, native destination playback, browser/visual validation, or any finite release gate. It does not establish the cost or success of an unvisited failed tail. No allowance was reset by this reviewer, and no product execution was performed as part of this review.

The detailed census auditor may build on these provenance checks. Runtime optimization and original recording completion remain unproved. Historical failures and all current limits retain their meanings.
