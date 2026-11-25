# Fresh-session demonstration

Written by the **demonstrating session** of TASK-030 from its own observation, as the
[session checkpoint](../../workflow/tasks/LOCAL-MIGRATION-20261124/SESSION.md) asks. It is an
account, not the acceptance of TASK-030: the implementing session judges it and updates the
ledger. Machine paths are left out; places beside the clone are named relative to it.

Observed on 2026-11-25 between 18:37Z and 18:39Z.

## The session and its host

| Item | Observed value | How |
| --- | --- | --- |
| Session | A new Claude Code session in the Code tab of the Claude desktop application, model Claude Opus 5.5, execution mode `local` | The session's own process and its application metadata |
| How the session recognised itself | The running Claude Code lies in the desktop application's support directory, under `claude-code/2.1.330/`; the application is its ancestor process | `ps -o command= -p $PPID` and the parent chain |
| Application version | 6.28899.6 | `CFBundleShortVersionString` of the installed application |
| Bundled Claude Code version | 2.1.330 | The process path above, not a terminal's `claude --version` |
| Instruction | `Continue.`, with no other text | The conversation |
| Earlier conversation, ZIP or Library download | None was used | No such input was opened |

## Checkout and Worktree setting

| Item | Observed value |
| --- | --- |
| Checkout | `OntoKin-worktrees/local-migration-20261124` beside the clone, a linked worktree of it |
| Branch and head | `work/local-migration-20261124` at `3e2885e2957e00a52445558edb018ac9865a818f`, tree `23a3aba72b9d4201fba77818d2c2b1bb43c2f635`, equal to its tracking ref |
| Working tree | No tracked change, no untracked file, no stash |
| Remote heads, `git ls-remote --heads origin`, 18:37Z | `main` `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`; `work/c271-missing-import-digest-control` `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`; `work/local-migration-20261124` `3e2885e2957e00a52445558edb018ac9865a818f`; no other head |
| Worktrees | Clone on `main`; `baseline-6b346b1e` and `candidate-checks`, both detached and clean; this one |
| Main checkout | No tracked change; untracked `TRDs/` and `Implementation_Plans/`; no `.venv` |
| Worktree setting | Off, inferred: the application's record of this session names this worktree as both its working and its original folder, and no `.claude/worktrees/` directory exists here. The switch itself was not seen |

## Instructions and skills

**Present without being opened.** The content of `CLAUDE.md` and, through its import, of
`AGENTS.md` was in the session before its first action. Also present, and no part of the
repository: the application's own instructions, and the index of the agent's private memory
for this project, with one line (see Differences).

**Opened with a tool.** In full: `LOCAL-START-HERE.md`, `GOAL.md`, `ROLE.md`,
`docs/workflow/registry.json`, `docs/workflow/CURRENT.json`, `docs/workflow/PROTOCOL.md`, the
task's `SESSION.md`, `REQUIREMENTS.md` and `PLAN.md`, `docs/workflow/LOCAL-PROMPTS.md`, the
`ontokin-session` skill, `.claude/.gitignore`. `STATUS.md` without its lines that hold only
empty anchors. In part: `task.json` (the top-level fields, the requirements by
status, and the steps after TASK-014 by identifier, status and title only), `docs/workflow/HANDOFF.md` (from its
statement on local sessions to its end), the approved TRD (REQ-017 to REQ-029 and parts of
the two beside them; its SHA-256 equals the recorded one), `docs/workflow/templates/SESSION.md`, the start
of `HOST-INVENTORY.md`. Outside the repository: the one file that the memory index names. The
setup guide, the DECISION and RECONCILIATION records and the adopted specifications were not
opened; this step needs none of them.

**Project skills.** The session's own skill list names all six: `communication`,
`ontokin-delivery`, `ontokin-learning`, `ontokin-session`, `to-implementation-plan`, `to-trd`.
Each `.claude/skills` link resolves to a `SKILL.md` under `.agents/skills/`. The list says of
`to-trd` and `to-implementation-plan` that they run only on explicit request. None was invoked;
`ontokin-session` was read as a file. The list also holds skills that the application supplies.

## Account of the task

- **Selected task:** LOCAL-MIGRATION-20261124, `in_progress`, mode `local`, scope issue 277
  open, owner `local-migration-0e9ea0a483b1`. CURRENT, the task record and the checkpoint agree.
- **Environment:** `.venv/bin/python` is CPython 3.12.13 (Homebrew) on macOS 26.6.2, arm64. The
  doctor reports `core` and `python-verification` ready, `visual-verification` mismatch (Node.js
  25.9.0, target 22), `package-smoke` and `historical-native` not checked, `linux-container`
  unsupported. The specification and lock digests in its output equal those of the checkpoint.
- **Completed work:** TASK-001 to TASK-005 and TASK-009 to TASK-029 are `done` in the ledger;
  its 42 requirements are all `not_done` until the audit of TASK-031.
- **Last completed gate:** TASK-027, the candidate checks against the baseline, with the
  second-worktree test of TASK-028; TASK-029 is the checkpoint.
- **Next action:** TASK-030, this record. No other step was started, no completed step was
  repeated, and no product milestone was selected.
- **Blockers:** TASK-006, the R06 archive and its receipt, which also holds back TASK-007,
  TASK-008 and TASK-031 (see Differences). C271 is unfinished and separate: draft pull request
  274 at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448` and issue 273 are open.
- **Not verified by this session:** the recorded test counts and evidence digests, the R06
  files, and the truth of cited evidence. Nothing was run beyond the startup checks and those
  below.

## Differences

1. **Unpublished commit.** The checkpoint states no unpublished commit at its code checkpoint.
   The local-only ref `refs/ontokin/prepared-corrections` now holds one,
   `d4d486b3621e26e71830beddfe988ac8bc2e9461`, whose parent is this head. No branch and no
   remote head holds it. Its subject says that R06 is verified and the reconciliation and
   storage records are complete; it changes four files. CURRENT, the task record and the
   checkpoint on this branch still call TASK-006 to TASK-008 blocked. Only its metadata and file
   list were read; its content was neither opened, used nor brought in.
2. **Agent-private memory.** The application put the memory index into the session, and the
   session opened the file that the index names before it read the checkpoint. That file
   describes the ref above and how to merge it later, and says who may write this record. Nothing
   in the account above comes from it: the ref was also listed by `git for-each-ref`, and the
   checkpoint itself says who may write. The session was therefore not free of all earlier
   context, but no step depended on it.
3. **Head and code checkpoint.** The checkpoint names
   `03d61c2dfd386698e0b6dead00c35b1fea70422a`; the head is one commit later and changes only
   CURRENT and the checkpoint itself, as it says Git will show.
4. **Package smoke.** The doctor reports `package-smoke` as not checked; the checkpoint calls it
   proven by its own record. The doctor's output does not mention that record, and neither was examined further.
5. **Other sessions.** A terminal Claude Code session works in the main checkout and runs a
   script whose file name says that it watches for this demonstration; one further desktop
   Claude Code process also has the main checkout as its folder. Neither was seen to write in
   this worktree. The checkpoint says that the implementing session writes nothing here
   meanwhile; it does not mention the second process.
6. **Order of the startup items.** The items were observed first and reported together after
   the records had been read, before this file was written.

No other difference was found.

## Checks

Run in this worktree with its own interpreter, after this file was written and before it was
committed:

| Command | Outcome |
| --- | --- |
| `.venv/bin/python -B docs/maintenance/reorganization-2026-10-17/verify_reorganization.py` | Passed: exit 0, no failure listed |
| `.venv/bin/python -B tools/chat_workflow.py check` | Passed: exit 0, 12 tasks |

The Worktree criterion of TASK-030 is not covered here; the checkpoint assigns it to a second,
read-only session.
