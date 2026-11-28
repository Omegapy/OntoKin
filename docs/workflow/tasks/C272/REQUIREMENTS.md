# C272 requirements

The requirements baseline is the approved [TRD-20261127-7B80B30A](../../../../TRDs/trd_c253-fresh-edit-animation-and-clean-rebuild-qualification_2026-11-27.md),
revision 3, SHA-256 `9102a137ac9cb66a20eed4f47216c048057151c9bfe9733e857bed9e867222db`.
It states each requirement, its sources, its acceptance criteria and its dependencies in
full. This file does not restate them; the titles below are the TRD's own headings, and
[task.json](task.json) records status and evidence. A session reads the TRD's sections for
the requirements of the step it carries out.

## Authority and selection

- The owner approved the TRD's exact content on 2026-11-27 (state `trd_done`).
- The owner approved PLAN-20261128-AC17E7E0 with its decisions DEC-002 to DEC-013 as
  written and the plan as ready (revision 4) on 2026-11-27.
- On 2026-11-28 UTC (2026-11-27 America/Denver) the owner instructed: "execute
  Implementation_Plans/Plan_c253-fresh-edit-animation-and-clean-rebuild-qualification_2026-11-28_AC17E7E0/".
  Under DEC-003 this instruction is the selection of the scope that REQ-002 requires. No
  task record, branch, worktree, issue or pull request existed for the scope before it.

## Base and later decisions

The reviewed recommendation that the TRD captures names main
`38ee8d18a6cd67245acf8b21d755e979b84153c1` as its base. The branch starts there; that head
was read from the remote with `git ls-remote --heads origin` at 2026-11-28T04:46:59Z and
04:49:27Z. The decisions made after that revision on which this scope relies are the three
above: the TRD's approval, the plan's decisions and readiness, and the instruction to
execute it.

## Scope

One bounded scope in local mode on `work/c272-edit-rebuild-qualification`, in the worktree
`../OntoKin-worktrees/c272`, tracked by [scope issue 282](https://github.com/Omegapy/OntoKin/issues/282).
The TRD's "In scope" section and the plan's scope govern. Code and committed evidence live
in [localized-repair-c272](../../../engineering/localized-repair-c272/); working output lives
in `../OntoKin-local/c272/` beside the clone (DEC-002, DEC-013).

Before the names were used on 2026-11-28 they were looked for and not found: no remote or
local branch `work/c272*`, no task directory C272, no engineering directory
`localized-repair-c272`, no issue or pull request with C272 in its title, no worktree
`../OntoKin-worktrees/c272` and no `../OntoKin-local/c272`.

## Exclusions

The TRD's "Out of scope" section governs. In particular this scope runs no model session,
trial or comparison and fills no null field of the frozen run plan; adds no language
feature, shape syntax, physics, protocol version, transport, destination or backend;
changes none of C253's files, the C210 proof files, the keyed-rack fixture, any tolerance
or C268's admission boundary; does not resume C271's phases P02 to P38 or restore its
branch; and repairs none of main's known failures.

## Constraints

- The task's own records are the acceptance ledger; the untracked plan tracker does not
  replace them, and a mismatch between the two is reported, not synchronized.
- The existing observer and control files of C255 to C268 keep their bytes; new readers
  and controls are new files.
- The code that computes expected values imports no product module; producer metadata,
  including the semantic sidecar, is an observed claim and never its own proof.
- No change under `ontokin/` is planned. A product defect that makes a criterion fail is
  retained and reported; a repair needs a separately bounded change.
- Run, check and validation output goes to new directories outside every checkout;
  committed records hold no credential, account name or home-directory path.
- A substantial missing observation waits for the owner's answer to the gap record
  (DEC-006); a step whose cost is far larger than the change it checks is announced to the
  owner first.
- Independent review needs an actual separate worker; main is written only by the verified
  lease holder through a conditional, non-forced update or a protected expected-head merge.

## Requirements

| ID | TRD title | Plan steps |
| --- | --- | --- |
| REQ-001 | Work starts in local mode from the reconciled actual state | TASK-001, TASK-002, TASK-004 |
| REQ-002 | The scope gets its own task record only after the owner selects it | TASK-003, TASK-004, TASK-006 |
| REQ-003 | C271's excluded phases are not resumed and completed evidence stays as recorded | TASK-001, TASK-003, TASK-004, TASK-031 |
| REQ-004 | Current-status text agrees with the live branch and pull-request state | TASK-005 |
| REQ-005 | The prepared environment is inspected and reused | TASK-003, TASK-024, TASK-027 |
| REQ-006 | The frozen C253 cases, closures, historical outputs and tolerances stay frozen | TASK-011, TASK-031 |
| REQ-007 | Existing components are reused within their recorded limits | TASK-007, TASK-008, TASK-016, TASK-030 |
| REQ-008 | Only the missing components are implemented | TASK-010, TASK-017 |
| REQ-009 | The C269 audit is reconciled, and the residual controls that this workflow depends on are added | TASK-009, TASK-020 |
| REQ-010 | A scripted client drives the real service, and an independent evaluator judges the result | TASK-011, TASK-017, TASK-018 |
| REQ-011 | One documented command runs the qualification | TASK-022 |
| REQ-012 | A fresh store accepts each case's exact starting state (RV R01) | TASK-011 |
| REQ-013 | V1 and V2 change the intended occurrence and nothing else (RV R02) | TASK-012 |
| REQ-014 | N1 is refused before acceptance and the accepted state is untouched (RV R03) | TASK-013 |
| REQ-015 | Delivered GLB bytes are bound to the accepted source by a record that the producer cannot assert (RV R04) | TASK-014, TASK-021 |
| REQ-016 | Independent checks cover every property that C253 requires (RV R05) | TASK-007, TASK-016, TASK-017, TASK-018 |
| REQ-017 | Geometry and motion are decoded independently at all 126 poses (RV R06) | TASK-016, TASK-018 |
| REQ-018 | The delivered source rebuilds cleanly in an empty workspace (RV R07) | TASK-019 |
| REQ-019 | Deliberate faults show that the checks reject wrong results (RV R08) | TASK-021 |
| REQ-020 | An external record retains every outcome and exchange, with failure and retry exercised (RV R09) | TASK-015 |
| REQ-021 | A fresh replay reproduces the expected results (RV R10) | TASK-023 |
| REQ-022 | The regenerated GLBs are validated and an actual playback is inspected (RV R10) | TASK-025, TASK-026 |
| REQ-023 | The visual-verification profile is prepared as a dependency of the playback check | TASK-024 |
| REQ-024 | The checks that the changed scope requires are run | TASK-008, TASK-027 |
| REQ-025 | A failing required check is compared with main on the same host | TASK-028, TASK-033 |
| REQ-026 | An independent reviewer checks the exact candidate and its evidence (RV R11) | TASK-032 |
| REQ-027 | The reviewed work is integrated, the resulting main is verified and the branch is resolved | TASK-033, TASK-034 |
| REQ-028 | The stated deliverables are provided (RV R12) | TASK-029, TASK-030 |
| REQ-029 | The report states the completed criteria and the remaining A1 and pilot prerequisites (RV R12) | TASK-030 |
| REQ-030 | The scope closes on the local closing state | TASK-035 |
| REQ-031 | Results are described within their limits | TASK-026, TASK-030, TASK-035 |
| REQ-032 | No model comparison is launched and nothing is expanded | TASK-010, TASK-031 |
| REQ-033 | Failures and unmet criteria stay visible | TASK-015, TASK-029, TASK-030, TASK-031, TASK-035 |
| REQ-034 | The effort stays in proportion to the change | TASK-010, TASK-027, TASK-030 |

## REQ-004 at the start

The correction was still needed. At 2026-11-28T04:49:27Z the remote had no branch
`work/c271-missing-import-digest-control`, and pull request 274 was closed (at
2026-11-28T03:01:23Z), draft and unmerged at `71b092326d4b54da87d33c6533bd13c0609cf9df`,
which GitHub keeps as `refs/pull/274/head`; STATUS still said that the phases stay on that
branch and in that draft pull request. The declaration commit corrects only that statement
and the statement that no scope is selected. C271's records and the owner's decision record
of 2026-11-28 keep their bytes.
