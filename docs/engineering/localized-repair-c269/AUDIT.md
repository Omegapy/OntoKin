# C269: C260 hinge qualification coverage audit

## Decision

The retained evidence supports complete finite coverage for **24 of 28 groups**. **H16, H20, H22 and H24 remain partial**. Across the map there are **99 material subcases: 94 complete and five partial**. No group is classified absent or contradictory. The complete C260 qualification is **not established**.

These are coverage findings. A missing control does not establish that the implementation is wrong. C269 executed no new observer behavior and changed no implementation, contract, fixture, existing control, dependency, semantic rule or budget.

The four interfaces separate source declarations, raw artifact claims, source/artifact agreement, and exact historical-byte admission. A passing result at one boundary cannot supply a stronger result at another.

## Scope and source support

The immutable audit baseline is `23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb`. [COVERAGE.json](COVERAGE.json) contains every material subcase, actual assertion location, input construction, execution record and remaining gap. [INPUT-IDENTITIES.json](INPUT-IDENTITIES.json) binds inspected files to exact revisions and hashes. The unchanged [C260 control plan](../localized-repair-c260/CONTROL-PLAN.md) governs the 28 groups.

Two actual independent investigators mapped disjoint group ranges; a third worker reviews the combined candidate. Their original reports and machine-readable maps are preserved: [H01–H14](evidence/audit-h01-h14/REPORT.md), [H15–H28](evidence/audit-h15-h28/REPORT.md). Root owns synthesis and publication.

| Group | Obligation | Coverage |
| --- | --- | --- |
| H01 | Original endpoints | complete |
| H02 | Source-only initial | complete |
| H03 | Artifact-only initial | complete |
| H04 | Paired initial | complete |
| H05 | Ordered limit mutations | complete |
| H06 | Inclusive and zero-width limits | complete |
| H07 | Angle and zero canonicalization | complete |
| H08 | Six signed basis axes | complete |
| H09 | Invalid/unsupported source axes | complete |
| H10 | Invalid artifact axes | complete |
| H11 | Computed literal-field refusal | complete |
| H12 | Joint names and keys | complete |
| H13 | Site names and keys | complete |
| H14 | Endpoint order and ownership | complete |
| H15 | Lexical endpoint access | complete |
| H16 | Unsupported endpoint/joint forms | partial |
| H17 | Declaration collisions | complete |
| H18 | Site compatibility | complete |
| H19 | Keyed membership | complete |
| H20 | Unrelated-field independence | partial |
| H21 | Complete joint/object sets | complete |
| H22 | Source/program provenance | partial |
| H23 | Absent direct site authority | complete |
| H24 | Structural/resource bounds | partial |
| H25 | Numeric bounds | complete |
| H26 | Historical file admission | complete |
| H27 | Changed raw authority | complete |
| H28 | Unobserved site/world behavior | complete |

## Remaining evidence gaps

| Group | Supported evidence | Missing demonstration |
| --- | --- | --- |
| H16 | Origin, keyed/deeper traversal, scene and non-hinge refusals are exercised. | A source-valid declared or computed `SiteRef` must be exercised with an exact unsupported-form assertion. Existing `self.ref` is undeclared; the broad allowed refusal set does not establish the required distinction. |
| H20 | Independent baseline/length expectations, raw field probes and some binding refusals exist. | Some source invariance expectations come from the observer itself. Comparison mutations bundle unrelated fields and do not separately exercise every actual ownership/follow/motion field. Independently authored expected fields and isolated changes are still needed. |
| H22 | Extensive stale, missing and contradictory artifact/source-map provenance controls exist. | An isolated removal of the actual source import digest and its retained outcome was not found. Generic truncation or a stale digest does not prove that specific case. |
| H24 | Structural/resource refusals and the exact 128-hinge/256-site boundary are exercised. | No supplied excessive-site input with its actual typed outcome was identified. Two endpoints per admitted hinge mathematically bound the site count, but that observation is not an executed excessive-site control. The remaining obligation needs an explicit decision or a bounded additional control. |

The first proposed next scope is H16: construct a valid typed/computed site-reference fixture and verify the precise unsupported-form boundary. [NEXT-TASK.md](NEXT-TASK.md) defines its bounded acceptance. No missing control is implemented in C269.

## Verification and execution provenance

The [identity audit](evidence/EXECUTION-ELIGIBILITY.json) verifies all 159 original input identities and 30 output identities from the recorded C268 actual-main run. Of those inputs, 152 remain unchanged at the audit baseline. The seven differences are documentation/state records; observer code, tests, fixtures and dependencies remain exact. The original execution is still attributed to `5084dd69312e8da5a49aadd33cf83ba56db7c058`: 12 groups, 282 methods, 14 corpus bindings, CPython 3.12.14 on Linux. Those results are inherited evidence, not a C269 rerun.

The [independent identity review](evidence/independent-review/READINESS.md) additionally matches all 282 authored methods to preserved successful log entries, planned commands and applicable environment identities. Its 1,139 checks are static evidence assertions, not 1,139 product tests. Fresh C269 documentation/workflow/reference checks and exact-candidate review are recorded separately in the final review and integration records.

Older evidence retains its limits. C261's detailed independent run names a local commit absent from this checkout, although the retained code hashes match the available published equivalent. C265's detailed run-06 has exact input/code hashes but lacks a Git execution revision; the later clean main run separately executes the same suite. Neither old detailed ledger is relabeled as a different run. Recipes/hashes versus archived actual bytes remain distinguished in the investigator maps.

## Preserved failures and limits

The early workflow-record check failed on a missing `suggested_task` field, then passed after correction. Authenticated terminal Git publishing was unavailable; the failed attempt is retained, and the available GitHub connector published the exact intended tree conditionally. The first H01-H14 inspection assumed a historical documentation version was unchanged; its failure and correction are retained. H15-H28 inspection corrections are retained in that report. None is presented as a newly observed product failure.

Historical full-regression failures, deferred native work and the existing narrow qualification boundaries remain unchanged. This audit establishes no site poses/world alignment, complete language/glTF validity, authentic accepted revision, invalid-edit atomicity, clean rebuild, native/model trial or comparative authoring advantage. Historical C262 remains unchanged. [LEARNING.md](LEARNING.md) records the scoped learning decision.

## Completion boundary

C269 can be complete as a coverage audit while the C260 qualification remains incomplete. Integration, resulting-main checks, verified saved handoff, separate receipt, issue/task closure and ownership release remain distinct gates. The live task and delivery receipt govern current completion; frozen archives may precede their own save receipts.
