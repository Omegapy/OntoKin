# Session checkpoint

Use one concise checkpoint for a selected scope under [PROTOCOL.md](../PROTOCOL.md).
Keep it with the active task's GitHub records; link detailed evidence. Record
what was observed and what remains uncertain. Do not store full transcripts,
credentials, private reasoning, or an additional competing task ledger.

Fill every group from observed state; write `none`, `not applicable` or `not observed`
instead of leaving a field out. Fields marked (browser) or (local) belong to that
execution mode. A record written under an earlier form of this template stays valid.

## Identity

- Checkpoint time and author identity:
- Task, session, and agent or tool identity:
- Execution mode, and the entry document or record that declared it:
- Worktree and branch:
- Current user objective and bounded milestone:
- Task, requirements, and plan paths:

## Context loaded

- Entry file and registry revision:
- Required read-set actually opened, with revision or hash:
- Required files missing, truncated, or inaccessible:
- Current/deferred product work and applicable adopted contracts:

## Source

- Starting revision and current code checkpoint:
- Dirty and untracked state:
- Actual remote observation, with command and time, or offline and stale:
- Repository, actual main SHA/tree, and observation time:
- Active branch/head, open PR, and scope issue:
- Local checkout identity and unpublished changes, if a workspace exists:

## Work

- Requirements completed, incomplete, blocked, and excluded:
- Completed acceptance items and last completed gate:
- Changed artifact paths and exact code/input identities:
- Decisions made:
- Remaining items:
- Learning checkpoint result and capture preference:

## Environment

- Profile and its readiness:
- Interpreter, operating system and architecture:
- Manifest and lock identities:
- Relevant tool versions:
- Terminal and executed interpreter/platform:
- Available read/write/conditional-update/merge operations:
- Missing capabilities and their effect on this milestone:

## Verification

- Commands actually executed and observed outcomes:
- Failures:
- Pending and not-run checks:
- Durable logs, review findings, and evidence links:
- Evidence locations and hashes:
- Relevant validation/CI results and source revisions:
- Current review eligibility and any changes since review:

## Recovery

- Unpublished commits:
- Unique uncommitted files:
- Outstanding operations and owned processes:
- Unknown operation and its intended parent/tree/commit or request identity:
- Remote readback needed before retrying that operation:
- Current blockers with concrete evidence:
- Unpublished work that must be recovered and its known location:
- Actual unpublished recovery payloads and declared external dependencies:

## Coordination

- Active workers and reserved files:
- Actual subagents, assigned scopes, and unresolved worker activity:
- Integration owner, expiry, and latest verified ownership record:
- Lease status:
- Ownership released, renewed, transferred, or still uncertain:

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition:
- The condition that makes that action safe and useful to execute:

## Delivery

- Local checkpoint status:
- Verified push state, or unconfirmed:
- Actual merge/resulting-main checks, or remaining integration gate:
- Branch retention/deletion evidence, or exact pending cleanup instruction:
- Durable evidence references:
- Integration state separate from saved-delivery state:
- Published checkpoint revision and readback result:
- (browser) Required session ZIP delivery still open, with intended filename and folder:
- (browser) Latest confirmed saved recovery/handoff identity, version, size and SHA-256:

No receipt of the receipt: record the code checkpoint and its evidence here, and let
Git reveal the later commit that carries this record. Keep a later push observation,
when one is needed, as a separate small record; do not rebuild frozen evidence for it.

When resuming, reconcile this record with live GitHub before making changes.
An earlier timestamp, absent roster entry, or expired lease does not prove
that another worker stopped or that an uncertain write failed.
