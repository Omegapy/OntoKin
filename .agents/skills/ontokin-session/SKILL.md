---
name: ontokin-session
description: Start or resume OntoKin work in a local session or a ChatGPT browser thread, including continuation after compaction or interruption. Explicitly load the mode's current instructions, reconcile actual state, and select one authorized bounded scope.
---

# Start or resume an OntoKin session

## Establish the mode and current context

The mode is explicit under [AGENTS](../../../AGENTS.md#execution-modes); never infer it.
Complete its entry document and [PROTOCOL sections 1–3](../../../docs/workflow/PROTOCOL.md)
unless read at the observed revision; reuse verified read-sets and record mode and gaps in
[SESSION](../../../docs/workflow/templates/SESSION.md). This procedure installs no
skill, tool or permission.

- **Local:** [LOCAL-START](../../../LOCAL-START-HERE.md). Reuse the checkout and a valid
  environment; its "Go"/"Continue" rule resumes the next unmet step.
- **Browser:** [START](../../../CHATGPT-START-HERE.md), with the ephemeral-host rule and any
  older ZIP handoff reconciled against live GitHub.

## Select and execute one bounded scope

Resume the matching authorized task or select a distinct scope under PROTOCOL.
Optional new-work scaffolding: `python3 tools/chat_workflow.py new-task ID --title ... --intent ...`.
Complete real requirements, plan and ownership before work; scaffolding proves no
execution. Apply [ROLE](../../../ROLE.md) and PROTOCOL's worker/verification/integration rules.

## Resume after an interruption

Apply PROTOCOL section 8 in the session's mode: reconcile unknown outcomes and preserve
bytes before any retry.

- **Local:** inspect the actual working tree, processes, refs and destination state; continue
  from existing commits and checkpoints.
- **Browser:** [HANDOFF](../../../docs/workflow/HANDOFF.md) governs required recovery and
  delivery.

Finish via [ontokin-delivery](../ontokin-delivery/SKILL.md); stop where the mode's rules say.
