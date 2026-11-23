# Start OntoKin in a ChatGPT browser chat

Entry: **Omegapy/OntoKin**. GitHub owns current instructions/work/evidence; [HANDOFF](docs/workflow/HANDOFF.md) governs saved browser-session ZIPs and live reconciliation.

## Mandatory ephemeral-host rule

**Mandatory ephemeral-host rule:** Every new ChatGPT browser discussion is a **different, disposable execution host**. Assume no access to any prior thread's filesystem, installed dependencies, virtual environments, running workers or temporary paths. Read GitHub and verified Library artifacts for continuity; inspect only relevant current-host capabilities and reconstruct required inputs in fresh session directories. Historical paths/receipts are evidence, not current resources. Do not search for or attempt to preserve a previous virtual host. See [EPHEMERAL-HOST](docs/workflow/EPHEMERAL-HOST.md).

## Prompt to use in a new chat

Use the full [continuation or recovery prompt](docs/workflow/BROWSER-PROMPTS.md); recovery includes delivery after implementation merges.

## Required startup

1. Director: observe actual GitHub `main`; retain its full SHA. At that revision read this file, [AGENTS](AGENTS.md), [GOAL](GOAL.md), [STATUS](STATUS.md), [ROLE](ROLE.md), [registry](docs/workflow/registry.json), [CURRENT](docs/workflow/CURRENT.json), [PROTOCOL](docs/workflow/PROTOCOL.md), [HANDOFF](docs/workflow/HANDOFF.md) **in full, once**, except STATUS lines consisting only of empty HTML `a` elements with only an `id` attribute: keep these navigation identifiers unchanged in the file; load them only for history/link work. Exclude no prose, heading, rule, state or evidence reference. Record that exclusion in the read-set; reopen only changed, missing or newly relevant text. Snippets, assumed snapshots and duplicate archive/remote copies cannot substitute.
2. Follow CURRENT to active task, else latest task. Read `task.json`, requirements, plan, full selected registry `SKILL.md` files and nested `AGENTS.md` governing edits. Read scope-required specifications; record missing/truncated required text.
3. Reconcile saved checkpoint with live branches, PRs, scope issues, integration ownership, relevant checks and surviving local work.
4. Record actual capabilities: repository read/write; branches/PRs; conditional updates; merge/deletion; terminal/tests; subagents; ZIP creation/verification; Library saving. A missing required capability blocks that action; procedures grant no tools/permissions.
5. Under PROTOCOL, declare authorized scope, one phase, starting revision, acceptance checkpoint, stop and material limits. Confirm early recovery ZIP before substantial/long work.

Explicitly load repository instructions/skills. Browser chats, Codex discovery and installed ChatGPT skills are separate host features; a connector can support manual execution.

## Work and finish

Use [PROTOCOL §4](docs/workflow/PROTOCOL.md#4-implement-delegate-and-bound-the-session) for workers/phase limits; HANDOFF for saved delivery. Optional local `python3 tools/chat_workflow.py brief`, `check`, `lookup QUERY` navigate/check structure; they neither contact GitHub nor prove remote actions.

[Human guide](docs/workflow/README.md): capability fallbacks. [C263 migration](docs/engineering/browser-workflow-c263/MIGRATION.md): preserved C262 evidence.
