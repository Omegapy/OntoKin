# C074: configurable execution budgets in the Agent lifecycle

This bounded increment implements the [C073 next task](../source-execution-budgets-2026-10-29-c073/NEXT-TASK.md) under [OK-AGENT-007/0.1.0](../../language-design/agent-v0.7/ADOPTION.md). It starts from actual main `f674eabec793e2dd31c9057a960bff7228a314cf`, tree `327115bc9e0b04af4ee339a3d4cb82fc1fb1ec77`. Worker `interactive-agent-execution-budgets-20261030-c074-2a264aad` owns branch `work/agent-execution-budgets-20261030-c074`; [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6525604559) declares the scope after C073 closure. Current [STATUS](../../../STATUS.md) remains the integration authority.

## Implemented scope

`BudgetAgentService` supplies explicit Agent/0.7 without registering a new route in the frozen earlier program-binding maps. Its separate database and protocol retain durable request IDs, exact source snapshots, accepted revisions, cancellation and transaction fencing. Source requests and JSON caps cannot create host policy. Each worker snapshots current policy and owns a fresh provisional ledger; all later work consumes that same counter and original deadline. Earlier defaults remain unchanged.

The new service supports all twelve operations, including actual source edits, saved-program/run authorization, requested-prefix delivery, chunk retrieval and mesh pages. Edits use exact byte spans in `['sources', source_id]` file scopes. A complete source-derived object identity map is committed with each accepted program; it permits safe comparison after a header repair without rerunning the old source. Rejected delivery cannot report an uncommitted artifact or a delivered level. A failed host clock preserves the original exception and retains a bounded cancellation receipt using the last established time.

See the [debit map](DEBIT-MAP.md), versioned [request/response schemas](../../language-design/agent-v0.7/README.md), and [next capability task](NEXT-TASK.md). This is experimental development, not complete reach or full-product release acceptance.

## Verification procedure

New tests cover the five deferred cases EB15, EB16, EB18, EB24 and EB29. `tools/run_budget_agent_acceptance.py` uses exact frozen C073 source/expected hashes and executes discovery, create, failed edit, repair, evaluation, saved-policy rejection, caller reduction, export, actual artifact retrieval, retries, cancellation and hostile input. Independent destination verification uses the retrieved bytes, `tools/verify_budget_glb.mjs`, pinned Khronos/Three.js/Chromium and actual visual review.

The relevant full local-driver run is `python3 tools/check_local.py --force-agent --timeout 1800 --output-dir OUTSIDE_CHECKOUT`. The increased test-process timeout does not change any product budget. Source inventories and actual Git identities must remain unchanged during that run. Exact runtime candidate, complete results, failed attempts, reviews and resulting-main checks are recorded in later files in this directory; this initial record asserts no completed full suite or merge.

Mutable test databases run on host-local temporary storage. Evidence is copied as closed SQLite backups, and the complete protocol transcript is written once after execution. Earlier development attempts with incomplete saved transcripts or request state remain failures of evidence collection and must not be relabeled as accepted workflow evidence. The independently verified source packet and historical files are retained unchanged.

## Preserved obligations

Original28 remains 24/28 failed, with P11/P16/P23/L03 unresolved at their original settings. M1 remains rejected; comparison accounting and passive authority remain open. C035 remains held, including adverse timing. C057, complete reach acceptance, missing compatibility/external roles, historical LFS migration and the rest of [GOAL](../../../GOAL.md) remain open. Higher-budget Agent output cannot pass an old fixed-budget gate retroactively. No hosted workflow is dispatched by this task.
