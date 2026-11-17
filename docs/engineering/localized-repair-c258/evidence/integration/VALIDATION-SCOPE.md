# C258 integration validation scope

This plan applies to the finite standalone explicit-follow observer under `docs/engineering/localized-repair-c258/`. It is not a release qualification plan.

## Exact-source gates

Before publication, freeze an identified author commit/tree and check that cumulative source edits are confined to the new component. The contract approved at `4cc41b0586e433caa4c70d5f819cad781d649a89` pins the C257 lexical/identity helper by hash. The reviewer must verify actual new parsing, source-derived values, artifact origins and explicit refusal boundaries. A separate structural review covers resource handling and public errors. Every original failed attempt remains preserved.

Run the authored follow suite on immutable clean source. Run the unchanged C257 ownership suite because C258 directly reuses its pinned utilities. Run the adjacent C256 reader and C255 oracle suites and the C253 manifest verifier to establish the stated preservation boundary for the existing observation chain. Run documentation preservation/navigation checks after adding current root navigation and evidence links.

The relevant script paths are:

- `docs/engineering/localized-repair-c257/test_ownership.py`
- `docs/engineering/localized-repair-c256/test_reader.py`
- `docs/engineering/localized-repair-c255/test_oracle.py`
- `docs/engineering/localized-repair-c253/verify_manifest.py`
- `docs/maintenance/reorganization-2026-10-17/verify_reorganization.py`

The new authored suite's actual path and method count must be recorded from its committed implementation. No count is assumed by this plan. `run_check.py` records exact HEAD/tree, script hash, interpreter/platform, command, complete output and clean/unchanged source.

## Why this cohort is bounded

The selected change adds an independently invoked experimental observer and its evidence. It must not edit shared language, construction, runtime, Agent, exporter, destination or release machinery, nor silently activate a new product path. The C253/C255 scientific inputs and C256/C257 code must remain byte-identical. Under OK-ENG-009, a change to any of those shared boundaries requires reassessing and expanding the relevant regression cohort; this plan cannot exempt such a change.

If the scope remains isolated, the focused component/dependency/preservation cohort tests the actual changed surface. It does not relabel the historical default aggregate as a new run. Unchanged strict normal-fidelity failure, R07/R08 gates and C251 current-authority refusal remain explicit.

## Integration and resulting main

Root owns shared documentation and coordination state, and acquires the main lease only by verified conditional update after reconciling current main, branches, PRs and ownership. Publish the exact reviewed tree through the existing C258 branch and use a PR. Inspect reviews, comments, relevant CI and the actual head before merging with the expected head guard.

Read back the merge and confirm the reviewed tree/source, then execute the same relevant cohort on actual merged main. Evidence reused from an independent immutable author review requires exact scientific-input equality; do not claim it was rerun on main. Evidence-only closure gets its own fresh documentation check.

Confirm branch ancestry/history retention, automatic deletion outcome, remaining branches and open PRs. C234 cleanup and C174 historical retention retain their explicit dispositions unless new evidence resolves them.

## Delivery gates

All workers must finish or checkpoint before final source/evidence freeze. The approved C258 packaging wrapper preserves the complete C257 payload and source graph. It does not replace actual archive verification, a fresh complete documented offline restore, original-v0/session preservation checks, the follow suite on restored source, and a confirmed saved final ZIP. Close issue245 only after those outcomes are observed. Stop at that delivery.

