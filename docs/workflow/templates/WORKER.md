# Bounded worker assignment

Use this template for an actual subagent assignment under [ROLE.md](../../../ROLE.md)
and [PROTOCOL.md](../PROTOCOL.md). Fill the fields with observed facts; use
`unavailable`, `unverified`, or `not applicable` rather than inventing a value.
An assignment document does not prove that a worker was launched.

## Identity and objective

- Task and requirement IDs:
- Assigning Director and actual worker identity:
- Role and required role/procedure paths:
- One bounded objective:
- Completion criteria and stopping condition:
- Actual subagent capability and launch receipt:
- Model/settings inheritance evidence, if required and available:
- Independence requirement and context supplied:

## Inputs and ownership

- Repository and observed base/main SHA:
- Candidate commit or exact input hashes:
- Files actually read, with revisions:
- Allowed reads:
- Exclusive allowed writes:
- Protected files and shared state:
- Dependencies and other workers' ownership:
- Branch or shared-workspace arrangement authorized by the Director:
- Current integration owner; worker integration authority, if any:
- Available tools and specific missing capabilities:

## Delivery and checks

- Required artifact paths and output format:
- Applicable commands and acceptance evidence:
- One concrete way the Director can inspect or exercise the result:
- Mandatory review or external gates:
- Known input limitations and unresolved questions:

## Worker return

- Actual changed paths and artifact identities:
- Executed checks, environment, observed outcomes, and evidence paths:
- Requirement coverage and unmet criteria:
- Findings, assumptions, and recommendations kept distinct:
- Any incomplete operation, unknown write, or active process:
- Integration or publication performed, with observed receipts; otherwise none:
- Exact next action and ownership disposition:

Return evidence to the Director. Do not update canonical task state, CURRENT,
STATUS, memory, or another worker's branch without a specific write assignment.
Do not treat a bounded worker result as whole-project completion.
