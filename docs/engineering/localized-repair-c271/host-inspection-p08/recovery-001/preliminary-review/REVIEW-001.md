# P08 preliminary static source review

Reviewer: `/root/implementation_review`. Candidate: `session/PRELIMINARY-MODULE-001.py`, 53,013 bytes, SHA-256 `b0838122bf76d052712379d39dbd82a5c93a1d76eb22d57205ad23ce83ac1a7d`, lines 1–897. The snapshot hash was read back and matched the Director's supplied identity.

**Disposition: mandatory static corrections identified; no final acceptance decision.** This review reads source only. No candidate import, compile, test, actual host inspection, runtime preparation, Node/ldd, Git operation or project subprocess occurred. The still-unwritten public observation/state-machine tail is known pending work and is not counted as a defect. Later complete-candidate and pre-execution fixture mapping reviews remain required.

## PRE-01 — Present alternate RTLD candidates need full executable closure

**Priority: high. Locations: 775–789, 819–829. Controls: HI06-E, HI07-E/G.**

Each present `rtld_candidates` row is bound by file hash at line 785. However, `all_roots` includes the selected Node interpreter, Python, shell, explicit commands, Git and extensions, but not the other present RTLD candidates. Those candidates also need not appear in `host.files`/aliases or `resolution.images`. The exact RTLDLIST comparison therefore does not establish complete executable coverage for all admitted candidates.

Concrete static witness: add a second present RTLD candidate with an independently bound file descriptor and matching RTLDLIST script text. Leave that candidate out of `images` and give it an undeclared DT_NEEDED dependency. The reviewed function contains no check requiring its ELF metadata/dependency closure. The independent script review is responsible for deciding executable branches; once a present candidate is admitted as potentially executed, file identity alone cannot replace the required interpreter/shared-input binding.

Correction: require every admitted present RTLD candidate in the canonical alias/file inventory and in the applicable ELF closure, including interpreter and transitive needed edges. Distinguish absent candidates from present executable candidates. Add a negative fixture whose affected candidate alone lacks its image/dependency, without mocking the closure predicate.

## PRE-02 — Symlink target normalization omits traversed components

**Priority: high. Locations: 432–451, especially 446–450. Controls: HI07-D, HI10-B.**

`_existing_chain` applies `normpath` to a symlink target before adding it to the pending path set. It also adds only the final resolved target. Both operations remove intervening components from targets containing `..`.

Concrete static witness: `/fixture/link` points to `walk/../payload`. The filesystem must traverse `/fixture/walk`, but both the normalized and final resolved pending targets are `/fixture/payload`. A guard set can omit `/fixture/walk`; `_existing_chain` does not demand it. Replacing that directory's inode while leaving the final target unchanged is therefore outside the enforced guard set.

Correction: preserve and guard every component actually traversed during symlink expansion, or explicitly refuse this unsupported target form. Do not normalize away a component before determining which identities the plan must bind. Keep normal source/role aliases compatible where the accepted design permits them.

## PRE-03 — PT_DYNAMIC is not checked against its loaded file mapping

**Priority: high. Locations: 595–611 and 634–639. Controls: HI08-B/C/D.**

The ELF parser reads PT_DYNAMIC directly from its `p_offset`, but does not require its `p_vaddr`/range to correspond to the same file bytes in a PT_LOAD segment. It checks a load mapping only for the dynamic string table. It also omits the load-segment `p_vaddr`/`p_offset` alignment-congruence check.

Concrete static witness: one PT_LOAD maps file offset 0 to virtual `0x400000`. A PT_DYNAMIC declares `p_offset=0x800` and `p_vaddr=0x400900`, with both ranges inside the file. The parser reads a dynamic table at `0x800`, while the virtual mapping describes bytes at `0x900`. Existing file/table-size checks do not reject this inconsistent image. A plan's declared metadata can match the parser's table even though the segment mapping is malformed.

Correction: require an unambiguous admitted PT_LOAD mapping of the dynamic table, consistent file/virtual offsets and bounds, and valid load alignment congruence. Reject inconsistent/overlapping mappings whose semantics the bounded parser does not establish. A synthetic file is sufficient for this control; no binary execution or real runtime input is needed.

## PRE-04 — glob limit is enforced after unbounded enumeration

**Priority: medium. Locations: 727–734. Controls: HI07-C, HI08-E; accepted 60-second static/finite-input bounds.**

`sorted(glob.glob(pattern))` materializes the complete match list before checking the 2,048-result ceiling. Multiple wildcard directory components can make the enumeration much larger than the admitted closure. No deadline callback runs during that traversal. The later limit detects excess only after spending the resources it was meant to bound.

Correction: use finite, explicitly admitted directory traversal with per-entry count/deadline checks, or conservatively reject unsupported include-pattern forms. Do not treat a post-materialization length check as bounded enumeration. Preserve the exact included-file set check.

## PRE-05 — Loader inputs can be absent from the emitted host lock

**Priority: high unless a later integrated validation explicitly closes it. Locations: 689–740, 743–852; compare 538–561. Controls: HI07-C/G, HI20-C.**

Present loader inputs are independently bound in `resolution.loader_inputs`, but `_check_resolution` does not tie those file bindings to `host.files`/aliases or `roles.loader_configuration`. `_check_host_static` checks only the role-union/set equality, so an unrelated already-listed file can satisfy the nonempty loader-configuration role while a real cache/config/include file is omitted from the eventual HOST inventory.

Concrete static witness: keep the true cache/config descriptors in `resolution.loader_inputs`, omit their names from HOST roles/aliases/files, and put an unrelated admitted regular file in `loader_configuration`. The reviewed guards can still check the plan-side loader files, but the P06-compatible HOST loses their consumer-visible binding. P07 explicitly requires representable admitted loader files in HOST and forbids dummy role filling.

Correction: enforce the appropriate complete relation between present admitted loader inputs and HOST aliases/files/loader roles; absence records remain in sidecars. Apply the same principle to every admitted executable input. If the unfinished tail supplies this relation, identify its exact live predicate and exercise the omission there; otherwise fix the static validator.

## PRE-06 — Strict type and parser-contract checks are incomplete

**Priority: medium. Locations: 260–275, 354–410, 855–895. Controls: HI01/HI03-I, HI13.**

Three concrete examples follow from the current code:

1. `plan['limits'] == LIMITS` accepts numerically equal floats such as `direct_starts: 2.0`; `runtime['candidate'] == NODE` similarly accepts a float byte count. Explicit exact-type checks exist for command integers, but not these closed fixed records. The accepted contract rejects unexpected types.
2. Valid JSON numeric spelling `1e999` decodes to a nonfinite float. `_canonical` then raises `CHI-EVIDENCE`, which `_decode` rethrows, instead of the required input `CHI-PLAN` rejection. Literal NaN/Infinity and overflowing ordinary number syntax need the same input-refusal boundary.
3. `parse_ldd_output` checks the expected-resolution keys but not the exact value shapes. Supplying `vdso` as a string makes `name in expected_resolution['vdso']` a substring test. For example, a kernel row named `evil` can satisfy a malformed string `prefix-evil-suffix`. This does not bypass the normal generated resolution path, whose kernel list is checked earlier, but it violates the public pure parser contract and can mask malformed fixtures.

Correction: enforce exact finite field types before equality checks; classify canonicalization failure during decode as an input error; validate the public expected-resolution mapping, interpreter and exact permitted vDSO list before parsing output. Add isolated negative cases; do not execute a runtime.

## Observations that are not final acceptance

The reviewed prefix separates external digest types from observed plan data, rejects unknown top-level plan keys, derives a fixed output topology with distinct raw/committed outcome paths, uses nonblocking/no-follow regular-file reads and preserves file identity across reads. The ldd parser validates every output row and requires exact expected library/interpreter mapping. Those are useful source observations, but the unfinished bootstrap, observation orchestration, atomic writer, failure state machine and actual test routing still need review.

Synthetic fixtures may replace actual host/runtime facts at explicit seams. The mutated admission/parser/path predicate itself must stay active; exact production Node/archive/constants need separate assertions. This review does not require H0 preparation, real runtime retrieval, or an operational host plan.
