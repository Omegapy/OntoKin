# C271 P21 independent H0 decision

**H0 is unaccepted because required installation evidence is unavailable among the declared inputs.** The static P20-environment rebind is independently accepted. No operational inspector or preparer was invoked for this decision, so no runtime refusal or executable failure is claimed.

## Concrete blocker: H0-INSTALLATION-RECEIPTS-001

The current `current_host_inspection_v01.py` requires both `runtime.install_receipt` and `dependencies.install_receipt`. Each is an index binding an actual unchanged-preparer plan and its successful report. The required purposes are `selected-node` and `retained-dependencies`.

`_check_installation` accepts only `INSTALLED_EXACT` or `ALREADY_PRESENT_EXACT`, with the required zero Node/ldd/checker counts and exact archive/member/tree/mode bindings. It also requires the entire preparation `source` object to equal the H0 source object, including root, commit, tree and inventory descriptor. A matching inspection-module hash or a `DRY_RUN_READY` report is insufficient. These are existing source predicates.

The inspected evidence cannot satisfy them:

| Evidence | What it supplies |
| --- | --- |
| P07 design | Explicitly unavailable operational fields; no executable receipt. |
| P09 | Exact archive observations, but an explicit stop before any installation plan, installation or executable inspection plan. |
| P19 | Raw actual-input observation and source-file identity. |
| P20 | A separate Python environment containing seven locked distributions. |
| P21 rebind | Preservation of the selected P20 environment and source inputs. |

The ledger review found no eligible pair in its declared, bounded evidence scopes, and the Director supplied no other exact paths. This is **not a claim that no installed tree or receipt exists anywhere**. Its three exact historical P09 paths were reported absent; this reviewer did not repeat host observations. No complete current H0 source-inventory descriptor or actual preparation pair was available for a full-object equality test.

## Stopping decision

P21's selected boundary excludes preparer invocation and Node/dependency installation. Creating the missing evidence now would expand the phase. The correct result is a blocked H0 prerequisite with accepted static preservation evidence. Do not fabricate a partial operational plan, copy an old receipt into a new source binding, or label this finding a product exception.

The next fresh bounded scope should recover the authenticated Node/C195 inputs, freeze one clean actual source object and complete archive/destination mappings, independently review the unchanged-preparer plans, and obtain the exact reports/indexes. Existing exact trees can yield `ALREADY_PRESENT_EXACT` through a reviewed no-apply check. Absent destinations require separately selected nonreplacing preparation; `DRY_RUN_READY` alone does not close the gate. Partial or changed content must be refused.

Use the same frozen clean source object for preparation and the later H0 plan. Preserve all older reports. Stop that future phase at accepted input evidence or its first concrete blocker, then deliver. H1, the original seven/full routine, R03, integration/R04 and parent closure/R05 remain later gates.

Recommend recording C271 as blocked on this input prerequisite, with the parent/issue open, PR draft/unmerged and branch retained. Canonical state and delivery remain Director-owned. N57 remains an external review obligation with no runtime pass or skip inferred.

## Evidence

The JSON companion binds the current source predicates, P09 reports, ledger advisory and accepted rebind outcome by exact hashes. No further observations, preparation or tests were run for this decision. Technical work is stopped; documentary publication and verified partial delivery may continue.
