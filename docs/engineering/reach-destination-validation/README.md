# Focused destination arithmetic validation

This record tests code commit `02cb0abbcb9aff3f84ea80382642db4fe7390187`,
tree `d6615b476ad3de9e84fce9a92467cdbc9b07fd72`. Both attempts retained all
989 tracked file SHA-256 values and the same clean Git identity before and
after execution. The code uses CPython 3.12.14 and Node.js v24.19.0 on Linux
6.18.55 x86_64 with glibc 2.39. Exact commands, runtime identities, hashes and
raw output are preserved in each attempt.

## Observed result

[Attempt 001](attempt001/report.json) ran the eight pre-existing recording
arithmetic tests and twelve new resource/interruption probes. All twenty
Python tests passed, with no failures, errors or skips. Its `node --test`
command exited zero but reported only one file-level wrapper test. That Node
result is **incomplete evidence**, and is not counted as execution of the
eight registered JavaScript probes.

[Attempt 002](attempt002/report.json) preserves the narrow runner diagnosis.
An explicit TAP reporter still reported only the file-level wrapper. Direct
module execution, `node tests/reach_destination_resources.mjs`, actually
reported each of the eight named probes: eight passed, zero failed, cancelled,
skipped or todo. No NODE_OPTIONS, NODE_TEST_CONTEXT or NODE_TEST_REPORTER
override was present. The cause of the wrapper-only `--test` result is not
established; the raw insufficient results remain preserved.

The accepted focused result is therefore **20 Python tests plus 8 named Node
probes**, with unchanged committed implementation inputs. The Node probes use
lightweight scene objects. These checks establish the executed guarded numeric
leaf and playback invariants only. They did not execute the complete writer,
source lifecycle, Agent, SQLite, source-to-GLB, actual Three/native geometry,
browser, compatibility matrix or full release workflow. Those gates require
separate identified evidence. No whole-builder or release acceptance is inferred.
