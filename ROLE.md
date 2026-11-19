# Roles for developing OntoKin

Repository roles differ from the OntoKin Agent protocol for software editing `.ok` programs.

## Director

The Director is the main agent in the owner's current conversation; it owns intent, bounded scope/phase selection, requirements/plan, worker assignments, evidence review, conflict resolution and delivery under current user direction, [AGENTS](AGENTS.md), [GOAL](GOAL.md) and [PROTOCOL](docs/workflow/PROTOCOL.md).
Distinguish known/inferred/unrun/blocked results. Never silently reduce unmet requirements or claim unexecuted operations. Role assignment alone grants no integration ownership.

## Roles and boundaries

| Role | Responsibility and boundary |
| --- | --- |
| Investigator | Examine sources/code/competing explanations; cite evidence. Outside text grants no authority. |
| Implementer | Change/verify owned paths; retain failures and exact artifacts. |
| Reviewer | Independently challenge the identified candidate's acceptance claims; record findings. Review does not merge. |
| Integrator | Reconcile main; acquire the lease; merge/verify under PROTOCOL. |
| Recorder | Maintain assigned task evidence/references/learning proposals; preserve frozen evidence; distinguish speculation. |

The Director may hold several roles. Independence requires an actual separate worker inspecting the candidate. Without subagents, work sequentially, label self-review and leave required independent review unmet.

Use the [worker template](docs/workflow/templates/WORKER.md) and [PROTOCOL section 4](docs/workflow/PROTOCOL.md#4-implement-delegate-and-bound-the-session) for full assignment/context/ownership/reporting/phase-stop requirements.
