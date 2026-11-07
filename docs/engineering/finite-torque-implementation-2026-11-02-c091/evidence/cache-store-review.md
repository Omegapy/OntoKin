# Independent review of .22 artifact proof ownership and store reuse

## Result and binding

The reviewed cache/store scope passes against interface commit `8594a3875f405c1a78a588ba534a9b8fda9ed738`, package SHA-256 `249da76c6d411587be3bd2abc0ac944fabfe131be5a89da7e5f968ee632011a4`. The companion JSON lists exact hashes for all reviewed modules and retained evidence. The reviewer implemented torque runtime work, not these interface/cache changes.

This is a bounded component review. It does not approve the final integrated numerical reader or the full torque release. The interface pin predates some integrated source-basis entries and later runtime guards. Those release checks require the final integrated source. The current source-only projection callback-identity finding is recorded separately and remains pending its own fix/replay.

## Why the proof reuse is sound in the reviewed scope

Every artifact request still reads current source authority, current provenance metadata and all current SQLite artifact bytes. A successful previous native immutable tuple is useful only if its project, artifact ID and complete byte string match the current request and current database row. Equality of the complete immutable byte strings permits reuse of their SHA-256 result. The current stored digest and content-derived artifact ID must also match. A changed byte anywhere, including outside the requested slice, forces the original full hashing path and refuses when it no longer matches the retained identity.

The proof is not a source-authority or database-version cache. Reopen and peer-service updates receive current admission. The retained digest never substitutes for current source, report, source revision, implementation or metadata checks. Exactly one bounded proof is retained per live service. Both byte equality hits and full hashing misses retain the same original integrity and slice ledger charges and callbacks.

The earlier frozen dataclass allowed in-place slot poisoning through `object.__setattr__`. Its replacement by an immutable tuple fixed that particular mutation, but a whole native tuple could still be assigned to the callback-visible service field. Both failures were independently reproduced using an actually accepted artifact, the original Agent callback and exact current SQLite bytes. Those failures remain in the evidence.

The reviewed fix makes that service field observation-only. The module owns publication in a weak-key map under a native lock. Ordinary `setattr` and `object.__setattr__` at integrity, publication and discover-publication callbacks cannot replace the proof. Close first fences the store, then clears under the same lock used by the publisher; an in-flight publisher cannot repopulate the proof after completed close. This is an ordinary native field/provenance protection, not a claim that arbitrary modification of the Python process or module code is sandboxed.

## Connection reuse and transaction behavior

The .22 store keeps one idle autocommit SQLite connection with a fixed 8 MiB SQLite cache. A native lock protects exclusive checkout. It is released before any query, callback or transaction. Nested and overlapping contexts use inherited fresh connections rather than waiting on their own active request. Existing commit/rollback boundaries remain authoritative; a caller leaving an unfinished explicit transaction receives the same rollback that closing the former fresh connection caused.

Close fences the inherited store before clearing its idle connection. A borrowed connection is closed when its borrower returns, so close does not invalidate a connection still in use by another thread. Actual interleaved and concurrent service requests exercise current commit visibility, authority revocation, nested context behavior and deferred close. Predecessor service/store selection remains separate.

## Actual independent checks

The independent driver in `tools/review_torque_cache_ownership.py` used a read-only backup of the actual closed A08 capacity08 store and an isolated exact 8594a38 package. It completed 41 checks across 19 real request/response exchanges. All six setter/stage replacement combinations refused the assignment; each changed final SQLite byte was rejected; immutable tuple slot mutation refused; restored current bytes succeeded; completed close cleared the proof. Full requests, responses and before/after package hashes are retained in `cache-owner-after-probe02`.

All 13 interface artifact/store test methods were independently replayed on that same isolated package and passed in 21.057 seconds. The real seed create/export used the unchanged 1,000,000-operation and 30,000-ms allocation. These methods cover original complete charge/callback trace equality, current authority and metadata, full-byte corruption, rollback, original exception identity, nested/concurrent connections and actual close/publication races. Sixteen source/JSON methods also passed on the same source pin; that separate source coverage does not erase the subsequently reproduced source-only equality defect.

The first custom after-probe searched only the diagnostic list while the correct refusal was in `protocol_error`; its retained result already shows correct rejection. It is classified as a review harness error, followed by a fresh successful replay. Two unit setup attempts lacked source-basis files in the sparse checkout. Their failures remain; exact committed documentation/destination files were restored without modifying product bytes, and the succeeding run is separate.

The 10,000-request capacity receipt is explicitly incomplete. Neither this review nor that measurement claims the remaining one-byte reads or final EOF requests were executed.
