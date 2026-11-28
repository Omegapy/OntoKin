# W1-correction: starts and deviations (C271-P37, S3)

Times UTC. Labels: `<worktree>` the C271 worktree; `<local>` the data root beside the clone.

## Deviations

- D-1. Before identifying the framework interpreter, W1 started the operating system's Python
  launcher `/usr/bin/python3 -I -S -B -c <program>` four times, to print members of three JSON
  records in `<worktree>` (the 0.2.0 contract's CONTRACT.json, P05's CONTRACT.json and MI's
  CONTROLS-FROZEN.json). The programs only opened those files for reading and printed; `-B` was
  given, so no bytecode was written. From then on, own scripts run as `python3 -I -S -B`, which
  resolves to the framework interpreter (<package-manager>'s Python 3.12, 3.12.13).

- D-2. W1 started Git by name (the `/usr/bin/git` dispatcher) in `<worktree>` four times outside any
  test fixture, which the assignment does not allow: at about 23:26Z `git status --short`,
  `git rev-parse HEAD` and `git branch --show-current` (one shell call), and at about 23:37Z
  `git -C <worktree> status --porcelain=v1`. All are reads. They showed a clean tree, head 2f728998
  and the assigned branch. The worktree's index file still has its modification time of 23:17:39Z,
  from before this session, so no status refresh wrote it. From then on W1 starts no Git outside its
  tests' fixtures.

## Starts

- 2026-11-27T23:34:34Z python3 -I -S -B index_scope.py (own script, scratchpad): read the measured workspace's .git/index and the worktree's tools/check_local.py; wrote index-scope-declaration-commit.json here. No Git start.
- Throughout: shell utilities (ls, cat, sed, grep, wc, shasum, stat, date, mkdir) and `python3 -I -S -B`
  for short read-only programs that print JSON members or edit this evidence directory's own files.
- 2026-11-27T23:40:22Z python3 -I -S -B parent_proof_timing.py (own script, scratchpad; one earlier start failed at its import, before reading anything): read the measured workspace's .git/index; wrote parent-proof-timing.json here. No Git start; no copied file read.
- 2026-11-27T23:53:14Z python3 -I -S -B compare.py (own script, scratchpad): read the base copies in the measured workspace and the worktree's files; wrote CHANGES.diff and COMPARISON.json here. No Git start.
- 2026-11-27T23:53:58Z python3 -I -S -B mutate.py (own script, scratchpad): ten one-text mutations of W1's two implementation files, each followed by one prescribed test run (runs/mutation-NN) and a restore checked by SHA-256; MUTATIONS.json here.
- 2026-11-28T00:03:58Z python3 -I -S -B mutate.py again, on the final bytes after a docstring-only edit of tools/check_local.py; the first round's records are kept as MUTATIONS-draft-before-docstring-edit.json and runs/mutation-NN-draft.log.
- 2026-11-28T00:08:49Z python3 -I -S -B compare.py again on the final bytes; CHANGES.diff and COMPARISON.json rewritten.
- 2026-11-28T00:10:59Z python3 -I -S -B mutate.py, third round, on the final bytes of all four files (the provider test module now writes one non-ASCII letter as its escape sequence); the second round is kept as MUTATIONS-round2-before-escape-edit.json and runs/mutation-NN-round2.log.
- 2026-11-28T00:14:56Z python3 -I -S -B compare.py a third time, on the final bytes; CHANGES.diff and COMPARISON.json rewritten.

## Test runs

Every test run used the prescribed command from `<worktree>`; `runs/RUNS.jsonl` records each one's
command (with labels for the account values and the temporary directory), start and end time, exit
status, result line, log and log digest. Labels: `base-` before any change; `impl1-`, `dev1-`,
`final-` and `closing-` during the work; `mutation-NN-draft`, `mutation-NN-round2` and `mutation-NN`
for the three mutation rounds; `last-` on the final bytes. Every run passed except the mutation runs,
each of which failed as intended.

## Privacy

The logs of the mutation runs (`runs/mutation-*.log`) hold machine paths in their tracebacks. A
portable record cites only their digests. No other file here holds an account or machine path.

## Never started

Node, `ldd`, `codesign`, `otool`, the routine driver as a program, the complete suite, any other test
module, a download or install, Finder, or a child agent. No Git command wrote in `<worktree>`.
