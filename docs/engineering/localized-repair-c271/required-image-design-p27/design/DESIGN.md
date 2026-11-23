# P27: portable required-image metadata decision

Decision **P27-REQUIRED-IMAGES-001**, version `ontokin.c271.required-image-metadata-decision/1`.
State: **candidate for independent review and separate Director adoption**. This is a design, not an implemented route or an executable inspection plan.
Author: `/root/design`. Inspected branch source: `daf05a17eb44e467114df8258b2c56d8466dc4b8`; governing main: `e43cc6c5777874101a40559e4058ad6826b07e51`.

## Decision and purpose

Specify one new, closed inspection-plan/profile pair for a **fixed five-image cohort from one retained glibc binary package**, with the already selected loader. Each image must be an actual direct dependency of the exact selected author Python and satisfy the complete existing plan proof. The new rule recognizes the x86-64 PLT tag trio on those five images. Separate predicates recognize `DT_FLAGS=24` on the exact libm and `DT_FLAGS_1=9` on the exact librt. Every older route, the existing libc rule, unknown-feature refusals, and later qualification gate retain their meaning. [S01–S06]

This is a portable package-input policy. Its catalog contains bytes, sizes, modes, package members and source associations; it contains no previous-host inode, boot identifier or scratch path. Operational paths must be freshly bound under the inherited rules. A host cannot extend the catalog, substitute another package or bless a newly observed feature. The next technical phase may implement only this design after adoption; it must stop before host preparation or H0. An additional compatibility problem is a concrete blocker, not an invitation to add another exception during implementation.

## Durable need and alternatives

P05 requires the original three real CPU readback cases and four coordinator controls, followed by the complete routine, with the fixed Node build and exact 24 external reader files. Its purpose is verification of the unchanged scientific checks. A particular disposable host is not the requirement. P07 requires a complete, independently reviewed native-input map before two bounded preparation commands may run. Those obligations cannot be satisfied by dropping a required library, skipping a method, replaying an old HOST document, or counting static metadata as execution. [S02, S03]

P26 supplies the necessary counterexample: exact libdl bytes, SHA-256 `295fa521a03cd2faa99974f378c9e23dd622021ec7d32bcad4f8ea61aec8a872`, are selected by the narrow first-Node-dependency source argument, but the ordinary parser excludes its PLT tags. The retained Python root observation names all five catalog libraries directly in `DT_NEEDED`. That establishes the finite dependency-name cohort; it does **not** complete Python's origin/search-directory/nonselection proof or prove every selected file. The future rule must reobserve Python metadata and require the existing independent resolution proof. [S01, S07]

| Route | Existing support and disposition |
| --- | --- |
| Recreate the exact saved Node, 24 reader files and seven pinned Python-package inputs in a fresh isolated environment | Approved input-reconstruction route under P05/P07/P20/P22. Previous installation receipts prove past preparation. Reconstruction alone leaves native metadata and complete H0 proof unresolved. No reconstruction occurs in P27. |
| Use an already conforming Linux/glibc host with an older plan/profile | Remains available if all that profile's exact selected Python, Node, libc/loader, dependency, script, path, source and verification requirements are independently established. No such conforming alternative host is identified by the retained evidence. Host search is not the next phase. |
| Use the retained binary package as inert portable metadata evidence | Available now. All five extracted members match the P26 observed hashes, sizes and modes. It supports this design and future data-only controls. It does not authorize installing system libraries, relocating the loader, or executing them. |
| Select another Node/Python build, change reader bytes, invoke a loader directly, inject a library path, or introduce a container/native-loader provider | No adopted route here permits that substitution. Each would require a separate versioned contract and verification decision. P27 selects none. |
| Keep every refusal without a new profile | Honest but leaves the unchanged P26 inputs incompatible. Recovery would require a concrete conforming input set or a separately reviewed contract change. The exact package cohort provides the smaller supported decision. |

The choice avoids a generic loader or platform framework. It also avoids granting a feature to arbitrary files based on a `lib*.so` name. One source-associated catalog addresses the complete observed cohort and its two distinct flag forms together. [S01–S08]

## Exact catalog and provenance

Catalog identifier: `debian-glibc-2.41-12+deb13u4-amd64-required-images-v1`.
Package: `libc6_2.41-12+deb13u4_amd64.deb`, 2,846,580 bytes, SHA-256 `967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9`.
Each member below is under `data.tar.xz`, at `./usr/lib/x86_64-linux-gnu/NAME`. All five operational modes are `0o644`. [S08]

| Catalog key / required SONAME | Bytes | SHA-256 | Additional recognition |
| --- | ---: | --- | --- |
| `libdl.so.2` | 14,408 | `295fa521a03cd2faa99974f378c9e23dd622021ec7d32bcad4f8ea61aec8a872` | PLT trio |
| `libm.so.6` | 977,112 | `6d567d53e895273ca14a1f9dc164fc6c8d39aed2f60aa46a733c2784228915f3` | PLT trio; exact flags 24 |
| `libpthread.so.0` | 14,408 | `85e21f7dba0394411d00959176fd18b470e575b0b05f1f4f41e5636802ce0500` | PLT trio |
| `librt.so.1` | 14,552 | `7b7b84d1aedda0e0b2bdfc68844362782132180b8f02be1300e21e77572e514b` | PLT trio; exact flags-1 value 9 |
| `libutil.so.1` | 14,408 | `e3981d10efd152a53f083e38f5f9ddde7a049c85d0ab388a5eec91b52fc98a11` | PLT trio |

The associated loader remains 225,672 bytes, mode `0o755`, SHA-256 `c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307`. The existing libc remains 1,995,216 bytes, mode `0o755`, SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`. Both independently extracted package members match their existing pins. Their roles and private rules are not transferred to the five new subjects. [S04, S05, S08]

Exact source association uses the retained `.dsc`, upstream archive and Debian patch archive. P27 recovered the upstream archive from its retained official HTTPS URL and verified its original 20,323,540-byte identity and SHA-256 `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998`. The 80 active patches were indexed against the selected source files. Selected upstream text and affected patch sections are retained with member hashes. This is the same package/source association accepted for P16/P17; it is not a signature verification, reproduced build, compiler-output proof or present-host observation. [S08–S12]

## Source interpretation: three separate rules

**PLT tags.** The Procedure Linkage Table supports calls into linked functions. The exact x86-64 source defines `DT_X86_64_PLT=0x70000000`, `DT_X86_64_PLTSZ=0x70000001`, and `DT_X86_64_PLTENT=0x70000003`. Its build recipe requests these tags for shared objects when the linker supports `-z mark-plt`, and explicitly suppresses them for the loader. This explains why the phenomenon is not libc-specific. The retained members, rather than the recipe alone, establish which exact inputs carry them. The numeric values collide with other architectures, so the new primitive is restricted to ELF64 little-endian x86-64 `ET_DYN`. It preserves the inherited OSABI acceptance of 0 or 3: the exact libm has OSABI 3. [S08, S09]

The loader's complete rewrite consumer reads relocation/GOT results, can change memory protection and rewrite instructions. These tags are not universally inert. That consumer does not introduce a new dependency name or search path. The metadata reader therefore treats the three values as opaque unsigned 64-bit data; it neither dereferences them nor uses them as allocation/read/loop bounds. The exact launcher environment continues to exclude `GLIBC_TUNABLES`; the bound source initializes rewriting off and requires an explicitly initialized nonzero tunable, without an environment alias, to enable it. This source argument is not a measurement of a running process or executable-code safety. [S09]

**libm flags 24.** `0x18` is `DF_BIND_NOW | DF_STATIC_TLS`. Thread-local storage (TLS) supplies separate storage for each thread. The exact source stores these flags and has relocation helpers that may require or attempt static TLS allocation. Allocation can fail. Recognition adds no TLS-layout, relocation, memory-capacity or runtime-success claim. It adds the exact value 24 on the exact libm subject; a lone 16 and additional bits remain refused. P17's corresponding libc rule stays unchanged. [S05, S10]

**librt flags-1 value 9.** `0x9` is `DF_1_NOW | DF_1_NODELETE`. The exact `get-dynamic-info.h` sets pending NODELETE state; `dl-open.c` activates it in the successful opening path; `dl-close.c` retains active objects and their relevant dependencies. `rt/Makefile` explicitly requests `-z nodelete` for librt, and no active Debian patch changes that recipe. The affected loader patches change debugger notification, a comment and other unrelated behavior, not these flag transitions or close checks. [S11, S12]

NODELETE also participates in relocation-dependency accounting in the inspected `dl-lookup.c`. It is a lifetime rule. The inspected flag handling adds no dependency name or search directory, but retained mappings can affect later loaded-object reuse. P27 consequently does not declare NODELETE globally harmless, emulate unload behavior or prove a complete runtime closure. The existing source-completeness review must still address relevant loading/reuse for the actual commands. The metadata reader adds only exact value 9 on the exact librt subject. It does not widen the flags-1 mask. [S03, S11]

## Version and closed input

New pair:

| Field | Literal value |
| --- | --- |
| `schema` | `ontokin.current-host-readback-inspection-plan/0.1.5` |
| `host_static.resolution.profile` | `linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-rtld-paths-required-images-v1` |

Every `/0.1.4` field remains required, including `origin_rpath`, `libc_plt` and `rtld_paths`. Add exactly one resolution member, `required_images`. Its exact keys are `schema`, `catalog`, `loader`, `subjects`. The new selector checks its exact schema/profile, complete closed resolution keys, required-image shape and catalog before delegating unchanged inherited subobject shapes. Descriptor path validation here is syntax-only; actual canonical/alias proof is later:

- `schema` is exactly `ontokin.current-host-readback-required-images/0.1.0`.
- `catalog` is exactly the catalog identifier above.
- `loader` is the unchanged closed `{path, sha256, size_bytes, mode}` descriptor, equal to `libc_plt.loader` and the selected loader's other bindings.
- `subjects` is a closed object with exactly the five catalog keys above. Each value is one closed descriptor. All five paths are distinct and canonical under inherited path rules; a descriptor's binding must equal its catalog row.

No flags, masks, tag lists, tunable settings, role overrides, package paths, approved/completeness words, arbitrary source association or optional subjects enter this object. The catalog is fixed code derived from this decision, not a runtime package parser. The plan's external expected digest remains separate authority; the rationale remains the existing independently reviewed source/closure document. `DECISION.json` is the normative machine-readable spelling and selector inventory.

Versions `/0.1.0` through `/0.1.4`, public `read_elf_metadata` signature/default, existing diagnostics/order and callback behavior remain exact. Old schemas cannot carry the new member. The new schema cannot use an old profile or omit inherited fields. Never relabel a new plan as an old schema internally. P06 HOST/inspection/result/configuration/probe schemas and the fixed `shared_libraries.stdout_predicate` remain unchanged. [S03–S06]

## Binding and dispatch order

The new route requires no dependency discovery algorithm. Use the already implemented order: authenticate plan and source; validate author/runtime and host bindings; read the exact selected Python through its existing origin route; establish the unchanged libc/loader policy. Only then derive the new immutable policy. The actual Python row's declared metadata must already equal freshly read metadata. [S06]

Refusal precedence is fixed before any new file-binding read: first require pairwise distinct subjects and exclusion of libc, loader, Python, Node, Git, inspector entry/script/interpreter canonical roots (`RI-SUBJECTS`); next exclude extensions and external inspector-command executables (`RI-ROLE`); next prove common-loader equality (`RI-LOADER`). Derive these paths from validated descriptors and already checked alias maps. Then, for each sorted key, check actual-needed/selected-edge/role relations (`RI-ROLE`), descriptor/complete-alias equality (`RI-DESCRIPTORS`), and catalog pin (`RI-PIN`). Contradictory later fields cannot conceal an earlier distinctness or forbidden-role failure. Only after every relation succeeds, `_bound` checks the five sorted subjects and then the loader. This is a pure relation proof followed by real binding reads, not mocked proof acceptance.

For each catalog key in sorted order, the new proof requires:

1. The key occurs in the freshly read Python `needed` list. Its unique declared Python image row maps that same key to one named alias. A declared-only name is insufficient.
2. That named path occurs in `roles.inspector_runtime` or `roles.shared_libraries`, and in both host and author-runtime alias maps. Both complete alias records agree and resolve to the corresponding subject's canonical path.
3. Exactly one image row exists for that subject path. Its descriptor equals the subject descriptor. Host and author-runtime resolved-file bindings equal the descriptor's binding. A filename match, unused same-hash row or swapped key cannot substitute.
4. Subject paths are pairwise distinct. No subject is the libc subject, loader, selected Python/Node/Git, inspector entry/script/interpreter, an external inspector command executable, or an author extension. Compare both named and canonically resolved forbidden paths after their row shapes have been validated. The allowed dependency role cannot override a forbidden role.
5. The common loader descriptor equals `libc_plt.loader`, the already proven actual Python interpreter's host/runtime aliases and files, and its unique image row, and matches the unchanged loader pin. Require subject/loader inequality. No arbitrary loader with the same name qualifies.
6. Compare every subject binding to the fixed catalog row. Use existing `_bound(..., category="INSPECTOR", private=False, check=check)` on all five canonical files and the loader before granting private dispatch. Preserve file/alias, byte/size/mode, identity, deadline and close guards. No policy survives a failure.

After the complete five-subject proof succeeds, derive a private immutable policy retaining the actual `/0.1.5` schema. `_read_plan_elf_metadata` may use the new primitive only when the exact canonical path matches one of these bound subjects. The lookup determines the fixed catalog key; a caller does not choose capabilities. Each actual image read retains the enclosing `_bound` check immediately before parsing, compares returned metadata with the declared image row, and requires the actual SONAME to equal that catalog key. Existing complete image/needed-edge/interpreter/architecture/search/alias/role and origin-nonselection checks still run. A partial proof or raw metadata result cannot produce `STATIC_READY`.

The existing libc subject continues through its unchanged P17 primitive. Other images continue through their old readers. A future implementation must explicitly add the new pair to the inherited origin/libc/RTLD routing sites, including the RTLD operational selector, without weakening the exact older selectors. The final five-image proof and full inherited closure/guard proof precede `_load_helpers`, all five Git reads and any command. Both early and final resolution calls repeat it; every complete `_recheck` derives it again from fresh actual metadata and files. [S06]

The five subject paths and loader already belong to both file maps, so the unchanged complete snapshots and final launch guards cover them. The new policy is not cached across checks. Final launch continues the inherited identity/alias/guard checks inside the existing command clock; it does not introduce six full file rereads under that clock. Post-command full recheck rehashes and rederives the proof. Preserve the existing outer `CHI-DRIFT` wrapper and underlying cause. Observed drift after a start retains the actual receipt/count; neither a lost callback nor a failed finalization becomes a zero-start success. Validation and later kernel loading are not atomic; the existing race/kernel/native-execution limits remain. [S03, S06]

## Exact private metadata semantics

Only the new private route changes. Ordering is normative:

1. Run all inherited file/open/header/program-table/segment/dynamic-table/mapping/terminator checks. Existing OSABI 0-or-3 acceptance remains.
2. Require machine 62 and type 3. Add only the three numeric PLT tags to the inherited ordinary set. Unknown tags, including `0x70000002`, refuse before multiplicity/flag checks.
3. Require exactly one occurrence of each PLT tag, including rejection of equal duplicates and any missing/all-absent trio. This is conservative catalog policy, not an ABI assertion. Values remain opaque, including zero, maximum uint64 or inconsistent synthetic values.
4. Require at most one `DT_FLAGS` and at most one `DT_FLAGS_1`. Apply the separate fixed table below.
5. Run every remaining string-table/name/search-path/SONAME/identity/final-callback check and return the unchanged nine metadata keys. The operational wrapper then checks catalog SONAME equality.

| Subject route | `DT_FLAGS`: absent or one value in | `DT_FLAGS_1`: absent or one value in |
| --- | --- | --- |
| libdl, libpthread, libutil | `{0, 8}` | `{0, 1, 134217728, 134217729}` |
| libm | `{0, 8, 24}` | `{0, 1, 134217728, 134217729}` |
| librt | `{0, 8}` | `{0, 1, 9, 134217728, 134217729}` |

The baseline entries preserve the ordinary reader's accepted flag states at this private primitive. Actual operational pins admit only the retained bytes. A synthetic flags variant cannot meet the pinned digest. In particular, `DT_FLAGS=16`, `DT_FLAGS_1=8`, `DT_FLAGS_1=134217737`, cross-subject use of 24/9, duplicated flags and every other extra bit refuse. Existing libc and all old-route masks remain unchanged.

New shape/profile failures use `CHI-PLAN`; new binding/pin/role/SONAME failures use `CHI-INSPECTOR`; new architecture/trio failures use `CHI-UNSUPPORTED`. Their literal reasons and two-key details are frozen in `DECISION.json`. Unknown-tag and flag failures retain exactly `CHI-UNSUPPORTED / Unreviewed ELF dynamic loader feature` and `CHI-UNSUPPORTED / Unsupported dynamic flags`, respectively, with empty details. Inherited parse/path/read errors retain their current categories, reasons and causes. No refusal becomes `supervisor.Stop`.

The raw extension performs only fixed-count scans of an already bounded table. Preserve 512 MiB maximum ELF file, 16 MiB individual bounded read, 256 program headers, 65,536-byte dynamic table, 4 MiB string table, 4,096-byte string bounds, 256 needed names and the existing 512-image plan ceiling. Add no caller-supplied bound. New callbacks occur at policy entry, each of five relation/binding iterations, before tag policy, during its entry scan, before/during flag scan and before final identity acceptance. Old routes receive no new callbacks. The new primitive tracks callback-origin faults, including `OSError`, `ValueError` and `UnicodeError`, so inherited parse-exception handling cannot relabel them. A primitive callback fault propagates as the same object after successful existing cleanup; inherited noncallback parse/I/O/close behavior is preserved. No descriptor may leak or be closed twice.

## Controls and future implementation boundary

`CONTROL-PLAN.json` freezes stable positive, boundary, refusal, fault and compatibility IDs with literal semantics. It is declarative and nonexecutable. Before future control execution, an independent fixture author must bind exact inert fixtures, unchanged companions, commands, adapters and expected results to those IDs. Expectations are fixed before product execution. Materializing fixtures cannot add a rule or repair an oracle to fit the implementation.

Controls distinguish actual reads of the package's inert bytes, synthetic metadata primitives, pure selectors/relations, and labelled mocked caller/recheck boundaries. Every new control expects zero Node, ldd, direct-loader and CPU-checker starts. A binding mock or a private primitive positive proves neither actual file admission nor a complete plan. The exact libdl counterexample must remain a refusal on the public parser and old operational non-subject dispatch routes and become metadata-readable only through the new authorized private capability in its appropriate control route. The old private libc primitives retain their intentionally weaker synthetic-metadata behavior; they never proved operational admission and are not required to refuse these bytes. libm and librt have separate exact positives and cross-subject refusal controls.

Future production edits are limited to `prototypes/static_tray_v01/current_host_inspection_v01.py`; the only new test adapter is `tests/test_current_host_required_images_v01.py`, with independently frozen inert control data/evidence under the P27/P28 documentary area. Existing tests, fixtures and oracles remain unchanged. `FUTURE-SURFACE.json` identifies each integration site and required inherited suites. All prior inspection, mapping, origin, libc and RTLD controls retain their IDs and expectations. N34 and historical N57 remain external independent source-completeness obligations, never runtime passes or skips.

Preserve the original seven method and helper bodies, scientific reader bodies and thresholds; exact Node/Python/libc/loader/24-file/seven-package pins; fixed two preparation commands and five-variable environment; five-second preparation limit; 60-second static and 30-second publication limits; CPU 30,000/28,000/2,000 ms outer/work/cleanup limits; source 100,000 operations/30,000 ms; all document/log/stage bounds and lifecycle accounting. No success of this design or its future focused controls closes H0, H1, original-seven, complete-routine, R03–R05 or parent completion. [S02, S03, S06]

## Stop and remaining gates

P27 stops technical expansion at independent acceptance/adoption of this exact design or a concrete design blocker. Only documentary publication, required record checks and verified saved handoff follow in this thread. No product/parser/test, Node, ldd, direct loader, host profile, package installation or H0/H1 execution occurred in this design work.

The next eligible fresh phase is **implementation and focused inert controls of this exact surface**, if the Director adopts it. Stop at independently accepted implementation or the first new design blocker, before host preparation. Later H0 still requires a fresh complete native selection, Python-origin/search-directory/variant evidence, runtime-role/alias agreement, exact source/input bindings and independently approved operational plan. P26's source-deduced blocker and all older failures remain historical facts; this decision does not relabel them as passes.

Exact sources, archive/member paths, hashes, read scopes and limitations are in `SOURCE-EVIDENCE.json` and `READ-SET.json`. The parent owns adoption, canonical records, Git publication and saved delivery.
