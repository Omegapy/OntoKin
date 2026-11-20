# C268 recovered acceptance evidence audit

**Verdict: eligible for evidence reuse, with publication identity checks and fresh resulting-main verification still required.** No blocking implementation or evidence finding was discovered. This audit executed 386 identity and accounting assertions; every assertion passed. It did not rerun the candidate cohort, edit the source repository or write to GitHub.

## Exact scope and evidence

Auditor: `/root/remote_audit`. Source checkout: `/workspace/scratch/014048e883e4/OntoKin`, clean at recovered accepted checkpoint `ffb912cce59ccfe7d0d82ab4349de9b12271cc03`. The reviewed and tested public candidate is `e6f55b73fa71953aa648bcd34711a6796a7346b6`, tree `d94436a22552db903b8016f9d035985a7d8b6752`.

The separate reviewer `/root/review_c268_final` accepted R01–R05 and recorded no unresolved mandatory finding. The original selector-length finding is resolved by the bounded lookup guard. Optional O01 concerns native Python Path rendering before its text cap; the reviewed contract treats this as future input-contract hardening, with no admission bypass or mandatory C268 change.

The audited corrected-candidate receipt proves 12 completed groups, 282 test methods and 14 C253 file bindings for three tasks, with zero failed, erroneous or skipped methods. Its 35 C268 methods record 131 calls: 12 historical admissions, nine raw successes and 110 typed refusals. This remains finite historical-byte admission and declaration comparison, with the existing nonclaims preserved.

## Independent checks performed

- Recomputed size and SHA-256 for every one of the 157 receipt inputs directly from the candidate Git blobs.
- Verified the complete implementation, tests, control fixtures, five-module dependency closure, fixed historical files, runner and contract pins remain identical at the accepted checkpoint.
- Recomputed all 30 cohort output identities and verified exact inventory. Checked all 31 reviewer-manifest artifacts, the separate review Markdown binding and candidate receipt binding.
- Parsed every group result and its log, verified method totals, corpus bindings, control accounting and the existing independent audit's passing assertions.
- Checked the preserved input ZIPs for unique safe names and CRC integrity.
- Verified clean source state before and after this audit, ancestry, and candidate tree identity.
- Verified the available interpreter binary and environment against the recorded execution: CPython 3.12.14, Linux 6.18.57 x86-64, glibc 2.41, Clang 22.1.3, runtime bundle 26.1117.11355. Binary SHA-256 is `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`.

Four of the candidate's 157 recorded inputs changed at the accepted checkpoint: STATUS, C268 RESULTS, CURRENT and C268 task.json. They are current records, not implementation or fixture changes. The recovered checkpoint also adds acceptance evidence. Its historical preintegration receipt records passing workflow/documentation checks; current publication still needs applicable checks and exact readback. Do not claim all 157 current inputs are unchanged or relabel the earlier candidate execution as execution of a later commit.

## Publication and resulting-main requirements

Publish the recovered payload without changing its file bytes, modes or histories. Verify the intended tree/blob identities at the destination, including binary input archives and ignored raw logs. Preserve the candidate SHA in all reused results. A different API-created commit identity is acceptable only with explicit provenance and verified payload equality; it cannot silently replace the recorded execution identity.

After actual integration, use the existing runner from an authentic clean resulting-main checkout, with a new output directory outside it:

```sh
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 -B docs/engineering/localized-repair-c268/evidence/run_checks.py --repo ACTUAL_CLEAN_MAIN_CHECKOUT --phase main-integration --output NEW_EXTERNAL_OUTPUT_DIRECTORY --c268-methods 35
```

Run from that checkout's root. The runner already performs the entire required cohort, including workflow and documentation checks, records Git identities before/after, retains 157-plus current input identities, and audits method counts. Default per-command timeout is 300 seconds; there is no reason to raise it or rewrite the runner. No dependency installation or hosted execution is required. Retain its full CHECKS.json and all receipt-listed outputs, including ignored files.

Any changed implementation, dependency, fixture, test, runner or applicable environment invalidates unconditional reuse and requires affected re-evaluation. Resulting-main checks, branch history/disposition and final saved delivery remain Director gates. Full product regression, other Python versions, source/export/conformance, native/visual/model trials, full C260 H groups, site/world behavior, accepted revisions, atomicity, rebuild equivalence and comparative advantage remain unrun or unqualified as already recorded.

Detailed machine-readable evidence and the audit script are in this directory as `ACCEPTANCE-AUDIT.json` and `audit_acceptance.py`.
