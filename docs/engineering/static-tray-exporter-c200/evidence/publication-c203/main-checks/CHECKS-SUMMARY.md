# Actual-main validation after C200 integration

**PASS: the merged main commit passed the applicable fresh checks.** Main is `2b2f3e7de7595099ad5f9e0176c5596220c0c2dc`, tree `7e1ab341160cf5b86807e8ffec2cc3bb7b47db92`. The clean validation worktree matches the integrator's captured GitHub main and merge readback for PR #137. Issue #136 is closed in that same readback. This verifier compared the retained API response independently; it did not issue another network request.

## Identity and preservation

All **301 immutable locked inputs** and the prior tested-source manifest match actual main, before and after these checks. Executable C200 source is identical to the previously executed qualification. Shared runtime, fixtures, schemas, grammar, conformance tools and workflows are identical to the premerge main.

The main tree differs from reviewed candidate `125353836119e50215287c27d80e99cef6d85e8f` only by the five published independent-review artifacts. Every published review file matches its approved original bytes. The merged source branch tree equals the actual main tree.

## Actual checks on main

| Fresh check | Result |
| --- | --- |
| Focused exporter/source/reader controls | 107 passed; zero skips; all five pinned-exporter source methods executed |
| C200 protocol controls | 10 passed; zero skips |
| Core conformance | 43 cases, 694 assertions, zero failures |
| Documentation preservation and navigation | 29 sources, 233 sections, 796 documents, 4,106 local links; zero failures |

The checks used CPython 3.12.14 on Linux x86-64. Commands, stdout, stderr, method identities, source bindings and results are preserved beside this report. Focused/protocol/documentation child-process observations contain eight Python reader CLI children and three Git metadata reads, all from the focused cohort; protocol and documentation started no children. The core CLI was executed directly, with its command and output recorded, but its child activity was not instrumented.

The **47 compiler methods** were not repeated. Their prior passing result remains reusable because the complete source tree change adds only unchanged review evidence, all locked/tested inputs match, and all four direct compiler source bindings independently match actual main. This reuse is recorded separately from the fresh checks.

No new native construction, receiving, Node, lifecycle, timed-author or qualification execution occurred. C199/C200 schedules remain closed.

## Preserved limits

The historical full regression remains **FAILED**: 4,239 distinct passing methods and 13 torque-read methods NOT RUN after the unchanged 30,000 ms setup timeout. It was not rerun. The unchanged shared runtime identities and the independently reviewed experimental boundary justify the applicable scope; this report makes no new full-suite or complete-release claim.

Existing visual limits, incomplete external compatibility and other release roles remain unchanged. Eight recovered preparation streams still have only recovery-time individual hashes. C201 admission has not executed. A later main change requires validation of its own identified source scope.

## Evidence

- `CHECKS-SUMMARY.json`: machine-readable decision, verified input bindings and limits.
- `IDENTITY-BEFORE.json` and `IDENTITY-AFTER.json`: exact main, remote-readback comparison, all 301 inputs and five review artifact hashes.
- `REMOTE-MERGE-READBACK.json`: unchanged copy of the integrator's captured API response.
- `focused/RESULTS.json` and `focused/tests.log`: actual 107-method execution.
- `protocol.stderr.log`, `core-conformance.json` and `DOCUMENTATION-CHECK.json`: actual corresponding results.
- Each `*-launch.json` and available `*-command.json`: exact commands, environment, stream hashes and process observations.
