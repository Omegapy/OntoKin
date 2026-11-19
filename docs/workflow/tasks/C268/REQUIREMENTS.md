# C268 requirements: historical hinge endpoint admission

Owner authorization: November 19, 2026 Prompt 1 permits one next approved step after C267 completion. Base `b2ca38875bd7b43b85011bbc671ee9fee1682441`; owner `c268-root-c7dae94da130`; branch `work/c268-historical-endpoint`; [scope issue](https://github.com/Omegapy/OntoKin/issues/265).

Implement only the fourth interface in unchanged [C260 CONTRACT](../../../engineering/localized-repair-c260/CONTRACT.md), using its [INPUTS](../../../engineering/localized-repair-c260/INPUTS.json), [CONTROL-PLAN](../../../engineering/localized-repair-c260/CONTROL-PLAN.md), actual C253 corpus and pinned C267 comparator.

## R01 — Historical identity

Admit only before/after endpoints from unchanged C260 INPUTS and matching C253 pins. Require exact size and SHA-256 for the selected main.ok, shared hinges.ok and GLB before calling the comparator. No alternate file, sidecar, network or ambient fallback.

## R02 — Safe bounded file access

Reject symbolic-link files and ancestors, repository escape, invalid endpoint, missing/permission/nonregular files and short/growing/wrong-sized or wrong-hash bytes. Check size before bounded reads; return typed refusals with bounded available identities and no qualified partial set. Preserve inherited resource bounds.

## R03 — Comparison and authority

Invoke exact pinned C267 comparator on captured bytes only after admission. Preserve comparison results, source-only/absent-artifact authority and all physical/execution nonclaims. Only this wrapper may affirm historicalInputsBound for original bytes; first three interfaces and supported changed raw inputs stay unchanged.

## R04 — Independent controls

Independently exercise both original endpoints, missing/changed-size/same-size-changed source and GLB, symlinks/ancestors/loops/escape, permission and nonregular paths, bounded read failures, dependency mutation and refusal propagation. Include raw changed-input versus historical admission controls for H01/H03/H04/H26/H27. Record actual coverage without claiming full H-group qualification. Original endpoints must each yield eight hinges, one shared joint definition and sixteen endpoint sites.

## R05 — Verification and independent review

Execute the complete affected C253/C255/C256/C257/C258/C261/C265/C266/C267/C268 cohort plus workflow/documentation checks on identified bytes. Obtain separate exact-candidate review, resolve mandatory findings, preserve failed attempts and all unrun roles.

## R06 — Integration and branch lifecycle

Use verified expected-head lease and conditional nonforce publication/expected-head PR merge; read back actual main and execute affected checks, retain reviewed history and verify branch disposition. New/worsened legacy failures block integration.

## R07 — Saved delivery

Verify exact manifest, safe ZIP inventory, fresh extraction and source snapshots; save final online browser-session handoff and prompt files in existing OntoKin folder, publish separate receipt, complete task only after every gate, release ownership and stop. Preserve C262 unchanged.

## Exclusions

No product runtime/parser/evaluator/exporter, source semantics, budgets, historical fixture/contract or hosted workflow changes. No site/world, accepted revision, edit atomicity, clean rebuild, native/model trial or comparative benefit qualification. This is an isolated standard-library engineering observer. Full product regression and other interpreter/native/visual roles remain unrun unless scope expands through a separate declared phase.
