# Independent P28 supplied-artifact recovery audit

## Verdict

The supplied recovery artifacts are internally byte-consistent. They do not contain a self-contained exact candidate for the interrupted original P28 implementation. Retain **P28-RECOVERY-BYTES-001**. The separate receipt still records the original uploaded tree and commit as `null`.

The executed audit passed **1,229 checks, with zero failures**. This is archive and recovery-evidence verification. It does not verify the reported 597 product tests.

## Exact inputs and checks

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| Supplied `OntoKin_C271_P28_Recovery_Handoff_2026-11-23.zip` | 9,054,965 | `00432c32fc71530cf060ba901330ef38018301363bb2ef378591af540b04ee85` |
| Complete separate `OntoKin_C271_P28_Recovery_Delivery_Receipt_2026-11-23.json` | 96,179 | `a345691387fa0f32133b4202fc94abbca12b17c94a73eadda0fe26838b4bc408` |

| Checked container | Members | Manifest payloads | Source bindings |
| --- | ---: | ---: | ---: |
| Supplied recovery ZIP | 87 | 86 | 70 |
| Original P28 early recovery ZIP | 63 | 62 | 42 |
| Direct P27 design handoff | 397 | 396 | 126 |
| Separate receipt's decoded evidence ZIP | 22 | 22 | — |
| Documentary candidate review ZIP | 5 | Covered by outer manifest | — |
| Retained observations ZIP | 14 | Covered by outer manifest | — |

Checks covered ZIP CRC integrity; safe relative names; duplicate absence; encrypted/symlink/special-file absence; exact manifest inventories, sizes and SHA-256 digests; source snapshot sizes/hashes; and P27's 259 recovery-file bindings. Every one of the root ZIP's 70 declared Git blob IDs was recomputed from its exact bytes and matched. The early/P27 source manifests do not declare blob IDs; their byte/hash declarations matched, and computed IDs are retained separately.

The root ZIP was extracted into a fresh directory owned by this reviewer. Every extracted byte matched both the ZIP and the Director's supplied extraction. The separate receipt's 22-file base64 evidence archive was decoded strictly and checked against its exact embedded manifest and archive digest. No archived script was executed.

## Candidate classification

The only packaged product file is `repository/prototypes/static_tray_v01/current_host_inspection_v01.py`. It is byte-identical in the recovery, original early, and P27 packages: SHA-256 `eea3e6343ae34d9c930a810ca4f363cbcd4264a8d943731f927e41b213755d7a`; Git blob `c583073999493e1c4bd76c5d2093bb34c07d1c05`. These packages contain no new P28 product tests, fixture corpus or modified implementation.

| Recorded identity | Meaning supported by inspected records |
| --- | --- |
| `360c80062e769230199602326fa8de25660df714`, tree `d210b615af1a7272150f3abb5185162d8090aaa8` | P28 starting parent in the original early archive, frozen before implementation |
| `105ac7c5f247fc1a01c1073266763f16e6587757`, tree `a14935d0ade0a5208400b6b0e60af3772387a05e` | P27 design source, explicitly excludes production/test implementation |
| `5f340b4f49d13638f3522e201a1e99b93a19358b`, tree `6a85465aa64ba44dbd13e54087191ec2efbf9e05` | Later documentary recovery publication; candidate manifest contains 25 documentary paths |
| `46b0fce68afb65cfbfcaba64f1276408d93ee85d`, tree `e5d8dc89b9e6fba4315a3386f43e13e758b33c0e` | Recovery receipt publication; candidate manifest contains four documentary paths |
| Original interrupted P28 resulting tree/commit | Unavailable; both fields explicitly `null` |

The supplied checkpoint expressly preserves `597/597 tests`, 945 protected files and prior documentation figures as reported but not reverified. No current product execution was performed or inferred. A retained historical `branch-tree.json` is an actual failed `Transport closed` response; it was preserved and not treated as a successful tree inventory.

The complete separate receipt names a durable `POSTFREEZE-EVIDENCE.zip` at receipt commit `46b0fce68afb65cfbfcaba64f1276408d93ee85d`, path `docs/engineering/localized-repair-c271/p28-recovery-20261123/POSTFREEZE-EVIDENCE.zip`, 30,001 bytes, SHA-256 `84b6f6b57831bb5af7a7f29fda3399c02a3e1f679ce8149e1d7897deb6fcbfa0`. Its inventory describes later recovery publication records, including publication intent and created tree. That ZIP's bytes are not embedded in the separate receipt; this worker did not fetch them. The Director was notified of this exact reference. The separately recorded publication payload Library identity also belongs to the documentary recovery publication, not the original P28 upload.

## Boundaries and next action

This audit covers exact supplied bytes. It does not independently certify all GitHub commit/path/mode mappings, live refs, or remote unreferenced object absence. All local blob declarations were checked; live repository reconciliation remains the Director's responsibility. P26 and older nested archives were verified as unchanged payload bytes but not recursively opened, because their declared phases precede original P28 implementation. No prior-host lookup, package installation, product reconstruction, original upload replay, external mutation or second phase occurred.

**Exact next action:** obtain the full original final P28 uploaded tree SHA together with its publication manifest and completed upload-group list, or obtain an exact implementation/fixtures/tests/review artifact. Inspect the identified object and verify the complete candidate before any branch update. If no such input is available, keep the blocker and obtain an explicit bounded reconstruction decision. New implementation must not be described as recovered bytes.

## Evidence and worker disposition

`audit.py` is the executed audit. `AUDIT.json` records every check, environment, inputs, limits and next action. `archive-inventories.json` records full member inventories. Three `*-source-bindings.json` files retain all source hashes and computed Git blob IDs. `receipt-summary.json`, `receipt-recovery-evidence.zip`, and `candidate-identity-inventory.json` retain the receipt analysis. `WORKER.md` records assignment boundaries. Files are confined to this review directory; the `extracted/` copy is reproducible and may be omitted from the final package if the original input ZIP remains preserved.

This worker has stopped at the missing-source blocker. It holds no integration authority, has no pending writes or running jobs, and has changed no canonical project, GitHub or Library state.
