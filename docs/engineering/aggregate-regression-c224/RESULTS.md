# C224 R02 aggregate regression result

The selected aggregate attempt **reached a blocker**. R02 is **blocked**. This result concerns the default local validation plan on Linux x86-64 / CPython 3.12.14. It does not establish other interpreter coverage, visual receiving fidelity or a complete release.

## Source, preparation and execution

The immutable source was `1530832e0ee566887a43ce6a5e5d374901a24860`, tree `5fbf7b27f37955871fec5fbc35cf346db027b3aa`. No STATUS, evidence or source edits were made in that checkout during execution. Publication uses a separate integration checkout. The complete saved C223 ZIP was reconciled against scope #178 and freshly verified: all 5,600 members retain exact hashes, sizes and modes.

A clean external verification environment installed the exact seven hashed packages from `tools/native-reader-verification-linux-cp312.lock`. The global environment's different rpds-py version was recorded, then left unchanged. The separate environment passes the native-reader image decoder preflight. [Dependency receipt](evidence/PREFLIGHT.json).

Independent discovery recorded **4,662 actual methods**, with zero duplicate IDs or failed-import placeholders, before driver launch. No methods executed during discovery. The precondition review passes 24 checks over timing, environment, command, all copied inputs, all fixture hashes and all test hashes. [Inventory](evidence/INVENTORY-SUMMARY.json), [precondition review](evidence/PRECONDITION-REVIEW.json).

The complete default seven-step plan used an explicit **900-second per-command limit**. No product evaluation budget, fixture expectation, tolerance or reader/cache guard changed. [Exact command and execution](evidence/RUN-EXECUTION.json).

## Observed driver steps

| Step | Status | Exit code | Seconds |
| --- | --- | ---: | ---: |
| unit-tests | failed | -15 | 900.031 |
| source | passed | 0 | 0.72 |
| agent | passed | 0 | 0.768 |
| construction | passed | 0 | 35.967 |
| surface | passed | 0 | 20.674 |
| impulse | passed | 0 | 47.4 |
| documents | passed | 0 | 1.98 |

The driver reports source unchanged: **True**; Git revision unchanged: **True**. All individual raw logs/reports and the original terminal summary are retained. Pending external cases remain pending even where a command permits their process handling.

## Independent method accounting

| Outcome | Methods |
| --- | ---: |
| passed | 3451 |
| failed | 0 |
| error | 0 |
| skipped | 0 |
| expected failure | 0 |
| unexpected success | 0 |
| failed import | 0 |
| timed out | 1 |
| incomplete observation | 0 |
| unrun | 1210 |

All **4662** selected methods are classified. The original driver timeout summary reports `tests_run: 0` because the interrupted unittest process emitted no terminal `Ran N tests` footer; it does not mean zero methods executed. Independent method identities and raw success lines establish the counts above, while the original summary remains unchanged. The interrupted method identifies the suite deadline boundary; no assertion failure or product-budget overrun by that method is inferred. Subtest events are counted separately and do not create extra methods. Terminal summaries, setup/import placeholders, interrupted methods and unrun methods are retained distinctly. [Exact accounting summary](evidence/METHOD-OUTCOMES-SUMMARY.json).

Three methods declared unavailable Node readback prerequisites at their original fixed paths. Their observed outcomes, including whether execution reached them, appear in the accounting. No skip guard was weakened or missing prerequisite relabeled as a pass. [Exact prerequisite paths](evidence/DECLARED-SKIP-PREREQUISITES.json).

## Scope and preserved limits

This attempt executes existing source and test/export paths. It performs no new Godot receiving proof. The optional `--full` visual plan and dedicated `--force-agent` plan were not selected; ordinary unit discovery still includes tests from those components. Python 3.11/3.13 compatibility and release attestation remain unexecuted here. Historical failed regressions and strict Blender normal failure retain their original meanings. Held PRs #155/#165/#167/#169 remain unchanged.

R00/R01 remain completed within their recorded scopes. All nine recommendation records and all 41 acceptance criteria are retained; R03-R08 are not advanced by this attempt. No product implementation, test, fixture, workflow or dependency lock changed.

## Evidence and next action

[Artifact identities](evidence/ARTIFACTS.json) bind complete logs, driver reports, inventory, per-method outcomes and executable accounting scripts in the saved C224 handoff. [Scope #180](https://github.com/Omegapy/OntoKin/issues/180) records exact publication and final delivery; the [recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-fd2f4b4d4da881919db4187f3b6fc77f_2ab2a24d43748191957f9bcc356b59de&account_id=personal) preserves actual current evidence. Do not infer a final save from this pre-save document.

Follow [NEXT-TASK.md](NEXT-TASK.md). Stop after the bounded result is reviewed, published as appropriate, packaged, verified and saved. No repair or later recommendation begins in this thread.
