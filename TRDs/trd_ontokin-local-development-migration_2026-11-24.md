---
schema_version: 2
trd_id: "TRD-20261124-E65C6113"
title: "OntoKin local development migration"
slug: "ontokin-local-development-migration"
created_at: "2026-11-24T23:01:50-07:00"
updated_at: "2026-11-24T23:06:00-07:00"
status: "trd_done"
revision: 3
last_action_id: "TO-TRD-006"
status_reason: "Owner explicitly approved the presented revision 2 (sha256 7e5a81b9...b8e5cc) in conversation on 2026-11-24."
---

# Task Requirement Document: OntoKin local development migration

## Destination

OntoKin's ordinary development runs in the owner's existing local clone, with a repeatable native Python environment and a repository-based agent workflow, so that a fresh local agent session resumes the selected task from repository records instead of a ChatGPT Library handoff. Unfinished work (C271), retained evidence, legacy handoffs and every existing project requirement stay preserved and truthfully reported throughout.

This document states what the migration must achieve and how success is recognized. It is a requirements baseline, not a plan, and it authorizes no implementation, installation, Git activity, publication or other action.

## Captured user intent

U01 — On 2026-11-24 the project owner invoked the to-trd skill with a single argument, the file `OntoKin_Local_Development_Migration_Brief.md`, and no further instruction: derive the task requirements for the migration that brief describes.

B — The brief was prepared for the owner on November 24, 2026. Its stated purpose is to "Establish a repeatable local development environment and durable agent workflow while preserving unfinished work, evidence, and project requirements." It calls itself "an implementation brief, not a record of completed installation": its author inspected GitHub source and the latest matching handoff, not the owner's computer.

The brief lists eighteen requirements "extracted from the user's intent" and names the basis of each. They are reproduced in the brief's words because they are the closest available record of what the owner asked for:

| ID | Requirement | Basis given by the brief |
| --- | --- | --- |
| MIG-01 | Use the existing local clone as the normal development workspace. | Explicit request |
| MIG-02 | Create or validate an isolated Python environment for this project. | Explicit request |
| MIG-03 | Determine which dependencies are missing or incompatible and install the required ones. | Explicit request |
| MIG-04 | Make a definite container decision. | Explicit request |
| MIG-05 | Make setup repeatable on a fresh machine or worktree. | Necessary implication |
| MIG-06 | Preserve unfinished work and unique files from the old handoff process. | Necessary implication |
| MIG-07 | Let a fresh agent resume without relying on the previous chat. | Explicit request |
| MIG-08 | Preserve goal-directed "Go/Continue" operation. | Interpreted intent |
| MIG-09 | Keep project status, requirements, plans, and handoff information consistent. | Explicit request |
| MIG-10 | Support the user's graphical coding-agent workflow. | Established preference |
| MIG-11 | Support safe parallel work. | Existing project practice |
| MIG-12 | Keep tests and evidence attributable to the actual source and environment. | Existing project contract |
| MIG-13 | Preserve the existing no-payment policy for hosted CI. | Existing owner direction |
| MIG-14 | Finish bounded work through the established merge-and-delete lifecycle. | Existing owner direction |
| MIG-15 | Avoid requiring a new ZIP and Library transfer after every ordinary local session. | Necessary workflow change |
| MIG-16 | Distinguish environment readiness, task completion, and product qualification. | Necessary correctness condition |
| MIG-17 | Preserve provenance while reducing repeated startup material. | Necessary implication of project growth |
| MIG-18 | Give the local agent a concrete implementation sequence and completion checklist. | Explicit request |

Two principles from the brief govern everything below:

- Persistence is not memory: "the local files can survive a new conversation, but a new agent still needs to reconstruct its understanding from recorded state". A persistent machine removes repeated environment reconstruction; it does not remove the need for checkpoints (B§1).
- Readiness is not completion. Environment readiness, task completion and product qualification are different results and are reported separately (MIG-16, B§14).

The brief marks each statement as "Observed" (a fact found in inspected sources), "Required" (the owner's intent or a condition needed to deliver it) or "Recommended" (an engineering decision the brief proposes). The requirements below say which kind each rests on. Decision D01 and the Assumptions section record how the recommended decisions are treated.

The brief also contains a prompt "intended to accompany this file when the user is ready to implement it" (B§15). The owner has not issued that prompt, and this document does not act on it.

## Context and sources

### Source labels

| Label | Source | What it supports |
| --- | --- | --- |
| U01 | The owner's to-trd invocation of 2026-11-24 with the brief as its only argument. | That a requirements document for this migration is wanted, derived from the brief. |
| B, B§n, MIG-nn | `OntoKin_Local_Development_Migration_Brief.md`, read in full from the owner's Downloads folder: 72,126 bytes, SHA-256 `1f05310df589ed3a303290712eaaad460d2e451371693ebc85347a5c6450d2cb`. B§n is its numbered section; MIG-nn is a row of its requirement table (B§3). | The owner's intent as extracted by the brief, the brief's recommended decisions, and its audit-time observations. |
| P | Project instruments read at commit `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`: `AGENTS.md`, `ROLE.md`, `GOAL.md`, `STATUS.md`, `CHATGPT-START-HERE.md`, `docs/workflow/` (`PROTOCOL.md`, `HANDOFF.md`, `EPHEMERAL-HOST.md`, `README.md`, `BROWSER-PROMPTS.md`, `registry.json`, `CURRENT.json`, `templates/SESSION.md`), `OK-ENG-006`, the OntoKin session and delivery skills, `pyproject.toml` and the dependency files under `tools/`. | Existing rules that the migration must amend or preserve. |
| S01 to S12 | Read-only observations made on the capturing machine on 2026-11-24, listed below. | The actual state at capture. They are a snapshot and do not replace the inventory required by REQ-001. |

### Limits of what was read

- The brief is not in the repository. This document restates its material content so that it can be read without the brief; the recorded size and hash identify the exact brief used.
- Not read during capture: the R06 handoff archive and its receipt (the brief's H1 and H2), the external tool documentation the brief cites (its D1 to D9), GitHub PR #274 and issue #273, and the full text of `OK-ENG-009` and `OK-ENG-010`. Statements about them are the brief's or come from the project files that cite them.
- GitHub was not contacted. "Remote" facts below are the clone's remote-tracking refs as last fetched.
- No project check, test or installation was run during capture.

### Observed at capture

| Label | Observation |
| --- | --- |
| S01 | Machine: Apple silicon Mac (arm64), macOS 26.6.2. |
| S02 | Clone: on an external APFS volume; one worktree; branch `main` at `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, equal to the `origin/main` remote-tracking ref; clean working tree; no stash. `origin` is an SSH remote for `Omegapy/OntoKin`. This is the commit the brief inspected. |
| S03 | C271: remote-tracking branch `origin/work/c271-missing-import-digest-control` at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`, 89 commits ahead of and 4 behind `main` (merge base `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`). On that branch `CURRENT.json` is 192,376 bytes and the C271 `task.json` is 418,591 bytes; the task status is `blocked` with reason P29-PUBLICATION-SIZE-001. Git blob `9facb186ec11523163520323d83dc58fd68e829c` and tree `db30c29f24c154f378a5acac713385fc8bb44f52` are absent from the local object store; commit `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` is present. |
| S04 | Workflow state on `main`: `CURRENT.json` (5,527 bytes) has `latest_task` C270, `active_task` null, next action `awaiting_user_direction`, `observed_main` `ca57a50cd2910861832b0bfcca609980efd78139` (older than the actual head) and a `delivery_policy` of kind `browser-session` with `required: true`. `registry.json` names `CHATGPT-START-HERE.md` as the entry point. |
| S05 | Python: Homebrew CPython 3.12.13 (`python3.12`, and the first `python3` on the capturing shell's PATH); uv-managed CPython 3.12.11 and 3.11.14; system Python 3.9.6; no CPython 3.13 found. uv is installed; pyenv and Conda are not. The clone has no `.venv`. |
| S06 | Node v25.9.0 and npm 11.12.1 (Homebrew); no Node.js 22 found; no `tools/node_modules`. |
| S07 | Git 2.50.1; Git LFS 3.7.1; GitHub CLI 2.86.0. Docker, Blender and Godot were not found. The Claude desktop application is installed. |
| S08 | Absent from the clone: a root `CLAUDE.md`, `LOCAL-START-HERE.md`, any Dockerfile, `uv.lock`, `tools/bootstrap_local.py`, `tools/doctor_local.py` and `docs/development/`. `.gitignore` ignores `.python-version` (line 325) and `.venv/`. Six `.claude/skills/` symlinks resolve to `.agents/skills/`: communication, ontokin-delivery, ontokin-learning, ontokin-session, to-implementation-plan and to-trd. |
| S09 | No file named as the R06 handoff was found in the owner's Downloads folder. Apart from the brief itself, the newest OntoKin files there are the C271 handoffs P22 (2026-11-22) and P28 (2026-11-23), so no R06 receipt was identified either. Other locations were not searched. |
| S10 | The capturing Claude Code session received the root `AGENTS.md` as loaded project instructions with no `CLAUDE.md` present, and listed all six project skills. This is one observation of one installed version, not the verification that REQ-019 and REQ-020 require. |
| S11 | Current rule text that the migration must reconcile: `AGENTS.md` requires "fresh relevant local checks in the assistant's hosted workspace, not user's computer"; `STATUS.md` says "fresh assistant-workspace checks"; PROTOCOL §8 requires a verified saved ZIP for every bounded browser development or recovery phase "unless owner changes requirement"; PROTOCOL §4 says "Never start a second phase in the same thread"; PROTOCOL §3 requires task records under `docs/workflow/tasks/` before substantial implementation, requires "no competing ledgers", and says the named `to-trd` and `to-implementation-plan` skills need explicit invocation. |
| S12 | Dependency and tool facts match B§2.1. `pyproject.toml` declares `ontokin-reference` 0.4.0, `requires-python >=3.11`, `dependencies = []` and build requirement `setuptools>=77`, and packages an installed facade, a payload and selected package data. `tools/force-agent-verification-requirements.txt` pins six packages; `tools/native-reader-verification-linux-cp312.lock` pins those six plus Pillow 13.0.0, one hash each, for CPython 3.12 on Linux x86-64. `tools/package.json` pins esbuild 0.25.10, gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1 and Three.js 0.180.0. `tools/check_local.py` offers `--full`, `--force-agent`, `--output-dir`, `--list` and `--timeout`, keeps explicit root-file and source-directory inventories, and its Node preflight accepts Node 18 or later. `tools/chat_workflow.py` `new-task` takes its base from `CURRENT.observed_main`. Both hosted workflows are `workflow_dispatch` only, with `enable_hosted_ci` defaulting to false. |

### Identities recorded by the brief (B§9.1)

The brief calls these "audit-time observations and historical identities, not instructions to reset a newer branch". S02 and S03 confirm the first three locally; the others were not checked during capture.

| Item | Identity |
| --- | --- |
| Main | `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` |
| Retained C271 branch | `work/c271-missing-import-digest-control` |
| C271 branch head | `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448` |
| Associated work | PR #274 (draft, open); issue #273 (open); C271's recorded requirements R03 to R05 unfinished |
| Latest matching handoff | `OntoKin_C271_P29_R06_Transfer_Capability_Handoff_2026-11-24.zip`, 41,730,084 bytes |
| R06 SHA-256 | `4b8fae8b846c6f2b27ed5e2630c71240739786791cf39f043e787c55ad727bc9` |
| Accepted candidate parent | `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` |
| Original intended candidate tree | `db30c29f24c154f378a5acac713385fc8bb44f52` |
| Exact unpublished evidence | `docs/engineering/localized-repair-c271/required-images-p29/evidence/VERIFICATION-EVIDENCE.zip`, 25,817,783 bytes |
| Evidence SHA-256 | `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038` |
| Evidence Git blob | `9facb186ec11523163520323d83dc58fd68e829c` |

The brief reports that the R06 checkpoint records an accepted candidate that was not published because the exact evidence file exceeded the available connector transfer route; that the R06 archive is an online continuation package, not a complete offline repository backup; and that it references the separate C262 historical archive. The brief's audit verified the 131 entries of the outer manifest and the recorded identities of the nested archives and the evidence member. It did not rerun the candidate's inherited behavioural tests or extract its roughly 944 MB inner evidence archive.

### Traceability from the brief's requirement table

| Brief | Requirements here |
| --- | --- |
| MIG-01 | REQ-001 |
| MIG-02 | REQ-003, REQ-013 |
| MIG-03 | REQ-005, REQ-006, REQ-007, REQ-011 |
| MIG-04 | REQ-010 |
| MIG-05 | REQ-011, REQ-014 |
| MIG-06 | REQ-030, REQ-031, REQ-032 |
| MIG-07 | REQ-024, REQ-029 |
| MIG-08 | REQ-023 |
| MIG-09 | REQ-022 |
| MIG-10 | REQ-019, REQ-021 |
| MIG-11 | REQ-035 |
| MIG-12 | REQ-036 |
| MIG-13 | REQ-037 |
| MIG-14 | REQ-041 |
| MIG-15 | REQ-017 |
| MIG-16 | REQ-033, REQ-042 |
| MIG-17 | REQ-027 |
| MIG-18 | REQ-002 |

The remaining requirements carry the brief's detailed design sections (B§4 to B§13) and its acceptance checklist (B§14).

## In scope

One migration scope, delivered through the existing workflow, covering:

- Adopting the existing local clone as the normal workspace, from an observed inventory.
- A native CPython 3.12 virtual environment, dependency profiles, platform-specific verification locks, and the setup (bootstrap) and diagnosis (doctor) tools with their tests and documentation.
- One installed-package check outside the checkout.
- A prospective local execution mode across all active instruction surfaces, a local entry point and a thin Claude adapter, with the browser rules retained for browser sessions.
- Repository-based continuity: the continuation convention, the local startup procedure, session checkpoint contents, compact current pointers and the supporting workflow-tool changes.
- Reconciliation of main, the C271 branch, the R06 handoff and the local clone, and preservation of unique evidence and historical records.
- Parallel-work rules, attributable evidence, and storage and backup of unique material.
- Independent review, integration into main, verification of the resulting main, and cleanup of the migration's own branch and worktree.

Target arrangement (B§1, recommended):

| Concern | Home after the migration |
| --- | --- |
| Source editing and execution | The existing local Git clone, with dedicated worktrees for independent editing sessions |
| Shared source history and collaboration | GitHub, synchronized through ordinary authenticated Git |
| Python packages | A validated `.venv` belonging to the active checkout or worktree |
| Dependency specifications | Versioned manifests and platform-specific locks |
| Agent instructions | Shared `AGENTS.md`, a local entry document and a small Claude adapter |
| Current work and acceptance | The existing `docs/workflow/` records |
| Session continuity | Concise repository checkpoints tied to actual commits, evidence and one next action |
| Large evidence and legacy handoffs | Preserved artifacts with manifests, durable locations and verified backup |
| Optional Linux reproduction | A separate qualified Linux host or an explicitly identified container profile |

Components the brief names as affected (B§12; the names of new files are proposals, see D03): `AGENTS.md`, the root `README.md`, `STATUS.md`, `GOAL.md` (operating references only), `docs/workflow/` (`PROTOCOL.md`, `HANDOFF.md`, `README.md`, `registry.json`, `CURRENT.json`, `templates/SESSION.md` and task records), the OntoKin session and delivery skills, `OK-ENG-006`, `.gitignore`, `tools/chat_workflow.py` with its tests, the `tools/check_local.py` inventories, and new local-entry, adapter, setup-guide, tool, lock and interpreter-specification files.

## Out of scope

- Resuming or completing C271. Exact publication of the accepted P29 candidate and C271's remaining acceptance (H0, H1, required regression, integration, parent completion) form a separately selected follow-on scope. For that later scope the brief records (B§9.3): authenticated local Git is a different publication route from the connector that failed; the evidence file is below GitHub's documented 100 MiB regular-Git file limit, subject to checking repository rules, credentials and upload state; later branch history is preserved, and a new commit that reconciles later recovery records may legitimately have a different tree from the original accepted tree; successful publication resolves the transfer gate only.
- Linux container automation and any Docker configuration; a native Linux x86-64 executor; a native Windows profile. For a later container the brief records (B§4.6): pin the base-image digest, architecture, Python patch, dependency locks, Node version and browser preparation; keep evidence outside the disposable writable layer; put no credentials in images; do not mount a writable primary checkout for a read-only verification job.
- Any Git LFS migration, conversion, upload or retrieval acceptance under `OK-ENG-010`.
- Adopting uv or another package manager. If one is adopted later, the brief requires one documented dependency authority and a reviewed lock migration (B§4.5).
- Changing or upgrading any adopted dependency version.
- Native-tool qualification (Blender, Godot and similar), replay of native trial schedules, and any release acceptance or product qualification.
- Execution evidence for Python versions other than the selected development interpreter; each claimed version still needs its own execution.
- Any change to OntoKin language semantics, expectations, numerical limits or fixtures, or to GOAL's mission, invariants, budgets and completion boundaries; unrelated product features.
- Enabling hosted CI or paid execution.
- Rewriting or relabelling historical handoffs, receipts or failed observations; full offline restoration of historical archives.

The brief requires that these follow-on scopes "must not become indefinite prerequisites for basic local editing and verified core operation" (B§13).

## Task requirements

### REQ-001 — Adopt the existing clone from an observed inventory
- Requirement: The owner's existing local Git clone becomes the normal development workspace, and before the migration changes anything the actual machine and clone are inspected and recorded: clone root, origin, branch, head, working-tree state (tracked modifications, untracked files, unpublished commits), worktrees, operating system and architecture, Python and Node installations, application installations, local Git authentication, disk capacity, backup coverage and divergence from the remote.
- Source: B MIG-01 — "Use the existing local clone as the normal development workspace." (explicit request).
- Source: B§2.3 and B§13 Stage 0 — the brief did not inspect the physical computer; the local agent must inventory it and preserve what it finds.
- Acceptance: A concise host inventory in the migration's task record gives each listed item its observed value or an explicit "not observed", and identifies the clone, origin, branch, head and working-tree state.
- Acceptance: Setup decisions cite that inventory, not the brief's audit-time snapshot, this document's S observations or a previously mentioned machine.
- Acceptance: Every local modification, untracked file and unpublished commit found by the inventory is still present and unaltered afterwards; nothing unique was overwritten.
- Depends on: None.

### REQ-002 — One distinct migration scope in the existing task system
- Requirement: The migration is carried out as one selected, distinct scope created from current main and recorded in the existing workflow task system, with a new task ID that is observed to be available rather than guessed, its exact starting revision, and its own branch and separate worktree.
- Source: B MIG-18 — "This brief is converted into one selected migration scope with reviewable changes and recorded acceptance." (explicit request).
- Source: B§9.2 step 2 and B§13 — a separate migration worktree from current main; one selected migration scope (recommended).
- Source: P PROTOCOL §3 — task records under `docs/workflow/tasks/` precede substantial implementation.
- Acceptance: One migration task record exists with requirements, plan, status, starting revision and recorded acceptance, and its changes are reviewable.
- Acceptance: The migration's commits are on its own branch from current main; the C271 branch is neither its working branch nor modified by it.
- Depends on: REQ-001

### REQ-003 — Native CPython 3.12 virtual environment as the default
- Requirement: Ordinary development uses a native, non-container environment: an ignored `.venv` in the active checkout or editing worktree, created with Python's built-in `venv` from CPython 3.12, whose exact patch version is selected from what the host inventory finds, verified, and committed in one tracked environment specification.
- Source: B MIG-02 — "Create or validate an isolated Python environment for this project." (explicit request).
- Source: B§1 and B§4.1 — CPython 3.12 family, exact patch chosen and recorded at machine setup, `.venv` per checkout or worktree (recommended).
- Acceptance: The selected interpreter's exact version, distribution or source, and platform are recorded, and the tracked specification names that exact patch.
- Acceptance: Project commands run through the environment's own interpreter (`.venv/bin/python` on macOS and Linux) without relying on shell activation or on whichever `python3` is first on `PATH`.
- Acceptance: No global or system Python installation is used as a writable project package environment.
- Acceptance: `pyproject.toml` still declares `requires-python >=3.11`, and no Python version is claimed as tested unless it was actually executed.
- Depends on: REQ-001

### REQ-004 — Environments are reused, never silently rebuilt or copied
- Requirement: An existing valid environment is reused; an environment is rebuilt only when its interpreter, location, package state or selected profile is incompatible, and that incompatibility is reported before any rebuild; environments, caches and dependency directories stay out of Git and out of handoff archives and are recreated from specifications rather than copied between locations.
- Source: B§4.1 — environment conventions (recommended).
- Source: B§10.1 and B§11.1 — `.worktreeinclude` is not an environment installer; environments are ignored and recreated (recommended).
- Acceptance: With a healthy environment present, setup rebuilds nothing; with an incompatible one, the incompatibility is reported and no rebuild happens without an explicit request.
- Acceptance: No environment, cache or dependency directory is tracked by Git, and no `.venv` is copied into a worktree by `.worktreeinclude` or any other means.
- Depends on: REQ-003

### REQ-005 — Dependency profiles with separately reported readiness
- Requirement: Setup is organized into named profiles, each a selection of tools and acceptance checks rather than a new product or task tracker: `core` (selected CPython, standard library, Git, optional editable install); `python-verification` (core plus the six Agent verification pins and Pillow under a lock valid for the platform); `visual-verification` (python-verification plus Node and npm, the committed npm dependencies and matching Chromium); `package-smoke` (a clean build environment and a separate clean installation environment); historical or native profiles (the exact interpreter, application, binary, importer and input bindings that their own contracts require); and an optional Linux container profile.
- Source: B§4.2 — dependency profiles (recommended).
- Source: B MIG-03 — "Determine which dependencies are missing or incompatible and install the required ones." (explicit request); its acceptance is "Profile-specific inventory, installation record, package checks, and meaningful smoke results."
- Acceptance: Each profile's contents and the checks that establish its readiness are documented, and a profile-specific inventory of missing or incompatible dependencies is recorded.
- Acceptance: Readiness is reported separately for each profile, and a core-only setup is never described as ready for the complete test suite.
- Depends on: REQ-003

### REQ-006 — Platform-specific verification locks
- Requirement: Verification packages are installed only from a lock valid for the host platform: the existing Linux CPython 3.12 x86-64 lock stays unchanged and is used only on a matching platform, and a separately named macOS arm64 lock is added for the same required versions, recording wheel filenames, platform tags, source locations, byte sizes and SHA-256 hashes, and is selected explicitly.
- Source: B§4.3 — macOS arm64 steps 1 to 5 (recommended); B§2.1 — the existing lock's wheel hashes cannot be treated as a Mac arm64 or Windows lock (observed).
- Source: S01 — the capturing machine is macOS arm64.
- Acceptance: On an incompatible platform the Linux lock is refused before anything is installed, and hash enforcement (`--require-hashes`) is never removed to make a lock install elsewhere.
- Acceptance: `tools/native-reader-verification-linux-cp312.lock` is byte-identical before and after the migration.
- Acceptance: The macOS arm64 lock exists under its own name with the recorded identities and is reviewed before use; binary wheels are used where the profile requires them, and any source compilation is a distinct, recorded preparation path with its own compiler and build dependencies.
- Depends on: REQ-005

### REQ-007 — python-verification readiness from the adopted exact versions
- Requirement: The normal development environment reaches `python-verification` readiness with exactly the repository's adopted verification versions (jsonschema 4.26.0, referencing 0.37.0, attrs 26.1.0, jsonschema-specifications 2025.9.1, rpds-py 2026.5.1, typing_extensions 4.16.0 and Pillow 13.0.0) wherever compatible distributions exist for the host platform.
- Source: B§4.2 and B§4.3 — the normal environment should reach python-verification readiness; the versions are observed repository requirements, "not suggestions to upgrade".
- Source: B MIG-03 — install the required dependencies (explicit request).
- Acceptance: Installed versions equal the adopted versions; package-consistency (`pip check`) and import and version checks pass, including the existing native-reader setup preflight; and an installation record is kept.
- Acceptance: No pin is replaced by "latest" or any other version; where an exact compatible distribution is unavailable, the exact package, version and platform are reported, the profile is not reported ready, and a source build or dependency change happens only as a reviewed and separately adopted decision.
- Depends on: REQ-006

### REQ-008 — Visual verification prepared only when selected, on the documented toolchain
- Requirement: Node, npm and Chromium are prepared only when the `visual-verification` profile is selected (exporter or viewer work, or `--full` checks); when it is selected, the documented target is Node.js 22, the committed npm versions are kept (esbuild 0.25.10, gltf-validator 2.0.0-dev.3.10, Playwright 1.56.1, Three.js 0.180.0), dependencies are installed from `tools/package-lock.json` with `npm ci`, and the matching Playwright Chromium headless shell is prepared as a step separate from Python package installation.
- Source: B§4.4, B§5.1 item 6 and B§6.3 — Node, browser and native applications (recommended); P `OK-ENG-006` §3.
- Source: S06 — the capturing machine has Node v25.9.0 and no Node.js 22.
- Acceptance: When the profile is not selected, nothing is installed for it and its state is reported as it actually is, never as ready.
- Acceptance: When it is selected, the actual Node and npm versions are recorded and compared with the Node.js 22 target; the checker's broader minimum-version acceptance is not treated as the toolchain pin.
- Acceptance: Because `npm ci` replaces an existing `node_modules` directory, it is used only for initial preparation or deliberate repair, and only when no validator or other agent is using that directory; a healthy repeat run verifies installed identities and skips it.
- Acceptance: Routine macOS instructions do not carry the Linux `--with-deps` option; Linux system-library preparation is a separate step.
- Depends on: REQ-005

### REQ-009 — Nothing is added beyond the adopted specifications
- Requirement: The migration keeps Python's built-in `venv`, pip and the repository's existing requirements and lock conventions, and adds nothing that the adopted specifications do not require: no new package manager (uv is not adopted), database service, always-running container or replacement test framework; no NumPy, PyTorch, TensorFlow, CUDA, Conda or Blender Python package in the default environment; no root `requirements.txt` made by freezing installed packages; and no consolidation or upgrade of unrelated experimental pins.
- Source: B§1 and B§4.5 — "Retain venv plus pip for the first migration." (recommended); B§4.4 — the runtime metadata gives no basis for ML or Blender packages.
- Source: S12 — `dependencies = []`.
- Acceptance: The default environment's installed packages are those of the selected profile's specification plus the tools needed to install them, and runtime, build, verification and optional-tool requirements remain separate.
- Acceptance: No `uv.lock` or other package-manager authority is added, and no setup or verification instruction depends on uv, Conda or another manager.
- Acceptance: Blender, Godot, graphics drivers and other native applications are prepared only under the profile of a task that selects them; general setup replays no consumed native trial schedule and never describes an installed application as a qualified destination.
- Acceptance: A historical profile that binds an exact interpreter (for example Linux x86-64 CPython 3.12.14) is reproduced only in its own separate environment; a newer interpreter is never substituted while reusing the old qualification, and new development is not forced into the historical environment.
- Depends on: REQ-005

### REQ-010 — Definite container decision: native by default
- Requirement: The native environment is the default for all ordinary editing and for the tests the host supports; Docker is not required before work can start; this migration adds no Docker configuration, Docker Compose or Kubernetes; and any later Linux or container profile must state its purpose and carry its own separate acceptance.
- Source: B MIG-04 — "Make a definite container decision." (explicit request); its acceptance is "Native environment is the default; any Linux/container profile has a stated purpose and separate acceptance."
- Source: B§4.6 — the brief's decision table and reasons (recommended); S07 — Docker is not installed on the capturing machine.
- Acceptance: The setup documentation states this decision and its reasons, and every acceptance check of this migration is passed or reported without a container.
- Acceptance: An emulated amd64 container on an Apple silicon Mac is never counted as native Linux qualification; architecture, emulation, kernel, graphics and timing stay explicit in any Linux evidence.
- Depends on: None.

### REQ-011 — Idempotent, profile-specific bootstrap
- Requirement: A setup tool (proposed path `tools/bootstrap_local.py`) prepares the selected profile: it resolves the intended repository or worktree and the selected interpreter; inspects OS, architecture, Python patch and distribution, the existing environment and relevant package and tool versions; selects a compatible committed profile; creates the environment only when absent; installs only missing or mismatched packages from the selected reviewed inputs; prepares Node and Chromium only for the visual profile; records installation provenance, selected lock identities, tool versions, changes made and failures; runs package-consistency, import and version, and appropriate smoke checks; and reports readiness by profile with the exact next unmet setup action.
- Source: B§5.1 — required bootstrap behaviour (recommended); B§5.3 — command interface design target.
- Source: B MIG-05 — "Make setup repeatable on a fresh machine or worktree." (necessary implication); its acceptance includes "A second setup run is idempotent".
- Acceptance: A second run against an unchanged healthy environment replaces no dependency, upgrades no package and regenerates no lock.
- Acceptance: A missing interpreter is distinguished from missing packages; when the required interpreter family is absent, the machine's existing trusted installation mechanism is used where available and the result recorded, and an environment built on a different interpreter is never labelled compliant.
- Acceptance: Concurrent installers cannot mutate the same environment, and a dependency directory is not replaced while another process is using it.
- Acceptance: The tool offers a preview that changes nothing, an explicit interpreter option, an explicit repository or worktree option where needed, and a new-output report location.
- Acceptance: The tool does not replace `tools/check_local.py`, change project behaviour, start native qualification experiments or publish source.
- Acceptance: Meaningful tests cover compatible-platform selection, incompatible-lock refusal, idempotence and wrong-interpreter diagnosis, and their execution against the migration candidate is recorded.
- Depends on: REQ-005, REQ-006

### REQ-012 — Non-mutating doctor
- Requirement: A diagnosis tool (proposed path `tools/doctor_local.py`) inspects readiness without installing, updating, fetching dependencies, modifying locks, changing source or launching native product trials, and reports in human-readable and JSON form on: the checkout (root, worktree, branch, local head and tree, tracked modifications, relevant untracked files); Python (actual executable, implementation, exact version, OS and architecture, environment isolation); packages (expected versus installed versions, import results, `pip check` outcome); the specification (selected profile and hashes of the manifests and locks used); visual tools (Node and npm, installed npm dependency identities, Playwright and browser availability); storage (selected LFS files, required client version, hydration state when applicable); the workflow (entry point, selected task, latest checkpoint, workflow structure check); and readiness for each profile.
- Source: B§5.2 — doctor behaviour and required observations (recommended); B§5.3 — command interface design target.
- Acceptance: Each profile's readiness is exactly one of `ready`, `missing`, `mismatch`, `unsupported` or `not_checked`; a package with the right name but the wrong version is a `mismatch`; an unexecuted check is never reported as a pass.
- Acceptance: Running the doctor leaves dependencies, locks and source unchanged; it writes a report only when one is explicitly requested.
- Acceptance: Ordinary diagnosis neither fetches nor publishes; remote status is observed only in an explicit online mode.
- Acceptance: General tool readiness is reported separately from native experiment acceptance, and diagnosis does not itself require the environment it diagnoses (the brief prefers a small standard-library implementation).
- Depends on: REQ-005

### REQ-013 — Reproducibility records for every environment
- Requirement: Reproducibility information is kept by kind: the interpreter and profile specification and portable dependency information are committed; machine-specific executable paths and local configuration live in ignored local files or identified reports; and each environment has a record of its exact interpreter, distribution or source, platform, installation-tool versions, build-tool versions, package versions, lock hashes and any browser or application versions.
- Source: B§5.4 — reproducibility records (recommended); B§2.1 — `setuptools>=77` is a lower bound, not an exact build lock (observed).
- Source: B MIG-02 — its acceptance is "Selected interpreter and environment are recorded; project commands use that interpreter."
- Acceptance: From the committed specifications plus the environment record, a reader can tell what was installed, from which inputs and with which tools, including the build tools actually used.
- Acceptance: Ignore rules change only where needed: the adopted interpreter specification is tracked (the existing `.python-version` ignore rule is removed only if that file is the adopted form), while environments, local configuration, worktrees and outputs stay ignored.
- Acceptance: Working evidence is written to a persistent local evidence directory or the runner's `build/local-checks/` location, and before the task closes the required summary and durable evidence references are preserved in the task record.
- Depends on: REQ-003

### REQ-014 — Setup is repeatable and documented
- Requirement: A fresh machine or fresh worktree can recreate the environment from the committed specifications, and a human-readable local setup guide (proposed `docs/development/LOCAL-SETUP.md`) gives setup, profiles, troubleshooting and exact commands.
- Source: B MIG-05 — its acceptance includes "a fresh environment can be recreated from committed specifications" (necessary implication).
- Source: B§12 — setup guide (recommended); B§4.1 — the existing policy's temporary external verification-environment example should be updated for persistent local operation.
- Acceptance: A fresh environment created from the committed specifications, in a location with no prior environment, reaches the same reported readiness as the original.
- Acceptance: The guide matches the tools' actual behaviour, and the existing policy's temporary external verification-environment example is updated for persistent local operation.
- Depends on: REQ-011, REQ-012

### REQ-015 — Installed-package behaviour proven outside the checkout
- Requirement: The migration performs one meaningful installed-package check: a wheel is built from an identified source revision in a recorded build environment, that emitted wheel is installed into a separate clean environment, and the installed `ontokin` entry point and one representative source operation given an absolute input path are run from a directory outside the checkout with source-path injection removed from the process environment.
- Source: B§6.5 — installed-package verification (recommended); B§4.1 — a separate clean environment for this check.
- Source: S12 — the package uses an installed facade, a payload and selected package data, which running from the repository root can mask.
- Acceptance: The record gives the source revision, build environment, wheel identity and imported module locations, which lie in the clean environment and not the checkout, and shows that the packaged resources are available.
- Acceptance: Installed-package correctness is not inferred from an editable install; a wheel-build failure is recorded and diagnosed as a separately visible packaging fix.
- Depends on: REQ-003

### REQ-016 — Explicit local and browser execution modes, adopted prospectively
- Requirement: Active operating instructions gain an explicit local execution mode beside the existing browser mode; the mode is selected explicitly rather than inferred from a path or an agent name; the change is recorded as a dated, prospective owner-direction decision; and `CHATGPT-START-HERE.md`, `docs/workflow/EPHEMERAL-HOST.md` and the browser rules stay in force for browser sessions.
- Source: B§7.1 — "Make the policy change prospective"; route by an explicit local or browser execution mode (recommended).
- Source: B§12 — a dated migration decision beside `OK-ENG-006` (recommended); P PROTOCOL §8 — the saved-ZIP rule applies "unless owner changes requirement".
- Acceptance: A dated decision record states the owner's local-development direction and that it applies prospectively.
- Acceptance: Old handoffs, receipts, failed observations and their original interpretation are unchanged.
- Acceptance: A browser session is still routed to the retained browser entry point and ephemeral-host rule, and a local session to the local entry point; neither is chosen by guessing.
- Depends on: REQ-002

### REQ-017 — Local-mode rules replace the browser-only rules for local sessions
- Requirement: In local mode: a checkout may persist, so its actual state is inspected and validated resources are reused; only missing or incompatible inputs are reconstructed; before substantial work a recoverable Git and checkpoint state is established and unique uncommitted inputs are preserved, in place of an early recovery ZIP; a session or scope closes on a source checkpoint, a truthful task and session record, verified push state when online, and durable evidence, with ZIP export optional unless the selected task explicitly requires one; work stops at the selected scope's acceptance point, at a concrete blocker, or at a session boundary after recording recovery state; tests run on the explicitly selected local or dedicated verification executor; and the normal continuation input is the local entry instructions plus repository task pointers rather than a Library link.
- Source: B§7.1 — table of existing browser rules and recommended local rules.
- Source: B MIG-15 — "Avoid requiring a new ZIP and Library transfer after every ordinary local session." (necessary workflow change).
- Acceptance: A local session closes with durable Git, checkpoint and evidence state while ChatGPT Library is unavailable, and no local-mode instruction makes a new Library ZIP a closing condition for an ordinary local session.
- Acceptance: A persistent local session may continue through the selected task's planned steps without a new conversation after each one, while a new unrelated scope still requires explicit selection through the established workflow.
- Depends on: REQ-016

### REQ-018 — The amendment is coherent across every instruction surface
- Requirement: The local-mode amendment is made together across every active surface: `AGENTS.md`, the registry and its required read sets, `docs/workflow/PROTOCOL.md`, `HANDOFF.md` and the workflow `README.md`, the OntoKin session and delivery skills, completion logic, `OK-ENG-006`, `STATUS.md` and the root `README.md` (local entry point as the normal front door, with a clear link to the browser workflow), while `GOAL.md` changes only in its affected operating references.
- Source: B§7.1 — "Changing only `AGENTS.md` would leave conflicting instructions elsewhere."; B§12 — file-level change map (recommended).
- Source: S11 — the current rule text that conflicts with local operation.
- Acceptance: No active instruction simultaneously directs a local agent to use the persistent workstation and to avoid the user's computer or rebuild an ephemeral host; the AGENTS and STATUS wording that confines checks to the assistant's hosted workspace is reconciled for local mode.
- Acceptance: GOAL's mission, semantics, invariants, budgets and completion boundaries are unchanged, and no language semantics change.
- Acceptance: The existing documentation and navigation check and the workflow-record check pass for the amended files.
- Depends on: REQ-016, REQ-017

### REQ-019 — One shared instruction authority, a local entry point and a thin Claude adapter
- Requirement: `AGENTS.md` remains the single shared project instruction source; a short local entry document (proposed `LOCAL-START-HERE.md`) covers local startup, environment readiness, state recovery and continuation; and a root `CLAUDE.md` is a thin adapter that imports `AGENTS.md` and adds only Claude-specific behaviour.
- Source: B§7.2 — "Keep one instruction authority" (recommended); S08 — neither file exists yet.
- Source: B MIG-10 — its acceptance is that Claude Desktop's Code tab can open the local project and run the documented workflow.
- Acceptance: `CLAUDE.md` imports `AGENTS.md` and contains no duplicated or competing project rule.
- Acceptance: In the installed application the shared instructions and the adapter are observed to have actually loaded; a filename existing is not accepted as that evidence.
- Depends on: REQ-018

### REQ-020 — Skills stay shared, linked and explicitly invoked
- Requirement: The six existing `.claude/skills/` links to the canonical `.agents/skills/` content are preserved as completed work; the OntoKin session and delivery skills are amended for local mode in their canonical location rather than copied into competing versions; and the `to-trd` and `to-implementation-plan` skills remain explicit-invocation only.
- Source: B§7.2 and B§2.1 — preserve the six links; update the session and delivery skill content (recommended).
- Source: P PROTOCOL §3 — ordinary records invoke neither named skill; named skills need explicit invocation.
- Acceptance: All six links resolve in the local clone, and the installed agent is observed to discover the six skills.
- Acceptance: Exactly one version of each skill exists, and the migration's ordinary task records invoke neither named planning skill.
- Depends on: REQ-018

### REQ-021 — The owner's graphical workflow works end to end
- Requirement: The owner can run the documented local workflow from Claude Desktop's Code tab, using the local environment and the correct project folder, without operating a terminal as the primary interface.
- Source: B MIG-10 — "Support the user's graphical coding-agent workflow." (established preference).
- Source: B§7.3 — configure the graphical agent deliberately (recommended).
- Acceptance: The Code tab opens the local project and the documented workflow runs there, with the agent executing the setup and test commands.
- Acceptance: The Code tab's own version is checked rather than assumed equal to a terminal installation; Worktree mode is enabled deliberately before parallel editing and the actual checkout path and branch are then verified; needed worktree files are committed or otherwise preserved before a session is archived.
- Depends on: REQ-019

### REQ-022 — One canonical task and acceptance system
- Requirement: The existing records keep their roles and remain the only owners of current status: `GOAL.md` (purpose, invariants, priorities, scope boundaries); `STATUS.md` (concise project status, important unresolved work, integration ownership); `docs/workflow/CURRENT.json` (small machine-readable pointer to the selected task and latest checkpoint); each task's `task.json` (canonical status and acceptance), `REQUIREMENTS.md` and `PLAN.md`; the session record based on `templates/SESSION.md`; knowledge and memory records (source-backed, subordinate to current source and task state); and Git history, PRs, issues and evidence manifests (provenance, review, published state).
- Source: B MIG-09 — "Keep project status, requirements, plans, and handoff information consistent." (explicit request).
- Source: B§8.1 — reuse the existing task system (recommended); P PROTOCOL §3 — "no competing ledgers".
- Acceptance: No independent `TODO.md`, personal plan, agent memory or database owns current status; agent transcripts and automatic memory are optional convenience only.
- Acceptance: Task pointers and statuses validate with the existing workflow structure check.
- Depends on: None.

### REQ-023 — "Go" or "Continue" resumes the selected scope
- Requirement: The local workflow documents this convention: "Go" or "Continue" means read the local entry instructions and current task records, reconcile actual local and remote state, and perform the next unmet step of the selected authorized scope, preserving evidence, reporting meaningful progress and checkpointing at completion or at a concrete blocker.
- Source: B MIG-08 — "Preserve goal-directed 'Go/Continue' operation." (interpreted intent: the brief reads the owner's "Go" wording as a short instruction for goal-directed continuation).
- Source: B§8.2 — the recommended local convention and its limits.
- Acceptance: Given the instruction, an agent resumes the selected task's next unmet gate from repository records and does not restart work already recorded and verified as complete.
- Acceptance: The instruction never selects a new product milestone merely because another task is blocked, never treats an old handoff's stop condition as a permanent prohibition on newly authorized local migration, and never treats environment setup as permission to rerun restricted native experiments.
- Acceptance: The convention depends on no ChatGPT Goals feature, scheduled Task or agent-private memory; a separate Goals interface, if the owner uses one, points at the same repository task state.
- Depends on: REQ-022

### REQ-024 — Local session startup procedure
- Requirement: The local entry document directs a starting agent to: identify the repository, working directory, branch or worktree, head, dirty changes, untracked work and any active agent ownership; read the shared instructions, `GOAL.md`, the concise `STATUS.md`, the registry, `CURRENT.json`, the selected task's requirements, plan and status, and its latest session checkpoint; load affected specifications and applicable skills, reading historical evidence only when the selected gate requires it; check actual remote state when online, distinguishing the local head, remote-tracking refs and an independently observed remote head, and preserving local changes before updating anything; run the lightweight doctor and the workflow structure check and reuse a valid environment; state one bounded objective with its acceptance checks and stopping condition; and continue from the first unmet step.
- Source: B MIG-07 — "Let a fresh agent resume without relying on the previous chat." (explicit request).
- Source: B§8.3 — local session startup (recommended); B§6.4 — startup diagnosis is lightweight; B§9.2 — historical archives are not an everyday startup prerequisite.
- Acceptance: The entry document contains these steps, and a session following them reports each item before starting work.
- Acceptance: When offline, local work may continue within scope, remote state is labelled stale, and push, merge and deletion are reported as unconfirmed.
- Acceptance: No costly full suite runs at every session start, and no historical archive download is a required startup step; the verified identities and locations of the R06 handoff and the C262 archive stay recorded and the archives are materialized only when selected work requires them.
- Depends on: REQ-012, REQ-019

### REQ-025 — Work conduct, blockers and interruption recovery
- Requirement: During local work, checkpoints are small and meaningful, task status stays aligned with actual acceptance, a concrete blocker is recorded once and investigated within the selected scope without repeated capability-only phases, and after an interruption the actual working tree, processes, refs and destination state are inspected before any operation is retried.
- Source: B§8.4 — conduct during work; B§11.3 — interruption recovery; B§6.4 — preserve baseline failures (all recommended).
- Acceptance: A checkpoint is enough for another agent to continue and is not a transcript of the conversation.
- Acceptance: Recovery proceeds from existing commits and checkpoint records; implementation is not restarted when only a push, review or delivery step remains.
- Acceptance: Changed-scope checks run at meaningful implementation checkpoints and the required integration checks afterwards; baseline failures are preserved rather than answered by repeated reinstallation or broader tests without a new diagnostic reason.
- Depends on: REQ-017

### REQ-026 — Session checkpoints carry what a successor needs
- Requirement: The existing session template is extended, not replaced by an incompatible record, to carry: identity (task, session, agent or tool identity, execution mode, timestamps, worktree and branch); source (starting revision, current code checkpoint, dirty and untracked state, actual remote observation); work (completed acceptance items, changed files, decisions, remaining items); environment (profile, interpreter, OS and architecture, manifest identities, relevant tool versions); verification (commands, results, failures, pending and not-run checks, evidence locations and hashes); recovery (unpublished commits, unique uncommitted files, outstanding operations, owned processes); coordination (active workers, reserved files, integration ownership, lease status); continuation (one next action and the condition that makes it safe and useful to execute); and delivery (local checkpoint status, verified push state, merge and branch disposition, durable evidence references).
- Source: B§8.5 — session checkpoint contents (recommended); P `docs/workflow/templates/SESSION.md` — the existing template.
- Acceptance: The template carries all nine field groups, and existing session records remain valid under it.
- Acceptance: No self-referential "receipt of the receipt" cycle is created: the code checkpoint and its evidence are recorded, the later checkpoint commit is found through Git, and later push observations may be kept as a separate small record without rebuilding frozen evidence.
- Depends on: REQ-022

### REQ-027 — Compact current pointers, complete history
- Requirement: Current startup records are compact projections with explicit provenance, while every historical record stays unchanged and reachable: the exact original versions of large records (such as the C271 branch's `CURRENT.json` and `task.json`) are preserved through Git and immutable archive references, historical receipts and logs are referenced files loaded on demand, and no evidence is deleted to meet a size target.
- Source: B MIG-17 — "Preserve provenance while reducing repeated startup material." (necessary implication of project growth).
- Source: B§8.6 — reduce startup size without discarding history (recommended); S03 — the C271 branch records are 192,376 and 418,591 bytes.
- Acceptance: `CURRENT.json` holds the current selection and checkpoint pointers rather than embedded receipts, and links to the retained history.
- Acceptance: The earlier content of every compacted record is retrievable unchanged from the recorded references.
- Acceptance: If a record schema changes, it is versioned, the workflow checker and its tests are updated, the old-to-new field mapping is documented, and the earlier schema's interpretation is preserved.
- Depends on: REQ-022

### REQ-028 — Workflow and validation tools follow the adopted structure
- Requirement: Existing tools change only as the adopted workflow requires: `tools/chat_workflow.py` and its focused tests validate any new mode or pointer structure; a new task never silently inherits a stale recorded `CURRENT.observed_main`, because the actual base is refreshed or explicitly supplied; and the explicit root-file and source-directory inventories of `tools/check_local.py` are reviewed and deliberately amended so that adopted setup inputs and new root instruction files have appropriate provenance coverage.
- Source: B§8.1 and B§12 — fresh-base handling and tool amendments (recommended); B§2.1 — the checker's inventories are explicit (observed).
- Source: S04 and S12 — `observed_main` on main is already older than the actual head, and `new-task` uses it as the base.
- Acceptance: A task created after main has moved records the actual base revision.
- Acceptance: The focused workflow-tool tests pass, and the inventory review modifies no historical evidence hash.
- Depends on: REQ-018

### REQ-029 — A fresh agent session resumes from the repository alone
- Requirement: After one agent session closes with a meaningful checkpoint, a fresh session started against the same repository identifies the selected task, the environment, the completed work and last completed gate, the next action and the blockers, without the previous conversation and without a required Library download.
- Source: B MIG-07 — its acceptance is "A new session can identify the selected task, completed work, next action, and blockers from repository records."
- Source: B§13 Stage 4 — prove continuation and recovery (recommended).
- Acceptance: The demonstration is performed and recorded, and the fresh session's account matches the repository records.
- Acceptance: Concise user instructions for starting, continuing, recovering and checkpointing a local session are delivered.
- Depends on: REQ-023, REQ-024, REQ-026

### REQ-030 — Main, C271, the R06 handoff and the local clone are reconciled
- Requirement: Before the next development task is chosen, the migration reconciles current main, the retained C271 branch, the R06 transfer-capability handoff with its matching delivery receipt, and the local clone, and records what is already in Git, what is unique to the handoff, which branch owns it and which acceptance gates remain open; the main workflow records then carry a concise reference to unfinished C271 without merging its incomplete implementation.
- Source: B MIG-06 — "Preserve unfinished work and unique files from the old handoff process." (necessary implication); its acceptance is "C271 and the R06 recovery chain are reconciled; unique accepted bytes remain recoverable."
- Source: B§2.2 — "A clean clone of main alone does not contain all unfinished work."; B§9.2 — recommended cutover sequence.
- Source: S03 and S09 — the exact evidence blob is not in the local object store, and the R06 handoff was not found in the Downloads folder at capture.
- Acceptance: A reconciliation record states those four findings, and main's workflow records reference C271's open state.
- Acceptance: Live state is re-read before acting, and the recorded identities are treated as audit-time observations, not as instructions to reset a newer branch.
- Acceptance: The R06 handoff and its receipt are on the local machine before reconciliation is claimed; a local agent is not assumed to have access to ChatGPT Library.
- Acceptance: If required legacy bytes are unavailable, the precise missing file is recorded and this requirement stays open, while safe inventory and environment setup in the isolated migration worktree continue and no capability-only loop results.
- Depends on: REQ-001, REQ-002, REQ-031

### REQ-031 — Legacy archives are verified before use and never overlaid
- Requirement: Before anything is imported from a legacy handoff, its outer archive identity, its manifest, its nested recovery identities and its accepted payload inventory are checked against the recorded identities; only needed data is extracted, into a new staging location; and no archive is overlaid on the current clone.
- Source: B§9.2 steps 3 and 4 — verify before importing (recommended); B§9.1 — the identities to verify against.
- Acceptance: The verification results are recorded before any extraction, using the identities listed under Context and sources.
- Acceptance: The clone's working tree receives no wholesale archive extraction, and overlapping records (`CURRENT.json`, the C271 `task.json`, `REQUIREMENTS.md` and `PLAN.md`) are reconciled by meaning rather than overwritten with old snapshots.
- Depends on: REQ-001

### REQ-032 — Unique accepted evidence and historical records are preserved exactly
- Requirement: Unique accepted bytes and historical records stay unchanged and recoverable: old handoff ZIPs and receipts are preserved unchanged; the exact unpublished C271 evidence archive keeps its raw bytes and its recorded Git blob identity; and for that file there is no conversion to an LFS pointer, recompression, splitting or substitution of a different artifact.
- Source: B MIG-06 — its acceptance includes "unique accepted bytes remain recoverable".
- Source: B§9.3 and B§11.1 — preserve the accepted raw evidence bytes and the old handoffs unchanged (recommended).
- Acceptance: Wherever the evidence archive is held, its size, SHA-256 and Git blob identity equal the values listed under Context and sources; where it is only referenced, its identity and durable location are recorded.
- Acceptance: The migration rewrites, force-moves or deletes no C271 branch history.
- Depends on: REQ-031

### REQ-033 — C271 stays a separate, visibly unfinished scope
- Requirement: The migration does not merge, close, complete or delete C271: its publication (transfer) gate, H0, H1, required regression, integration and parent completion remain separately tracked and visible, and no unfulfilled historical ZIP or release gate is relabelled as passed because future local sessions use a different delivery mechanism.
- Source: B§7.1 — historical C271 delivery requirements require explicit reconciliation; B§10.2 — "C271 is not eligible for deletion merely because the migration finishes."
- Source: B MIG-16 — a successful install is not reported as C271 completion (necessary correctness condition).
- Acceptance: The migration performs no merge, closure or deletion of the C271 branch, PR #274 or issue #273, and the workflow records show C271's unmet gates.
- Acceptance: C271's own delivery requirements are reconciled explicitly when that scope is next selected, not implicitly by this migration.
- Depends on: REQ-030

### REQ-034 — Ordinary local Git is the publication route
- Requirement: Once local Git authentication is verified, ordinary authenticated local Git is the normal source-publication mechanism, so that dependency installation and large source publication no longer depend on encoding files through browser-chat requests, while GitHub connectors remain usable for review and metadata.
- Source: B§10 — Git, parallel agents and branch lifecycle (recommended); B§1 — shared history "synchronized through ordinary authenticated Git".
- Acceptance: Authentication is verified by observation before publication is relied on.
- Acceptance: No step of the local workflow requires transferring source or evidence through a browser-chat request.
- Depends on: REQ-001

### REQ-035 — Safe parallel work
- Requirement: Independent writers work in explicit worktrees and branches with owned files: each editing worktree has its own environment binding and independently writable dependency installation (package-download caches may be shared only where the package tool supports that safely); independent agents never concurrently modify the same index or install into the same environment; one integrator owns shared `STATUS`, `CURRENT`, acceptance and integration updates; workers own explicitly assigned paths and return results and commit identities to the integrator; and the existing ownership and lease discipline governs shared publication.
- Source: B MIG-11 — "Support safe parallel work." (existing project practice); its acceptance is "Independent writers use explicit worktrees/branches and owned files; shared state publication is serialized."
- Source: B§10.1 — worktrees and concurrent writers (recommended); P PROTOCOL §4 and §7.
- Acceptance: A second worktree's environment binding is tested: setup and check commands run there act on that worktree and its environment, not on the main checkout, and the evidence is preserved before cleanup.
- Acceptance: Parallel worktrees share no writable environment and do not overwrite each other's state.
- Acceptance: Isolation is never assumed from a separate conversation; worktree location, branch, source base and dependency readiness are inspected at startup; lease expiry alone is not taken as proof that an earlier writer stopped.
- Acceptance: No automatic setup or check hook is added until it is verified to act on the actual worktree path supplied in its input.
- Depends on: REQ-011, REQ-012

### REQ-036 — Evidence is attributable to the actual source and environment
- Requirement: Every test and evidence report identifies its source revision, platform, interpreter, dependencies, commands, outputs, failures and limitations, and validation continues to run through the existing `tools/check_local.py` driver, which setup and diagnosis surround but do not replace with a second validation system.
- Source: B MIG-12 — "Keep tests and evidence attributable to the actual source and environment." (existing project contract).
- Source: B§2.1 and B§6.4 — reuse the existing runner; checks selected by scope (recommended); P PROTOCOL §5 and `OK-ENG-006` §4.
- Acceptance: The migration's reports separate passed, failed, pending and not-run items, and pending external gates reported by the driver remain pending.
- Acceptance: The checks required for the actually changed scope under the AGENTS check table are run against the actual candidate in the selected environment and recorded.
- Acceptance: The driver's `--timeout` is used as a per-command limit and its output directory is new or empty and under `build/` or outside the checkout; local instructions do not depend on the non-portable outer `timeout 7200` shell example.
- Acceptance: Existing product failures are preserved with a clear next action, and no expectation is changed to make a check pass.
- Depends on: REQ-007

### REQ-037 — The no-payment hosted-CI policy is preserved
- Requirement: Local checks remain the default validation route, and the migration introduces no automatic hosted job, no paid execution and no requirement to wait for hosted CI.
- Source: B MIG-13 — "Preserve the existing no-payment policy for hosted CI." (existing owner direction).
- Source: P `OK-ENG-006` §6 and AGENTS — hosted workflows are manual-only with a default-false opt-in; S12 confirms that is the current state.
- Acceptance: No workflow definition gains a push, pull-request or scheduled trigger, and hosted workflows remain manual-only with the opt-in defaulting to false.
- Depends on: None.

### REQ-038 — Durable storage and backup of unique material
- Requirement: Material is stored by kind: source, instructions, manifests and small task records are committed; environments, `node_modules`, caches and reproducible temporary builds are ignored and recreated; test working outputs go to a new run directory carrying source and environment identities; required durable evidence keeps its exact bytes, a manifest and a durable retrieval location; machine-specific paths and credentials stay in local configuration or a credential store; and unique untracked work and external evidence are covered by an existing durable backup mechanism whose location is recorded.
- Source: B§11.1 and B§11.3 — evidence storage, backup and interruption recovery (recommended); B§1 — large evidence and legacy handoffs need "durable locations, and verified backup".
- Acceptance: One representative unique artifact is restored from its durable backup and its identity verified.
- Acceptance: An ignored directory on one disk is not counted as a backup, a Git bundle is not counted as covering untracked files or LFS payloads, and a copied environment is not counted as an environment-recreation specification.
- Acceptance: Growing chains of recursively nested handoffs are not moved into the repository as the normal local-session format; small current pointers and immutable referenced evidence are used instead.
- Depends on: REQ-001

### REQ-039 — Git LFS is left as it is
- Requirement: The migration does not broaden Git LFS tracking beyond the existing bounded archive-storage contract, converts no existing payload and rewrites no Git history.
- Source: B§11.2 — "Do not broaden LFS to all binaries or rewrite Git history as part of environment setup."; P `.gitattributes` and `OK-ENG-010`.
- Acceptance: The LFS rules in `.gitattributes` and the Git identities of all existing payloads are unchanged by the migration.
- Depends on: None.

### REQ-040 — Independent review of the exact candidate
- Requirement: Before integration, the exact migration candidate is examined by an actual independent reviewer, a separate reviewer session or subagent, under the existing protocol.
- Source: B§13 Stage 5 — obtain the independent review that the existing protocol requires (recommended); P PROTOCOL §5 and `ROLE.md`.
- Acceptance: The reviewer's identity, the exact candidate reviewed, the findings, their resolutions and the acceptance disposition are retained; mandatory findings are resolved and affected revisions are reviewed again.
- Acceptance: Self-review is never reported as independent review; where no independent reviewer is available, the review gate stays open while other useful independent work continues.
- Depends on: REQ-036

### REQ-041 — Integration and cleanup through the established lifecycle
- Requirement: The completed migration is integrated into main through the established procedure and its ownership and lease rules: main movement, branch movement, ownership, affected checks and any dependency on unfinished work are reconciled first; the merge is non-force and rejects stale expected state; the actual resulting main is verified with the applicable checks; and only the completed migration branch and worktree are removed, after their changes and required evidence are retained and no active worker, unpublished commit, untracked file, unknown write or dependent scope still needs them.
- Source: B MIG-14 — "Finish bounded work through the established merge-and-delete lifecycle." (existing owner direction).
- Source: B§10.2 and B§13 Stage 5 — integration and cleanup (recommended); P PROTOCOL §7 and `OK-ENG-009`.
- Acceptance: The merge commit and resulting main are read back, and the applicable resulting-main checks are recorded.
- Acceptance: The C271 branch is not deleted, and a branch whose deletion cannot be confirmed is reported with the exact pending action.
- Depends on: REQ-040

### REQ-042 — Readiness, completion and qualification are reported separately
- Requirement: Reports distinguish environment readiness, task completion and product qualification, and readiness is reported by component rather than as one overall result.
- Source: B MIG-16 — "Distinguish environment readiness, task completion, and product qualification." (necessary correctness condition).
- Source: B§14 — "Report readiness by component rather than one misleading 'everything works' result."; B§13 Stage 5 and B§15 — the closing report.
- Acceptance: A successful install is not reported as C271 completion, native-tool qualification or a release pass, and no unrelated product gate is marked complete.
- Acceptance: A missing required verification package prevents the corresponding profile being reported ready even while other work continues; missing optional tools and unsupported profiles remain visible.
- Acceptance: The migration ends with a concise report of the changes, the checks actually run, readiness by profile, retained blockers, remaining work and the next selected action.
- Depends on: REQ-012

## Decisions

- D01 — The brief's recommended decisions are carried as requirements. The brief labels its own engineering choices "Recommended". They are captured here as requirements, each citing the brief section it comes from, because the owner supplied the brief as this document's only source (U01). They are settled by the owner's approval of this document, not by this capture. The main ones: a native `.venv` on CPython 3.12 (REQ-003); `venv` plus pip with no new package manager (REQ-009); profiles (REQ-005); bootstrap and doctor tools (REQ-011, REQ-012); the local-mode rule set (REQ-017); `AGENTS.md` as the single authority with a local entry point and a `CLAUDE.md` adapter (REQ-019); the "Go/Continue" convention (REQ-023); and the reconciliation sequence (REQ-030 to REQ-033).
- D02 — Choices the owner delegated. The owner asked for "a definite container decision" (MIG-04) and for the missing or incompatible dependencies to be determined (MIG-03). The brief made those determinations; REQ-005 to REQ-010 record them.
- D03 — Proposed names are not mandated. `tools/bootstrap_local.py`, `tools/doctor_local.py`, `LOCAL-START-HERE.md`, `docs/development/LOCAL-SETUP.md`, `docs/workflow/LOCAL-PROMPTS.md`, `.python-version` and the command lines in B§5.3 are the brief's design targets. B§12 says: "The implementing agent should keep existing naming conventions where a suitable equivalent already exists." `CLAUDE.md` is the exception, because its name is fixed by the tool that reads it.
- D04 — Left to implementation planning, within the requirements: the exact CPython 3.12 patch (it must be an available, supported 3.12 patch observed on the host; S05 found 3.12.13 and 3.12.11); the form of the tracked interpreter specification (`.python-version` "or one equivalent", B§12); the migration task ID and the worktree location; the mechanism that makes the execution mode explicit; how the macOS lock is produced; tool flags and report formats; whether `docs/workflow/LOCAL-PROMPTS.md` is added ("Add if useful") and whether build-tool constraints are added ("Add if needed"); and how the fresh-session demonstration and the second-worktree test are staged. None of these changes what the owner receives or how success is recognized.
- D05 — Visual verification is not a completion condition of this migration. B§4.2 sets `python-verification` as the normal readiness target; B§5.1, B§13 and B§15 prepare Node and Chromium only for a selected visual profile; the brief selects no visual acceptance for the migration; and the migration changes no exporter or viewer code, so the AGENTS check table does not require `--full` for it. The tools must still support the profile and report its state (REQ-008, REQ-011, REQ-012). On the capturing machine that state would not be ready (S06). The owner can select the profile at any time; that adds preparation and `--full` evidence without changing a requirement here.
- D06 — Size figures are design targets, not acceptance rules. B§8.6 gives "approximately 5–10 KB or less" for `CURRENT.json` and "roughly one or two pages" for a session checkpoint as "Recommended design targets, not current acceptance rules". REQ-027 therefore requires compact, pointer-based records without a byte limit.
- D07 — The backup mechanism is not chosen here. B§11.3 requires "an existing durable backup mechanism" and B§2.3 records backup coverage as unknown; S02 adds that the clone is on an external volume. REQ-038 requires that an existing mechanism be identified, recorded and proven by one restore. Provisioning a new service, uploading to an external service or spending money is outside this document and needs the owner's separate decision; without an existing mechanism the backup acceptance of REQ-038 stays unmet.
- D08 — This document is a requirements source, not a second ledger. The project's task record under `docs/workflow/tasks/` remains the acceptance ledger for the migration (P PROTOCOL §3; MIG-09; REQ-022). This document tracks only its own drafting and approval state.
- D09 — The migration scope closes under the local-mode rules it adopts. B§13 says the stages "are engineering checkpoints, not a requirement to open a new chat or create a ZIP after each stage", its Stage 4 and Stage 5 deliverables include no Library ZIP, and PROTOCOL §8 lets the owner change the saved-ZIP requirement. The migration therefore needs no Library ZIP to close, provided REQ-016 and REQ-017 are in force first.
- D10 — The brief's stage order is planning material. Stages 0 to 5 (B§13) are captured through their deliverables and acceptance; ordering appears here only as real dependencies in the `Depends on` fields.
- D11 — Open reconciliation does not block setup. If REQ-030 stays open because legacy bytes are unavailable, the brief lets inventory and environment setup proceed (B§9.2). This document does not add a rule on integrating completed parts in that state; AGENTS assigns development integration to `OK-ENG-009`, and the migration is not reported complete while any requirement here is unmet (REQ-042).

## Open questions

None.

## Not yet specified

None.

## Assumptions

- Accepted: The brief is the owner's adopted statement of this migration, including its recommended decisions and its reading of the owner's "Go" wording as goal-directed continuation (MIG-08, which the brief itself labels interpreted intent). Basis: U01 — the owner supplied the brief as the only source for this document and excluded or changed nothing in it; the owner's approval of this document is where that adoption is confirmed.
