# C193 recovery: legacy regression disposition

Detailed file paths below identify members of the [complete evidence archive](legacy-regression-recovery.tar.xz). The archive retains the original report and every linked member; this copy changes navigation only. The [disposition](disposition.json) and [independent final review](FINAL-REGRESSION-REVIEW.json) are also available directly.

**The stock driver remains FAILED. Fresh split-process coverage records 4,239 unique passing methods and the same thirteen experimental `.22` artifact-read methods NOT RUN.** The fresh class-setup failure matches the retained C191 baseline on its diagnostic, original budget, stage and program/implementation identities. No additional completed test failure, skip, unexpected method or unresolved started method remains.

This is a complete inventory disposition for bounded development review under OK-ENG-009. It does not certify the full regression driver, the torque release, unexecuted compatibility, external roles or the full OntoKin goal. The original unavailable C193 driver result remains **unknown**.

## Identified inputs

| Item | Observed identity |
| --- | --- |
| Candidate commit | `bc8c0918045248cd3d34c64e40c135fff0eec985` |
| Candidate tree | `631034be6fcd5249af753a9852a13f76baf44493` |
| Coordinator-provided observed main | `294d84ac5c5a15e07d042e5225646c2dab440293` |
| Baseline tree | `482db2167147fd568d3701a2e4da99e10340e860` |
| Independent source checkout | `/workspace/scratch/3be63d9ca584/regression-source` |
| Local audit branch | `work/c193-recovery-regression` |

Of 13,268 baseline tracked entries, 13,267 have identical Git modes and object identities. The sole changed inherited path is README.md; 280 paths are added. Runtime, all 363 test files, all 219 shared tool files, workflows, package configuration and the torque contract have identical trees across the retained C191 baseline/run sources, observed main and C193 candidate. Both the stock source-integrity check and the supplemental source/workspace checks passed. See input equality (archive member `input-equality.json`), prior failure source binding (archive member `prior-source-binding.json`) and full disposition (archive member `disposition.json`).

## Actual executions

| Invocation | Observed result |
| --- | --- |
| Original C193 execution before this recovery | Result unavailable; unknown. |
| Recovery default 900-second driver attempt | Intentionally interrupted after 377 methods passed and one method started without a result. Outer session exit 130. Its unfinished original summary and logs are retained. |
| Stock driver with authorized `--timeout 1800` | FAILED. Unit command exceeded 1,800.045 seconds after 3,282 passing methods and one interrupted method; 969 methods had not started. All six later driver steps completed successfully. |
| Separately supervised ordered tail | FAILED due to one class-setup error. Fresh discovery identified all 4,252 methods. The tail selected 970 methods in 79 intact module suites; 957 methods passed in 670.386 seconds and thirteen did not run. |
| Combined stock prefix and ordered tail | 4,239 unique methods passed; exactly thirteen remain unexecuted after the unchanged `.22` setup failure. No previously passing method was repeated in the tail. The one interrupted method was retried and passed. |

The 1,800-second driver option controls supervision of the entire test command. It does not change the limits inside any product or test fixture. The default attempt was stopped after retained C191 evidence established that its complete unit command had previously required 1,248.746 seconds. Both recovery attempts and all prior failures remain separately recorded.

The independent review required full stock discovery, a fresh isolated candidate workspace, the intact boundary module and every later module suite in original order, standard unittest setup/teardown, and finite supervision. The actual boundary was `test_reach_reference_sparse_cartesian`. The reviewed helper verified exact discovery-order prefix equality, complete inventory coverage, zero already-passing overlap and stable inputs. Previous-process warm state was not recreated. These are split-process observations; no single-process equivalence is claimed.

## The retained failure

`TorqueArtifactReadTests.setUpClass` created its own fresh store and attempted the frozen A08 export using the actual runtime clock. It retained its original **1,000,000 operations and 30,000 ms** request and host ceiling. It failed with:

- Code: `OKL-E-RESOURCE`.
- Reason: `execution_deadline_exceeded`.
- Stage: `recording_export_readback`.
- Protocol: `ontokin.agent/0.22`.
- Implementation source identity: `sha256:3e6ef2df6a7e8837050abb949075bff9b65f6a4aa4a9f1587850d7ddd59bce56`.

The program, entry revision and policy identities also match the retained baseline exactly. The thirteen class methods are **NOT RUN**, not passed or skipped. Their full identities and every observed method outcome appear in combined observations (archive member `combined-method-observations.json`). The complete diagnostic is retained in the tail log (archive member `ordered-tail/unit-tests.log`); disposition.json (archive member `disposition.json`) contains the normalized fresh/prior comparison. Run timings are recorded without a timing-equivalence claim. The outer supervision failure remains an unsuccessful verification result.

## Other stock-driver roles

| Role | Actual result |
| --- | --- |
| Source conformance | 43/43 cases; 694 assertions. |
| Agent conformance | 10/10 cases. |
| Construction | 19 passed, 1 pending, zero failed. |
| Surface | 1 passed, 11 pending, zero failed. |
| Impulse | 8 passed, 4 pending, zero failed. |
| Documentation preservation | Passed. |

These six driver steps exited successfully while **sixteen external cases remain pending**. No hosted checks or additional interpreter/platform compatibility runs were requested by this auditor.

## Environment and pinned verification tools

CPython 3.12.14; Linux 6.18.57, x86_64, glibc 2.41. A clean external virtual environment installed binary wheels from the exact repository lock with `--require-hashes`. The lock SHA-256 is `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f`. Native-reader Pillow setup passed.

| Verification package | Installed version |
| --- | --- |
| attrs | 26.1.0 |
| jsonschema | 4.26.0 |
| jsonschema-specifications | 2025.9.1 |
| referencing | 0.37.0 |
| rpds-py | 2026.5.1 |
| typing_extensions | 4.16.0 |
| Pillow | 13.0.0 |

See dependency receipt (archive member `dependencies.json`) and installation log (archive member `pip-install.log`).

## Exact commands and evidence

The complete stock invocation, from the independent source checkout, was:

```text
/workspace/scratch/3be63d9ca584/recovery-regression/venv/bin/python tools/check_local.py --timeout 1800 --output-dir /workspace/scratch/3be63d9ca584/recovery-regression/stock-core-1800
```

The separately authorized supplemental invocation was:

```text
/workspace/scratch/3be63d9ca584/recovery-regression/venv/bin/python /workspace/scratch/3be63d9ca584/recovery-regression/ordered_remainder.py
```

The helper SHA-256 independently reviewed before execution is `cfee2f1453581079a53e56137f173bfbed6f9ac6b9d9e9ea2bdadd3de53c35a1`. Its selection receipt records the complete discovered and selected ID sequences before execution. The helper, parser and combined reconciler bytes are retained with their hashes.

Key records are stock summary (archive member `stock-core-1800/summary.json`), stock unit log (archive member `stock-core-1800/logs/unit-tests.log`), tail selection (archive member `ordered-tail/selection.json`), tail result (archive member `ordered-tail/test-result.json`), tail command/integrity (archive member `ordered-tail/command.json`), initial interrupted attempt (archive member `interrupted-inventory.json`), and final disposition (archive member `disposition.json`). The evidence archive contains the full logs, reports, inventories, dependencies and prior-failure comparison; installed environments and source workspace copies are excluded.
