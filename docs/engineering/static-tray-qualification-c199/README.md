# C199 — finite static-tray implementation and qualification

This checkpoint implements the explicitly selected `ontokin.static-tray/0.1.0`
prototype under the [C198 mapping decision](../static-tray-mapping-c198/ADOPTION.md).
The [actual qualification result](RESULTS.md) is **stopped at N01 after an exporter
failure**: one construction start, zero accepted deliveries and no receiving run.
The profile remains unqualified. [C200](NEXT-TASK.md) addresses the observed
pinned-exporter compatibility errors under a new reviewed qualification protocol.

It uses the existing OntoKin construction compiler and a separately identified
direct-Python source route. Both routes produce one canonical record and use
the same static Blender constructor. No existing runtime default is changed.

## Implementation and acceptance

The implementation is in [prototypes/static_tray_v01](../../../prototypes/static_tray_v01/).
Its geometry is limited to two roots with six centered boxes each. It preserves
the specified semantic identities, ownership and following metadata, metre units,
the finite rotation subset and fixed tray/payload materials. It creates no
rigid bodies, constraints, animation or simulation.

The [source-admission note](SOURCE-ADMISSION.md) defines the finite direct-Python
execution surface and the bounded input reads. The independent GLB reader is
in [tools/static_tray_reader_v01](../../../tools/static_tray_reader_v01/).
It derives its expected geometry separately from the contract's decimal inputs;
it does not import or execute the source lowerer or native geometry constructor.
The receiving process reopens the actual saved native scene, then clears it and
imports the delivered GLB. It measures both and renders one review image.

An accepted transaction means its immutable candidate passed source, delivered
geometry, receiving and cleanup checks before conditional pointer promotion.
Profile qualification additionally requires the delivered corruption controls,
paired byte equality, clean regeneration, unchanged right siblings, all assigned
native cases, visual inspection and independent result review. Neither result
admits a later public tray task or establishes an authoring advantage.

## Execution control

The constructor and receiver use the exact C198-pinned Blender 4.5.3 distribution,
build `67807e1800cc`. Its archive, executable, bundled Python, glTF implementation
and host shared-library closure are inventoried. The lock expands all commands,
environments, source inputs, settings, native slots and output paths before
independent approval. Unbound repository bytecode and ambient Python site
startup are excluded from the locked host bootstrap.

The source allowance remains 100,000 operations and 30,000 ms. Each qualification
transaction has one 65,000 ms monotonic deadline: construction and independent
reading at most 30,000 ms; receiving at most 30,000 ms; promotion at most 3,000 ms;
cleanup at most 2,000 ms. A later stage requires its full remaining allowance.
The supervisor consumes an assigned slot at actual process start, retains
failures, and never retries a native or receiving process.

Success finalization requires a durable result, a matching terminal receipt,
both immutable candidate closures and the expected accepted pointer. An
uncertain write retains a pending marker and stops further slots. The outer
in-process alarm is suspended while the separately clocked subprocess supervisor
performs mandatory process-group cleanup; only the unspent original deadline
is restored afterward.

## Preparation history

All preparation failures and repairs remain evidence. An early lifecycle cohort
passed its original controls, but independent review found missing checks and
incomplete contemporaneous input binding. It does not qualify the later bytes.
The separately reviewed [L-R1 amendment](LIFECYCLE-AMENDMENT.md) authorized exactly
one replacement cohort against [its exact input lock](LIFECYCLE-INPUTS.json).
That cohort passed all eight cases and the
[131-check independent result review](evidence/lifecycle-r1-review/RESULT-REVIEW.json).
It consumed eight direct stub starts and one grandchild, for historical totals
of sixteen direct starts and two grandchildren. These are controlled lifecycle
processes, not evidence of actual Blender cancellation or simulation.

The [transaction preparation receipt](evidence/transaction/PREPARATION.json)
records focused, child-free tests of result persistence and the interaction
between the host alarm and process cleanup. These tests supplement the lifecycle
cohort; they do not create another process allowance.

## Preserved limits and next gate

This checkpoint does not change the C193 adapter, inherited contracts, historical
fixtures, shared compiler or old tests. The inherited full regression remains
**FAILED**: 4,239 distinct methods passed and thirteen torque-read methods were
**NOT RUN** after the unchanged 30,000 ms setup failure. The focused checks here
do not change that result.

The complete [OntoKin goal](../../../GOAL.md) remains in force. General contact,
live destination physics, production backend coverage, compatibility and external
validation roles, comparative authoring benefit, full regression and full-product
acceptance remain separate unmet gates.

The exact execution outcome, consumed and unused native slots, integration result
and next bounded action are recorded in the closing checkpoint files. The
[handoff tools](handoff_tools/README.md) preserve the exact committed source and
retained history, verify the ZIP and restore it without network access. Their
recorded C196 audit is inherited evidence verification, not a new native trial.
