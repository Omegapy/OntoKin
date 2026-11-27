# C271-P35 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-27 (UTC), after the qualifying cohort and its
independent audit.

**Four supported lessons, captured** in [memory](../../../workflow/memory.json). Each record names
its evidence and its limits.

- **`memory-c271-executable-outer-bound`.** A frozen time limit must be one the actual executor can
  carry out.
  - The case: freeze 001 said that a command past its limit is interrupted once with Ctrl-C.
    Claude Code's shell tool has no terminal, blocks the Director in foreground mode, and ends a
    foreground command at its own timeout of at most 600 s.
  - The method that worked:
    - each command is launched alone in background mode, beside a frozen bound timer that only
      waits for the exit file;
    - at the bound, the outcome is UNKNOWN, the recorded starts are probed, and only processes
      whose identity is established may be stopped;
    - nothing is ever sent to the command or its group.
  - Evidence: [freeze review 001](reviews/freeze-review-001/FREEZE-REVIEW-001.md) (FR-01), its
    [disposition](reviews/FREEZE-REVIEW-DISPOSITION-001.json), [freeze 002](plans/freeze-002/FREEZE-002.json),
    and the 72 [launch lines](director/s7/LAUNCH-LINES.json) of S7.
  - Limits: the shell tool of the desktop app on macOS. No command overran, so the overrun steps
    themselves were never exercised.
- **`memory-c271-evaluate-listing-probe-predicates`.** A capture tool that exits 0 whatever it
  records checks nothing by itself.
  - The fix: each of the listing's and the probe's predicates is evaluated by a frozen step before
    the next start. Here they were appended to the main command's expectations, which its checker
    step evaluates.
  - Evidence: [freeze review 001](reviews/freeze-review-001/FREEZE-REVIEW-001.md) (FR-02), the
    [difference record](plans/freeze-002/FREEZE-002-DIFFERENCES.json) and [the audit](audit/AUDIT-001.md).
- **`memory-c271-portable-copies-ignored-names`.** The repository's `.gitignore` matches `*.log`
  and `ENV/`.
  - On macOS's case-insensitive file system, `ENV/` also matches `env/`.
  - Portable copies with those names stay untracked unless they are added with `git add -f`, as
    earlier evidence logs were. Here 29 copies were affected.
  - Evidence: [EXACT-RECORDS.json](EXACT-RECORDS.json) and the commit that carries this record.
- **`memory-c271-privacy-scan-scripts-stay-local`.** Workers' privacy-scan scripts often hard-code
  the terms they search for.
  - They stay beside the clone, recorded by digest. Only labelled reports, and scripts that derive
    their terms at run time, are committed.
  - A plain search misses split literals, so each Python file's joined string constants are
    searched as well.
  - Evidence: [README-PORTABLE.md](README-PORTABLE.md), [EXACT-RECORDS.json](EXACT-RECORDS.json)
    and plan review 001's [disposition](reviews/PLAN-REVIEW-DISPOSITION-001.json) (PR-06).

**Considered and not captured:**
- **The launch deviation (AU-01)** is a one-off slip in this session, recorded in the
  [audit](audit/AUDIT-001.md) and [the outcome](OUTCOME.json).
- **The simulated MC10 receipts (AU-03)** and **the missing MC37 receipt (AU-02)** are properties of
  this gate's tooling. They are recorded in the audit and the outcome for MR, and are not general
  lessons.
- **The extra Node start for MC30-probe** is a design decision of this contract. It is recorded in
  the freeze and the outcome.

No lesson claims anything beyond this executor, this contract, or the inputs that MH exercised.
