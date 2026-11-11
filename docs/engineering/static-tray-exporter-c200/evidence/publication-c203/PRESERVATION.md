# Preserved C200 evidence for C203 publication

This record distinguishes recovered historical bytes from new publication work.
The [independent C203 preservation audit](PRESERVATION-AUDIT.json) of the
restored C202 input completed
on November 11, 2026 at 14:41:56.448520 UTC. It did not run qualification,
Blender, receiving, Node, lifecycle or author processes, and did not repeat the
numeric or visual reviews.

## Immutable identities and retained evidence

| Item | Identity or verified count |
| --- | --- |
| Executed source commit | `62b2316cc3f88db187f69fbd7fdb2cf0997a97de` |
| Executed source tree | `87779ee65fb31dbd6de0f4372697a91f1bf4744a` |
| Executable-input lock SHA-256 | `e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0` |
| Original evidence overlay | 303 files, 51,356,757 bytes |
| Frozen repository inputs checked | 301 |
| Native archive members checked | 2,565 |
| Native archive regular payload | 1,704 files, 60,009,373 bytes |
| Explicit final-review bindings checked | 26, none unresolved |
| Direct receipt copies already present | 255 |
| Additional exact log copies recovered | 74 files, 58,822 bytes |

The [original native archive](../native-execution/captured-native-execution.tar.gz)
has SHA-256 `e09cffdb792a90d7c08c74000b301dd2045401027edf3d48a05276252bee127b`.
Its [original manifest](../native-execution/MANIFEST.json) has SHA-256
`b693875183201c9a1806442c692b945546df00efa35b6059a8cb4aecc9be34d6`.
The [recovered-log manifest](RECOVERED-LOGS-MANIFEST.json) identifies each
copy. The recovered log copies came from that sealed archive. They are original
process output copied to its recorded repository destination, not newly
produced logs. The 255 existing and 74 recovered direct copies cover all 329
native receipt-copy entries.

The [independent final review](../result-review/RESULT-REVIEW.json),
[numeric review](../result-review/NUMERIC-REVIEW.json),
[visual review](../result-review/VISUAL-REVIEW.json), input lock and pre-execution
approval remain unchanged. The original coordinator's pending-review flag is
retained alongside the later acceptance. C199's consumed failed start is not
removed. The audit verifies these original artifacts; it does not constitute
review of a later publication candidate or proof of integration.

## Supplied-package gaps and later recovery

The C202 input and the initial C203 preservation audit lacked these nine
preparation-log candidates. A later
[fresh original-path recovery](FRESH-LOG-RECOVERY.json), recorded at
14:47:41.791911 UTC on November 11, 2026, found all nine in the surviving
original workspace and copied their 2,707 bytes into the candidate. No listed
candidate remains unavailable. The older missingness records remain unchanged.
The table below preserves the evidence available before that discovery.

| Candidate, relative to `evidence/preparation/` | Retained basis |
| --- | --- |
| `synthetic/tests.log` | Exact SHA-256 and 617-byte size in synthetic RESULTS.json |
| `synthetic/actual-node-controls/Q01-changed-reference/synthetic-readback.stdout.log` | Process-derived filename; no individual retained hash |
| `synthetic/actual-node-controls/Q01-changed-reference/synthetic-readback.stderr.log` | Process-derived filename; no individual retained hash |
| `synthetic/actual-node-controls/Q01-positive/synthetic-readback.stdout.log` | Process-derived filename; no individual retained hash |
| `synthetic/actual-node-controls/Q01-positive/synthetic-readback.stderr.log` | Process-derived filename; no individual retained hash |
| `synthetic/actual-node-controls/Q03-positive/synthetic-readback.stdout.log` | Process-derived filename; no individual retained hash |
| `synthetic/actual-node-controls/Q03-positive/synthetic-readback.stderr.log` | Process-derived filename; no individual retained hash |
| `synthetic-driver/stdout.log` | Candidate from interrupted account and naming convention; no standalone binding |
| `synthetic-driver/stderr.log` | Candidate from interrupted account and naming convention; no standalone binding |

The recovered [synthetic-test log](../preparation/synthetic/tests.log) matches
the retained SHA-256
`3b819175599f065c983e488db4c255cbafed0567045d9d5cf5760f78b9ddfc4d`
and 617-byte size in its [summary receipt](../preparation/synthetic/RESULTS.json).
Six Node stdout/stderr files are correlated with exact original working
directories, matching historically hash-bound process receipts, byte counts,
probe stdout fields and recorded warning process/loader details. The two driver
streams now exist in the original repository evidence directory beside matching
command/start/completion receipts; stdout agrees with the three-test PASS
summary and stderr is empty. The
[driver completion receipt](../preparation/synthetic-driver/COMPLETED.json)
remains unchanged.

Eight stream hashes are newly observed recovery bindings, not retroactive
individual hashes from the original qualification. The fresh recovery manifest
records every source, destination, hash, size, classification and correlation.
No fresh test or process output substitutes for original bytes.

The independently audited source still carries the original historical
qualification and regression limits. The publication candidate must receive
its own source/evidence binding review and applicable fresh checks before
integration. Its final published tree and actual-main results must be retained
as separate records. C199 and C200 schedules remain closed throughout.

## Historical status preservation

The [previous status text](STATUS-before-C203.md.txt) retains all 69,085 bytes
of STATUS immediately before the concise C203 result summary. Its SHA-256 is
`33d686e46dcbe7ff37301237bfe7105653295f672b67f054b1a0f6ff303281f8`.
The archive already contains the verified C203 lease paragraph. The same
paragraph is retained byte for byte in current STATUS. The `.txt` suffix keeps
this raw record's original root-relative links from being treated as active
navigation at its archival location; no historical content was rewritten.
