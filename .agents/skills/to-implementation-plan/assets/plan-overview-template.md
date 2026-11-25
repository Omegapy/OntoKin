<!-- Generated projection. plan.json is canonical. Double-brace field markers define renderer inputs. -->

# {{title}}

## Plan identity

| Field | Value |
| --- | --- |
| Plan ID | `{{plan_id}}` |
| Status | `{{status}}` |
| Status reason | {{status_reason}} |
| Revision | {{revision}} |
| Created | {{created_at}} |
| Updated | {{updated_at}} |
| Initial record IDs | {{initial_record_ids}} |
| Canonical SHA-256 | `{{canonical_sha256}}` |
| Managed directory | `{{managed_directory}}` |

## Objective

{{objective.summary}}

User value: {{objective.user_value}}

### Success outcomes

{{objective.success_outcomes_as_list}}

## Scope

### In scope

{{scope.in_scope_as_list}}

### Out of scope

{{scope.out_of_scope_as_list}}

### Execution authority

{{scope.execution_authority}}

## Project baseline

Root hint: `{{project.root_hint}}`

Inspected: {{project.inspected_at}}

### Guidance inspected

| Path | Observed | Digest | Summary |
| --- | --- | --- | --- |
{{project.guidance_as_rows}}

### Observed facts

| Fact | Evidence | Observed |
| --- | --- | --- |
{{project.baseline_facts_as_rows}}

### Constraints

{{project.constraints_as_list}}

### Preserved paths

{{project.preserved_paths_as_list}}

### Evidence gaps

{{project.evidence_gaps_as_list}}

## Sources

| Source | Kind | Title | Locator | Accessed | Digest | Inspection method | Limitations |
| --- | --- | --- | --- | --- | --- | --- | --- |
{{sources_as_rows}}

## Requirements

| Requirement | Outcome | Status | Sources | Evidence count |
| --- | --- | --- | --- | ---: |
{{requirements_as_rows}}

## Decisions

| Decision | Status | Statement | Authority |
| --- | --- | --- | --- |
{{decisions_as_rows}}

## Open questions

| Question | Status | Affects | Answer |
| --- | --- | --- | --- |
{{open_questions_as_rows}}

## Assumptions

| Assumption | Status | Statement | Basis |
| --- | --- | --- | --- |
{{assumptions_as_rows}}

## Phase summary

| Phase | Title | Status | Depends on | Tasks |
| --- | --- | --- | --- | ---: |
{{phases_as_rows}}

## Latest validation

| Field | Value |
| --- | --- |
| Checked revision | {{validation.checked_revision}} |
| Checked at | {{validation.checked_at}} |
| Result | `{{validation.status}}` |

{{validation.findings_as_table}}

## Recent history

| Revision | Timestamp | Action | Affected IDs | Status change | Summary | Authority |
| ---: | --- | --- | --- | --- | --- | --- |
{{history_as_rows}}
