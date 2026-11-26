# C271-P31 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-26 (UTC), after the adoption of the design.

**One supported lesson, proposed and not captured.** Before designing around a runtime's sandbox
or permission feature, check how it interacts with every flag and call that the bound code
already requires. Here, Node's permission model looked like a clean replacement for Linux's
child-subreaper guarantee. It turned out to be unusable for this probe: under the model, the
probe's `--experimental-loader` needs a worker grant, workers do not inherit the model, and
descriptor `fsync`, which the preserved probe calls, is disabled.

- Evidence: [INDEPENDENT-REVIEW-001](INDEPENDENT-REVIEW-001.md), finding G-01, and the Node.js
  `v24.22.1` permissions documentation listed in the [read set](READ-SET.json).
- Applicability and limits: designs that add a sandbox to existing bound code. It rests on one
  design and one runtime version.
- A second, smaller observation: on macOS, CoreFoundation adds `__CF_USER_TEXT_ENCODING` to the
  environment of any process that loads it, so exact-environment checks need an explicit
  allowance there (G-13).

**Capture.** Not captured in this phase, for the reason C271-P30 recorded:
`docs/workflow/memory.json` is one of the six files in conflict with main. These lessons are left
for capture at or after the merge of gate MB or R04, together with P30's and R07's.
