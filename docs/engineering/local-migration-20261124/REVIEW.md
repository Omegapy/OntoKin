# Independent review of the exact candidate

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
TASK-032, REQ-040. Reviews of earlier, changing states are in [PRE-REVIEWS](PRE-REVIEWS.md).

**Reviewer:** one independent reviewer subagent with a fresh context, model inherited from the
session, which wrote none of the work. It worked in its own clone and in a scratch directory, changed
nothing in the candidate, pushed nothing and did not contact GitHub. It returned its reports as
text; this record was written by the Director from them. No self-review is reported here as
independent.

| Round | Candidate | Disposition |
| --- | --- | --- |
| 1 | `7caaff61a07654c872a14ba5f48cf7e58c9daaf1`, tree `fc1908f821fd71163bbc78d8ab82afd034efc99f` | **Not accepted**: 2 mandatory, 6 minor, 5 notes |
| 2 | `60760d6f0216c790466a97fb26d92bcaf7bdb6e3`, tree `a7340fa3042bd8eff6711c784563c7f02a56ce15` | **Accepted with minor findings**: none mandatory, 3 minor, 3 notes |

The candidate of round 2 is the second parent of the merge commit ([INTEGRATION](INTEGRATION.json)).
Its differences from round 1 (10 files) were examined in round 2.

## Round 1

| ID | Severity | Finding, in short | Resolution |
| --- | --- | --- | --- |
| M-1 | Mandatory | Records said that details of the machine's protection are off the public record; earlier published commits still hold them | Records corrected (`a80a3947`). The owner was told on 2026-11-25 and decided to merge normally |
| M-2 | Mandatory | The evidence for the startup report of REQ-024 was described wrongly: the guided run's prompt itself asked it to write to the owner | Described as it was; the point counts as not observed, which the owner accepted on 2026-11-25 |
| m-1 | Minor | Two audit rows pointed to checks that the audit did not contain | Audit has a Checks section |
| m-2 | Minor | Remote readings stated for a time at which none was made | Read again at the stated time |
| m-3 | Minor | The last tool correction missed some uses of the Node dependencies | Fixed in `16c83df5` with six cases that fail without it; driver runs and candidate record made again |
| m-4 | Minor | Evidence from earlier tool revisions was counted without saying so | Audit names the revisions and the later real runs |
| m-5 | Minor | Backup coverage withheld without saying so in the audit | Stated |
| m-6 | Minor | Ledger and audit states differed without explanation | Explained in the checkpoint; the ledger is closed with TASK-036 |
| n-1 to n-5 | Note | A merged remote reading; later commits; surviving mutants; the local-only material of REQ-038; the waiver is recorded truthfully | The first four corrected or covered; the last needed nothing |

Found right in round 1: identity, difference and preserved identities; constraints; the R06 identities;
every cited digest and the comparison with the baseline from the raw logs; the counts and the sampled
criteria of the audit apart from the findings; the demonstration logs; no conflict between
instruction surfaces; GOAL unchanged apart from one operating sentence.

## Round 2

All findings of round 1 were found resolved, m-2 in part (r-3). Checks of the reviewer: documentation
verifier, workflow check and 85 tests of the setup tool passed; cited digests and the baseline
comparison equal; after `16c83df5` only documents changed; 42 scenarios of the corrected code with no lost
detection and no false positive.

| ID | Severity | Finding, in short | Disposition |
| --- | --- | --- | --- |
| r-1 | Minor | Use detection opens any existing file that a Node.js process names: with `--repair-node` a FIFO makes setup wait while it holds its lock, and a loop of symbolic links ends in an error. Nothing is changed or lost | Known limit. Next action: a separately selected correction of `tools/bootstrap_local.py` |
| r-2 | Minor | The checkpoint's time is older than its remote reading, and it states no unpublished commit although two were | Corrected with the closing checkpoint |
| r-3 | Minor | The audit's doctor run was made at `7a0d46f4`, not at the audited content; its "second program" also wrote the candidate record | Stated here. The doctor was run again in the main checkout ([MAIN-ENVIRONMENT](MAIN-ENVIRONMENT.json)) |
| r-4 | Note | The question to the owner named disk encryption and backup software, not account permissions | Stated here and in the closing report |
| r-5, r-6 | Note | Surviving mutants; older misses of use detection (paths with spaces, words past the 63rd, removed directories) | Known limits |

## Limits

As the reviewer stated them: GitHub was not contacted, local session logs were read only where a claim
rested on them, and the full driver, native tools, Linux, C271's history and the Library beyond the
R06 files were not checked.
