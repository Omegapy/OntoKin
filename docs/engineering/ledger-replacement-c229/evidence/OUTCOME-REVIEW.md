# C229 independent outcome review — launcher blocker

Decision: **accept the blocker record; no retry**. The finite diagnosis did not reach a product test or replacement observation. `OUTCOME-REVIEW.json` binds ten raw records/source files and records fifteen passing consistency checks. These checks validate the reported failure and cleanup; they do not make the diagnosis pass.

## Actual execution

Root invoked the reviewed launcher once from `/workspace/scratch/9d6b968559d5`, passing `diagnosis-author/prepared/RUN-PLAN.json` as a relative plan path. The launcher accepted the exact approved plan and harness bytes, claimed its fresh output directory and verified clean source `d578a30dab9a112895d2e3c09561a17866d9c464`, tree `080b9d00bc340dfd9728601147d11816fab4375d`.

It attempted one Python worker. The worker command supplied `diagnosis-author/prepared/diagnose_replacement.py` as a relative script argument while changing the child working directory to `/workspace/scratch/a9488c5c1afa/restore-c228`. Python therefore looked for the script beneath that source checkout and reported that it could not open the file. It exited with code 2 before loading the worker script.

The first worker was reaped, and the launcher's process-group observation was empty. Its standard output is empty, no worker result/environment directory was created, and the temporary fixture root is empty. The launcher then recorded `Missing complete worker result; no further start`, exited with code 1, and marked the schedule consumed. The second worker was never attempted. Before/after source identity, clean status and all nine bound source/contract hashes agree.

| Count | Observed value |
| --- | ---: |
| Root launcher invocations | 1 |
| Python worker start attempts | 1 |
| Python workers reaped | 1 |
| Product methods and subtests executed | 0 |
| Instrumented replacement cases | 0 |
| Synthetic ledger beginnings / reservations | 0 / 0 |
| Native starts / aggregate attempts / retries | 0 / 0 / 0 |

## Cause and review limit

The immediate blocker is an orchestration path error. Root supplied a relative plan path. The launcher derives the harness from `args.plan.parent` without making it absolute, verifies that path in the root working directory, and later passes it unchanged to a child with a different working directory. The actual missing-script stderr matches that resolution exactly. This is supported by the raw process command and static launcher code, independently of the root's explanatory receipt.

The preexecution review missed this working-directory boundary. It approved the finite harness but did not require or verify the actual outer invocation with absolute paths. The earlier preparation feedback remains useful evidence, but it did not cover this defect. The approved plan, approval and executed launcher are preserved unchanged; there is no revised passing attempt.

## What this establishes

The finite launcher stops safely on a missing result and does not consume the second worker slot after the blocker. Its fresh output cannot be reused. No ledger replacement mechanism was measured. Numeric inode reuse remains a hypothesis based on static source inspection, and C228's historical inode sequence remains absent. C228's one failed method and both replacement subtest failures remain unchanged; R02 is still blocked.

The logical next action is a separately selected bounded scope that corrects and qualifies launcher path handling from an unrelated working directory, binds the complete outer invocation using absolute paths, then independently reviews and saves a fresh finite plan before any new diagnostic authorization. Path qualification itself can use inert fixtures rather than product execution. The consumed C229 attempt is not resumed. Product guard/test changes and aggregate replay remain later decisions supported by actual diagnostic evidence.

The reviewer executed no product module, test method, harness, replacement probe or native process during outcome review.
