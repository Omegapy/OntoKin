# Git LFS storage preparation: measured validation

October 28, 2026. This is a separate verification-tool increment based on C059 candidate `4155acfd1b01e1b72aac23be5e28b054d2e10440`. Working changes are disclosed and individually hashed in the execution receipts. The main integrator records publication and resulting-main identities separately.

## Final focused result

[Attempt 006](attempt-006/receipt.json) passed **15 dedicated storage tests** and **21 local-driver tests**, with zero skips or expected failures. Both logs are retained: [storage](attempt-006/execution-001.log) and [local driver](attempt-006/execution-002.log). All nine captured source/workflow/attribute files remained unchanged during this execution.

The environment was CPython 3.12.14 and Git LFS 3.8.1. The [client acquisition record](git-lfs-client-verification.json) binds the official release archive and executable hashes. The published checksum matched; a PGP signature check was not performed. The client was prepared in a task-local directory; no global installation/configuration change or executable binary is committed here.

The tests use actual temporary Git repositories, canonical pointer commits, hydrated payloads, isolated private LFS object caches, and strict original-byte verification. Negative checks cover missing/unhydrated/corrupt payloads, unsupported pointer forms, ordinary-file mismatches, ambient/uncommitted attribute overrides, unconverted tracked archives, dirty or already-configured migration inputs, unauthorized extra migration paths and an unrelated committed gitlink. The local-driver suite preserves existing failure propagation, source isolation, timeout, no-skips and pending-provider behavior, and verifies that future tracking rules with zero payloads require no Git LFS client.

No product runtime, SQLite store, new geometry/animation run, hosted CI job, authenticated upload or remote LFS fetch was executed by these checks. The local fixture conversion does not establish that private GitHub objects are available. These tests establish the scoped storage behavior, not a new runtime release or a rerun of C059's full suite.

## Preserved iterations

[Attempt 002](attempt-002/receipt.json) passed ten earlier storage tests; [attempt 003](attempt-003/receipt.json) passed thirteen storage and twenty local-driver tests before the migration verification and workflow-hydration changes. [Attempt 004](attempt-004/receipt.json) passed thirteen and twenty with that verifier; [attempt 005](attempt-005/receipt.json) passed fourteen and twenty after the independent review identified and closed a gitlink omission in exact-tree verification. Their receipts retain their original inputs and should not be attributed to later bytes. Attempt 006 additionally covers the restricted bootstrap tracking configuration.

The inherited development handoff reported an earlier ten-test attempt with one test-fixture error and one hook-isolation failure. That raw failed log was not present in the recovered workspace, so this record does not invent an execution receipt for it. The finalized implementation disables hooks in isolated repositories; the real-client test now verifies that no hook files, remote configuration or credential-helper configuration are copied/installed. It also fixes the local preflight fixture to copy the newly required helper module. These development fixes do not change product behavior.

The dedicated Git LFS suite lives under `tools/storage_tests` so the default core suite remains independent of the additional client. Both manual workflows received only `lfs: true` on their existing checkout steps. Attempt 006 confirms that removing those three added lines reproduces their original bytes exactly; dispatch triggers, default-false opt-in and job guards remain unchanged.

## Publication boundary and next action

[OK-ENG-010](../OK-ENG-010-git-lfs-archive-storage.md) contains the storage contract and exact no-rewrite procedure. The committed root `.gitattributes` activates future tracking only beneath the unused `docs/engineering/lfs-archives/` directory. The recorded bootstrap check confirms zero current matched payloads and exact rule bytes. No archive replacement, repository pointer, remote upload or billing change is included. The planner and verifier write only new external evidence directories.

Actual conversion requires an authenticated Git/LFS executor. After the selected main integration, regenerate a plan from the exact clean main, convert only its recorded archive paths, upload their objects before publishing the pointer branch, and independently fetch/hash them from an empty cache. Integrate that verified storage commit through the current lease/expected-head procedure. Preserve all historical commits, archive parts and their member manifests.

[The retained-member inventory](retained-inputs.json) binds the earlier execution receipts, logs and client provenance as originally copied. Later attempts and final documentation/patch checks have their own separately bound records. The original documentation check remains attributed to the earlier narrative; it is not overwritten by the final check.
