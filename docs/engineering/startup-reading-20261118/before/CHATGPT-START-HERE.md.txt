# Start OntoKin in a ChatGPT browser chat

This is the stable entry point for agents developing **Omegapy/OntoKin**.
GitHub holds the current instructions, tasks and evidence. Each bounded browser
development or recovery phase also requires a verified session handoff ZIP saved
in the owner's existing OntoKin Library folder. The ZIP carries continuation
context; the next chat reconciles it with current GitHub state.

## Prompt to use in a new chat

```text
We are developing https://github.com/Omegapy/OntoKin in this ChatGPT browser chat.
Source handoff: [paste the latest saved handoff ZIP link, or state unavailable].
Read its README-START-HERE.md and checkpoint. Use the GitHub connection to read
CHATGPT-START-HERE.md and its required instructions once at observed current main.
Reconcile live refs, ownership and the active task. Resume that authorized scope
for one declared phase. Verify and confirm an early recovery ZIP before long
or substantial work. Follow PROTOCOL for bounded workers and phase stopping.
Save a verified partial or completed handoff under docs/workflow/HANDOFF.md,
record the actual state and stop. Keep the parent task open until all gates pass.
My request for this thread: [describe the work, or say "continue the ready task"]
```

Use the complete [continuation and recovery prompts](docs/workflow/BROWSER-PROMPTS.md)
for normal work and interrupted conversations. Recovery resumes only the
unfinished authorized scope, including delivery when implementation already merged.

## Required startup

1. The Director reads the actual `main` head through the GitHub connection. Retain its full
   commit SHA, the identifier for that revision. Read the following files at
   that same SHA, not from search snippets or an assumed local snapshot:
   [AGENTS.md](AGENTS.md), [GOAL.md](GOAL.md), [STATUS.md](STATUS.md),
   [ROLE.md](ROLE.md), [registry](docs/workflow/registry.json),
   [current checkpoint](docs/workflow/CURRENT.json), and
   [workflow protocol](docs/workflow/PROTOCOL.md) and
   [handoff contract](docs/workflow/HANDOFF.md). Read required text once at that
   revision; retain the read-set and reopen only changed or newly relevant text.
   Do not load duplicate archived and remote copies. Full applicable instructions
   remain mandatory.
2. Follow the checkpoint to the active task, or latest task if none is active.
   Read its `task.json`, requirements and plan. Select and read the full relevant
   `SKILL.md` files from the registry. Inspect any more specific `AGENTS.md`
   governing paths you will edit. Read source specifications only as needed for
   the chosen task. Missing required text is an explicit information gap.
3. Inspect live branches, open PRs, the scope issue, integration ownership and
   relevant checks. Read surviving local changes if this session has a checkout.
   A saved checkpoint describes an observation; live state may have advanced.
4. Record actual available capabilities: repository reads and writes, branch/PR
   operations, conditional updates, merge/deletion, terminal/tests, subagents
   and ZIP creation/verification and Library saving. A skill file cannot provide
   a missing tool; a missing required delivery capability is a concrete blocker.
5. State the scope, one session phase, starting revision, acceptance checkpoint,
   stopping point and material limits briefly. Confirm an early recovery ZIP
   before substantial or long work. Continue authorized work. If the checkpoint
   says `awaiting_user_direction` and the user supplied no new scope, report the
   completed state and queued option; do not start it automatically. The full
   continuation prompt authorizes selecting one next bounded step only when
   there is no active authorized scope to resume.

Do not assume a browser chat automatically loads `AGENTS.md` or repository
skills. Explicitly read them. Codex discovery and installed ChatGPT skills are
separate host features. These repository procedures also work when followed
manually through a connector.

## Work and finish

The main chat agent is the Director described in [ROLE.md](ROLE.md). Follow
[PROTOCOL section 4](docs/workflow/PROTOCOL.md#4-implement-delegate-and-bound-the-session)
for bounded workers with fresh context when supported, compact reports and
limited tool output. Children read full applicable governing instructions and
receive current user constraints; they do not repeat global startup unless
assigned. Keep main integration serialized. Capture requirements and a plan
before substantial implementation.

When a terminal is available, these optional local commands help inspect a
checkout. They do not contact GitHub or prove that a remote action occurred:

```sh
python3 tools/chat_workflow.py brief
python3 tools/chat_workflow.py check
python3 tools/chat_workflow.py lookup "source authority"
```

Refresh durable checkpoints at phase changes and before long work, preserving
unique unpublished bytes. Stop at the declared checkpoint or first unplanned
expansion, save a verified handoff and report changed files, actual checks,
PR/merge state, branch disposition, saved ZIP and first unmet gate. A planned
partial handoff completes the session's delivery, not the parent task; it is
not a blocker. A local ZIP or attempted upload is not delivery. Continue the
same unfinished task in a fresh parent chat. Do not assume compaction, a length
warning, automatic new-chat creation or a parent reset from subagents.

See the [human workflow guide](docs/workflow/README.md) for normal use and
capability fallbacks. Historical C262 evidence remains registered in the
[migration record](docs/engineering/browser-workflow-c263/MIGRATION.md).
