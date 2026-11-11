# C200 exporter repair and one new qualification cohort

**Decision identity:** `OK-QUAL-STATIC-TRAY-C200/0.1.0`  
**Date:** November 11, 2026, America/Denver  
**State:** adopted for bounded engineering, conditional on independent approval of exact executable inputs before native execution  
**Mapping retained:** `OK-MAP-STATIC-TRAY-001/0.1.0`; selected experimental profile `ontokin.static-tray/0.1.0`

## Observed reason for this revision

[C199](../static-tray-qualification-c199/RESULTS.md) implemented the two source
routes and shared static-tray constructor. Its one native qualification
invocation stopped at N01. The pinned exporter accessed an uninitialized
`loglevel` key, and its inactive action-filter callback accessed an absent Scene
property. It consumed **one construction start**, with **zero accepted
transactions, GLBs, receiving starts or actual-delivery checker starts**.
N02–N12 were not started. The failure was not a timeout.

The C199 lock, independent approval, ledger, raw process logs, result review and
partial saved scene remain immutable evidence. No old slot is recovered, no
old ledger is reset, and the old coordinator is never resumed. The observed
published recovery baseline is `e8df6496033b13ac7e387c9525fc83c5fada1453`.
Its source bytes and the distinct original local implementation identity must
remain distinguishable. [QUALIFICATION.json](QUALIFICATION.json) pins the
preserved failure evidence and the new allowance.

## Bounded implementation decision

Repair invocation of the same Blender 4.5.3/build `67807e1800cc` exporter. Bind
the supported negative logging sentinel to its actual effective logging/debug
behavior. Define the inactive action-filter callback policy while retaining the
complete explicit property inventory. Retain observed startup measurements
before the export can fail. [Compatibility record](EXPORTER-COMPATIBILITY.md)
explains the exact source path and focused controls.

No installed Blender source is changed. The shared constructor geometry,
canonical arithmetic, source semantics, both frontends, independent reader,
receiving measurements, fixed materials, fixtures and tolerances remain as
adopted. The shared qualification result's scope sentence may name its cohort
through the exact input lock instead of hardcoding C199. That editorial repair
changes no measured gate or process behavior.

## Separate execution authority

This revision conditionally authorizes **one new C200 qualification cohort**,
with twelve independently reviewed construction slots, each permitting at most
one start, and at most one receiving process and one actual-delivery Node check
per successful corresponding slot. It is a new qualification of repaired
bytes, not unused allowance from C199. Including the retained C199 failure,
the combined construction ceiling is thirteen; the combined receiving ceiling
is twelve. Failures consume starts. The new schedule stops at the first
unexpected outcome and permits no automatic retry or repaired continuation.

The [qualification protocol](QUALIFICATION.md) preserves all C198 cases, order,
expectations and numeric limits. The independent reviewer must approve the
exact C200 lock and this revision identity, explicitly acknowledging the
consumed C199 failure. The supplied preparation scripts cannot create an
approval. A new directory alone supplies no execution authority.

Preparation permits one separately reviewed cohort of exactly three read-only
Node controls: synthetic Q01 and Q03 positives, then a changed-transform
negative. A new hash-bound harness supplies the verified current dependency and
host paths to the unchanged historical test implementation. It must reject
missing dependencies rather than report skipped controls as passes. Preserve
its exact inputs, each actual process receipt and failure; stop on the first
unexpected result and do not repeat the cohort. These starts are additional
preparation checker starts, not any of the twelve actual-delivery checker
slots. No Blender, export, receiving Blender, lifecycle or author starts are
permitted by this preparation allowance. The independent preparation review
must bind the harness, test, probe, dependencies and expected controls before
this cohort starts; native readiness approval follows its actual result.

Child-free CPU checks may inspect the exact pinned exporter functions and
exercise production supervision/finalization seams. They establish only their
stated scope. The unchanged L-R1 lifecycle implementation and its completed
evidence may be reviewed by exact byte identity; no additional lifecycle child
or grandchild allowance is created here. Node version and trusted `ldd`
inspection commands are dependency observations, not geometry checks or native
constructions, and are recorded separately.

## Preserved boundaries

Source execution stays at **100,000 operations / 30,000 ms**. Each actual
qualification transaction retains its original **65,000 ms** total, including
construction/reader at most 30,000 ms, receiving at most 30,000 ms, promotion
at most 3,000 ms and cleanup at most 2,000 ms. All output, polling and process
cleanup bounds remain fixed. The observed compatibility failure supplies no
basis for increasing them.

Only successful complete technical qualification can lead to a later separate
tray-admission protocol. That protocol retains four native exports total,
one baseline and one clean regeneration per route, including failures. Timed
authors remain later. The inherited full regression remains **FAILED**:
4,239 distinct passing methods and thirteen torque-read methods **NOT RUN**
after the unchanged 30,000 ms setup failure. General contact, live destination
physics, comparative benefit, external compatibility roles, full release and
the [complete OntoKin goal](../../../GOAL.md) remain open.
