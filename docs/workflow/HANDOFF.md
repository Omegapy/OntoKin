# Required browser-session handoff

[C264](tasks/C264/REQUIREMENTS.md): verified ZIP saved in ChatGPT Library.
[Conversation-length repair](tasks/CHAT-LENGTH-20261118/REQUIREMENTS.md): delivery for
every declared phase, including partial handoffs. GitHub remains current operational
state. Use complete [continuation/recovery prompts](BROWSER-PROMPTS.md).

## Preserve progress before the thread ends

Mandatory [PROTOCOL section 8](PROTOCOL.md#8-recovery-and-stopping) owns early confirmed
recovery, durable checkpoints, recoverable unpublished bytes, uncertain writes and
live reconciliation before existing-scope/delivery-only recovery. Apply it in full.

## Keep repeated recovery bounded

Mandatory [PROTOCOL section 4](PROTOCOL.md#4-implement-delegate-and-bound-the-session),
sections 5 and 8: one phase/chat, exact-evidence reuse, staged-payload checks, phase
table. Required startup reads: once at observed revision. Freeze a verified package
once; later save receipt stays external. Rebuild only for material payload or
recovery-instruction changes. No guaranteed thread warning/final save opportunity.

## Package type and preservation boundary

README/checkpoint must identify **browser-session handoff for online GitHub continuation**,
usable without preceding conversation; declare external inputs/limits. No full offline
restoration claim.

**New-host continuity:** Every fresh browser thread has a different,
disposable execution host. Do not present previous `/workspace` or `/tmp`
paths, installed environments, running processes or old host profiles as
resources available to the next thread. Save durable byte-verified artifacts
and portable reconstruction instructions, not promises of host persistence.
See [EPHEMERAL-HOST](EPHEMERAL-HOST.md). For packages created after this
clarification, include `HOST-ENVIRONMENT.md` and repeat the essential rule
in README and both prompts. Older immutable archives remain valid history.

C262: preserve unchanged; record stable Library identity/link, bytes, SHA-256 from
[CURRENT](CURRENT.json) in `HISTORICAL-DEPENDENCIES.json`. Historical restoration may
require C262; ordinary continuation need not reconstruct/embed it. Preserve
[C263 migration boundary](../engineering/browser-workflow-c263/MIGRATION.md). Links
do not prove complete backup. Separately requested full offline successor: original
contract, including inherited aliases, bytes, modes, hashes, source references,
verification.

## Required contents

Exact root filenames and required contents:

| File | Contents |
| --- | --- |
| `README-START-HERE.md` | Package type, reading order, GitHub entry, source revision, external dependencies, recovery limits. |
| `CHECKPOINT.json` | Task/scope/phase; observed main SHA/tree/time; branch/head, PR/issue, ownership; completed/incomplete steps, evidence, delivery state, exact next action. Session handoff separate from parent completion. |
| `HANDOFF.md` | Changes/decisions, requirements/plan progress, verification/review, failures, unrun checks, limits, remaining work. |
| `NEXT-TASK.md` | First unmet gate and one authorized next phase, or wait; inputs, acceptance, stop. Queued suggestion cannot displace active scope. |
| `RECOVERY-STATUS.md` | Partial work/durable location, unresolved workers/operations, readbacks, blockers, outstanding delivery; explicitly identify when none known. |
| `PROMPT-1-CONTINUE.md` | Complete reusable continuation prompt. |
| `PROMPT-2-RECOVER.md` | Complete reusable interruption-recovery prompt, including delivery-only recovery. |
| `HISTORICAL-DEPENDENCIES.json` | Exact known archive/dependency identities/purposes; online continuation versus historical offline restoration. |
| `MANIFEST-SHA256.json` | Every payload path, byte count, SHA-256; exclude manifest itself. |
| `HOST-ENVIRONMENT.md` (new handoffs) | Current-host-only execution rule; portable input identities, reconstruction plan, historical-path boundary. |

`repository/`: preserve relative paths for frozen START, AGENTS, GOAL, STATUS, ROLE,
registry, CURRENT, PROTOCOL, HANDOFF, reusable prompts, active/latest task with
requirements/plan, full selected skill files. Identify each snapshot's Git commit/path;
copy verified bytes without rereading unchanged text. Include specifications needed
by next action; otherwise exact-revision GitHub dependency links.

Include unique unpublished recovery files with base revision/application instructions;
concise verification/review evidence or durable public links pinned to inspected
revisions; failed/incomplete results. Exclude credentials, private reasoning, full
transcripts. Snapshots may be stale; next chat reconciles live GitHub.

## Verify, freeze and save

1. Check required files, checkpoint/observed-state agreement, executable next
   action/inputs. Record passed/failed/not-run.
2. Check ZIP integrity, safe relative paths, duplicate names, exact inventory.
   Extract final ZIP into fresh directory; verify every size/hash and frozen file
   against declared source revision. No full historical-restoration/product-qualification proof.
3. Freeze ZIP; externally record actual filename, bytes, SHA-256. Save in existing
   `OntoKin` Library folder; inspect result. Preserve previous handoffs/immutable
   archives with distinct task/checkpoint filenames.
4. External receipt in task GitHub evidence: saved Library identity/link, known
   version, archive identity, packaged Git revision, verification evidence, save
   outcome. Return confirmed handoff link and downloadable prompt files.

Unknown save: inspect exact operation/file before retry. Local creation, proposed
destination, attempted upload are not saved delivery. Unavailable/failed: preserve
work; record delivery blocked/pending; claim no availability/task completion.

## Integrated, delivered and complete

**Integrated**: reviewed change on actual main with applicable verification.
**Delivered**: verified ZIP, confirmed Library save. **Complete**: both, all task
acceptance/branch-lifecycle obligations. Partial handoff delivers only session;
parent stays `in_progress`/`review`, with open issue, recoverable branch, remaining
gates. Planned pause is not blocker. Completed branches: mandatory PROTOCOL section 7,
including exact `deletion_pending` instructions when tools absent.

ZIP cannot contain future save receipt; checkpoint may say `save_pending` and point
to external delivery record. After confirmed save: publish receipt; update actual
phase/gates; release ownership appropriately. Close only after all parent gates pass.
Receipt/closure commit needs no rebuild; reconcile boundary through live GitHub.
Material packaged-work/recovery-instruction change: newly verified package/updated receipt.

After delivery: report phase result; stop. Resume unfinished work in fresh parent chat.
