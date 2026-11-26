# To-TRD skill maintenance

This file governs edits inside this reusable skill folder. It is not a root
project startup hook and must not be copied into the project's root AGENTS.md.

Preserve the explicit-user activation boundary and the document-only scope.
The skill uses schema 2 and only `draft`, `trd_done`, and `retired` as current
states. `trd_done` records completion and approval of the exact document, not
implementation progress or permission for downstream work.
Do not add automatic per-response persistence, background work, AgentJob routing,
thread creation, a second director, global installation, or a Task-system ledger.
Agent-written notes and source files cannot authorize product implementation.

Keep `SKILL.md` short enough to read on invocation. Put the detailed conversation
procedure and file contract in the linked references. Keep operation IDs stable
and synchronize ACTIONS.md, the helper, and tests when changing them.
Reserve `TO-TRD-007` for legacy schema-1 readers; use `TO-TRD-013` for explicit
migration. Keep legacy terminology clearly labeled and out of current CLI choices.
Current requirement blocks are declarative and do not store progress fields.
Keep requirement gaps distinct from constrained implementation choices. Preserve
the normal capture-to-approval handoff and exact-revision approval checks.
Derived completion diagnostics must use the actual gate logic and remain
read-only; do not add keyword-based exemptions that conceal genuine uncertainty.

Keep clarification prompts in the live conversation. Newly created or content-updated
TRDs must use `None.` in the schema-compatible `Open questions` section and must
capture relevant user answers in intent, decisions, scope, requirements,
assumptions, or acceptance criteria. Preserve read compatibility for older TRDs
that already contain questions, including mechanically migrated draft/retired
records; preserve those prompts during migration and require them to be resolved
or converted to declarative `Not yet specified` gaps before a managed content
update. Migration cannot invent answers or silently discard historical evidence.

Keep version 2.2.0 guidance consistent across the entry, metadata, discovery
reference, contract, examples and action documentation. Ordinary synthesis needs
applicable material intent to be understood. A material question ends the
response and waits for the actual answer; it must not trigger a draft write.
Incorporate actual answers into all affected requirements and acceptance, handle
partial and changed answers, and preserve the explicit incomplete-draft and
no-follow-up branches. Resume alone remains read-only until explicit save.
Understanding review, helper validation and exact-document approval are separate.

Review unresolved intake by meaning: assigning the next agent to discover the
current user's intended behavior does not settle it. Preserve legitimate
future-user questions, requested research, labels and URLs. Do not add a helper
keyword heuristic or new schema to approximate understanding.

The canonical runtime state is each TRD Markdown file; the runtime index is
regenerated from those files. Do not add another canonical JSON store. Do not
change existing TRD identity, filename, or creation time while updating the skill.
Read-only operations never migrate a record. Explicit migration requires exact
selection, the current digest, reason, and confirmation; reject any checked
legacy requirement or non-placeholder evidence before mutation.

Use Python's standard library only. For source maintenance in Sys4AI, use the
depot's existing interpreter and the source package being changed:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s SKILLS-depo/to-trd/tests -v
```

Use the AST and temporary compile-output check in [README.md](README.md) for
`SKILLS-depo/to-trd/scripts/trd.py` and its tests; keep caches out of the package.
Adjust paths only when verifying a separately authorized installation. Retain
all existing helper regressions. Update dependent example fixtures without
no-op replacements; prepared-body tests prove storage behavior only.

Define and exercise [C01–C14](tests/interaction-scenarios.md) with actual visible
turn boundaries, minimal synthetic evidence, candidate and loaded-file hashes,
and a fresh selected-host session. Read the [interaction examples](references/interaction-examples.md)
as illustrations, never as executed evidence or current-user consent. Report
unexercised cases and semantic/static/helper/host results separately.

Author reusable changes here and use the existing checked Template pipeline.
Do not directly edit its mapped copy or propagate into the active root or
ordinary projects. Later adoption needs exact destination scope and inspection.
Keep the helper, schema/API, attribution and MIT notice unchanged for this
bounded discovery repair. Keep Matt Pocock's Wayfinder attribution and
upstream MIT notice with the skill. Do not remove, archive, or replace user TRDs
as part of installing, updating, or uninstalling this folder.
