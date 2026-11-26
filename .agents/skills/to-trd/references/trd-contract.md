# TRD storage and operation contract — version 2

## Authority and storage

The canonical artifact is `<project-root>/TRDs/trd_<slug>_<YYYY-MM-DD>.md`.
Each file contains its own metadata and requirements. `TRDs/INDEX.md` is a
generated human-facing projection. It is never authoritative over a TRD.

To-TRD tracks the document's drafting, approval, and retirement. It does not
track implementation progress or satisfaction of the captured requirements.
`trd_done` means that the exact requirements document is complete and approved.
It does not authorize planning, implementation, installation, migration, Git
activity, publication, deployment, or external action. Each operation retains
its own activation and authority requirements.

One helper, `scripts/trd.py`, manages naming, parsing, lifecycle transitions,
read-only inspection, and index regeneration. There is no `task.json`, task
subfolder, transcript, response ledger, current-document pointer, background
watcher, or database. A project with N TRDs needs N document files and one index.
Temporary write files and a short-lived catalog lock are not durable records.

The root must be explicitly supplied to each command. The helper accepts an
existing absolute or relative project path and resolves it; it does not search
upward or guess that its own directory is the project root. A symlinked `TRDs/`
or managed document/index path is rejected. A symlink resolving the explicitly
selected project root itself is resolved once to establish the actual root.

## Naming and identity

A title is nonblank, single-line UTF-8 text of at most 160 bytes. Slugs are NFKD
normalized, lowercase ASCII alphanumeric words separated by hyphens, bounded to
60 characters. A title without retained ASCII characters uses `trd` as its slug.

Creation uses the local date, producing `trd_contacts-export_2026-08-28.md`.
For the same slug/date, use `trd_contacts-export-2_2026-08-28.md`, then `-3`, and
so on, shortening the base if necessary to keep the name bounded. Collision
resolution occurs under the catalog lock and never overwrites an existing TRD.

The stable ID is `TRD-YYYYMMDD-XXXXXXXX`, where the suffix is eight uppercase
UUID-derived hexadecimal characters and is checked against the catalog. The
filename, ID, slug, and created timestamp remain immutable. Changing a title
changes only the display name and H1. A different date does not rename an old TRD.

Timestamps are ISO 8601 with explicit offsets. The default is the host's local
clock; `--timezone America/Denver` or another available IANA timezone can be
supplied explicitly. An unknown timezone produces an input error. Updated time
never moves before the prior update, including when the host clock moves back.
The helper supports Python 3.10 or later and uses `zoneinfo` from the standard
library; an explicitly requested timezone must exist in the host timezone data.

## Frontmatter

Use these keys and no others, in the generated order:

| Key | Type | Rule |
| --- | --- | --- |
| schema_version | Integer | Exactly 2 for current records, not a Boolean |
| trd_id | String | Stable valid ID matching the creation date |
| title | String | Nonblank single-line display title |
| slug | String | Matches the filename name component |
| created_at | String | Immutable aware creation timestamp |
| updated_at | String | Aware timestamp not before creation/prior managed update |
| status | String | draft, trd_done, or retired |
| revision | Integer | Positive; starts at 1 and advances only for actual document changes |
| last_action_id | String | Current mutating action type from ACTIONS.md; legacy TO-TRD-007 is invalid in schema 2 |
| status_reason | String | Concise lifecycle reason, at most 1,024 bytes |

Every value is a **JSON scalar on one line**, inside a YAML-compatible frontmatter
block. This intentionally narrow convention avoids a third-party YAML parser
and arbitrary YAML behavior. Do not add multiline YAML, aliases, duplicate keys,
unknown fields, or unquoted string values. The helper's SHA-256 receipt is not
stored in the document, since the document cannot contain its own final hash.

```yaml
---
schema_version: 2
trd_id: "TRD-20260828-0123ABCD"
title: "Contacts export"
slug: "contacts-export"
created_at: "2026-08-28T16:00:00-06:00"
updated_at: "2026-08-28T16:00:00-06:00"
status: "draft"
revision: 1
last_action_id: "TO-TRD-001"
status_reason: "Created as a draft from an explicit user request."
---
```

The helper renders `# Task Requirement Document: <title>` after the metadata.
Do not put an H1 or frontmatter into the payload body.

## Discovery and save boundary

The agent follows [intent discovery](wayfinding.md) before ordinary synthesis.
Its readiness review establishes supported meaning, the helper validates the
artifact's structure, and the user approves the exact presented revision. These
are distinct controls; passing `validate` or `completion.content_ready` cannot
establish understanding or consent.

An unresolved current-task choice remains intake even when phrased as a
requirement for the next agent to determine the intended behavior. This is an
agent semantic review, not a helper keyword rule. Supported future-user
questions, research objectives, quoted labels, and URL queries remain legitimate
content under the field rules below.

Capture permits a new draft at the authorized synthesis boundary. Resume alone
is read-only until explicit save. A revision requires an exact record read and
authority for its content update. Questions and answers do not cause automatic
persistence. An explicit incomplete-draft request permits known intent with
declarative gaps, including zero requirements; a prohibition on follow-ups does
not itself supply either missing intent or artifact authority. Read-only and
lifecycle-only operations retain their existing boundaries.

## Current body contract

Use these H2 headings exactly once, in this order:

```text
Destination
Captured user intent
Context and sources
In scope
Out of scope
Task requirements
Decisions
Open questions
Not yet specified
Assumptions
```

Each heading requires content. `None.` is the explicit empty-list value.
Destination and Captured user intent must be meaningful statements, not empty
scaffolding. Context and sources can state that a source is missing or that the
only source is the user's current request; no source should be fabricated.

Use one requirement block per bounded task outcome:

```markdown
### REQ-001 — Export the existing contacts
- Requirement: Export the existing contacts list as a local CSV file.
- Source: U01 — the user's current request.
- Acceptance: The file contains the existing contacts without modifying their source records.
- Depends on: None.
```

Field values are single-line Markdown text. Add more `Source` or `Acceptance`
lines when needed. Use exactly one `Requirement` and `Depends on`, and at least
one `Source` and `Acceptance`. `Depends on` contains `None.` or comma-separated existing
IDs. Duplicate IDs, duplicate dependencies, missing targets, self references,
and cycles are rejected. A document may contain at most 2,000 requirements.

Use readable titles after the ID. The template uses an em dash; the parser also
accepts a spaced ASCII hyphen. Requirement IDs have at least three digits and
need not be consecutive. Do not renumber or reuse an existing ID casually.

An underspecified draft can use the exact text `No task requirements captured
yet.` in Task requirements. A `trd_done` document cannot. Current requirements
have no implementation-completion checkbox or `Evidence` field, and the current
body has no `Completion evidence` section. Those legacy fields are rejected in
schema 2, and current validation does not count completed requirements.

Assumptions contains `None.` or lines beginning with `- Accepted: ` or
`- Unconfirmed: `. Accepted assumptions require a real basis in the user's
instruction or sources. The prefix is not permission to invent acceptance.

`Open questions` is a schema-compatibility section. It must contain exactly
`None.` in every newly created or updated TRD. Clarification questions belong in
the live conversation; the document records the user's resulting answer in the
appropriate intent, decision, scope, requirement, assumption, or acceptance
entry. `Not yet specified` may preserve an unresolved in-scope area in a draft,
but it must state the gap declaratively rather than ask a question or instruct a
downstream agent. Optional future enhancements belong out of scope.

An implementation choice is not an unresolved requirement when the desired
behavior, scope, acceptance, and authority are already bounded. Record which
choices remain with implementation planning under `Decisions`, including the
constraints and basis for that boundary. Do not put ordinary library versions,
internal APIs, or packaging details in `Not yet specified` merely because no
implementation plan exists. A user-mandated technical constraint or a real
behavior, compatibility, or permission gap remains a requirement-level issue.
Moving a real gap to another heading does not make the document complete.

The helper rejects current creation or update payloads that would persist
question content in `Open questions` or a question mark in `Not yet specified`.
Historical questions remain readable in legacy records and mechanically migrated
`draft` or `retired` records under the compatibility rules below. Migration
preserves that content verbatim; it never converts questions into declarations
or invents the user's answer. A subsequent managed content update must resolve
questions into document content or describe an unresolved area declaratively.

Unfilled `{{template_slots}}` are rejected in runtime documents. The slots in
`assets/trd-body-template.md` are intentional and must be replaced before writing.
The template is an artifact-shape aid after discovery, not an intake checklist.
For an honest zero-requirement draft, replace the entire sample requirement
block with `No task requirements captured yet.`. The concrete
`assets/example-input.json` is valid as supplied and labels its clarification
as fictional. That answer changes the example's requirement and acceptance,
not only its decision notes.

## Lifecycle

`draft` means that intent, scope, requirements, acceptance criteria, decisions,
assumptions, or other document content needs review or clarification. It says
nothing about implementation. `trd_done` is the approved, completed requirements
document. `retired` preserves an inactive document without implying implementation
success or failure.

| Current state | Allowed destinations |
| --- | --- |
| draft | trd_done, retired |
| trd_done | draft, retired |
| retired | draft |
| Any state | Same state as a no-op |

New records always start as draft. A `set-status` request must include the
current hash, a nonblank reason, and `--confirmed`, attesting to the current
user's explicit instruction. The helper cannot independently prove that consent.
Same-state requests validate identity/hash and remain true no-ops: no revision,
time, reason, or index write is performed.

### Document completion gate

To enter `trd_done`, the TRD must have at least one valid requirement, `Open
questions` and `Not yet specified` must both be `None.`, and Assumptions must
have no unconfirmed entries. The user must explicitly approve the exact current
revision, identified by its digest. The required nonblank reason and
`--confirmed` attest to that approval; they cannot establish consent on their
own. The gate checks document structure and settled content, never whether
product requirements were implemented, tested, deployed, or otherwise satisfied.

The agent must compare the document with the user's stated intent, sources,
constraints, and acceptance criteria before representing it as complete. It
must not invent approval or claim that document approval proves product behavior.

The agent binds approval of a presented, unchanged revision to the helper's
current digest. The user does not need to type a SHA-256. An unambiguous approval
of that document is sufficient; a request to fix the skill, inspect status, or
create a plan is not document approval. A normal capture with settled content
ends with a reviewable artifact and one approval question if approval is missing
and the current instructions permit questions.
Explicit draft-only requests and read-only operations do not start that exchange.

### Completion diagnostics

Every document summary and write receipt includes a derived `completion` object:

| Field | Meaning |
| --- | --- |
| `content_ready` | Whether the current-schema document passes the structural content gates; `null` for legacy schema 1. This is not semantic review or user approval. |
| `blockers` | All content blockers, each with `code`, `section`, and a bounded `message`. |
| `next_action` | `resolve_requirements`, `request_approval`, `none`, `restore_to_draft`, or `migrate`, according to content and lifecycle state. |

Content blocker codes are `missing_requirements`, `open_questions`,
`unspecified_requirements`, and `unconfirmed_assumptions`. Legacy records report
`legacy_schema`. A rejected `trd_done` transition returns the same content
blockers as `completion_blockers` in its error receipt. Missing confirmation,
stale hashes, locks, and other operation failures retain their existing errors.

Diagnostics use the same checks as the actual transition. They do not classify
arbitrary prose, clear fields, approve a document, or persist new metadata.
`request_approval` identifies the remaining workflow step, not a command to ask
again when approval of that unchanged content already exists. A retired record
first needs explicit restoration; a legacy record first needs explicit migration.
Reading these fields changes neither canonical bytes nor index content.

### Revision and restoration

`update` can change the title and/or body of a `draft` or `trd_done` document.
Any change to the title, outcome, scope, exclusions, requirements, acceptance,
dependencies, decisions, assumptions, sources, or other approval-bearing content
of a `trd_done` record atomically saves the revision as `draft` with a clear
reason that renewed review is required. There is no evidence-only progress path.

The comparison is conservative: only CRLF/LF representation and outer blank
lines may be normalized to establish a representation-only no-op. Such a no-op
preserves the existing canonical bytes, hash, status, revision, timestamps,
reason, and index. Interior content or title edits require review even if the
agent considers them editorial. Unknown equivalence is a material change.

Retired TRDs cannot be updated directly. Explicitly restore a retired document
to `draft` first. Retirement preserves the file, identity, content, and index
entry. A `trd_done` document can also return explicitly to `draft` through the
confirmed lifecycle operation.

### Action identities

The existing create (`TO-TRD-001`), update (`TO-TRD-003`), and read/index action
identities remain. Current document lifecycle mutations use:

| Operation | Action ID |
| --- | --- |
| Approve document completion: draft to trd_done | TO-TRD-006 |
| Retire draft or trd_done | TO-TRD-008 |
| Restore retired to draft | TO-TRD-009 |
| Return trd_done to draft explicitly | TO-TRD-012 |
| Explicit legacy-schema migration | TO-TRD-013 |

A material `update` records `TO-TRD-003`, including its atomic fallback to
`draft`. `TO-TRD-007` is reserved for legacy schema-1 implementation completion
and is never accepted or emitted as a current record's action. It is not reused.

## Legacy schema-1 compatibility and migration

Schema 1 is an explicitly labeled read-only compatibility format. Its legacy
states are `draft`, `not_done`, `done`, and `retired`; its body includes a
`Complete` checkbox and `Evidence` fields for each requirement and a final
`Completion evidence` section. Those fields are recognized only to read and
safely migrate historical documents, not as current progress tracking.

The compatibility parser retains structural validation, identity, dependency,
size, path, and secret checks. It does not apply the legacy implementation
evidence gates or infer that a legacy status establishes true product completion.
It also does not apply current readiness gates to an unmigrated legacy record.
This permits inspection and precise preflight diagnostics for a checked box
with placeholder evidence or another structurally readable historical record.
Unknown schema versions or malformed structure still fail validation. The read
parser also permits historical `Open questions` and question-form uncertainty
in schema-2 drafts or retired records produced by mechanical migration. This
read compatibility does not relax the rules for new creation, managed content
updates, or the `trd_done` document gate.

Every summary identifies the document schema and reports `compatibility` as
`current` for schema 2 or `legacy_v1_requires_migration` for schema 1, with an
explicit Boolean `migration_required`. `show`, `list`, and `validate` never
rewrite legacy records or their index. An ordinary `update` or `set-status`
against schema 1 fails with the `migration_required` category, even for an
otherwise same-state request. Legacy state tokens are not current CLI aliases.

### Migration preflight

Migration requires an exact selector, the current lowercase SHA-256, a nonblank
reason, and `--confirmed` attesting to explicit migration authority. A read-only
preflight is available as `migrate SELECTOR --check`; it may also require a
supplied digest through `--expect-sha256`. Preflight grants no write authority
and changes neither canonical documents nor the index. The write operation
performs the same checks again under the catalog lock with stale-write protection.

Preflight checks every legacy requirement checkbox, every `Evidence` value,
and the entire `Completion evidence` content. Any checked box blocks migration,
including a checked box whose evidence is a placeholder. Any non-placeholder
evidence blocks migration regardless of length: `OK` and `v1` are blocking
historical content, not empty evidence. There is no minimum-length exception.
Only recognized empty markers, compared case-insensitively after trimming, may
be removed: `none`, `n/a`, `na`, `not yet verified`, `not verified`, `unverified`,
`pending`, `todo`, `tbd`, `not run`, `not tested`, `no evidence`, or `no evidence
yet`, optionally followed by one period or exclamation mark.

A blocker reports the exact selected record and field before canonical or index
mutation. No automatic evidence archive, invented replacement, or silent loss
is allowed. Historical `Open questions`, `Not yet specified`, and assumptions
are preserved verbatim when the mapped state is `draft` or `retired`. If the
mapped state is `trd_done`, unresolved content fails its document completion
gate. Migration does not supply a content-edit bypass or answer old questions.

### Migration result

For a qualifying legacy record, remove only its unchecked completion lines,
placeholder `Evidence` lines, and placeholder `Completion evidence` section.
Preserve all sourced requirements, acceptance criteria, dependencies, decisions,
scope, exclusions, assumptions, and other approval-bearing meaning. Apply this
deterministic state mapping:

| Legacy schema-1 state | Current schema-2 state |
| --- | --- |
| draft | draft |
| not_done | trd_done |
| done | trd_done |
| retired | retired |

Validate the complete schema-2 candidate using historical-question read
compatibility and its destination-state document gate before publication.
Preserve the filename, ID, slug, title,
creation timestamp, and requirement IDs. Increment the revision once, keep the
update timestamp monotonic, set schema version 2 and `TO-TRD-013`, and record the
explicit migration reason. The receipt makes the before/after schema, state,
revision, digest, identity, and index outcome reviewable. Mapping a legacy
settled state asserts no implementation result. A mechanically migrated draft
remains draft until a separate approval of its exact current revision.

Each catalog member must be explicitly selected for migration; catalog reads
and `reindex` do not migrate records. The canonical-first commit and partial
index recovery rules apply to migration as to other writes.

For an already-schema-2 target, `migrate --check` reports `already_current`.
A migration write invocation still validates the exact selector, current hash,
nonblank reason, and confirmation, then returns `no_op` with unchanged canonical
bytes, revision, timestamps, status, and index.

## Implementation-plan handoff

A `trd_done` document can be observed as a settled source for
To-Implementation-Plan with its ID, revision, digest, schema, and document state. A `draft` source
remains visibly unsettled. Source observation is read-only and grants no
planning or execution authority. Plan readiness, plan execution, requirement
satisfaction, and implementation evidence remain in To-Implementation-Plan and
Task under their separately activated workflows.

## CLI

All actual operations return JSON. `--help` prints ordinary help. Argument and
payload failures return JSON errors with a stable exit category.

Global arguments precede the command:

```bash
python3 /path/to/to-trd/scripts/trd.py --project-root /project [--timezone America/Denver] COMMAND
```

| Command | Inputs | Result |
| --- | --- | --- |
| create | `--input FILE` or `--input -`; payload has exactly title and body | Draft receipt, path, ID, hash, index result |
| update | Exact selector, `--expect-sha256 HASH`, input with title and/or body | Updated receipt or no-op; scope_changed when changed |
| set-status | Exact selector, current hash, target status, reason, `--confirmed` | State-change receipt or no-op |
| migrate | Exact legacy selector, current hash, reason, `--confirmed` | Schema-2 migration receipt and index result |
| migrate --check | Exact selector; optional `--expect-sha256 HASH` | Read-only migration preflight; no mutation |
| list | Optional current `--status` | Classified canonical summaries and separate current/legacy counts; no mutation |
| show | Exact selector | Metadata, body, current hash; no mutation |
| validate | No selector | Full canonical validation and index drift; no mutation |
| reindex | No selector | Regenerated index or no-op; does not change TRDs |

`set-status --status` and `list --status` accept only `draft`, `trd_done`, and
`retired`. They reject the legacy tokens `not_done` and `done`. A status-filtered
listing selects only current schema-2 records; an unfiltered listing also shows
explicitly classified legacy records.

Selectors are exact ID, exact filename, or unique case-insensitive complete
title. ID takes precedence over filename, then title. Paths, hidden selectors,
partial IDs, substring matching, and fuzzy matching are not supported. A title
containing a path separator can still be selected by ID or filename.

Creation input example:

```json
{"title": "Contacts export", "body": "## Destination\n\n...complete template body...\n"}
```

The abbreviated body above is explanatory, not runnable. Use the complete
`assets/example-input.json` for a runnable sample. Payloads and TRDs are limited
to 1 MiB each; duplicate JSON keys and unknown payload fields are rejected.
Payload files must be regular, non-symlink files. Reading an explicitly supplied
payload outside the project is allowed; it does not permit writing there.

`show` returns `document.sha256`; pass that exact lowercase value to the next
existing-document mutation. The revision is a human-readable counter, while the
hash also catches manual edits that did not advance the revision. After a conflict,
reread the latest file and reconsider the proposed change; do not blindly retry.

## Result and error categories

Normal results contain `schema_version`, `command`, `project_root`, `status`,
`mutated`, and `warnings`, with document receipts or catalog fields as applicable.
A receipt includes ID, path, state, revision, timestamps, hash, and requirement
count, plus the schema compatibility classification. Neither current nor legacy
summaries expose a completed-requirement count. The path is project-relative.
A `show` result additionally includes body. Catalog `counts` contains only the
three current states and counts only schema-2 records. If legacy records exist,
`legacy_counts` separately reports the four legacy state counts; otherwise that
field is omitted. The top-level response schema version is 2 and is distinct
from each document's own schema version.

| Exit | Meaning |
| --- | --- |
| 0 | Successful read, write, or no-op |
| 2 | Invalid arguments, input, or direct document format |
| 3 | Missing project or exact target |
| 4 | Ambiguous full title |
| 5 | Unsafe managed path or corrupt canonical catalog |
| 6 | Stale content hash |
| 7 | Catalog lock exists / busy |
| 8 | Prohibited transition, retired edit, missing confirmation, unmet document/migration gate, or migration required |
| 9 | I/O failure; inspect mutated, document, and index_updated fields |

Canonical catalog corruption is reported as category 5 even when the underlying
problem is a field format error. Projection drift is a warning, not corrupt
canonical state: `validate` returns `canonical_valid: true` and
`index_current: false`, allowing the caller to distinguish the two.

A partial index failure returns `mutated: true`, the committed document receipt,
`index_updated: false`, and a reindex recovery instruction. Do not tell the user
that nothing was saved, and do not repeat creation. A pre-canonical write failure
returns no document commit. The helper does not claim a transaction across both
files or an ACID database guarantee.

## Index generation

The index is generated from canonical `trd_*.md` files, never from its previous
rows. It shows counts for the three current states and a table of ID, linked
title, state, schema compatibility, created/updated timestamps, and revision.
Legacy records retain their actual state under an explicit schema-1 label and
separate legacy counts; they are never silently counted as current documents.
Retired documents remain present.

Sort current records by `draft`, `trd_done`, `retired`, then most recent actual
update instant, then ID. Group legacy records separately after current records,
ordered by their legacy `draft`, `not_done`, `done`, `retired` states, then actual
update instant and ID in the same way. The snapshot time is the maximum
canonical update, or `No records`.
No current-time generation stamp causes spurious drift on each read. Escape
Markdown-sensitive title characters; links target the safe local filenames.

List/show/validate work when the index is absent or stale. They report drift and
never repair it implicitly. If a canonical file is malformed, stop rather than
skip it and produce an incomplete catalog. `reindex` is the explicit repair path
for navigation only. It may initialize an empty TRDs directory and index.

## File safety and recovery

The helper writes with one `.to-trd.lock/` directory in TRDs and same-directory
`.to-trd-tmp-*` files. The lock serializes cooperating writers. Existing-document
hashes are checked after reading and again just before atomic publication. File
content is flushed before replacement. The canonical TRD is committed before
its derived index. The design assumes an ordinary local filesystem supporting
these operations, not a distributed lock service or hostile multiuser directory.

Read operations do not acquire or remove locks; they check before and after
scanning and return busy if a lock is observed. They are not linearizable reads
against arbitrary non-cooperating editors. Manually editing a file concurrently
with a write is still discouraged.

A crash can leave a lock or temporary file. Do not steal the lock based only on
age or a process ID. Confirm no writer is active, inspect the exact lock and
owner metadata, remove only that stale lock's owner file and directory under
user authority, validate canonical documents, then reindex. Do not delete the
TRDs directory or documents. A malformed document must be repaired from known
content, not reconstructed by guessing user intent or historical evidence.

The pre-write secret guard recognizes only a few obvious key/token patterns and
credential assignments. It is not a comprehensive secret scanner or privacy
classifier. The agent must avoid saving secrets, hidden reasoning, full transcripts,
or unnecessary logs before calling the helper. The helper never executes commands
from a TRD or a source document.
