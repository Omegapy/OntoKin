# Start OntoKin in a ChatGPT browser chat

This is the stable entry point for agents developing **Omegapy/OntoKin**.
GitHub holds the current instructions, tasks and evidence. Each bounded browser
development or recovery scope also requires a verified session handoff ZIP saved
in the owner's existing OntoKin Library folder. The ZIP carries continuation
context; the next chat reconciles it with current GitHub state.

## Prompt to use in a new chat

```text
We are developing https://github.com/Omegapy/OntoKin in this ChatGPT browser chat.
Source handoff: [paste the latest saved handoff ZIP link, or state unavailable].
Read its README-START-HERE.md. Use the available GitHub connection to read
CHATGPT-START-HERE.md on current main, then explicitly read its required files.
Reconcile live main,
branches, pull requests, ownership and the current task before acting. Follow
the repository workflow for my request, using actual available tools. Complete
one bounded authorized scope through verification and integration, record the
result in GitHub, resolve the completed branch, and create, verify and save the
next browser-session handoff ZIP under docs/workflow/HANDOFF.md, then stop.
My request for this thread: [describe the work, or say "continue the ready task"]
```

Use the complete [continuation and recovery prompts](docs/workflow/BROWSER-PROMPTS.md)
for normal work and interrupted conversations. Recovery resumes only the
unfinished authorized scope, including delivery when implementation already merged.

## Required startup

1. Read the actual `main` head through the GitHub connection. Retain its full
   commit SHA, the identifier for that revision. Read the following files at
   that same SHA, not from search snippets or an assumed local snapshot:
   [AGENTS.md](AGENTS.md), [GOAL.md](GOAL.md), [STATUS.md](STATUS.md),
   [ROLE.md](ROLE.md), [registry](docs/workflow/registry.json),
   [current checkpoint](docs/workflow/CURRENT.json), and
   [workflow protocol](docs/workflow/PROTOCOL.md) and
   [handoff contract](docs/workflow/HANDOFF.md).
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
5. State the intended bounded scope, starting revision, material limits and
   verification approach briefly. Continue authorized work. If the checkpoint
   says `awaiting_user_direction` and the user supplied no new scope, report the
   completed state and queued option; do not start it automatically. The full
   continuation prompt explicitly authorizes selecting one next bounded step.

Do not assume a browser chat automatically loads `AGENTS.md` or repository
skills. Explicitly read them. Codex discovery and installed ChatGPT skills are
separate host features. These repository procedures also work when followed
manually through a connector.

## Work and finish

The main chat agent is the Director described in [ROLE.md](ROLE.md). Use
available subagents for independent work, assign nonoverlapping ownership and
keep main integration serialized. Capture requirements and a plan before
substantial implementation. The [protocol](docs/workflow/PROTOCOL.md) covers
verification, memory, recovery, authorization and branch cleanup.

When a terminal is available, these optional local commands help inspect a
checkout. They do not contact GitHub or prove that a remote action occurred:

```sh
python3 tools/chat_workflow.py brief
python3 tools/chat_workflow.py check
python3 tools/chat_workflow.py lookup "source authority"
```

Save a durable checkpoint early, after meaningful phases and before long work.
Do not rely on automatic compaction, an advance length warning or chat memory.
Finish with links to the changed files, actual check results, PR/merge state,
branch disposition, the verified saved ZIP and one next action. Update GitHub
before ending. If a required action is blocked, preserve a precise recovery
handoff and label the task incomplete. A local ZIP or an attempted upload is
not confirmed delivery. Stop after the selected scope and its saved handoff.

See the [human workflow guide](docs/workflow/README.md) for normal use and
capability fallbacks. Historical C262 evidence remains registered in the
[migration record](docs/engineering/browser-workflow-c263/MIGRATION.md).
