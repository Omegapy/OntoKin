# C270 recovery finalization

This phase resumes the existing evidence-only task after the conversation ended. It does not repair the observer. Starting main `c7b99e7c37bf8e3b11b58660b2903150211dc355` and branch `1a2e9f85fa3ba210a16235e5660f1762ea8a953e` were reconciled with both supplied ZIPs, the confirmed early receipt, issue270, empty PR inventory and expired ownership. New ownership was conditionally acquired and read back at `ab0f196cd8c67dfa94cba369381dafa8b6c7a015`.

## Gate table

| Gate | Observed state | Evidence or next action |
| --- | --- | --- |
| C269 delivery and closure | Complete | Prior confirmed receipt and source archive audit |
| C270 input and expectation freeze (R01) | Complete | Original control/EXPECTED.json and SOURCE-VALIDITY.md |
| Actual H16 control (R02) | Failed, retained | Exactly three category assertions failed at `1ae7b594cc075031d11f2f1a33e4c5c0f0171da4`; no partial qualified set |
| Affected cohort | 108 methods and 14 corpus bindings passed | Original candidate/regressions/CHECKS.json; no behavioral rerun in this phase |
| Independent exact-candidate review (R03) | Pending | Reviewer examines published candidate and cumulative scope |
| Evidence integration and actual-main checks (R04) | Pending | Conditional integration after review; fresh documentation/workflow checks |
| Partial delivery and receipt (R05) | Pending | Verify frozen ZIP, save ZIP/prompts, publish separate receipt |

## Preservation and limits

The original failure input, oracle, code, logs and prior reviews remain unchanged. Main/current-task disagreement is reconciled through the scope branch; an older frozen `save_pending` value is not evidence that an upload failed. No unknown remote write remains from the observations. The prior workspace is unavailable; all known substantive work is on GitHub, and supplied ZIP overlays remain recoverable. This cannot exclude unpublished bytes elsewhere.

The new early recovery is [confirmed](RECOVERY-EARLY-RECEIPT.json). Detailed source-archive verification, startup read-set and reconciliation are in `evidence/recovery-20261120/`. Current workers are independent reviewer `/root/candidate_review` and packager `/root/handoff_audit`; root owns canonical writes and integration. No nested workers or external model runner are used.

R02 remains unmet even if documentation checks, evidence review, integration and delivery pass. Keep task C270 and issue270 open, retain the unfinished branch and stop after the saved partial handoff. [NEXT-TASK](NEXT-TASK.md) proposes the smallest classification correction for a fresh main chat. H20/H22/H24 and full contract/product/site/world/native/model qualification remain outside this phase. Existing scoped LEARNING.md already records the supported lesson; no duplicate project memory entry is needed.
