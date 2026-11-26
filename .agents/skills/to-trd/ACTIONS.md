# To-TRD actions

Action IDs identify **operation types**, not response records or job IDs. The
helper records only the last operation that mutated a TRD in `last_action_id`.
Read operations and `reindex` do not change that field. These IDs do not establish
permission: the current user's request and host permissions still govern work.

| ID | User operation | Helper route | Writes |
| --- | --- | --- | --- |
| TO-TRD-001 | Capture a new TRD | `create --input ...` | New draft and index |
| TO-TRD-002 | Resume a selected draft | `show <selector>` then clarification | None until explicit save |
| TO-TRD-003 | Revise document content | `update <selector> --expect-sha256 ... --input ...` | Selected document and index; material approval-bearing edits return trd_done to draft |
| TO-TRD-004 | List TRDs | `list [--status ...]` | None |
| TO-TRD-005 | Show status/content | `show <selector>` | None |
| TO-TRD-006 | Approve document completion | `set-status ... --status trd_done` from draft | Document metadata and index |
| TO-TRD-007 | Reserved legacy schema-1 implementation-completion action | No current helper route | Never accepted or emitted for schema 2 |
| TO-TRD-008 | Retire a TRD | `set-status ... --status retired` | Metadata and index; no deletion |
| TO-TRD-009 | Restore a retired document | `set-status ... --status draft` from retired | Metadata and index |
| TO-TRD-010 | Validate the catalog | `validate` | None |
| TO-TRD-011 | Rebuild the runtime index | `reindex` | Index only; initializes TRDs if absent |
| TO-TRD-012 | Return a completed document to draft | `set-status ... --status draft` from trd_done | Metadata and index |
| TO-TRD-013 | Migrate a legacy schema-1 document | `migrate <selector> --expect-sha256 ... --reason ... --confirmed` | Selected schema-2 document and index, or validated no-op when already current |

Capture reaches `create` only at the authorized synthesis boundary after
[discovery](references/wayfinding.md), or when an incomplete draft is explicitly
requested. A material question ends the response and waits; neither asking nor
receiving an answer automatically writes. Resume remains read-only until
explicit save. Revision resolves and reads the exact record before its authorized
update; list/show/validate and lifecycle-only requests do not start an interview.
When follow-ups are prohibited, report material gaps and save only an authorized
incomplete artifact. No operation changes its ID or gains write authority from
these conversational rules.

Every `set-status` call requires `--expect-sha256 HASH`, `--reason TEXT`, and
`--confirmed`. Every existing-document update requires the current content hash.
Migration writes require the same hash, reason, and confirmation preconditions.
`migrate <selector> --check` runs read-only preflight; it never records an action
or repairs the index. Repeated same-state changes are no-ops, not new actions.
A scope edit through TO-TRD-003 that automatically returns a document to draft still records
TO-TRD-003 because revision was the operation performed.

User-facing phrases such as `$to-trd approve <ID>` are interpreted by the agent;
they are not extra Python CLI subcommands. Use the exact helper routes above.
The helper has eight subcommands: create, update, set-status, migrate, list, show,
validate, and reindex. Current status choices are `draft`, `trd_done`, and `retired`.
Legacy `not_done` and `done` are recognized only by labeled schema-1 readers and
migration, never as current CLI choices. Document approval does not authorize
downstream planning or execution.
