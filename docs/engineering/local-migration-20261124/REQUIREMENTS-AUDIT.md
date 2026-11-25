# Requirements audit of the candidate

**Task:** [LOCAL-MIGRATION-20261124](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md),
TASK-031. **Auditor:** Director `local-migration-f58a0f3c1d5a`, who took over after the tools, tests
and instructions had been written. This is the Director's own audit, made
again after the review of the first frozen candidate `7caaff61`. The independent review of
the exact candidate is TASK-032 and has its own record.

## Candidate

| Item | Value |
| --- | --- |
| Base | `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, the head of main on the remote (`git ls-remote` at 2026-11-25T21:02Z); it is the merge base |
| Audited content | Commit `a80a3947f3f6c6ae174f048c70605b5c7c369d95`, tree `9f3fba65d8fd70986db02e9c58f6f38d8cb8bd9f` |
| Difference from the base | 37 files added, 21 modified, none deleted or renamed; 18,625 of 18,646 base files keep path, mode and blob |
| Later commits | Only this audit and the session checkpoint; Git lists them |
| Frozen candidate | The commit that carries this file. A file cannot name its own commit, so the pull request and the review record name it, with its tree. No later change is made to it without renewed review |

## Method

All 111 acceptance criteria of the 42 requirements in the
[approved TRD](../../../TRDs/trd_ontokin-local-development-migration_2026-11-24.md) were walked against the
difference from the base, the records and, where a fact could be computed, a fresh computation.
"Met" means that the named evidence was opened and supports the criterion. A criterion that only a
later step can satisfy is open under that step's name. The wording of the criteria is shortened
here; the TRD governs.

Computed again for this audit, not taken from earlier records: every identity in
[PRESERVATION](PRESERVATION.json); the difference from the base; the searches below; the identities of
the R06 archive, its 131 manifest entries, its receipt and the evidence archive inside it; the
comparison of the raw driver logs with the raw baseline logs, with a second program; the doctor;
and, at 2026-11-25T21:02Z, the remote heads, the state of pull request 274 (open draft at `bef67902`) and of
issues 273 and 277 (open). The audit draft of the previous Director was used as
a list of pointers; each pointer was checked to resolve.

## From the requirements to evidence

94 criteria are met, 2 are met except for a part that the owner waived,
15 are open for later steps, and none is unmet. Open: TASK-032 2, TASK-033 1, TASK-034 6, TASK-035 1, TASK-036 5.

| Requirement | Criterion, in short | State | Evidence |
| --- | --- | --- | --- |
| REQ-001 | Host inventory, each item observed or "not observed" | met | [HOST-INVENTORY](HOST-INVENTORY.md); backup coverage was observed, its value is withheld there on purpose |
|  | Setup decisions cite the inventory | met | `selected_from` in [the specification](../../../tools/local-environment.json); [DECISION](DECISION.md) DEC-003 |
|  | Everything the inventory found is still there | open: TASK-034 | Main checkout: head, untracked `TRDs/` and `Implementation_Plans/`; rechecked at integration |
| REQ-002 | One task record with requirements, plan, status, start and acceptance | met | [Task records](../../workflow/tasks/LOCAL-MIGRATION-20261124/); identifiers looked for before use ([REQUIREMENTS](../../workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md)) |
|  | Own branch from current main; C271 untouched | met | Merge base `6b346b1e`; C271 head `bef67902` in `git ls-remote` |
| REQ-003 | Exact version, distribution and platform recorded and tracked | met | [Specification](../../../tools/local-environment.json); [ENVIRONMENT](ENVIRONMENT.json) |
|  | Project commands use `.venv/bin/python` | open: TASK-035 | Migration and candidate worktrees; the main checkout follows |
|  | No global Python is written | met | Setup writes only `.venv`; Homebrew Python holds no project package |
|  | `requires-python` unchanged; only executed versions claimed | met | `pyproject.toml` unchanged; CPython 3.12.13 only |
| REQ-004 | Healthy: nothing rebuilt. Incompatible: reported, rebuilt only on request | met | tests/test_bootstrap_local.py; scenario runs in [PRE-REVIEWS](PRE-REVIEWS.md) |
|  | Nothing of the kind tracked or copied | met | Tree search; [SECOND-WORKTREE](SECOND-WORKTREE.json) |
| REQ-005 | Profiles and their checks documented, missing dependencies inventoried | met | [LOCAL-SETUP](../../development/LOCAL-SETUP.md#profiles); [ENVIRONMENT](ENVIRONMENT.json) |
|  | Readiness reported per profile | met | [Readiness](#readiness-completion-and-qualification) |
| REQ-006 | Linux lock refused elsewhere, hashes always enforced | met | tests/test_bootstrap_local.py, PlatformSelectionTests |
|  | Linux lock byte-identical | open: TASK-034 | [PRESERVATION](PRESERVATION.json) |
|  | Reviewed macOS lock under its own name | met | [LOCK-REVIEW](LOCK-REVIEW.md); [provenance](../../../tools/native-reader-verification-macos-arm64-cp312.provenance.json) |
| REQ-007 | Installed versions, `pip check`, imports, preflight, record | met | [ENVIRONMENT](ENVIRONMENT.json) |
|  | No pin replaced | met | Pins file and locks unchanged or reviewed |
| REQ-008 | Nothing installed while not selected; state as it is | met | Doctor: mismatch, Node.js 25.9.0 |
|  | When selected, Node and npm compared with the target | met | Visual checks and tests; a real preview refused Node.js 25 |
|  | `npm ci` only for first preparation or deliberate repair, never in use | met | VisualProfileTests, UseTests; not exercised for real here |
|  | No `--with-deps` in macOS instructions | met | [LOCAL-SETUP](../../development/LOCAL-SETUP.md#visual-verification) |
| REQ-009 | Installed packages are those of the profile and pip | met | [ENVIRONMENT](ENVIRONMENT.json): no additional package |
|  | No other package manager | met | [Searches](#searches) |
|  | Native applications only under a selecting task | met | Setup refuses those profiles |
|  | Historical profiles only in their own environment | met | [LOCAL-SETUP](../../development/LOCAL-SETUP.md#native-by-default-no-container) |
| REQ-010 | Decision and reasons stated; every check without a container | open: TASK-036 | [LOCAL-SETUP](../../development/LOCAL-SETUP.md#native-by-default-no-container); no container used so far |
|  | Emulation never counted as native Linux | met | Same section; no Linux evidence is claimed |
| REQ-011 | Second run changes nothing | met | [ENVIRONMENT](ENVIRONMENT.json) second run; tests |
|  | Missing interpreter and packages told apart; existing mechanism | met | InterpreterTests |
|  | Concurrent installers excluded; used directories not replaced | met | FailureTests, UseTests; real concurrent runs |
|  | Preview, interpreter, root and report options | met | `tools/bootstrap_local.py --help`; CommandLineTests |
|  | Does not replace the driver, change behaviour or publish | met | OtherProfileTests; driver unchanged apart from inventories |
|  | Four required behaviours tested and executed on the candidate | met | [CANDIDATE-CHECKS](CANDIDATE-CHECKS.json) |
| REQ-012 | Five states; wrong version is a mismatch; unexecuted is no pass | met | ReadinessTests |
|  | Diagnosis changes nothing | met | ReportTests, RealEnvironmentTests |
|  | No fetch, no publish; remote only with `--online` | met | SectionTests |
|  | Tool readiness apart from native acceptance; no environment needed | met | Runs with CPython 3.9 and 3.11 |
| REQ-013 | What was installed, from which inputs, with which tools | met | [ENVIRONMENT](ENVIRONMENT.json); [PACKAGE-SMOKE](PACKAGE-SMOKE.json) |
|  | Ignore rules changed only where needed | met | `.claude/.gitignore`; root `.gitignore` byte-identical |
|  | Working evidence persistent; summary preserved before closing | open: TASK-036 | This directory; [STORAGE](STORAGE.md) |
| REQ-014 | A fresh environment elsewhere reaches the same readiness | met | [SECOND-WORKTREE](SECOND-WORKTREE.json) |
|  | Guide matches the tools; the old example is replaced | met | [LOCAL-SETUP](../../development/LOCAL-SETUP.md); [OK-ENG-006](../OK-ENG-006-local-validation-and-hosted-ci-policy.md) |
| REQ-015 | Revision, build environment, wheel, import locations, resources | met | [PACKAGE-SMOKE](PACKAGE-SMOKE.json) |
|  | Not inferred from an editable install | met | Separate clean environment in the same record |
| REQ-016 | Dated, prospective decision | met | [DECISION](DECISION.md) |
|  | Old handoffs and receipts unchanged | met | All other base paths keep their blobs |
|  | Both modes routed, neither guessed | met | [AGENTS](../../../AGENTS.md#execution-modes); registry |
| REQ-017 | Local closing without the Library | met | [HANDOFF](../../workflow/HANDOFF.md#local-sessions) |
|  | Continues within the task; a new scope needs selection | met | [PROTOCOL](../../workflow/PROTOCOL.md#4-implement-delegate-and-bound-the-session) |
| REQ-018 | No instruction both ways | met | [Reading for conflicts](#reading-for-conflicts) |
|  | GOAL boundaries and semantics unchanged | met | GOAL: one operating reference |
|  | Documentation and workflow checks pass | met | [Checks](#checks) |
| REQ-019 | `CLAUDE.md` imports AGENTS and adds no rule | met | [CLAUDE](../../../CLAUDE.md) |
|  | Observed to have loaded in the application | met | [FRESH-SESSION](FRESH-SESSION.md); [judgement](FRESH-SESSION-ACCEPTANCE.md) |
| REQ-020 | Six links resolve and are discovered | met | [PRESERVATION](PRESERVATION.json); [FRESH-SESSION](FRESH-SESSION.md); [judgement](FRESH-SESSION-ACCEPTANCE.md) |
|  | One version of each skill; no named skill invoked | met | Tree; task records |
| REQ-021 | Documented workflow runs in the Code tab | met | [FRESH-SESSION](FRESH-SESSION.md); [judgement](FRESH-SESSION-ACCEPTANCE.md) |
|  | Own version checked; Worktree mode deliberate; path and branch verified | **met, except a part the owner waived** | Version read from the application. Worktree mode not observed; waived by the owner ([judgement](FRESH-SESSION-ACCEPTANCE.md)) |
| REQ-022 | No competing ledger | met | [Searches](#searches) |
|  | Pointers and statuses validate | open: TASK-036 | `tools/chat_workflow.py check` |
| REQ-023 | Resumes the next unmet gate from records | met | [FRESH-SESSION](FRESH-SESSION.md); [judgement](FRESH-SESSION-ACCEPTANCE.md) |
|  | Never selects a milestone or reruns native work | met | [LOCAL-START-HERE](../../../LOCAL-START-HERE.md) |
|  | Depends on no Goals feature, Task or memory | met | Same document |
| REQ-024 | The steps are there and are followed | **met, except a part the owner waived** | [LOCAL-START-HERE](../../../LOCAL-START-HERE.md); steps followed in [FRESH-SESSION](FRESH-SESSION.md). The report before the first change was not observed in an unguided session; accepted by the owner ([judgement](FRESH-SESSION-ACCEPTANCE.md#what-the-logs-show-beyond-the-accounts)) |
|  | Offline rule | met | Same document |
|  | No suite or archive at startup; identities recorded | met | [FRESH-SESSION](FRESH-SESSION.md); [RECONCILIATION](RECONCILIATION.md#identities-for-later-on-demand-use) |
| REQ-025 | A checkpoint another agent can continue from | met | [SESSION](../../workflow/tasks/LOCAL-MIGRATION-20261124/SESSION.md); [FRESH-SESSION](FRESH-SESSION.md); [judgement](FRESH-SESSION-ACCEPTANCE.md) |
|  | Recovery from commits and checkpoints | met | [PROTOCOL](../../workflow/PROTOCOL.md#8-recovery-and-stopping) |
|  | Changed-scope checks at checkpoints; baseline preserved | met | [BASELINE-CHECKS](BASELINE-CHECKS.json); [CANDIDATE-CHECKS](CANDIDATE-CHECKS.json) |
| REQ-026 | Nine field groups; earlier records valid | met | [Template](../../workflow/templates/SESSION.md) |
|  | No receipt of the receipt | met | Same template |
| REQ-027 | CURRENT holds pointers and links history | met | [CURRENT](../../workflow/CURRENT.json) |
|  | Earlier content retrievable unchanged | met | [CURRENT-before-migration](CURRENT-before-migration.json), SHA-256 `fec57459…` |
|  | Versioned schema, checker, tests, mapping | met | [SCHEMA-MAPPING](SCHEMA-MAPPING.md); tests/test_chat_workflow.py |
| REQ-028 | A task after main moved records the actual base | met | StartingRevisionTests |
|  | Focused tests pass; no historical hash modified | met | [CANDIDATE-CHECKS](CANDIDATE-CHECKS.json) |
| REQ-029 | Demonstration performed, recorded, matching | met | [FRESH-SESSION](FRESH-SESSION.md); [judgement](FRESH-SESSION-ACCEPTANCE.md) |
|  | Concise user instructions | met | [LOCAL-PROMPTS](../../workflow/LOCAL-PROMPTS.md) |
| REQ-030 | Four findings recorded; C271 referenced from main | met | [RECONCILIATION](RECONCILIATION.md); [STATUS](../../../STATUS.md#current-workflow-and-next-action); [CURRENT](../../workflow/CURRENT.json) `unfinished` |
|  | Live state re-read, identities as observations | met | Same record |
|  | R06 and receipt on the machine first | met | [R06-VERIFICATION](R06-VERIFICATION.json), `retrieval` and `files` |
|  | Missing bytes named; safe work continued | met | The task record named the missing files as a blocker of TASK-006 only until 2026-11-25; inventory, environment and tools went on meanwhile ([PLAN](../../workflow/tasks/LOCAL-MIGRATION-20261124/PLAN.md#order-and-dependencies)) |
| REQ-031 | Verified before any extraction | met | [R06-VERIFICATION](R06-VERIFICATION.json): 16 checks, before any extraction |
|  | No overlay; records reconciled by meaning | met | [RECONCILIATION](RECONCILIATION.md#overlapping-records-reconciled-by-meaning); `git diff --name-status` adds no file of a handoff |
| REQ-032 | Evidence identity equals the record, durable location recorded | met | [R06-VERIFICATION](R06-VERIFICATION.json) `evidence_member`; [RECONCILIATION](RECONCILIATION.md#identities-for-later-on-demand-use) |
|  | No C271 history rewritten | open: TASK-034 | `git ls-remote` |
| REQ-033 | No merge, closure or deletion; unmet gates shown | open: TASK-034 | PR 274 and issue 273 open; STATUS; CURRENT |
|  | Reconciled when that scope is selected | met | [DECISION](DECISION.md#history-that-keeps-its-interpretation) |
| REQ-034 | Authentication observed before publication | met | [HOST-INVENTORY](HOST-INVENTORY.md); pushes of this branch |
|  | No transfer through a browser chat | met | [PROTOCOL](../../workflow/PROTOCOL.md#7-integration-and-branch-lifecycle) |
| REQ-035 | Second worktree acts on itself; evidence preserved | met | [SECOND-WORKTREE](SECOND-WORKTREE.json) |
|  | No shared writable environment | met | Same record |
|  | Isolation inspected, lease expiry no proof | met | [PROTOCOL](../../workflow/PROTOCOL.md) |
|  | No hook | met | None in the diff |
| REQ-036 | Passed, failed, pending and not run apart | met | [CANDIDATE-CHECKS](CANDIDATE-CHECKS.json) |
|  | Required checks run on the actual candidate | met | [CANDIDATE-CHECKS](CANDIDATE-CHECKS.json); [Checks](#checks) |
|  | Per-command timeout, new outside output, no outer timeout | met | Same record; [LOCAL-SETUP](../../development/LOCAL-SETUP.md#run-the-checks) |
|  | Existing failures preserved, no expectation changed | met | Same record |
| REQ-037 | No trigger added | met | `git diff` of `.github`: empty |
| REQ-038 | One unique artifact restored and verified | met | [STORAGE](STORAGE.md#restore-check); [R06-VERIFICATION](R06-VERIFICATION.json). Unique untracked local material is listed as protected by no project mechanism, as DEC-009 foresees |
|  | Ignored directory, bundle and copied environment are no backups | met | [STORAGE](STORAGE.md#existing-durable-mechanisms) |
|  | No nested handoffs | met | None in the diff |
| REQ-039 | LFS rules and payload identities unchanged | open: TASK-034 | [PRESERVATION](PRESERVATION.json) |
| REQ-040 | Reviewer, candidate, findings, resolutions, disposition | open: TASK-032 | After the freeze |
|  | Self-review never reported as independent | open: TASK-032 | [PRE-REVIEWS](PRE-REVIEWS.md) keeps earlier reviews apart |
| REQ-041 | Merge and resulting main read back and checked | open: TASK-033 | After review |
|  | C271 branch kept; deletion observed or pending | open: TASK-034 | After integration |
| REQ-042 | Install is no completion, qualification or release | open: TASK-036 | STATUS; reports |
|  | A missing package prevents ready | met | [SECOND-WORKTREE](SECOND-WORKTREE.json) |
|  | Closing report | open: TASK-036 | TASK-036 |

Some evidence was made with earlier revisions of the tools, which were corrected later:
[ENVIRONMENT](ENVIRONMENT.json) (`4bdb2ee6`), [PACKAGE-SMOKE](PACKAGE-SMOKE.json) (`3fd7b922`) and
[SECOND-WORKTREE](SECOND-WORKTREE.json) (`3c7985db`). With the tools of `d4d486b3` a preview, a fresh setup, a
repeat and the doctor were run in a new clone. With those of `7caaff61` the Director made a fresh
environment in the reviewer's clone, and the reviewer's repeat changed nothing. Both were ready. The isolation of two worktrees and the installed
package were not tested again. The setup in the main checkout (TASK-035) is the next real run.

## From the changes back to the requirements

Every changed path serves a requirement. "…/" is `docs/engineering/local-migration-20261124/`. REQ-041 has no
file yet; its record is made at integration.

| Path | Requirements |
| --- | --- |
| `.agents/skills/ontokin-delivery/SKILL.md` | REQ-018, REQ-020 |
| `.agents/skills/ontokin-session/SKILL.md` | REQ-018, REQ-020 |
| `.claude/.gitignore` | REQ-004, REQ-013 |
| `AGENTS.md` | REQ-014, REQ-016, REQ-017, REQ-018, REQ-037 |
| `CLAUDE.md` | REQ-019 |
| `GOAL.md` | REQ-018 |
| `LOCAL-START-HERE.md` | REQ-019, REQ-023, REQ-024, REQ-029 |
| `README.md` | REQ-016, REQ-018 |
| `STATUS.md` | REQ-018, REQ-022, REQ-027, REQ-030, REQ-033, REQ-042 |
| `TRDs/INDEX.md` | REQ-002 |
| `TRDs/trd_ontokin-local-development-migration_2026-11-24.md` | REQ-002 |
| `docs/README.md` | REQ-016, REQ-018 |
| `docs/development/LOCAL-SETUP.md` | REQ-005, REQ-008, REQ-009, REQ-010, REQ-014 |
| `docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md` | REQ-014, REQ-017, REQ-018, REQ-037 |
| `…/BASELINE-CHECKS.json` | REQ-036 |
| `…/CANDIDATE-CHECKS.json` | REQ-007, REQ-011, REQ-018, REQ-028, REQ-036, REQ-037 |
| `…/CURRENT-before-migration.json` | REQ-027 |
| `…/DECISION.md` | REQ-016 |
| `…/ENVIRONMENT.json` | REQ-003, REQ-004, REQ-005, REQ-007, REQ-011, REQ-013 |
| `…/FRESH-SESSION-1.md` | REQ-029 |
| `…/FRESH-SESSION.md` | REQ-019, REQ-020, REQ-021, REQ-023, REQ-024, REQ-029 |
| `…/FRESH-SESSION-ACCEPTANCE.md` | REQ-019, REQ-020, REQ-021, REQ-023, REQ-024, REQ-029 |
| `…/HOST-INVENTORY.md` | REQ-001, REQ-034 |
| `…/LOCK-REVIEW.md` | REQ-006 |
| `…/PACKAGE-SMOKE.json` | REQ-013, REQ-015 |
| `…/PRE-REVIEWS.md` | REQ-040 |
| `…/PRESERVATION.json` | REQ-006, REQ-008, REQ-020, REQ-032, REQ-033, REQ-039 |
| `…/R06-VERIFICATION.json` | REQ-031, REQ-032, REQ-038 |
| `…/RECONCILIATION.md` | REQ-030, REQ-031, REQ-032, REQ-033 |
| `…/REQUIREMENTS-AUDIT.md` | REQ-009, REQ-010, REQ-018, REQ-022, REQ-042 |
| `…/SCHEMA-MAPPING.md` | REQ-027, REQ-028 |
| `…/SECOND-WORKTREE.json` | REQ-004, REQ-014, REQ-035 |
| `…/STORAGE.md` | REQ-038 |
| `docs/user-guide/development-and-scope.md` | REQ-018 |
| `docs/workflow/CURRENT.json` | REQ-022, REQ-027, REQ-030, REQ-033 |
| `docs/workflow/HANDOFF.md` | REQ-017, REQ-018 |
| `docs/workflow/KNOWLEDGE.md` | REQ-018 |
| `docs/workflow/LOCAL-PROMPTS.md` | REQ-021, REQ-029 |
| `docs/workflow/PROTOCOL.md` | REQ-016, REQ-017, REQ-018, REQ-025, REQ-035 |
| `docs/workflow/README.md` | REQ-018 |
| `docs/workflow/knowledge.json` | REQ-018 |
| `docs/workflow/registry.json` | REQ-016, REQ-018, REQ-028 |
| `docs/workflow/tasks/LOCAL-MIGRATION-20261124/PLAN.md` | REQ-002 |
| `docs/workflow/tasks/LOCAL-MIGRATION-20261124/REQUIREMENTS.md` | REQ-002 |
| `docs/workflow/tasks/LOCAL-MIGRATION-20261124/SESSION.md` | REQ-025, REQ-026 |
| `docs/workflow/tasks/LOCAL-MIGRATION-20261124/task.json` | REQ-002, REQ-022 |
| `docs/workflow/templates/SESSION.md` | REQ-026 |
| `tests/test_bootstrap_local.py` | REQ-004, REQ-008, REQ-011 |
| `tests/test_chat_workflow.py` | REQ-022, REQ-027, REQ-028 |
| `tests/test_doctor_local.py` | REQ-008, REQ-012, REQ-042 |
| `tests/test_local_checks.py` | REQ-028, REQ-036 |
| `tools/bootstrap_local.py` | REQ-004, REQ-008, REQ-011 |
| `tools/chat_workflow.py` | REQ-022, REQ-027, REQ-028 |
| `tools/check_local.py` | REQ-028, REQ-036 |
| `tools/doctor_local.py` | REQ-008, REQ-012, REQ-042 |
| `tools/local-environment.json` | REQ-003, REQ-005, REQ-009, REQ-013 |
| `tools/native-reader-verification-macos-arm64-cp312.lock` | REQ-006, REQ-007 |
| `tools/native-reader-verification-macos-arm64-cp312.provenance.json` | REQ-006 |

## Reading for conflicts

Read in full on this branch: AGENTS, CLAUDE, LOCAL-START-HERE, CHATGPT-START-HERE, GOAL, STATUS, ROLE,
the registry, CURRENT, PROTOCOL, HANDOFF, EPHEMERAL-HOST, the workflow guide, LOCAL-PROMPTS, the session
and worker templates, KNOWLEDGE, the session, delivery and learning skills, OK-ENG-006, OK-ENG-009,
LOCAL-SETUP, the root README and the changed parts of the documentation and user guides; the
summaries of all memory records and capabilities. All tracked files were searched for wording that
confines checks to a hosted workspace or requires a saved ZIP.

- Every rule that would keep a local agent off the owner's machine, rebuild a host or require a ZIP
  is marked for browser sessions, stands in a browser document, or is history.
- GOAL changes in one sentence, the place where work stops in each mode.
- No conflict was found. One sentence was too weak, the startup report ([judgement](FRESH-SESSION-ACCEPTANCE.md#what-the-logs-show-beyond-the-accounts)); it is corrected.

## Searches

| Search in the candidate tree | Result |
| --- | --- |
| `uv.lock`, Dockerfile, Compose file, `TODO.md`, `.python-version`, `.worktreeinclude`, Pipfile, poetry or Conda files | 0 found |
| `requirements*.txt` at the root | 0 found |
| Tracked environment, `node_modules` or cache | 0 found |
| Difference under `.github` | None; both workflows are manual with the opt-in defaulting to false |
| Preserved identities (13 files and links) | All equal |
| Home directories, machine paths, addresses, keys and tokens in added lines | Only made-up values in tests |
| Second ledger | None; `Implementation_Plans/` is not committed |

## Checks

| Check | Result |
| --- | --- |
| Documentation verifier, with this file | Passed: 1,344 documents, 6,160 local links, 161 anchors, no failure |
| Workflow check | Passed: 12 tasks |
| Focused tool tests at `16c83df5` | 307 tests, OK with a resolved temporary directory; two not passing with the default one, as on the base |
| Routine driver at `16c83df5`, both temporary-directory settings | Fails with one and 307 tests, exactly those of the unmodified base; every other step passes ([CANDIDATE-CHECKS](CANDIDATE-CHECKS.json)) |

## Readiness, completion and qualification

These are three different results.

**Environment readiness**, reported by the doctor (`tools/doctor_local.py --json`) in the migration
worktree at the audited content:

| Profile | Readiness | What is not ready |
| --- | --- | --- |
| `core` | ready |  |
| `python-verification` | ready |  |
| `visual-verification` | mismatch | Node.js v25.9.0; the target is Node.js 22. not installed: @esbuild/darwin-arm64 0.25.10, esbuild 0.25.10, fsevents 2.3.2, gltf-validator 2.0.0-dev.3.10, playwright 1.56.1, playwright-core 1.56.1, three 0.180.0 Playwright is not in |
| `package-smoke` | not_checked | The wheel is built in the clean build environment and its tool versions are recorded. The wheel is installed into the separate clean environment. The installed entry point runs from outside the checkout with source-path injection  |
| `historical-native` | not_checked | Established only by the contract of the selected experiment. General setup neither prepares nor accepts it, and a newer interpreter never inherits an old qualification. |
| `linux-container` | unsupported | A later profile must state its purpose and carry its own acceptance. An emulated amd64 container is never native Linux qualification. |

The main checkout has no environment yet (TASK-035).

**Task completion.** Not complete. Open: TASK-032 (review), TASK-033 (integration and
resulting-main checks), TASK-034 (preservation, cleanup), TASK-035 (environment of the main
checkout), TASK-036 (closing report).

**Product qualification.** Unchanged. The migration qualifies no language, native, destination or
product claim, closes no release gate and completes none of C271's gates. A successful install is
evidence of an environment only.

## Limits

One machine, one interpreter, one application version. Accounts of earlier steps, such as the setup
trials and the mutations of the reviews, were read and not repeated. The truth of records about
C271's history and about the owner's ChatGPT Library beyond the R06 files was not checked.
