# Project knowledge and recall

Use this page to find OntoKin's governing sources and bounded capability
records. [knowledge.json](knowledge.json) contains terms, relationships and
capability entries; [memory.json](memory.json) contains source-backed decisions,
constraints, lessons and open questions. These records support explicit recall
across browser chats when the agent reads them.

This knowledge map provides navigation. It changes no adopted language
semantics, proves no new release or comparative result, and implements no
RDF/SPARQL/SHACL, inference, vector retrieval, or background learning service.
Current source documents govern their own subject. An older memory record must
be checked against those sources before it is applied.

## Find the authoritative source

| Need | Start here | Boundary |
| --- | --- | --- |
| Product purpose and current priority | [GOAL](../../GOAL.md) and [C252 decision](../engineering/review-integration-c252/DECISION.md) | Current scope remains semantic authoring and evidence-based investment. |
| Current work and actual observations | [CURRENT](CURRENT.json), [STATUS](../../STATUS.md), and the linked live issue/PR | A saved checkpoint can become stale; reconcile live GitHub before writing. |
| Language meaning and adopted profiles | [Specification index](../README.md) | Separate adopted contracts from proposals and measured implementation support. |
| Source-authoritative object repair | [GOAL](../../GOAL.md) and [Agent contracts](../engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) | Supported behavior depends on the named source/Agent/export profile. |
| Localized-repair qualification | [C253 protocol](../engineering/localized-repair-c253/README.md) | A public qualification family does not demonstrate a general authoring advantage. |
| Hinge declarations and observation boundaries | [C260 contract](../engineering/localized-repair-c260/CONTRACT.md), [C261 reader](../engineering/localized-repair-c261/README.md) and [C265 source observer](../engineering/localized-repair-c265/README.md) | Raw metadata claims, independent source facts, comparison and historical admission are separate. |
| Verification and integration | [AGENTS](../../AGENTS.md), [OK-ENG-006](../engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md), and [OK-ENG-009](../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) | Applicable checks and resulting-main evidence govern an increment; a merge alone is not a full release. |
| Browser-chat operation | [Entry point](../../CHATGPT-START-HERE.md), [Director role](../../ROLE.md), and [protocol](PROTOCOL.md) | Repository instructions do not create execution tools or platform permissions. |

## Read the records

For a local checkout with an execution tool:

```sh
python3 tools/chat_workflow.py lookup hinge
python3 tools/chat_workflow.py lookup integration
python3 tools/chat_workflow.py brief
```

The helper is a deterministic lookup and summary tool. Open the referenced
source before relying on a claim. Without an execution tool, fetch the JSON
files and relevant sources directly through GitHub.

Memory records distinguish `current`, `historical`, `proposed`, `unresolved`,
and `superseded`. A superseding record identifies the old record; history is
retained. Capability entries have explicit status and limits. `documented`
means a governing procedure or contract exists, not that this session has
executed it. `partial` identifies a bounded implementation whose broader
obligations remain open. `unimplemented` and `deferred` remain visible.

Current hinge records distinguish C261 raw artifact observation and C265
independent source observation from the unfinished source/artifact comparison
and historical admission interfaces. Site poses remain unevaluated. Neither
component establishes physical, native-engine or model-trial validity.

## Maintain useful knowledge

Follow [ontokin-learning](../../.agents/skills/ontokin-learning/SKILL.md).
Capture only useful supported findings under the current owner's write scope.
Check for duplicates, cite the real source, state applicability, and preserve
earlier records when conclusions change. Honor the user's capture opt-out.

Run `python3 tools/chat_workflow.py check` after authorized record edits when
execution is available. This checks structure and references; a human or agent
still has to assess whether cited evidence supports each conclusion. Update
capability status only after the corresponding source and verification record
justify it.
