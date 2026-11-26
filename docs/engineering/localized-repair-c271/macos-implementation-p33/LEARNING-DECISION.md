# C271-P33 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-26 (UTC), after the final verification and
the independent review of gate MI.

**Five supported lessons, captured** in [memory](../../../workflow/memory.json). Project memory
was reconciled with main at gate MB, so they can be captured now (C271-P32's session checkpoint).
Each record names its evidence and its limits.

- **`memory-c271-frozen-companion-check`.** Before a plan gives an existing test file to a worker,
  search the test modules for runtime freezes of companion bytes.
  - Evidence: [D-18](DIRECTOR-DECISIONS.md#d-18-the-driver-test-file-stays-p29s-frozen-companion)
    and the first run in [CHECKS](CHECKS.json). C271-P29's required-images controls refused to
    load after this phase's sanctioned change to one of their 24 companions.
  - Limits: frozen control sets that authenticate companions when they load; observed once.
- **`memory-c271-facade-binds-version`.** A facade that dispatches between contract versions binds
  the version once per transaction, at its start, and does not decide it again at every call.
  - Evidence: finding I-01 of [INDEPENDENT-REVIEW-001](INDEPENDENT-REVIEW-001.md), its fix in
    [D-20](DIRECTOR-DECISIONS.md#d-20-the-dispositions-of-independent-review-001), and the control
    added in [CONTROLS-REFREEZE-002](CONTROLS-REFREEZE-002.json).
  - Limits: the readback provider's versioned facade; observed once.
- **`memory-c271-platform-metadata-starts`.** On macOS, CPython's `platform.platform()` starts
  `uname -p` and `file -b` on its first call in a process, and caches the answer.
  - Consequence: a control that counts every process start depends on test order unless it
    isolates this metadata leaf.
  - Evidence: [D-19](DIRECTOR-DECISIONS.md#d-19-two-control-defects-returned-to-w6-for-a-refreeze)
    and [CONTROLS-REFREEZE-001](CONTROLS-REFREEZE-001.json).
  - Limits: CPython 3.12.13 on macOS 26.6.2 arm64. Earlier Linux tests stubbed the same call
    (`113e1b85`).
- **`memory-c271-darwin-killpg-eperm`.** On Darwin, `killpg(pgid, 0)` answers EPERM while a
  group's members have exited but are not yet reaped, and ESRCH after reaping.
  - Evidence: [AMENDMENT-001](AMENDMENT-001.md), the direct probe's
    [output](evidence/zombie_group_probe.out.json), and control MC37 in the final verification.
  - Limits: one host and one OS build.
- **`memory-mock-call-environment-leak`.** When a unittest assertion on a mocked
  `subprocess.Popen` fails, its message prints the recorded calls' `env` argument, which is the
  parent process environment.
  - Evidence: the redaction note in [CHECKS](CHECKS.json). Two of this phase's working logs held
    such dumps. They were redacted, and none was published.
  - Limits: tests that assert on a mocked `Popen` called with an environment.

**Not captured here:** the lessons that R07, C271-P30 and C271-P31 left for later capture. Their
sources must be checked again before they become current records, and that is outside gate MI's
objective. They stay proposed in those phases' learning decisions.
