# Start OntoKin in a ChatGPT browser chat

Stable entry for **Omegapy/OntoKin**. GitHub holds current instructions, work and
evidence; [HANDOFF.md](docs/workflow/HANDOFF.md) defines the required saved
browser-session ZIP and its reconciliation with live GitHub.

## Prompt to use in a new chat

Use the complete [continuation or interrupted-thread recovery prompt](docs/workflow/BROWSER-PROMPTS.md).
Recovery includes delivery-only work after implementation has merged.

## Required startup

1. The Director observes actual `main` through GitHub and retains its full commit
   SHA. At that same revision, read this file, [AGENTS](AGENTS.md), [GOAL](GOAL.md),
   [STATUS](STATUS.md), [ROLE](ROLE.md), [registry](docs/workflow/registry.json),
   [CURRENT](docs/workflow/CURRENT.json), [PROTOCOL](docs/workflow/PROTOCOL.md) and
   [HANDOFF](docs/workflow/HANDOFF.md) in full. Retain the read-set; read each once
   and reopen only changed, missing or newly relevant text. Search snippets,
   assumed snapshots and duplicate archived/remote copies do not replace this read.
2. Follow CURRENT to the active task, or latest task when none is active. Read
   its `task.json`, requirements and plan, full selected registry `SKILL.md`
   files, and nested `AGENTS.md` governing edited paths. Read additional source
   specifications as the scope requires. Record missing or truncated required text.
3. Reconcile live branches, PRs, scope issues, integration ownership, relevant
   checks and surviving local work with the saved checkpoint.
4. Record actual repository read/write, branch/PR, conditional-update,
   merge/deletion, terminal/test, subagent, ZIP creation/verification and Library
   saving capabilities. A missing required capability is a concrete blocker;
   repository procedures supply neither tools nor permissions.
5. Declare the authorized scope, one phase, starting revision, acceptance
   checkpoint, stopping point and material limits under PROTOCOL. Confirm the
   early recovery ZIP before substantial or long work.

Repository instructions and skills require explicit loading; browser chats,
Codex discovery and installed ChatGPT skills are separate host features.
These procedures can also be followed manually through a connector.

## Work and finish

Follow [PROTOCOL section 4](docs/workflow/PROTOCOL.md#4-implement-delegate-and-bound-the-session)
for workers and phase limits, and HANDOFF for saved delivery. Optional local
helpers `python3 tools/chat_workflow.py brief`, `check` and `lookup QUERY` provide
navigation/structural checks; they neither contact GitHub nor prove remote actions.

See the [human guide](docs/workflow/README.md) for capability fallbacks and the
[C263 migration record](docs/engineering/browser-workflow-c263/MIGRATION.md) for
preserved historical C262 evidence.
