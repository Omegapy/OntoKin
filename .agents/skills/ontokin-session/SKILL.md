---
name: ontokin-session
description: Start or resume OntoKin work from a ChatGPT browser thread, including continuation after compaction, interruption, or an older ZIP handoff. Explicitly load current GitHub instructions, reconcile live state, and select one authorized bounded scope.
---

# Start or resume an OntoKin session

## Establish the current context

Complete [START](../../../CHATGPT-START-HERE.md) and [PROTOCOL sections 1–3](../../../docs/workflow/PROTOCOL.md)
unless read at the observed revision; reuse verified read-sets and record gaps in
[SESSION](../../../docs/workflow/templates/SESSION.md). This procedure installs no
skill, tool or permission.

## Select and execute one bounded scope

Resume the matching authorized task or select a distinct scope under PROTOCOL.
Optional new-work scaffolding: `python3 tools/chat_workflow.py new-task ID --title ... --intent ...`.
Complete real requirements, plan and ownership before work; scaffolding proves no
execution. Apply [ROLE](../../../ROLE.md) and PROTOCOL's worker/verification/integration rules.

## Resume after an interruption

Apply PROTOCOL section 8/[HANDOFF](../../../docs/workflow/HANDOFF.md): reconcile
unknown outcomes, preserve bytes, confirm required recovery/delivery. Finish via
[ontokin-delivery](../ontokin-delivery/SKILL.md); stop at the declared phase.
