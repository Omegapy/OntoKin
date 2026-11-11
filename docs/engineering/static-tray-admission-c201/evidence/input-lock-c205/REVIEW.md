# Independent C205 input-lock component review

**Decision: APPROVE_COMPONENT_ONLY.** No component blocker remains on the reviewed revision. This decision does not approve a production input lock, current host, coordinator or native invocation.

## Exact candidate

- Commit: `28bf6d74f651b22acc0ee5a4154dcd21b861c81b`
- Tree: `7acaeb92a51d88fd3c10f3edaed72e651eb42cb2`
- Base main: `5183504302ad0c21f1e9e91c6ad146eee64a22c8`
- Changes: `input_lock.py`, its dedicated CPU test module, and `INPUT-LOCK-C205.md` only.

All 50 reviewed source, test, protocol and dependency-file bindings match this exact candidate. Its worktree was clean at readback. The repository, approved protocol, earlier ledger and historical C199/C200 inputs were read without modification. Detailed identities and hashes are in `CANDIDATE-BINDINGS.json` and `REVIEW.json`.

## Evidence and findings

The implementer's final cohort passed 72 methods, with zero failures, errors or skips. I inspected its complete retained result and compared the three committed file hashes with the reported tested bytes; I did not repeat that cohort. Separately, I executed 23 independent controls against the real validator. All passed, and source/test bytes stayed unchanged during that run. The controls use labeled synthetic fixtures and actual filesystem operations. Product subprocess, fork and shell launch seams were blocked; native, receiver, Node, lifecycle and timed-author starts were zero.

The independent controls cover exact source/dependency hashes, missing fixed roles despite fixture resealing, omission relative to a separately sealed closure, a dependency reachable only through a frozen constructor, schedule/receipt boolean-versus-integer confusion, duplicate JSON fields, incomplete/self-issued/mismatched approval, FIFO/symlink reads, replaced authority, consumed authority with a new output directory, nested alternate path spellings, safe native flags and Blender environment, extra Node evaluation arguments, populated environment roots, broad host namespaces and singleton loader roles. The passing baseline retains all execution and admission authorization fields as false.

Draft review identified and resolved four material issues:

1. **Path ancestry bypass.** The draft accepted a nested output with a POSIX `//` spelling. The original failing helper and public-validator controls, exact draft source and fixture are retained. Final absolute-path validation rejects that spelling, and the public control now passes.
2. **Frozen dependency traversal.** Preseeding the visited set with frozen bindings skipped their outgoing dependencies. Root and reviewer independently identified this by inspection. The fix starts with an empty visited set; a real positive control proves that a dependency reachable only through the qualified constructor is accepted. This was repaired before the first independent full control run, so no failed execution is claimed for it.
3. **Clean launch compatibility.** Generic argv membership and a minimal environment could not express the qualified native policy. Final validation fixes inherited safe Blender flags and expanded job paths, exact Node policy and loader, and independent per-slot environment roots with the qualified variables. Unsafe mutations reject even when fixture plan digests are deliberately resealed.
4. **Host namespace compatibility.** Requiring a whole host namespace to be disjoint from repository/output roots could not describe real OS inputs spread through the filesystem. The namespace may now be `/`; checks apply to the actual bound host and gate files. The broad-namespace positive control passes, while a host file hidden inside the repository rejects. The module-loader role also requires exactly one member.

The original negative evidence remains separate from final passing controls. No failed record was rewritten as a success.

## Trust and integration boundary

`TrustedContext` pins independently obtained source identities, lock/approval/closure/launch-plan digests, reviewer and gate issuers, and the persistent authority identity. It is immutable under normal API use. The implementation deliberately cannot authenticate its caller, observe Git or the running interpreter, or establish that an arbitrary context was retained across a restart. A future bootstrap must establish those facts from real inputs and independently received review. Creating context fields from a candidate lock would defeat this trust boundary.

The graph verifier checks a complete *declared and independently sealed* closure. It does not discover omitted dynamic imports, ELF loader dependencies, package aliases or undeclared reads. Symlink and hardlink inputs conservatively reject. Actual alias inventory/bootstrap integration remains necessary for the intended host; it is not supplied by the fixture corpus. No production approval or complete current-host lock was created.

The component is a read-only preflight snapshot. It cannot retain executable file handles, reserve a stage, enforce process deadlines, validate transaction outputs or create native readiness. A later coordinator must preserve or revalidate the inputs before use, safely create the per-slot environment subdirectories, and use the existing exclusive ledger with the same trusted authority. Initial empty-directory checks cannot replace runtime integrity checks after output directories acquire content.

## Next gate and preserved limits

Root still owns applicable existing checks, integration, actual-main verification, lease closure and handoff delivery. Component approval remains reusable only while the reviewed input bytes match.

The next bounded implementation is C201 transaction/readback compatibility. Full orchestration, accepted-source/regeneration resolution, equality and sibling preservation, cleanup/deadlines, atomic promotion, complete actual-host closure and independent native readiness remain later gates. C201 starts remain zero; C199/C200 remain closed.

The inherited full regression remains failed: 4,239 distinct passing methods and thirteen torque-read methods not run after the unchanged 30,000 ms setup timeout. Existing visual limits, missing external compatibility evidence, broader release requirements and unestablished authoring advantage remain unchanged.
