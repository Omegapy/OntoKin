<!-- Generated projection. plan.json is canonical. Double-brace field markers define renderer inputs. -->

# {{phase.phase_id}} - {{phase.title}}

| Field | Value |
| --- | --- |
| Plan | `{{plan_id}}` |
| Phase status | `{{phase.status}}` |
| Depends on | {{phase.depends_on_phase_ids}} |
| Canonical revision | {{revision}} |

## Objective

{{phase.objective}}

## Scope

{{phase.scope_as_list}}

## Entry conditions

{{phase.entry_conditions_as_list}}

## Exit criteria

{{phase.exit_criteria_as_list}}

## Risks

{{phase.risks_as_list}}

## Task summary

| Task | Title | Status | Requirements | Depends on | Parallel group |
| --- | --- | --- | --- | --- | --- |
{{phase.tasks_as_rows}}

{{phase.task_detail_blocks}}

<!-- Each generated task detail block has this fixed order:
## TASK-NNN - Title
Action; status and state reason; requirement IDs; design basis; target artifacts;
dependencies and parallel group; risks; acceptance criteria; planned verification;
completion time; and evidence table with result status and target digest ordered by
the parsed absolute timestamp then evidence ID.
-->
