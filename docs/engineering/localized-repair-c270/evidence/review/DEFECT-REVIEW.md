# C270 independent review of the observed classification defect

**Verdict: the frozen H16.02 control failed as recorded. The evidence is internally consistent and establishes a specific preexisting source-observer classification defect.** This is approval of the failure evidence, not successful qualification or implementation approval.

## Exact execution and result

The published execution candidate is `1ae7b594cc075031d11f2f1a33e4c5c0f0171da4`, tree `2af435b52ca1047a1a16e5a66afb91a855d1d1bd`. GitHub independently returned that same identity. The run started at 2026-11-20 04:10:21.649993 UTC and finished at 04:10:22.066592 UTC on CPython 3.12.14 / Linux. Tracked source was clean and all recorded code/input identities remained unchanged. One untracked regression-review JSON was disclosed; it was not an execution dependency.

The original source and source/artifact comparison controls passed with eight actual hinge records, sixteen site records and unique identities. The changed declared SiteRef input produced `MALFORMED` in all three public calls: C265 source observation, C266 input binding and C267 comparison. Each retained the reason `endpoint must resolve to a declared site`. The frozen [expectation](../../control/EXPECTED.json) requires exactly `UNSUPPORTED_SOURCE_FORM` and remains unchanged.

Only `exact_unsupported_category` failed in each negative call. The source hashes/byte counts, artifact identity where applicable, nonempty reason, source causal attribution and absence of a qualified partial result all passed. Optional diagnostic-origin metadata was null and remained explicitly null. The outer binding/comparison exceptions preserve the original source code and reason. The causal traceback reaches the same source API and endpoint/site check in each call; stale artifact provenance did not produce this failure.

The independent [execution audit](EXECUTION-REVIEW.json) passed **77 static evidence checks**. It checked the actual response files, tracebacks, expected/input hashes, published candidate/tree and unchanged preexisting code, without rerunning the observer. Those audit passes do not alter the failed behavioral result.

## Cause

In the exact checked [C265 source observer](https://github.com/Omegapy/OntoKin/blob/1ae7b594cc075031d11f2f1a33e4c5c0f0171da4/docs/engineering/localized-repair-c265/source_hinges.py), `endpoint()` line 552 sends a two-token member path to `site()`. At line 521, `site()` requires both a present member and `memberKind == "site"` in one assertion. That assertion uses `_require`'s default `MALFORMED` category. The scanner already retains declared parameters and their type/expression tokens at lines 404–409.

The frozen `parent_site_ref` member exists, has declared type `SiteRef`, and aliases the existing same-class `pivot` under the independently reviewed source rules. It is outside C260's supported endpoint syntax, but it is not an undeclared endpoint. Combining absence and wrong declaration kind in one malformed-input check loses the distinction required by C260/H16.

The source observer and both wrappers are byte-identical to the pre-C270 baseline. This phase exposed the defect; it did not introduce a runtime regression. C266 and C267 propagation itself behaved as designed.

## Smallest proposed correction for a fresh authorized phase

1. Distinguish an absent endpoint name from the recognized declared `SiteRef` parameter case in C265's endpoint/declaration classification. Return `UNSUPPORTED_SOURCE_FORM` for that unsupported declared-reference form. Do not evaluate the parameter default, follow the alias, or emit a qualified endpoint set.
2. Preserve existing malformed-name/type/access outcomes and all supported direct-site behavior. Use the unchanged C270 frozen fixture/expectation as the regression target; add only the narrowly necessary differential guards for accidental reclassification of genuinely undeclared or invalid endpoints. This is not a complete source-validity checker.
3. Account for the exact dependency chain. C266 pins C265; C267 pins C265/C266; C268 pins C265/C266/C267. A source edit without reviewed pin/identity updates causes legitimate `INPUT_BINDING` refusals downstream. A future correction must prepare the smallest consistent successor or pin refresh, preserving all original snapshots and failed evidence. Pin changes alone must never weaken byte verification.
4. Recheck the corrected source/binding/comparison result, original positive controls and complete affected independent suites. If downstream pins change, include C268's historical-admission suite in that later phase. No product compiler/evaluator/exporter, supported-SiteRef expansion, contract change or unrelated H-group work follows automatically.

No correction, new behavioral probe or additional source execution was performed by this reviewer. C270 R02 and H16.02 remain unmet; the parent task/issue must stay open. H20/H22/H24 and full C260 qualification remain outside this result. Evidence-only publication is eligible only after the Director's remaining regression, exact-candidate review, integration and saved-handoff gates; no closure claim follows from this review.
