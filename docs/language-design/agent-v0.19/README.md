# Experimental keyed renaming Agent/0.19

This explicit interface implements the published [C086 language decision](../keyed-rekey-v0.1/ADOPTION.md). The [input freeze](../keyed-rekey-v0.1/INPUT-FREEZE.json) fixes the acceptance inputs independently of implementation. Implementation, executed validation, integration and full feature release remain separate facts.

The binding is `ontokin.agent/0.19`, for source `0.19`, profile `keyed-rekey-0.1` and recorded destination `ontokin.glb/0.19`. Immutable transport remains `ontokin.bundle/0.2` and `ontokin.files/0.2`. The store is `keyed-rekey-program-agent.sqlite3`, with schema `ontokin.keyed-rekey-program-agent-store/0.1`. Older bindings retain their contracts; CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain ordinary defaults.

## Discovery and source operation

`rekey_keyed<T>(input, (old_key, value) -> new_key)` accepts exactly `Keyed<T>` and returns exactly `Keyed<T>`. Each pure callback returns exactly String. The 24 inherited immutable leaf families, exact aliases, units and frames retain their meaning. The complete input is evaluated and admitted once before callbacks. Unknown-payload static checking also applies to empty inputs.

Callbacks run once per old key in canonical ASCII order. Computed keys have 1–64 ASCII characters, begin with an alphanumeric character and otherwise contain only alphanumerics, period, underscore or hyphen. Keys remain case-sensitive. The first computed collision fails immediately, before later callbacks. Successful output sorts by new key and retains every original payload exactly. No String concatenation, suffix generation or overwrite policy is added.

Discovery reports these boundaries, the 256-entry maximum, current host ceilings, inherited operations, identity consequences and the four actual cancellation stages: `keyed_rekey_iteration`, `keyed_rekey_key_validation`, `keyed_rekey_collision` and `keyed_rekey_publication`. The last is an internal construction checkpoint, including for empty input; it is not an Agent commit.

## Operations and transport

The twelve request shapes remain inherited:

| Operation | Responsibility |
| --- | --- |
| `discover` | Read detached capabilities and current host authority. |
| `create` | Admit an exact offline source and asset bundle atomically. |
| `edit` | Apply revision-bound UTF-8 source and asset changes with exact preconditions. |
| `validate` | Check the named accepted or candidate program at the requested level. |
| `inspect` | Read bounded detached source, values, state and original contributor lineage. |
| `surface.mesh_page` | Page the selected revision's native source-derived mesh and UV data. |
| `evaluate` | Record supported motion under current authority. |
| `reset` | Apply inherited reset and immutable revision/run semantics. |
| `export` | Publish a complete verified artifact for the explicit recorded destination. |
| `artifact` | Retrieve exact bounded artifact bytes under pinned identity. |
| `status` | Reconcile durable request/run status and unknown outcomes. |
| `cancel` | Apply cooperative cancellation without partial accepted publication. |

Source inspection uses the existing bounded complete source-unit item pages. No `source_slice` request field is introduced. Asset and artifact byte slices retain their existing shapes and scope checks. Requests remain bounded by 8,388,608 bytes. The cumulative current-request ledger, 100,000-operation and 30,000-ms ordinary defaults, independently current host ceilings, reducing caller caps and inherited response/cursor/parser bounds remain in force.

## Closed detached lineage

The new fields are `derived_rekeys` on derived values and `input_rekeys` on generated occurrence provenance. Every record has exactly seven fields:

| Field | Meaning |
| --- | --- |
| `expression` | Full original rekey expression location. |
| `input` | Full original input expression location. |
| `body` | Full original callback body location. |
| `element_type` | Canonical resolved element type. |
| `old_key` | Original key for a selected contributor; null for an aggregate. |
| `new_key` | Computed key for that contributor; null for an aggregate. |
| `input_entry` | Original payload entry location when available; null for an aggregate or unavailable entry. |

Locations contain exactly `source_id`, `source_revision`, `filename`, `start_byte` and `end_byte`. Aggregate old_key, new_key and input_entry are all null. Selected records require both actual keys; an unavailable original entry can remain null. Extra fields are rejected. The new key schema enforces the full ASCII key domain, including rejection of trailing line breaks. [SCHEMA-DERIVATION.json](SCHEMA-DERIVATION.json) records every structural change from the exact C085 schemas.

Input and selected callback records retain actual evaluation order and complete-record deduplication. Prior map, reduction, filter, merge and zip records keep their original contributor keys. Generated IDs and paths use new keys, while the singular generated input entry remains the original payload source span. A rename therefore removes the old occurrence identity and introduces the new one; identity renaming preserves the key. This read-only lineage grants no writable synthetic identity. Repairs still require original source/member locations, exact revisions and UTF-8 preconditions.

## Refusal and acceptance boundary

A duplicate computed key and an invalid computed key use the exact `OKL-E-ID` diagnostics and original source locations fixed by the adoption. Input and callback boundary mismatches use exact `OKL-E-TYPE` diagnostics. Static invalidity precedes dynamic input evaluation; dynamic key validation precedes collision lookup. Existing callback exceptions retain their identity. No failure, cancellation, resource exhaustion or interrupted publication may expose a partial accepted source, run or artifact.

The frozen [Agent cases](../../../examples/keyed-rekey/agent/workflows.json) define scoped first-instance renaming, unchanged siblings and pinned libraries/assets, duplicate rollback, reverse repair and independent marker motion. Their explicit .18 controls and byte-level allowances govern comparisons. The exact PNG declaration closure includes reachable .13–.19 units, unused definitions, empty inputs and discarded payloads. Nothing in this interface expands physical authority or establishes complete feature or product acceptance.
