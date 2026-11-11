# C207 independent review

**Decision: APPROVE_CWD_COMPONENT_ONLY.** The bounded working-directory correction is suitable for integration after the integrator's remaining applicable checks. This decision does not authorize a native invocation or establish production readiness.

## Exact reviewed candidate

- Commit: `bd9fbf1487e557b9c21baf1d39e7b9cb818d4773`.
- Tree: `701e7ea878434c6f6d06366eaa3f08754d4c55d7`.
- Base: published C206 main `2a1ac8ccbdc290942e88504c640790b1bda9229c`.
- Branch: `work/c207-cwd-impl-cbf19c`.
- Working tree was clean when final controls recorded their binding.
- This independent reviewer changed no implementation file and made no publication or integration write.

The candidate changes six files: the C201 input validator and transaction component, their two existing test modules, one new directory-control test module and the C207 contract document. The exact files read by this review, including helpers and qualified contracts, are recorded in [final/SOURCE-BINDINGS.json](final/SOURCE-BINDINGS.json).

## Contract and source decision

The input validator now binds each command's working directory to that command's distinct stage-output directory. Its existing command, environment, job-path, disjointness, file-identity and independently reviewed plan checks remain intact. Thus a coherently altered launch plan still requires a new trusted plan digest; simply changing the outer lock's digest does not make it acceptable.

The transaction component no longer allows its outer command and underlying supervisor receipt to describe different working directories. Both must agree with the exact locked output path. Existing construction and receiving job validation already binds `output_directory` to that same path. Accepted evidence retains the original launch directory after its files move into the sealed store; read-only inspection continues checking the original process binding.

Removing the three obsolete fixture-purpose-only checks allows the validated `production-inputs` classification through this component. The validated-factory token and matching purpose checks still apply. Input validation, preparation and acceptance retain false execution/readiness/admission flags. This change does not authenticate caller observations or provide any launcher.

The decision agrees with the unchanged qualified supervisor, worker and receiver. The supervisor passes the stage as the child's actual cwd, and both native script prefixes check cwd against their job output. The same choice gives the future Node command a consistent plan. Its actual C201 probe, wrapper, jobs and retained-output contract are still missing. Historical Node code and a synthetic role file cannot substitute for that implementation.

The four approved protocol documents never required repository cwd. Their byte identities remain unchanged, so this implementation correction does not amend the frozen schedule, ceilings, qualified mapping or admission rules. [Contract audit](CONTRACT-AUDIT.md)

## Independent executed evidence

All **29 independent CPU methods passed**, with zero errors and zero skipped tests. The run used the available Linux x86-64 CPython 3.12.14 environment. It is the same available environment used by the other agents, not an independent machine or operating system.

The controls cover all twelve slot/stage plans; repository, relative, noncanonical and cross-stage cwd rejection; cross-slot output aliasing; wrong output and job arguments; a coherent path change with a stale trusted plan; replaced and symlinked directory identities; actual construction/receiving job bindings; mismatched outer and underlying process evidence; accepted-source regeneration and preserved baseline pointers; failed precommit pointer replacement; and `UNKNOWN` after a real local pointer replacement followed by simulated interruption.

Three calls to the qualified supervisor's `Popen` boundary were deliberately intercepted before a child existed. The observed arguments and retained failed-launch receipts used the planned construction, receiving and Node directories. The Linux descendant-reaping setup was also mocked, so this control did not change host process settings. These are launch-argument controls, not native execution evidence.

The exact `worker.main` and `receiver.main` AST prefixes were exercised with fixture job files. A sentinel stopped each valid prefix at its first Blender API access; invalid cwd paths rejected earlier. No `bpy` module, Blender operation, native process or Node process was started. These prefix checks establish only the initial cwd contract.

The accepted-source controls used actual transaction, source-lowering, independent geometry-checking, receiving-comparison, file-sealing and pointer operations with explicitly synthetic geometry, native containers, process receipts and images. A synthetic fixture carrying `production-inputs` strings exercised binding and preparation with all authorization flags false. No actual production lock, host seal or approval was created.

[Final results](final/RESULT.json), [full method log](final/controls.log), [control script](independent_controls.py)

## Historical preservation

An independent comparison passed all **301 inherited locked-input bindings**, the **four frozen protocol documents**, and **1,033 files** across the C198/C199/C200 contract, source, fixture and evidence prefixes. These are overlapping views of preservation and must not be summed as distinct files. The protected prefixes have no tracked diff or new untracked path.

Qualified constructor, receiver, supervisor, source lowering, independent reader, stores, settings, C199/C200 lock and receipt histories, budgets and closed schedules remain exact. Nothing from those schedules was re-executed.

[Preservation result](final/PRESERVATION.json), [preservation checker](verify_preservation.py)

## Original draft result

The first reviewer run passed 28 methods and failed one due to an incorrect reviewer expectation. A precommit `OSError` correctly propagates as rejected `C201-BINDING`, whereas `C201-PROMOTION`/`UNKNOWN` identifies a completed or uncertain pointer replacement. The reviewer corrected that expectation and narrowed fault injection to the actual `state.json` replacement. No implementation change was made for this result. The exact draft script, original failing log and input bindings remain in `draft/`; [DRAFT-FINDINGS.md](DRAFT-FINDINGS.md) records the correction.

## Remaining gates and stopping point

No blocking defect remains within this bounded correction. The next implementation boundary is the C201 readback/probe compatibility component. True process provenance, current-host/dependency/alias sealing, durable trusted bootstrap, complete coordinator/ledger/control sequencing, real process deadlines, native readiness, the sole authorized four/four/four invocation, images and independent admission remain later gates.

No native, receiving, Node, lifecycle or timed-author start occurred in this review. There is no unknown remote operation. The inherited full regression remains FAILED with 4,239 distinct passing methods and thirteen torque-read methods not run after the unchanged 30,000 ms setup timeout; this review did not rerun it. Broader physics, external compatibility, measured authoring advantage and the full GOAL are unestablished.

The approval applies to the exact candidate and its reviewed bytes. Integration must verify applicable input equality or rerun affected checks if source or contract inputs change, retain the original evidence, and record the actual resulting main revision separately.
