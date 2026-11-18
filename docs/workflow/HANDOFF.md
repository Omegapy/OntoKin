# Required browser-session handoff

The owner's [C264 clarification](tasks/C264/REQUIREMENTS.md) requires a verified
handoff ZIP saved in ChatGPT Library at the end of each bounded browser-chat
task. GitHub holds current code, instructions and task state. The ZIP supplies
a portable session checkpoint for the next chat. Use the
[continuation and recovery prompts](BROWSER-PROMPTS.md) with this contract.

## Preserve progress before the thread ends

A thread can end before a final response. Do not depend on automatic context
compaction, an advance warning, a remaining-message estimate or a final chance
to save. Create an early durable checkpoint after reconciling the starting
state and selecting the authorized scope. Update it after meaningful phases:
requirements and plan, implementation, verification/review, integration and
delivery. Checkpoint before a long operation or a handoff between workers.

Publish recoverable progress on the existing task branch or in its scope
record. Preserve actual unpublished bytes through an appropriate committed
checkpoint, patch, Git bundle or saved recovery file. A path in a temporary
workspace and a prose description do not preserve missing files. Keep unique
partial work and failed results. Identify unresolved workers, processes and
writes; record the intended target, parent/tree/commit or operation identity
needed to reconcile them. A timeout does not prove failure.

Save an early recovery file when important work cannot yet be recovered from
GitHub. After an interruption, reconcile live refs, the task, ownership, saved
files and unknown operations before retrying. Resume the unfinished scope and
branch. If implementation is already integrated, finish only the outstanding
verification, cleanup or delivery steps; do not start the next milestone.

## Package type and preservation boundary

Identify the new package as a **browser-session handoff for online GitHub
continuation**. It must be usable without the previous conversation. It is not
a full offline repository restoration package. State this boundary in its root
README and checkpoint, and identify any required external inputs.

Keep the original C262 archive unchanged. Record its stable Library identity,
link, byte count and SHA-256 in `HISTORICAL-DEPENDENCIES.json`; its registered
identity is in [CURRENT.json](CURRENT.json). Historical recovery may require
that archive, but ordinary online continuation does not require reconstructing
it. The [C263 migration record](../engineering/browser-workflow-c263/MIGRATION.md)
describes the preserved historical boundary.

Do not copy the whole C262 ZIP into each session ZIP or treat links as proof of
a complete offline backup. Any separately requested full offline successor
must still satisfy the original restoration and preservation contract,
including inherited aliases, bytes, modes, hashes, source references and
applicable verification. This session format does not weaken that contract.

## Required contents

Use these exact root filenames so both reusable prompts have a stable entry.

| File | Required meaning |
| --- | --- |
| `README-START-HERE.md` | Package type, reading order, current GitHub entry point, source revision, external dependencies and recovery limits. |
| `CHECKPOINT.json` | Task and scope; observed main SHA/tree and time; active branch/head, PR and issue; integration ownership; completed/incomplete steps; evidence; delivery state; exact next action. |
| `HANDOFF.md` | Changes and decisions, requirements/plan progress, actual verification and review, failures, unrun checks, limits and remaining work. |
| `NEXT-TASK.md` | One authorized continuation or explicit wait for user direction, with inputs, acceptance condition and stopping point. A queued suggestion is not automatic authority to start. |
| `RECOVERY-STATUS.md` | Partial work and its durable location, unresolved operations/workers, required readbacks, blockers and outstanding delivery. State explicitly when none are known. |
| `PROMPT-1-CONTINUE.md` | Complete reusable normal continuation prompt. |
| `PROMPT-2-RECOVER.md` | Complete reusable interrupted-thread recovery prompt, including delivery-only recovery. |
| `HISTORICAL-DEPENDENCIES.json` | Exact known identities and purpose of retained archives and other external dependencies; distinguish online continuation from historical offline restoration. |
| `MANIFEST-SHA256.json` | Complete payload inventory with relative paths, byte counts and SHA-256 hashes. Exclude the manifest itself from its hash inventory. |

Include a frozen repository read-set under `repository/`, preserving repository
relative paths. Include `CHATGPT-START-HERE.md`, `AGENTS.md`, `GOAL.md`,
`STATUS.md`, `ROLE.md`, the workflow registry, protocol, current checkpoint,
handoff contract, reusable prompts, active/latest task with requirements and
plan, and the full selected skill files. Identify every snapshot's Git commit
and path. Include further specifications only when the next action needs them;
otherwise link to their exact GitHub revision and identify that dependency.

Include actual unique unpublished/WIP recovery files when present, with their
base revision and application instructions. Include concise verification and
review evidence, or durable public links pinned to the inspected revision.
Preserve failed and incomplete results. Do not embed credentials, private
reasoning or complete conversation transcripts. Saved snapshot observations
can become stale; the next chat must reconcile them with live GitHub.

## Verify, freeze and save

1. Verify that required files exist, the checkpoint agrees with observed
   repository state, and the next action is executable with the named inputs.
   Record which checks passed, failed or were not run.
2. Check ZIP integrity, safe relative paths, duplicate names and the exact
   payload inventory. Verify every declared size/hash after extracting the
   final ZIP into a fresh directory. Check frozen repository files against
   their declared source revisions. These checks do not prove a full historical
   restore or product qualification.
3. Freeze the verified ZIP. Record its actual filename, byte count and SHA-256
   outside the package. Save it in the existing `OntoKin` Library folder and
   inspect the actual save result. Preserve the previous handoff; use a distinct
   task/checkpoint filename. Do not silently replace an immutable archive.
4. Record an external delivery receipt in the task's GitHub evidence. Include
   the saved Library identity/link, known version, archive identity, packaged
   Git revision, verification evidence and save outcome. Return the confirmed
   handoff link and downloadable prompt files to the owner.

If a save has an unknown result, look for that exact operation/file before
retrying. A locally created ZIP, a proposed destination or an upload attempt
does not establish saved delivery. If saving is unavailable or fails, preserve
useful work and record delivery as blocked or pending; do not mark the task
complete or claim the file is available.

## Integrated, delivered and complete

Keep these observations distinct. **Integrated** means the reviewed change is
on actual main with the applicable verification recorded. **Delivered** means
the verified handoff ZIP has a confirmed Library save. **Complete** requires
both, plus the task's remaining acceptance and branch-lifecycle obligations.
An unfinished branch stays recoverable across chats. A completed merged branch
is deleted after safe retention checks, or explicitly recorded as
`deletion_pending` with the exact user action when deletion tools are absent.

A ZIP cannot contain its own future save receipt. Its frozen checkpoint may
therefore say `save_pending` and point to the task's external delivery record.
After the save succeeds, publish that receipt, update current task state,
release integration ownership and close the scope as appropriate. This later
receipt/closure commit does not require recursively rebuilding the ZIP. The
next chat reads live GitHub to reconcile that deliberate boundary. A material
change to the packaged work or recovery instructions does require a newly
verified package and an updated delivery record.

After delivering one bounded scope, report its result and stop. Do not spend
the remaining thread on another milestone.
