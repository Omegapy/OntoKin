# C271-P34 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-26 (UTC), after the preparation and its
independent result review.

**Three supported lessons, captured** in [memory](../../../workflow/memory.json). Each record names
its evidence and its limits.

- **`memory-c271-pipless-exact-venv`.** To give the qualification `.venv` exactly its seven
  pinned distributions and no pip, install the hash-locked wheels with the base interpreter
  installation's pip, through `--python`.
  - Settings: offline, with `--no-compile`, no bytecode, and a declared environment.
  - Why: the setup tool installs through the venv's own pip, which would stay in `site-packages`,
    and M0 refuses it.
  - Evidence: [the plan](PREPARATION-PLAN.md), sections 3 and 7, the exact check in
    [run-001](run-001/venv-verify-002.json), and [the result review](reviews/RESULT-REVIEW-001.md).
  - Limits: CPython 3.12.13 with pip 26.0 on macOS arm64; observed once.
- **`memory-c271-preparer-dry-run-report`.** The 0.2.0 preparer writes its report on a dry run
  too, and every run needs an absent report path. A dry run and its application therefore need
  plan variants that differ only in `report`.
  - Evidence: [DRY-RUN-VARIANTS](plans/DRY-RUN-VARIANTS.json) and W1's
    [notes](plans/AUTHOR-NOTES.md).
- **`memory-c271-reviewed-digest-binding`.** Pass the reviewed digests of exact plans as recorded
  values. A digest recomputed from the plan file at run time makes the frozen-digest check vacuous.
  - Evidence: [PLAN-REVIEW-001](reviews/PLAN-REVIEW-001.md), finding P-07, and the
    [run log](run-001/00-steps.txt).

**Considered and not captured:** the Director's own check script failed once, on PEP 508's
single-quoted markers ([the rerun record](run-001/venv-verify-rerun.md)). It is a local defect of a
one-off script, and it is recorded where it happened.
