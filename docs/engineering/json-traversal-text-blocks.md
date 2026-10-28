# Bounded JSON text blocks across container boundaries

## Redundant work

The JSON preflight already checks short immutable strings in blocks of at most
64 strings, each at most 128 Unicode code points. Its previous iterator frame
retained a separate pending block at every nesting depth. Closing a child
merged its block into its parent's; when the combined blocks exceeded 64, the
parent was flushed early. Repeated nested certificate objects consequently
triggered many partially filled literal scans. The fresh P09 baseline records
2,706 literal scans and their corresponding return checkpoints across the
complete request before its operation cap is reached.

The change retains one pending block for the current traversal. Containers
still retain their own iterators, depth and cycle identities. Their already
admitted short keys and string values enter the same bounded block. It is
flushed at 64 strings, before an unbatched long string, or when the traversal
ends. The same literal and escaped-string arithmetic is performed on fewer,
more complete blocks; no scan is performed without its original charged
domain/return checks. No existing work is refunded or relabeled.

## Escaped groups and the first measured candidate

The first traversal-wide candidate, implementation
`d58813875d6e25ed557b0ac3c2d3aca7818f7e4e`, retained the earlier escaped-string
size cache. The preserved `full-json-traversal-001` recording run was still
23/28 under the unchanged 100,000-operation limit. Both that run and
`full-p23-integrated-001` on `e238c9e2928a1e08071b8c134263f4b9a87fb60c`
reported stable inputs. They expose a real grouping regression:

| Observed work | Earlier grouping on `e238c9e2` | Traversal grouping on `d5881387` |
| --- | ---: | ---: |
| P11 total text blocks | 2,618 | 1,858 |
| P11 escaped-block native encodings / misses | 238 | 1,604 |
| P11 escaped-block hits, derived from block and encode counters | 1,968 | 2 |
| P11 independent key poses reached before failure | 380 | 320 |
| P13 total text blocks | 2,146 | 1,526 |
| P13 escaped-block native encodings / misses | 213 | 836 |
| P13 escaped-block hits, derived from block and encode counters | 1,677 | 532 |
| P13 completed operations | 68,051 | 68,158 |

The cache key included every short string in its block. Quoted carrier paths,
such as `rig.arms["left"]` or `rig.arms["first"]`, force a mixed block through
escaped handling. The new boundaries mix those paths with changing literal
clock strings. Larger blocks remove partial scans but destroy much of the
old reuse. In P13, all non-JSON and non-cache counters are identical. Its 623
extra misses add 2,492 encode/return/insert/evict charges; the other changed
JSON/cache counters save 2,385, explaining the measured 107-operation increase.
P11 reaches fewer numerical comparisons because the text preflight consumes
more of the same request budget. This is not a new numerical-kernel result.

Those two source cuts also differ in P23 source-seed work. Their P23 results
cannot be attributed to the JSON change alone.

## Fresh bounded escaped sizes

The correction keeps the traversal buffer and literal scan but removes the
escaped-size lookup and insertion. A successful escaped-size cache hit charged
domain, lookup and promotion: three operations. Fresh encoding charges domain,
native encode and encode return: also three operations. A miss additionally
inserts and, when full, evicts; retaining these sizes cannot reduce the charged
work relative to fresh bounded encoding. The correction eliminates that actual
cache work instead of changing the charge for any operation that still occurs.

Every escaped block now executes the same native encoder on its actual current
strings. Both encoder callbacks remain, as do the earlier domain callback and
logical-entry checks. The original work-owner admission is unchanged. No JSON
size entry is read, promoted or published, so successful text preflight leaves
the request's numerical cache values, order and capacity untouched. Cache work
explicitly performed by a user callback remains the callback's own work.

At a full cache, omitting the three extra miss charges would save 4,812
operations for P11's 1,604 observed misses and 2,508 for P13's 836 observed
misses relative to `d5881387`. These are charge-model projections, not new
measurements. Fresh encoding replaces two old P11 hits and 532 P13 hits with
bounded encoder calls; elapsed time and downstream cache effects still require
actual execution. Those projections are followed by the separately identified executed results
below; no additional passing recording is claimed.

## Exact byte and resource meaning

Compact JSON size is the sum of container punctuation, numeric/null/Boolean
representations and each quoted string's UTF-8 representation. Container
punctuation and every scalar value retain the original walk. A string's
encoded size does not depend on its container or nesting depth. Therefore
regrouping those exact immutable strings preserves the final size. Repeated
occurrences remain separate block entries, including shared containers.

The pending buffer never exceeds the existing 64-string limit; its maximum
literal join remains 8,192 characters. Escaping still uses the existing bounded
native encoder, with its exact UTF-8 checks and worst-case size. The walker
retains fewer string references than the former per-depth blocks. There is no
additional cache, retained source value, output-format change, or altered
byte/entry/depth, numerical-cache, operand or operation cap.

Every original value, key type, nonfinite number, integer width, container
type, cycle, logical occurrence and depth check remains in place. The original
logical-entry cancellation check still runs every 128 visited values. Text
block callbacks and the same shared work object remain authoritative; their
exceptions retain identity. Moving a block boundary can change the point at
which a failed request reports a byte overrun or cancellation. For inputs with
multiple defects, it can also change which diagnostic appears first: for
example, a later invalid value may be visited before an earlier pending string
is scanned. Every such input still fails; an oversized encoding cannot pass.
No byte-limit result is returned until the final
pending block has been admitted and counted.

Nested measurements have their own local block. Unsupported/custom values
cannot use the block to bypass the ordinary exact-built-in type checks. The
unchanged no-work path continues its ordinary per-string scan.

## Verification obligations

Dedicated tests compare actual UTF-8 encoder lengths and logical occurrence
counts across nested records, long strings, empty containers, escaping,
Unicode, repeated shared values, exact byte/entry/depth boundaries, changed
values, cycles, nested measurement and cancellation. The previous assertion
that two repeated escaped blocks invoke the native encoder once is explicitly
replaced with two invocations. Cancellation is checked at domain, encode and
encode-return callbacks rather than using an eliminated cache lookup as a
proxy; pre-encode cancellation still permits zero native calls, and return
cancellation sees exactly one. Pre-existing numeric entries must retain their
values, object identities, order and cache generation with capacities 1, 2 and
256. The actual GLB byte/clock and changed-invalid-metadata reader tests remain
unchanged. Existing JSON
limit/literal/reuse, recording-budget and relevant GLB reader tests must pass.
Full original recording executions measure the actual effect. These focused
and development executions do not establish complete release acceptance.


## Executed development result

Candidate `6ff69cb18b422b5db1d0c74cdd317fc0a40cc53a` (tree
`992577beff5c152d447c020034f5a7399d0192da`) passed **47/47** focused methods
on CPython 3.12.14 with no failures, errors or skips, followed by the complete
original source suite at **23/28**. Both runs retained stable input identities.
All 23 successful GLBs are byte-for-byte identical to the earlier `d5881387`
JSON candidate, including their JSON and binary chunks. The first comparison
script incorrectly assumed every implementation hash would change; its
failed attempt is retained separately from the corrected complete comparison.

P13 uses **65,650** operations, exactly 2,508 fewer than `d5881387` and 2,401
fewer than the preceding integrated `e238c9e2`. P20 uses **83,693**, saving
2,637 versus that integrated cut. Every successful case has a lower total
than `e238c9e2`; the smallest reduction is 112. P11 reaches 480 independent
key-pose checks and 448 certificate members, compared with 320/280 on the
first candidate and 380/348 on `e238c9e2`, but still exhausts the unchanged
100,000-operation cap. Equal capped totals do not quantify a complete-request
saving. P09, P11, P16, P23 and L03 remain the five failing original recordings.
The candidate's P23 runtime predates `e238c9e2`'s cold-seed integration, so its
P23 failure progress is not attributed to this JSON change.

The raw runs are `json-fresh-focused-001`, `full-json-fresh-001` and
`json-fresh-comparison-002`, with the excluded comparator attempt retained as
`json-fresh-comparison-001`. These are worker-source executions. Integration
must repeat focused correctness followed by all 28 original recordings on the
combined source; no old-source pass substitutes for that check.
