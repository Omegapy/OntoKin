# C268 live recovery audit

Observed 2026-11-19 14:45:53 UTC by /root/live_recovery_audit. Read-only audit; no repository mutations and no tests executed by this worker.

## Exact state

- Main: `7ff41e071fb694dadf1ba256b13168e1a4083926`, tree `bb517e2cf02f22ad3e2a0b5c253fcd5150af896a`. Latest commit changes STATUS only.
- Candidate branch `work/c268-historical-endpoint`: `734789521f82248d39b623c33aae9d3284ab4bce`; implementation predecessor `8a2fc5708e60e620987db3d1db33c01456833bda`.
- Shared ancestor `4595bade65291f36900be3e648c733aea74d5c40`; candidate is two commits ahead and one behind actual main.
- Sole open PR [266](https://github.com/Omegapy/OntoKin/pull/266) is draft and unmerged. No PR reviews or comments. Scope [265](https://github.com/Omegapy/OntoKin/issues/265) remains open.
- Only two branch results; only one open PR result. Each collection had fewer than its 100-item limit.
- Main STATUS lease owner `c268-root-c7dae94da130`, expiry `2026-11-19T14:58:39.000Z`. Historical worker names are records, not proof of current liveness.
- Candidate GitGuardian check completed successfully; zero Actions workflow runs; combined commit status pending with zero legacy statuses. These do not replace local acceptance evidence.

## First unmet gate

P03: affected candidate checks plus independent exact-candidate review.

The candidate task marks P01/P02 done and P03 in progress. Its affected-cohort check is not_run. Published tree contains the independent controls, run-03 result and startup/runner reviews, but no final candidate cohort results, RESULTS.md or REVIEW.json. Main STATUS says 12 groups / 281 methods / 14 bindings passed; without the corresponding exact evidence this remains an assertion to reconcile with surviving unpublished bytes or rerun, not accepted evidence.

Independent control run-03 itself is available: 34 methods, passed with zero failures/errors/skips, 130 calls (120 historical, 10 raw), 12 historical admissions, 9 raw successes, 109 typed refusals, no untyped exceptions. Preserve the recorded 12-error first author run. Exact checked inputs are in the run-03 JSON. The prior reader implementer and control author are distinct; the listed final reviewer state is active/pending, not a verdict.

P04 integration/main verification/branch disposition and P05 final delivery remain pending. Source handoff and save reconciliation are the Director's separate assignment.

## Proposed bounded recovery

Recover/validate exact candidate evidence, obtain independent final review, resolve only necessary scoped findings and save the P03 handoff. Leave PR266 draft, issue265 open and the branch retained if integration remains for the next chat. Do not replay the published implementation or independent controls. Preserve the old owner lease until release/expiry; reconcile heads and uncertain outcomes before a new conditional acquisition.

## Sources and saved evidence

Required pinned instructions and selected skills: `recovery-audit/main/`, original relative paths; exact UTF-8 snapshot sizes/hashes: `SNAPSHOT-IDENTITIES.json`.

Candidate task and coordination/control records: `recovery-audit/candidate/`.

API evidence in adjacent JSON files preserves main/branches/open and recent PRs, issue265, PR266, checks/status/Actions inventory, compare result and full candidate evidence-tree inventory. [Pinned entry](https://github.com/Omegapy/OntoKin/blob/7ff41e071fb694dadf1ba256b13168e1a4083926/CHATGPT-START-HERE.md), [candidate task](https://github.com/Omegapy/OntoKin/blob/734789521f82248d39b623c33aae9d3284ab4bce/docs/workflow/tasks/C268/task.json), [candidate control record](https://github.com/Omegapy/OntoKin/blob/734789521f82248d39b623c33aae9d3284ab4bce/docs/engineering/localized-repair-c268/evidence/control-author/run-03/results.json).

Limits: this is repository-state and durable-evidence inspection, not implementation review, rerun validation, complete historical graph proof, Library verification or proof that no prior unpublished work exists.
