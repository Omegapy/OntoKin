# C271-P32: resolution of the merge of main into the C271 branch (gate MB)

This merge commit joins this branch's head `6fb6525f670ac619857d4830cda0a3e2bf298d93` (C271-P32's
declaration) with main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`. The merge base is
`e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. It is gate MB of the adopted macOS contract
([CONTRACT](../macos-contract-design-p31/CONTRACT.md) section 11). It brings main's local-mode
files onto this branch and does not integrate anything into main.
[MAIN-CONFLICTS](../p29-local-publication-r07/MAIN-CONFLICTS.md) placed this resolution inside
R04, after R03. The adopted contract moved the branch-side merge earlier, because implementation
and preparation need main's files. Integration into main, and its checks, stay in R04.

## Files changed on one side only

- **104 paths changed only on main** take main's bytes. They include the current instructions
  (`AGENTS.md`, `CLAUDE.md`, `GOAL.md`, `LOCAL-START-HERE.md`, `docs/workflow/PROTOCOL.md`,
  `HANDOFF.md` and `registry.json`), the workflow tool `tools/chat_workflow.py`, and the local
  environment specification, doctor and setup tools. They also include
  `tools/native-reader-verification-macos-arm64-cp312.lock` with its provenance. This branch's
  older copies of those instruction files are replaced, as MAIN-CONFLICTS anticipated.
- **3,659 paths changed only on this branch** keep this branch's bytes.

## The six files changed on both sides

| File | Resolution | Both purposes kept |
| --- | --- | --- |
| `docs/README.md` | Merged cleanly by Git | main's local entry points and this branch's C271 loader-path section |
| `STATUS.md` | Main's side of the one conflict hunk. That side holds the local migration's paragraph, main's dated C271 paragraph and main's C270 paragraph, which adds "That direction came on November 24, 2026". This branch's P22 status line is not carried forward: main's newer C271 entry supersedes it as C271's status line, and its text stays in Git history (`6fb6525f`) and in C271's REQUIREMENTS, section P22. | main's status; C271's entry stays a dated observation until R04, as MAIN-CONFLICTS requires |
| `docs/workflow/CURRENT.json` | Rewritten in main's schema 2, which main's workflow check requires, since the registry is schema 2. Active task C271 in local mode, with checkpoint `docs/workflow/tasks/C271/task.json` and `P32-SESSION.md`. Main's boundaries, delivery policy and history entry are kept, and two C271 boundary lines are added. Main's `unfinished` entry for C271 is removed, because C271 is the active task here. | main's pointer model; C271's current pointers; this branch's schema-1 file is retained byte for byte as [CURRENT-C271-schema1.json](CURRENT-C271-schema1.json) (215,534 bytes, SHA-256 `b0f51618e0aa9c706f33d8de5ad8e49323f1574d7484ed100adf20c414a6c368`) and bound in CURRENT's `history` |
| `docs/workflow/memory.json` | The union. Both sides keep the 15 base records unchanged. This branch's `memory-c271-loader-source-admission-boundary` and main's `memory-local-state-in-checkpoint` are both kept, in that order. | both lessons |
| `tools/check_local.py` | The one conflict hunk keeps this branch's `READBACK_CONFIG_ENV` and `READBACK_DIGEST_ENV`, and takes main's `SOURCE_DIRS` (which adds `TRDs`) and `ROOT_FILES` (which adds `LOCAL-START-HERE.md`, `CLAUDE.md`, `LICENSING.md` and `NOTICE`). Main's lists already contain this branch's additions: `.agents`, `CHATGPT-START-HERE.md` and `ROLE.md`. Every other C271 driver change merged without conflict and is unchanged: the readback selection, the scrubbing of the readback environment and the process accounting. | C271's readback bindings and process controls; the migration's larger copied-input set |
| `tests/test_local_checks.py` | Both sides added a test at the same place, and the two tests shared their middle assertions. Both are kept as separate methods, each with the shared assertions: this branch's `test_workflow_instruction_targets_survive_workspace_isolation` and main's `test_instruction_files_and_adopted_requirements_reach_the_isolated_workspace`. Main's `test_declared_instruction_inputs_exist_in_this_repository` is kept as well. This branch's `execute` helper mocks the readback selection for the synthetic runs and so applies to main's test too. | C271's seam binding and isolation test; the migration's isolation and declared-input tests |

## Checks of the merged tree, before the commit

These checks run main's tools, which came in with the merge, through this worktree's
`.venv/bin/python` (CPython 3.12.13, holding no package):

| Check | Result |
| --- | --- |
| `tools/chat_workflow.py check` | passed: 13 tasks, now including main's LOCAL-MIGRATION-20261124 |
| documentation verifier | passed, with no failure |
| `git diff --cached --check` on the six files and this phase's records | passed |
| `-B -m unittest tests.test_local_checks -v`, with a resolved temporary directory | 33 tests, all passed, no skip. The three tests above ran. |

Raw outputs are kept in `../OntoKin-local/c271-p32/checks/merge/` beside the clone.

**Environment readiness (separate).** The doctor now diagnoses this worktree, since the
specification came in with the merge. `core` is ready. `python-verification` is missing, because
the worktree's `.venv` holds none of the seven pinned packages; preparing them belongs to gate MP.
The doctor was given a non-existent Node path, so no Node process started.

No routine driver, no readback method and no behavioural test ran.
