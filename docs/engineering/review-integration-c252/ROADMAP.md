# Evidence-led roadmap after the November 16 review

The [C252 decision](DECISION.md) changes investment order while preserving
existing language contracts and receiver evidence. The unit of value is a task
an agent can complete correctly, such as changing one named component without
damaging a sibling. Additional syntax, profiles and adapters must earn their
maintenance cost through such tasks.

## Ordered gates

| Gate | Bounded outcome | Evidence required before moving on |
| --- | --- | --- |
| A0 — next task | Freeze a localized-assembly-repair protocol and select existing eligible fixtures. | Exact task/input identities, permitted edits, independent scoring, route applicability, model/tool budgets and an analysis plan. No trials in this step. |
| A1 | Build and validate only the minimal runner/oracles required by the approved protocol. | Positive and negative oracle controls, complete attempt accounting, source/artifact identity and a reproducible fresh-checkout path. No broad framework. |
| A2 | Execute one predeclared pilot using available routes, followed by a separate decision on a larger study. | Raw attempts, failed/limited runs, paired outcomes, uncertainty and setup/maintenance costs. Pilot feasibility and product advantage are separate conclusions. |
| B | Resolve one selected native receiver objective, then decide on a finite OpenUSD mapping. | Actual target/version observations, field-level preservation/loss/unsupported classification and source traceability. If a target is needed earlier for the pilot, scope that dependency explicitly. |
| C | Demonstrate generated-asset complementarity. | A content-identified external asset, supported semantic bindings, a useful localized operation and checked delivery; no claim based only on appearance. |
| D | Publish a limited, reproducible research claim or reduce scope. | Repeated comparative evidence on the declared task population, auditable artifacts and a clear account of limitations and engineering cost. |

Only A0 is the successor task selected by this handoff. A1 and later gates are
not authorized as part of A0 merely because they appear here. There is no fixed
calendar or promise that every gate will justify proceeding.

## Comparison design requirements

Reuse [C180's matched-comparison principles](../semantic-physical-scope-c180/README.md).
The same pinned model/version, equivalent task information and comparable
resource budgets must serve every route. Use fresh contexts, balanced route
order, repeated trials and task-level pairing where applicable. Keep development
examples separate from evaluation variants. Multiple edits of one assembly are
related observations; a large row count does not create independent assemblies.

OntoKin and direct Blender/Python are the first routes to assess for the
existing fixture. Assess OpenUSD-native authoring on the same requested
semantics. Record supported, unsupported and unavailable capabilities before
trials. An unavailable baseline is a limitation, not a failed competitor.
CadQuery or another mechanical baseline is optional only if the task is a good
fit; it must not create an unrelated implementation track.

Prefer a common destination evaluator and output requirements where feasible.
If routes use different exporters or backends, report the comparison as an
end-to-end workflow comparison; it cannot isolate the causal effect of `.ok`.
A narrower language-effect claim needs the stronger shared-backend design.
Route-specific adapters, reusable setup and maintenance costs must be recorded
separately from per-task cost and included in the investment decision.

## Metrics to define before execution

| Measure | Required interpretation |
| --- | --- |
| End-to-end task success | Fraction of all eligible attempted tasks meeting the requested edit, source rebuild and applicable artifact checks within the declared budget, without human correction. Preserve every failure in accounting. |
| First-pass success and repair | Distinguish the first submitted artifact from final budget-limited success; record every repair iteration and intervention. |
| Unintended changes | Check forbidden changes to unrelated identities, values, topology or geometry against task-specific invariants and tolerances. Hash changes alone do not imply semantic changes. |
| Invalid-edit handling | Score designated negative cases separately: reject at the stated boundary and retain the accepted revision/artifacts. Rejecting a valid task is not success. |
| Identity and provenance | Bind source closure, accepted revision, semantic IDs and actual output bytes; separately test stale or mismatched references. |
| Transport loss | For tasks involving a receiver, compare observed preservation and declared losses. Classify unobserved fields explicitly. |
| Efficiency | Report input/output/cache tokens separately, tool calls, repair turns and elapsed time with clear units. Choose one primary efficiency endpoint; do not combine unlike quantities into an undefined burden score. |

Freeze timeout, missing-output, infrastructure-failure and abstention rules.
Report exclusions and reasons; do not discard inconvenient attempts after seeing
their outcomes. Use an evaluator independent of the submitted route where
feasible, and record scoring before revealing route labels.

## Proceed, revise or reduce scope

The supplied review proposes either a **20 percentage-point absolute success
gain** or a **30% relative reduction in effort at non-inferior success**. These
are candidate investment thresholds. They are neither release gates nor
measurements of OntoKin. A later protocol must choose and justify its primary
endpoint, success noninferiority margin, uncertainty method, task/assembly
sample size and decision rule before observing trial outcomes.

| Result | Decision |
| --- | --- |
| Predeclared benefit supported without unacceptable semantic or provenance errors | Continue only the task families and small improvements supported by the evidence; report the engineering cost. |
| A concrete route or harness defect prevents a fair comparison | Fix that bounded defect, preserve the failed attempt and separately authorize a new protocol/run. Do not retrofit thresholds to the result. |
| Uncertainty is too large or the pilot is too narrow | Report inconclusive. Decide whether a larger justified study is worth its cost; do not claim superiority or general failure. |
| A mature, adequately specified comparison shows no practically useful advantage | Stop expanding the DSL and document whether a smaller semantic schema, provenance library or validation toolkit retains useful value. |

An efficiency claim must meet the predefined success rule and semantic guardrails,
not merely consume fewer tokens on fewer successful tasks. Report confidence
intervals or another justified uncertainty analysis alongside point estimates.
The protocol must state whether its thresholds apply to those estimates or to
their uncertainty bounds. No statistical rule is retroactively selected here.

## Scope still held

C251 native sampling, the rest of R07 admission/execution, an OpenUSD exporter,
generator ingestion, broad profile consolidation and general runtime refactors
remain separate scopes. Existing completed evidence stays completed within its
original limits. The strict Blender-normal failure remains failed. This roadmap
does not reopen a consumed native schedule or declare a second target passed.
