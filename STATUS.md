# OntoKin status

Checkpoint: October 28, 2026, C059 integration preparation. The full [GOAL](GOAL.md) remains in progress: an AI-agent programming language for editable 3D shapes, objects and animation, with validated delivery to game engines including Unreal Engine.

## Released capability

The finite force-0.1 / Agent/0.5 / recorded GLB/0.5 release remains complete at its identified implementation and [release evidence](docs/engineering/force-release-validation/README.md). Earlier core, construction, surface and impulse releases retain their meanings. Recorded GLB playback supplies no live destination physics. No new release or engine acceptance is claimed by C059.

## Current development integration

C059 prepares one main integration of the reviewed C032 runtime and later C058 evidence. It excludes the held C035 runtime changes and preserves their exact tests and historical results. Explicit source 0.6 / planar-reach-0.1, Agent/0.6 and GLB/0.6 remain experimental; their discovery text states that release acceptance is incomplete. Existing defaults remain CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1.

[The reconciliation record](docs/engineering/repository-reconciliation-2026-10-28/README.md) identifies source selection, archive proof and actual verification. Fresh candidate checks and main integration are pending at this preparation checkpoint. Historical C032 results remain separate from new executions.

## Decisions and unresolved gates

[OK-DEC-COMPARE-M1/0.1.0](docs/engineering/OK-DEC-COMPARE-M1-0.1.0.md) rejects exact C058 M1 for comparison-only operation saving. No replacement accounting model is adopted. The C057 comparison accounting/passive-authority concern remains open.

Historical original recording evidence remains **24/28, failed**. **P11/P16/P23/L03** remain unresolved, and **C035 remains held, including adverse timing**. Preserve all original limits: 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and 64 cursor updates; all fixtures, horizons/fps/helpers, equations, independent oracles and tolerances remain.

The next runtime objective is to resolve the remaining original recording failures under the adopted semantics and complete-request accounting, beginning with the identified P11/L03 source-evaluation bottleneck and its independent evidence. Every new runtime change requires relevant regression and original-input verification. The finite reach release still needs all 28 source recordings and ten Agent artifacts, CPython 3.11/3.12/3.13, independent rates/native/browser/visual and hostile/inherited roles, formal input closure, and every R01–R12/Q01–Q22 requirement.

## Repository lifecycle and ownership

[OK-ENG-009/0.1.0](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) treats main as the current development baseline and keeps release acceptance separate. Use one branch per active bounded scope, normally at most three active work branches; checkpoints are commits. Retain exact histories before removing inactive branches. The historical archive `archive/pre-consolidation-20261028` preserves all 104 original heads through 95 distinct parents; never merge its index-only tree into main.

Active root scope: `work/main-reconciliation-20261028-c059`, [Issue #26 comment 6478260243](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6478260243). Main lease owner `interactive-main-reconciliation-20261028-c059-7of9` acquired `22c43aa07012eed147f34d7fe311dfd1bf1e8123` at `2026-10-28T19:24:54.000Z`, expiring `2026-10-28T19:54:54.000Z`. Root alone owns main, source edits and runtime/test/SQLite execution. The explicitly delegated cleanup worker may remove only reconciled historical refs; it cannot change source or main. Reconcile actual heads before uncertain retries. Both hosted workflows remain manual-only/default-false; no hosted execution is selected.

## Remaining product scope

Keep the complete GOAL scope: richer typed algorithms/libraries and replacement, textures/mapping/skin deformation, continuous torques and contacts/collisions, general rigid dynamics and mechanisms, vehicles, articulated creatures and purposeful movement, flight/swimming and medium forces, vegetation/flexibility/wind, terrain/buildings, liquids/deformable solids, animation transitions, live engines, measured scale/performance, and a documented direct-tool authoring comparison. Finishing reach will not complete those domains.

The prior [main status](https://github.com/Omegapy/OntoKin/blob/2bb4588e121fcfe99b4d42c734b15b38362f3642/STATUS.md) and [C058 continuation status](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/STATUS.md) preserve their historical evidence and limitations unchanged.
