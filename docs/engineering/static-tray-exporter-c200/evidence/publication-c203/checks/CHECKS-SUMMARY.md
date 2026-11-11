# C203 applicable candidate checks

**All selected checks passed.** The checks ran against candidate source `16c736c522c1f3684b5baabe6e72e56536ef08ce`, tree `278dcd3f8ba14fd3d632dbd92af33d5a8d5a998e`, using CPython 3.12.14 on Linux-6.18.57-x86_64-with-glibc2.41. Unlocked documentation/evidence was being prepared separately. The actual worktree status is retained in each runner receipt.

| Check | Fresh result |
| --- | --- |
| Focused static-tray source, reader, transaction and exporter controls | 107/107 methods passed; zero skips. |
| Construction compiler controls | 47/47 methods passed; zero skips. |
| C200 closed-schedule/protocol controls | 10/10 methods passed. |
| Core conformance | 43/43 cases passed; 694 assertions. |

All 301 files in the executed input lock matched before and after testing. Executable source, tests, tools and workflows match historical executed C200 source `62b2316cc3f88db187f69fbd7fdb2cf0997a97de`. The exact source list and hashes are in `TESTED-SOURCE-MANIFEST.json`.

## Exact pinned exporter source

The original dependency workspace was present. Both required files match their historical hashes: `io_scene_gltf2/__init__.py` (`82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e`) and `io/com/debug.py` (`a0112a1488ce1520f6554f1c337494845ab0aea9b683a73b0b747505d6a2fa94`). All five pinned-source abstract syntax tree controls therefore ran. No pinned-source test was omitted. Their bindings are in the focused runner's input/result receipts.

## Process accounting

The focused runner's introductory comment says it starts no subprocess, but two unchanged reader tests actually start eight isolated Python reader CLI processes. The audit hook recorded all eight plus three Git metadata reads. The compiler runner started three Git metadata reads. Protocol tests started no child. Exact child arguments are retained in the command receipts. No unexpected child was blocked.

No Blender construction, receiving process, Node checker, lifecycle stub, timed author or qualification run was started. C199 and C200 schedules remain closed. Core conformance ran directly through the ordinary Python CLI; its subprocess activity was not separately instrumented.

## Why the full legacy suite was not repeated

The observed remote main was `2cad7ecfece83295a3534d8afc97ab127a665ded`. Its runtime, schemas, conformance, grammar, tools and workflows have no differences from the tested candidate. The selected checks exercise the bounded static-tray increment and core behavior. This does not claim a fresh full-regression pass. The inherited full regression remains failed: 4,239 distinct passing methods and 13 torque-read methods not run after the unchanged 30,000 ms setup timeout.

## Review boundary

The final candidate may add unlocked documentation and evidence after this test source. Its independent exact-tree review must match `TESTED-SOURCE-MANIFEST.json` and verify that later changes stay outside the tested executable closure. Documentation/link validation is owned by the separate documentation reviewer. Full commands, interpreter/platform, source bindings, stdout/stderr and test logs are retained in this directory and indexed by `CHECKS-SUMMARY.json`.
