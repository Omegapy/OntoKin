# P11 independent design and control review

**Accepted for the bounded P11 design/control adoption.** Candidate004 resolves all five findings raised against candidate002. There are no remaining blocking findings within this review scope. Acceptance applies to the versioned decision and its exact inert controls; it does not authorize implementation or establish that the selected host can satisfy the new profile.

## Accepted identity and scope

| Item | Independently checked identity |
| --- | --- |
| Candidate manifest | `session_evidence/loader_design/candidate004/CANDIDATE-MANIFEST.json` |
| Manifest size | 35,041 bytes |
| Manifest SHA-256 | `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de` |
| Exact candidate inventory | 146 payload files and 29 supporting references |
| Frozen control corpus | 97 cases, 131 fixture files, 26 inert ELF images and eight auxiliary-vector assets |
| Original oracle preserved | All 93 prior expected records, projected into their original serialization, equal SHA-256 `57cd7b319d03cbe1f4f43bdd291be181af68be2405acc7e9e9812c29955b38bb` |
| Inspected product source | Commit `e0119f376441fee0fc3956852ac63110ab141011`; inspector SHA-256 `0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612` |

The original phase scope was design plus frozen inert controls. The review did not import or call product code, execute an author validator, inspect actual `/proc` or logical fixture paths, prepare a runtime, launch a target, run product tests, invoke Node or `ldd`, or perform H0/H1/full-routine/integration work. Source and artifact bytes were read as data. The reviewer wrote only assigned review evidence.

## Independent verification

The reviewer-authored static audit passed **1,675 checks** on candidate004. It verified the exact complete manifests, physical inert-file modes, case/oracle bindings, all 16 cited local source files and 22 protected files. It decoded the ELF headers, program tables, dynamic entries, string tables and raw metadata independently with standard byte operations. It also decoded the eight auxiliary-vector assets. These results are in `candidate004/STATIC-REVIEW.json`, `CHECKS.json`, `ELF-FACTS.json`, `AUXV-FACTS.json` and `CASE-FACTS.json`.

The focused revision audit checked the entire candidate002-to-candidate004 delta. It established that only P07 and N69 changed among the original fixture contexts, exactly four new contexts were added, every original ELF/auxiliary byte asset is unchanged, all 93 old expected records reproduce their original bytes, and the supplied text diff equals an independently generated diff. It also reverified candidate002's 139 payload files and 14 support files without changing them. The retained withdrawn candidate003 inventory contains exactly 148 payloads and 12 supports, all matching its external retention manifest.

The initial revision helper passed 404 of 405 assertions. The remaining assertion incorrectly required N76's otherwise coherent synthetic `/fixture` directory inode to retain P01's integer value. The new context assigns it a fresh unique inode of 1001 instead of 102. It is an initial context with no preapproval state, no stale absence-parent reference and no conflicting directory observation. A separate targeted follow-up verified that this was the only additional difference and cleared the reviewer-helper false positive. The original failed result and script remain preserved; neither candidate nor oracle was edited. See `candidate004/REVISION-REVIEW.json` and `REVISION-FOLLOWUP.json`.

Earlier candidate002 evidence remains available: 1,573 integrity checks passed, while the separate 83-assertion case review recorded three actual control-adequacy failures. Candidate001's original 127-file corpus still matches its original manifest, and its failed long-path positive remains recoverable. `ATTEMPTS.json` records successful and failed reviewer attempts, retrieval failures, bounded rereads after truncated outputs, and the helper correction. No static-check count is represented as a product-test count.

## Finding dispositions

| Finding | Resolution in accepted candidate004 |
| --- | --- |
| DR-01: N69 could refuse because several paths exceeded the same byte limit | P07/N69 now use the same explicitly synthetic base-only suffix model and short `py` basename. N69's raw pre-normalization expression alone is 4,097 bytes; every supplied path is at most 4,093. |
| DR-02: long-path contexts omitted required ancestor guards | P07 and N69 each contain all 67 required directory guards, with coherent origin, parent and sibling-directory identities. No ancestor is silently supplied by an adapter. |
| DR-03: byte ceiling was underspecified relative to legacy character counting | ASCII is explicitly required only for new origin/variant fields. The old `_absolute` behavior is unchanged. N76/N77 coherently isolate non-ASCII origin and suffix refusal. |
| DR-04: finite-ceiling coverage claim exceeded the controls | P09/N75 now isolate 128/129 pre-reduction components. The proposed separate 4 MiB document policy was withdrawn after the user's question; the existing 16 MiB reader and inherited controls are reused. No new document-size control or private reader seam is required. |
| DR-05: Git transport cannot preserve physical `0o600` permission bits | `MATERIALIZATION.md` binds a fresh private copy procedure with byte verification, exclusive creation, exact inert modes and an external receipt. It never changes operational subject permissions or makes fixture images executable. |

The component pair counts the leading root and unreduced parent component explicitly. P09's raw expression has 128 components while every supplied path has at most 127. N75's raw expression has 129 while every supplied path has at most 128. All paths in those controls remain far below the byte ceiling. The independent measurements match the author's declared revision facts.

The existing auxiliary, name-union, suffix and product negatives remain isolated: 257 auxiliary pairs; 4,097 union names with at most 256 per image; 129 suffixes; and 257 names times 128 present directories, yielding 32,896 checks. These cause-specific assertions concern supplied static context, not executed policy behavior.

## Why the finite decision is supportable

The new profile is limited to the exact selected direct author Python image and the exact literal RPATH `$ORIGIN/../lib`. It keeps the raw ELF result separate from the derived absolute directory. It requires an exact kernel executable witness, nonsecure auxiliary state, image identity, nonsymlink ancestry, and a single guarded sibling derivation. Synthetic positive controls remain private-rule examples. They cannot pass the selected real-image hash/size/mode pin; the explicit operational-binding negative preserves that distinction.

The derived directory must be nonselecting for the complete declared dependency-name union, including extensions and other roots, across all independently reviewed loader suffixes. Any matching directory entry of any kind refuses. This conservative condition preserves the selected dependency map without inventing a general loader algorithm or equating RPATH with RUNPATH. Actual hardware/TLS variant completeness must be justified against the exact selected loader, and arbitrary future dynamic loads outside the declared closure remain outside the profile.

The source review covered both parser admission sites, initial validation, `_recheck`, required paths, snapshots and final launch checks. For the new profile, complete origin and nonselection proof must precede project-helper imports. The proposed earlier host/author/resolution functions are helper-independent in the inspected source. Rechecks cannot treat a raw-token parse as cached proof of complete admission. The old profile's order and public parser behavior remain unchanged.

The variant document now uses the existing `_document` function, unchanged `LIMITS['document_bytes']` value of 16 MiB, and existing callbacks, descriptor/file-identity checks and canonical JSON decoding. The new closed variant shape is checked afterwards. Current `case_HI03` source confirms inherited duplicate-key/decoder, overlimit-input and mid-read-drift controls. Those tests were inspected as source and were not executed. This reuse removes an unsupported extra policy while preserving established safeguards. The decision and its rationale are recorded in `DOCUMENT-CAP-DECISION.json`; the withdrawn 99-case attempt is retained without relabelling it as adopted.

The future edit surface is explicit: the existing inspection module and one new focused test module, in a later separately selected phase. No P06 consumer/schema changes, global token bypass, command-shape changes, changed pins, enlarged time budgets, rewritten legacy expectations, or alternative runtime selection are authorized by this design. All 135 existing inspection methods and 40 P10 mapping controls remain later implementation obligations.

## Source support and unresolved operational prerequisites

The prior detailed review in `candidate002/REPORT.md` records exact local-source support and independently opened primary references. The final revision retains the same source identities and core semantics. Relevant primary sources include the published [Linux origin implementation](https://sources.debian.org/src/glibc/2.36-8/sysdeps/unix/sysv/linux/dl-origin.c/), [glibc loader source](https://sources.debian.org/src/glibc/2.36-8/elf/dl-load.c/), [loader manual](https://man7.org/linux/man-pages/man8/ld.so.8.html), [explicit-loader origin discussion](https://sourceware.org/pipermail/libc-alpha/2025-March/165169.html), [kernel executable-link manual](https://man7.org/linux/man-pages/man5/proc_pid_exe.5.html), and published [auxiliary constants](https://sources.debian.org/src/glibc/2.36-9%2Bdeb12u10/bits/auxv.h) and [ELF auxiliary type definitions](https://sources.debian.org/src/glibc/2.36-8/elf/elf.h/).

Published versioned source and an upstream patch discussion are not evidence of the actual host's loader version. Retained P09/P10 evidence establishes the selected Python identity and raw RPATH observation, but not the complete current Python/extension closure, actual execution-origin eligibility, sibling `lib` contents, or a complete loader variant inventory. No actual eligible host has passed this proposed rule. If those prerequisites cannot be established later, the required outcome is refusal; this acceptance does not promise H0 success.

The selected-image operational identity remains SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`, 30,894,944 bytes, mode `0o755`. Its exact external recovery dependency remains necessary. H0/H1, the original seven, full routine/R03, integration/R04 and parent closure/R05 remain unmet. Root may adopt these exact design/control bytes, finish the declared P11 handoff and stop; further implementation or host work requires a separately selected phase.
