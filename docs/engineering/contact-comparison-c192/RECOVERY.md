# C192 recovery after the interrupted publication

The November 10 continuation recovered a completed comparison. It did not run
the participant task again. Both routes remain rejected at both frozen targets;
the next implementation task is the bounded C193 diagnosis in [NEXT-TASK.md](NEXT-TASK.md).

## What had already been completed

The uploaded C191 ZIP passed its inventory and hash check: 302 manifest files,
511,531,279 uncompressed bytes. C191 had merged through PR #124 at
`afae5f59558bc90200691f6727709124d2e119ea`.

At recovery, GitHub main was `1b311a9b884d5de638d0247d2e0233dd19f05e62`, the
previous C192 integration lease. Draft PR #125 was at
`95dafda2c2388c03772bdaecb6be10c95d07fbf3`. It contained the frozen preparation
and first-submission results. The surviving coordinator checkout was clean at
`0dd0e1fb44abb73d2fef65bc3a318c54ca2ea13f`, tree
`0641a47137f70d860cd82362a0c35abfa7be5a5d`. That local checkpoint also contained
the completed reuse phase, independent rebuild and scene-replay records,
receiving evidence, reviews, failure accounting and C193 instructions.

The exact recovered tree was published to the same PR as
`9722fa93256cf2c023d2d877f4e7060f40c5fb5f`. This is a publication identity for
the recovered local tree, not a new participant trial or a new measurement.
[Publication receipt](evidence/recovery/recovered-publication.json)

The original participant histories also survived:

| Route | First submission | Reuse submission |
| --- | --- | --- |
| OntoKin | `721f3691935cadf0d11cead973db11358071d33b` | `9a98e15ad242ddc0d20288fa8f43e6ef44e164c6` |
| Python | `375f0df7bb63e8d7b72c7f0cf41643db3000da22` | `f3b1b5fa89e1e19075793e0c75b3e68b53c5a844` |

Both first submissions directly descend from the frozen local preparation
`9d1118f63195c8458aa804f2a99922cc780365aa`. Its tree matches published
preparation `25c5efb9a8d9b3cae2f4eebb6dc33c1dc7db5742`. The outgoing source
bundle retains the participant histories and the recovered coordinator history
under explicit checkpoint refs. No older handoff is needed to inspect them.

## What this continuation verifies

Two fresh default subagents with empty histories reviewed the recovered record
in separate worktrees. One replayed the numerical evidence; the other checked
the protocol, source localization, chronology and reporting. Their reviews are
retained under [numerical recovery](reviews/recovery-numerical/REVIEW.md) and
[protocol recovery](reviews/recovery-protocol/REVIEW.md).

Recorded-evidence replay checks the archive inventory, 116 frozen input files,
all six failed participant builds, 28 analytic controls, captured scene replay
and rebuild/regeneration identity. It performs no new native simulation or
receiving-application execution. The original actual receiving receipts and
twelve rendered panels retain their original provenance; the comparison image
was inspected again during this recovery.

The saved coordinator/participant records attest to the original launch
settings and empty histories. They do not provide independently recoverable
provider telemetry, exact model snapshot, token totals or cost. Those fields
remain unavailable. The preserved commits independently establish the source
chronology and actual edits.

## Integration and remaining limits

The former lease expired at `2026-11-10T15:44:36.028873+00:00`. After checking
the actual refs and outstanding work, owner `c192-recovery-9c186c07` acquired a
new bounded lease through an expected-head nonforce update. The acquisition
commit is `4f54fa0ee87fe1b11660652a2373ca9ad2c9b9f1`.
[Lease receipt](evidence/recovery/lease-acquisition.json)

This continuation changes documentation and recovered evidence only. The
runtime, original C191 backend and contract, historical tests, frozen checkers,
budgets and hosted workflows retain their bytes. Applicable fresh checks are
recorded separately from inherited results. The older full legacy driver is
still **FAILED**: 4,239 methods passed and thirteen torque artifact-read methods
were not run after their original 30,000 ms class-setup timeout.

The outgoing checkpoint and publication receipt identify the actual merge,
resulting-main verification and lease release. A review approval here means the
experiment record is fit to integrate. It does not accept its rejected outputs,
establish an authoring advantage, or qualify a release.

## Verified publication

PR #125 merged at `1b16f2754b964899c9c8b4993342f4246df26f15`, with reviewed
candidate `332a78aadbd8e95e04dc128c91f610d0d6ee4cf1`. Both have tree
`921267e1c43b8620acb70182a720527874538564`. Fresh resulting-main checks passed
all 116 frozen inputs and documentation preservation (29 source records, 706
documents and 3,835 local links). Exact candidate-tree equality and unchanged
legacy scope were verified. [The publication receipt](evidence/recovery/publication/resulting-main/result.json)
records those commands and the clean checkout. A subsequent status/evidence
commit releases the lease; the outgoing checkpoint names that actual final main.
