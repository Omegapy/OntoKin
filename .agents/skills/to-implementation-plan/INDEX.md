# Package index

This index covers the complete source-only `to-implementation-plan` package. Every listed path is relative to this directory.

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Explicit-only entrypoint, operation routing, shared workflow, authority limits, and stop conditions. |
| `README.md` | Transferable package context, requirements, later installation, explicit use, runtime layout, lifecycle, validation, and recovery. |
| `ACTIONS.md` | Stable action IDs `TO-IP-001` through `TO-IP-012`, helper routes, write sets, and gates. |
| `INDEX.md` | This package inventory. |
| `agents/openai.yaml` | User-facing name and prompt plus disabled implicit invocation. |
| `assets/example-input.json` | Valid reviewed example of a draft-plan creation payload. |
| `assets/plan-overview-template.md` | Renderer field and section contract for generated `PLAN.md`. |
| `assets/phase-template.md` | Renderer field and section contract for generated per-phase Markdown. |
| `assets/traceability-template.md` | Renderer field and section contract for generated `TRACEABILITY.md`. |
| `references/intent-and-project-discovery.md` | Source intake, provenance, project inspection, intent extraction, clarification, synthesis, and coverage workflow. |
| `references/lifecycle-and-recovery.md` | Plan/task transitions, derived phase state, evidence gates, stale updates, locks, partial success, and bounded recovery. |
| `references/plan-contract.md` | Canonical schema, identity, selectors, storage, projections, result envelope, errors, bounds, security, transactions, and compatibility. |
| `scripts/plan_state.py` | Standard-library CLI for canonical validation, deterministic projections, exact selection, safe mutations, and recovery. |
| `tests/test_plan_state.py` | Focused contract, fault, projection, lifecycle, source-boundary, and package tests using temporary projects. |

No runtime file is expected outside this directory. There is no icon, plugin manifest, database, daemon, external dependency, changelog, migration utility, or automatic plan executor in V1.

No attribution or third-party license file is required because this package uses original project-specific implementation and wording. Add those files later only if protected code or text is actually incorporated under compatible terms.
