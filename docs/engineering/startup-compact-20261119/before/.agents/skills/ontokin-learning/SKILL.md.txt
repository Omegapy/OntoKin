---
name: ontokin-learning
description: Review evidence-backed OntoKin lessons after substantive verified work or an explicit learning request. Retrieve project memory, assess applicability, and capture authorized durable records without claiming automatic cross-session learning.
---

# Review and retain useful project knowledge

Use already-required [PROTOCOL](../../../docs/workflow/PROTOCOL.md),
[memory](../../../docs/workflow/memory.json),
[knowledge](../../../docs/workflow/knowledge.json) and relevant direct sources.
Recheck current authority before applying recalled conclusions.

## Retrieve and assess

Use `python3 tools/chat_workflow.py lookup QUERY` when available; otherwise read
the JSON and [guide](../../../docs/workflow/KNOWLEDGE.md). Retrieval grants no
write authority or automatic cross-session learning.

After substantive verified work, assess reusable decisions, lessons, constraints
or open questions. Skip acknowledgments, read-only requests, duplicates,
speculation and unsupported agent assertions; finding nothing useful is valid.
State applicability and limits: local checks establish only exercised inputs
and environments, not general language, physics, destination or comparative claims.
Distinguish current decisions, historical observations, proposals and unresolved
questions.

## Capture under current ownership

Respect opt-outs. Discussion alone grants no publication authority; existing
milestone authorization may cover scoped evidence-backed notes without repeated
permission. Only the assigned canonical writer edits memory; others return
proposals with evidence and allowed scope through the Director.

1. Search existing IDs/summaries; choose a stable ID, kind, status, concise
   summary, scope and recorded date.
2. Cite exact evidence. Prefer immutable commit links for byte-specific
   observations; live specification links identify current authority, not old
   results.
3. Add only supported new information. Retain replaced records as `superseded`
   and link `supersedes`; use `historical` for still-valid old-context observations.
4. Exclude credentials, personal data, transcripts and private reasoning.
5. Run `python3 tools/chat_workflow.py check` when executable, review the diff,
   then publish through PROTOCOL's authorized conditional delivery procedure.

Change knowledge definitions/capabilities only with their authoritative source;
never rewrite adopted semantics. Record stale sources as open questions naming
the source the next worker must reconcile.
