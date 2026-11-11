# Next task: implement the prepared C201 admission protocol

C200's finite qualification is integrated through
[PR #137](https://github.com/Omegapy/OntoKin/pull/137), and actual-main applicable
checks passed at `2b2f3e7de7595099ad5f9e0176c5596220c0c2dc`.
[Integration and verification record](evidence/publication-c203/INTEGRATION.json)
Both C199/C200 schedules remain closed; their evidence is not rerun for context.

The separate [C201 protocol](../static-tray-admission-c201/ADMISSION.md) and
[bound rules](../static-tray-admission-c201/ADMISSION.json) are prepared.
Independent static review of those documents passed 171 consistency checks. Its
[implementation instructions](../static-tray-admission-c201/IMPLEMENTATION-NEXT.md)
identify the next bounded work: separate four-slot coordinator, lock,
transaction/readback compatibility, explicit references and durable state,
followed by meaningful controls, full executable closure and independent
native-readiness approval. No coordinator or admission execution is claimed.

Reconcile current main, work scope, PRs and the integration lease before editing.
The C201 preparation scope is recorded in [issue #138](https://github.com/Omegapy/OntoKin/issues/138).
Preserve the [recovered evidence](evidence/publication-c203/PRESERVATION.md),
including its original missingness observations and later source-path log
recovery. Retain the inherited failed regression and reject newly introduced
or worsened legacy behavior.

## Preserve the prepared admission boundary

Follow the independently reviewed C201 preparation protocol. Build
and review its own coordinator, invocation gate and ledger before execution.

| Route | Maximum native exports, including failures |
| --- | --- |
| OntoKin | One baseline and one clean regeneration |
| Direct Python | One baseline and one clean regeneration |

The total ceiling is four exports, with zero timed authors. Use the qualified
shared constructor and existing versioned static-tray mapping. Freeze the exact
task, source and dependency closure, commands, measurements, receiving checks,
unchanged-sibling requirements, clean regeneration comparisons, budgets and stop
rules before execution. Preserve ordinary 100,000-operation/30,000 ms limits
and inherited stage allowances unless an explicit separate decision changes
scope or allowance before use.

The current `prototypes/static_tray_v01/qualification.py` requires twelve
accepted transactions and checks, and C200's single invocation is already
consumed. A new argument of four, a cleared ledger, another output directory or
a reset invocation is not an admission coordinator. Implement the separate
four-export control path and review its failure accounting before any native
start. Neither qualification replay nor a timed author comparison belongs to
this step.

Preserve all prior failed attempts, the N05/N06 image-resolution limit and the
N07/N08 hidden right interior. Admission remains separate from general contact,
live destination physics, external compatibility, comparative benefit, full
regression, full release and the wider [GOAL](../../../GOAL.md).
