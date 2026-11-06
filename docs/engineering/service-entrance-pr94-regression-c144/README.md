# C144: PR #94 regression handoff publication

This is an **operational handoff**, not a regression pass or a change to the service-entrance implementation. The code review remains in [PR #94](https://github.com/Omegapy/OntoKin/pull/94); keep its frozen source commit unchanged until the pending regression is audited.

## Verified state, 2026-11-06

- Repository: `Omegapy/OntoKin`; observed `main` before this documentation branch: `3182d4667606db523aafebecd6f7eb708f192fcb`.
- PR #94: **open, draft**. Reviewed head `fe6a9dd23511916f49dc52fc9c5854a8108b95e0`; reviewed tree `ba6067f5fb99658acf3df3e82988e47b04c393e4`.
- C140 independently replayed the focused checker on a merge preview: 22 CLI cases matched expectations; 13 corrupt exports were rejected; both renamed/reordered scene checks and the documentation check passed. This is **not** the full baseline.
- C142 restored the frozen candidate offline on Linux x86-64 with CPython 3.12.14 and verified seven pinned dependencies.
- C143 checked input integrity, the PR, available worker evidence and a local Linux host. No job reference was recorded in the PR, and no original closed `run-01.evidence.zip` was located in the inspected records. The runner inspector returned `outcome=runner_unavailable`: its systemd user manager was unavailable and storage was not persistent. **C143 submitted zero jobs and executed zero regression steps**. An unreported external job cannot be ruled out.
- **Do not merge PR #94 yet.** Its seven-step stock regression, original worker exit, independent audits and integration checks are outstanding.

## Portable regression kit

The complete [C143 ZIP in the owner's ChatGPT Library](https://chatgpt.com/library?file_id=libfile_397a14fcc59c81918fbb61baebaa7458&account_id=personal) contains the offline base, original C132 worker, pinned dependencies, runner inspection scripts, receipts and the detailed `README-START-HERE.md`, `HANDOFF-C143.md` and `NEXT-TASK.md`.

- File: `OntoKin_C143_PR94_Regression_Handoff_2026-11-06.zip`
- SHA-256: `014b208b2e82013c77153ca747dd086a03250a128c3d13d7351be4a7368a3dbb`
- The large ZIP is **not committed to this repository**; a Git commit cannot substitute for its original binary evidence or the returned worker ZIP.

## Next action

1. Check PR #94 and the actual runner queue for an existing job, and check for a closed original `run-01.evidence.zip`. If either exists, follow/audit it without submitting a duplicate.
2. If a persistent Linux x86-64 host is available, use CPython 3.12.14, a functional user-level systemd manager with lingering (or the documented alternate durable supervisor), several GiB free and at least one uninterrupted hour. From the extracted kit, you may probe a reachable SSH host using:
   ```bash
   ssh "$runner" 'bash -s' < C140/C139/runner/inspect-runner.sh
   ```
3. Extract the **entire** kit on the selected host as the submitting account; run `bash run-on-linux.sh --inspect`. If and only if it reports `outcome=no_local_record` and both PR and queue remain clear, run `bash run-on-linux.sh --submit` once. Record host label, start time and job/service ID on PR #94.
4. Preserve the original `run-01.evidence.zip` even if the worker fails. Audit its closed bytes against a fresh checkout. Acceptance requires worker exit 0, all seven steps passing, exactly **3,988 passing baseline methods and zero skips**, matching inventories/license bytes, matching pending reasons for the 16 external cases, both audits passing and both collector decisions reporting `stock_gate_passed`.
5. Only after acceptance, reconcile PR #94 against actual current main and apply the integration procedure from the kit. Re-run relevant checks on the resulting merge.

This record is specific to runner coordination. It does **not** acquire or modify the main integration lease, alter `STATUS.md`, or claim that the development/release gates have passed.
