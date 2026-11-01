# Explicit Agent/0.17 keyed merge

Select `ontokin.agent/0.17` for source 0.17 / keyed-merge-0.1 and recorded
`ontokin.glb/0.17` after the reviewed adoption is published. This interface
inherits the twelve .16 operations and request shapes. The binding remains
experimental and explicit; earlier default entry points and protocols retain
their meanings. Immutable bundle/files remain `0.2`.

`merge_keyed<T>(left, right)` combines two exact `Keyed<T>` values. It evaluates
and fully admits left once, then right once, including empty operands. Each
input and the result are bounded to 256 entries. The result uses canonical
ASCII key order and detached typed values. A shared key is refused even when
both values are equal. The lowest shared ASCII key is diagnosed before a
disjoint-result size refusal.

The collision diagnostic is `OKL-E-ID`, category `invalid`, phase
`elaboration`, rule `LANG-007`, at the right operand's first lexical token.
The left operand's first lexical token is its single related location, and
details contain `operation: "merge_keyed"` and `key: <the shared key>`. An
opening `(` is the first token of a grouped operand. These token spans are
distinct from the full expression spans retained in provenance.

A disjoint union above 256 uses `OKL-E-RESOURCE`, category `resource_limit`,
phase `support`, rule `LANG-009`, at the original `merge_keyed` keyword with
no related location. Its details are `bound: "keyed_merge_result_entries"`,
`limit: 256` and `actual: <the disjoint total>`. Exact operand mismatches use
`OKL-E-TYPE`, category `invalid`, phase `type`, rule `LANG-003`, at the
offending operand's first token, with resolved `expected` and `actual` type
details and no related location. Inherited input/constructor failures retain
their original diagnostic shapes. No partial collection, accepted source,
run or artifact is published after refusal.

Inspection adds read-only `derived_merges` on derived values and `input_merges`
on generated occurrence source provenance. Each record has exactly
`expression`, `left`, `right`, `element_type` and `input_side`. The locations
refer to original complete source expressions and use existing source IDs,
revisions and UTF-8 byte spans. `input_side` is `"both"` for aggregate records
and `"left"` or `"right"` for the contributing input of an individual entry.
Generated `input_merges` keeps aggregate records first, then contributing
entry records, with exact-record deduplication. Existing original entry
provenance and independent map/reduction/filter records remain available.

For nested `outer = merge(inner = merge(A, B), C)` with plain disjoint inputs,
an A entry's generated `input_merges` order is `[inner/both, outer/both,
inner/left, outer/left]`. Indexing that entry into a derived scalar uses the
same order in `derived_merges`. Downstream bodies that ignore their input
values still retain actual aggregate merge reads.

Both inputs' actual dependencies and taints remain visible even when one or
both are empty. The records create no writable identity. Repair the original
source/member through its current program revision and exact byte
precondition. Old runs retain their original revisions and memberships.

All evaluation, admission, collision lookups, canonical comparisons, copying,
provenance and materialization consume current cumulative authority. Actual
`keyed_merge_collision` and `keyed_merge_iteration` checkpoints support
cooperative cancellation. Ordinary defaults remain 100,000 operations /
30,000 ms; higher requests need independent current host authority and caller
caps can only reduce it.

The service uses `keyed-merge-program-agent.sqlite3` and store schema
`ontokin.keyed-merge-program-agent-store/0.1`. Preserve the 8,388,608-byte
request envelope, exact PNG admission and bounded source/asset/mesh/artifact
retrieval, stale-revision/cursor refusals, rollback, cancellation,
reopen/retry, changed-payload refusal and interrupted-publication handling.

Read the [language decision](../keyed-merge-v0.1/ADOPTION.md) and the separately
frozen workflow requirements. The schema and guide alone establish no
executed workflow, completed feature release or full-product acceptance.
