# C071 integration preparation: signed merge identity

PR #69 merged successfully as actual commit `1a3f13beda56dd94e5aa53d06d1ea5083a183307`, tree `34f984a43ca41cfec1aa443cb2d67fa1e728eb94`, with ordered parents `[b881f319f3602d94db90e252ded24fd64b256b36, f1a1bb41b0000453d9bf8d3371c35f9c529b519f]`. The remote merge result was not changed during this local recovery.

The initial local identity helper handled unsigned commits only. The actual GitHub merge was signed, so reconstruction from unsigned author/date/message metadata failed its Git SHA-1 assertion. A subsequent local main-ref update rejected the unavailable commit object. The documentation wrapper then rejected staged STATUS before invoking its preservation checker. These were local preparation failures, not a failed product request or failed documentation-checker execution.

The original helper, failure summary and observed command sequence are retained under [integration-preparation/merge-materialization-001](integration-preparation/merge-materialization-001/). The [corrected helper](integration-preparation/install_commit.py) uses the exact API-provided signature and unsigned payload to construct candidate raw commit bodies and accepts one only when its Git SHA-1 equals the actual remote commit. It preserves signature continuation bytes and the payload's original timezone bytes. No synthetic snapshot identity or changed expected hash is used.

The corrected raw signed body is 1,270 bytes and hashes to the actual merge. The local tree is independently reconstructed from the candidate plus the exact leased STATUS bytes, and matches the actual merge tree. Its only candidate difference is STATUS. The local main ref was then set to the verified actual merge, with a clean source state.

Only after that recovery did the unchanged checker execute for the resulting-merge role. It passed on all 3,791 stable tracked inputs, with 29 preserved sources, 233 sections, 355 documents, 2,370 local links, 94 anchors and zero failures. The [integration record](integration.json) binds that actual command and its streams. No product import, request, suite, native trigonometry, mesh generation or hosted job occurred.
