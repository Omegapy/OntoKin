# C263 requirements: development through browser chats

Status: implementation in progress. [Task record](task.json) tracks acceptance.

## Intent and scope

The owner wants to develop OntoKin through successive ChatGPT browser chats,
with the repository holding the instructions, work state and evidence that each
chat needs. Adapt the useful behavior in the supplied Sys4AI reference files:
explicit startup, Director accountability, bounded delegation, requirements,
plans, memory, learning and project knowledge. The owner explicitly requested
implementation in GitHub after requirements extraction and planning.

This is one workflow increment, C263, under [scope252](https://github.com/Omegapy/OntoKin/issues/252).
It does not implement the source hinge observer queued by C262. Complete this
workflow, integrate verified work and wait for the owner's next direction.
Routine continuation no longer requires creating or restoring a handoff ZIP.
Retain the existing archive and its historical evidence.

## Requirements and observable acceptance

| ID | Requirement | Acceptance |
| --- | --- | --- |
| R01 | GitHub holds the operational workflow and current checkpoint. | One stable entry URL and reusable prompt locate the current task without a ZIP or prior chat. |
| R02 | Read instructions explicitly at an observed revision. | Entry instructions require AGENTS, GOAL, STATUS, ROLE, current task and selected skills; distinguish Codex discovery from browser behavior. |
| R03 | Use capabilities actually available in the session. | Record read/write/merge/test/subagent access; unavailable tools produce precise limits, never fictional execution or a universal browser restriction. |
| R04 | Give one Director accountability and bounded worker roles. | Assignments identify owner, inputs, write scope, evidence and stop condition; one verified owner integrates main. |
| R05 | Extract intent into traceable requirements. | Each requirement has a stable ID, observable acceptance and evidence; user changes revise scope explicitly. |
| R06 | Maintain a durable implementation plan. | Every requirement maps to a plan step with outputs, verification and status; completion cannot leave an in-scope requirement unaccounted for. |
| R07 | Recover work across chats and unknown write outcomes. | Reconcile live refs/PRs/lease with checkpoint; resume the existing scope; record unpublished work and retry only after readback. |
| R08 | Record actual verification and honest completion. | Changes have revision-specific checks and review; unrun/failed checks remain visible; structural checks do not certify live GitHub or product semantics. |
| R09 | Integrate completed work and resolve its branch. | Verify PR/main result and head retention, then confirm deletion or give the owner the exact safe-to-delete branch. |
| R10 | Retain project memory and lessons with evidence. | Read-only retrieval exposes source and applicability; completion considers a deduplicated lesson; opt-outs are respected and historical memory cannot overrule current instructions. |
| R11 | Provide source-backed project knowledge navigation. | Terms, typed relationships and capability limits link to adopted sources; the map does not introduce new OntoKin semantics or an inference engine. |
| R12 | Load reusable repository skills only when relevant. | A registry names each skill, trigger and path; skill files are explicitly read and are not represented as installed browser features. |
| R13 | Supply small executable workflow tools and a browser-only route. | Standard-library check, brief, lookup and draft-task creation work; connector-only sessions can follow the same records manually without claiming unrun tests. |
| R14 | Preserve OntoKin's product and operational constraints. | Product source, fixtures, budgets, frozen evidence and manual-only hosted workflows remain unchanged; current documentation keeps earlier failures and deferred domains visible. |
| R15 | Ground the adaptation in the supplied sources. | Source register distinguishes inspected files, official documentation, verified video metadata and missing implementation/transcript evidence. |
| R16 | Finish one bounded workflow delivery and stop. | Current state records completion, links to evidence and waits for user direction; the scientific next task remains a separately selectable scope. |

## Deliberate boundaries

The supplied files describe a local Sys4AI depot. Its desktop app, template
propagation, native task service, Basic Memory backend, RDF/SPARQL/SHACL runtime,
automatic schedules and complete role packages were not supplied. This
increment implements repository procedures and a small offline tool; it does
not claim those systems are installed. Instructions cannot create permissions,
subagents, a terminal, model settings or persistence beyond available tools.

The existing product Agent protocol is a different system: it lets software
edit and inspect `.ok` programs. C263 governs agents developing the repository.

## Sources and plan

The [source register](../../../engineering/browser-workflow-c263/SOURCES.md)
records what was actually inspected. The [implementation plan](PLAN.md) maps
these requirements to concrete work. The current owner request governs this
scope; older archive next-task instructions remain historical evidence.
