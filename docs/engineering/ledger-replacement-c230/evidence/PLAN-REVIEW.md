# C230 finite diagnosis — independent review

Decision: **APPROVE_FINITE_DIAGNOSIS** for the exact new plan and source recorded in `APPROVAL.json`, conditional on root confirming durable preservation of that approval and all bound preparation before its sole absolute outer invocation. This review started only harmless stand-in workers. It performed no product import, method replay, replacement case, aggregate or native application start.

## Exact reviewed result

Author commit `91737d1f73744e2ac86ab93e04af13692330d77e` has the reviewed C230 launcher and plan. The plan digest is `17f895542e68f99d06ca6b3771049b180308e380762f8bdd972b3ed8f80fbcd9`; launcher digest is `2505d1c84cff16a1218130c9e9e7bdf26132272f3420fa88492cc03447306653`. The observation worker is reused byte-for-byte from C229 at digest `c35dec8ced137cfac49ea5f093c5bd97aa3e47cfee50030f73497c226bd5f3a4`. Its C229 schema labels remain explicit provenance; the C230 plan/launcher identifies the fresh invocation.

The documented offline restore now exists at `/workspace/scratch/ad17c735596b/OntoKin`. Independent Git readback confirms commit `e19acb44784ba5654f24bd3d87fb7310249f6d05`, tree `24a3af6da34dc5cce7e6813734fb65958791f712`, empty status and all nine exact source/test/protocol/contract hashes. These nine inputs also match C228 executed revision `fc500331ce789eb6f9c1210ea4f3b394d45e507c`. The exact preserved C228 failure-record hashes match the plan. `PREEXECUTION-CHECKS.json` records 29 successful independent static/binding conditions and the restored-source readback.

## Launcher path correction

The new launcher resolves caller plan and approval paths before reading them. Source/output paths embedded in a plan resolve relative to its absolute directory. Derived launcher/worker paths must exist, refer to files, and match the reviewed hashes; the actual running launcher must be at that resolved launcher path. The interpreter is resolved and bound by digest/version/platform. Every worker script/source/output/scratch argument is absolute before the child working directory becomes the immutable source checkout. The actual approved outer invocation is fully absolute.

The original single-use output-directory claim remains. A source/output overlap is rejected; absent source and output-parent directories reject. A plan must name exactly the two script bindings and exactly the original-method/observed-cases slots, each with one start and a ceiling no greater than 60 seconds. The actual frozen plan uses 60 seconds each. Pre-start attempt records now distinguish a consumed start attempt from successful `Popen` return.

## Harmless qualification evidence

The author's 24-control report and qualification-script hashes match the frozen plan. That report includes an actual inert reproduction of the old relative-path failure, corrected relative/absolute/unrelated-cwd paths, missing/mismatched inputs, source identity refusals, one-use refusal, finite-limit refusals, missing/malformed results, unexpected failures/exits, child-attempt reports and timeout stopping.

I separately authored and ran eight controls against byte-identical copies of the frozen new launcher in `inert-controls/run-01`. The source was a tiny independent Git repository containing only an anchor text file. The workers imported no OntoKin code and returned synthetic result shapes. All **88 assertions** passed across relative caller inputs with a different child cwd; absolute inputs from an unrelated cwd; relative embedded source/output paths; missing worker; changed worker digest; one-use repeat refusal; first-worker missing result; and a simulated forbidden-child-attempt report. Those controls used ten inert worker starts and zero product imports, methods or replacement cases. Exact script paths, child cwd, absolute arguments, bytecode-disabled state, source equality, reaping and empty process groups were checked. The one-use repeat left every output byte unchanged. Details and raw invocations/results remain under `inert-controls/`.

These controls prove the observed launcher behaviors, not ledger behavior. Synthetic ten-subtest/four-case result shapes must never be included in product diagnosis counts.

## Fixed product diagnosis boundary

Root may invoke the frozen plan once after saving the approved source/evidence. It contains two sequential workers at most: one original, unchanged method with ten mutation subtests, followed only on allowed complete outcomes by four predeclared marker/journal replacement observations. The cases are marker and journal without held descriptors, followed by separately labeled held-descriptor controls. The maxima remain fourteen `Ledger.begin` calls and twenty-eight reservation calls, four bounded Git metadata starts, zero worker children, zero native starts, zero aggregates and zero automatic retries. Product source, assertions, protocol, fixtures and limits remain unchanged.

The original worker records unittest callbacks without altering the selected filesystem operations. The observation worker preserves exact originals before mutation in a pre-opened synchronized event file; no extra evidence-file allocation occurs between unlink and recreation. It records missing/recreated paths, device/inode numbers, modes/link counts/times, descriptor inventories, original/recreated/post-reservation bytes, return/exception chains and stopped/uncertain state. A retained descriptor changes object lifetime intentionally and stays separately identified. The instrumentation changes timing and cannot recreate C228's absent allocation sequence.

A second reservation occurs only after first-reservation rejection. After an unexpected successful first reservation, the poison check is explicitly not run; a later stage-order rejection cannot substitute for missing replacement rejection. The selected test likewise does not reach its poison assertion after `assertRaises` itself fails. Retain that distinction in all outcome summaries.

## Cleanup, stopping and interpretation

Workers run in separate process groups. Timeout/interruption invokes group termination and bounded reaping. The launcher requires reaped workers and no observed remaining group members, complete results, no reported child attempt, original temporary-fixture cleanup and closed retained descriptors before completing or advancing. Unexpected outcomes stop. Source commit, tree, status and nine bound hashes are compared before/after; the launcher exits nonzero if source equality fails. A missing/partial receipt or any unknown start outcome requires reconciliation and no retry under this plan.

The fixed diagnosis can establish a new observed mechanism if same-content unlink/recreation reuses numeric identity and the reservation returns. It cannot retrospectively prove that C228 had that exact allocation event. If no such observation occurs, report the finite result as unresolved without adding cases. An isolated original-method pass cannot erase C228's retained two replacement failures. R02 remains blocked; any product repair or another aggregate belongs to a later scope. C229's old plan/output remains consumed and unchanged.
