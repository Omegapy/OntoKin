# C271 P21 installation-source advisory review

**Finding: no current-source Node or retained-dependency installation plan/report/index pair is available among the declared sources reviewed.** This is a missing input-provenance finding. No runtime command was attempted, no runtime failure is claimed, and this report does not itself adjudicate the P21 stopping point.

Reviewed at 2026-11-22T23:39:49.194214+00:00. Source candidate: `b99f7e3bd33e6d2796d2732f97f21cdc3d04aaf9`, tree `cf9371c486b13fa95d1ff0934c8f2fbd4ac4411d`, ordinary checkout `/workspace/scratch/f0af7d5d28fc/repo`. The independent H0 reviewer remains responsible for the complete-plan decision.

## What the implementation requires

The current inspection implementation requires **both** a `selected-node` installation index and a `retained-dependencies` index. Each index binds an unchanged preparer plan and an actual final report. `_check_installation` requires `selected["source"] == plan["source"]`: the entire H0 source object must agree, including absolute root, commit, tree, and the inventory descriptor's path, SHA-256, size and mode. A matching inspection-module hash alone does not satisfy this relation.

The report must be successful `INSTALLED_EXACT` or `ALREADY_PRESENT_EXACT`, with zero Node, ldd and checker executions. The code also checks source-purpose-report correspondence, archive bindings, complete member inventory, exact installed files/directories/modes and selected destinations. A `DRY_RUN_READY` report is insufficient. These requirements are existing source predicates, not a new condition added by this review.

Source evidence at the candidate revision:

| File | Bytes | SHA-256 | Coverage |
|---|---:|---|---|
| `prototypes/static_tray_v01/current_host_inspection_v01.py` | 196305 | `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206` | Installation and runtime/dependency predicates |
| `tools/prepare_current_host_readback.py` | 19788 | `fd4da23dde3cd75a95c3f5edc071028e5884da62932c32cba4be928e72f87bb3` | Plan/source checks and actual outcome branches |
| `prototypes/static_tray_v01/current_host_readback_v01.py` | 65533 | `2a8144624ea00f3f350a6b7f482c993665b4049b363b93bc399ed0cd7a14ba78` | Immutable Node/dependency pins |

All source was read as data. None was imported or executed.

## Declared evidence and source comparison

| Record | Authoritative source information | Installation-evidence result |
|---|---|---|
| P07 qualification design | Runtime source and installation receipt fields are null; `executable` is false. | A design placeholder supplies neither plan nor report. |
| P09 input locations | Root `/workspace/scratch/e33f906d0e8e/h0_source`; commit `2c6bbfb7aa1d402ce47ffdc24adb4d89b8a81c1e`; tree `03f8751715eb2196f8d56f12868cc572d3392dd8`. | Root, commit and tree differ from P21. P09 explicitly stopped before any operational installation plan, installation or executable inspection plan. |
| P09 archive inventories | Two Node members and 730 C195 members; all target mappings are null. | Authenticated archive observations, not selected destination/file mappings or successful preparer receipts. |
| P19 raw observation plan | Revision `2f791017c6559bfd47937b32b1862cfe98a81551`; inspection source bytes have the same `e14542…` hash as the candidate. | Raw input review stopped at the fifth Python package; it supplies no complete H0 source object or installation pair. |
| P20 preparation plan | Revision `4bf7cb0023d1747be16c8752795819dd9a0cca37`; venv `/workspace/scratch/371612fd9cb3/isolated-p20`. | Prepares seven Python packages. These are separate from Node and the 24 retained validator/Three.js/module-loader files. |
| P21 environment-rebind plan | Revision `b99f7e3bd33e6d2796d2732f97f21cdc3d04aaf9`. | Current revision is bound for the selected Python preservation check. This is not a complete H0 plan or a Node/dependency receipt. |

The complete current H0 `source.inventory` descriptor has not been supplied to this installation-source review. Therefore a full-object equality test against an actual complete H0 plan is not available. No eligible historical preparer plan/report pair is available to compare in the first place. The source table above states only the authoritative fields actually present.

## Exact declared P09 paths

The following exact historical paths returned `FileNotFoundError` from `lstat` during this review:

- `/workspace/scratch/e33f906d0e8e/h0_source`
- `/workspace/scratch/e33f906d0e8e/inputs/OntoKin/OntoKin_C271_P05_Node_Candidate_2026-11-20.tar.gz`
- `/workspace/scratch/e33f906d0e8e/h0_source/docs/engineering/ownership-recovery-c195/evidence/recorded-evidence.tar.xz`

The retained Node archive record pins 45,186,132 bytes, SHA-256 `100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5`. The retained C195 archive record pins 2,611,764 bytes, SHA-256 `b1e54a6cfef133f7004b1988c90bc718fc954409843c2bcac3772d42e904a0c9`. Those are historical data assertions; this review did not re-create or execute either archive. The raw inventories retain all members and deliberately null target mappings.

No exact path to an operational Node/dependency preparer plan, report or index is declared in the reviewed P07/P09/P19/P20 records. Root also confirmed that no additional exact paths are known. Bounded searches found no such actual JSON plan or successful report in the published C271 records or the retained OntoKin evidence scopes enumerated in the JSON companion. This does **not** prove that no installed tree or receipt exists elsewhere. No broader search follows root's instruction.

## Possible remedy and phase boundary

Preserve historical records unchanged. A source-current installation receipt cannot be manufactured by editing an old source object or relabelling a prior report.

For a future separately selected phase, exact existing installed trees may allow the unchanged preparer, without `--apply`, to authenticate the archive and complete tree and produce a fresh `ALREADY_PRESENT_EXACT` report. This requires an independently reviewed plan bound to the actual complete source object, approved archive/member mappings and fresh report paths. This review establishes neither the presence of those trees nor permission to invoke that preparer.

If a selected destination is absent, the no-apply outcome would be `DRY_RUN_READY`, which the H0 inspection predicate does not accept as successful installation evidence. Creating Node or the 24-file dependency tree would require a separately authorized installation phase. Partial or changed content must be refused; no silent in-place repair or substitution is allowed.

**Root has explicitly limited P21 to no preparation or installation.** Either preparer invocation or installation would expand that boundary. The next action is to finish and review the already-selected read-only P20 environment rebind, then let the independent H0 reviewer decide whether missing installation evidence is the first concrete complete-plan blocker and define the next bounded phase. This report grants no runtime approval.

H0 remains unaccepted. H1, the original seven, full routine/R03, main integration/R04 and parent closure/R05 remain unmet. N57 remains an external independent-review obligation, with no runtime pass or skip inferred.

## Review provenance and operation limits

The JSON companion records exact document paths, complete-file SHA-256 values, source revisions, read coverage, authoritative source fields, path observations and bounded search scope. It distinguishes targeted reading from full reading; the large P07 design display was truncated, and no full semantic-read claim is made for it.

This review executed zero product imports, preparer/inspector commands, Node/ldd commands or installations. It made zero shared-runtime, Git or remote mutations. Only the two requested advisory reports were written. Active commands at completion: none.
