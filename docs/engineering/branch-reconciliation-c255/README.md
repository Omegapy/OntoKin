# C255 branch reconciliation

The owner's additional November 16 instruction consolidated the ten reviewed
experimental-source PRs into development main under
[OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md).
This is a C255 delivery amendment, not a new scientific milestone or C256.
All ten PRs are merged. The observed inventory fell from **13 branches and ten
open PRs to three branches and no open PRs**. One redundant C234 working ref
remains because an authenticated deletion operation is unavailable.

The exact source-integration result is main
`05aadeb008186b6644a2dbd67a2f7e5f2e23766d`, tree
`55f86b06508e607cb6ea34af610668518171368d`.
The [integration record](evidence/INTEGRATION.json) identifies each original head,
preceding main, actual merge and resulting tree. All ten original heads remain
ancestors. The 137 reviewed additions match their original source bytes;
16,165 baseline paths remain unchanged and the only other baseline change is
the exact reviewed STATUS lease. The four original C255 scientific files remain
byte-exact. This closure changes documentation only.

## Published source integrations

| PR | Original working branch | Actual merge commit |
| --- | --- | --- |
| [#155](https://github.com/Omegapy/OntoKin/pull/155) | `work/c211-blender-receiving` | `64502cb69a46282062feb202c1fd9d8315b176d7` |
| [#165](https://github.com/Omegapy/OntoKin/pull/165) | `work/c216-native-receiving` | `28bbe7acb60bf62d92710d7a3dfde31a70d97aa0` |
| [#167](https://github.com/Omegapy/OntoKin/pull/167) | `work/c217-namespace-capture` | `2d01576738be1757b906b0c5ab7504462fbb6d06` |
| [#169](https://github.com/Omegapy/OntoKin/pull/169) | `work/c218-saved-scene-reopen` | `b4c0197f5ee607b1d461bd92f95f59c6c6358ded` |
| [#222](https://github.com/Omegapy/OntoKin/pull/222) | `work/c246-held-observer` | `5dd6d3b1bb31dcf664e389186db21880fccc9f08` |
| [#224](https://github.com/Omegapy/OntoKin/pull/224) | `work/c247-held-mesh-arrays` | `5e16bbdeaa357abb96e2575c01a598638642c774` |
| [#226](https://github.com/Omegapy/OntoKin/pull/226) | `work/c248-held-materials` | `dd7a625ec4f210107d65df8e3db309d625604b99` |
| [#228](https://github.com/Omegapy/OntoKin/pull/228) | `work/c249-held-animation-inventory` | `36616c8a48ae9a8eda4cbecd05533fbb6c04b499` |
| [#230](https://github.com/Omegapy/OntoKin/pull/230) | `work/c250-held-pose-observation` | `30bdb64c43796c6cac530dbd233da1c701e79d7d` |
| [#232](https://github.com/Omegapy/OntoKin/pull/232) | `work/c251-controlled-attachment` | `05aadeb008186b6644a2dbd67a2f7e5f2e23766d` |

The post-merge [branch snapshot](evidence/POST-MERGE-BRANCHES.json) confirms that
all ten merged working branches are absent. The [PR snapshot](evidence/POST-MERGE-OPEN-PRS.json)
confirms no open PRs. The original heads and historical local validation commits
remain preserved in source history and handoff bundles; deleting a redundant ref
does not delete their reviewed source.

## Checks and independent review

Three actual subagents performed the independent scopes in the shared hosted
Linux environment, inheriting the same model as the integrator. They were not
separate machines, external models or execution on the user's computer.
Here, "local checks" means processes in that hosted workspace. The "offline
observation checker" checks recorded, inert observations without a live native
application; it does not mean execution on an offline user machine.

| Evidence | Executed result and scope |
| --- | --- |
| [Older-source checks](evidence/OLDER-CHECKS.json) | 68 fresh CPU methods passed: C211 27, C217 15, C218 26. C216's 14 historical controls were bound to their exact inputs and results, not reexecuted. |
| [Observer-stack checks](evidence/STACKED-CHECKS.json) | 212 fresh inert CPU methods passed. These checks do not parse GDScript or start a destination. |
| [Independent combined review](evidence/INDEPENDENT-REVIEW.json) | Approved the exact disjoint source union for experimental development integration. Its original wording remains preserved. |
| [C211 discovery correction](evidence/C211-DISCOVERY-ADDENDUM.json) | The 27 C211 CPU methods join default unittest discovery. The receiver runtime remains explicit opt-in. Static import review found no shared released-runtime mutation. No aggregate rerun is claimed. |
| [Actual published-main checks](evidence/ACTUAL-MAIN-CHECKS.json) | Fresh 31 C255 methods, 14 bound C253 files / three cases, and preservation of 29 sources / 233 sections / 5,415 local links passed at the exact source-integration main above. The prior 68 and 212 method observations were reused only after exact source/input equality. |

These are separate bounded observations, not a full aggregate regression run.
The one-link difference from the 5,416-link combined candidate comes from the
reviewed lease text replacing one local reader-task link. Source, command and
log hashes are recorded in the linked results. Run the documentation preservation
checker on this exact closure candidate before publication; its author/review
receipt belongs to the amended handoff.

## Preserved failures and execution limits

The original strict normal-fidelity failure remains failed. Historical render
failures and the C216 namespace-origin refusal remain preserved. Finite import,
save or reopen evidence does not establish lossless normals or general receiving
support. Native holds and consumed schedules are unchanged.

C251's current-authority qualification remains **FAIL**: its frozen bindings for
`AGENTS.md` and `GOAL.md` no longer match current authority. The executed
[failure log](evidence/C251-CURRENT-AUTHORITY-FAIL.log) is retained. The separate
[historical reproduction](evidence/C251-HISTORICAL-BINDING.json) passed against
the original held source; it does not qualify current main. No frozen pins were
regenerated to conceal the mismatch. Integration admits reviewed experimental
source without authorizing a native run or completing R07, R08 or any unmet C221
criterion. No native process, model trial, schedule replay or C256 reader started.
Comparative advantage remains unproven.

## Remaining branches and concrete blocker

| Ref | Observed disposition |
| --- | --- |
| `main` | Holds all ten reviewed source integrations at the revision above; this documentation closure is separately reviewed before publication. |
| `archive/c174-model-research` | Intentionally retained at `46821f412c2941efa0ab75a20b42a52d905a8d50`. It is an index-only historical branch, not product source. Complete offline ancestry is unavailable, so safe deletion is not established. |
| `work/c234-cpu-materials` | Still present at `4afb8d2d2d9a62bf1b5195b09c716607008e8a6c`. Its source is already an ancestor of main and preserved by original C255. Ref deletion remains blocked. |

The [cleanup record](evidence/CLEANUP-LIMITATION.json) distinguishes the known
failure from an unknown remote outcome. The connector exposes no branch/ref
deletion operation, the hosted repository has no configured Git remote, and the
cloud browser showed a signed-out session. One Delete action had no effect;
API readback confirmed the same C234 head. No credentials or user takeover were
requested. PR #202 refers to a different, already deleted branch and provides
no alternative action. The exact remaining maintenance action is to remove only
the C234 ref after fresh head/retention checks through a supported authenticated
capability, then confirm its absence. C174 remains retained.

## Delivery state and next action

The original C255 version-0 handoff remains a completed saved delivery;
[scope #238](https://github.com/Omegapy/OntoKin/issues/238) is closed. The separate
[progress recovery ZIP](https://chatgpt.com/library?file_id=libfile_fde3_f-c6367137bebc819195890c217c42b27c_2ab2a24d43748191957f9bcc356b59de&account_id=personal)
is confirmed saved: 830,699 bytes, SHA-256
`3d814b9a8dc94975bfd8a55c71f1f61273ee0b89ad34015e3aa1b18448643fae`.
Its [identity receipt](evidence/PROGRESS-SAVE.json) and the
[retention review](evidence/RETENTION-REVIEW.json) identify exact predecessor and
recovery bindings. Copied records retain their original bytes; the
[binding map](evidence/SOURCE-EVIDENCE-BINDINGS.json) connects them to the full
handoff evidence. Local build paths inside historical records are provenance,
not the sole recovery location.

**The amended final ZIP is still pending at this closure.** Scope
[#240](https://github.com/Omegapy/OntoKin/issues/240) remains open for the C234
cleanup blocker and final delivery. Publish this reviewed documentation closure,
verify and save the amended handoff, confirm the exact saved identity, then stop.
Keep the previous saved handoff available. The [next-task record](NEXT-TASK.md)
separates that closure from any future finite GLB-reader work.
