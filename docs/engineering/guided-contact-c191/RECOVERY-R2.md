# C191 second recovery

On November 10, 2026, coordinator `c191-finalization-e313` resumed the existing
C191 scope after another interrupted discussion. The attached C190 ZIP passed
all 1,441 manifest entries. C190 was already integrated through PR #123.

The actual C191 branch retained 13 commits through
`dc782500d74a8b269c3471121345d6c8566508eb`, including the adopted contract,
independent frozen inputs, adapter, first recovery fixes and verification tools.
PR #124 remained a draft. Main was
`ec5c1fd3299dd915e6ef5d68944b3955978f3eb1`; its prior integration lease had expired.
The existing branch and PR are continued. No earlier published work is discarded.

The published branch did not contain the original C191 or C191-R1 execution
artifacts. Their claimed runs cannot be treated as recovered measurements.
Fresh attempts in this continuation are named **C191-R2 recovery verification**.
The earlier [recovery record](RECOVERY.md), its source changes and documented
failures retain their original identities. No C190 participant trial is repeated.

Two fresh subagents with empty histories and default settings audit the existing
contract/adapter and independent qualification in separate worktrees. They run
in this conversation's execution environment. A separate host or isolation
preflight is not required. The coordinator handles legacy compatibility,
receiving-application checks, integration and the handoff.

The reviewer verified the existing semantic, checker, source and contract seals
before inspecting new adapter outputs. Git ancestry places those freezes before
implementation. No frozen tolerance or historical test is changed. Any new
supplemental probe is identified separately, and each failure is retained before
a correction is tested.

The exact Blender archive and executable hashes were verified. The complete
local driver runs from a detached checkout which no worker edits. Source review
and independent execution precede any integration claim. The final result record
and handoff checkpoint will identify measured outcomes and remaining limits.

The [initial observation](evidence/recovery-r2-start.json) records the exact
repository, input, runtime and ownership state. No hosted run was requested.
