# C271 P28 exact source recovery: independent state audit

**Verdict: the exact original P28 candidate remains unavailable in the inspected durable records. Preserve `P28-RECOVERY-BYTES-001`; do not replay the unknown original upload or reconstruct implementation under this recovery scope.** Thirty-one static evidence checks passed. No product tests ran and no remote state was changed by this reviewer.

## Exact observed state

- Governing main: `e43cc6c5777874101a40559e4058ad6826b07e51`.
- Retained branch: `work/c271-missing-import-digest-control`, head `46b0fce68afb65cfbfcaba64f1276408d93ee85d`, tree `e5d8dc89b9e6fba4315a3386f43e13e758b33c0e`.
- Original P28 intended parent: `360c80062e769230199602326fa8de25660df714`.
- Documentary recovery source A: `5f340b4f49d13638f3522e201a1e99b93a19358b`, tree `6a85465aa64ba44dbd13e54087191ec2efbf9e05`. Current head is its receipt-only B successor.
- PR274 is draft/open/unmerged; issue273 is open. C271 R01/R02 remain done; R03–R05 remain not_done; P01 is done and P02 in_progress. Exact-head GitHub status has zero statuses and zero Actions runs; no CI success is inferred.

The complete time-bounded history since 18:00 UTC contains four commits: P27 A/B and documentary recovery A/B. Comparing the original intended parent to the observed branch head gives two commits and 29 changed documentary paths. No production or test changes appear in that delta. The inspected comments and current operative records supply no original final tree SHA, commit SHA, or exact implementation payload. This is a bounded negative finding; unreferenced Git objects may exist.

## Delivery and ownership reconciliation

Live terminal comments [7113998703](https://github.com/Omegapy/OntoKin/pull/274#issuecomment-7113998703) and [7113999171](https://github.com/Omegapy/OntoKin/issues/273#issuecomment-7113999171) match exactly. They resolve only the previous documentary recovery's delivery-pending fields and release `c271-p28-recovery-acb73444303d`. They explicitly preserve incomplete original P28 implementation, earlier worker liveness and historical unknown operations.

The external receipt identified there is `libfile_fde3_f-46d1b2e049348191b5ab4eb4645330e3_2ab2a24d43748191957f9bcc356b59de`, 96,179 bytes, SHA-256 `a345691387fa0f32133b4202fc94abbca12b17c94a73eadda0fe26838b4bc408`. Actual Library-byte verification belongs to the separate artifact audit. This reviewer verified the live matching declarations and Git identities. The Director separately handles this session's ownership declaration, reported as PR comment7114912816, and later publication.

Main CURRENT still points to completed C270. C270's recorded correction merge is `4d27756f1c503b430dd85219235778a1f78ef101`, with delivery confirmed and ownership released. That older main pointer does not displace the current authorized C271 recovery or reopen C270.

## Additional durable input

`POSTFREEZE-EVIDENCE.zip` was independently fetched as base64 at the exact observed head. Its 30,001 bytes match SHA-256 `84b6f6b57831bb5af7a7f29fda3399c02a3e1f679ce8149e1d7897deb6fcbfa0` and Git blob `5f8d81f94531661ed62e20b427c513d973675592`. All 25 members passed ZIP integrity and were inventoried and hashed. Its publication intent, manifest, create-tree and create-commit receipts refer to documentary source A above. The manifest has 27 documentary files; the intent explicitly says original P28 objects remain unknown and were not retried. This archive does not close the missing-candidate gate.

## Read coverage and limits

The five assigned governing files were read fully: AGENTS, ROLE, PROTOCOL, HANDOFF and EPHEMERAL-HOST. C270 REQUIREMENTS and PLAN were read fully; its operative task and main CURRENT fields were reviewed. C271 REQUIREMENTS was read fully. PLAN's complete unique text was read, with identical historical line sequences matched to the already-read requirements; `AUDIT.json` records every PLAN interval. Current C271 task/CURRENT operative fields, all returned contemporary P27/P28 comment bodies, and the selected recovery outcome/reconciliation/session records were reviewed. Exact input snapshots and hashes are retained.

Historical JSON arrays, most historical check/reference lists, large older PR/issue bodies, and every embedded archive audit assertion were not fully reread. Truncated displays are not counted as full reads. Nine complete nonrecursive Git trees establish no nested AGENTS in the selected docs/workflow/tasks/C271 and docs/engineering/localized-repair-c271/recovery/design directory chains; no whole-repository scan is claimed. The Director owns global startup and separate artifact verification.

No separately recorded reconstruction decision was supplied to this worker or found in the inspected operative sources. The task explicitly requires exact source recovery or a separate bounded decision. Preserve the original unknown upload, historical C270 broad-driver completion, prior-process liveness and P13 difflib uncertainty. Stop this search and finish the authorized documentary handoff.
