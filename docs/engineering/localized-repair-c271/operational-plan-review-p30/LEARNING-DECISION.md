# C271-P30 learning checkpoint

Assessed under the ontokin-learning skill on 2026-11-26 (UTC), after the reviewed outcome of
this phase.

**One supported lesson, proposed and not captured.** A host contract whose pins are the bytes
of an ephemeral provider runtime can have no executor once development moves to another
execution mode. Here the pins are the Codex runtime's Node `v24.22.1` build and its CPython
3.12.14 image, observed only on disposable browser-thread hosts. Before designing or extending
host-specific tooling for such a contract, compare its pinned inputs with the executors that the
session's mode actually has.

- Evidence: this phase's [executor inventory](EXECUTOR-INVENTORY.json),
  [contract requirements](CONTRACT-REQUIREMENTS.json) and [review](REVIEW-OUTCOME.md), sections
  1 to 3; P05's [contract](../current-host-p05/CONTRACT.md), section 4.
- Applicability and limits: host-bound qualification contracts. It rests on one task and one
  local host, and it establishes no general rule about whether test results depend on the
  platform.
- Duplicate check: `tools/chat_workflow.py lookup executor` and `lookup host` on main found no
  record that covers it. MEM-006 is the hosted-CI policy constraint.

**Capture.** Not captured in this phase. `docs/workflow/memory.json` is one of the six files
that main and this branch both changed ([MAIN-CONFLICTS](../p29-local-publication-r07/MAIN-CONFLICTS.md)),
and this phase's plan changes no memory record. The lesson is left for capture at or after R04,
together with R07's lesson that an error from a text-only reader does not establish that an
object is absent.
