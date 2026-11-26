# Fresh-session demonstration

The account that TASK-030 of
[LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/PLAN.md) asks for,
written by the demonstrating session from its own observation on 2026-11-25. Places are named
relative to the clone. It records one session; it qualifies no product, native or destination
claim, and the Director decides whether it meets the step.

## Session and application

| Item | Observation |
| --- | --- |
| Instruction | The session's first and only user message was `Continue.`, with the full stop, marked by the application as pasted text. |
| Application | Claude for macOS `6.28899.6`, `CFBundleShortVersionString` of the installed application. |
| Claude Code | `2.1.330`, from the path of this session's own process, which lies in the desktop application's support directory under `claude-code/`. No terminal installation was asked. |
| Model | Claude Opus 5.5, as the application states it. |
| How it was recognised as the demonstrating session | The process path above, the Code tab that the application names, and the absence of `FRESH-SESSION.md` in the worktree. |
| Process arguments | None of `--resume`, `--continue` or `--fork…` among them. |
| Host | macOS 26.6.2, arm64; zsh. |

## Checkout

| Item | Observation |
| --- | --- |
| Folder | `OntoKin-worktrees/local-migration-20261124` beside the clone, a linked worktree. |
| Branch and head | `work/local-migration-20261124` at `d70d3ad90a6f03656cd383105c346ca1275774b9`, tree `b69717e71cfd0ecd1afed2c3afd2ab5977ed20d7`. |
| State | Clean; no untracked file, stash or commit that the remote lacks. |
| Worktree setting | Off, inferred: the session works in the chosen folder on the branch that was already there, the application made no new branch, and `.claude/worktrees` does not exist here. The setting itself was not read in the application. |
| Other worktrees | Main checkout on `main` at `6b346b1e…` with untracked `TRDs/` and `Implementation_Plans/`; `baseline-6b346b1e` at `6b346b1e…` and `candidate-checks` at `03d61c2d…`, both detached and clean. |
| Remote | `git ls-remote --heads origin` at 2026-11-25T19:10Z: `main` `6b346b1e…`, `work/c271-missing-import-digest-control` `bef67902…`, `work/local-migration-20261124` `d70d3ad9…`; no other head. |
| GitHub | Issue 277 open, no comment; no pull request of this branch; PR 274 an open draft at `bef67902…`; issue 273 open. |

## Instructions and skills

**Present without being opened.** The root `CLAUDE.md` and, through its import line, the full
text of `AGENTS.md`, both introduced by the application as project instructions checked into the
codebase. Beside them the application's own instructions, the owner's account address, a date,
and a Git snapshot: branch, clean state and the subjects of the five latest commits. No
user-level `CLAUDE.md` or rules directory exists, and the repository has no other `CLAUDE.md`.

**Opened by this session.**

- In full: `LOCAL-START-HERE.md`, `GOAL.md`, `ROLE.md`, `docs/workflow/registry.json`,
  `docs/workflow/CURRENT.json`, `docs/workflow/PROTOCOL.md`, the task's `SESSION.md`, `PLAN.md`
  and `REQUIREMENTS.md`, `docs/workflow/LOCAL-PROMPTS.md`, and the session and delivery skills.
- `STATUS.md` without the lines that hold only empty anchors.
- In part: `task.json` (every field outside its lists in full; state counts of the 42
  requirements; identity, state and title of all 36 steps; all checks); HANDOFF's local section
  and definitions, with the start of its browser sections; the first part of the session
  template; the TRD's REQ-019, 020, 021, 023, 024 and 029, at SHA-256 `12e905a7…`; the start of
  `DECISION.md` and of `ENVIRONMENT.json`.
- Not opened: `FRESH-SESSION-1.md`, of which only the name and what `PLAN.md`, `SESSION.md` and
  `task.json` say about it were seen; the plan tracker in the main checkout; every other evidence
  record; the learning skill.

**Project skills seen.** The application listed all six by name and description without any file
being opened: `communication`, `ontokin-delivery`, `ontokin-learning`, `ontokin-session`,
`to-implementation-plan` and `to-trd`. The last two are described there as explicit-invocation
only. All six `.claude/skills` links resolve, and each skill has one `SKILL.md`, under
`.agents/skills`. None was started through the skill tool; the session and delivery skills were
read as files. The application also offered skills of its own, which are not the project's.

## The session's account, compared with the records

| Subject | Account | Against the records |
| --- | --- | --- |
| Selected task | LOCAL-MIGRATION-20261124, `in_progress`, mode `local`; no product milestone selected; C271 separate, blocked and untouched. | Equal in [CURRENT](../../workflow/CURRENT.json), the [task record](../../workflow/tasks/LOCAL-MIGRATION-20261124/task.json) and the [checkpoint](../../workflow/tasks/LOCAL-MIGRATION-20261124/SESSION.md). |
| Environment | The worktree's `.venv`, CPython 3.12.13 (Homebrew), reused unchanged. Doctor: `core` and `python-verification` ready; `visual-verification` mismatch, Node.js 25.9.0 for target 22 and npm packages missing; `package-smoke` and `historical-native` not checked; `linux-container` unsupported. | Equal to the checkpoint, with the same digests of the manifest, both locks and the pins. |
| Completed work | TASK-001 to TASK-029 `done`; TASK-030 to TASK-036 `not_done`; all 42 requirements `not_done` before the audit. | Equal in the task record and the checkpoint. |
| Change size | Base to `dc04523f…`, tree `d186b0e0…`: 34 added, 21 modified, none deleted. Since then only `CURRENT.json` and `SESSION.md` changed. | Equal to the checkpoint. |
| Last completed gate | The R06 handoff, TASK-006 with TASK-007 and TASK-008, after TASK-027 to TASK-029. | Equal to the checkpoint, the only record that names it; the step states in the task record agree. |
| Next action | TASK-030, a clean run by this session, then TASK-031 by the Director. | Equal in all three records. |
| Blockers | None for this step. Outside it: TASK-030's Worktree criterion waits for the owner's read-only session; integration waits for audit, review and lease. | Equal. `blockers` is empty in the task record. |
| Ownership | Lease released; Director `local-migration-f58a0f3c1d5a`; this session is a worker for this file only. | Equal in STATUS, the task record and the checkpoint. |

**Differences.**

1. The records give the instruction as `Continue`; the message was `Continue.`, which is the form
   in [LOCAL-PROMPTS](../../workflow/LOCAL-PROMPTS.md). Read as the same instruction.
2. The checkpoint's head is its code checkpoint `dc04523f…`; the observed head is `d70d3ad9…`, one
   commit later, the commit that carries the checkpoint. The checkpoint foresees this.
3. The path of the process has one more directory between `2.1.330/` and the program than the
   checkpoint's description `claude-code/VERSION/` shows. It still lies under that directory.
4. The checkpoint's statements about other processes and desktop sessions, and about copies in
   the owner's ChatGPT Library, were not checked.

No difference concerns the selected task, the completed work, the next action or the blockers.

## Earlier conversation, memory, ZIP and Library

- **Earlier conversation:** none present; no summary or transcript of another session was in
  context, and none was looked for.
- **Private agent memory:** none present and none used. The application's own instructions
  describe a memory directory for this folder and say that it exists; by its listing, it does
  not. No memory text or index was in context, and this session wrote none. Memory directories
  of other folders were not looked for.
- **ZIP or Library download:** none present, requested or used.
- **During the session:** the application announced further tools of its own, a notification
  reader and a chart tool among them. The announcement carried nothing about the project, and
  neither of those two tools was used.

## What this session did

It read the records, reported the startup items, ran the doctor and the workflow check, wrote
this file, and ran the two checks that the checkpoint names. It restarted no recorded work, opened
no other scope and changed no other file. The commit that holds this file and its push are shown
by Git. Not observed here: TASK-030's Worktree criterion.
