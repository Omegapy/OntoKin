# Develop OntoKin with an agent

Two ways of working share one repository, one task system and one set of rules.
The entry document a session starts from decides which one applies.

| Mode | Entry | Use it for |
| --- | --- | --- |
| Local | `LOCAL-START-HERE.md` | Ordinary development in the owner's clone, normally from the Code tab of the Claude desktop application. |
| Browser | [CHATGPT-START-HERE.md](../../CHATGPT-START-HERE.md) | ChatGPT browser threads, each on a different, disposable host. |

## What happens in a session

The agent reads current instructions and the live checkpoint, checks what its
tools can actually do, and selects the scope authorized by your request. It
records requirements and a plan, implements the change, verifies it and updates
GitHub. Independent workers can help when available. Completed approved work
is integrated into main and the work branch is resolved.

- A **local** session reuses the checkout and its environment, may continue
  through the selected task's planned steps, and closes on commits, truthful
  records, verified push state and durable evidence. It needs no ZIP unless the
  task asks for one. See [HANDOFF.md](HANDOFF.md#local-sessions).
- A **browser** session rebuilds what it needs on its current host, works on one
  declared phase, and then verifies and saves the required browser-session ZIP
  under [HANDOFF.md](HANDOFF.md). Use the separate
  [continuation and recovery prompts](BROWSER-PROMPTS.md).

A task can span several sessions. The next session resumes the same task and
branch after checking their current state. It does not create another branch
simply because the conversation changed. If the previous operation timed out, it
checks the actual state before repeating it.

## Where information lives

| File or directory | Purpose |
| --- | --- |
| [STATUS.md](../../STATUS.md) | Short current project state, product limits and main integration ownership. |
| [CURRENT.json](CURRENT.json) | Pointer to the active/latest task and explicit next-action disposition. |
| [Current task pointer](CURRENT.json) | Locates the active/latest task's requirements, plan, evidence and completion record. |
| [Registry](registry.json) | Required reads and the small set of reusable repository skills. |
| [ROLE.md](../../ROLE.md) | Director, worker and reviewer accountability. |
| [PROTOCOL.md](PROTOCOL.md) | Startup, execution, recovery, verification and integration rules. |
| [HANDOFF.md](HANDOFF.md) | Browser: required saved session ZIP, early checkpoints and confirmed delivery. Local: what closes a session or scope. |
| [Browser prompts](BROWSER-PROMPTS.md) | Copyable normal continuation and interrupted-thread recovery prompts. |
| [Memory](memory.json) | Source-backed decisions, constraints and lessons; current instructions retain authority. |
| [Knowledge guide](KNOWLEDGE.md) | Project vocabulary, relationships and documented capability boundaries. |

The task's `task.json` is the status/acceptance record. Its requirements and plan
Markdown explain the work. STATUS summarizes the project and lease; CURRENT
points to the task. These records have distinct jobs, so a second competing
task ledger is unnecessary. [Templates](templates/SESSION.md) help capture
session observations without saving entire conversations.

## When capabilities differ

Browser threads differ in what they can do:

| Available in this chat | Supported route |
| --- | --- |
| GitHub read/write plus a terminal | Edit in a temporary checkout, run relevant checks and publish through authorized GitHub operations. |
| GitHub read/write without a terminal | Read and edit through the connector. Inspect records manually, but mark execution checks `not_run`; use actual available verification evidence before claiming completion. |
| GitHub read only | Inspect/review and prepare the exact change or recovery instructions. Repository publication remains blocked until a write-capable session is available. |
| Subagent tools | Delegate independent work with bounded ownership and review the returned artifacts. |
| No subagent tools | Work sequentially and identify self-review. Do not claim a separate worker ran. |

The browser's product surface and available connections determine capabilities.
Instructions in GitHub do not install a tool, create permissions, change the
selected model or guarantee automatic file discovery. Report an observed
restriction precisely; do not infer that all browser chats share it.

## Small offline tools

Use Python 3.11 or later from a checkout. The tools use the standard library and
make no network calls:

```sh
python3 tools/chat_workflow.py check
python3 tools/chat_workflow.py brief --json
python3 tools/chat_workflow.py lookup "hinge"
python3 tools/chat_workflow.py new-task C265 --title "Selected scope" --intent "Owner's request"
```

`check` checks record structure, references and completion fields. It cannot
prove that evidence is scientifically correct or that a branch was merged.
`brief` summarizes the saved checkpoint and local checkout. `lookup` finds
actual memory/knowledge entries with their sources and status. `new-task`
creates local draft task, requirements and plan files and refuses to overwrite an existing task. It does not
publish, select the task in CURRENT or authorize work. Review and commit a
draft through the normal branch procedure when that scope is authorized.

In a connector-only session, use the same JSON records directly and follow the
manual acceptance checks in the protocol. Do not claim that the CLI ran.

## Historical handoffs

C262 remains a preserved historical archive. Its code baseline and source
integration were reconciled with GitHub before this migration. Ordinary work
starts from current GitHub main. Full historical offline restoration remains a
separate operation with its original archive contract; this workflow does not
claim to replace or rerun it. See the [migration record](../engineering/browser-workflow-c263/MIGRATION.md).

The owner later clarified on November 18 that each bounded browser development
or recovery scope must still produce a verified ZIP saved in the existing
OntoKin Library folder. [C264](tasks/C264/REQUIREMENTS.md) records this prospective
change; C263's original migration record remains historical. The new session ZIP
is for online continuation against GitHub, with explicit historical dependencies.
It is not a complete offline source archive. Keep C262 unchanged and preserve its
full restoration contract. Integration alone does not complete required delivery.
