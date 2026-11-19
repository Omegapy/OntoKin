---
name: ontokin-session
description: Start or resume OntoKin work from a ChatGPT browser thread, including continuation after compaction, interruption, or an older ZIP handoff. Explicitly load current GitHub instructions, reconcile live state, and select one authorized bounded scope.
---

# Start or resume an OntoKin session

## Establish the current context

Complete [START](../../../CHATGPT-START-HERE.md) and
[PROTOCOL sections 1–3](../../../docs/workflow/PROTOCOL.md) if not already read
at the observed revision. Reuse that verified read-set; record gaps in
[SESSION](../../../docs/workflow/templates/SESSION.md). This repository procedure
installs no skill, tool or permission.

## Select and execute one bounded scope

Resume the matching authorized task or select a distinct scope under PROTOCOL.
For new work, optional `python3 tools/chat_workflow.py new-task ID --title ... --intent ...`
scaffolds records; complete real requirements, plan and ownership before work.
Scaffolding proves no execution. Follow [ROLE](../../../ROLE.md) and PROTOCOL's
worker, verification and integration rules.

## Resume after an interruption

Apply PROTOCOL section 8 and [HANDOFF](../../../docs/workflow/HANDOFF.md) to
reconcile unknown outcomes, preserve bytes and confirm required recovery/delivery.
Finish through [ontokin-delivery](../ontokin-delivery/SKILL.md), then stop at the
declared phase.
