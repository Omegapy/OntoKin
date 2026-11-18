# C263 implementation plan

Plan prepared before implementation on November 18, 2026.
Owner: `c263-root-c3681d8a01ea`.
Base: `bbe30e2f5863d743bd2393466341511b4924ad9d`.
Scope: [issue252](https://github.com/Omegapy/OntoKin/issues/252).
Branch: `work/c263-browser-workflow`.

## Sequence and ownership

| Step | Work and outputs | Requirements | Owner and dependency | Verification |
| --- | --- | --- | --- | --- |
| P01 | Reconcile main, C262 delivery, supplied reference files and official sources; write requirements and this plan. | R05, R15 | Director; first | Inspect full selected records and distinguish observed facts from proposals. |
| P02 | Add stable entry, reusable prompts, role and protocol; make current STATUS short with exact historical preservation. | R01, R02, R03, R07, R14, R16 | Director after P01 | Cold-start read-through, preservation hashes and existing documentation checker. |
| P03 | Add registered session/delivery/learning skills, worker/session templates, memory and knowledge map. | R04, R10, R11, R12 | Documentation worker after P01; disjoint files | Inspect source references, authority boundaries and handoff examples. |
| P04 | Implement offline check, brief, lookup and draft task creation with failure-path tests. | R06, R08, R13 | Tooling worker after schema agreement | Run actual CLI operations and unit tests, including malformed and unsafe inputs. |
| P05 | Review complete workflow independently and exercise fresh-start/recovery scenarios; correct defects and record evidence. | R02, R03, R06, R07, R08, R10, R12, R13, R14 | Independent reviewer after P02-P04 | Structural check, authored tests, independent controls, cold-start exercise and documentation preservation check. |
| P06 | Publish reviewed candidate, acquire short integration lease, merge conditionally, check actual main and record branch disposition; stop. | R09, R16 | Director after P05 | Read back PR, main and branch inventory; rerun relevant checks on resulting main; publish completion record. |

The [task record](task.json) is the machine-readable status and acceptance
record. This plan explains the sequence; do not maintain an independent status
ledger in this prose. Update the task record when evidence changes.

## Working rules

Workers own nonoverlapping paths in the shared checkout. The Director owns the
root entry files, registry, task records and integration. No worker commits,
pushes or changes main independently. This is one branch for one active scope;
the repository's general parallel-branch policy remains available for future
independent scopes. Parallelism is actual only when workers have been spawned.

Current user authorization covers implementation and GitHub publication.
Acquire the main integration lease only after reviewable work exists. Recheck
main before merging; if it moved, reconcile and repeat affected checks. Preserve
unknown write outcomes and inspect the remote before retrying.

## Verification scope

Run the new workflow tests and the existing documentation/preservation checker.
Exercise draft creation in a disposable directory and prove it cannot overwrite
an existing task or alter the current checkpoint. Check plan coverage, missing
evidence, malformed records, escaped paths and misleading done states. Review
one new-chat startup and one interrupted-write scenario from the entry file.

Product source and contracts are unchanged. Do not rerun expensive product
benchmarks or start native tools merely to validate workflow documentation.
Preserve the inherited regression failure and deferred scientific gates.

## Risks and recovery

- Browser capabilities vary. Explicit read order and capability observations
  support both connector-only and terminal-capable sessions.
- An old ZIP or long status can misdirect the next chat. Current entry/state
  points to concise records, while original history remains accessible.
- A schema can verify structure but not truth. Independent artifact review and
  actual remote readback remain required.
- Main can move during work. Expected-head updates and a bounded lease serialize
  integration without granting permanent ownership.

Stop after P06. Wait for the owner before selecting the source hinge observer
or another product milestone. A new ZIP is outside this delivery request.
