# Working on OntoKin

The owner authorizes autonomous technical development and repository stewardship toward [GOAL.md](GOAL.md), through implementation, verification and reviewable publication within the selected scope. This grants neither legal ownership nor wider platform or outside-project authority.

## Recenter and resume

At session start, after compaction, and before selecting or closing a milestone:

1. Follow [CHATGPT-START-HERE](CHATGPT-START-HERE.md), including the registry, CURRENT, GOAL, STATUS, ROLE, active task/plan and full selected skills. GitHub skill files are not automatically installed. [PROTOCOL §1](docs/workflow/PROTOCOL.md#1-authority-and-explicit-loading) governs read-set retention and changed/missing instructions. Reconcile current user direction, actual state and adopted contracts; identify the goal and next unmet gate.
2. Inspect the working tree, actual GitHub head, integration lease and relevant CI. Preserve existing work; a synthetic local snapshot is not the remote head.
3. Read applicable specifications through [docs/README.md](docs/README.md), especially adopted language rules and the active contract. Historical proposals are not implementation guarantees.
4. Continue authorized useful work; record genuine blockers and exact next actions. Do not replace an unmet goal with an easier demonstration.

## GitHub-owned browser workflow

[ROLE](ROLE.md) and [PROTOCOL](docs/workflow/PROTOCOL.md) govern requirements, plans, actual independent workers, evidence, memory and bounded session phases. Repository records do not invoke named TRD/plan skills or native ChatGPT Tasks. Knowledge is source-backed context, not authority.

GitHub checkpoints and verified session ZIP delivery are separate gates. Follow [HANDOFF](docs/workflow/HANDOFF.md) and [BROWSER-PROMPTS](docs/workflow/BROWSER-PROMPTS.md): save early recovery, finish the selected phase, verify its required handoff and stop. Do not assume compaction or context warnings. Read-only questions do not automatically create a development scope or require a ZIP.

## Coordinate parallel workers and main integration

Follow the complete [coordination and lease rules in PROTOCOL §7](docs/workflow/PROTOCOL.md#7-integration-and-branch-lifecycle). Nonoverlapping branches may implement, test and publish during another lease. Only its verified holder writes main or protected shared state, through observed-head conditional/nonforce updates or protected PR merges with live readback and checks. Preserve others' work. Normally use roughly 30-minute leases; expiry does not prove a writer stopped. Routine authorized work needs no repeated permission; an unavailable conditional write blocks that operation, not independent work.

## Development integration and branch lifecycle

[OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) governs development integration separately from finite release acceptance. Explicit experimental source/Agent/destination bindings may remain incomplete; preserve earlier defaults, behavior, diagnostics, budgets and release gates. New or worsened legacy failures block integration.

Use one branch per active bounded scope, normally at most three; checkpoints are commits. Preserve exact provenance and durable history, resolve PR dispositions, and recheck heads before deletion. Never merge an index-only archive commit into main or use it for development. Keep STATUS concise and detailed evidence immutable. Report the exact completed branch if authorized deletion is unavailable.

## Preserve meaning and evidence

- Keep `.ok` authoritative and [GOAL's invariants, budgets and completion rules](GOAL.md#invariants-budgets-and-completion) intact.
- Semantic changes require an explicit versioned decision, synchronized grammar/examples/diagnostics and conformance evidence. Never change expectations merely to pass tests.
- Preserve product, semantic, foundation, diagram and maintenance history, archival hashes and failed evidence. Record new decisions/results separately.
- Distinguish represented, constructed, evaluated, exported and destination-validated results. Expose unsupported behavior, loss, failure and stale results.
- Preserve GOAL's current/deferred/superseded domains in STATUS. C210/C252 change priorities, not semantics or historical results; C252 advances localized-authoring preparation without completing C221. Finite success proves neither the whole product nor an untested destination.
- Runtime dependencies, architecture and limits need deliberate decisions. Changing the standard-library reference requires a concrete reason, dependency/provenance review and evidence. Never commit installed dependency directories.

## Verify the actual change

The owner's no-payment direction and [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md) require fresh relevant local checks. Here, local means the assistant's hosted workspace, not the user's computer. Do not wait for hosted CI, retry blocked jobs or enable paid execution to proceed. Before integrating older branches, inspect changed workflows: hosted jobs stay manual-only with default-false opt-in, never push/pull-request/scheduled. Report repository-wide Actions disablement only if observed.

Use checks applicable to the change. Documentation-only changes require the focused documentation check and applicable workflow validation below.

| Scope | Required check |
| --- | --- |
| Routine development except documentation-only changes | `python3 tools/check_local.py`; `--full` adds the existing visual job after pinned-tool preparation. |
| Runtime/semantics | Normally `python3 -m unittest discover -s tests -v` and `python3 -m ontokin conformance --output /tmp/ontokin-conformance.json`. |
| Documentation/navigation | `python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py`. |
| Workflow records/tools | `python3 tools/chat_workflow.py check`; tool changes also need focused tests. |
| Agent/0.5 | Prepare pinned verification packages; run `python3 tools/check_local.py --force-agent` for exact dependencies, zero-skip cohort, fresh source workflow and independent audit. May combine with `--full`; neither closes the release. |
| Exporter/viewer | Fresh source-to-GLB builds, independent Khronos/Three.js checks and visual inspection under [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md). |
| Agent interface | Execute actual protocol cases, including failure/retry paths; schemas alone are insufficient. |

Record actual source revision/input hashes, environment, commands, settings, artifacts, logs, results, relevant remote CI and limits durably. Preserve source Git identity in isolated validation workspaces, even with external evidence paths. A core run covers only its executed Python version/roles; compatibility, external attestations and visual review remain pending unless performed. Local drivers do not certify releases or replace historical CI schemas. Offline observation checks use inert recordings, not live native applications; workflow structural checks prove neither merging nor scientific validity.

Use actual subagent tools with verified model inheritance where supported; no external different-model runner is required. Do not invent workers or settings. Never claim untested destinations, universal numerical accuracy, unrun benchmarks/jobs or whole-product coverage from a small corpus. Publish the result and next unmet gate in STATUS through its authorized integrator.

## Interactive progress and interrupted writes

Give brief factual progress updates at meaningful checkpoints; continue work between them. Prefer bounded calls and small verified commits over silent unrelated batches or filler.

After uncertain writes, preserve intended parent/tree/commit and inspect actual refs, relevant files and lease before retrying. A timeout proves neither termination nor failure. Reconcile completed/concurrent work; never replay blindly or force-move an old tree. Follow [PROTOCOL §8](docs/workflow/PROTOCOL.md#8-recovery-and-stopping) for precise recovery and ownership release/renewal. Checkpoints and updates improve recoverability but cannot guarantee the response stream.
