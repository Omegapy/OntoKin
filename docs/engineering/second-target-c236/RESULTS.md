# C236: finite CPU world-pose comparison

**The separately versioned CPU checker is complete and independently accepted
on exact author source `8bbc4ff12cc19e372e9d4808b2c6e8b084b1677e`.** A pose is an object's position and
orientation. This step compares all **18 parts at seven times: 126 poses**
against the original retained source samples. It establishes no native result.

## What changed

The opt-in [checker](../../../tools/second_target_c236/check_poses.py) and
[controls](../../../tools/second_target_c236/tests/run_controls.py) implement
the [contract](CONTRACT.md), committed before controls at `255cb2539c028be9f2d463790262d072dd974510`.
Earlier runtime, CLI defaults, source, material and normal checkers are unchanged.
Each call freshly admits original C221 authority, rereads the pinned GLB and
reference bytes, and binds exact observation bytes and the complete part/time map.
No evaluator, new source sample, export or native application is used.

The original inclusive limits remain **0.001 m position**, **0.001 rad
orientation** and **0.000001 s time**. Position uses the original largest
absolute XYZ-component error. Exact represented-value differences decide
position/time gates; rational cosine bounds decide sign-invariant quaternion
orientation. Displayed angles are diagnostic. No new source-error allowance,
nearest-time rematching or axis conversion is introduced.

Raw world matrices, translations, quaternions and scales remain beside derived
measurements. The predeclared **2^-20** dimensionless matrix consistency envelope
is a separate structural rule that permits finite independent rounding. It does
not prove perfect rigidity or compatibility with an unknown native decomposition.
The original GLB establishes unit source scale, but C220 supplies no scale
tolerance. C236's exact-unit-scale condition is an explicitly separate stricter
profile; an honest near-unit native scale may fail it while the original pose
gates pass. Both outcomes and every loss remain visible.

Structural refusal is `FAIL_CLOSED`. Admissible accuracy failure is
`FAIL_POSE_LIMIT`; separate scale-only failure is `FAIL_SCALE_PROFILE`.
Every admissible comparison retains all 126 rows, 378 translation components,
378 scale components, per-part/time summaries and the complete loss list.
Only both the original pose gates and added scale profile passing produces
`PASS_CPU_POSES`. Labels such as `unattested-native` confer no trust.

## Executed checks

| Cohort | Passing methods |
| --- | ---: |
| New C236 controls | 37 |
| Unchanged C221 authority controls | 20 |
| Unchanged C222 correspondence controls | 23 |
| Unchanged C234 material controls | 24 |
| Unchanged C235 normal controls | 31 |
| Total affected methods | **135** |

All methods passed with zero test failures, errors or skips on Linux x86-64 /
CPython 3.12.14. Exact source commit/tree and all checked files remained unchanged.
[Author receipt](evidence/AUTHOR-RESULTS.json). The initial C221 launch omitted
mandatory `--report` and exited with argument error 2 before any test method;
its raw result is preserved separately. Correcting the command required no
source change, and the 37 already successful C236 methods were not repeated.

[Independent review](REVIEW.md) passed **85 public scenarios**: 83 predeclared
CLI cases and two API controls resolving same-process fresh-admission coverage.
It independently audited 36 complete reports: 4,536 controlled rows over the
same 126 unique source pairs, including 40,824 matrix residuals and 4,536
orientation ratios. Expected negative outcomes are successful controls, not
claims that all deliberately changed observations meet accuracy limits.

## Publication and actual-main verification

[PR #206](https://github.com/Omegapy/OntoKin/pull/206) merged at `6ff721689fcc52c24bf8129ccb6c84b258fd488c`, with reviewed tree `69d6c157f350548d40e4911d978678d6b39fb0a5`. The independent publication review passed 64 checks. A fresh affected cohort on that actual merged revision passed all 135 methods; documentation verified 29 preserved sources and 5,019 local links. Source remained clean and unchanged. [Integration receipt](evidence/INTEGRATION.json) and [actual-main receipt](evidence/ACTUAL-MAIN-RESULTS.json) preserve the exact distinction between author, local reviewed and published revisions.

This documentation closure releases the integration lease. The final archive, fresh offline restore and saved delivery remain separate required operations in scope #205; no save is inferred from a merged PR.

## Preservation and limits

The input C235 archive and documented fresh restore passed. Initial scratch
ENOSPC and SIGKILL checkout failures remain preserved; one serialized retry
with reduced duplicate temporary bytes and lower Git cache settings succeeded.
The exact cause of SIGKILL remains unproven. All surviving earlier heads were
already retained; five dirty historical navigation files were preserved
separately without applying them. The alternate scope #201 and four held drafts
remain unchanged.

All completed source and frozen scientific evidence are confirmed saved in
[recovery version 4](https://chatgpt.com/library?file_id=libfile_fde3_f-234745aad0848191a0c14fd8feaffb70_2ab2a24d43748191957f9bcc356b59de&account_id=personal).
The [bindings](evidence/RECOVERY-BINDINGS.json) separate this save from final
successor delivery. [Scope #205](https://github.com/Omegapy/OntoKin/issues/205)
owns publication, actual-main checks, verified final ZIP and confirmed delivery.

R07 remains pending. Original Blender strict-normal failure, Godot build lineage,
rendering/capture/provenance, cross-target/semantic treatment, persistence,
settings/cameras and process protocols retain their unmet gates. Other
interpreters, native observations and a full release are unestablished.
All native/version, source-evaluation, export, import, render, native scene-write
and aggregate starts are zero. C233's completed aggregate and all nine
recommendations/41 criteria retain their original scope.

After verified delivery, the [next separate bounded step](NEXT-TASK.md) is a
CPU semantic-treatment and explicit-loss checker. No second feature runs here.
