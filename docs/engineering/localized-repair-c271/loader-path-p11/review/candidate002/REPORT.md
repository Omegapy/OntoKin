# Independent review of P11 candidate002

**Verdict: revision required before adoption.** The finite design is supportable, but the frozen control corpus does not yet establish all of its claimed boundaries. No product implementation or operational host qualification was reviewed or executed.

The exact reviewed manifest is `session_evidence/loader_design/candidate002/CANDIDATE-MANIFEST.json`: **30,583 bytes**, SHA-256 **`563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4`**. Candidate002 remains immutable. A later candidate must preserve this attempt, the findings below, and all original expected records.

## Exact checks and what they establish

The reviewer-authored `audit_candidate.py` passed **1,573 independent static checks**. It verified all 139 payload files and 14 supporting files, the complete 127-file fixture inventory and its physical modes, all 93 case/oracle mappings, 16 cited local source identities, and 22 protected source identities. It independently decoded the 26 ELF headers, program tables, dynamic entries, string tables and raw metadata from inert bytes, rather than importing the product parser or accepting the author's reported metadata. It also decoded all eight auxiliary-vector assets as little-endian type/value pairs. The complete check results and decoded facts are retained beside this report.

The separate reviewer-authored `review_case_semantics002.py` passed 80 of 83 case-specific assertions. The three failed assertions concern missing long-path ancestor guards and the masked N69 boundary. Every one of the 73 negative cases has a checked supplied cause; the existing four legacy refusal controls match current source guard ordering and exact reason text. The three drift controls retain their preapproval observations and intended cause. The initial integrity pass is not an acceptance of control adequacy: the separate failed semantic result is retained without changing either input or expectation.

These are artifact and source checks. They do not count as product tests, callbacks executed in production, host observations, target starts, H0, H1, the original seven, or the full routine.

## Findings requiring a distinct corrected candidate

### DR-01: the 4,097-byte expansion refusal is masked

N69 has four overlimit strings: the raw pre-normalization path is 4,097 bytes, the subject path is also 4,097, and two variant paths are 4,113 and 4,101 bytes. An implementation could omit the intended pre-normalization bound and still return the same `LP-BOUND` refusal because a different path is too long. P07 and N69 need the same explicitly synthetic base-only suffix model and a short executable basename. Only N69's pre-normalization string should exceed 4,096; subject, origin, derived path and all supplied variant paths must fit. Existing outcome records can remain unchanged.

### DR-02: the long-path positive lacks ancestor facts

P07 and N69 each need 67 existing directory guards for their supplied subject/derived path ancestry, but contain five, with 63 needed ancestors absent and one unrelated guard. P07's positive context therefore does not provide the origin proof required by the decision. Complete the synthetic ancestor inventory, retain coherent identities for origin, parent and sibling `lib`, and keep the filesystem states inert. An adapter must not silently invent the omitted guards.

### DR-03: new byte limits need an explicit encoding rule

The decision specifies a byte ceiling while the existing `_absolute` implementation measures Python string length. Its separate reference to existing bounds does not say how the new pre-normalization string is encoded. Define the new field domain or byte encoding precisely, without changing legacy `_absolute`. A narrow ASCII-only rule for the new subject/origin/derived/variant paths and suffixes is acceptable. Freeze a coherent non-ASCII refusal so a future adapter cannot satisfy the rule merely by reusing a character-count check.

### DR-04: the claimed finite-ceiling coverage is incomplete

The control contract claims coverage of every new finite ceiling. It has no exact variant-document read-size pair at 4 MiB and 4 MiB plus one, nor a pre-normalization path-component pair at 128 and 129. Add isolated controls or withdraw the unsupported coverage claim with an explicit accepted deferred obligation. A raw bounded-read positive is acceptable as a separately named seam; it cannot be presented as valid variant JSON, a valid closed schema, or a profile acceptance. The existing canonical JSON requirement must remain intact.

N31, N70, N71 and N72 do isolate their named early limits. N31 contains 257 otherwise complete auxiliary pairs. N70 has 4,097 union names across 17 images with at most 256 names each, and a candidate product of 4,097. N71 has 129 suffixes while other size ceilings fit. N72 has 257 names and 128 present variants, producing 32,896 checks while the separate name and suffix limits fit. Their later incomplete context cannot mask the exact expected early selector because those later checks have different stages/rules.

### DR-05: Git transport needs a materialization contract

Physical mode `0o600` is meaningful for these inert fixtures, but Git regular-file mode does not preserve these permission bits. A normal checkout can therefore have exact bytes with mode `0o644` and fail the frozen mode check. This does not require changing the frozen bytes or relaxing `0o600`. Document a bounded procedure: verify Git blob bytes, exclusively create a fresh private fixture copy, apply only recorded inert modes there, and verify exact inventory, hashes, sizes and modes before controls. Do not chmod the source checkout, follow aliases, overwrite existing destinations, or change the real operational Python's `0o755` descriptor. Include the rule in the corrected frozen candidate so later adoption is self-contained.

## Substantive design assessment

The proposal is conditional and narrow. It admits only the exact selected direct author Python and the literal raw RPATH `$ORIGIN/../lib`, under a new exact schema/profile pair. Its output remains raw metadata; the derived directory is separate. Public standalone parsing and the old schema/profile continue rejecting tokens. The current source has two relevant parser call sites, in `_check_author_runtime` and `_check_resolution`; the design names both and requires the same plan-specific admission on initial and repeated validation.

The origin proof distinguishes direct execution from an explicit loader invocation, aliases, cwd, evidence-copy locations and environment fallback. It requires an exact current kernel executable witness, subject identity, nonsecure auxiliary witness, nonsymlink ancestry and a single guarded sibling derivation. The helper-only synthetic positives cannot pass the real selected-image pin, and N25 explicitly retains that refusal. The real selected image, its actual origin, loader variant set and sibling directory contents remain unavailable for operational qualification.

The nonselecting condition is a valid conservative way to avoid introducing a general loader algorithm. It includes the union of all declared needed names, including extensions and other roots, across a separately reviewed complete hardware/TLS suffix set. Any matching entry of any kind refuses. This does not flatten RPATH inheritance or RUNPATH scope. It also does not establish behavior for arbitrary future `dlopen` targets outside the finite declared closure. Exact loader bytes and independently justified variant completeness remain later prerequisites; generic glibc documentation does not prove the selected host meets them.

For the new profile, complete origin, static closure and nonselection checks must precede `_load_helpers`. Source inspection confirms the proposed earlier `_check_host_static`, `_check_author_host_bindings` and `_check_resolution` functions do not depend on imported project helpers. The initial raw token read grants no authorization by itself. The design preserves the old profile's order, requires full proof on `_recheck`, adds all relevant real paths and absence witnesses to snapshots, and retains a small final kernel witness under the existing command clock. Kernel namespace and undetectable concurrent mutation remain declared trust boundaries, not solved properties.

The proposed future edit surface is explicit: the existing inspector module and one new focused test module. It does not authorize implementation in P11. Closed P06 consumers, command shapes, fixed stdout predicate, pins, source budgets, 135 legacy inspection methods, and 40 P10 mapping controls remain protected. Current protected source bytes matched their declared identities. Later executable verification and source review are still required to establish that an implementation actually obeys this design.

## Source support and limits

The reviewer read the exact cited local parser, plan, runtime, closure, snapshot, recheck and launch boundaries and the retained P09/P10 observations. The independent P10 observation supports the raw RPATH, six direct needed names, selected-image identity and `DT_FLAGS_1=1`. It does not establish a full closure or harmless expanded directory.

Primary references were independently opened:

- [Published glibc Linux origin implementation, Debian 2.36-8](https://sources.debian.org/src/glibc/2.36-8/sysdeps/unix/sysv/linux/dl-origin.c/): direct process origin uses the kernel executable link; its environment fallback is excluded by the proposed profile.
- [Published glibc loader implementation, Debian 2.36-8](https://sources.debian.org/src/glibc/2.36-8/elf/dl-load.c/) and [ld.so manual](https://man7.org/linux/man-pages/man8/ld.so.8.html): RPATH/RUNPATH ordering, inheritance and token behavior support the conservative nonselection rationale.
- [Upstream explicit-loader origin discussion, March 2025](https://sourceware.org/pipermail/libc-alpha/2025-March/165169.html): supports treating explicit-loader semantics separately. A proposed patch is not evidence of deployment on the selected host.
- [glibc invocation manual 2.39](https://sourceware.org/glibc/manual/2.39/html_node/Dynamic-Linker-Invocation.html): distinguishes explicit and implicit loader invocation.
- [Kernel executable link manual](https://man7.org/linux/man-pages/man5/proc_pid_exe.5.html) and [auxiliary-vector manual](https://man7.org/linux/man-pages/man3/getauxval.3.html): support executable-path and secure-mode witness requirements and their availability limits.
- [Published auxiliary constants](https://sources.debian.org/src/glibc/2.36-9%2Bdeb12u10/bits/auxv.h) and [ELF auxiliary type definition](https://sources.debian.org/src/glibc/2.36-8/elf/elf.h/): establish `AT_NULL=0`, `AT_SECURE=23`, and two 64-bit fields for the reviewed ELF64 representation.

Version-fixed published source identifies semantics for those source versions. No retrieved page proves the actual selected loader version or source correspondence. Original failed source retrievals, oversized tool outputs, and the reviewer's mistaken exploratory filename are recorded in the attempt history. No product source, author candidate, Git state or external storage was modified by this reviewer.
