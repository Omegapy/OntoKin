# Agent/0.5 local integration evidence

This record establishes the routine Agent/0.5 checkpoint on identified source
under [OK-ENG-006](../OK-ENG-006-local-validation-and-hosted-ci-policy.md).
It implements the integration gate in [OK-AGENT-005](../OK-AGENT-005-finite-force-program-workflows.md),
not the complete force release. [Validation metadata](validation.json) binds the
executions and retained files; [integration metadata](integration.json) records
the resulting main separately. [PR #16](https://github.com/Omegapy/OntoKin/pull/16)
preserves the owned scope and investigation checkpoints.

## Identified passing execution

The complete run used actual published commit
`0d56b255a9e813e92bacba0c4cf5891a2481bca3`, tree
`04f9f7029dcc85ab7e43fede69a572b45bfed232`. Its isolated workspace retained
that exact commit and tree with an independent Git index. All **623 original
input files** and the original source Git revision remained unchanged.
The runtime and frozen language fixtures are byte-identical to the preserved
Agent branch at `2f08ff2858a5fca3aac7cff95b3aa1ebdd823f1c`.

The run completed at **2026-10-19T18:11:01Z**, with exit **0**, in
**427.837 seconds** on **CPython 3.12.14 / Linux x86_64 / glibc 2.39**.
The standard-library SQLite version was **3.53.1**. The unchanged application
runtime is `ontokin-reference` 0.4.0, SHA-256
`ad1c473a595dc1147bfeef10330a39bbffb33cd68cc236ec70fc12b445e720ea`.

| Executed role | Actual result |
| --- | --- |
| Complete local plan | 11/11 steps passed |
| Full regression suite | 753 tests, zero failures, errors, skips or expected failures |
| Dedicated Agent/0.5 cohort | 56 tests, zero skips; these methods are also included in the full suite |
| Original source conformance | 43 cases / 694 assertions passed |
| Original Agent operations | Standalone A01–A10 passed |
| Construction, surface and impulse | All three local commands passed; their external release attestations remain explicit |
| Actual Agent/0.5 recording | 418 exchanges, 25 immutable source snapshots, 334 predetermined samples across 22 positive programs |
| Independent source/message/schema audit | Passed, including 411 complete force projections |
| Documentation preservation | 29 historical sources and 233 sections verified, with no preservation/link failures |

The six exact verification-only package versions and download hashes are retained
in [prerequisite provenance](prerequisites/pip-install.json). Runtime dependencies
remain Python's standard library. The raw driver summaries retain their own
`remote_head_verified: false` values: separate
[remote observations](supplemental/candidate-remote-observations.json) supply
the connector verification rather than silently rewriting a local result.

## Preserve the unsuccessful attempts

The [first attempt](failed-attempt.tar.gz) used `04e4f78d…` and exited 1.
Its full suite ran 725 methods with three class-setup errors; 24 intended
methods did not execute. Existing surface/impulse builders required Git identity
that the isolated workspace lacked when evidence was outside the repository.
The driver now preserves the actual source commit/tree in independent local Git
metadata, including copied dirty/untracked bytes, without copying credentials,
configuration or the source's mutable index. Twenty focused driver tests and a
previously failing five-test impulse workflow passed before the full rerun.

The [second attempt](failed-attempt-2.tar.gz) used `0d56b255…` and also exited 1.
All 753 regression and 56 dedicated Agent tests passed, but the standalone
recorder failed at request 0298 because its durable request row was absent.
It retained 297 completed exchanges, 17 snapshots, 251 sample roles and the
unpaired request. The independent audit was correctly blocked. Earlier success
receipts and an accepted project/run were also missing from the closed store.

The [storage investigation](diagnostics/storage-investigation.json) and
[closed-store observation](diagnostics/storage-failure-observation.json) retain
the distinction between observed facts and inference. A fresh, sequential
production-store probe reproduced lost rows without Agent evaluator or workflow
logic, and observed the main database inode change with a regressing timestamp.
A separate executor read overlapped that probe. Concurrent executor/filesystem
synchronization is consistent with the observation; the replacing environment
component remains unidentified. SQLite documents the risks of
[replacing an open database file](https://sqlite.org/howtocorrupt.html#unlinking_or_renaming_a_database_file_while_in_use).

With other executor/filesystem activity paused, the unchanged normal-WAL probe
passed 2,500 cycles with a stable inode. The complete
[passing attempt](passing-attempt.tar.gz) then ran under that same discipline:
only session-output polls and remote PR/UI updates occurred while it executed.
The suite's own concurrency and transaction tests ran unchanged. No runtime,
journal-mode, source-fixture or tolerance change was made to obtain a pass.
This is evidence for the stated execution conditions, not a claim that the
unidentified environment defect is repaired.

## Retention and reproduction

The three compressed archives preserve raw summaries, before/after inventories,
commands, logs, reports, source bundles and recorded request/response bytes.
Their member manifests and [retention verification](retention-verification.json)
identify every member and permit an independent standard-library integrity check:

```sh
python3 reproduction/verify_retained.py
```

Run that command from this directory. Exact executed packaging scripts and
command records are retained under `reproduction/`; the original environment
paths are provenance, not required destinations for a new project run. Mutable
SQLite stores, Git workspaces, caches and installed packages are excluded.
The [separately recovered historical archive](../force-agent-validation/README.md#historical-archive-recovery)
keeps its original hosted execution and later re-audit distinct from all three
fresh local attempts. The original `CHECKPOINT.json` remains unchanged.

For a new acceptance run, prepare the pinned packages as described in the
[Agent verification guide](../force-agent-validation/README.md), then run:

```sh
python3 tools/check_local.py --force-agent --output-dir /tmp/ontokin-agent05-checks
```

Use a new output directory and a filesystem that retains live SQLite identities.
In this executor environment, pause other executor/filesystem calls while the
validation process runs. Do not reuse these archived receipts as a fresh run.

## Limits and next gate

Sixteen external attestations remain pending in the inherited current conformance
reports. This run does not establish a Python 3.11/3.13 matrix, macOS, fresh browser
review, or a complete release. No hosted workflow was dispatched or retried;
both current workflow definitions are manual-only with default-false job opt-in.
Repository-wide Actions settings and historical branch workflows were not changed.

Agent/0.5 supports explicit finite-force discovery, inspection, atomic
mass/force/duration repairs, isolation, retries, cancellation and bounded failure.
GLB/0.5 requests still fail without an artifact. The next bounded component is
the acceleration-aware recorded GLB/0.5 adapter. The preserved dependent branch
`work/glb05-native-forces-20261019-1315-astra` at `18cea63b…` publishes only its
engineering contract; implementation and verification remain pending. Its
OK-ENG-006 identifier conflicts with the adopted local policy and must be
reconciled explicitly when that contract is integrated. F01–F12 and the full
[product goal](../../../GOAL.md) remain open.
