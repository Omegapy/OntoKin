# Independent A08 artifact-loop auditor review

Reviewer: runtime agent, independent of the interface implementation and auditor author.

The listed offline auditor scope passes at commit `f95b9d29abb514bdd167d8d9fdc717d25224097d`. The reviewed file is `tools/audit_torque_artifact_loop.py`, SHA-256 `f682f7afb17691b5f3413bf219fd56aab412da70ed5dc82a40b68dce486b7383`. The companion JSON binds 15 review findings, exact preserved witnesses, the complete historical control and the explicitly incomplete capacity control.

## What the auditor establishes

The tool imports only the Python standard library. It does not use the product service, cache, producer or independent numerical reader as its authority. It admits the exact original freeze manifest and derives the A08 source closure from the frozen workflow, file manifest, entry, imported module and PNG. Those original bytes determine the program revision independently.

It requires an actual closed SQLite database, rejects unapplied WAL or journal bytes, checks database integrity and opens the file in immutable read-only mode. It compares accepted source and committed project/run identities, the complete artifact BLOB and its digest, the report and the recorded implementation. It then walks the original gzip transcript and the actual durable request table in lockstep. Every transcript exchange must have exactly one ordered durable row with the same request identity, canonical payload, payload hash and complete canonical response serialization. The engine on every stored request and the committed run implementation must agree with the artifact producer. The tool rejects extra durable rows and extra workflow requests.

For every artifact or PNG request, it reconstructs the exact frozen materialized request and compares every decoded returned byte with the actual stored artifact or frozen asset range. It checks exact offsets, lengths, next offsets, truncation flags and full artifact/source identity. A complete result requires all artifact chunks, successful exact EOF, the prescribed past-EOF refusal and every original PNG chunk. The explicit prefix mode does not manufacture missing requests: its `complete_frozen_loop` field stays false.

The final receipt binds the original database hash and size, compressed and uncompressed transcript hashes and sizes, canonical request/response chain hashes, source closure, report/run data and implementation identity. Original database and transcript bytes are hashed again after observation. The auditor is an independent receipt reconciliation; it is not a second torque physics proof or an independent meter of every production primitive.

## Findings and correction

The original auditor accepted nine coherent invalid variants in an independent bounded matrix. Each variant changed the raw transcript and matching durable serialization/digest consistently where relevant, so simple row/transcript equality could not detect it. The accepted variants were a Boolean request max_bytes, foreign stored engine, negative consumed work, negative elapsed time, Boolean returned offset, Boolean next offset, integer truncation flag, floating-point budget limit and Boolean recorded chunk size.

The review also found that iteration over a gzip stream allocated a complete arbitrarily long line before enforcing the intended 8 MiB record limit. The old tool rejected the oversized witness eventually, but its read itself was not bounded.

Commit f95b9d2 corrects these specific admissions. Exact frozen requests and allocation dictionaries are compared through canonical JSON, preserving numeric types. Required sizes, indices, offsets, next offsets and consumed work are native nonnegative bounded integers; booleans do not qualify. Truncation is an actual Boolean. Elapsed time is finite and nonnegative, original clocks are finite, and the original deadline interval is checked. Stored engines and run implementation are bound to producer identity. Gzip input now uses `readline(8 MiB + 1)` before decoding, and rejects an over-limit or incomplete record immediately.

## Actual independent replay

All 11 cases in the committed independent driver passed against the corrected tool: the unchanged control succeeded; the nine formerly accepted invalid records were rejected; and the oversized line was rejected with a bounded read. More strongly, the corrected tool was then run against the exact preserved before-case input files, without recreating or editing them. Every database and transcript hash remained unchanged. Each invalid case failed at its intended number, frozen-request, provenance or bounded-line predicate, not at an unrelated setup condition. Those literal before/after outcomes are retained in `a08-auditor-preserved-witnesses-after02/results.json`.

An independent complete historical A08 control with 65,536-byte chunks passed 1,221 checks over 48 original exchanges. It covered the entire 2,447,148-byte artifact in 38 chunk reads, exact EOF, the past-EOF refusal and six PNG reads covering 89 bytes. This control is explicitly bound to its historical implementation, not the proposed final integrated source.

The actual 10,000 one-byte capacity measurement was separately reconciled: all 10,002 setup/read exchanges passed 250,075 checks. Its receipt correctly reports `complete_frozen_loop: false`, 10,000 retrieved artifact bytes, no EOF/past-EOF and no PNG reads. Its producer package hash is `249da76c6d411587be3bd2abc0ac944fabfe131be5a89da7e5f968ee632011a4`. Audit success does not turn that prefix into a completed A08 loop.

Two preparation failures remain retained. The earlier independent mutation harness left a SQLite connection open and therefore hit the correct WAL refusal before reaching intended mutations; the corrected before matrix explicitly closes each copy. One initial preserved-witness replay script had a syntax error before it invoked the auditor or read inputs; the next attempt contains the actual exact-input results. Neither failed preparation is counted as successful verification.

## Handoff and claim boundary

The auditor reads and hashes a real closed SQLite file. It does not reconstruct the original physical database from the transcript. If a handoff omits a large successful original database, that omission must be explicit, with the original database hash, full original transcript, retrieved artifact, source closure, report/run metadata and this audit receipt retained. A transcript may allow semantic replay; it is not evidence that an absent byte-identical physical database can be recovered.

This review approves the listed auditor bytes for the stated checks. It does not approve a final integrated release, complete a one-byte workflow that has not been executed, resolve the canonical-history numerical blocker, or replace fresh receipts for future implementation bytes.
