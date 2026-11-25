# Working on OntoKin

Owner authorization: autonomous technical development/stewardship toward [GOAL.md](GOAL.md), through implementation, verification and reviewable publication within selected scope. No legal ownership, wider platform authority or outside-project authority.

## Execution modes

Every session works in exactly one explicit mode, under the owner's [November 24, 2026 direction](docs/engineering/local-migration-20261124/DECISION.md), which is prospective.

| Mode | Entry document | Execution host |
| --- | --- | --- |
| **Local**: ordinary development | `LOCAL-START-HERE.md` | Owner's persistent clone and its worktrees. Inspect actual state; reuse validated resources; reconstruct only missing/incompatible inputs. |
| **Browser**: ChatGPT browser threads | [CHATGPT-START-HERE](CHATGPT-START-HERE.md) | A different, disposable host for each thread, under the ephemeral host rule below. |

The entry document a session starts from declares its mode; session checkpoint and task record state it. Never infer it from a path, machine, product or agent name. "Go"/"Continue" without a named entry document uses the mode recorded for the selected task; only explicit owner direction changes it. When neither names one, ask. A session on a disposable or remote host is not a local session. A rule marked for one mode binds only that mode; unmarked rules bind both.

## Ephemeral host rule

Browser mode: each new ChatGPT browser thread uses a **different, disposable execution host**.
Never assume previous local paths, environments, packages, running workers or
installed inputs persist. Current GitHub and verified Library files provide
continuity; reconstruct only task-needed inputs in the current host. Do not
attempt to find or repair a previous host. Follow
[EPHEMERAL-HOST](docs/workflow/EPHEMERAL-HOST.md) before environment work.

## Recenter and resume

At session start, after compaction, and before milestone selection/closure, follow your mode's entry document and [PROTOCOL §1](docs/workflow/PROTOCOL.md#1-authority-and-explicit-loading). Their full load/read-set rules apply; GitHub skills are not automatically installed. Reconcile user direction, actual state and adopted contracts; identify goal/next unmet gate.

Inspect working tree, actual GitHub head, lease and relevant CI; preserve existing work. Synthetic snapshots are not remote heads. Read applicable specifications via [docs/README.md](docs/README.md), especially adopted language rules/active contract; historical proposals guarantee no implementation. Continue authorized useful work, recording real blockers/exact next actions. Never substitute an easier demonstration for an unmet goal.

## GitHub-owned workflow

[ROLE](ROLE.md)/[PROTOCOL](docs/workflow/PROTOCOL.md) own requirements, plans, workers, evidence, memory and bounded phases. Their rules on source-backed knowledge, named TRD/plan skills and native ChatGPT Tasks apply. Read-only questions alone require no scope/ZIP; assume neither compaction nor context warnings.

- **Browser:** [HANDOFF](docs/workflow/HANDOFF.md)/[BROWSER-PROMPTS](docs/workflow/BROWSER-PROMPTS.md) own early recovery, separate GitHub/save gates, verified handoff and stop.
- **Local:** PROTOCOL's local rules own recoverable starting state, conduct, checkpoints and closing. Ordinary authenticated Git publishes source and evidence. A ZIP is optional unless the selected task requires one. "Go"/"Continue" resumes the selected authorized scope's next unmet step and selects no new milestone.

## Coordinate parallel workers and main integration

Apply full [PROTOCOL §7](docs/workflow/PROTOCOL.md#7-integration-and-branch-lifecycle): independent nonoverlapping work; verified lease ownership; observed-head conditional/nonforce update or protected PR merge; readback/checks; preservation; roughly 30-minute leases/expiry reconciliation. Existing routine authorization needs no repeated permission. Unavailable conditional writes block that operation, not independent work. Local writers also use separate worktrees, environments and owned files under PROTOCOL §4.

## Development integration and branch lifecycle

[OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) governs development integration, separately from finite release acceptance. Explicit experimental source/Agent/destination bindings may remain incomplete; preserve prior defaults/behavior/diagnostics/budgets/release gates. New/worsened legacy failures block integration.

Follow PROTOCOL §7 for one branch per bounded scope, normally at most three, checkpoint commits, exact provenance/history, PR dispositions, live head/deletion checks and exact reporting when deletion is unavailable. Never merge index-only archive commits into main or develop from them. STATUS stays concise; detailed evidence immutable.

## Preserve meaning and evidence

- Keep `.ok` authoritative and [GOAL invariants/budgets/completion](GOAL.md#invariants-budgets-and-completion) intact.
- Semantic changes: explicit versioned decision, synchronized grammar/examples/diagnostics, conformance evidence. Never change expectations to pass tests.
- Preserve product/semantic/foundation/diagram/maintenance history, archive hashes and failed evidence; record new decisions/results separately.
- Distinguish represented, constructed, evaluated, exported, destination-validated. Expose unsupported behavior, loss, failure, stale results.
- STATUS retains GOAL's current/deferred/superseded domains. C210/C252 alter priorities, not semantics/history; C252 advances localized-authoring preparation without completing C221. Finite success proves neither whole product nor untested destinations.
- Decide runtime dependencies, architecture and limits deliberately. Changing the standard-library reference needs a concrete reason, dependency/provenance review and evidence. Never commit installed dependency directories.

## Verify the actual change

Owner's no-payment direction/[OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md): fresh relevant checks on the mode's explicitly selected executor. Local mode: the owner's prepared environment, run as `.venv/bin/python`, or another verification executor named for the check. Browser mode: the assistant's hosted workspace, not user's computer. Do not wait for hosted CI, retry blocked jobs or enable paid execution. Inspect older branches' changed workflows before integration: manual-only/default-false opt-in; no push/pull-request/scheduled jobs. Claim repository-wide Actions disablement only if observed.

Select checks for actual scope; documentation-only changes require documentation and applicable workflow checks below.

| Scope | Required check |
| --- | --- |
| Routine development, except documentation-only | `python3 tools/check_local.py`; `--full` adds existing visual job after pinned-tool preparation. |
| Runtime/semantics | Normally `python3 -m unittest discover -s tests -v` and `python3 -m ontokin conformance --output /tmp/ontokin-conformance.json`. |
| Documentation/navigation | `python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py`. |
| Workflow records/tools | `python3 tools/chat_workflow.py check`; tool edits also need focused tests. |
| Local environment specification, locks or setup tools | Focused tests; `tools/doctor_local.py` for each affected profile; independent review before a changed lock is used. |
| Agent/0.5 | Prepare pinned verification packages; `python3 tools/check_local.py --force-agent`: exact dependencies, zero-skip cohort, fresh source workflow, independent audit. May combine `--full`; neither closes release. |
| Exporter/viewer | Fresh source-to-GLB builds, independent Khronos/Three.js checks, visual inspection per [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md). |
| Agent interface | Execute actual protocol cases, including failure/retry; schemas are insufficient. |

PROTOCOL §5 owns durable revision/input/environment/command/settings/artifact/log/result/CI/limit evidence. Isolated validation retains source Git identity even with external evidence paths. Core runs cover only executed Python/roles; compatibility/external attestations/visual review require execution. Local drivers neither certify releases nor replace historical CI schemas. Offline observations use inert recordings, not live native apps; workflow structure proves neither merge nor scientific validity.

Use actual subagent tools/verified model inheritance where supported; no external different-model runner required. Invent no workers/settings. Claim no untested destination, universal numerical accuracy, unrun benchmark/job or whole-product coverage from a small corpus. Authorized integrator publishes result/next unmet gate in STATUS.

## Interactive progress and interrupted writes

Apply PROTOCOL §§4/8: brief factual checkpoint updates with continued work; bounded calls/small verified commits over silent unrelated batches/filler; preserved write intent and actual-state reconciliation before retries; ownership release/renewal. Timeout proves neither termination nor failure. Never replay blindly or force-move an old tree. [PROTOCOL §8](docs/workflow/PROTOCOL.md#8-recovery-and-stopping) governs precise recovery; checkpoints/updates improve recoverability, not guaranteed response delivery.
