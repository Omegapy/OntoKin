# Closing report: local development migration

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
TASK-036, 2026-11-25. Three different results are reported apart: environment readiness, task
completion and product qualification.

## Changes

- An explicit local execution mode beside the browser mode across the instruction surfaces, with a
  local entry document, prompts, a thin Claude adapter, an extended session template and a compact
  CURRENT that links its history. Browser sessions keep their rules.
- A tracked environment specification, a reviewed macOS arm64 lock, a setup tool and a doctor with
  tests, and a setup guide. Linux lock, pins, npm files, LFS rules and the root ignore file are
  byte-identical.
- The reconciliation of main, C271, the verified R06 handoff and the clone, and a storage record.

Merged by [PR278](https://github.com/Omegapy/OntoKin/pull/278) as `8e847c15e41c7e5970581993c465690526cd43d2`: 37 files
added, 21 modified, none deleted ([integration](INTEGRATION.json), [disposition](BRANCH-DISPOSITION.json)).

## Checks actually run

| Where | Result |
| --- | --- |
| Independent review of the exact candidate | Accepted in the second round, with three minor findings ([review](REVIEW.md)) |
| Resulting main: documentation verifier, workflow check, 307 focused tool tests with a resolved temporary directory | Passed |
| Resulting main: routine driver, two temporary-directory settings | Overall status **failed**, unchanged: of 4,989 unit tests one and 307 do not pass, exactly those of the unmodified base; every other step passes. No new or worsened failure |
| Pending, as before | 16 external cases; three readback tests skipped |
| Not run | `--full`, `--force-agent`, hosted CI, Linux |

## Environment readiness

| Profile | Main checkout |
| --- | --- |
| `core`, `python-verification` | ready ([record](MAIN-ENVIRONMENT.json)) |
| `visual-verification` | mismatch: Node.js 25.9.0 is installed, the target is 22; not prepared |
| `package-smoke` | not checked by the doctor; proven at `3fd7b922` by [its record](PACKAGE-SMOKE.json) |
| `historical-native` | not checked |
| `linux-container` | unsupported |

## Task completion

All 36 steps are closed and all 42 requirements are accepted, two of them with parts that were not
observed and that the owner waived on 2026-11-25:

- REQ-021: the application's Worktree mode;
- REQ-024: a startup report before the first change in an unguided session.

The plan tracker PLAN-20261125-CB551B16 stops at TASK-030, because removing a criterion there would
return the approved plan to draft; the [ledger](../../workflow/tasks/LOCAL-MIGRATION-20261124/task.json) is
the acceptance record.

Accepted by the owner on 2026-11-25: earlier commits of the branch, now in main's history, hold
details of the machine's protection that the current files leave out. The question named disk
encryption and backup software; the old lines also name the permissions of the GitHub account.

## Product qualification

Unchanged. Nothing here is a language, native, destination or release pass. The successful
installation does not complete C271, whose gates stay open on its own branch and draft
[PR274](https://github.com/Omegapy/OntoKin/pull/274).

## Retained blockers and remaining work

| Item | Next action |
| --- | --- |
| C271, blocked at P29-PUBLICATION-SIZE-001 | A separately selected scope; ordinary authenticated Git is a publication route that failed connector transfers are not |
| One unit test differs in the last digit of regenerated fixture values | A separately selected scope, on a second platform as well |
| Setup tool: a FIFO or a loop of links named by a Node.js process (review r-1), and older misses of use detection | A separately selected correction; relevant only with `--repair-node` |
| Node.js 22 for `visual-verification` | Only when that profile is selected |
| Unique local material without a project backup ([storage](STORAGE.md#material-that-exists-only-on-the-local-disk)) | The owner's decision |

**Next selected action:** none. The next scope is the owner's choice; C271 is the queued unfinished one.

## Learning checkpoint

One lesson was recorded in project memory: current state belongs in the session checkpoint, not in an
agent's private memory, which is loaded into every later session of the project.
