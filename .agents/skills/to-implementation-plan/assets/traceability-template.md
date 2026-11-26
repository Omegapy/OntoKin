<!-- Generated projection. plan.json is canonical. Double-brace field markers define renderer inputs. -->

# Traceability for {{plan_id}}

| Field | Value |
| --- | --- |
| Plan title | {{title}} |
| Plan status | `{{status}}` |
| Canonical revision | {{revision}} |
| Validation result | `{{validation.status}}` |

## Source to requirement

| Source | Requirements | Disposition |
| --- | --- | --- |
{{coverage.source_to_requirement_as_rows}}

## Requirement to task

| Requirement | Tasks | Disposition |
| --- | --- | --- |
{{coverage.requirement_to_task_as_rows}}

## Requirement acceptance and evidence

| Requirement | Acceptance criteria | Status | Evidence | Open finding |
| --- | --- | --- | --- | --- |
{{requirements_acceptance_as_rows}}

## Reverse task basis

| Task | Phase | Requirements | Design basis | Coverage result |
| --- | --- | --- | --- | --- |
{{tasks_reverse_basis_as_rows}}

## Coverage findings

| Finding | Severity | Status | Code | Targets | Message |
| --- | --- | --- | --- | --- | --- |
{{coverage_findings_as_rows}}
