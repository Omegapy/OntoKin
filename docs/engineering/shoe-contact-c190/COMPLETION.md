# C190 publication completion after the later interruption

**November 9, 2026, America/Denver.** This continuation recovered the completed C190-R2 experiment from the surviving workspace, verified it independently, and finished its publication and handoff. It did not run another authoring trial. The exact publication result is in the user handoff checkpoint and [PR #123](https://github.com/Omegapy/OntoKin/pull/123).

## Two interruptions, different recovery outcomes

The first C190 thread left its plan and evaluator identity in GitHub but no recoverable native results. The next thread therefore ran the explicitly identified C190-R2 recovery replication. [That history](RECOVERY.md) remains separate from the original unavailable trial.

The R2 replication's sources, submissions, numerical audits and rendered evidence survived the later interruption. GitHub still held draft PR #123 at `b54ff44546df2f675916aabbe02d55382a000ea1`, with main at `4e1b5d1f1eeb5dc67807ed82f3675ab0412f3de2`. The previous workspace also held uncommitted result documentation and the two completed evidence archives. The missing items were final publication, checkpoint, source snapshot/bundle, manifest and outgoing ZIP.

An independent authenticated audit recovered the published R2 checker archive. All 106 members matched the surviving evaluator. The original four checkpoint files and the published checker archive remain unchanged. The recovered trial archive has 768 members, SHA-256 `87cefb40d9d58581f90a77caf1e0d4f66bbd82c847909fa9e99fc79d0b6f437d`; its 766 shared files match the recovered handoff. The render archive has 61 members, SHA-256 `83c7a06c0e043b45460a0d0cdcd95d817880d2be9c1ba9e20def925210c6ff4d`; all 60 shared files match. The additional archive members are their manifests and trial guide. Archive receipts are in [completion-evidence.zip](completion-evidence.zip).

## Fresh verification in this continuation

| Check | Observed result |
| --- | --- |
| Supplied C189 handoff | All 448 manifest files verified; numerical replay matched the published result bytes. |
| C190 seals | All 104 evaluator entries, 209 runtime entries, 50 accepted Blender files, 48 OntoKin files and 46 failed-first-submission Blender files verified. |
| Independent evaluator replay | All 45 trajectory controls and three swept controls reproduced their expected outcomes. |
| Six final outputs | All three Blender projected finals passed; all three OntoKin outputs retained their expected contact failure. Their exact measurements matched the recovered results. |
| Receiving-format checks | Twelve raw/final GLBs had zero errors and warnings; the three projected Blender finals retain the disclosed unused-sampler information. Three.js reproduced six clips and eighteen selected poses. |
| Fresh Blender source audit | Four formal builds, two third-stop saved-scene replays and two native collider controls reproduced the recovered result. Twenty sealed formal stable-file comparisons and five third-stop repeat comparisons passed. |
| Fresh OntoKin source audit | Four formal builds and two independent third-stop builds reproduced the negative result and its native diagnostics. All 209 runtime files stayed unchanged. |
| Visual review | Coordinator inspected all eighteen preserved GLB render panels. No new browser capture or new rendering is claimed by this continuation. |

The replay receipt, independent Blender and OntoKin reviews, command logs, hashes and authenticated repository audit are in [completion-evidence.zip](completion-evidence.zip). Extract it beside the two original evidence archives.

The fresh Blender audit matched 61 comparable prior files byte for byte. Three raw/final JSON reports differ only in object-key order; their decoded content is identical. The initial strict report comparison and its corrected semantic comparison are both retained. These report-format differences do not change the native sources, traces, exported bytes or acceptance rules. The summary differs only in its completion timestamp.

The native Blender control again changes left final travel from 200.000003 mm to 250.000000 mm when the shoe's collision component is removed. The other lane and fixed-part records remain bit-identical. Every native carriage X sample and timestamp is preserved in the projected final files. [Native result and projection limits](README.md)

## Publication and restart

Owner `c190-completion-d0b9f6a7` reconciled the expired recovery lease and acquired completion lease `47c1c5a42a7b85f344e22fff724aaff952711de5` with an expected-head update. The scope is the project README, STATUS and `docs/engineering/shoe-contact-c190/`. The current result, preserved evidence and concrete C191 proposal are published through the existing PR. The outgoing source snapshot and checkpoint identify the actual resulting main; no synthetic snapshot is presented as the remote head.

The two original evidence ZIPs retain their recovered bytes. New completion receipts are separately identified. Product runtime, historical tests, adopted meanings and hosted workflows remain unchanged. The applicable repository gate is documentation preservation plus this experiment's replay and native audits. No full regression, hosted CI pass, unseen-task advantage or complete contact release is claimed.

Continue with [C191](NEXT-TASK.md): define an explicit experimental source-owned contact relationship and qualify a small mapping to the measured Blender/Bullet setup. The proposal has not yet been adopted or implemented. Use two fresh subagents in the current conversation's execution environment, with separate writable directories, empty histories and default settings. No separate host or isolation preflight is required.
