# P06 current-host provider implementation

P06 implements the separately versioned verification provider adopted in P05. It adds a Python provider, JavaScript probe, static installer, explicit driver configuration and original-test lifecycle bindings. This is validation infrastructure for the still-open C271 task. Actual host qualification and the required complete routine remain unfinished.

The final technical candidate is `113e1b855d97773307c8c2fced00e886a809bce1`, tree `5e3dd09d054dc149a5ca322160a14a1d64d67b2c`. The principal adversarial controls ran on `d76e76d9d432d3a74e69347e817eb1ae7a57de66`. The only subsequent change was two metadata fixture lines in a new driver test file. Independent review verified that production bytes, ten test identities and 39 assertions were unchanged. Results remain attributed to the revision that actually ran them.

## Observed checks

| Check | Actual result | Scope |
| --- | --- | --- |
| Existing local-driver regression | 31 passed | Candidate `d76e76d9`; real Python child-process and isolation tests. |
| New provider regression | 25 passed | Candidate `d76e76d9`; bounded file, selection, archive and failure controls. |
| New driver regression | 10 passed after the retained fixture correction | Candidate `113e1b85`; explicit digest selection, refusal evidence and environment transport. |
| Independently frozen controls | 62 selected original IDs and two supplemental IDs passed | 145 effective passing variants; one initial adapter error retained and corrected without changing its oracle. Three actual-host IDs remain unrun. |
| Final source binding | Two checks passed | Exact `113e1b85` preservation plus real selection, 18,941-file isolated copy and configuration derivation. Only physical host validation was mocked. |
| Original scientific obligations | Nine function/helper AST identities, seven loader IDs, 15 protected JavaScript segments and 15 historical source/input files preserved | Enumeration and source preservation; none of the original seven method bodies executed. |
| Documentary checks | Workflow, documentation and whitespace passed on the clean implementation candidate | Final record and delivery publication checks are recorded separately. |

The exact commands, source identities, logs, failures and limits are in [EXECUTION-CHECKS.json](EXECUTION-CHECKS.json) and the saved session evidence. The [independent review](INDEPENDENT-REVIEW.md) gives the acceptance boundary.

## Corrections and retained history

Review corrected file-reopen races in new Python/JavaScript readers, retained observed configuration identity on refusals, and made no-start accounting explicit through later evidence failures. The frozen expected configuration digest reaches the probe independently of the manifest. Historical helper and scientific bodies remain unchanged.

The first driver-test attempt intercepted an unrelated `uname -p` metadata query through its process-start spy. A narrowly reviewed metadata fixture correction resolved it; all original assertions remained. The independent preservation adapter initially assumed a field present on declared methods also existed on generated-method records. Its narrow correction retained the frozen generated corpus and the first failure. Initial interpretation, workflow-schema and local-fetch failures are also preserved. No failure was relabeled as a pass or removed.

## Limits and next action

No Node or `ldd` command, actual runtime installation, JavaScript syntax execution, original CPU readback outcome, complete discovery run, full routine, hosted Actions invocation, native/model trial or main integration occurred. Mocked supervisor calls and callbacks are not real checker starts. Static retained dependency extraction is fixture evidence only.

Gate H first needs a reviewed way to observe the actual host and author fresh host/inspection records, with a frozen execution plan and explicit configuration digest. That authoring entry point remains unimplemented. The actual executable destination, host/runtime/dependency closure, direct-probe refusals and original seven-method outcomes must then qualify. Gate R retains the complete routine and independent R03 acceptance. R04 integration and R05 parent closure remain separate.

P06 stops at this implementation boundary and its verified partial handoff. The branch and draft PR #274 remain retained/open/unmerged; issue #273 and C271 remain open. Main remains `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`; no main lease is held. R01/R02 remain done, R03–R05 remain not_done, and plan P02 remains in_progress. Historical C270 broad-driver completion and global prior-process termination remain unknown.
