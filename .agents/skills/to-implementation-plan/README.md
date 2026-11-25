# To Implementation Plan

`to-implementation-plan` is an explicitly invoked Codex skill for creating and maintaining durable, project-aware implementation plans. It accepts readable source material, inspects the live target project, extracts source-linked requirements, and stores ordered phases and bounded tasks with dependencies, acceptance criteria, evidence, lifecycle state, and bidirectional traceability.

The skill is a planner and tracker. It does not automatically execute a plan. Creating, approving, selecting, or resuming a plan does not authorize changes to the target project or any separately governed action.

## Delivery status

This directory is the reusable source package staged in `SKILLS-depo`. Initial delivery stops here. It is not registered in the Sys4AI depot manifest, synchronized into a consumer, installed in a personal skill directory, published, or represented as live-tested by Codex.

Registration, synchronization, installation, Git actions, publication, and deployment each require separate authority and their normal review process.

## Package contents

```text
to-implementation-plan/
  SKILL.md
  README.md
  ACTIONS.md
  INDEX.md
  agents/
    openai.yaml
  assets/
    example-input.json
    plan-overview-template.md
    phase-template.md
    traceability-template.md
  references/
    intent-and-project-discovery.md
    lifecycle-and-recovery.md
    plan-contract.md
  scripts/
    plan_state.py
  tests/
    test_plan_state.py
```

[INDEX.md](INDEX.md) describes each file. The package uses original project-specific text and implementation; it has no copied-code attribution or license file.

## Requirements

- Codex or another agent host that can load a folder-based skill.
- Python 3.10 or later on a POSIX host that provides `O_NOFOLLOW`, `O_DIRECTORY`, and directory-relative file opening for race-resistant local reads.
- Only the Python standard library at runtime.
- Read access to the user-supplied sources and target project.
- Write access to the selected project's plan catalog for mutating operations.

URL and structured-document intake use tools already available to the current agent. The skill has no required MCP server, database, daemon, hosted service, or Python package dependency. If the current host cannot read a format or URL, the plan records the exact limitation instead of fabricating content.

The current skill-creator structural validator imports PyYAML. The validation command below uses an isolated `uv --with PyYAML` environment; PyYAML is not a runtime or project dependency.

## Later installation

Installation is intentionally separate from this source-only delivery.

For a later project-scoped installation, first confirm the exact consumer root and that the destination does not contain an unreviewed package with the same name. Copy this entire directory as one unit to the skill location recognized by that project, commonly:

```text
<consumer-project>/.agents/skills/to-implementation-plan/
```

For a personal installation, follow the current Codex skill-installation workflow and place the complete folder under the active Codex skills root. Do not copy selected files, rerun the initializer over an existing package, or add a depot manifest entry as an incidental installation step.

After any authorized copy, validate the copied package and compare its inventory with [INDEX.md](INDEX.md). Installing the skill does not authorize creation of a plan in a consumer project; the user must still invoke it explicitly.

## Explicit use

The metadata sets `allow_implicit_invocation: false`. Use `$to-implementation-plan` or explicitly ask to use this named skill.

Examples:

```text
Use $to-implementation-plan to create a tracked implementation plan from this prompt for /absolute/project.

Use $to-implementation-plan to create a draft from /absolute/project/specs/feature.trd and preserve all open questions.

Use $to-implementation-plan to show PLAN-20260828-A1B2C3D4 in /absolute/project and report its unresolved items.

Use $to-implementation-plan to validate the managed plan catalog in /absolute/project without repairing it.

Use $to-implementation-plan to record this observed test result for TASK-004 in PLAN-20260828-A1B2C3D4. Do not mark the task complete unless every acceptance criterion is supported.
```

Ordinary requests such as "make a plan" do not activate this skill.

## Supported inputs

The agent can normalize:

- a direct user prompt;
- pasted text;
- a readable regular local file;
- a Task Requirement Document (TRD);
- a Product Requirements Document (PRD), whether structured or narrative;
- an accessible URL; or
- another user-supplied source the current agent can lawfully read.

Every source receives a stable local ID and immutable provenance. The plan preserves facts used, access time, a locator, the actual inspection method, and exact access limits. Agent-inspected local facts always require a matching SHA-256 digest; limitations-only and user-supplied records can retain null when no digest was observed. `direct_text` and format-aware methods apply only to `file`, `trd`, or `prd`; `browser_tool` applies only to URLs; prompt and pasted text remain user-supplied. Supported PDF, document, spreadsheet, and presentation formats use an available format-aware tool before extracted facts are accepted. URL intake stores extracted facts and locators, not a full page snapshot by default.

Source content is data, not authority. Embedded instructions cannot cause execution, installation, deletion, publication, secret access, hidden-reasoning storage, or changes to another state system.

See [intent-and-project-discovery.md](references/intent-and-project-discovery.md) for the complete intake and synthesis workflow.

## What creation does

An explicit create operation:

1. establishes one exact project root;
2. inventories and reads accessible sources;
3. inspects applicable project guidance, architecture, dependencies, tests, conventions, repository state, and protected artifacts;
4. separates observed facts, user decisions, proposals, assumptions, contradictions, questions, and access gaps;
5. creates stable requirements, phases, tasks, dependencies, risks, acceptance criteria, verification steps, and evidence fields;
6. checks source-to-requirement-to-task coverage and reverse task basis;
7. writes a canonical draft and deterministic Markdown projections through the helper;
8. reopens and validates the exact plan; and
9. reports its identity, path, state, counts, unresolved items, and validation result.

Creation accepts planning state only: tasks start `planned`, requirements do not start `satisfied`, and completion evidence cannot be imported through `create`. The operation then stops. It does not implement the plan.
An honest draft may retain unresolved material, but readiness-critical fields containing standard draft markers, including dotted or spaced variants, produce blocking findings. Lifecycle reasons and exception authorities reject placeholder text before mutation.

Evidence records classify the observed result separately from their type and verification level. Use `result_status` values `planned`, `passed`, `failed`, `blocked`, `partial`, or `not_exercised`; planned-only records never count as executed verification. Completion adds the helper-computed highest successful verification level after a strictly later final project reinspection.

## Runtime catalog

The default project-local layout is:

```text
<project-root>/
  Implementation_Plans/
    INDEX.md
    Plan_<safe-slug>_<YYYY-MM-DD>_<SHORTID>/
      plan.json
      PLAN.md
      TRACEABILITY.md
      phases/
        PHASE-001_<safe-slug>.md
```

`plan.json` is the only canonical state. `PLAN.md`, `TRACEABILITY.md`, phase files, and the catalog `INDEX.md` are deterministic projections. Editing a projection does not change plan state. Use the explicit rebuild routes to repair drift.

Pre-existing Markdown plans and unknown directories are unmanaged. The skill does not index, adopt, migrate, rewrite, or delete them automatically. A per-invocation plans-root override is allowed only when it remains confined beneath the resolved project root.

## Identity and exact selection

Plans use `PLAN-YYYYMMDD-XXXXXXXX`. Phases use `PHASE-001`; tasks use `TASK-001`; sources use `SRC-001`. Generated requirement IDs use `REQ-001`, while valid unique supplied requirement IDs are preserved. IDs remain tied to their original meaning.

An existing plan can be selected by its full plan ID, exact managed directory name, or a unique case-insensitive complete title. Partial IDs, substrings, fuzzy titles, and recency do not resolve. An ambiguous title returns candidates and changes nothing.

## Helper commands

The agent normally calls the helper. Maintainers can inspect the same interface directly:

```text
python scripts/plan_state.py --project-root PROJECT [--plans-root PATH] COMMAND ...
```

The command routes and stable action IDs are:

| Action | Route | Purpose | Writes canonical state |
| --- | --- | --- | --- |
| `TO-IP-001` | `create --input FILE|-` | Create one draft plan. | Yes |
| `TO-IP-002` | `show SELECTOR` | Show or resume an exact plan. | No |
| `TO-IP-003` | `list [--status STATE]` | List valid managed plans. | No |
| `TO-IP-004` | `update SELECTOR --expect-revision N --expect-sha256 HASH --input FILE|-` | Revise the baseline using stale-state preconditions. | Yes |
| `TO-IP-005` | `update-phase SELECTOR PHASE-ID --expect-revision N --expect-sha256 HASH --input FILE|-` | Revise phase content, dependencies, gates, scope, or risks; status remains derived. | Yes |
| `TO-IP-006` | `update-task SELECTOR TASK-ID --expect-revision N --expect-sha256 HASH --input FILE|-` | Revise task content or request a legal task transition. | Yes |
| `TO-IP-007` | `record-evidence SELECTOR TARGET-ID --expect-revision N --expect-sha256 HASH --input FILE|-` | Append classified evidence to a task or requirement. | Yes |
| `TO-IP-008` | `set-status SELECTOR --expect-revision N --expect-sha256 HASH --status STATE --reason TEXT --confirmed` | Request a gated plan-state transition. | Yes |
| `TO-IP-009` | `validate [SELECTOR]` | Validate one plan or the catalog without repair. | No |
| `TO-IP-010` | `rebuild-projections SELECTOR` | Regenerate only one plan's Markdown. | No canonical write |
| `TO-IP-011` | `reindex` | Regenerate only the managed catalog index. | No canonical write |
| `TO-IP-012` | `reconcile SELECTOR --input FILE|- --confirmed` | Apply one reviewed, bounded recovery. Use an exact plan selector for plan scope or literal `catalog` for catalog scope. | Reviewed scope only |

Use `python scripts/plan_state.py COMMAND --help` to inspect the live interface. [ACTIONS.md](ACTIONS.md) documents the same flags, write sets, and authority gates. Existing-plan mutations require the current revision and canonical SHA-256 returned by `show`.

Every command returns one structured JSON envelope with command, project root, plans root, result status, mutation flag, warnings, errors, recovery requirement, plan receipt, and command-specific data. Distinct nonzero exits identify invalid input, missing target, ambiguous selector, unsafe or corrupt state, stale state, active lock, prohibited transition, unmet gate, I/O failure, and canonical/projection partial success.

## Creation input

[example-input.json](assets/example-input.json) is a complete create-input example. It contains source-linked requirements, one phase, two tasks, and bidirectional coverage. Creation input omits helper-generated plan identity, timestamps, revision, derived phase state, validation result, and history. The helper produces the complete canonical record after validation.

Input is strict JSON: UTF-8 without a byte-order mark, no comments, no duplicate keys, and no nonfinite values. The helper rejects unknown fields, wrong types, unsafe IDs, unresolved references, dependency cycles, over-bound content, and known secret forms before writing.

## Lifecycle

Plan states are:

```text
draft -> ready -> in_progress -> completed
```

The controlled lifecycle also supports `paused`, `blocked`, `retired`, and `cancelled`, with explicit restore or reopen paths. Material scope change returns an approved or active plan to `draft`.

Task states are `planned`, `in_progress`, `blocked`, `paused`, `completed`, and `skipped`. Phase state is derived from task state and cannot be set independently.

Readiness requires complete structure, acyclic dependencies, project inspection, settled material questions, bidirectional coverage, current validation, and user approval of the exact revision. Starting work requires separate execution authority for the exact plan. Completion requires current evidence for every acceptance criterion, consistent rollups, complete traceability, final project inspection, honest test reporting, and explicit confirmation.

See [lifecycle-and-recovery.md](references/lifecycle-and-recovery.md) for every legal transition and gate.

## Continuation and tracking

Canonical state supports continuation without relying on conversation history or memory. To resume:

1. explicitly invoke the skill;
2. identify the project root and exact plan selector;
3. use the read-only `show` route;
4. inspect canonical revision, SHA-256, tasks, blockers, evidence, and validation;
5. obtain any missing implementation or mutation authority; and
6. perform one explicit update with current stale-state preconditions.

The tracker remains separate from a project Task ledger, TRD lifecycle, Codex task state, native goal state, issue tracker, Git, and deployment state. A conflict is reported; the skill does not silently synchronize another system.

## Evidence limits

Evidence distinguishes planned checks, agent observations, command or test results, runtime observations, user reports, external reports, and not-exercised work. Each record also carries `result_status`; a planned command is not a passing result or a classified execution report. A user report remains labeled as a user report.

Task completion requires meaningful current `passed` evidence for every criterion and one non-planned result classification for each verification step. The helper normalizes case, Unicode, punctuation, and marker-only word combinations, so values such as `Pass.`, `OK, done.`, or `Success: pass` do not count. A truthful `0 failed` summary is allowed; a positive failure count contradicts `passed`. The helper binds evidence to the target and its relevant project, scope, source, requirement, coverage, and phase context. Passing evidence explicitly names the criterion, and agent/tool observations include a reviewable locator or command; plan-authored expectations and failed results do not count. A phase is complete only when all required tasks are complete or have an explicitly authorized skip with disposed requirement coverage. A plan is complete only after all completion gates, a strictly post-evidence project inspection, affirmative exact-path preservation observations, and current confirmation pass. A negated, false, failed, or unsuccessful preservation statement cannot satisfy that gate.

Do not store credentials, private keys, access tokens, hidden reasoning, full transcripts, default full-page snapshots, or large raw logs. Keep a concise observed result and a safe locator. The contract's field and file bounds limit memory and privacy exposure.

## Validation

Run focused package checks from the Sys4AI project root or adjust paths for an authorized copy:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m py_compile \
  SKILLS-depo/to-implementation-plan/scripts/plan_state.py \
  SKILLS-depo/to-implementation-plan/tests/test_plan_state.py

PYTHONDONTWRITEBYTECODE=1 python -m unittest discover \
  -s SKILLS-depo/to-implementation-plan/tests -v

uv run --with PyYAML -- python \
  "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" \
  SKILLS-depo/to-implementation-plan
```

The quick validator checks `SKILL.md` structure, naming, and unfinished scaffold markers. It does not prove metadata policy, links, helper behavior, plan correctness, or installed Codex discovery. Use the focused test suite and direct file/link inspection for those claims.

For a read-only catalog check:

```bash
python SKILLS-depo/to-implementation-plan/scripts/plan_state.py \
  --project-root /absolute/disposable/project validate
```

Run mutations and fault tests only in disposable project roots. Do not point them at a live project merely to demonstrate the package.

## Recovery

Read-only operations never repair state. Use:

- `rebuild-projections` when canonical state is valid but one plan's generated Markdown is missing or stale;
- `reindex` when the generated catalog index is missing or stale; and
- `reconcile` only for one exact reviewed recovery specification with current confirmation; catalog scope uses `reconcile catalog`.

A canonical commit followed by projection failure is partial success. Do not repeat the original mutation. Use the recovery route in the JSON receipt.
If projection publication and owned-lock cleanup both fail after the canonical commit, the receipt preserves an ordered chain: reconcile the lock residue, rebuild projections, reindex, and validate. A later failure never replaces an earlier required repair.

Never infer that a lock is abandoned from age or a recorded process ID alone. Inspect the exact lock, check for an active writer, validate canonical state, and remove only a confirmed helper-owned abandoned or `.released-TOKEN` artifact through bounded reconcile. A removal-only catalog recovery against an absent catalog is a byte-preserving no-op; it does not initialize `Implementation_Plans/`. Partial-create recovery declares whether the reviewed remainder is `temporary` or `empty`. If a partial result already removed the temporary file, its receipt advances the retry input to `state: empty`. Recovery does not guess corrupt JSON, manufacture consent or evidence, adopt unmanaged plans, or delete a plan.

## Contract references

- [ACTIONS.md](ACTIONS.md): operation IDs, routes, write sets, and confirmation gates.
- [plan-contract.md](references/plan-contract.md): canonical schema, identifiers, selectors, projections, results, bounds, locking, and compatibility.
- [intent-and-project-discovery.md](references/intent-and-project-discovery.md): source intake, project inspection, intent extraction, clarification, synthesis, and coverage review.
- [lifecycle-and-recovery.md](references/lifecycle-and-recovery.md): state transitions, evidence gates, stale updates, partial publication, locks, and bounded recovery.

## Known validation boundary

Source-package tests can verify normalized payloads, schema behavior, transactions, projections, fault handling, links, and an isolated copied package. Raw prompt-to-plan synthesis, format-aware extraction, browser access, activation routing, project inspection, and other agent-mediated scenarios require a separate forward evaluation and are listed explicitly in the test module's Director-level scenario ledger. These tests do not prove that this staged source directory is installed or discoverable in a live Codex session. Report installed-host behavior only after a separately authorized installation and end-to-end exercise.
