# C266 implementation plan

Owner: `c266-root-2593880e88fd`. Branch: `work/c266-hinge-input-binding`. Base: `7818de1f17e379df50680cb94347ce86bcabb8a5`. [Scope258](https://github.com/Omegapy/OntoKin/issues/258). [Requirements](REQUIREMENTS.md) and [task state](task.json) govern this increment.

## P01. Publish scope, requirements, plan and early recovery checkpoint

Requirements: R01, R02, R03, R04, R05.

Verification: Verify startup revision/read-set, source archive audit, live refs/ownership and capabilities.

## P02. Implement provenance binding and independently authored controls

Requirements: R01, R02, R03, R04, R05, R06.

Verification: Run original and changed-input cases, independent mutations and boundary checks.

## P03. Verify published candidate and resolve independent review

Requirements: R06.

Verification: Run full applicable C253/C255/C256/C257/C258/C261/C265/C266 cohorts, workflow and preservation checks; reviewer inspects exact bytes.

## P04. Integrate reviewed scope and verify actual main

Requirements: R07.

Verification: Read lease/PR/main, merge expected head, run fresh applicable checks and verify retained head/deletion.

## P05. Freeze, verify, save, record receipt and close

Requirements: R08, R07.

Verification: Verify exact ZIP/fresh extraction/Git read-set, inspect saved identity, publish receipt and release lease.

## Ownership and verification scope

The Director owns task records, documentation, evidence integration, Git index, all remote writes, shared STATUS/CURRENT under a verified main lease, and final delivery. The implementer owns only `hinge_binding.py`. The control author owns only `test_hinge_binding.py` and its independently built fixture helper if necessary. A separate reviewer inspects the published candidate and runs adversarial checks. Shared-checkout disjoint writes are allowed; workers must not commit or modify shared state.

This isolated standard-library engineering observer is not imported by the product and changes no released runtime machinery. The complete affected regression inventory is the C253 input audit and C255/C256/C257/C258/C261/C265/C266 component cohorts, plus workflow and documentation preservation. Full product aggregate, native/visual checks, source exports, hosted workflows and other Python compatibility roles are not applicable to this increment and remain not-run, with prior failures unchanged. If shared product machinery changes, revise scope and execute its complete inherited obligations first.

After implementation and each substantive verification/integration stage, publish a recoverable checkpoint and refresh the saved recovery file. Preserve failed attempts and unknown operation identities. Stop only after verified integration, branch disposition and confirmed saved handoff receipt.

## Interrupted-session recovery

The November 18 Prompt 2 resumes this same scope and branch under Director `c266-recovery-31766bc15fec`. The former owner and original base above remain historical provenance. Published implementation and controls at `e808af1403411960ebf360aa4588c9e358d2035a` are preserved unchanged. P03–P05 remain the authorized work; no new comparator implementation is selected. See [RECOVERY.md](RECOVERY.md).
