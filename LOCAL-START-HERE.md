# Start a local OntoKin session

Entry document of **local mode**: ordinary development in the owner's persistent clone or
one of its worktrees. Starting here declares the mode; record `local` in the session
checkpoint, and in a new task record that names no mode yet. A task recorded as `browser`,
like every earlier record that names no mode, is resumed here only on explicit owner
direction. A ChatGPT browser thread starts
from [CHATGPT-START-HERE](CHATGPT-START-HERE.md). A session on a disposable or remote host
is not local, whatever application runs it: say so and ask. The persistent clone shows itself
by what it retains, such as the worktrees, branches and environment that earlier records
name; a fresh copy without them is not it unless the owner says so.

The checkout persists; your understanding does not. Rebuild it from the records below. No
previous conversation and no ChatGPT Library download is needed.

## "Go" or "Continue"

Read this document and the current task records, reconcile actual local and remote state,
and perform the next unmet step of the selected authorized scope, preserving evidence,
reporting meaningful progress, and checkpointing at completion or at a concrete blocker.

- The next unmet step is the one that CURRENT's next action names; the session checkpoint
  gives its detail. A blocked step is reported and holds back no step that does not depend on
  it.
- It restarts nothing that is recorded and verified as complete.
- It selects no new product milestone, even when another task is blocked. With no selected
  scope, report the state and ask.
- An old handoff's stop condition is no permanent prohibition on newly authorized local work.
- Environment setup is no permission to rerun restricted native experiments.
- It depends on no ChatGPT Goals feature, scheduled Task or agent-private memory. A separate
  goals interface points at the same repository task state.

## Startup

Report each item to the owner in your reply, before the first change. A file, a plan tool or
unseen reasoning is no report.

1. **Identify** the repository, working directory, branch or worktree, head, tracked changes,
   untracked work, the other worktrees and work branches, and any active agent or lease
   ownership: `git status --short --branch`, `git worktree list`, `git branch -vv`,
   `git stash list`, the checkpoint's coordination group and the lease in STATUS. When the
   selected task's branch is checked out in another worktree, or its records there are newer,
   report that and work there. When another agent may be active on it, ask before writing,
   unless the checkpoint hands this step to your session.
2. **Read** the shared instructions [AGENTS](AGENTS.md), [GOAL](GOAL.md), [STATUS](STATUS.md),
   [ROLE](ROLE.md), the [registry](docs/workflow/registry.json),
   [CURRENT](docs/workflow/CURRENT.json) and [PROTOCOL](docs/workflow/PROTOCOL.md); then the
   selected task's requirements, plan and `task.json`, and the session checkpoint that
   CURRENT names. Where the task's requirements refer to a longer document, read its sections
   for the requirements of the next step. Skip only STATUS lines that hold nothing but empty
   `a` anchors.
3. **Load** the affected specifications and the applicable registered skills. Read
   historical evidence only when the selected gate requires it.
4. **Check the remote** when online, with `git ls-remote --heads origin`. Distinguish the
   local head, the remote-tracking refs and the independently observed remote head. Read the
   scope's issue and pull request when `gh` is available. Preserve local changes before
   updating anything.
5. **Diagnose**, and reuse a valid environment:

   ```sh
   .venv/bin/python tools/doctor_local.py
   .venv/bin/python tools/chat_workflow.py check
   ```

   Without a `.venv`, run both with `python3` and follow the doctor's next setup action.
   The [setup guide](docs/development/LOCAL-SETUP.md) explains profiles and repairs.
6. **State** one bounded objective, its acceptance checks and its stopping condition.
7. **Continue** with that step.

Offline: work may continue within scope. Label remote state stale and report push, merge and
deletion as unconfirmed.

No full test suite and no archive download is a startup step. Identities and locations of
the R06 handoff and other legacy archives stay in the
[reconciliation record](docs/engineering/local-migration-20261124/RECONCILIATION.md) and in
the history that CURRENT links; materialize one only when the selected work requires it.

## While working and before stopping

[PROTOCOL](docs/workflow/PROTOCOL.md) sections 4, 5, 7 and 8 govern conduct, parallel
worktrees, checks, publication and recovery. Close under
[HANDOFF's local section](docs/workflow/HANDOFF.md#local-sessions) with a checkpoint from the
[session template](docs/workflow/templates/SESSION.md). Copyable instructions:
[LOCAL-PROMPTS](docs/workflow/LOCAL-PROMPTS.md).
