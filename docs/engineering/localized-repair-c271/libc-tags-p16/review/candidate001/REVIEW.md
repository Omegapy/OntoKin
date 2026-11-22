# Independent review of P16 candidate001

Reviewer: `/root/design_review`. Scope: one formal review of the frozen tag decision and inert controls. This is a source and data review, not implementation acceptance or host qualification.

## Verdict

**Accept the bounded tag-only design and its frozen control obligations for separate Director adoption. No mandatory revision finding.** The exact three-tag exception is justified for dependency-metadata reading on the selected x86-64 libc. The candidate keeps the public and earlier plan routes unchanged, binds its new operational route to an actual selected dependency and exact loader, and preserves all existing flags and subsequent checks. The opaque-value claim is deliberately narrower than loader or executable safety.

Two nonblocking observations are recorded below: a shared baseline fixture descriptor has an imprecise field name outside the binding controls; and a separate flags decision should precede implementation. Neither changes the frozen bytes or expectations. This review does not authorize implementation, a flags exception, an operational plan, H0/H1, Node/ldd, or parent closure.

## Exact reviewed object and independent work

The candidate directory is `/workspace/scratch/fd30b8a094f0/p16-session/tag-design/candidate001`. Its `CANDIDATE-MANIFEST.json` is 36,725 bytes, SHA-256 `61b18ceb15d3ee05d3022c60941ccbbce9c3e08bac148c7750da9f6588091156`. The manifest binds 169 payload files totaling 1,074,121 bytes. `EXPECTATIONS.json` is SHA-256 `33a17cc66604f8b57be88dae7dd05a4bec066c0eaa191fc08400cfc79e18137e`.

The independent inspector in `inspect_static.py` completed 1,493 static assertions with no failed assertion. It compared the entire file/directory inventory, hashes, lengths and modes; checked the 120 fixture bindings and all 73 context/expectation links; independently reconstructed every byte of all 47 ELF images from their declared layouts; recorded every complete context and literal expectation; and calculated the actual mutations relative to the positive contexts. These are static evidence assertions, not product-test passes. The inspector did not import production or execute any author script. Results are in `STATIC-INSPECTION.json`, `CASE-INSPECTION.json` and `STATIC-READSET.json`.

All 18 candidate upstream source copies match their exact members in the bound `glibc_2.41.orig.tar.xz` archive. A separate independent comparison checked all 80 active Debian patch names, sizes, hashes and selected-file headers for the 18 selected source paths. Only the already reviewed CPU-feature and Makefile sections appear. `SOURCE-PATCH-COMPARISON.json` records that comparison. It did not apply patches or build code.

The 26 paths in `PROTECTED-SOURCES.json` and five additional paths in `PROTECTED-PATH-RESOLUTION.json` retain the declared hashes and lengths. The recorded nonexistent `prototypes/static_tray_v01/synthetic.py` remains absent. The explicit correction identifies the actual helper in the existing test source; no missing file was invented. Root's complete protected-tree comparison remains its own publication responsibility.

## Source-backed compatibility decision

The prior independent source review is frozen in `../attempt001/SOURCE-REVIEW.md` and its bound source/inspection artifacts. It independently matched the captured libc to the official retained Debian package member and inspected the complete relevant loader consumer. Candidate source copies were compared to the same upstream archive, rather than accepted on the author's description alone.

| Tag | Bound x86-64 definition | What the inspected consumer does |
| --- | --- | --- |
| `0x70000000` | `DT_X86_64_PLT` | Uses the address with the object's load bias for PLT rewriting. |
| `0x70000001` | `DT_X86_64_PLTSZ` | Uses the region's byte size for page-protection and rewrite operations. |
| `0x70000003` | `DT_X86_64_PLTENT` | Uses the entry size when locating PLT branches. |

The exact primary definitions and full consumer are `sources/upstream/elf/elf.h` and `sources/upstream/sysdeps/x86_64/dl-machine.h`, principally lines 531–765 of the latter. `elf/dynamic-link.h` connects the hook to relocation. The active consumer reads relocated GOT/relocation data and can change page protection and instructions. Describing these tags as universally inert would be false. The candidate does not do so. The inspected operation does not add a dependency name or a library-search rule; that limited conclusion supports this dependency-metadata exception.

The numeric collisions on AArch64 make the explicit x86-64 guard necessary. The once-only complete trio is a conservative policy for this selected image, not a general ABI requirement. The source does not establish that all ELF objects need all three tags or prohibit equal duplicates as an ABI rule; the candidate states this distinction correctly.

The extra environment argument is supported as a source-level condition. The bound initializer disables rewriting; the setter is reached through the initialized nonzero tunable. The selected `dl-tunables.list` has no environment alias for this tunable. Independently read `elf/dl-tunables.c` and `scripts/gen-tunables.awk` sections connect the absent alias and `GLIBC_TUNABLES` handling to the initialization path. The active patches do not change these selected sections. This strengthens the argument under the retained five-variable launch contract. It does not observe a live process's rewrite state or establish general runtime safety.

The retained package/source association has the stated limits: no reproduced build, compiler invocation, build-log proof or local OpenPGP verification was supplied. The independent official-source web checks and one failed direct psABI retrieval are preserved in `../attempt001`; this review relies on the exact retained source for semantics and does not claim a successful direct read of that psABI commit.

## Finite bounds and metadata scope

No extra numeric bound is needed for the claim actually made. The rule reads the unsigned values already decoded from bounded 16-byte dynamic entries, counts three fixed tags, and leaves those values opaque. It adds no address dereference, tag-sized allocation, value-driven loop or read range. The existing 65,536-byte dynamic-table ceiling and all earlier file, program-table, read, string-table and deadline bounds continue to constrain the work.

P02, P03 and P04 deliberately contain zero, maximum unsigned and inconsistent values. P01's synthetic PLT address is outside its 2,048-byte file. Their expected metadata success is consistent with an opaque reader. It would be inconsistent with a claim to validate executable PLT structure. The exact operational pins prevent those synthetic images from becoming an operational positive. A future request to validate mapping, alignment, divisibility, relocations, branch targets, or executable safety would require a separately reviewed policy; this candidate does not supply one.

## Operational binding and order

`DECISION.md` sections 3–5 and `FUTURE-SURFACE.json` provide a concrete implementation contract:

1. The exact new `/0.1.2` schema/profile pair adds one closed `libc_plt` object. The old `/0.1.0` and `/0.1.1` branches retain their contracts. Every origin object, nonselection proof, external digest, source inventory, launcher and author-runtime requirement still applies.
2. The actual selected Python metadata must contain `libc.so.6`. Its unique image row must resolve that needed name to a named inspector-runtime or shared-library role. Both complete alias records must connect that name to the subject canonical path.
3. The host/runtime file bindings, unique subject image row and subject descriptor must agree. The actual Python interpreter and bound runtime interpreter must connect through both complete aliases/files and the unique loader row to the exact loader descriptor. Forbidden roles and distinct subject/loader paths are checked.
4. Corresponding descriptors are compared before fixed pins. Both actual canonical files then pass the existing `_bound` check before the private libc primitive is called. A matching hash on an unused row is insufficient. Synthetic observations confer no actual-file authority.
5. Full existing image, needed-edge, interpreter, search-directory, origin and guard checks still run before helpers, source Git reads or commands. Every complete recheck reconstructs the policy and proof. Existing snapshots cover both canonical files because those files must already be identical entries in host/runtime maps. Existing path guards and launch checks remain required.

I checked these requirements against the retained inspection source, especially `_check_author_runtime`, `_check_author_host_bindings`, `_check_resolution`, `_validate`, `_recheck`, `_required_paths`, `_check_plan_guards`, `_input_snapshot` and `_launch_check`. The new version must join every required origin early/recheck/kernel branch while preserving the old branches. The future surface explicitly identifies those obligations and does not require inventing a new approval document or runtime switch.

The loader relation proven by the new primitive is the selected author-Python relation. This is not proof that every executable root uses the same loader. The full finite plan and its independent source/closure rationale still govern Node, shell, Git, extensions, ldd candidates and the libc's own needed edges. The candidate's requirement to retain that complete review matters; this verdict does not collapse those later checks into the private binding positive.

Within the new raw reader, the order is implementable and explicit: inherited structural/terminator checks; x86-64 ET_DYN guard; ordinary-tag predicate with exactly three additions; complete once-only trio; unchanged flags; inherited string, path and identity checks. N14 and N15 fix two combined-fault precedences. The old flag masks remain `0x8` and `0x1 | 0x08000000`; their original multiplicity and empty-detail errors remain intact. The new helper must not use the Python origin path callback on libc.

## Complete control review

Every control's actual context, literal expectation, image bytes where present, and calculated mutation is retained in `CASE-INSPECTION.json`.

| Controls | Count | Review result and practical limit |
| --- | ---: | --- |
| L01–L05 | 5 | Earlier public/literal/origin routes reject the trio; tagless x86-64/AArch64 preserve ordinary metadata. L03's origin subject is explicitly a different Python path. |
| P01–P07 | 7 | Opaque tuple variants, inherited allowed or absent flags, and reordered trio produce the unchanged metadata dictionary. They are private primitive obligations only. |
| N01–N27 | 27 | Architecture/type, exact unknown tags, all missing/duplicate trio members, combined-fault order, old flags, strings, names, paths and structural faults have matching isolated byte changes and literal refusals. N16 explicitly preserves refusal of `DT_FLAGS=0x18`. |
| S01–S08 | 8 | Exact new pair/closed shape and mismatches are isolated. These call the new selector only; old-schema cases do not redefine the public old `_plan_shape` diagnostic. |
| B01–B16 | 16 | Actual-needed/selected-edge/role relations, complete alias equality, file/image equality, interpreter relation, coherent wrong pins/mode and the synthetic-pin negative are distinct. B01 expressly proves no actual file binding. B16 calls the unchanged external digest primitive. |
| D01–D02 | 2 | Each changes only one host file digest in the mocked after observation. The real new binding primitive must fail before raw libc parsing, inside the existing drift wrapper with its exact cause. |
| F01–F08 | 8 | Named callback, short-read, final identity and I/O faults identify actual boundaries. The same opened descriptor must close once; callback object identity and original details/cause are preserved as specified. |

The binding controls intentionally use logical descriptors that differ from the materialized synthetic bytes. B15 coherently substitutes the synthetic descriptor in every subject position and must fail the fixed pin. Nothing in the corpus authorizes changing production pins, treating a mocked `_bound` result as operational evidence, or manufacturing an expected failure by case identifier.

The frozen expectations are authored obligations, not outputs from a product run. A future adapter still needs independent review of actual primitive calls, injection reachability, exact file-descriptor cleanup and all mocked observations. The candidate explicitly requires this. The existing 135 inspection, 40 mapping and 96 P13-applicable origin controls remain future gates, with historical N57 accounted for externally rather than reported as a runtime pass or skip.

## Nonblocking observations

### N01 — Shared baseline descriptor is not the per-case image descriptor

`build_inert_controls.py` assigns the same `actual_fixture_bytes` descriptor to all contexts. In 35 mutated ELF contexts this differs from that context's `image` descriptor; P02 is a simple example. The shared descriptor names the baseline synthetic bytes used for the mocked binding distinction and B15. The separate `image` descriptors, fixture manifest, construction record and actual bytes agree for all 47 images.

This is a naming/provenance note, not a broken control or ambiguous acceptance policy. The route contract selects the actual `image` as the reader input. A future adapter must use its frozen descriptor and must not replace it with the shared baseline descriptor. The full affected-case list and both descriptors are in `CASE-INSPECTION.json`. No fixture or expectation change is needed for adoption; retaining this clarification in the Director handoff will prevent a misleading per-case reading of the field name.

### N02 — Review the separate flags decision before implementation

The exact captured libc has `DT_FLAGS=0x18`. The unchanged source mask accepts only `0x8`, so `0x18 & ~0x8` is nonzero. **Inference:** after successful new tag recognition, this same exact libc would be refused by the later flags predicate. **Observation:** P15 stopped at the earlier first unsupported tag; it did not observe the flags failure. The candidate preserves this distinction and freezes the refusal in N16.

I recommend a fresh, separately bounded source-backed `DT_FLAGS`/`DF_STATIC_TLS` compatibility decision before implementation. That allows the next implementation scope and operational usefulness to be assessed from complete evidence, while avoiding implementation of a profile that is presently guaranteed not to admit its own exact selected libc. A flags decision might retain refusal; no favorable result is assumed. It should not silently widen either earlier plan route or this phase's masks.

`DECISION.md` section 6 identifies fresh implementation as the next eligible work. This is a scheduling statement, not a technical dependency of the tag policy. The Director can supersede it in ADOPTION/HANDOFF with the separate flags-review ordering while preserving the frozen candidate. This review adopts no flag semantics or exception.

## State, authority and completion boundary

The early saved recovery was confirmed before this substantive review; its receipt and exact identity are retained in the preceding read-set. Root reports phase-start checkpoint `f3f84d4cb58bcce318f2bc92135e83000e9db466` changed canonical documents only. All source identities verified here remain the initial C271 source bytes at `0d5a3053ced2805f4cc04b77f361bb07dbdc7999`. Current main at the observed `70ca7e68ff95df876f801137369d176fe5b2bab3` correctly retains C270 because C271 is unmerged; the branch/task/PR govern unfinished C271 scope.

This review claims no implementation, product parser/test pass, operational-plan acceptance, current-host input read, H0/H1, runtime launch, original-seven/full-routine result, R03–R05 acceptance, merge or parent closure. The reviewer changed only its owned review directory. Root owns separate adoption, canonical updates, durable publication and any later phase assignment. Candidate001 and the preceding frozen source-review attempt remain unchanged.
