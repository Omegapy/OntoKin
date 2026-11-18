# C264 implementation plan

Owner: `c264-root-c3681d8a01ea`. Branch: `work/c264-required-browser-handoffs`. Base: `727cc298cd9862f53684061a34e9e41a8ec8cd06`. [Scope254](https://github.com/Omegapy/OntoKin/issues/254). [Machine-readable progress](task.json).

## P01. Record clarified requirements and inspect authoritative sources

Requirements: R01, R02, R06.

Outputs: `docs/workflow/tasks/C264/REQUIREMENTS.md`, `docs/workflow/tasks/C264/PLAN.md`.

Verification: Read current GitHub workflow and C262 root controls; resolve the existing Library folder.

## P02. Write both prompts and align current delivery and recovery instructions

Requirements: R01, R02, R03, R04, R05.

Outputs: `docs/workflow/BROWSER-PROMPTS.md`, `docs/workflow/HANDOFF.md`.

Verification: Independent review of ordinary continuation, crash recovery and delivery-only recovery.

## P03. Verify workflow documentation and preserved boundaries

Requirements: R03, R04, R05, R06, R08.

Outputs: `docs/engineering/browser-handoff-c264/RESULTS.md`.

Verification: python3 tools/chat_workflow.py check --json; python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py; Independent prompt/package inspection.

## P04. Integrate the reviewed instructions and verify actual main

Requirements: R04, R08.

Outputs: `docs/engineering/browser-handoff-c264/INTEGRATION.json`.

Verification: Observe exact merge, recheck current main and completed-branch absence.

## P05. Create and save session handoff and prompts, record delivery and stop

Requirements: R05, R06, R07, R08.

Outputs: `docs/engineering/browser-handoff-c264/DELIVERY.json`.

Verification: Verify exact ZIP member manifest, extraction, frozen GitHub files and saved artifact identity.

## Delivery order and interruption handling

Publish requirements and this plan before implementation. Preserve a GitHub checkpoint before long work. Integrate the reviewed instructions with delivery still outstanding, create and verify a frozen session ZIP at the observed main revision, save it and the prompts, then publish the external delivery receipt and close the task. The ZIP cannot contain its own future save receipt; its checkpoint must explicitly retain that boundary. A delivery-only closure commit does not require recursively rebuilding the ZIP. Read live GitHub to reconcile it.
