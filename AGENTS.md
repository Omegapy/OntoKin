# Working on OntoKin

Owner authorization: autonomous technical development/stewardship toward [GOAL.md](GOAL.md), through implementation, verification and reviewable publication within selected scope. No legal ownership, wider platform authority or outside-project authority.

## Recenter and resume

At session start, after compaction, and before milestone selection/closure, follow [CHATGPT-START-HERE](CHATGPT-START-HERE.md) and [PROTOCOL §1](docs/workflow/PROTOCOL.md#1-authority-and-explicit-loading). Their full load/read-set rules apply; GitHub skills are not automatically installed. Reconcile user direction, actual state and adopted contracts; identify goal/next unmet gate.

Inspect working tree, actual GitHub head, lease and relevant CI; preserve existing work. Synthetic snapshots are not remote heads. Read applicable specifications via [docs/README.md](docs/README.md), especially adopted language rules/active contract; historical proposals guarantee no implementation. Continue authorized useful work, recording real blockers/exact next actions. Never substitute an easier demonstration for an unmet goal.

## GitHub-owned browser workflow

[ROLE](ROLE.md)/[PROTOCOL](docs/workflow/PROTOCOL.md) own requirements, plans, workers, evidence, memory and bounded phases. Their rules on source-backed knowledge, named TRD/plan skills and native ChatGPT Tasks apply. [HANDOFF](docs/workflow/HANDOFF.md)/[BROWSER-PROMPTS](docs/workflow/BROWSER-PROMPTS.md) own early recovery, separate GitHub/save gates, verified handoff and stop. Read-only questions alone require no scope/ZIP; assume neither compaction nor context warnings.

## Coordinate parallel workers and main integration

Apply full [PROTOCOL §7](docs/workflow/PROTOCOL.md#7-integration-and-branch-lifecycle): independent nonoverlapping work; verified lease ownership; observed-head conditional/nonforce update or protected PR merge; readback/checks; preservation; roughly 30-minute leases/expiry reconciliation. Existing routine authorization needs no repeated permission. Unavailable conditional writes block that operation, not independent work.

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

Owner's no-payment direction/[OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md): fresh relevant local checks in the assistant's hosted workspace, not user's computer. Do not wait for hosted CI, retry blocked jobs or enable paid execution. Inspect older branches' changed workflows before integration: manual-only/default-false opt-in; no push/pull-request/scheduled jobs. Claim repository-wide Actions disablement only if observed.

Select checks for actual scope; documentation-only changes require documentation and applicable workflow checks below.

| Scope | Required check |
| --- | --- |
| Routine development, except documentation-only | `python3 tools/check_local.py`; `--full` adds existing visual job after pinned-tool preparation. |
| Runtime/semantics | Normally `python3 -m unittest discover -s tests -v` and `python3 -m ontokin conformance --output /tmp/ontokin-conformance.json`. |
| Documentation/navigation | `python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py`. |
| Workflow records/tools | `python3 tools/chat_workflow.py check`; tool edits also need focused tests. |
| Agent/0.5 | Prepare pinned verification packages; `python3 tools/check_local.py --force-agent`: exact dependencies, zero-skip cohort, fresh source workflow, independent audit. May combine `--full`; neither closes release. |
| Exporter/viewer | Fresh source-to-GLB builds, independent Khronos/Three.js checks, visual inspection per [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md). |
| Agent interface | Execute actual protocol cases, including failure/retry; schemas are insufficient. |

PROTOCOL §5 owns durable revision/input/environment/command/settings/artifact/log/result/CI/limit evidence. Isolated validation retains source Git identity even with external evidence paths. Core runs cover only executed Python/roles; compatibility/external attestations/visual review require execution. Local drivers neither certify releases nor replace historical CI schemas. Offline observations use inert recordings, not live native apps; workflow structure proves neither merge nor scientific validity.

Use actual subagent tools/verified model inheritance where supported; no external different-model runner required. Invent no workers/settings. Claim no untested destination, universal numerical accuracy, unrun benchmark/job or whole-product coverage from a small corpus. Authorized integrator publishes result/next unmet gate in STATUS.

## Interactive progress and interrupted writes

Apply PROTOCOL §§4/8: brief factual checkpoint updates with continued work; bounded calls/small verified commits over silent unrelated batches/filler; preserved write intent and actual-state reconciliation before retries; ownership release/renewal. Timeout proves neither termination nor failure. Never replay blindly or force-move an old tree. [PROTOCOL §8](docs/workflow/PROTOCOL.md#8-recovery-and-stopping) governs precise recovery; checkpoints/updates improve recoverability, not guaranteed response delivery.
