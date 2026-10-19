# Working on OntoKin

The owner authorizes autonomous technical development and repository stewardship toward [GOAL.md](GOAL.md). Routine work within that mandate should continue through implementation, verification, and reviewable publication. This is not legal ownership and does not enlarge platform permissions or authorization outside the project.

## Recenter and resume

At the start of a session, after compaction, and before choosing or closing a milestone:

1. Read GOAL and [STATUS.md](STATUS.md). Restate the current goal and the next unmet acceptance gate to yourself.
2. Inspect repository status/tree, the actual GitHub head, the integration lease, and relevant CI. Do not treat a synthetic local snapshot commit as the remote head or discard existing work.
3. Read the relevant specifications through [docs/README.md](docs/README.md), especially the adopted language rules and the active engineering contract. Historical proposals are not current implementation guarantees.
4. Continue authorized useful work. Record genuine blockers and the concrete next action; do not silently replace the goal with an easier demonstration.

## Coordinate parallel workers and main integration

**Parallel branch development is allowed; main integration remains serialized.** A live integration lease is **not** a project-wide read-only lock. It protects writes to `main`, integration ownership in `STATUS.md`, and any explicitly reserved overlapping/shared files. Independent workers (including scheduled reviewers that have actual editing tools) may implement, test, and publish **nonoverlapping** work on their **own** branches while someone else integrates. An enabled schedule or branch is not proof that multiple agents are executing.

1. **Inspect and declare scope.** Before editing, read current `main`, `STATUS.md`, CI, existing branches/PRs, and issue handoffs. Choose an unclaimed task with a bounded file/feature scope. Give each worker a distinct identity and its own new branch from an observed commit. Record the owned scope, branch, starting SHA, and dependencies in its PR or issue. Do not edit another worker's branch or assumed-owned files. If scope overlaps, coordinate or choose other useful independent work; do not overwrite.
2. **Keep shared integration state exclusive.** Only the verified holder of the main integration lease may write `main` or change the integration lease/coordination fields in `STATUS.md` while it is live. Workers on independent branches must not silently modify shared status, release records, pinned evidence, or files reserved for an active integration. Preserve the other worker's published and possibly unpublished work. Independent progress goes in the worker's branch and a GitHub PR/issue handoff rather than a competing `STATUS.md` update.
3. **Produce reviewable work without waiting.** A nonintegrating worker can implement on its isolated branch, run targeted and relevant full tests, commit, push, and prepare a PR containing actual changed files, exact head SHA, CI/evidence, known failures, and the next step. Passing branch CI qualifies work for review, not automatic acceptance of a whole release. Continue other safe scoped tasks rather than idling behind an unrelated lease.
4. **Serialize merges and verify them.** The integration holder reviews incoming branches against the **current** `main`, resolves dependency/conflict order and required gates, and uses observed-head conditional/nonforce updates or GitHub's protected PR merge path. Confirm the real merge result and run relevant checks on the resulting `main`. Do not force-move a ref or assume a past successful CI run applies to changed bytes. A merge of an unrelated branch does not complete an unverified milestone.
5. **Use bounded, recoverable leases.** New main integration leases should normally have an expiry of roughly 30 minutes, with a distinct owner and task; renew only after meaningful implementation/verification checkpoints that record the new expiry. Existing unexpired leases retain their stated end time unless the holder explicitly releases them. A lease must not be prolonged solely through repeated status messages. When released or expired, inspect `STATUS.md`, relevant heads, outstanding writes and CI, then acquire ownership through a verified expected-head compare-and-swap before touching shared integration state. Expiry is *not* proof that the previous worker stopped; an unknown outcome requires remote reconciliation before retrying.
6. **Handle genuine blockers precisely.** If an operation cannot enforce the necessary conditional head check, would collide with owned work, or needs a platform-required confirmation, do not bypass it. Document the exact blocker and continue permitted nonoverlapping branch work where possible. Routine repository access, edits, tests, commits, and authorized integration do not require repeated owner permission.

At every substantial branch checkpoint, record the work scope, code SHA, executed tests and observed results, unmet gates and exact handoff action. The main integrator owns `STATUS.md` publication and lease release/renewal. These rules permit concurrent independent progress; they do **not** guarantee that a scheduled task, external chat, or separate worker is actively running.

## Preserve meaning and evidence

- Keep `.ok` authoritative. Preserve identity, units/frames, independent ownership/following/connections, one motion authority, mass accounting, and honest release/state transfer.
- A semantic change needs an explicit versioned specification decision, synchronized grammar/examples/diagnostics, and corresponding conformance evidence. Do not silently change expected outcomes to make tests pass.
- Preserve historical product, semantic, foundation, diagram, and maintenance records. Do not rewrite preservation hashes or archival evidence to suppress a failure. Record new decisions and measured results separately.
- Distinguish represented, constructed, evaluated, exported, and destination-validated results. Unsupported behavior, information loss, failed goals, and stale results must remain visible.
- Keep the full GOAL scope and missing domains in STATUS. Completing OK-AGENT-001 or another finite release is not completing OntoKin.
- Runtime dependencies, architecture, and product limits are deliberate decisions. The current reference uses Python's standard library; a future change needs a concrete reason, dependency/provenance review, and relevant evidence. Installed dependency directories must not be committed.

## Verify the actual change

The owner’s October 19, 2026 no-payment direction adopts [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). Fresh local checks are the default for routine development and integration. Do not wait for hosted CI, retry blocked hosted jobs, or enable paid execution as a prerequisite for useful work. Run `python3 tools/check_local.py`; use `--full` for the complete existing visual job after preparing its pinned local tools. For a documentation-only change, the preservation/link checker below remains the focused check.

Record the actual source revision, input hashes, interpreter/platform, commands, logs and results. A core run establishes only its executed Python version and selected roles. Missing compatibility runs, external attestations and visual review remain pending. The local driver does not certify a full release or replace the historical CI-evidence schemas. Before integrating an older branch, inspect every workflow it adds or changes and apply the manual-only, default-false hosted-job opt-in policy; do not restore push, pull-request or scheduled hosted jobs. Repository-wide Actions disablement is a separate setting and must be reported from an observed result.

For Agent/0.5 work, prepare the pinned verification-only packages and run `python3 tools/check_local.py --force-agent`. This adds exact dependency checks, a zero-skip Agent cohort, a fresh source workflow and its independent audit. It can be combined with `--full`; none of these local options alone closes the full force release. Preserve the actual source Git identity in isolated validation workspaces, including when evidence is written outside the repository.

Use checks relevant to the change. Runtime or semantic changes normally require:

```bash
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-conformance.json
```

Documentation and navigation changes require:

```bash
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

Exporter/viewer changes also require fresh source-to-GLB builds, independent Khronos/Three.js checks, and visual inspection as documented in [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md). Agent-interface work must execute the actual protocol cases, including failure/retry paths; a schema alone is insufficient.

Before declaring a release gate passed, identify the exact source/implementation revision, settings, artifacts, test results, relevant remote CI, and remaining limits. Preserve evidence in the repository or link to a durable identified result. Do not claim an untested destination, universal numeric accuracy, an unrun benchmark, a configured-but-unexecuted job, or all product requirements from a small passing corpus.

Update STATUS with the result and the next unmet gate. Keep it short enough to reread after compaction; detailed reasoning, contracts, and evidence belong in linked engineering records.

## Interactive progress and interrupted writes

During long interactive work, send brief, factual progress updates at meaningful checkpoints and continue the task between them. Report completed inspection, a reproduced defect, a test result, a saved commit or a real blocker. Avoid long silent batches of unrelated connector operations, filler heartbeats, and acknowledgements that replace the requested work. Prefer individually bounded calls and small verified commits.

An application timeout is not proof that the earlier worker stopped or that its last write failed. Before any retry, read the actual refs, relevant files and lease. Reconcile completed or concurrent work instead of replaying a batch or force-moving an old tree. Give each active integration worker a distinct owner token; do not reuse a generic owner name to infer authority across independent sessions.

After an unknown write result, keep the intended parent, tree and commit identities, then inspect the remote head. Retry only after establishing the current state and the applicable lease. Save precise recovery instructions and release or renew ownership before ending. Frequent chat updates and repository checkpoints improve visibility and recoverability, but do not guarantee that the application or network will maintain the response stream.
