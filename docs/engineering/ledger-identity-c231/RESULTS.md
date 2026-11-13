# C231 ledger identity repair result

## Result and exact checked source

The narrow repair is checked on local author commit
`e9f811dbd0d32d16aea55ce90ca3615a138a3416`, tree
`e21381900f793a5fd30f9ef8fe2124d848e928c8`. The repaired ledger SHA-256 is
`1436c7f10c4ba35fae5d90e7a4201c3bf7d92315d2baa385dcbd8de89f807c03`.
Publication is a separate root-owned step; these author identities must not be
called published merely because a later candidate has equal file bytes.

Both original authority files stay open while the capability can mutate. The
retained file objects must remain regular, singly linked and equal to their
initial identities. Existing pathname/content checks, nonblocking/no-follow
opens, directory checks, journal bounds and checked append remain. Same-content
replacement now poisons the capability even when a deterministic control makes
the replacement's numeric identity look equal to the original.

Cleanup covers partial creation, failed persistence, stop/completion, disposal,
interruption and process boundaries. Interrupted cleanup-lock acquisition keeps
ownership and finalization available for a later first close attempt. Unknown
close outcomes are never retried on a possibly reused descriptor number. An
already active exception retains precedence over a cleanup failure. The
[contract](CONTRACT.md) states the precise trusted-host and collection limits.

## Actual checks

| Check | Observed result |
| --- | --- |
| Complete affected C201 cohort plus new controls | 307/307 passed: 284 existing and 23 additive; zero failures, errors, skips, expected failures or unrun methods; 46.793 seconds. |
| Source stability | Exact commit/tree, clean status and complete tracked-file hashes unchanged during execution. |
| Deterministic old-code controls | Both marker and journal replacement bypasses reproduced when only the replacement's observed numeric identity was forced equal. This is defect evidence. |
| Independent final controls | 17 groups / 136 assertions passed, including both replacement rejections and separate later STOPPED observations. |
| Additional independent regressions | Both context-body exception cases and both interrupted-cleanup-lock cases passed. |
| Process lifecycle | One bounded CPU fork in the final author run exited 0, was reaped and did not time out; parent/child ownership and partial-creation coordination were checked. |
| Original test and historical inputs | Original 36-method ledger file unchanged; 42 frozen records, 301 overlapping protected-input records and 33 historical digest files preserved. Counts are not summed as distinct files. |
| Author documentation check | 29 preserved sources and 4,856 local links passed. Root candidate/final navigation checks are separate. |

The [author record](evidence/author/AUTHOR-RESULT.md),
[complete selected method outcomes](evidence/author/affected-run-03/RESULT.json),
[unittest log](evidence/author/affected-run-03/unittest.log) and
[independent controls](evidence/independent/candidate-e9f-independent-result.json)
identify actual Linux x86-64 / CPython 3.12.14 execution. No other interpreter or
platform is established.

## Failures and superseded evidence retained

The first reporting runner failed before test execution because it supplied an
incompatible unittest discovery root. Its script and stderr remain in the
handoff. The corrected runner executed all 306 methods at the earlier source
`8e7e4fca361358a87fc34b722d4e558e2140ba12`; that pass did not cover the later
independently demonstrated cleanup-lock defect.

Independent probes retained the context-exit failure on
`71e5e17` and the cleanup-lock/finalizer failure on `8e7e4fc` before correction.
The final source and added regression passed the expanded 307-method cohort.
Draft source checkpoints, failing probes, earlier passing checks and complete
source inventories are preserved distinctly in the C231 source history and
handoff; none is reclassified as a final-source result.

## Scope and remaining obligations

Only the experimental ledger implementation, additive controls and the new
component contract change product-facing source. Shared compiler, parser,
geometry, Agent, exporter, budgets, workflows and the entire original ledger
test file retain their bytes. Historical pin disagreement with the new live
ledger is expected source evolution; C229/C230 plans remain consumed and must
not be repinned or replayed.

**R02 remains blocked pending a fresh complete passing aggregate.** No aggregate
or native application ran in C231. C224/C226/C228 outcomes, the unresolved C226
A08 deadline cause, original strict Blender normal failure, held drafts,
consumed native schedules, all nine recommendation records / 41 criteria,
other interpreters and pending external roles retain their meanings.

The [next task](NEXT-TASK.md) is one independently reviewed immutable aggregate
with complete method/process accounting. Finish publication and one verified
saved C231 handoff, then stop.

## Published integration and actual main

[PR #195](https://github.com/Omegapy/OntoKin/pull/195) merged published candidate
`937fb460521f97da4ff7f55931a62ea9caea17f0` at
`231caabacabaeca810acc8d75a081be3646b4a4b`, with exactly the independently
reviewed tree `edd9b17f0e82599947bf01ab05da2b68ae02b74d`. This is distinct from
the retained local author and integration candidate histories.

Fresh checks on that actual main passed all 307 methods in 48.368 seconds, with
zero failures/errors/skips/unrun methods and unchanged clean source. Its bounded
CPU fork exited 0 and was reaped without timeout. Documentation preservation
passed 29 sources / 4,874 local links. The work branch was observed absent. The
[integration receipt](evidence/INTEGRATION.json) binds these results.

This following documentation-only closure releases root ownership; its exact
published revision and final saved ZIP are recorded in the final handoff and
scope #194 after conditional publication. Archive/save completion cannot be
claimed by this earlier sealed repository record.
