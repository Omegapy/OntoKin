# W2-controls: starts and deviations (C271-P37, S4)

Times UTC. Labels: `<worktree>` the C271 worktree; `<local>` the data root beside the clone. W2 is the
independent control author for Director `c271-p37-08beec34eb0a`.

## Deviations

- D-1. At about 00:25:20Z W2 started the operating system's Python launcher once, as
  `/usr/bin/env -i PATH=/usr/bin:/bin /usr/bin/python3 -c "print(1)"`, to check an interpreter path. It was
  not under `-I -S -B`, as the assignment requires for W2's scripts. It printed `1`, read and wrote no file,
  and imported no project code.
- D-2. In the same shell call, from `<worktree>`, W2 started `.venv/bin/python -I -S -B -c "import sys;
  print(sys.version, sys.executable)"`: the checkout's interpreter outside the prescribed test command. It
  imported no project code; `-B` was given, and no bytecode exists in `<worktree>` afterwards (checked with
  `find` at the final runs).
- D-3. At 00:55:55Z the run `final-combined` passed the three module names as one argument, because the shell
  (zsh) does not split an unquoted variable. unittest reported one import error and ran no test. It is kept in
  `runs/RUNS.jsonl`; `final-combined-2` is the run with the names given separately.

## Starts

- About 00:25Z: `which python3` and `python3 -I -S -B -c` (the framework interpreter, 3.12.13) to print its
  version; D-1 and D-2 above.
- 00:26:18Z `python3 -I -S -B exploration/explore_git.py`, from `env -i` with `PATH=/usr/bin:/bin`: Git only,
  in a fresh temporary directory, never in `<worktree>` (version, init, add, commit, fetch, update-ref,
  read-tree, update-index, status, ls-files, rm --cached, reset, ls-tree, rev-parse). It learned the Git
  version, porcelain quoting, the index's stat data after read-tree and after a refresh, and two status forms.
  Output `exploration/explore_git.out.json`.
- 00:37:27Z `python3 -I -S -B exploration/explore_path_wrapper.py`, the same way: Git only, in a fresh
  temporary directory, through a logging wrapper placed first on `PATH` (no recursion through the
  dispatcher: three starts, three log lines).
- Throughout: shell utilities (ls, cat, sed, grep, head, tail, wc, shasum, diff, find, date, mkdir, cp) and
  short `python3 -I -S -B -c` programs that read records and printed members (MI's CONTROLS-FROZEN.json and
  CONTROLS-REFREEZE-001.json, W1's MUTATIONS.json, MR's OUTCOME.json, the standard library's subprocess.py
  path) and an `ast` listing of W2's module. W1's changes were read with `diff -u` against the declaration
  commit's copy in `<local>/c271-p37/measure/prep-001/workspace`; no Git command ran for that.
- Test runs, each with the prescribed command from `<worktree>` (`runs/RUNS.jsonl` has the command with
  labels, times, exit, result, log and log digest):
  - 00:47:30Z `draft1-derived-controls`: 45 tests OK (an earlier version, before P37-C24 and the evidence lines);
  - 00:51:02Z `draft2-derived-controls`: 46 tests OK (the final bytes);
  - 00:54:14Z `final-derived-controls`: 46 tests OK;
  - 00:55:19Z `final-local-checks`: 39 tests OK; 00:55:28Z `final-provider-v02`: 64 tests OK;
  - 00:55:55Z `final-combined`: D-3; 00:56:12Z `final-combined-2`: the three modules together, 149 tests OK.
- After each run, `python3 -I -S -B scripts/record_run.py` appended its record to `runs/RUNS.jsonl`.
- 01:01:48Z, 01:02:21Z and 01:02:35Z `python3 -I -S -B scripts/build_controls_frozen.py`: it read the module
  statically (ast), cross-checked it with the frozen table and wrote
  `<worktree>/docs/engineering/localized-repair-c271/derived-workspace-p37/CONTROLS-FROZEN.json`; the third
  writing is the record. Between the first two, one `sed -i` edited that script's own text.

## What the controls start

Inside the test runs: real Git for the fixtures (the Git on `PATH`, by absolute path), the logging `/bin/sh`
wrappers that exec it, and the exact-line stand-in (`/bin/sh`, then `cat`). Controls c07, c34, c63 and c64 call
`tools.check_local.run` in the test process with a substituted plan; c34's and c64's planned Python step never
started (each control asserts it). Every Git start of the code under test ran in a temporary directory.

## Never started

Node, `ldd`, `codesign`, `otool`, the routine driver as a program, the complete suite, any module other than
W2's and W1's two focused modules, a download or install, Finder, or a child agent. No Git command ran in
`<worktree>`, and W1's files were not changed (their SHA-256 at the final runs equal W1's reported values).
