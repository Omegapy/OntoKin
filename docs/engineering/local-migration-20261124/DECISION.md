# Owner direction: local development

**Date:** November 24, 2026 (America/Denver)
**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md)
**State:** Adopted owner direction, applied on the migration branch. It becomes
active project instruction when the reviewed migration is integrated into main.

## Authority

The project owner, on November 24, 2026:

1. approved the exact content of
   [TRD-20261124-E65C6113](../../../TRDs/trd_ontokin-local-development-migration_2026-11-24.md),
   revision 3, as the requirements for moving OntoKin's ordinary development to
   the existing local clone;
2. approved the implementation plan PLAN-20261125-CB551B16, revision 3, with its
   decisions as written; and
3. instructed: "execute PLAN-20261125-CB551B16".

This record states that direction. It adds no choice of its own.

## Decision

OntoKin's ordinary development runs in the owner's existing local clone and its
Git worktrees. The active operating instructions gain an explicit **local**
execution mode beside the existing **browser** mode.

- The mode is selected explicitly: it is declared by the entry document a
  session starts from and is recorded in the session checkpoint and the task
  record. It is never inferred from a path, a machine or an agent name.
- A local session starts from the local entry document and follows the local
  rules of REQ-017.
- A browser session starts from
  [CHATGPT-START-HERE.md](../../../CHATGPT-START-HERE.md) and follows the browser
  rules.

## Prospective effect

The change applies from its integration into main onward. It does not change how
any earlier session, handoff or check is read.

[PROTOCOL section 8](../../workflow/PROTOCOL.md#8-recovery-and-stopping) requires
a saved ZIP for every bounded browser phase "unless owner changes requirement".
For local sessions the owner has changed that requirement: a local session or
scope closes on a source checkpoint, a truthful task and session record, verified
push state when online, and durable evidence. A ZIP is optional unless the
selected task requires one.

The October 19 direction in
[OK-ENG-006](../OK-ENG-006-local-validation-and-hosted-ci-policy.md) stands:
local validation is the normal route, hosted workflows stay manual-only with a
default-false opt-in, and no paid execution is enabled.

## Rules that remain for browser sessions

These stay in force, with unchanged meaning, for every browser session:

- the entry point and startup read set in
  [CHATGPT-START-HERE.md](../../../CHATGPT-START-HERE.md);
- the ephemeral-host rule in
  [EPHEMERAL-HOST.md](../../workflow/EPHEMERAL-HOST.md);
- the early recovery ZIP, the verified saved handoff and the external receipt in
  [HANDOFF.md](../../workflow/HANDOFF.md);
- one declared phase for each thread, and the
  [browser prompts](../../workflow/BROWSER-PROMPTS.md).

## History that keeps its interpretation

Old handoffs, receipts, checks, failed observations and incomplete gates keep
their bytes and their original interpretation. No unfulfilled historical ZIP or
release gate is relabelled as passed because local sessions use another delivery
mechanism. C271 remains a separate, visibly unfinished scope, and its own
delivery requirements are reconciled explicitly when that scope is next selected.

## Limits

This decision changes no language semantics, expectation, numerical limit,
fixture, GOAL mission, invariant, budget or completion boundary. It selects no
product milestone, resumes no unfinished scope and authorizes no hosted or paid
execution.

## Decisions the owner approved with the plan

DEC-001 was settled when the owner approved the TRD and invoked planning from it.
The owner approved DEC-002 to DEC-012 as written, in conversation on November 24,
2026. The statements are copied unchanged from the plan, which is not committed.

| Decision | Statement |
| --- | --- |
| DEC-001 | The approved TRD-20261124-E65C6113 (revision 3, state trd_done) is this plan's requirements baseline: its REQ-001 to REQ-042 are carried with their IDs, wording, acceptance criteria and dependencies, and its decisions D01 to D11 apply unchanged, including that visual verification is not a completion condition and that proposed file names are not mandated. |
| DEC-002 | The migration uses the task ID LOCAL-MIGRATION-20261124, the branch work/local-migration-20261124 and the evidence directory docs/engineering/local-migration-20261124/, each confirmed unused at selection time; if one is taken, the next free variant is chosen and recorded. |
| DEC-003 | The development interpreter is the Homebrew CPython 3.12 installation, at the exact patch the TASK-001 inventory finds (3.12.13 at planning time); the uv-managed interpreters are not used. |
| DEC-004 | One tracked file, `tools/local-environment.json`, holds the exact interpreter patch, the profile definitions and the lock names for each platform; no `.python-version` file is added and its existing ignore rule stays. |
| DEC-005 | The macOS lock is `tools/native-reader-verification-macos-arm64-cp312.lock` in the existing lock's format, with wheel identities in an adjacent provenance record; hashes come from downloaded wheel bytes, are cross-checked against the Linux lock for the five platform-independent wheels, and are reviewed by a separate reviewer before first use. |
| DEC-006 | Local driver output and manually created worktrees live in directories beside the clone, outside the main checkout, and worktrees that the Claude application creates under `.claude/worktrees/` are covered by a targeted ignore rule; the reason is that the documentation verifier scans every non-dot directory under the repository root, including `build/`. |
| DEC-007 | The execution mode is declared by the entry document a session starts from and is recorded in the session checkpoint and the task record; the registry lists the browser and local entry points with their read sets; `CLAUDE.md` points to the local entry only for persistent local development. |
| DEC-008 | `docs/workflow/LOCAL-PROMPTS.md` is added as the concise user instructions for starting, continuing, recovering and checkpointing; no build-tool constraints file is added unless the installed-package check shows that the build cannot be reproduced from the recorded tool versions. |
| DEC-009 | For REQ-038 the existing durable mechanisms are GitHub for committed and pushed material and ChatGPT Library for the legacy handoff archives and receipts already saved there; no new backup service is set up; the restore check is the retrieval of the R06 handoff from the Library, verified against its recorded size and SHA-256; material that exists only on the local disk is reported to the owner. |
| DEC-010 | The fresh-session demonstration of REQ-029 is performed by the owner starting a new session in the Claude Desktop Code tab against the repository and giving the instruction Continue; the same session provides the REQ-019, REQ-020 and REQ-021 observations; a context-free subagent run may rehearse it but does not count as the demonstration. |
| DEC-011 | Integration waits for the reconciliation record: PHASE-006 depends on PHASE-002. If the R06 archive or its receipt is still unavailable when all other work is ready, work stops before integration and the owner decides whether to revise the plan. |
| DEC-012 | The approved TRD file and its index are committed unchanged on the migration branch so that the project task record can cite the requirements by path, and the `TRDs/` directory joins the local driver's source inventory; the `Implementation_Plans/` directory is not committed by this plan and stays in the main checkout, because the plan helper binds a plan to the project root it was created under. |
