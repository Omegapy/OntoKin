# C061 collector provenance and accounting review

Date: 2026-10-28. Reviewer and new audit-tool author: `/root/handoff_integrity`.

## Disposition

The collector is suitable for the prescribed bounded control/capture round, subject to root's final independent review and exclusive execution. This is a static authorization to measure. It does not establish observation neutrality, product completion, an optimization saving or release acceptance. Those conclusions require the actual paired evidence and successful offline audit.

The starting source is C060 commit `00533b953ed345cbf5fa13eaa56aafa3a2f052a8`, with C061 declared on `work/reach-reader-setup-20261028-c061` in Issue #26 comment `6482986855`. Root owns source publication and subsequent execution. No product request, product import, numerical replay, test, archive operation, Git mutation or remote write was performed by this reviewer. Verification here was limited to source reading, static AST parsing and standard-library hashing.

This reviewer independently assessed the collector and existing C060 audit, then implemented the new C061 audit adapter at root's request. The adapter therefore requires the separate independent review assigned to `/root/c060_review` and root; this document is not an independent certification of the reviewer's own code.

## Frozen tool identities

| Tool | Bytes | SHA-256 |
| --- | ---: | --- |
| `tools/capture_reach_reader_setup.py` | 50,678 | `b90854f1a73053a3f9f9ebd7b67662d27b788f478a39a36cbc95abad2429183e` |
| `tools/audit_reach_reader_setup.py` | 41,586 | `ef322586e7693647f07f6901737611c82c844e2a6ed98578f499ac49bf994602` |
| `tools/audit_reach_recording_work.py` | 71,385 | `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf` |

The C060 auditor remains unchanged. Its exact SHA-256 is pinned in the new adapter before that dependency is loaded. The collector's final revision changes the documentation to say that collector-specific output is written after the request; the unchanged probe also writes its input inventory before compilation/export. That wording correction does not change behavior or line count.

## Collector review

The new collector retains the existing three C060 envelope wrappers and schemas for request, key, failure-local and raw-byte evidence. Eighteen additional named source functions are observed only during reader setup. The high-level functions invoke their saved originals once and forward the same positional/keyword objects. Low-level arithmetic, work charging, cache admission, native callback implementations and trace/profile hooks remain untouched.

Setup wrappers are installed after the existing reader-entry observation and restored before the first `_key_comparisons` call. Reader exit and final cleanup restore them again. Every restoration now records whether the installed function was the wrapper or the saved original before restoring it. The offline audit requires wrappers at first-key entry and originals at both later boundaries. Argument-object, work-owner, callback-owner and observer identities are retained per observed span. Native dispatch is checked before installation, at the first-key cutoff and after the request.

The complete `_verify_certificates` call remains unwrapped because it encloses later key execution and the eventual failure. Its pre-key work is retained in the unwrapped setup residual. All accepted setup spans must return before the cutoff; clipped spans and open stacks are rejected.

Observations use bounded detached native fields. Source and work cache counts are read without lookup, insertion or promotion. Typed operands preserve integer, rational, binary64, interval and sequence distinctions. The collector does not call source arithmetic or admission helpers merely to inspect state. A collector observation error invalidates the measurement and is retained; it does not authorize changing the original failure or continuing a failed request.

## Reuse of the C060 audit

The adapter loads the unchanged standard-library audit through its exact file path. It changes only `CAPTURE_PATH` to `tools/capture_reach_reader_setup.py`. The original three named wrapper functions remain the complete traceback-removal allowlist; generic setup frames are not silently removed. If setup instrumentation changes the original failure frontier, the old comparison rejects the pair.

All original audit stages run: source snapshot and commit/tree reconstruction; materialized-file and loaded-module checks; fixed original settings and limits; complete work maps and cache occupancy; diagnostic and exception identity; underlying frames, formatted traceback and causal graph; byte equality of all retained reader inputs; independent GLB/source census; complete prefix ledger; failure-local reconciliation; and actual command, executable, argv, output, raw exit status and log receipts.

Both auditor files are hashed and included in stable input receipts. The adapter, pinned C060 dependency, new collector and unchanged diagnostic probe must each be explicit materialized entries in the verified executed-source snapshot. Their descriptors are checked again. The audit refuses a dependency-hash mismatch, unstable input, foreign tool path or product-module import. All result files use fresh output paths and retain failed product status.

## Independent setup reconciliation

The new setup artifact must agree with the C060 capture on case, source commit/tree, driver bytes and actual argv. Its entry is compared with the original reader-entry work map. Its cutoff is compared with the first key's entry map, work cache occupancy, source-cache occupancy and source-cache categories. C060's `reference_pose:<kind>` categories are collapsed to the collector's `reference_pose` grouping before comparison.

Every span has an ID, parent, depth and distinct entry/exit events. The auditor replays the complete contiguous event sequence, verifies exact stack nesting and ordering, and rejects open, crossed, clipped, missing or repeated endpoints. This also distinguishes zero-charge siblings, where counter values alone cannot establish ordering. Exactly 4,096 completed spans are allowed; a disabled or over-limit collector is rejected.

Inclusive scalar deltas use shared operations, admitted Reach operations and the `checkpoint` category. Exclusive deltas subtract direct children only. All components must be nonnegative, preserve subset containment, and sum with the unwrapped residual to the original first-key setup interval. The auditor checks complete category maps in temporal order at every coarse boundary. Its disjoint top-level stages and intervening gaps telescope exactly to the full setup category map.

Nested structural spans contain only the three scalar counters. Their exclusive full category maps are explicitly unavailable. No per-function category map is invented from a generic `checkpoint` label or source expectations. Coarse inclusive categories are exact measured differences; nested inclusive/exclusive scalar costs are exact measured differences. These are separate report fields and must not be summed as if all were disjoint.

The target inventory is independently matched to the bound source AST, including module, qualified function, original file and code first line. The audit also validates typed phase/axial inputs and outputs, bounded rational and binary64 representations, source-reference/arithmetic ownership, and exact restoration sequence. Repeated input groups are descriptive. Process-local IDs, repeated vectors or matching results do not establish valid cache reuse, source authority or savings after admission, insertion and displacement costs.

## Execution boundary and remaining obligations

Only root may execute the four prescribed sequential product requests and the later offline audits. The source revision used for that round must already contain the frozen tools. No other worker should edit the checkout or run Agent, SQLite, product or archival work during that window. The proposed partial checkout must disclose every omitted tracked input; it is not the complete stock harness.

Passing the new audit will validate this pair's diagnostic and measured setup prefix only. It will not prove elapsed-time neutrality, an optimization opportunity, complete-request cost, a passed original recording or a release gate. Both original failures, retained unvalidated bytes, C035's held state and exact M1's rejection remain intact. Any proposed runtime change still needs a positive complete-cost argument, semantic review, bounded control/capture evidence and applicable existing tests.

The collector and adapter are frozen at the identities above. This worker has no running process and will pause all commands, edits and transfers after sending this review to root.
