# C271 P01: isolated missing import-digest control

The candidate resolves the specific missing-control evidence identified as C269 H22.02. Both historical baseline inputs passed source observation, source/program binding and hinge comparison. Four inputs with only the required digest clause or its quoted value removed returned exact `MALFORMED` refusals through all three interfaces.

There were **six input cases and 18 interface calls**: six positive calls and twelve refusals. The runner recorded 1,042 assertion checks with zero failures; these are assertions within those calls, not 1,042 separate tests. Source was the clean published commit `067392f2b5f592a5c3104fa8848cc0030ba1117b`, tree `21ab07914931495d6bee70591a70ff2d8bcabb84`, on CPython 3.12.14/Linux x86-64.

## Independence and exact evidence

The separate worker `/root/control_author` derived expectations from adopted import syntax, unchanged C260 rules and the actual historical source. It did not read or execute observer/test/product code or historical observer outputs. [EXPECTED.json](control/EXPECTED.json) was published before execution with SHA-256 `0b8da6eab52323e8092c348fabad0d8d77247552e4eb5e3a1ffdc17266d12522`. Each mutation deletes one exact contiguous range and preserves every other source byte, the companion source and the artifact. The before/after baseline expectations independently specify eight hinges, sixteen endpoint sites, eighteen objects, identities and exact numeric values.

[RESULTS.json](evidence/control-candidate/RESULTS.json) identifies every call and response. [RAW-EVIDENCE.zip](evidence/control-candidate/RAW-EVIDENCE.zip) retains all complete responses, request records, input identities and individual assertions with its own manifest. [EXECUTION-RECEIPT.json](evidence/control-candidate/EXECUTION-RECEIPT.json) preserves the exact tool-observed command, including interpreter flag `-B`, which Python sys.argv omits from the original report. The original report remains unchanged. No behavior was rerun to repair that metadata omission.

Every refusal retained exact source hashes and byte counts; binding/comparison also retained artifact identity. The same source refusal reason propagated through the higher interfaces. No successful return or partial qualified records accompanied a refusal. Baseline results retained their stated nonclaims.

## Phase and remaining gates

This P01 candidate is not merged. The parent stays open for P02: required routine local driver, complete affected regression inventory, independent integration approval, expected-head ownership/update, fresh actual-main checks, branch lifecycle and final saved delivery. Focused independent review and phase record checks are recorded separately. Main stays at `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`.

No observer/runtime/grammar/contract/pin or historical control changed. No complete H22/C260 qualification, accepted-revision authority, source evaluation, export, native/model trial, physical correctness or comparative benefit follows. H20/H24 remain outside scope. Historical broad-driver completion remains unknown.
