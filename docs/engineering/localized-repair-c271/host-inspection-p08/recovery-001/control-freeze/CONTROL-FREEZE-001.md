# C271 P08 independent control expectation freeze

This freezes the HI control oracles before author execution. All actual project child starts remain zero. Mocked starts and historical unresolved starts use separate counts. It is not a real-host plan or a qualification result.

The exact candidate and deterministic fixture/hash-to-control mapping must be inspected before focused execution. A helper/parser test establishes only that helper boundary; it cannot stand in for an integrated admission or persistence check.

Coverage: 20 accepted HI controls, 105 material variants, 5 positive controls.

| Parent | Required boundary | Material variants | Expected category |
| --- | --- | ---: | --- |
| HI01 | Plan selection | 7 | CHI-PLAN |
| HI02 | No self-approval | 2 | CHI-PLAN |
| HI03 | Safe plan read | 9 | CHI-PLAN |
| HI04 | Bound source | 7 | CHI-SOURCE |
| HI05 | Exact candidate | 5 | CHI-RUNTIME |
| HI06 | Inspector and Python | 7 | CHI-INSPECTOR |
| HI07 | Loader resolution | 7 | CHI-LOADER |
| HI08 | Unsupported host | 6 | CHI-UNSUPPORTED |
| HI09 | Evidence path | 4 | CHI-PATH |
| HI10 | Prelaunch time of use | 3 | CHI-DRIFT |
| HI11 | Postlaunch time of use | 3 | CHI-DRIFT |
| HI12 | Version result | 4 | CHI-OUTPUT |
| HI13 | ldd grammar | 7 | CHI-OUTPUT |
| HI14 | Launch failure | 4 | CHI-PROCESS |
| HI15 | Deadline | 4 | CHI-PROCESS |
| HI16 | Output limits | 4 | CHI-OUTPUT |
| HI17 | Cleanup and receipt | 5 | CHI-PROCESS |
| HI18 | Evidence failure | 6 | CHI-EVIDENCE |
| HI19 | Interrupted or unknown | 6 | CHI-EVIDENCE |
| HI20 | Strict output projection | 5 | CHI-COMPAT |

## Key count and durability decisions

- HI14 separates a proven prelaunch zero, an observed callback start, and a lost launch-to-callback window with exact null/lower bound zero.
- HI18 separately covers prelaunch persistence failure, start-ledger failure, postlaunch publication failure, uncertain no-replace replies, and final completion-marker failure. A final-marker failure after two successful command mocks has one start per command and two total; it still cannot return successful observation.
- HI19 reconciliation launches nothing and changes no evidence. The inspected fixture can contain zero, one, or unknown historical starts. A missing process group cannot prove a successful earlier completion.
- HI13 pure parser cases have zero starts. Its integrated malformed-ldd variant has a preceding successful version mock, then one ldd mock: two mocked direct starts total.
- If a launch record or cleanup outcome is uncertain, preserve that uncertainty. If the filesystem cannot finalize failure evidence, report evidence_finalized=false and retain the caller-capture boundary.

Every variant, mutation, route, category, count, evidence policy and additional assertion is in `CONTROL-FREEZE-001.json`. `INDEPENDENT-FIXTURE-SEMANTICS-001.json` fixes synthetic positive ldd/version/process semantics without pretending virtual fixture paths are actual authorized host paths.

Root and implementer must retain this freeze unchanged. Any material correction is a new explained revision before affected execution. No production/test source was edited or imported by the reviewer.
