---
name: ontokin-session
description: Start or resume OntoKin work from a ChatGPT browser thread, including continuation after compaction, interruption, or an older ZIP handoff. Explicitly load current GitHub instructions, reconcile live state, and select one authorized bounded scope.
---

# Start or resume an OntoKin session

Treat this file as an explicitly read repository procedure. Its presence on
GitHub does not install a personal skill or create tools, permissions, memory,
subagents, or background execution.

## Establish the current context

1. Read [CHATGPT-START-HERE.md](../../../CHATGPT-START-HERE.md). Follow its
   [registry](../../../docs/workflow/registry.json), required reading order,
   and [CURRENT pointer](../../../docs/workflow/CURRENT.json). Fetch the required
   files at the observed repository revision; do not treat a search excerpt
   as a complete read. Record missing or truncated content.
2. Read [AGENTS.md](../../../AGENTS.md), the relevant nested instructions,
   [ROLE.md](../../../ROLE.md), and the active requirements and plan. Use
   [PROTOCOL.md](../../../docs/workflow/PROTOCOL.md) for precedence, state,
   ownership, and recovery rules. Read only the additional procedures needed
   for the selected work.
3. Inspect actual GitHub main, branch inventory, open pull requests, relevant
   issue handoffs, and integration ownership. Inspect surviving local work
   when a workspace exists. Record observed SHAs and distinguish an authentic
   checkout from a reconstructed snapshot.
4. Compare the current user's direction with CURRENT, the active plan, and
   any supplied handoff. Preserve prior evidence, but use live repository
   observations to reconcile stale progress or branch claims. A queued
   product task does not override a different authorized current request.
5. Inventory available repository reads, writes, conditional ref updates,
   pull-request integration, terminal/tests, subagents, and artifact tools.
   Record observed capability or its specific absence. Do not probe access
   through an unnecessary mutation or infer permission from a role title.

## Select and execute one bounded scope

State the intended outcome, starting revision, owned scope, verification gate,
and stopping condition. Reuse a matching active task after reconciling its
ownership. Create a new task only for a distinct authorized objective. Reading
status or asking a question does not start unrelated implementation.

If a terminal is available, the repository helper supports:

```sh
python3 tools/chat_workflow.py check
python3 tools/chat_workflow.py brief
python3 tools/chat_workflow.py lookup hinge
```

Use the helper output as navigation and structural checks. Open the governing
sources and compare live GitHub state separately. Without a terminal, read the
same files directly and identify checks that were not executed.

For new authorized work, use `new-task ID --title ... --intent ...` as described
in the protocol, then complete its real requirements, plan, and ownership.
Scaffolding a task does not establish that implementation or verification ran.

Delegate independent work only through available subagent tools and the
Director's role contract. Give every worker an exact input revision and bounded
write scope using [WORKER.md](../../../docs/workflow/templates/WORKER.md).
Keep integration serialized. Continue authorized work without repeated approval
requests for routine reversible steps.

## Resume after an interruption

Save a durable checkpoint early, after material phases and before long work.
Follow the required session ZIP contract in
[HANDOFF.md](../../../docs/workflow/HANDOFF.md). Do not depend on automatic
compaction, a remaining-context estimate or an advance thread-limit warning.
Use [SESSION.md](../../../docs/workflow/templates/SESSION.md) to retain the
read-set, capabilities, owner, code/evidence identities, unknown operations,
and next action. After an uncertain write, inspect the remote refs and exact
artifacts before retrying. A timeout or expired lease does not prove that a
previous writer stopped or a write failed.

Complete through [ontokin-delivery](../ontokin-delivery/SKILL.md). If a required
capability or gate is unavailable, preserve a precise GitHub checkpoint where
possible and report the concrete blocker. Stop at the selected milestone;
do not begin the next product step merely because it is listed in CURRENT.
