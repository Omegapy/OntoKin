# Required browser-session handoff

[C264](tasks/C264/REQUIREMENTS.md) requires verified ZIPs saved in ChatGPT Library;
the [conversation-length repair](tasks/CHAT-LENGTH-20261118/REQUIREMENTS.md)
requires delivery for each declared phase, including partial handoffs.
GitHub remains the current operational state. Use the complete
[continuation and recovery prompts](BROWSER-PROMPTS.md).

## Preserve progress before the thread ends

Follow [PROTOCOL section 8](PROTOCOL.md#8-recovery-and-stopping) for early confirmed
recovery, durable checkpoints and uncertain writes. Preserve actual unpublished
bytes through a committed checkpoint, patch, Git bundle or saved recovery file;
a temporary path or description cannot recover missing bytes. Include work
unrecoverable from GitHub, failed results and unresolved workers/processes/writes.
Reconcile live refs, task, ownership, saved files and unknown operations before
resuming the existing scope, including delivery-only recovery.

## Keep repeated recovery bounded

Follow [PROTOCOL section 4](PROTOCOL.md#4-implement-delegate-and-bound-the-session)
for one phase per chat, section 5 for exact-evidence reuse and staged-payload
checks, and section 8 for the phase table. Required startup reads remain
mandatory once at the observed revision. Freeze a verified package once; its
later save receipt is external. Rebuild only for material payload or
recovery-instruction changes. Thread warnings or a final chance to save are
not guaranteed.

## Package type and preservation boundary

Identify the package in its README/checkpoint as a **browser-session handoff for
online GitHub continuation**, usable without the preceding conversation.
Declare external inputs and limits; it is not a full offline restoration.

Preserve C262 unchanged. Record its stable Library identity/link, bytes and
SHA-256 from [CURRENT](CURRENT.json) in `HISTORICAL-DEPENDENCIES.json`.
Historical restoration may require it; ordinary continuation does not require
reconstructing or embedding it. Preserve the [C263 migration boundary](../engineering/browser-workflow-c263/MIGRATION.md).
Links do not prove a complete backup. A separately requested full offline
successor must satisfy the original contract, including inherited aliases,
bytes, modes, hashes, source references and verification.

## Required contents

Use these exact root filenames:

| File | Required content |
| --- | --- |
| `README-START-HERE.md` | Package type, reading order, GitHub entry, source revision, external dependencies and recovery limits. |
| `CHECKPOINT.json` | Task/scope/phase; observed main SHA/tree/time; branch/head, PR/issue, ownership; completed/incomplete steps, evidence, delivery state and exact next action. Separate session handoff from parent completion. |
| `HANDOFF.md` | Changes/decisions, requirements/plan progress, verification/review, failures, unrun checks, limits and remaining work. |
| `NEXT-TASK.md` | First unmet gate and one authorized next phase, or wait for direction; inputs, acceptance and stopping point. A queued suggestion cannot displace an active scope. |
| `RECOVERY-STATUS.md` | Partial work/durable location, unresolved workers/operations, readbacks, blockers and outstanding delivery; explicitly identify when none are known. |
| `PROMPT-1-CONTINUE.md` | Complete reusable continuation prompt. |
| `PROMPT-2-RECOVER.md` | Complete reusable interruption-recovery prompt, including delivery-only recovery. |
| `HISTORICAL-DEPENDENCIES.json` | Exact known archive/dependency identities and purposes; distinguish online continuation from historical offline restoration. |
| `MANIFEST-SHA256.json` | Complete payload paths, byte counts and SHA-256 hashes, excluding the manifest itself. |

Under `repository/`, preserve relative paths for the frozen START, AGENTS, GOAL,
STATUS, ROLE, registry, CURRENT, PROTOCOL, HANDOFF, reusable prompts,
active/latest task with requirements/plan, and full selected skill files.
Identify each snapshot's Git commit/path; copy verified bytes without rereading
unchanged text. Include further specifications needed by the next action;
otherwise identify dependencies through exact-revision GitHub links.

Include unique unpublished recovery files with base revision and application
instructions, plus concise verification/review evidence or durable public links
pinned to inspected revisions. Retain failed/incomplete results. Exclude
credentials, private reasoning and full transcripts. Snapshots can become stale;
the next chat reconciles live GitHub.

## Verify, freeze and save

1. Check required files, checkpoint agreement with observed state and executable
   next action/inputs. Record passed, failed and not-run checks.
2. Check ZIP integrity, safe relative paths, duplicate names and exact inventory.
   Extract the final ZIP into a fresh directory; verify every size/hash and each
   frozen file against its declared source revision. This proves neither full
   historical restoration nor product qualification.
3. Freeze the ZIP; record actual filename, bytes and SHA-256 externally. Save in
   the existing `OntoKin` Library folder and inspect the result. Preserve previous
   handoffs and immutable archives with distinct task/checkpoint filenames.
4. Publish an external receipt in the task's GitHub evidence: saved Library
   identity/link, known version, archive identity, packaged Git revision,
   verification evidence and save outcome. Return the confirmed handoff link
   and downloadable prompt files.

For an unknown save, inspect that exact operation/file before retrying.
Local creation, a proposed destination or attempted upload is not saved delivery.
If unavailable/failed, preserve work and record delivery blocked/pending; do not
claim availability or task completion.

## Integrated, delivered and complete

**Integrated** means the reviewed change is on actual main with applicable
verification. **Delivered** means a verified ZIP has a confirmed Library save.
**Complete** requires both, all task acceptance and branch-lifecycle obligations.
A partial handoff delivers only that session: retain the parent's `in_progress`
or `review` state, open issue, recoverable branch and remaining gates. A planned
pause is not a blocker. Handle completed branches under PROTOCOL section 7,
including exact `deletion_pending` instructions when tools are absent.

A ZIP cannot contain its future save receipt: its checkpoint may say
`save_pending` and reference the external delivery record. After confirmed save,
publish that receipt, update actual phase/gates and release ownership as
appropriate. Close only after all parent gates pass. A receipt/closure commit
does not require rebuilding the ZIP; reconcile that boundary through live
GitHub. Material changes to packaged work/recovery instructions require a newly
verified package and updated receipt.

After delivery, report the phase result and stop. Resume unfinished work in a
fresh parent chat.
