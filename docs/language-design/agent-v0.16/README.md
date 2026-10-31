# Explicit Agent/0.16 keyed filtering

Select `ontokin.agent/0.16` for source 0.16 / keyed-filter-0.1 and recorded
`ontokin.glb/0.16`. This interface inherits the twelve .15 operations and request
shapes. The binding remains experimental and must be selected explicitly;
earlier default entry points and protocols retain their meanings.

`filter_keyed<T>(input, (key, value) -> predicate)` admits a finite immutable
`Keyed<T>`, evaluates a strict Boolean predicate for every admitted entry in
canonical ASCII key order, and returns unchanged keys/values for the survivors.
The input bound remains 256. All work, copies, dependency/provenance merges and
serialization consume current cumulative authority. Ordinary defaults stay
100,000 operations / 30,000 ms; higher source requests need current independent
host authority and caller caps only reduce that authority.

Inspection adds read-only `derived_filters` on derived values and `input_filters`
on generated occurrence source provenance. A filter record has exactly four
fields: `expression`, `input`, `predicate` and canonical resolved `element_type`.
The three locations point to original source IDs/revisions and UTF-8 byte spans.
Existing entry keys and input-entry origins remain separate. Map/reduction
origins and actual dropped-entry dependencies/taints must remain visible.

The filter record creates no writable identity. To repair selection, edit the
original source/member through its current program revision and exact byte
precondition. Existing stale-cursor checks, rollback, durable reopen/retry,
changed-payload refusal and interrupted publication rules still apply. Old runs
remain pinned to their old source revisions and memberships.

The service uses `keyed-filter-program-agent.sqlite3` and store schema
`ontokin.keyed-filter-program-agent-store/0.1`. The 8,388,608-byte request envelope
and bounded source, asset, mesh and complete artifact retrieval remain inherited.
Read the [language decision](../keyed-filter-v0.1/ADOPTION.md) and
[frozen workflow requirements](../../../examples/keyed-filter/workflows.json).
Schemas and actual implementation evidence are separately identified by the
coordinator; this guide alone is not evidence that the service has executed.
