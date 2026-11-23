# Bounded worker assignment and result

- **Task:** C271, original P28 exact candidate recovery; `P28-RECOVERY-BYTES-001`.
- **Director / actual worker:** `/root` / `/root/artifact_audit`.
- **Role:** Independent Investigator and Reviewer; no integration authority.
- **Objective and stop:** Verify supplied recovery ZIP, direct predecessor artifacts and complete separate receipt. Stop when an exact source candidate is found or one concrete missing-source blocker is confirmed. No second phase.
- **Launch evidence:** This worker received the actual `NEW_TASK` assignment from `/root`. Launch call arguments/model settings were not exposed to the worker; none are invented. No child workers were launched.
- **Current constraints:** Read-only source inputs; no prior-host searches, no original-upload replay, no product reconstruction, no product execution. Substantive candidate work waits for the Director's early-save confirmation; this worker performed only the assigned source audit.
- **Full governing instructions read:** `session/governing/AGENTS.md`, `ROLE.md`, `docs/workflow/PROTOCOL.md`, `docs/workflow/HANDOFF.md`, `docs/workflow/EPHEMERAL-HOST.md`; worker template also read. The Director owns global startup and saving.
- **Repository and supplied observed refs:** `Omegapy/OntoKin`; main `e43cc6c5777874101a40559e4058ad6826b07e51`; retained branch `work/c271-missing-import-digest-control` at `46b0fce68afb65cfbfcaba64f1276408d93ee85d`; PR274 draft, issue273 open. These live facts were supplied by the Director, not independently re-observed by this worker.
- **Exact input identities:** Recorded in `AUDIT.json` and `REPORT.md`.
- **Allowed reads:** `inputs/p28`, original ZIP and separate receipt in `inputs/OntoKin`, assigned governing files; exact recorded Git objects only if needed. This worker used no GitHub calls.
- **Exclusive writes:** `/workspace/scratch/002c49ccf480/session/reviews/artifact_audit/` only.
- **Protected state:** Canonical project files, GitHub, Library, other workers' directories and source inputs.
- **Execution:** `python3 session/reviews/artifact_audit/audit.py`; standard-library Python ZIP/hash checks; 1,229 passed, zero failed. Current execution environment is recorded in `AUDIT.json` and is not portable host state.
- **Director inspection:** Read `REPORT.md` then `AUDIT.json`; compare input archive digest and review the full candidate/source inventories if needed. The initial audit performs a fresh extraction and does not overwrite it on rerun.
- **Remaining gate:** Exact original P28 tree/complete publication intent or source artifact unavailable. Product test claim remains unverified. Main integration, branch deletion and parent closure remain outside this assignment.
- **Disposition:** Stopped. No active jobs, uncertain writes, publication or integration. The Director owns final delivery and disposition.
