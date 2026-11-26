# To-TRD

**Understand the intended outcome, resolve material ambiguity, and derive task
requirements from the user's actual decisions.**

To-TRD is an explicitly invoked, project-local skill. It uses a lightweight
adaptation of **Wayfinder by Matt Pocock** to clarify the user's intended outcome,
then writes one **Task Requirement Document (TRD)**. `TRP` is supported as an
alias from the originating request; it does not name a different technical
requirements format here.

Version 2.2.0 uses schema 2 and tracks completion of the requirements document.
Planning and implementation remain separate workflows.

## What it creates

```text
project/
  TRDs/
    INDEX.md
    trd_contacts-export_2026-08-28.md
    trd_another-outcome_2026-08-28.md
```

Every TRD contains a short intent statement, scope and exclusions, sources,
task requirements with stable IDs and acceptance criteria, decisions, and
assumptions. Requirement fields are declarative; implementation progress and
evidence stay with their owning plan and Task systems. A compatibility section
named `Open questions` remains present but is `None.` in every new or
content-updated document. Its frontmatter is the canonical identity and state.
`INDEX.md` is generated from those files and can be rebuilt.

It does **not** create response records, task folders, a JSON database, startup
hooks, automatic resume notices, background jobs, issue tickets, branches, or
new agent threads. There is no dependency on the Task system, AgentJob,
upstream Wayfinder, or any other companion skill.

## Install in a project

Requirements: a local agent host that supports the skill format, project-local
filesystem access, and **Python 3.10 or later**. The helper uses only the standard
library. A chosen IANA timezone needs to be present in the host timezone data;
otherwise use the host-local default. No package installation is required.

Copy the **entire `to-trd` folder** to:

```text
<project-root>/.agents/skills/to-trd/
```

The folder must contain `SKILL.md`, `agents/openai.yaml`, and the other resources
listed in [INDEX.md](INDEX.md). Keep the attribution and license files with it.
A skill-source library may keep the reusable source at `skills/to-trd/`; that
source layout does not replace project-local installation/discovery.

Run the following from the directory containing the reusable `to-trd` folder,
after replacing the project path and confirming the installation destination:

```bash
TRD_PROJECT="/absolute/path/to/your/project"
test -d "$TRD_PROJECT" && \
  test ! -e "$TRD_PROJECT/.agents/skills/to-trd" && \
  mkdir -p "$TRD_PROJECT/.agents/skills" && \
  cp -R ./to-trd "$TRD_PROJECT/.agents/skills/to-trd"
```

This deliberately stops when the destination skill already exists. Inspect and
update an existing installation separately; do not blindly overwrite local edits.
Do not copy this skill's `AGENTS.md` to the project root. Do not install globally.

**Do not copy sample `TRDs/` over a project's existing TRDs.**
Install only the skill folder. The first explicit creation initializes `TRDs/`
and its index. An explicit `reindex` can initialize an empty catalog when wanted.
If an existing TRD catalog uses another format, run read-only validation first;
there is no automatic migration or permission to overwrite unknown documents.

The included Codex metadata disables implicit invocation. Official host behavior
and local skill locations are documented in [OpenAI's Build skills guide](https://learn.chatgpt.com/docs/build-skills).
Actual discovery and behavior depend on the installed host; the package's tests
do not claim a live Codex session was exercised. If a copied skill does not
appear, inspect the host's skill list and project path and reload the host as
needed. Verify installation and discovery in the selected host separately from
the package's structural checks.

## Use it

In Codex, explicitly mention `$to-trd`. Example requests:

```text
$to-trd Capture my intent for a local contacts-export command as task requirements.
$to-trd Create a draft from these notes; preserve unresolved areas without writing interview questions into it.
$to-trd Resume TRD-20260828-0123ABCD, clarify the remaining export-field uncertainty, and fold my answer into the requirements.
$to-trd Revise TRD-20260828-0123ABCD to exclude cloud upload.
$to-trd list
$to-trd show TRD-20260828-0123ABCD
$to-trd Approve this exact revision of TRD-20260828-0123ABCD as trd_done; the requirements document is complete.
$to-trd Return TRD-20260828-0123ABCD to draft because its scope needs review.
$to-trd Retire TRD-20260828-0123ABCD because the proposed feature is no longer needed.
$to-trd Restore retired TRD-20260828-0123ABCD to draft for review.
$to-trd Check whether legacy TRD-20260828-0123ABCD can be migrated without changing it.
$to-trd validate
$to-trd reindex
```

IDs above are examples. Use an actual ID returned by your catalog. Natural-language
operations are interpreted by the agent and routed to the helper; `approve`,
`retire`, and `resume` are not additional Python subcommands.

The skill first checks the applicable outcome, use, current state, scope,
interfaces, constraints, authority, success conditions, and consequential edge
cases. If no material decision remains, it writes directly within the requested
operation. Otherwise it inspects available facts and asks one focused question
about a user-owned decision, then ends the response and waits. A recommended
option, silence, or an unrelated reply is not an answer.

Each answer changes every affected intent statement, scope boundary, requirement,
and acceptance criterion. Partial answers settle only their clear portion; a
changed choice invalidates obsolete assumptions and follow-up branches. The
agent reviews the understood intent before synthesis. That review, mechanical
validation, and approval of the exact saved document are distinct controls.

You can interrupt discovery and request an incomplete draft, including one with
zero requirements. Material gaps remain declarative in `Not yet specified` and
the record stays draft. If follow-ups are prohibited, the skill reports the
limits without inventing answers and saves only an authorized artifact. New
capture permits a write at its synthesis boundary; resume alone stays read-only
until explicit save. Answers never trigger automatic per-turn persistence.

See the [synthetic interactions](references/interaction-examples.md) for these
branches and their effect on requirements. Assigning a future agent to determine
what the current user intended does not resolve intake. Questions that are
themselves requested product behavior or research remain valid content.

To continue later, explicitly select the TRD by exact ID, exact filename, or
unique complete title. The current file provides the context. There is no
“most recent means current” rule. Ordinary conversation does not trigger a TRD
scan, a resume prompt, or a write.

## The three document states

| State | Meaning | Typical next action |
| --- | --- | --- |
| `draft` | Intent or the requirements baseline is still being settled. | Clarify a material uncertainty in conversation or approve the captured baseline. |
| `trd_done` | The exact requirements document is complete and explicitly approved. | Read it as a settled source or revise it when requirements change. |
| `retired` | No longer active; retained rather than deleted. | Read, or explicitly restore to draft. |

New records always start as `draft`. Approval as `trd_done` requires at least
one valid requirement, `None.` in both `Open questions` and `Not yet specified`,
no unconfirmed assumptions, and explicit approval of the current content digest
with a reason and confirmation. The agent checks that the document faithfully
captures intent and acceptance criteria. Product implementation or test evidence
is not part of this document completion gate.

An implementation plan does not have to exist before the TRD can be completed.
Library selection, exact versions, internal APIs, and distribution details can
remain implementation choices when the required behavior and constraints are
already clear. The skill records that boundary under `Decisions`. Only actual
unresolved requirements belong in `Not yet specified`; moving a real scope,
compatibility, or approval-authority gap elsewhere does not resolve it.

For a normal capture, the agent presents the saved document and asks for approval
once its requirements are settled and questions are permitted. You can approve the displayed, unchanged
revision in ordinary language; the agent reads and checks its hash. It then
changes the state and verifies `trd_done` in the saved file. An explicit request
for a draft ends with the draft, and status questions do not start an approval
exchange. Approval already given for that unchanged content is not requested again.

Helper summaries now explain completion through `completion.content_ready`,
`completion.blockers`, and `completion.next_action`. These distinguish missing
requirements from a document awaiting approval. They are derived diagnostics,
not another persisted state or an automatic approval mechanism.

An approved title or approval-bearing content change atomically returns
`trd_done` to `draft`. Only proven CRLF/LF or outer-blank-line differences are
representation-only no-ops; these preserve the existing bytes, state, revision,
timestamps, and index. A completed document may also explicitly return to draft.
Retired documents must be restored to draft before editing. Retirement preserves
the file and does not assert implementation success or failure. Same-state
requests validate selection, digest, reason, and confirmation without writing.

`trd_done` can be a settled source for To-Implementation-Plan. Reading its ID,
revision, digest, and document state does not activate planning or authorize
implementation. Installation, migration, Git activity, publication, deployment,
and external actions also retain their own authorization boundaries.
A draft can also be used as an unsettled source for a separately requested draft
plan. The plan preserves its real uncertainties instead of requiring every
implementation detail to be decided in the TRD first.

## Direct helper use

The agent normally runs the helper for you. Its CLI is also usable directly:

```bash
python3 .agents/skills/to-trd/scripts/trd.py --project-root /absolute/project list
python3 .agents/skills/to-trd/scripts/trd.py --project-root /absolute/project validate
python3 .agents/skills/to-trd/scripts/trd.py --project-root /absolute/project show TRD-ID
```

All operational results are JSON. `show` returns `document.sha256`, which must
be passed back for an update, lifecycle change, or migration. Replace the
documented path, ID, and hash metavariables with actual values. The project root is mandatory so
a command cannot silently use the wrong current subdirectory.

For a **disposable example project**, the following Python snippet runs the
shipped example and prints the created record. It does not create sample data
inside your actual project:

```python
import json
from pathlib import Path
import subprocess
import sys
import tempfile

skill = Path(".agents/skills/to-trd").resolve()
with tempfile.TemporaryDirectory() as temporary_project:
    result = subprocess.run(
        [sys.executable, str(skill / "scripts/trd.py"),
         "--project-root", temporary_project,
         "create", "--input", str(skill / "assets/example-input.json")],
        check=True, text=True, capture_output=True,
    )
    print(json.dumps(json.loads(result.stdout), indent=2))
```

A new input is a JSON object containing exactly `title` and `body`. An update
contains either or both. Use the complete body template, not arbitrary Markdown;
the grammar keeps machine state checks reliable without another parser dependency.
The helper renders the metadata and H1. Pass long text in a payload file or
stdin, not as interpolated shell code. Do not store secrets in payloads.

Example lifecycle command after reading a current document:

```bash
python3 .agents/skills/to-trd/scripts/trd.py \
  --project-root /absolute/project \
  set-status TRD-ID \
  --expect-sha256 CURRENT-SHA256 \
  --status trd_done \
  --reason "The user approved this exact requirements document as complete." \
  --confirmed
```

The confirmation flag is an attestation of an actual user instruction, not a
mechanism that creates consent. State changes never execute the requirements.
For the full field, state, selector, result, and error contracts, read
[references/trd-contract.md](references/trd-contract.md).

## Legacy schema-1 migration

Read-only `show`, `list`, and `validate` retain legacy schema-1 records without
rewriting them. Summaries label each document `current` or
`legacy_v1_requires_migration` and include `migration_required`. Ordinary update
and status operations require schema 2. Current `set-status --status` and
`list --status` accept only `draft`, `trd_done`, or `retired`; they reject the
legacy `not_done` and `done` tokens. Status-filtered lists include current records
only; unfiltered lists also show classified legacy records.

Inspect the selected record and optionally run a read-only preflight:

```bash
python3 .agents/skills/to-trd/scripts/trd.py \
  --project-root /absolute/project \
  migrate TRD-ID --check --expect-sha256 CURRENT-SHA256
```

The digest is optional for `--check`. Preflight changes neither the document nor
the index and grants no migration authority. With explicit authority to migrate
the selected current content, use:

```bash
python3 .agents/skills/to-trd/scripts/trd.py \
  --project-root /absolute/project \
  migrate TRD-ID \
  --expect-sha256 CURRENT-SHA256 \
  --reason "The user authorized migration of this exact legacy document." \
  --confirmed
```

The legacy mapping is deterministic: `draft` stays `draft`, `not_done` and `done`
become `trd_done`, and `retired` stays `retired`. Migration removes only unchecked
legacy completion lines and recognized placeholder evidence fields/section.
Any checked requirement or non-placeholder implementation evidence blocks the
write and identifies the exact record and field. Short values such as `OK` or
`v1` are preserved by blocking, not treated as empty. There is no automatic
evidence archive or content replacement.

Mechanical migration preserves historical `Open questions`, `Not yet specified`,
and assumptions verbatim in draft or retired documents. The read parser accepts
that historical content after migration. A later managed content update must
resolve questions or express unresolved scope declaratively; approval as
`trd_done` still requires settled content. A migrated draft requires its own
approval of the exact post-migration revision.

Migration preserves identity, filename, creation time, requirement IDs, and
approval-bearing meaning. It records the new schema, one revision increment,
monotonic update time, migration reason, before/after receipt, and index result.
For an already-schema-2 target, `--check` reports `already_current`; a migration
write still checks selector, digest, reason, and confirmation, then returns a
no-op with unchanged document and index. Reindexing never migrates records.

## Index behavior and recovery

The runtime index includes every valid TRD, including retired documents. It lists
IDs, names, links, states, schema compatibility, creation/update timestamps,
revisions, and state counts. Current counts contain only schema-2 `draft`,
`trd_done`, and `retired` records. Mixed catalogs show legacy counts separately;
there is no completed-requirement count.

Its content is deterministic and derived from canonical files, not prior rows.
A missing/stale index does not hide a document from list/show/validate.

Read-only commands do not repair navigation. To rebuild it explicitly:

```bash
python3 .agents/skills/to-trd/scripts/trd.py --project-root /absolute/project reindex
```

A malformed canonical document stops catalog mutation rather than being silently
omitted. Repair the exact document from known user/source content; never invent
its missing requirements or historical evidence. Reindex does not change TRD
meaning and cannot repair corrupt canonical content.

Writes use one short-lived `TRDs/.to-trd.lock/` and same-directory temporary files.
A stale hash means someone changed the document: reread and reconsider the edit,
rather than retrying blindly. A lock means another writer may be active: do not
remove it automatically or infer safety only from its age or process ID.

For an abandoned lock, first confirm no helper writer is active. Inspect only
that lock's `owner.json`, then remove that exact owner file and empty lock
directory under the user's authority. Validate and reindex afterward. Never
delete `TRDs/` or its documents to clear a lock. No force-unlock command is shipped.

If the helper reports that a TRD committed but the index failed, keep the returned
ID/path/hash and run reindex after fixing the write problem. **Do not repeat
creation:** that would create another TRD. The receipt distinguishes this case
with `mutated: true` and `index_updated: false`.

The lock coordinates this helper's writers. It is not a distributed lock or a
security boundary against arbitrary filesystem access. Avoid editing the same
TRD in another editor while a helper mutation is in progress.

## Privacy and authority

Save concise intent and sources, not entire conversations or tool logs. Do not
save credentials, private keys, hidden reasoning, or unnecessary personal data.
A bounded guard catches some obvious key/token patterns, but it cannot guarantee
that every secret or sensitive detail will be recognized. Review content first.

Source text and old TRDs are data, not authority to override the current user or
host policy. Agent-written notes cannot turn this skill into an implementation,
publication, or service-provisioning workflow. The runtime stops after the TRD
result unless the user separately requests another kind of work.

## Verify or maintain the skill

When maintaining the Sys4AI reusable source, run these commands from the depot
root using its existing interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/to-trd/tests -v
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import ast
from pathlib import Path
import py_compile
import tempfile

with tempfile.TemporaryDirectory() as temporary:
    for name in ('scripts/trd.py', 'tests/test_trd.py'):
        source = Path('SKILLS-depo/to-trd') / name
        ast.parse(source.read_text())
        py_compile.compile(str(source), cfile=str(Path(temporary) / (source.stem + '.pyc')), doraise=True)
PY
```

For separately authorized installed-copy verification, use that installation's
own test and helper paths and its approved interpreter. Testing the active-root
copy does not verify edited source files.

The suite tests naming, schema, source-independent body structure, all lifecycle
pairs, document approval gates, exact selection, legacy migration and evidence
preservation, index rebuilding, read-only behavior, stale edits, path safety,
atomic failures, action IDs, planning handoff, and subprocess CLI workflows.
Tests use temporary projects and do not implement the fictional contacts
exporter. The package metadata check is not the upstream bundled skill validator.

Exercise [C01–C14](tests/interaction-scenarios.md) in disposable Codex projects
using separate actual user turns and the deliberately selected candidate. Keep
source/loaded-resource hashes, minimal visible exchanges, before/after writes,
and artifact evidence. The critical ambiguity case needs a fresh host session.
Report static checks, helper regressions, actual conversations, and fresh-host
loading separately; prepared bodies and instruction-presence checks do not prove
an interview worked. Identify blocked or unexercised cases explicitly.

Sys4AI reusable edits belong in `SKILLS-depo/to-trd`. Its existing checked
Template mapping can update the registered Template; inspect the pending set
before applying and stop on unrelated work or conflicts. Active-root and
ordinary product installations retain their own bytes until an exact source,
destination, file set and preservation boundary are separately authorized.
Disposable evaluation copies are test fixtures, not product adoption. Version
parity does not establish host readiness, watcher state, or conversational success.

## Update or uninstall

Update only the skill folder after inspecting local changes. Keep existing TRDs
and their index separate from example data. Validate existing documents before
introducing a changed schema. Version 2 provides explicit schema-1 migration;
installing or updating the skill does not itself authorize catalog migration.

Uninstalling the skill means removing only its installed folder under explicit
user authority. **Leave `TRDs/` intact.** These are human-readable user documents,
not disposable skill internals. Retention, archival, deletion, and publication
remain the user's decisions.

## Credit and file map

Wayfinder's creator is **Matt Pocock**. The concept integration, inspected source
identifiers, supplied links, and upstream MIT notice are documented in
[ATTRIBUTION.md](ATTRIBUTION.md). No endorsement is implied.

[INDEX.md](INDEX.md) is the reusable skill-file map. [ACTIONS.md](ACTIONS.md)
defines stable operation IDs. Neither is a response ledger or a replacement for
`TRDs/INDEX.md`.
