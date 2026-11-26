---
schema_version: 2
trd_id: "TRD-20261125-CE424ADD"
title: "C271 P29 exact publication in local mode"
slug: "c271-p29-exact-publication-in-local-mode"
created_at: "2026-11-25T16:51:10-07:00"
updated_at: "2026-11-25T17:12:52-07:00"
status: "trd_done"
revision: 2
last_action_id: "TO-TRD-006"
status_reason: "Owner explicitly approved the presented revision 1 (sha256 6a6ca5e3...8476ff6) in conversation on 2026-11-25."
---

# Task Requirement Document: C271 P29 exact publication in local mode

## Destination

C271's accepted P29 candidate is published byte for byte on the retained C271 branch, through ordinary authenticated Git from the owner's local clone. The candidate has 245 files, among them the exact 25,817,783-byte evidence archive that a 16 MiB connector limit kept out of the repository. The publication keeps the later recovery history, is independently reviewed and is verified from the remote. C271's records then state the local execution mode, the completed publication, every gate that is still open and one exact next action, and the work stops there.

This document states what that one bounded publication phase must achieve and how success is recognized. It is a requirements baseline, not a plan, and it authorizes no implementation, Git activity, publication or other action.

## Captured user intent

U01 — On 2026-11-25 the project owner invoked the to-trd skill, first without an argument and then, asked which task to capture, with the text of a brief titled "OntoKin: next task for the local AI" as the only argument and no further instruction: derive the task requirements for the task that brief describes.

B — The brief was prepared for the owner on November 25, 2026, from a browser session. It calls itself "a source-based assessment and execution brief" and says: "No repository changes, installations, or project tests were performed for this assessment." Its recommendation is: "Resume C271 in local mode and complete the exact publication of its accepted P29 candidate. Preserve the existing branch history and evidence. Stop after a reviewed, remotely verified publication checkpoint."

The brief's instruction to the local AI, in its words:

- "Resume the existing C271 task in the owner's persistent local clone. The selected scope is P29 publication recovery in local mode, not a new product feature or another general environment migration. Read the current project instructions, reconcile actual local and remote state, authenticate the saved candidate, and publish its exact accepted bytes through ordinary authenticated Git. Preserve subsequent recovery history. Independently review the reconciled publication and verify the remote result."
- "Use the current local workflow for this prospective continuation. Record the mode selection and reconcile C271's historical browser-specific delivery requirement in its task and session records. Preserve historical ZIPs and receipts; do not retroactively mark an unmet gate as passed. This brief does not waive scientific, test, review, integration, or evidence requirements."
- "The stopping point is the verified publication checkpoint. Keep C271 unfinished and PR #274 draft. The next separate phase is the `/0.1.5` operational-plan review."

Why the brief puts this task next (B§2): C271 checks a narrow source-provenance failure, an imported module that is missing its required content digest. Its initial control and the observed refusal are recorded as complete; the required regression and the integration remain open. P29 is accepted preparation work for inspecting the runtime files that those remaining checks use. The brief calls it "a reviewed reconstruction under the adopted design, not proof that the earlier P28 uploads or their reported test result were recovered". Its accepted implementation and evidence are not on the branch, because the publication failed through a connector with a 16 MiB request limit. Ordinary authenticated local Git is now the appropriate route, and the brief adds: "This changes the available transfer route; it does not change the evidence or qualify a host." The brief's judgment is that "preserving and publishing this accepted work has the highest immediate value", that a new feature "would leave the current validation dependency unresolved", and that another setup phase "would repeat completed migration work".

The brief's acceptance list (B§5) is reproduced in its words, because it is the closest available record of how the owner recognizes success. The phase "is complete only when all of the following are evidenced":

| ID | Acceptance in the brief's words |
| --- | --- |
| A1 | "The source archive, receipt, nested candidate, and all 245 accepted payload entries match the recorded identities." |
| A2 | "The exact original candidate tree and parent are preserved, and the current C271 branch also retains all subsequent recovery history." |
| A3 | "Production code, tests, fixtures, adapters, and evidence retain accepted bytes; the four workflow records truthfully reconcile the successors." |
| A4 | "An independent reviewer accepts the publication candidate and any mandatory findings are resolved." |
| A5 | "Applicable documentation and workflow checks are recorded with actual outcomes and executor identity." |
| A6 | "The remote branch and exact evidence blob are independently verified after publication." |
| A7 | "C271's records show publication complete, remaining gates open, and one exact next action. A fresh local session can resume from those records without this conversation." |

It ends: "Stop here. Do not label R03, R04, R05, C271, H22, C260, or the product complete. Do not merge PR #274 or delete its branch. If a required check or transfer fails, retain the candidate and record the precise remaining action; do not disguise a partial phase as complete."

Three principles from the brief govern everything below:

- Exactness. The accepted bytes are published as they are. Nothing is regenerated, recompressed, split or replaced by a pointer (B§3.B).
- Publication is a transfer gate only. It resolves the blocker P29-PUBLICATION-SIZE-001. It passes none of C271's remaining requirements and qualifies no host (B§2, B§5).
- Separate claims. Environment readiness, publication, test qualification, integration and product completion are reported apart (B§8).

## Context and sources

### Source labels

| Label | Source | What it supports |
| --- | --- | --- |
| U01 | The owner's to-trd invocation of 2026-11-25 with the brief's text as its only argument. | That a requirements document for this task is wanted, derived from the brief. |
| B, B§n, A1 to A7 | The brief. It arrived as pasted text without its link targets. A file with the same title and wording, `OntoKin_Next_Task_Local_AI_2026-11-25.md` (21,571 bytes, SHA-256 `c117d204cd2c7832613aa0f04469b75bc3ee04e321a2f40872a74f8a248c8d63`), was found in the owner's downloads folder and read in full. B§n is its numbered section, B§3.A to B§3.E the parts of section 3, and A1 to A7 the rows of its acceptance list. | The owner's intent as the brief states it, its instructions and exclusions, and its point-in-time observations. |
| P | Project instruments on main at `51223c9b94a222f29d38eb6c33808f8e55e2bff9`: `AGENTS.md`, `CLAUDE.md` and `LOCAL-START-HERE.md`; under `docs/workflow/`, `PROTOCOL.md`, `HANDOFF.md`, `CURRENT.json` and `templates/SESSION.md`; the lines of `STATUS.md` on C271, on verification and on the lease; the source-execution ceilings in `GOAL.md`; and the check and worktree sections of `docs/development/LOCAL-SETUP.md`. | The rules that govern a local session and the limits the phase must keep. |
| M | Records of the local development migration on main, under `docs/engineering/local-migration-20261124/`: `DECISION.md`, `RECONCILIATION.md`, `R06-VERIFICATION.json`, `RESULTS.md` and `STORAGE.md`. | The owner's direction of November 24, 2026, the reconciliation of main, C271 and the R06 handoff, and the verified identities. |
| K | C271's own records on its branch at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`, read from Git objects without a checkout: under `docs/workflow/tasks/C271/`, `REQUIREMENTS.md` (R01 to R05, the section list and the P27 to P29 sections), `PLAN.md` (section list and closing sections), `SESSION.md` and the top-level fields of `task.json`; the top-level fields of the branch's `docs/workflow/CURRENT.json`; and under `docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/`, `NEXT-ACTION.md`, `PUBLICATION-BLOCKER.json`, `SUMMARY.md`, `PHASE.json` and the summary fields of `REMOTE-BLOB-DISPOSITION.json`. | C271's requirements, its blocker, its recorded next action and its recorded publication design. |
| G | Live GitHub, read on 2026-11-25: the branch heads, the state of pull request #274 and issue #273, and the R06 terminal record, which is comment 7136207682 on the pull request. | The current remote state and the latest recovery phase, which the branch does not hold. |
| S01 to S12 | Read-only observations made on the capturing machine on 2026-11-25 between 23:30Z and 23:40Z, listed below. | The actual state at capture. They are a snapshot and do not replace the inspection that REQ-005 requires. |

### Limits of what was read

- The brief is not in the repository. This document restates its material content so that it can be read without the brief; the recorded size and hash identify the file that was read. The pasted text and the file were compared by reading, not byte by byte.
- Not read during capture: the contents of the R06 archive and of its nested archives (only the outer archive and the receipt were hashed, at both recorded locations); the inventory file `recovery-review.json`; the P07 qualification plan and its later supplements; the C252 roadmap; the full texts of `OK-ENG-006`, `OK-ENG-009` and `OK-ENG-010`; the R03 and R05 comments on pull request #274; and, in C271's records, the long history arrays of `task.json` and the phase sections P02 to P26 of the requirements and the plan.
- Nothing was fetched, checked out, staged, extracted, committed or pushed, no worktree was created, and no project check or test was run. GitHub was contacted for reading only.
- Statements about what the handoff chain contains come from M, which verified it on 2026-11-25, and from K.

### Observed at capture

| Label | Observation |
| --- | --- |
| S01 | Clone: one worktree, on `main` at `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, equal to its remote-tracking ref; no tracked modification, no stash and no local branch other than `main`. Untracked: `Implementation_Plans/`, the plan tracker of the completed migration. `origin` is an SSH remote for `Omegapy/OntoKin`. |
| S02 | Live remote heads, read with `git ls-remote --heads origin`: exactly two, `main` at `51223c9b94a222f29d38eb6c33808f8e55e2bff9` and `work/c271-missing-import-digest-control` at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`. Both equal the clone's remote-tracking refs. |
| S03 | The C271 branch is 89 commits ahead of and 60 behind main, with merge base `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. The candidate's parent `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` is in the local object store and is an ancestor of the branch head, two commits back (`b706942f` and `bef67902`, both of 2026-11-23). Those two commits changed 35 paths: the four workflow records named in REQ-017 and 31 files under `p29-publication-recovery-r02-20261123/`. Tree `db30c29f24c154f378a5acac713385fc8bb44f52` and blob `9facb186ec11523163520323d83dc58fd68e829c` are absent from the local object store. |
| S04 | The C271 branch predates the migration. It has no `LOCAL-START-HERE.md`, `CLAUDE.md`, `tools/doctor_local.py`, `tools/bootstrap_local.py`, `tools/local-environment.json` or `docs/development/LOCAL-SETUP.md`, and its `AGENTS.md` is an earlier, 7,068-byte version. It holds its own versions of `tools/chat_workflow.py`, `tools/check_local.py` and the documentation verifier. `prototypes/static_tray_v01/current_host_inspection_v01.py` exists there with 233,502 bytes, while the accepted candidate's version has 249,393 bytes (M). `tests/test_current_host_required_images_v01.py` and `docs/engineering/localized-repair-c271/required-images-p29/` are absent. |
| S05 | C271's records on its branch: `task.json` has `schema_version` 1, status `blocked`, blocked reason "P29-PUBLICATION-SIZE-001: accepted implementation preserved; exact evidence archive cannot be transferred by currently permitted routes", and owner `c271-p29-r02-18d6675d4cbb`. The branch's `CURRENT.json` has `schema_version` 1, `active_task` C271, `observed_main` `e43cc6c5777874101a40559e4058ad6826b07e51`, a blocked next action, and a `delivery_policy` of kind `browser-session` with `required: true` and the completion gate "confirmed saved ZIP plus external delivery receipt". |
| S06 | C271's requirement R05, "Verified phase delivery and truthful closure", reads: "Confirm early recovery before substantial work. Verify and save each phase handoff and matching prompts; publish its separate receipt. Keep parent and scope issue open until every requirement, integration and final delivery gate passes." The branch's recorded next action for the publication phase also names "a verified saved handoff". |
| S07 | Main's `CURRENT.json`: `active_task` null, `execution_mode` null, next action `awaiting_user_direction` with C271 as the suggested task, and one unfinished entry for C271 with mode `browser`, status `blocked`, observed head `bef67902` and observation time 2026-11-25T06:52:26Z. Its `observed_main` is `8e847c15e41c7e5970581993c465690526cd43d2`, older than the actual head, as the brief also notes. |
| S08 | Main integration lease (STATUS): released on 2026-11-25T21:33:52Z, with no unknown write. |
| S09 | Pull request #274: open, draft, unmerged, head `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`, base `main`; GitHub reports it as conflicting with main; 18 comments, the last being the R06 terminal record of 2026-11-24T15:32:44Z. Issue #273: open, 12 comments; its last comment, of 2026-11-24T15:32:35Z, has the same body as that terminal record, which is the condition the record sets for the release of the R06 phase owner. |
| S10 | The R06 archive and its receipt are present at both locations that M records: the owner's downloads folder and the local evidence directory beside the clone (`OntoKin-local/handoffs/`). At both, sizes and SHA-256 equal the identities listed below. The archives were not opened. |
| S11 | `.gitattributes` is identical on main and on the C271 branch. Its Git LFS rules cover only `docs/engineering/lfs-archives/`, and no rule matches the evidence path. |
| S12 | Git access: a read over the SSH remote succeeded (S02). No push and no dry run of one was attempted, so write access through that route was not observed. |

### Identities

The brief lists the required identities in B§4. The last column names where else each was found. The two intermediate members are named by the brief; their sizes and digests come from M.

| Item | Identity | Also recorded in |
| --- | --- | --- |
| R06 archive | `OntoKin_C271_P29_R06_Transfer_Capability_Handoff_2026-11-24.zip`, 41,730,084 bytes, SHA-256 `4b8fae8b846c6f2b27ed5e2630c71240739786791cf39f043e787c55ad727bc9` | M, G, S10 |
| R06 receipt | `OntoKin_C271_P29_R06_Delivery_Receipt_2026-11-24.json`, 149,563 bytes, SHA-256 `24aa014cb430d9b7269ee2e39ff08e7005d3630e8dd41c109f824e80039909d8` | M, G, S10 |
| Nested member 1 | `previous-recovery/OntoKin_C271_P29_R05_Authentication_Blocker_Handoff_2026-11-23.zip`, the corrected version 1: 40,934,668 bytes, SHA-256 `406b86f0fe9787ce0b1ead460f8391d3aaf2f79345e852c0ea3107b6469b9182` | M |
| Nested member 2 | `previous-recovery/OntoKin_C271_P29_R03_Transfer_Blocker_Handoff_2026-11-23.zip`, 39,644,692 bytes, SHA-256 `d1d099eff1ccbec55ea01ac61d65fc1d698466cde65fd8142c8b480fdd68f19e` | M |
| Accepted inner ZIP (nested member 3) | `pending-candidate/OntoKin_C271_P29_accepted_Publication_Recovery_2026-11-23.zip`, 38,143,260 bytes, SHA-256 `84b4c7781779a108bf7f6f991bafdcc06632289e4031135c6484c373e6ed114f` | M |
| Accepted payload inventory | `evidence/reviews/recovery-review.json`, field `candidate_rows`: 245 rows | M |
| Original candidate parent | `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` | K, M, S03 |
| Original candidate tree | `db30c29f24c154f378a5acac713385fc8bb44f52` | K, M |
| Evidence archive | `docs/engineering/localized-repair-c271/required-images-p29/evidence/VERIFICATION-EVIDENCE.zip`, 25,817,783 bytes, SHA-256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038` | K, M |
| Evidence Git blob | `9facb186ec11523163520323d83dc58fd68e829c` | K, M |

The accepted payload, as M verified it: 245 files with 35,793,027 bytes and 213 distinct contents; 14 of the files are empty.

| Part of the accepted payload | Files | Bytes |
| --- | --- | --- |
| `docs/engineering/localized-repair-c271/required-images-p29/`, with the evidence archive | 239 | 34,722,710 |
| `prototypes/static_tray_v01/current_host_inspection_v01.py` | 1 | 249,393 |
| `tests/test_current_host_required_images_v01.py` | 1 | 50,181 |
| `docs/workflow/CURRENT.json` | 1 | 188,560 |
| `docs/workflow/tasks/C271/task.json` | 1 | 407,441 |
| `docs/workflow/tasks/C271/REQUIREMENTS.md` | 1 | 86,812 |
| `docs/workflow/tasks/C271/PLAN.md` | 1 | 87,930 |

The first three rows are the 241 files that must keep their accepted bytes. The last four are the workflow records that exist in two successor versions and are reconciled by meaning (REQ-017).

### C271's gates

Read from M and G. R01 and R02 are `done`; R03, R04 and R05 are `not_done`; C271 is `blocked`.

| Gate | State at capture | This phase |
| --- | --- | --- |
| Exact publication (transfer) of the accepted P29 candidate | Open, blocked by P29-PUBLICATION-SIZE-001 | Its only objective |
| Operational-plan review (`/0.1.5`) | Open, a separate later phase | Recorded as the next action, not begun |
| H0 | Open | Not touched |
| H1 | Open, not begun | Not touched |
| Required regression (R03) | Open | Not touched |
| Reviewed integration and actual-main verification (R04) | Open | Not touched; the conflicts with main are documented for it |
| Parent completion and final delivery (R05) | Open | Not touched; its delivery wording is reconciled for local mode |

### Traceability from the brief

| Brief | Requirements here |
| --- | --- |
| Instruction to the local AI | REQ-001, REQ-002, REQ-003, REQ-026, REQ-028, REQ-029, REQ-030 |
| B§1, observed state and its consequences | REQ-002, REQ-005, REQ-026 |
| B§2, why this task comes next | REQ-021, REQ-024, REQ-028 |
| B§3.A, starting state | REQ-004 to REQ-009 |
| B§3.B, authenticating the saved bytes | REQ-010 to REQ-012 |
| B§3.C, accepted tree and later history | REQ-013 to REQ-018, REQ-022 |
| B§3.D, review, publication and readback | REQ-019 to REQ-023 |
| B§3.E, conflicts with main | REQ-027 |
| B§4, input identities | REQ-011, REQ-014, REQ-016, REQ-022 |
| A1 | REQ-010, REQ-011, REQ-012 |
| A2 | REQ-014, REQ-015, REQ-022 |
| A3 | REQ-016, REQ-017 |
| A4 | REQ-019 |
| A5 | REQ-020 |
| A6 | REQ-022 |
| A7 | REQ-023, REQ-024, REQ-025 |
| B§5, stop paragraph | REQ-026, REQ-030, REQ-031 |
| B§6, what follows | REQ-024 for the next action; the rest under Out of scope |
| B§7, test and environment facts | REQ-032, REQ-033 |
| B§8, final report | REQ-034 |

## In scope

One bounded phase of the existing C271 task, on its existing branch, covering:

- The record of the local continuation in C271's own records: the mode and the owner direction it rests on, the objective, inputs, acceptance checks, ownership and stopping condition, and the explicit reconciliation of C271's delivery requirement, which was written for browser sessions.
- Inspection of the actual local and remote starting state, and a worktree for the C271 branch with its own executor.
- Authentication of the R06 archive, its receipt, the nested chain and the inventory of 245 files, and staging of the candidate outside every checkout.
- The immutable candidate commit with the recorded parent and tree, a descendant of the latest C271 head that keeps both lines of history, and the four workflow records reconciled by meaning.
- Independent review, the applicable documentation and workflow checks, a non-forced publication through authenticated Git, and a readback from the remote.
- C271's session checkpoint and publication record, the task and current pointers on its branch, and a record of the conflicts with main for the later integration gate.
- The final report.

Affected, all on the C271 branch: `docs/engineering/localized-repair-c271/required-images-p29/` (239 new files), `prototypes/static_tray_v01/current_host_inspection_v01.py` (replaced by the accepted version), `tests/test_current_host_required_images_v01.py` (new), the branch's `docs/workflow/CURRENT.json`, the records under `docs/workflow/tasks/C271/`, and the new records of this phase. Outside the repository: a staging directory and local working evidence. Main is not affected.

## Out of scope

- The work that the brief lists as following this checkpoint (B§6), each a separate later phase, in this order: the review of the `/0.1.5` operational plan against the published candidate and current host facts; H0, which prepares and independently reviews the exact inspection plan without executing Node or `ldd`; H1 and the remaining qualification stages of the adopted plan; the required regression and the independent integration review, with the conflicts with main resolved deliberately (R03); and reviewed integration, fresh resulting-main checks, branch and worktree disposition and truthful local closure (R04, R05 and parent completion). For the operational-plan review the brief records: require a concrete reason for any further preparation work; assess whether an existing executor meets the adopted contract before more host tooling is built; make any executor substitution explicit and keep the original test meaning. It also records that the original qualification plan explains H0 to H3 and that later adopted supplements remain authoritative and must be read before execution.
- The routine driver, historical behavioural reruns, the candidate's inherited tests and any native loader execution.
- Merging pull request #274, merging main into the C271 branch, resolving the conflicts with main, deleting the branch and closing issue #273.
- Any write to main, including main's `STATUS.md` and `CURRENT.json`, and any use of the main integration lease (D04).
- A new ChatGPT Library ZIP, prompts or separate receipt for this phase (REQ-003, D03), and retrieval of the separately saved Library copy of the evidence archive while the local archive is available.
- Any change to accepted bytes, and any Git LFS conversion, recompression or splitting of them.
- Importing the phase records or the earlier packages of the handoff chain into the repository.
- A new product feature, another environment migration, new physics, broad syntax, additional receivers and model training. The brief says that these "do not follow automatically from this publication task".
- Qualification of the localized-edit evaluator and the separately scoped comparative pilot, which the brief names as the product goal after these dependencies.
- Preparing Node.js 22 or the visual profile, Docker or a Linux executor, and running `--full`, `--force-agent`, Linux validation or hosted CI.
- Changing the source-execution ceilings or any fixture, tolerance or expected outcome, and enabling paid execution.
- Creating credentials, broadening access and changing the repository's visibility.
- Rewriting or relabelling historical handoffs, receipts or failed observations.

## Task requirements

### REQ-001 — Resume the existing C271 task as one bounded publication phase
- Requirement: The work resumes the existing C271 task on its retained branch `work/c271-missing-import-digest-control` as one bounded phase whose single objective is the exact publication of the accepted P29 candidate; it opens no new task, no new product feature and no further environment migration.
- Source: B instruction — "Resume the existing C271 task in the owner's persistent local clone. The selected scope is P29 publication recovery in local mode, not a new product feature or another general environment migration."
- Source: K NEXT-ACTION — C271's own first unmet gate is to resolve P29-PUBLICATION-SIZE-001 and publish the exact accepted candidate.
- Acceptance: The phase is recorded in C271's existing task record under `docs/workflow/tasks/C271/` on the C271 branch; no new task directory, task ID or scope branch is created for it.
- Acceptance: Pull request #274 and issue #273 remain the pull request and the scope issue of the work.
- Depends on: None.

### REQ-002 — Local execution mode, recorded on the owner's direction
- Requirement: This continuation of C271 runs in local execution mode, in the owner's persistent clone and its worktrees, on the owner's explicit direction, and C271's task record and session checkpoint state the mode and the direction it rests on.
- Source: B instruction — "Use the current local workflow for this prospective continuation. Record the mode selection ... in its task and session records."; B§1 — "Record this explicit local continuation before implementation."
- Source: P AGENTS and PROTOCOL (execution modes) — the mode is explicit, stated by the session checkpoint and the task record, and never inferred; "A session resumes a task recorded for the other mode only on explicit owner direction".
- Source: S07 — main's `CURRENT.json` records C271 for browser mode.
- Acceptance: The task record and the session checkpoint name the mode `local`, the entry document that declared it and the owner's direction with its date; that direction is the owner's own instruction for this continuation, which this document records and does not replace.
- Acceptance: The mode is recorded before implementation begins and is not inferred from a path, a machine, a product or an agent name.
- Acceptance: A session on a disposable or remote host does not carry out this phase as a local session.
- Depends on: REQ-001

### REQ-003 — C271's browser-specific delivery requirement is reconciled explicitly and prospectively
- Requirement: C271's task and session records state how its delivery requirement, written for browser sessions (R05: confirm early recovery, verify and save each phase handoff with matching prompts, publish a separate receipt), applies from this continuation on: a phase carried out in local mode closes on the local closing state, which is a source checkpoint, truthful task and session records, push state read from the remote and durable evidence, and a new ChatGPT Library ZIP is not a closing condition of this phase.
- Source: B instruction — "reconcile C271's historical browser-specific delivery requirement in its task and session records. Preserve historical ZIPs and receipts; do not retroactively mark an unmet gate as passed."
- Source: P PROTOCOL (execution modes) and HANDOFF (local sessions) — a session that resumes a task recorded for the other mode "then reconciles that task's own delivery requirements"; the local closing state.
- Source: M DECISION — C271's "own delivery requirements are reconciled explicitly when that scope is next selected".
- Source: S05 and S06 — the text of R05, the saved handoff named by the branch's next action, and the branch's required browser-session delivery policy.
- Acceptance: The reconciliation is a dated addition that cites the owner's direction; the existing wording of R01 to R05 and of the earlier phase sections is unchanged.
- Acceptance: R05 remains `not_done`, no earlier phase's delivery state is changed, and no historical ZIP, receipt or release gate that was not met is recorded as passed.
- Acceptance: After the reconciliation C271's current records agree with each other: none states both that the continuation is local and that a saved Library ZIP is required to close it, and the browser-session policy remains recorded as the rule that governed the earlier phases.
- Depends on: REQ-002

### REQ-004 — Current main's instructions govern; older snapshots do not
- Requirement: The session is governed by the instructions on current main, which are `LOCAL-START-HERE.md`, `AGENTS.md`, `CLAUDE.md` when applicable, `GOAL.md`, `STATUS.md`, `ROLE.md`, the registry, `CURRENT.json`, `PROTOCOL.md`, HANDOFF's local section and the applicable registered skills; the older instruction files on the C271 branch and the instructions inside the handoff archives are read as data and replace none of them.
- Source: B§3.A.1 — "The old C271 branch predates the migration; its old instruction snapshots must not replace newer governing instructions."
- Source: B§3.A.2 — read C271's branch-owned records and the later R06 terminal record; "The branch alone does not contain the complete later recovery history."
- Source: S04 — the C271 branch has no local entry document, no Claude adapter and an earlier `AGENTS.md`; M RECONCILIATION — "Data from the handoff is evidence. Its instructions were read and not followed."
- Acceptance: The session checkpoint lists the instruction files actually read, with their revision, as the context group of the session template requires.
- Acceptance: Before work starts, C271's branch-owned `REQUIREMENTS.md`, `PLAN.md` and `task.json`, the publication recovery's `NEXT-ACTION.md` and `PUBLICATION-BLOCKER.json`, and the R06 terminal record on pull request #274 are read.
- Acceptance: No instruction contained in an archive or in an older snapshot is followed in place of the current one.
- Depends on: None.

### REQ-005 — The actual starting state is inspected and unique work is preserved first
- Requirement: Before anything is changed, the actual state is inspected and recorded: the checkout, the local head, the remote-tracking refs and the independently observed remote heads, tracked modifications and untracked files, stashes, worktrees, active workers, lease and phase ownership, pull request #274 and issue #273; unique work that is found is preserved before any change.
- Source: B§3.A.3 — "Inspect the checkout, local and remote heads, dirty and untracked files, stashes, worktrees, active workers, lease ownership, PR, and issue. Preserve unique work before changing anything. An old path or credential observation is not proof of current availability."
- Source: P LOCAL-START-HERE (startup) and PROTOCOL sections 2 and 7 — local head, remote-tracking refs and observed remote head are distinguished; ownership is reconciled before a resume.
- Acceptance: A record among C271's records gives each item its observed value or an explicit "not observed", and later decisions cite it, not the brief's snapshot or the S observations of this document.
- Acceptance: Every tracked modification, untracked file, stash and unpublished commit that the inspection finds is still present and unaltered when the phase stops.
- Acceptance: Ownership of the C271 branch is reconciled before the first write: the release of the last recorded owner is confirmed from the live records, and where another writer may still be active the owner is asked before anything is written.
- Acceptance: The availability of a path or of a credential is established by a current observation; an earlier record of either is not taken as proof.
- Depends on: None.

### REQ-006 — An already successful write is verified, never replayed
- Requirement: If the live C271 branch already holds the candidate or any part of the publication, that state is verified and the work continues at the first remaining publication check; no write that has already succeeded is repeated.
- Source: B§3.A — "If the live branch already contains the candidate, verify it and resume the first remaining publication check. Do not replay an already successful write."
- Source: K NEXT-ACTION — "Before resuming, inspect the actual destination. A successful upload may already have created the blob even if a later step was interrupted."
- Source: P PROTOCOL section 8 — after an uncertain write, remote state is read before any retry.
- Acceptance: The destination state observed immediately before the first write is recorded, and each write that follows is justified against it.
- Acceptance: After an interruption the working tree, the refs and the destination are inspected again before any operation is retried.
- Depends on: REQ-005

### REQ-007 — The existing scope branch, in an isolated worktree with its own environment
- Requirement: The phase works on the existing scope branch, in the existing C271 worktree if one exists and is available and otherwise in a separate worktree for that branch with its own environment; no environment is copied or symlinked from another worktree.
- Source: B§3.A.4 — "Use the existing C271 worktree if it exists and is available. If a separate worktree is needed, retain the existing scope branch and give that worktree its own environment. Do not copy or symlink another worktree's `.venv`."
- Source: P PROTOCOL section 4 (local parallel work); S01 — at capture the clone has one worktree, on `main`, and no local C271 branch.
- Acceptance: The branch keeps its name, and the worktree's location, branch, source base and environment are recorded at startup.
- Acceptance: No environment in the worktree is a copy of, or a link to, the environment of another worktree.
- Depends on: REQ-005

### REQ-008 — Lightweight startup checks on an explicit executor, without merging main
- Requirement: The startup checks are the local doctor and the workflow check, run through an applicable validated environment; where the C271 branch lacks the newer setup tools, an isolated and explicitly identified executor is selected with current main's setup guide, and main is not merged into the C271 branch to obtain a tool.
- Source: B§3.A.5 — "Use the local doctor and workflow check as the startup checks, through the applicable validated environment. If the old branch lacks the new setup tools, use the current main setup guide to select an isolated, explicit executor. Do not merge main merely to obtain a startup script. A full suite or native loader execution is not a startup action."
- Source: S04 — the branch has no doctor, no setup tool and no environment specification.
- Acceptance: The startup record names each check, the executor used (interpreter, version, platform and environment) and the actual result.
- Acceptance: No full test suite and no native loader execution is run as a startup action.
- Acceptance: The C271 branch history contains no merge of main that was made to obtain a startup tool.
- Depends on: REQ-007

### REQ-009 — A declared, recoverable checkpoint before substantive work
- Requirement: Before substantive work, the phase's objective, inputs, acceptance checks, ownership, local execution mode and stopping condition are recorded in the existing C271 records, and the branch checkpoint is recoverable.
- Source: B§3.A.6 — "Record the objective, inputs, acceptance checks, ownership, local execution mode, and stopping condition in the existing C271 records. Keep the branch checkpoint recoverable before substantive work."
- Source: P PROTOCOL section 8 (local) — a recoverable Git and checkpoint state takes the place of the early recovery ZIP: unique uncommitted inputs are preserved, the checkpoint is recorded, and push state is verified when online.
- Acceptance: The declaration is a commit on the C271 branch that carries no candidate file and is made before the candidate is committed or the four records are reconciled.
- Acceptance: Its push state is read from the remote, or recorded as unconfirmed when offline.
- Acceptance: The stopping condition it records is the verified publication checkpoint of REQ-030.
- Depends on: REQ-001, REQ-002, REQ-005

### REQ-010 — The exact R06 archive and receipt, from the recorded locations
- Requirement: The R06 handoff archive and its delivery receipt are taken from the locations that the migration recorded, the owner's downloads folder and the copy beside the clone, which are checked first; if neither holds them, that exact durable artifact is recovered from its recorded source, and only a missing input or access that actually blocks this step is requested from the owner.
- Source: B§3.B — "Check those specific recorded locations first. Use the identity table below; do not assume a path from this browser session exists on the owner's machine." and "If the local archive is missing, recover that exact durable artifact using the recorded source. Request only a missing input or access that actually blocks this step."
- Source: M R06-VERIFICATION and STORAGE — the durable location is the owner's ChatGPT Library, which a local agent cannot read; S10 — both files were at both locations at capture.
- Acceptance: The location actually used and the identities observed there are recorded.
- Acceptance: If the archive or the receipt is missing, the precise missing file is reported, this step stays open and no other artifact is substituted.
- Depends on: REQ-005

### REQ-011 — The archive chain and the inventory are verified before anything is used
- Requirement: Before anything is extracted or imported, the outer archive and the receipt, the three nested archives in their recorded order, the safety of every member name, and the complete accepted payload inventory with its binding to the selected package are verified against the recorded identities.
- Source: B§3.B — "Verify the outer archive and receipt, the nested archive identities, safe member names, and the complete accepted payload inventory."
- Source: B§4 — the identities, the nesting order, and the inventory `evidence/reviews/recovery-review.json`, field `candidate_rows`: "Verify its binding to the selected package before use. The R05 member is the corrected version 1, not the older version mentioned in an earlier comment."
- Source: P HANDOFF (local sessions) — before anything is imported from a legacy handoff, its outer identity, manifest, nested identities and payload inventory are checked against the recorded values.
- Acceptance: The verification results are recorded before the first extraction and cover the bytes actually used in this phase; every identity equals the value listed under Context and sources.
- Acceptance: The inventory has 245 rows, each with a path, a size, a SHA-256 and a Git blob identity, and the payload of every row is present in the accepted inner archive with those identities.
- Acceptance: The R05 member that is verified is the corrected version 1 of 40,934,668 bytes.
- Acceptance: A mismatch stops the import: the precise difference is recorded and nothing is published from bytes that do not match.
- Depends on: REQ-010

### REQ-012 — Only the needed candidate, staged outside every checkout, in its original bytes
- Requirement: Only the accepted candidate is extracted, into a new staging directory outside every checkout, and its original bytes are used: nothing is regenerated from prose, and no recompressed ZIP, split archive, empty file or Git LFS pointer is substituted for an accepted file.
- Source: B§3.B — "Extract only the needed candidate into a new staging directory outside the checkout. Use the recorded inventory's paths, sizes, SHA-256 digests, and Git blob identities." and "Use the original bytes. Do not regenerate the implementation from prose or substitute a recompressed ZIP, split archive, empty file, or Git LFS pointer."
- Source: P HANDOFF (local sessions) — only needed data is extracted, into a new staging location and never over a checkout.
- Acceptance: Every staged file equals its inventory row in path, size, SHA-256 and Git blob identity, and the staged set is exactly the 245 inventoried files; a file is empty only where its inventory row says so.
- Acceptance: No archive is extracted over a checkout, and no phase record or earlier package of the handoff chain is added to the repository as a file.
- Depends on: REQ-011

### REQ-013 — Destination objects are inspected before writing; unknown is not absent
- Requirement: Before the first write, the destination and the Git objects available there are inspected, with `REMOTE-BLOB-DISPOSITION.json` consulted; the 43 candidate object identities whose earlier reads were rejected by a text-only reader are treated as of unknown existence, not as absent.
- Source: B§3.C.1 — "Inspect the destination and available Git objects before writing. The earlier text-only reader left 43 object identities unresolved; a UTF-8 read error does not prove that an object is absent. Consult `REMOTE-BLOB-DISPOSITION.json` in the publication recovery directory."
- Source: K REMOTE-BLOB-DISPOSITION and PUBLICATION-BLOCKER — of 213 distinct candidate blobs, 166 were absent, 43 of unknown existence and four readable when they were observed on 2026-11-24.
- Acceptance: The inspection and its result are recorded before the first write.
- Acceptance: No step is justified by an absence that is inferred from the earlier read error.
- Depends on: REQ-005

### REQ-014 — An immutable candidate commit with the exact recorded parent and tree
- Requirement: The accepted candidate is preserved as an immutable commit whose parent is `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` and whose tree is `db30c29f24c154f378a5acac713385fc8bb44f52`, built from the verified staged bytes.
- Source: B§3.C.2 — "Preserve an immutable candidate commit with the exact recorded parent and tree. Verify every accepted payload against its inventory. Record any newly created commit identity as new; do not invent a historical commit SHA."
- Source: K NEXT-ACTION and PUBLICATION-BLOCKER — the original candidate binds that parent and that tree.
- Acceptance: The commit's parent and tree equal the recorded identities, every accepted payload in its tree equals its inventory row, and the blob at the evidence path is `9facb186ec11523163520323d83dc58fd68e829c`.
- Acceptance: The commit's own identity is recorded as newly created in this phase; no historical commit identity is invented or claimed for it.
- Acceptance: If the tree built from the staged bytes differs from the recorded tree, the difference is recorded, no other tree is published as the accepted candidate, and the phase is reported as partial under REQ-031.
- Acceptance: Once created, the commit is not amended or rewritten.
- Depends on: REQ-009, REQ-012

### REQ-015 — A descendant of the latest C271 head that keeps both lines of history
- Requirement: The publication is a descendant of the latest observed C271 head that retains the accepted payload and all later recovery records, so that the candidate commit and the later documentary checkpoint commits both remain in the published history, and their content in the resulting tree.
- Source: B§3.C — "The original accepted candidate and the later recovery records descend from the same old parent. Neither fully contains the other."; B§3.C.3 — "Create a reviewed descendant of the latest observed C271 head that retains the accepted payload and all later recovery records. A merge commit can preserve both lines of history."
- Source: K NEXT-ACTION — "Later documentary checkpoint commits must remain in history and in the resulting tree."; S03 — the two later commits and what they changed.
- Acceptance: The C271 head observed immediately before publication is an ancestor of the published head.
- Acceptance: The candidate commit of REQ-014 is retained and can be retrieved from the remote after publication.
- Acceptance: In the resulting tree every path of the observed head is unchanged, except the four reconciled records, the paths that the accepted payload supplies and the records that this phase adds or updates.
- Depends on: REQ-006, REQ-013, REQ-014

### REQ-016 — The accepted bytes are retained exactly in the published branch
- Requirement: In the published branch the production code, tests, fixtures, adapters and evidence of the accepted candidate keep their accepted bytes, and the evidence archive keeps its raw bytes and its recorded Git blob identity.
- Source: B§5 (A3) — "Production code, tests, fixtures, adapters, and evidence retain accepted bytes"; K NEXT-ACTION — "Do not substitute an empty file, LFS pointer, split archive or changed compression for the accepted bytes."
- Source: S11 — no LFS rule matches the evidence path on either branch.
- Acceptance: In the published tree each of the 241 accepted files other than the four workflow records equals its inventory row: the 239 files under `docs/engineering/localized-repair-c271/required-images-p29/`, `prototypes/static_tray_v01/current_host_inspection_v01.py` and `tests/test_current_host_required_images_v01.py`.
- Acceptance: The blob at `docs/engineering/localized-repair-c271/required-images-p29/evidence/VERIFICATION-EVIDENCE.zip` is `9facb186ec11523163520323d83dc58fd68e829c`, with 25,817,783 bytes and SHA-256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`, stored as an ordinary Git blob and not as an LFS pointer.
- Depends on: REQ-015

### REQ-017 — The four overlapping records are reconciled by meaning
- Requirement: The branch's `docs/workflow/CURRENT.json` and C271's `task.json`, `REQUIREMENTS.md` and `PLAN.md`, each of which exists in two successor versions of the same parent, are reconciled by meaning: the candidate's technical acceptance details and the later recovery and blocker history are both kept, and the actual publication outcome and the local mode are recorded.
- Source: B§3.C.4 — "Reconcile these four overlapping records by meaning ... Keep the candidate's technical acceptance details and the later recovery/blocker history. Record the actual new publication outcome and local mode."
- Source: M RECONCILIATION (overlapping records) — what each version adds. The candidate adds `p29_reconstruction` to `CURRENT.json`, six `p29_` fields to `task.json` and 16 lines on the P29 implementation to the two documents; the branch head adds the R02 recovery and delivery fields and seven lines on the R02 recovery.
- Acceptance: Neither version of a record is taken wholesale over the other; the additions of both successors that the reconciliation record names are present in each reconciled record.
- Acceptance: Status, blocker and next action in the reconciled records state the outcome actually reached in this phase.
- Acceptance: The candidate's exact versions of the four records stay retrievable from the candidate commit, and the earlier branch versions from the commit that held them.
- Depends on: REQ-015


### REQ-018 — Concise current pointers, and no evidence deleted
- Requirement: New current entries are concise pointers; detailed historical receipts stay in their existing history or in durable evidence, and no evidence is deleted to make a record smaller.
- Source: B§3.C.5 — "Keep detailed historical receipts in their existing history or durable evidence and use concise current pointers. Do not delete evidence to make a record smaller."
- Source: M STORAGE — handoffs are not moved into the repository; small pointers and referenced evidence replace them for local sessions.
- Acceptance: Any content that leaves a current record remains retrievable unchanged from a recorded Git reference.
- Acceptance: The R03 to R06 phases, whose records exist only in comments on pull request #274 and inside the R06 handoff, are named with those locations and identities; the nested handoffs themselves are not added to the repository.
- Depends on: REQ-017

### REQ-019 — Independent review of the exact publication candidate
- Requirement: Before the reconciled descendant is published, an independent reviewer, who is a separate agent or reviewer and not the authoring session, inspects the precise candidate, the reconciliation, the manifest matches, the retained history and the acceptance claims, and every mandatory finding is resolved.
- Source: B§3.D — "Have an independent reviewer inspect the precise candidate, reconciliation, manifest matches, retained history, and acceptance claims. The reviewer must be a separate agent or reviewer; label self-review honestly if an independent reviewer is unavailable."; B§5 (A4).
- Source: P PROTOCOL section 5 — the reviewer's identity, the inspected candidate and the acceptance criteria are recorded; mandatory findings are resolved and affected changes reviewed again; "self-review cannot close this gate".
- Acceptance: The record names the reviewer, the exact commits reviewed, the findings, their resolutions and the disposition; changes made after a finding are reviewed again.
- Acceptance: The reconciled commit that is published is the one the reviewer accepted.
- Acceptance: A self-review is labelled as one and does not meet this requirement; without an independent reviewer the review gate stays open and the phase is not reported as passed.
- Depends on: REQ-016, REQ-017, REQ-018

### REQ-020 — The applicable documentation and workflow checks, with their actual outcomes
- Requirement: The documentation and workflow checks that apply to the changed records are run against the actual candidate on an explicitly identified executor, and their actual outcomes are recorded, failed and not-run results included.
- Source: B§3.D — "Run the documentation and workflow checks applicable to the changed records using the identified executor. Preserve failed and not-run results."; B§5 (A5).
- Source: P AGENTS (check table) and PROTOCOL section 5 — documentation and navigation changes need the documentation verifier, and workflow records the workflow check; durable evidence names the revision, the environment, the command and the outcome.
- Acceptance: For each check the record gives the source revision, the command, the executor (interpreter, version, platform and environment) and the observed result.
- Acceptance: No expectation, fixture or tolerance is changed to make a check pass; a required check that does not pass leaves the phase partial under REQ-031.
- Depends on: REQ-017

### REQ-021 — Publication through the owner's configured authenticated Git, without force
- Requirement: The reviewed result is published to the C271 branch with ordinary Git through the owner's already configured authenticated route, as a normal non-forced update from the observed head; the branch is never forced back, rewritten or deleted, and the routes that failed are not repeated.
- Source: B§3.D — "Publish through the owner's already configured authenticated Git route."; B§3.C.3 — "Use a normal non-forced publication."
- Source: K NEXT-ACTION — "never force the branch back to the old tree"; "Do not repeat the 16 MiB connector route or the browser-blocked download"; "No credential creation, broader access, visibility change, hosted job or paid execution is requested."
- Source: P PROTOCOL section 7 — once authentication is verified by observation, ordinary authenticated local Git is the normal route for source and evidence; updates are conditional on the observed head and never forced.
- Acceptance: Authentication for writing is verified by observation before the publication is relied on; no credential is created, no access is broadened and the repository's visibility is unchanged.
- Acceptance: The remote head read immediately before the update equals the head that the result descends from; a remote that has moved is reconciled, not overwritten.
- Acceptance: The evidence archive travels as an ordinary Git object in that update, not through a connector request, a browser upload or a browser-chat transfer.
- Depends on: REQ-019, REQ-020

### REQ-022 — A remote readback that local objects cannot stand in for
- Requirement: After publication the remote branch is read back, and the published commit and tree, the candidate commit and the exact evidence blob are verified from objects obtained from the remote, in a way in which locally cached source objects cannot stand in for remote evidence.
- Source: B§3.D — "Read back the remote branch and verify the published commit/tree and exact archive blob. A successful local commit, push attempt, or local object alone is insufficient. Prefer a separate verification fetch so cached source objects do not masquerade as remote evidence."; B§5 (A6).
- Source: B§3.C — "The original candidate tree must remain reproducible. The final reconciled branch tree will have a different identity because it includes later records. Verify both boundaries separately."
- Acceptance: The remote head equals the published commit, and the record gives the command, the time and the result of the readback.
- Acceptance: From objects obtained from the remote, the evidence blob is `9facb186ec11523163520323d83dc58fd68e829c`, with 25,817,783 bytes and SHA-256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`.
- Acceptance: The two boundaries are verified separately: the candidate commit's parent and tree equal the recorded identities, and the reconciled head's own tree identity is recorded and its content checked against REQ-015 and REQ-016.
- Acceptance: A local commit, the exit status of a push or a local object is not recorded as proof of publication.
- Depends on: REQ-021

### REQ-023 — Session checkpoint and publication record on the C271 branch
- Requirement: A concise C271 session checkpoint and a publication record are committed on the C271 branch with the source and remote identities, the archive hashes, the checks, the reviewer, the failures and the next gate, and the task and current pointers on that branch agree with them.
- Source: B§3.D — "Commit a concise C271 session checkpoint and publication record with the source and remote identities, archive hashes, checks, reviewer, failures, and next gate. Update task/current pointers on the C271 branch consistently."
- Source: P HANDOFF (local sessions) and the session template — a source checkpoint, truthful records, push state and durable evidence; no receipt of the receipt.
- Acceptance: The checkpoint follows the session template, states the mode `local` and one exact next action, and is enough for another session to continue without being a transcript.
- Acceptance: `task.json` agrees with the acceptance actually reached, and the branch's `CURRENT.json` points to the task record and to the checkpoint.
- Acceptance: The push state of the commit that carries these records is read from the remote; frozen evidence is not rebuilt to insert later identities.
- Acceptance: Ownership of the phase is recorded as released, or as handed over with its holder named.
- Depends on: REQ-022

### REQ-024 — C271 after the phase: publication complete, remaining gates open, one next action
- Requirement: C271's records show the publication of the accepted P29 candidate as complete and the blocker P29-PUBLICATION-SIZE-001 as resolved, as a transfer gate only, with every remaining gate open and one exact next action: the `/0.1.5` operational-plan review, as a separate phase.
- Source: B§5 (A7) — "C271's records show publication complete, remaining gates open, and one exact next action."; B instruction — "The next separate phase is the `/0.1.5` operational-plan review."
- Source: B§2 — "This changes the available transfer route; it does not change the evidence or qualify a host."
- Source: M RECONCILIATION (open gates) and G (R06 terminal record) — the gates and their states at capture.
- Acceptance: R01 and R02 remain `done` and R03, R04 and R05 remain `not_done`; the operational-plan review, H0, H1, the required regression, reviewed integration with actual-main verification, and parent completion with final delivery are each recorded as open.
- Acceptance: The record of the resolved blocker says that the transfer route changed and that this neither changes the evidence nor qualifies a host.
- Acceptance: The next action is stated once and is not begun.
- Depends on: REQ-023

### REQ-025 — A fresh local session can resume from the records alone
- Requirement: From C271's committed records alone, without this conversation, an earlier chat, ChatGPT Library or an agent's private memory, a fresh local session can identify the execution mode, the governing instructions, the published state, the open gates and the next action.
- Source: B§5 (A7) — "A fresh local session can resume from those records without this conversation."
- Source: P LOCAL-START-HERE and HANDOFF (local sessions) — the checkout persists and understanding is rebuilt from the records; a scope closes on state that a fresh session can read.
- Acceptance: The records state the mode, that current main's instructions govern in place of the branch's older snapshots, the published branch head, the completed publication, each open gate and the one next action.
- Acceptance: How this was evidenced is recorded, and the evidence comes from reading the records without the conversation.
- Depends on: REQ-023, REQ-024

### REQ-026 — PR #274 stays an open draft, issue #273 stays open, the branch is retained
- Requirement: Pull request #274 remains open, draft and unmerged, issue #273 remains open, the C271 branch is retained and C271 remains unfinished.
- Source: B instruction — "Keep C271 unfinished and PR #274 draft."; B§1 — "Do not merge or delete the unfinished branch during this phase."; B§5 — "Do not merge PR #274 or delete its branch."; B§3.D — "Keep issue #273 open and PR #274 draft."
- Acceptance: After the phase the observed state of the pull request is open, draft and unmerged, the issue is open, and the branch exists at the published head.
- Depends on: None.

### REQ-027 — Conflicts with main are documented for the later integration gate, not resolved
- Requirement: The overlap between current main and C271 in `STATUS.md`, `docs/README.md`, `docs/workflow/CURRENT.json`, `docs/workflow/memory.json`, `tools/check_local.py` and `tests/test_local_checks.py` is documented for the later R04 integration gate, including that both purposes must survive reconciliation: C271's readback-configuration bindings and process and environment controls in the driver, and the migration's larger set of instruction files copied into validation workspaces.
- Source: B§3.E — "This publication phase should document the conflicts; it should not merge current main into C271 or resolve runtime conflicts by blindly choosing one side. Main integration remains the later R04 gate."
- Source: M RECONCILIATION (files changed on both sides); S09 — GitHub reports pull request #274 as conflicting with main.
- Acceptance: A record on the C271 branch lists the six files with each side's change as observed at that time, and names R04 as the gate that resolves them.
- Acceptance: The C271 branch receives no merge of main in this phase, no conflict is resolved, and main is not changed by this phase.
- Depends on: REQ-005

### REQ-028 — Historical handoffs, receipts and observations keep their bytes and their meaning
- Requirement: Historical handoff ZIPs, receipts, failed observations and unresolved uncertainties stay unchanged and keep their original interpretation; no gate that was not met is retroactively marked as passed.
- Source: B instruction — "Preserve historical ZIPs and receipts; do not retroactively mark an unmet gate as passed."
- Source: B§2 — P29 "is a reviewed reconstruction under the adopted design, not proof that the earlier P28 uploads or their reported test result were recovered."
- Source: M DECISION (history that keeps its interpretation); P AGENTS (preserve meaning and evidence) and HANDOFF (local sessions) — "A historical ZIP, receipt or release gate that was not met stays unmet."
- Source: K PHASE — the operations of unknown outcome that C271 lists, each marked as not replayed.
- Acceptance: The R06 archive and its receipt keep their recorded identities at the locations used, and no committed historical record or receipt on the C271 branch is rewritten.
- Acceptance: The records keep describing P29 as a reviewed reconstruction; the original P28 uploads and their reported 597-test result stay recorded as unresolved and unverified.
- Acceptance: Operations that C271's records list as of unknown outcome stay recorded as unknown, and none is replayed.
- Depends on: None.

### REQ-029 — No existing requirement is waived
- Requirement: No scientific, test, review, integration or evidence requirement of C271 or of the project is waived, weakened or relabelled by this phase.
- Source: B instruction — "This brief does not waive scientific, test, review, integration, or evidence requirements."
- Acceptance: The acceptance criteria of R01 to R05 in C271's records are unchanged, and the required regression, the routine driver and the integration checks remain requirements of their own later gates.
- Depends on: None.

### REQ-030 — The phase stops at the verified publication checkpoint
- Requirement: The work stops at the verified publication checkpoint: the `/0.1.5` operational-plan review, H0, H1, later qualification stages, the required regression, the routine driver, historical behavioural reruns, native loader execution, main integration and parent closure are not begun, and none of R03, R04, R05, C271, H22, C260 or the product is labelled complete.
- Source: B instruction — "The stopping point is the verified publication checkpoint."; B§3.D — "Do not start the routine driver, H0/H1, or historical behavioral reruns as part of this publication phase."; B§5 — "Stop here. Do not label R03, R04, R05, C271, H22, C260, or the product complete."
- Source: G (R06 terminal record) — "The /0.1.5 operational-plan review and all later acceptance/integration gates remain separate phases."
- Source: P PROTOCOL section 4 (local conduct) — "a new unrelated scope still needs explicit selection".
- Acceptance: No command of an excluded activity is run in this phase, and the records contain no completion claim for any of the named items.
- Acceptance: No new, unrelated scope is started when the phase stops.
- Depends on: None.

### REQ-031 — A failed check or transfer leaves an honest partial phase
- Requirement: If a required check or the transfer fails, the candidate is retained, the precise remaining action is recorded, and the phase is reported as partial and not as complete.
- Source: B§5 — "If a required check or transfer fails, retain the candidate and record the precise remaining action; do not disguise a partial phase as complete."
- Source: P PROTOCOL sections 4 and 8 — a concrete blocker is recorded once; a publication method that was diagnosed as unavailable is not repeated.
- Acceptance: The failure, its evidence and the one exact remaining action are recorded in C271's records, and the verified candidate bytes and the commits already made remain recoverable.
- Acceptance: A failed publication method is not retried unchanged, and the final report then ends with the concrete unresolved publication action instead of the next gate.
- Depends on: None.

### REQ-032 — Test and environment facts stay visible and unchanged
- Requirement: The phase keeps the recorded test and environment facts visible and changes none of them: local readiness (`core` and `python-verification` ready on macOS arm64 with CPython 3.12.13) is separate from the historical Linux x86-64 CPython 3.12.14 qualification contract; the container profile is unsupported and Docker is not needed here; the routine run on the resulting main remains failed, with 4,989 unit tests, of which one does not pass and three are skipped with a resolved temporary directory and 307 distinct tests do not pass with the default symlinked one; 16 external cases are pending; the visual profile is not prepared; and `--full`, `--force-agent`, Linux validation and hosted CI were not run.
- Source: B§7 — "Test and environment facts that must remain visible"; "Those facts do not block an exact publication by themselves; they must be reconsidered when the relevant later gate is selected."
- Source: M RESULTS and P STATUS — the same facts as the migration recorded them.
- Acceptance: No record or report of this phase states or implies that local readiness qualifies the Linux contract, that the routine run passes, or that a pending or unrun item passed.
- Acceptance: No frozen fixture, tolerance or expected outcome is changed; the last-digit difference in regenerated fixture values stays recorded with its platform cause as inferred, not established.
- Acceptance: The checkpoint names where these facts are recorded, so that the gate they concern can reconsider them.
- Depends on: None.

### REQ-033 — Source-execution ceilings and the no-payment policy are preserved
- Requirement: The ordinary source-execution ceilings of 100,000 operations and 30,000 ms stay unchanged, no paid hosted execution is enabled, and no broader timeout is used to change those source limits.
- Source: B§7 — "Preserve the repository's ordinary source-execution ceilings of 100,000 operations and 30,000 ms. Do not enable paid hosted execution or use a broader timeout to change those source limits. The validation driver's per-command timeout is separate from those per-source ceilings."
- Source: P GOAL (invariants, budgets and completion) and AGENTS (the owner's no-payment direction).
- Acceptance: No ceiling, budget or limit in source, configuration or records is changed by this phase, and a per-command timeout of the driver is not presented as a change to a per-source ceiling.
- Acceptance: No hosted workflow is enabled, triggered or waited for.
- Depends on: None.

### REQ-034 — A final report with separate claims and the exact next gate
- Requirement: The phase ends with a report that states the published branch and commit, the preserved candidate tree, the verified evidence blob with its size and SHA-256, how the later history was retained, the independent review, the checks executed and their failures, and the remote readback; that says explicitly whether the publication phase passed; and that ends with the exact next gate.
- Source: B§8 — "Report the published branch and commit, the preserved candidate tree, the verified evidence blob/size/SHA-256, how later history was retained, independent review, executed checks and failures, and the remote readback. State explicitly whether the publication phase passed."
- Source: B§8 — "End with the exact next gate: `/0.1.5` operational-plan review, or the concrete unresolved publication action. Keep environment readiness, publication, test qualification, integration, and product completion as separate claims."
- Acceptance: Each listed item is present with its observed value, or with an explicit statement that it was not reached.
- Acceptance: Environment readiness, publication, test qualification, integration and product completion appear as separate claims, and none is inferred from another.
- Acceptance: The report's last statement is the `/0.1.5` operational-plan review or, if the phase did not pass, the concrete unresolved publication action.
- Depends on: None.

## Decisions

- D01 — The brief's instructions are carried as requirements. The brief is a recommendation and an execution brief written for the owner; its author introduces the choice of task with "My judgment is". The owner supplied it as this document's only source (U01). Its instructions, its acceptance list and its exclusions are captured here as requirements, each citing its section. They are settled by the owner's approval of this document, not by this capture.
- D02 — Recorded identities and observations are audit-time facts. Every observation of the brief that was checked at capture matched: the heads of main and of the C271 branch, the state of pull request #274 and issue #273, the released lease, the identities of the R06 archive and its receipt at both recorded locations, and the figures that M and K record. None was contradicted. They remain snapshots: REQ-005 requires the live state to be read again before anything is done, and no identity here is an instruction to reset a newer ref.
- D03 — How the delivery requirement is reconciled. C271 was written for browser sessions: R05 requires a saved handoff with prompts and a separate receipt for every phase, the branch's recorded next action names "a verified saved handoff", and its `CURRENT.json` records a required browser-session delivery (S05, S06). The brief directs "the current local workflow for this prospective continuation", its acceptance list names no ZIP, and its list of later work ends in "truthful local closure". REQ-003 therefore requires the local closing state and no new Library ZIP for this phase, keeps R05 `not_done` and relabels nothing. HANDOFF leaves a ZIP "optional unless the selected task explicitly requires one"; if the owner requires one for C271 after all, that adds only the package, verification and save rules and changes no other requirement here.
- D04 — Main is not written by this phase. The brief places every record update in "the existing C271 records" and "on the C271 branch", and leaves integration with main to R04 (B§3.A.6, B§3.D, B§3.E). No main integration lease is needed. One consequence follows: until that later gate, or a separately authorized update of main, main's `STATUS.md` and `CURRENT.json` keep describing C271 as it was observed on 2026-11-25, recorded for browser mode, at head `bef67902` and with the publication gate open (S07). A session that starts from main finds the newer state on the C271 branch, where the local startup procedure sends it when a task's records are newer there.
- D05 — The checks selected for this phase. The phase runs the documentation and workflow checks that apply to the changed records (B§3.D). The routine driver that the AGENTS check table names for routine development, the candidate's inherited behavioural tests and the required regression are not run here: C271's R03 holds them, and the brief excludes them from this phase without waiving them (REQ-029, REQ-030). P29's historical results stay preserved as historical evidence (K SUMMARY); this phase transfers the accepted bytes and reruns no behaviour.
- D06 — Left to implementation planning, within the requirements: the name of the phase in C271's sequence (the brief calls it "P29 publication recovery in local mode"); the location of the worktree and of the staging directory, and how the worktree's executor is prepared; which revision of each check tool applies to the branch's records, given what the branch and current main hold (S04); how the 43 objects of unknown existence are observed; how the two lines of history are joined (D07); the form of the readback (D08); the form and location of the publication record, of the record of conflicts with main and of the delivery reconciliation; who the independent reviewer is, provided it is a separate agent or reviewer; how the resumability of REQ-025 is evidenced; and whether a comment on the pull request or the issue accompanies the checkpoint, which PROTOCOL section 7 governs. None of these changes what the owner receives or how success is recognized.
- D07 — A merge commit is the recorded route, not a mandate. The brief and C271's own next action say that a merge commit "can" keep both lines of history. REQ-015 requires that the candidate commit and the later checkpoint commits both remain retrievable from the remote, without force and without rewriting; any joining that achieves this meets it.
- D08 — The separate verification fetch is the preferred form of the readback. B§3.D says "Prefer a separate verification fetch". REQ-022 requires that the evidence of publication comes from the remote and that local source objects cannot stand in for it; the form is left to planning.
- D09 — The migration's verification is not reused as this phase's evidence. M shows the chain intact on 2026-11-25 with 16 checks passed, and S10 shows the outer identities unchanged at capture. REQ-011 still requires the bytes actually used to be verified in this phase, as B§3.B instructs. The method that M records may inform the plan.
- D10 — The R03 to R06 phase records are referenced, not imported. They exist only in comments on pull request #274 and inside the R06 handoff. The brief has only the needed candidate extracted and keeps "detailed historical receipts in their existing history or durable evidence" (B§3.B, B§3.C.5), and M records that handoffs are not moved into the repository. REQ-018 therefore requires pointers with identities, not copies.
- D11 — This document is a requirements source, not a second ledger. C271's task record on its branch remains the acceptance ledger for C271 (P PROTOCOL section 3, "no competing ledgers"). This document tracks only its own drafting and approval state.
- D12 — The later work is recorded, not selected. The order in B§6 is kept under Out of scope so that a reader sees what the publication is for. This document selects, plans and authorizes none of it, and REQ-024 requires that the next action is recorded and not begun.

## Open questions

None.

## Not yet specified

None.

## Assumptions

- Accepted: The brief is the owner's adopted statement of this task, including its recommendation to resume C271 in local mode and its direction to use the local workflow for this continuation. Basis: U01 — the owner supplied the brief as the only source for this document and excluded or changed nothing in it; the owner's approval of this document is where that adoption is confirmed.
