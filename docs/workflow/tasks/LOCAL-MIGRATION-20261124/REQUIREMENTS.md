# LOCAL-MIGRATION-20261124 requirements

The requirements baseline is the approved [TRD-20261124-E65C6113](../../../../TRDs/trd_ontokin-local-development-migration_2026-11-24.md),
revision 3, SHA-256 `12e905a76da826f52e61c1237977a836750ce89260e208ba8553ebc8aeb28d76`.
It states each requirement, its sources, its acceptance criteria and its
dependencies in full. This file does not restate them; the titles below are the
TRD's own headings, and [task.json](task.json) records status and evidence.

## Authority

- The owner approved the TRD's exact content on 2026-11-24.
- The owner approved PLAN-20261125-CB551B16 with its decisions DEC-002 to
  DEC-012 as written, and then instructed on 2026-11-24:
  "execute PLAN-20261125-CB551B16".
- The decision record `docs/engineering/local-migration-20261124/DECISION.md`
  states the prospective owner direction (TASK-003).

## Scope

One migration scope from main `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` on
`work/local-migration-20261124`, tracked by
[scope issue 277](https://github.com/Omegapy/OntoKin/issues/277). The TRD's "In
scope" section governs.

## Exclusions

The TRD's "Out of scope" section governs. In particular this scope does not
resume or complete C271, add a container or LFS change, adopt another package
manager, change an adopted version, prepare the visual-verification profile,
enable hosted or paid execution, or change language semantics, expectations,
numerical limits, fixtures or GOAL's mission, invariants, budgets and completion
boundaries.

## Constraints

- C271's branch, pull request and issue are not merged, closed, completed or
  deleted, and none of its commits is taken.
- Historical evidence, receipts, handoffs and failed observations keep their
  bytes and their original interpretation.
- No expectation is changed to make a check pass. A new or worsened failure in
  released behaviour blocks integration; baseline failures are preserved.
- The repository is public: committed records hold no credential, account name
  or home-directory path, and machine-specific paths stay in ignored local files.
- Independent review needs an actual separate reviewer.
- Main integration is serialized through the verified lease and the
  expected-head, non-force procedure.

## Requirements

| ID | TRD title | Plan steps |
| --- | --- | --- |
| REQ-001 | Adopt the existing clone from an observed inventory | TASK-001 |
| REQ-002 | One distinct migration scope in the existing task system | TASK-002 |
| REQ-003 | Native CPython 3.12 virtual environment as the default | TASK-009, TASK-013, TASK-035 |
| REQ-004 | Environments are reused, never silently rebuilt or copied | TASK-011, TASK-013, TASK-028 |
| REQ-005 | Dependency profiles with separately reported readiness | TASK-009, TASK-016 |
| REQ-006 | Platform-specific verification locks | TASK-004, TASK-010, TASK-034 |
| REQ-007 | python-verification readiness from the adopted exact versions | TASK-013, TASK-027 |
| REQ-008 | Visual verification prepared only when selected, on the documented toolchain | TASK-004, TASK-011, TASK-012, TASK-016, TASK-034 |
| REQ-009 | Nothing is added beyond the adopted specifications | TASK-009, TASK-016, TASK-031 |
| REQ-010 | Definite container decision: native by default | TASK-016, TASK-031 |
| REQ-011 | Idempotent, profile-specific bootstrap | TASK-011, TASK-013, TASK-027 |
| REQ-012 | Non-mutating doctor | TASK-012 |
| REQ-013 | Reproducibility records for every environment | TASK-009, TASK-013, TASK-014 |
| REQ-014 | Setup is repeatable and documented | TASK-016, TASK-017, TASK-028, TASK-035 |
| REQ-015 | Installed-package behaviour proven outside the checkout | TASK-014 |
| REQ-016 | Explicit local and browser execution modes, adopted prospectively | TASK-003, TASK-017, TASK-018, TASK-021 |
| REQ-017 | Local-mode rules replace the browser-only rules for local sessions | TASK-017, TASK-018 |
| REQ-018 | The amendment is coherent across every instruction surface | TASK-017, TASK-018, TASK-021, TASK-022, TASK-024, TASK-027, TASK-031 |
| REQ-019 | One shared instruction authority, a local entry point and a thin Claude adapter | TASK-019, TASK-020, TASK-030 |
| REQ-020 | Skills stay shared, linked and explicitly invoked | TASK-004, TASK-022, TASK-030, TASK-034 |
| REQ-021 | The owner's graphical workflow works end to end | TASK-030 |
| REQ-022 | One canonical task and acceptance system | TASK-024, TASK-025, TASK-031, TASK-036 |
| REQ-023 | "Go" or "Continue" resumes the selected scope | TASK-019, TASK-030 |
| REQ-024 | Local session startup procedure | TASK-019, TASK-030 |
| REQ-025 | Work conduct, blockers and interruption recovery | TASK-018, TASK-029 |
| REQ-026 | Session checkpoints carry what a successor needs | TASK-023, TASK-029 |
| REQ-027 | Compact current pointers, complete history | TASK-024, TASK-025, TASK-036 |
| REQ-028 | Workflow and validation tools follow the adopted structure | TASK-025, TASK-026, TASK-027 |
| REQ-029 | A fresh agent session resumes from the repository alone | TASK-019, TASK-030 |
| REQ-030 | Main, C271, the R06 handoff and the local clone are reconciled | TASK-005, TASK-007, TASK-024 |
| REQ-031 | Legacy archives are verified before use and never overlaid | TASK-006, TASK-007 |
| REQ-032 | Unique accepted evidence and historical records are preserved exactly | TASK-004, TASK-006, TASK-007, TASK-034 |
| REQ-033 | C271 stays a separate, visibly unfinished scope | TASK-004, TASK-005, TASK-024, TASK-034 |
| REQ-034 | Ordinary local Git is the publication route | TASK-001, TASK-033 |
| REQ-035 | Safe parallel work | TASK-018, TASK-028 |
| REQ-036 | Evidence is attributable to the actual source and environment | TASK-015, TASK-026, TASK-027 |
| REQ-037 | The no-payment hosted-CI policy is preserved | TASK-017, TASK-027 |
| REQ-038 | Durable storage and backup of unique material | TASK-006, TASK-008 |
| REQ-039 | Git LFS is left as it is | TASK-004, TASK-034 |
| REQ-040 | Independent review of the exact candidate | TASK-032 |
| REQ-041 | Integration and cleanup through the established lifecycle | TASK-033, TASK-034 |
| REQ-042 | Readiness, completion and qualification are reported separately | TASK-012, TASK-031, TASK-036 |

## Inputs that only the owner can supply

- The R06 transfer-capability handoff archive and its delivery receipt, placed on
  the local machine (TASK-006; REQ-030 and REQ-031 stay open until then).
- A fresh session in the Claude Desktop Code tab with the instruction "Continue"
  (TASK-030).
