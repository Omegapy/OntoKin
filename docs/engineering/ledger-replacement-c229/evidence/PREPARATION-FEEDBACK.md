# C229 pre-run review feedback

No product run, import, filesystem replacement probe or native process was executed by the reviewer. These findings were raised while the author's first harness draft was still being prepared; they do not consume a diagnostic slot and are not product failures.

## Required preparation corrections

- The worker's environment report called `platform.platform()` after installing its no-child audit hook. In the installed CPython 3.12 standard-library `platform.py`, `platform()` unpacks `uname()`, whose lazy processor field falls back to `subprocess.check_output(['uname', '-p'], ...)` on this Linux path. That could attempt a forbidden child before the worker's protected execution block. Use non-spawning `os.uname()` fields.
- The launcher must reconcile top-level unittest failures with the recorded failed subtests. Otherwise an extra method-level failure could be ignored merely because ten subtest callbacks occurred. The finite follow-up is permitted only after the original expected failure class or a clean isolated pass, with all outcomes accounted.
- Observed-case completion must require explicit successful closure of retained original-file descriptors, in addition to child exit and reaping. A completed count alone does not establish this cleanup.

## Interpretation requirements sent to author

Use fresh temporary locations on the workspace filesystem for both slots; C228 used its workspace `aggregate-run/tmp`. Record the new placement and filesystem facts, without claiming historical allocator equivalence. Capture nested `PERSISTENCE`/`INTEGRITY` causes. Run one poison check only after an initial rejection; a second call after a successful reservation tests stage order rather than replacement rejection. Retained-descriptor conditions are explicit interventions and must remain separate from the no-held-descriptor observations and original method replay.
