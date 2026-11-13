# C228 — complete R02 aggregate; replacement rejection remains blocked

C228 records one complete default regression attempt on an immutable published baseline. **All 4,662 methods ran: 4,661 passed and one failed.** Two replacement subtests within that single ledger method reported `LedgerError not raised`. The independent outcome review passed its 33 evidence checks and keeps **R02 blocked**. [Result summary](evidence/RESULT-SUMMARY.json), [complete outcome review](evidence/OUTCOME-REVIEW.json).

The original A08 setup completed within this aggregate and all thirteen torque artifact-read methods passed. The six later default commands also passed. Sixteen external conformance cases remain pending. [Results and limits](RESULTS.md).

## Source and evidence

| Role | Exact identity |
|---|---|
| Executed published commit | `fc500331ce789eb6f9c1210ea4f3b394d45e507c` |
| Executed tree | `8eba004b6b08a00449663d868674c9fc8521469f` |
| Environment | Linux x86-64 / CPython 3.12.14 |
| Selected scope | One default seven-step aggregate; original product budgets |

The source and Git identities stayed unchanged during execution. The process was reaped with no remaining observed descendants or process-group members. This increment records documentation and evidence; product behavior and test expectations are unchanged. [Execution receipt](evidence/RUN-EXECUTION.json).

Read [preparation](PREPARATION.md), [results](RESULTS.md), [independent review](REVIEW.md), then [the next bounded task](NEXT-TASK.md). The next task is a separately reviewed CPU diagnosis of the two same-content authority-file replacement failures. Their underlying cause remains unproven.

[Saved recovery evidence](https://chatgpt.com/library?file_id=libfile_fde3_f-801ea23215d48191bba121ab38628a8b_2ab2a24d43748191957f9bcc356b59de&account_id=personal), confirmed at version 5, contains the complete logs, inventory, source bindings and reviews. [Raw evidence identities](evidence/RAW-EVIDENCE.json) identify those exact bytes. [Scope #188](https://github.com/Omegapy/OntoKin/issues/188) records integration and subsequent final handoff delivery as they are observed.
