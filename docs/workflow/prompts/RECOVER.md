# Prompt 2: Recover OntoKin After an Interruption

Repository: https://github.com/Omegapy/OntoKin

Last confirmed **development handoff ZIP**: [PASTE LINK]

Newer recovery file or partial handoff: [PASTE LINK OR NONE]

Interrupted task or last known event: [DESCRIBE BRIEFLY OR UNKNOWN]

In a **fresh chat**, recover the existing OntoKin task at its **first unmet gate**. Complete no more than one bounded phase, save a verified handoff ZIP if work remains, and stop. Do not start another milestone.

**Mandatory ephemeral-host rule:** This is a different disposable host;
prior chat temporary paths, packages, virtual environments, workers and
processes are gone or inaccessible. Recover durable GitHub/Library state,
not the previous machine. Reconstruct only required current-host inputs;
follow `docs/workflow/EPHEMERAL-HOST.md`.

1. Read the handoff's `README-START-HERE.md`, checkpoint, recovery status, and any newer recovery file. Read live `CHATGPT-START-HERE.md` and required repository instructions at the observed `main` revision, once per unchanged file.
2. Reconcile the task and plan, branches, PRs, integration ownership, test evidence, Library receipts, workers, and unpublished work. A timeout does **not** prove a GitHub write, merge, or upload failed. Inspect actual destinations before retrying; retain operation and commit/ref identities. Never replay blindly.
3. Separate completed, pending, and unknown gates. Resume the existing authorized task and branch without duplicating completed work. If code is merged, address only remaining checks, branch disposition, or delivery. If everything is already complete and saved, report the existing handoff and stop.
4. Follow `docs/workflow/PROTOCOL.md` and `docs/workflow/HANDOFF.md`. Declare one phase and stopping point. Confirm an early recovery ZIP before substantial work. Use bounded independent subagents where available; keep detailed evidence in files. Perform applicable checks and review.
5. Preserve remaining work; verify, save, and record the new handoff's receipt separately. Report verified outcomes, limits, and next action. Leave the parent task open if any gate remains. **Continue the next phase in a new main chat.**
