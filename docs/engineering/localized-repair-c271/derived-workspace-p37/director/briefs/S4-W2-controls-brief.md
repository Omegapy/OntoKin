You are W2, the independent control author for the OntoKin project, task C271, phase C271-P37 (the correction of the derived workspace's source check), Director `c271-p37-08beec34eb0a`. You work in a fresh context. You wrote none of the implementation (W1's correction, or MI's), the contracts, or the decision. Your one bounded objective: stage S4 of the correction plan, **the frozen controls** for the corrected derived route. Contract section 9 requires an independent author to freeze exact inputs and expected outcomes before execution. The Director executes your controls; you freeze them.

## Where things are
- Worktree (shared checkout): `<worktree>`, branch `work/c271-missing-import-digest-control`, at the declaration commit `2f728998456c829f3cdc13bbf72d6dd805fefa36`, with W1's uncommitted correction in its working tree. Call it `<worktree>`; `.../` stands for `<worktree>/docs/engineering/localized-repair-c271/`.
- Beside the clone: `<local>/` (`<local>`). Your evidence directory: `<local>/c271-p37/workers/W2-controls/` (create it). W1's evidence: `<local>/c271-p37/workers/W1-correction/` (read only).
- **Your exclusive writes in the worktree**, and nothing else there:
  - one new test module under `tests/`, which you name (for example `tests/test_current_host_readback_derived_v02.py`);
  - `.../derived-workspace-p37/CONTROLS-FROZEN.json`.

## Read first
- `<worktree>/AGENTS.md`, `<worktree>/ROLE.md`, `<worktree>/docs/workflow/PROTOCOL.md` sections 4 and 5, `<worktree>/docs/workflow/templates/WORKER.md`.
- The correction plan `.../derived-workspace-p37/CORRECTION-PLAN.md` and `PHASE.json` (A4).
- W1's decision `.../derived-workspace-p37/DECISION-001.md` and interface note `.../derived-workspace-p37/interfaces/W1-CORRECTION.md`, and the changed code: `tools/check_local.py` and `prototypes/static_tray_v01/current_host_readback_v02.py`. To see exactly what W1 changed, compare the working tree with the declaration commit by reading Git's files, or with the copy at `<local>/c271-p37/measure/prep-001/workspace`, which holds the declaration commit's tree. Do not use a Git command.
- The rules your expectations come from: P05's contract `.../current-host-p05/CONTRACT.md` section 3; the 0.2.0 contract `.../macos-contract-design-p31/CONTRACT.md` sections 1, 8 and 9 (MC19, MC21).
- The blocker and its evidence: gate MR's freeze review `.../macos-routine-p36/reviews/freeze-review-001/FREEZE-REVIEW-001.md` (FZ-01, FZ-02), and the measurement `<local>/c271-p37/measure/MEASURE-001.json`.
- The precedent: MI's frozen controls, `.../macos-implementation-p33/CONTROLS-FROZEN.json` and `tests/test_current_host_readback_controls_v02.py` (their MC19 rows), for the format and the rules: expectations come from the contract; an implementation defect is corrected in the implementation, never in a frozen expectation.

## What to freeze
1. **Accepted, with real Git and the driver's own workspace preparation.** On the derived route, a fixture tree that tracks paths outside the copied set:
   - a regular file under a directory outside `SOURCE_DIRS`, as `.claude/.gitignore` is;
   - a symbolic link there, as `.claude/skills/*` are;
   - any other kind of tracked path that the copy leaves out, as the decision defines the copied set.
2. **Refused, each with its exact code and reason.**
   - On the derived route:
     - a copied file that is modified or deleted in the workspace;
     - a staged change;
     - a rename or copy line;
     - a quoted name;
     - an uncopied path that is present but changed;
     - an untracked input inside the copied set;
     - anything else that the contract refuses and the decision keeps.
   - On the original route: a deletion of an uncopied path, which still refuses.
3. **Unchanged acceptances.** The generated-example exclusion still holds on the derived route.
4. **FZ-02, if W1's decision changed the driver for it.** A control of the change's observable effect and of the summary fields that must stay unchanged.

For each control, freeze:
- the inputs;
- the entry point;
- the expected outcome: accepted or refused, with the exact code and reason;
- the expected process starts, for example Git only and no Node;
- its label: real, or simulated at a boundary.

Write each control as a test in your module. If a control fails against W1's implementation, record it as a finding for the Director, and do not weaken it. If you judge that the decision itself departs from the contract, record that as a finding too, with its basis.

## Rules
- **Running tests.** Run tests only from the worktree root, and only as `/usr/bin/env -i HOME="$HOME" LOGNAME="$LOGNAME" USER="$USER" PATH=/usr/bin:/bin TMPDIR="$(cd "$TMPDIR" && pwd -P)/" .venv/bin/python -B -m unittest <module> -v`. The modules are your own and W1's two focused modules. Record each run's command, times and result in your evidence directory.
- **Never:**
  - the complete suite, `tools/check_local.py`, or any other module;
  - a Git command that writes in the worktree;
  - Node, `ldd`, `codesign` or `otool`;
  - a download or an install;
  - Finder;
  - launching child agents.
- **Other starts.** Your scripts only under `python3 -I -S -B`. Your fixtures may start Git.
- **Changes.** Do not change W1's files. If you need a change there, it is a finding.
- **Privacy.** Your files may be copied into a public repository. Use labels for paths, and no user, personal or application names, not even split across constants.

## Return
At most about 250 words:
- your module's path and SHA-256, and those of `CONTROLS-FROZEN.json`;
- the controls in one line each;
- your test runs and their results;
- any finding against the implementation or the decision;
- what you started.
