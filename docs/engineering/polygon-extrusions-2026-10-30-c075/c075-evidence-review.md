# C075 independent final-evidence reconciliation

Reviewed 2026-10-30 by the independent `/root/extrusion_review` agent. This is a separate evidence review from `c075-review.md`, which covers the runtime and contract source.

## Result

**The completed acceptance, destination, and Agent schema evidence reconciles without an unresolved finding.** No product tests, exporter runs, or browser rendering were rerun for this review. The review used saved outputs, independent hashes and revision calculations, JSON schema revalidation, and a read-only SQLite connection.

The only concrete evidence item still outstanding at this review snapshot is the terminal result of `/tmp/c075-final-core`. At **2026-10-30T17:03:57.973373+00:00** its summary remained `running`, with `force-agent-tools` passed and the unit suite still executing. This record does not convert that running suite into a pass. The parent should reconcile the completed core summary and retained logs before claiming the final core/force-agent gate passed.

## Source binding

| Identity | Verified value |
|---|---|
| Candidate commit | `d3f0d69b953550b60b5eb0a0b41bc390ba934985` |
| Candidate tree | `ea880242abd9e323c1d80a46c2b01bdbd35a2aa8` |
| Package implementation digest | `sha256:c940ee62876a38e61cdd359cd46bb6849124e61788cdd710cf12edd9338ad19b` |
| Tracked source inventory | 3,979 files; 625,566,123 bytes |
| Acceptance canonical source inventory digest | `sha256:4c82b5161cf107c4a942ffea71976229bbc2934af8163fc6315478c8f4e8a5b1` |
| Completed-evidence binding digest | `ac3d54376aecfcae86957ff051b020dba2bb9ca9b3de16f158ec7d82083f3ab1` |

All three completed evidence summaries identify that same candidate. Acceptance and schema capture retained equal before/after inventories. Their path-keyed contents agree with each other, and this reviewer rehashed all 3,979 current files against them. The current repository is clean at the candidate. The implementation digest was independently recomputed from the package's Python files and matched the saved standalone receipts and Agent receipts.

The completed-evidence binding covers **135 files** across the three completed output directories. Exact paths, byte lengths, and SHA-256 hashes are in `c075-evidence-review.json`. The core summary is separately identified as an in-progress observation because it can change after this snapshot. Local acceptance metadata explicitly says `remote_head_verified: false`; this evidence review does not claim to have independently verified a remote ref.

## Counts and coverage

| Evidence | Reconciled result | What that count means |
|---|---|---|
| Frozen standalone cases | 28 | 10 delivered valid cases, 17 expected source/profile rejections, one source-valid binary32 delivery rejection |
| Acceptance assertions | 212 passed | Recorded assertions in the acceptance driver; not 212 independent source programs |
| Delivered GLBs | 12 | The 10 standalone successes plus generated reusable parts and the Agent-repaired assembly |
| Khronos validation | 12/12; zero errors and warnings | Every delivered GLB appears once with the matching bytes/hash |
| Native Three playback | 80 poses | Five times for each of the 16 total carrier occurrences across the 12 GLBs |
| Browser playback | 40 poses | Five times for eight carriers across four browser-selected GLBs |
| Rendered captures | 8 | Front and oblique views of concave bracket, placed bracket, generated parts, and repaired assembly |
| Actual acceptance exchanges | 57 | 57 request/response exchanges, including retries and deliberate rejections |
| Durable acceptance requests | 55 | One SQLite row per unique project/request identity |
| Acceptance response envelopes | 59 | Includes two additional nested target envelopes in cancel/status responses |
| Schema capture tests | 23 passed | Saved log confirms zero failures, errors, or skips |
| Schema observations | 306 | In-process `handle`/`submit` observations; repeated/intermediate observations are included |
| Schema response envelopes | 310 | Nested response envelopes included; all independently revalidated without errors |
| Schema request identities | 150 | Distinct service/project/request identities across 22 services |
| Schema payloads | 151 | Distinct service/payload pairs; includes a changed-payload retry |

All 12 advertised Agent operations occur in the schema observations. Ten observations contain intentionally schema-invalid requests, representing **five request identities**, and all were rejected. The saved summary identifies every one; none was silently counted as an accepted conforming request.

## Frozen inputs and standalone outcomes

The saved original and correction manifests match the candidate's manifest files. All original and corrected file bytes match their declared sizes and hashes. Every frozen case appears exactly once in the acceptance case list and has its own receipt. Source hashes and bundle program revisions were independently recomputed from the exact supplied fixture text and filenames.

For the ten valid standalone cases, each receipt's artifact hash and byte length match the actual GLB. Each negative case has a non-delivered receipt and no GLB. The binary32-collapse case specifically retains `achieved_level: evaluated` and a numerical-delivery failure; it is not described as invalid source or as successfully delivered. Every prescribed diagnostic code is present. All recorded operation counts agree with the corresponding receipts.

The additional generated and repaired bundle program revisions were independently recomputed, including the repaired assembly retaining the original entry filename and the unchanged pinned `parts.ok` module. All 12 GLBs have intact binary headers and decoded JSON metadata for schema `0.8`, profile `polygon-extrusion-0.1`, delivery contract `ontokin.glb/0.8`, and their expected program revisions.

## Agent transcript and durable store

The 57 individual exchange files exactly match the 57 ordered JSONL rows. Every saved request and every response envelope, including the nested cancel/status target receipts, independently satisfies the pinned `.8` schemas.

The durable database passes SQLite's read-only integrity check, identifies `ontokin.extrusion-program-agent-store/0.1`, and has a closed worker session. All 55 unique request identities have exactly one durable row. Each row's original canonical payload, SHA-256 digest, operation, state, and terminal receipt agree with the transcript or its nested target receipt. The request-state distribution is **51 succeeded, two rejected, one cancelled, and one failed**.

The intentional negative exchanges are fully accounted for:

1. Exchange 6 rejects the invalid vertex edit; its candidate source remains retained with `accepted_once = 0`.
2. Exchange 9 rejects a cursor from the old revision.
3. Exchange 12 rejects a changed payload reusing `c075-10`. The original evaluation at exchange 10 and its identical retry at exchange 11 have equal receipts and share one durable row. These two extra exchanges explain 57 exchanges versus 55 durable requests.
4. Exchange 57 fails the artifact request under the current lower host ceiling, with the expected `host_ceiling_exceeded` reason.

Exchange 54 initially queues validation; the later cancel/status responses and persisted request agree on terminal cancellation before work. That queued observation is not treated as completed execution.

The source table contains exactly the frozen original assembly, the deliberately invalid candidate, and the exact frozen repaired assembly. Their bundle revisions independently match the stored keys. Only the original and repaired revisions have accepted-source identity records; the final accepted revision is the repair. Three durable runs correspond to evaluation through one second, export through one second, and reset to zero. All bind to the repaired source and the same implementation, without candidate-only or failure markers.

There is exactly one durable artifact. Its data is byte-for-byte equal to `agent-repaired.glb`; the ID, SHA-256, program revision, and length agree with the published export response. The **39 successful retrieved chunks** have contiguous offsets and correct next offsets, revision, and digest, and concatenate to those exact bytes. The failed lower-authority retrieval is separately retained and contributes no artifact chunk. The export receipt records 8,915 operations, agreeing with the acceptance summary.

## Destination and visual evidence

The destination suite has exactly the same 12 artifacts as acceptance. Every GLB size/hash and every expectation-sidecar hash matches. Every artifact's Khronos record has zero errors and warnings, and no error/warning is concealed in its message list. The checker hash matches the candidate's `tools/verify_extrusion_glb.mjs`.

For each native and browser observation set, the carrier/time pairs are complete and unique. Saved translations independently agree with the frozen origin-plus-velocity expectations at 0, 0.25, 0.5, 0.75, and 1 second, and saved carrier quaternions agree with the identity rotations in these fixtures. Browser reports have no page errors or failed requests.

All eight expected PNG files exist, have intact 1100 by 780 PNG headers, and match the hashes in the browser reports. Their recorded framing values are within the viewport. The separate `visual-review.json` identifies the same source candidate, binds the exact destination summary hash, and attests that the root assistant actually opened each matching image, with a passing observation, view, and time. This reviewer reconciled those bytes and attestations and **did not independently open the eight final images**.

The destination summary's original `pending_actual_image_inspection` fields are preserved as the state at the end of automatic rendering. The later, explicitly bound visual-review record supplies the completed actual inspection. This is an auditable two-stage record, not a concealed unfinished visual review.

## Scope and reviewer notes

The completed evidence supports the selected experimental C075 polygon-extrusion behavior and its recorded rigid-animation delivery. Both acceptance and destination summaries retain `release_acceptance: false`. Neither the reviewed outputs nor this report certify whole-product conformance, release readiness, live destination physics, or Unreal Engine import.

The independent reconciliation recorded 1,144 consistency checks, with none failing in the final record. These are evidence checks and must not be added to product test counts.

A preliminary reviewer comparison treated two source inventories as ordered lists. Their producers use different path ordering, so that comparison initially reported a mismatch. Comparing by path established identical files, lengths, and hashes with no source change. The preliminary record is retained as `c075-evidence-review-preliminary.json`; the final script and JSON explicitly describe this reviewer correction. It is not a product or evidence failure.

No optional expanded testing is requested. Complete and reconcile the already running core/force-agent gate, then retain these completed artifacts and their identities with the final handoff.
