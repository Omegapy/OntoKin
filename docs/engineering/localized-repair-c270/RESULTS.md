# C270 result: valid SiteRef classified as malformed

The frozen H16.02 control exposes a refusal-classification defect. A declared private `SiteRef` parameter that retains the existing pivot identity is valid under the adopted source rules. C260 intentionally excludes this endpoint form and requires `UNSUPPORTED_SOURCE_FORM`. The source observer instead returns `MALFORMED`, with reason `endpoint must resolve to a declared site`. The binding and comparison APIs preserve that same category.

## Executed result

The exact source/runner checkpoint is `1ae7b594cc075031d11f2f1a33e4c5c0f0171da4`, tree `2af435b52ca1047a1a16e5a66afb91a855d1d1bd`. [Frozen oracle](control/EXPECTED.json), [source-validity argument](control/SOURCE-VALIDITY.md), [preexecution review](evidence/review/PREEXEC-REVIEW.json), [actual five-call record](evidence/candidate/h16/RESULTS.json).

| Case | Actual outcome | Acceptance |
| --- | --- | --- |
| Original source observation | Eight hinges and sixteen sites | Passed |
| Original source/artifact comparison | Complete original agreement | Passed |
| Declared SiteRef source observation | MALFORMED | Failed exact category |
| Declared SiteRef input binding | Same source MALFORMED | Failed exact category |
| Declared SiteRef comparison | Same source MALFORMED | Failed exact category |

The three category assertions are the only failures. All input identity, retained reason, no-partial-output and applicable source-propagation assertions passed. The runner returned exit status 1. Diagnostic byte origin is null and explicitly retained; C260 requires source failure attribution, input identities and reason, not an invented mandatory span. Actual cause chains identify the source API before artifact parsing or provenance comparison. The unchanged original GLB is used only for refusal propagation; it is not rebound to the modified source and supplies no paired agreement claim.

The independently selected affected cohort passed **108 methods**: C265 source 49, C266 binding 34 and C267 comparison 25. Fixture reconstruction, 14 original corpus bindings, documentation preservation and workflow structure also passed. [Exact commands, environment, inputs and logs](evidence/candidate/regressions/CHECKS.json) identify CPython 3.12.14 / Linux execution. The green regression cohort does not change the failed new control.

## Scope and cause

C265 `Source.site()` treats both an absent member and an existing member whose kind is not site as `MALFORMED`. Here the name exists and denotes a declared SiteRef parameter. The finite profile should refuse that valid unsupported form without evaluating it. The wrappers correctly preserve the upstream category; they are not the source of the classification error.

No observer, runtime, adopted contract, original control/fixture, dependency, budget or hosted-workflow byte changed. This is a failing evidence checkpoint, not a corrective implementation. C269 remains historical and unchanged; H16 still cannot be marked complete. H20/H22/H24 remain open. No source evaluator, exporter, native app, model trial, full product regression, site/world or accepted-revision qualification ran.

## Retained process failures

The initial workflow check rejected incomplete schema fields; corrected fields passed without changing checker rules. The initial documentation check found relative links in relocated raw observed Markdown; exact bytes were retained with `.md.txt` names and an explicit mapping. A publication intent read was truncated before any commit/ref mutation; actual branch state and retained tree receipts were reconciled before continuing. [Setup records](evidence/setup/CORRECTION.md) preserve those outcomes. None is represented as a product regression.

## Completion boundary

C270 R02 remains unmet. The parent task and scope issue must stay open. Eligible evidence integration, fresh actual-main checks and saved partial handoff do not make this phase a successful H16 qualification. Preserve the unfinished branch and stop after delivery. [NEXT-TASK](NEXT-TASK.md) identifies the next bounded correction; no correction is implemented in this chat.
