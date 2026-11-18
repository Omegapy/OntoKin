---
name: ontokin-learning
description: Review evidence-backed OntoKin lessons after substantive verified work or an explicit learning request. Retrieve project memory, assess applicability, and capture authorized durable records without claiming automatic cross-session learning.
---

# Review and retain useful project knowledge

Read [PROTOCOL.md](../../../docs/workflow/PROTOCOL.md),
[memory.json](../../../docs/workflow/memory.json), and the relevant direct
sources. Use [knowledge.json](../../../docs/workflow/knowledge.json) to locate
terms, relationships, and capabilities. Reinspect current governing documents
before applying recalled conclusions.

These files provide explicit repository recall. They do not train a model,
create automatic cross-session memory, install a search service, or execute
background maintenance. New chats must read relevant records and sources.

## Retrieve and assess

With a terminal, use `python3 tools/chat_workflow.py lookup QUERY` for a bounded
lookup. Without one, inspect the JSON and [knowledge guide](../../../docs/workflow/KNOWLEDGE.md)
through the repository tools. Retrieval does not authorize a write.

After material verified work, ask whether the evidence supports a reusable
decision, lesson, constraint, or open question. Skip routine acknowledgments,
read-only requests, duplicated facts, speculative generalizations, and findings
whose only evidence is an agent's assertion. A useful review can find nothing
to save.

Record applicability and limits. A local test proves only the exercised inputs
and environment. Keep current decisions, historical observations, proposals,
and unresolved questions distinguishable. Do not turn a narrow success into
a general language, physics, destination, or comparative claim.

## Capture under current ownership

Respect an explicit opt-out. A request to discuss a lesson alone does not grant
new publication authority. Existing authorization for the current milestone
can cover scoped evidence-backed records; do not ask for permission again for
each note already within that authority.

Only the assigned canonical writer updates memory. Other workers return
proposals with evidence and allowed scope. Follow the Director's ownership and
integration procedure, including current-head checks, for publication.

Before adding a record:

1. Search existing IDs and summaries for a matching finding.
2. Choose a stable ID, kind, status, concise summary, scope, and recorded date.
3. Link exact source evidence, using an immutable commit URL for observations
   tied to specific bytes when available. A live specification link identifies
   current authority; it does not freeze an old test result.
4. Add only supported new information. When replacing a conclusion, retain the
   earlier record as `superseded` and point the new record's `supersedes` to it.
   Use `historical` for an observation that remains valid for its old context.
5. Do not store credentials, personal data, transcripts, or private reasoning
   in these records. Store concise conclusions and public project evidence.
6. Run `python3 tools/chat_workflow.py check` when executable tools are present,
   review the diff, and publish only through the authorized delivery procedure.

Update knowledge definitions or capability status only when their authoritative
source changes. Do not rewrite OntoKin's adopted language semantics in this
navigation map. Record stale-source concerns as open questions and direct the
next worker to the source that must be reconciled.
