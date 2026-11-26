# C271 and current main: files changed on both sides

Record of C271-P29-R07 for the later R04 integration gate. It documents the overlap and resolves
nothing: this phase merges no main into the C271 branch, edits no file because of the overlap
and writes nothing to main.

Observed on 2026-11-26 at about 01:15Z. Current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`
(read with `git ls-remote`), C271 branch head `80fecf97b785544e8044a60df849cc5918929599` (the
declaration commit of this phase), merge base `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. Since
the merge base, main changed 110 paths and the C271 branch 3,371; the accepted candidate commit
`dbf20beed1bd6274a42531c997d054c09fb8ebb8` adds no further overlap.

## The six files

Method: the intersection of `git diff --name-only` from the merge base to main and from the merge
base to the C271 head, with `git diff --numstat` for each side. A dry
`git merge-tree --write-tree --name-only origin/main HEAD` in the C271 worktree, which changes no
ref and no working file, reports a content conflict in five of them; `docs/README.md` merges
without conflict. GitHub reports pull request 274 as `CONFLICTING` (merge state `DIRTY`).

| File | Main's change (lines added/removed) | C271's change (lines added/removed) | Dry merge |
| --- | --- | --- | --- |
| `STATUS.md` | 13/5: the local migration's status, the local-mode entry wording, the verification line for the local baseline and resulting main, the concise "C271 is unfinished and separate" entry, the released migration lease | 2/0: the C271 P22 retained-input line and its preparation result | conflict |
| `docs/README.md` | 7/0: the local entry point, setup guide, local prompts, owner direction and reconciliation record | 4/0: the "Current C271 loader-path prerequisite" section (P14) | clean |
| `docs/workflow/CURRENT.json` | 65/78: compact schema-2 pointers (execution modes, delivery policy for both modes, the unfinished C271 entry, retained history linked) | 3,066/58: C271's schema-1 pointers with its embedded receipts through P29 R02 and this phase's local-mode fields | conflict |
| `docs/workflow/memory.json` | 14/0: lesson `memory-local-state-in-checkpoint` | 15/0: lesson `memory-c271-loader-source-admission-boundary` | conflict |
| `tools/check_local.py` | 4/3: larger copied-input inventories, `SOURCE_DIRS` adds `.agents` and `TRDs`, `ROOT_FILES` adds `CHATGPT-START-HERE.md`, `ROLE.md`, `LOCAL-START-HERE.md`, `CLAUDE.md`, `LICENSING.md` and `NOTICE` | 130/12: `SOURCE_DIRS` adds `.agents`, `ROOT_FILES` adds `CHATGPT-START-HERE.md` and `ROLE.md`; the readback selection required before the unit step (`--readback-config`, `--readback-config-sha256`, `prepare_readback_selection`, `bind_readback_workspace`), scrubbing of the readback environment variables for that step, and process accounting | conflict |
| `tests/test_local_checks.py` | 35/3: an instruction-file and adopted-requirement isolation test and a declared-input test | 56/2: binds the readback seam in the synthetic runs and adds an instruction-target isolation test | conflict |

## What must survive the reconciliation

Both purposes, not one side chosen over the other:

- C271's readback-configuration bindings and its process and environment controls in the
  driver and their tests, which the required regression of R03 depends on.
- The migration's larger set of instruction files and inputs copied into validation
  workspaces, with its inventory tests, which current main's isolated documentation step
  depends on.

The two `CURRENT.json` versions differ in schema (1 on the branch, 2 on main) and in purpose;
the two `memory.json` additions are independent records; the `STATUS.md` and `docs/README.md`
additions are independent sections. Each is reconciled by meaning.

## Further notes for the integration gate

- Main's entries for C271 in `STATUS.md` and `docs/workflow/CURRENT.json` are dated
  observations (head `bef67902`, browser mode, publication gate open, observed
  2026-11-25T06:52:26Z). They stay as they are until the later gate, or a separately authorized
  update of main, replaces them with the state that C271's own records then hold.
- This phase commits the approved TRD file `TRDs/trd_c271-p29-exact-publication-in-local-mode_2026-11-25.md`
  on the C271 branch. Main tracks a generated `TRDs/INDEX.md` that does not list it; the main
  checkout holds an uncommitted index that does. No file-level conflict exists, but the index
  should be regenerated with the TRD tool when the TRD reaches main.
- The C271 branch carries older copies of instruction files (`AGENTS.md`, `docs/workflow/PROTOCOL.md`,
  `docs/workflow/HANDOFF.md`, `docs/workflow/registry.json`, `tools/chat_workflow.py`) that main
  has since changed. They are not in the six-file overlap because only main changed them; a
  merge takes main's versions.

R04 is the gate that resolves these conflicts, in a later phase, after R03.
