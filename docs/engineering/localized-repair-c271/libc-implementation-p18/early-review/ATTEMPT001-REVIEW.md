# P18 early recovery — attempt001 rejected

The independent review found **three mandatory correction groups**. Preserve the first archive unchanged and produce a distinct corrected attempt. Do not use this archive to release implementation.

1. **Recovery map closure:** `recovery/session/build_handoff.py` is present but absent from `RECOVERY-FILE-MAP.json`. Add its exact identity and application instructions.
2. **Checkpoint completeness:** add the actual main observation time and the required concise phase/gate table with completed evidence, pending actions and current unknown operations. The early-save state must remain pending in its own frozen archive.
3. **Required handoff context:** give concise verification/review evidence, actual failures or explicit none, checks not run and current unknown operations none. Reconcile historical main/branch CURRENT fields precisely against the declared P18 phase and preserved P17 terminal confirmation. Preserve this rejection in the corrected attempt.

## Checks that passed

All 82 entries are safe, unique, regular inert0644 files with valid CRC and lengths. The exact 81-row payload manifest passes. Fresh extraction to `audit/early-extracted` produced 82 exact files, all mode0600 under a private root. All 40 source snapshots match immutable Git blobs at their declared revisions, including source tree identity. All 27 existing recovery rows are correct. Three P17 predecessor whole-file identities match the completed prior audit. Both external prompts equal their archive members. C262 identity/purpose and the C263 workflow boundary are retained; no offline-complete claim is made.

Main is `70ca7e68ff95df876f801137369d176fe5b2bab3`. Source is the retained receipt revision `8dc78c0a0ba6b69f502d35e0bbd1727c3c2ab7e8`, tree `058c14ef754761aaf4d0e04a7bdb690b2a901ea1`. The archive is 35,040,327 bytes, SHA-256 `d1c6723cb3c666be55a1ebd95fe54a7a61ef412c0097732f6c0ed493d6d1050b`.

## Historical fields

Branch CURRENT still points to P17 terminal delivery. The contained P17 reconciliation and live checkpoint evidence establish that delivery complete. Main CURRENT still contains C270-era `active_task:null`, `awaiting_user_direction`, and an older observed-main field; these are frozen document values, not current branch-state observations. P18 `early_save_confirmed:false` and `save_pending` remain accurate until the later matching saved-file receipt.

No product or recovered code ran. Read-only Git object queries verified source bytes; no repository/index/ref or external mutation occurred. The original archive was not rebuilt. Detailed results and member identities are preserved in `ATTEMPT001-INTEGRITY.json` and `ATTEMPT001-REVIEW.json`.
