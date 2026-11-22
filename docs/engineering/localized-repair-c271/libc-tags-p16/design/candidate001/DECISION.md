# P16: bounded recognition of the selected libc's PLT tags

Decision identifier: `ontokin.c271.libc-plt-metadata-decision/1` (`P16-ELF-001`).

State: proposed design and inert controls, awaiting independent review and a separate Director adoption. No production implementation, operational plan or host acceptance is supplied.

Author: `/root/tag_design`. Retained source: `0d5a3053ced2805f4cc04b77f361bb07dbdc7999`, tree `429b01242d98329e32dbe31be45e9f7c2f52aed4`. Director-supplied main: `70ca7e68ff95df876f801137369d176fe5b2bab3`. Substantive source work followed the Director's confirmed early save, SHA-256 `8cf4fa4e248260411191ec7583eeca4334c0ea6e9cebd38eccc17f3495e342a9`.

## 1. Decision and claim

Propose an explicit new inspection-plan/profile pair that recognizes exactly three processor-specific tags on the **already selected, exact P15 x86-64 libc dependency**, with the exact associated loader. The new reader treats their values as opaque for its dependency-metadata purpose. It does not use the values as addresses, byte counts, allocation sizes, loop bounds or read ranges. It returns the existing metadata shape without adding PLT fields. All ordinary structural, string, dependency, path, flag, identity and deadline checks remain in force.

The complete once-only trio is a conservative policy chosen here for this exact selected image. It is **not an ABI rule** that every x86-64 ELF must contain these three entries or contain them exactly once. The exact operational image already has this shape. Other shapes stay outside this small profile. [S01–S05]

| Numeric tag | Name in the bound x86-64 source | Meaning in its loader consumer | P15 retained value |
| --- | --- | --- | --- |
| `0x70000000` | `DT_X86_64_PLT` | Link-time virtual address used with the object's load bias for PLT rewriting | `0x28000` |
| `0x70000001` | `DT_X86_64_PLTSZ` | Byte size used when changing the PLT region's protection | `0x3d0` |
| `0x70000003` | `DT_X86_64_PLTENT` | Entry size used when locating and rewriting individual PLT branches | `0x10` |

PLT means **Procedure Linkage Table**, code used to call dynamically linked functions. These are active loader inputs when the rewrite feature is enabled. The inspected consumer can change memory protection and rewrite branches to values already obtained from the object's Global Offset Table (GOT). Its dependency on relocation records and runtime feature state makes it incorrect to describe these tags as universally inert. They do not introduce a dependency name, search path or alternative image-selection rule in the inspected implementation. That last statement is the finite dependency-metadata conclusion used here; it is not executable-code validation. [S05]

The bound source initializes rewriting to disabled. Its setter requires an explicitly initialized, nonzero `glibc.cpu.plt_rewrite` tunable, and the tunable has no environment alias. P07's exact five-variable launcher/child environment excludes `GLIBC_TUNABLES`; the author-runtime guard checks the actual environment. Retain those requirements. The source argument does not measure a past or current process's rewrite state, validate PLT contents, authenticate a kernel, or establish native runtime safety. No new runtime rewrite-state field or approval Boolean is introduced. [S06, S07, S10]

## 2. Exact evidence and preserved blocker

The retained inert libc capture is 1,995,216 bytes, SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`. A fresh data-only comparison in this phase matches it byte for byte to `./usr/lib/x86_64-linux-gnu/libc.so.6` in the retained official Debian `libc6_2.41-12+deb13u4_amd64.deb`. The loader member matches 225,672 bytes, SHA-256 `c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307`. Package control metadata identifies source `glibc`, version `2.41-12+deb13u4`, architecture `amd64`. Exact upstream/patch archives and all relevant patch sections support the interpretation. [S02–S09]

This is a package/source association supported by retained official HTTPS records and exact checksums. No OpenPGP signature verification, binary build log, compiler-output proof or reproduced build is claimed. No current-host file was inspected. The P15 libc/loader pathnames and observations remain historical inputs. [S02]

P15's first refusal remains exactly `CHI-UNSUPPORTED / Unreviewed ELF dynamic loader feature`; the first excluded tag was `0x70000000`. Its later flag predicate was not reached. The recorded raw `DT_FLAGS=0x18` remains unchanged. This proposal preserves the original masks and does not make that file a positive product/host case. Its flag compatibility and every later H0 prerequisite remain outside this decision. The separately frozen synthetic `0x18` control requires the unchanged flag refusal after the new tag gate. It is not a new observation of the real libc. [S01, S10]

## 3. Exact opt-in and unchanged older routes

Keep these existing interfaces exact:

- Public `read_elf_metadata(path, *, check=..., require_interpreter=False)`, its defaults and metadata keys.
- Plan `/0.1.0` with `linux-glibc-declared-closure-v1`.
- Plan `/0.1.1` with `linux-glibc-declared-python-origin-rpath-v1` and every P11/P13 origin rule.
- Existing error categories/reasons/order on those routes, original allowlist and flag masks, P06 consumer schemas, command shapes, environment and all limits.

Proposed new pair:

| Item | Exact value |
| --- | --- |
| Plan schema | `ontokin.current-host-readback-inspection-plan/0.1.2` |
| Resolution profile | `linux-glibc-declared-python-origin-rpath-libc-plt-v1` |
| Additional resolution key | `libc_plt` |
| `libc_plt.schema` | `ontokin.current-host-readback-libc-plt/0.1.0` |

All `/0.1.1` top-level and resolution members remain required, including the unchanged `origin_rpath` object and its complete nonselection proof. The new resolution object adds exactly `libc_plt`. That object has exactly `schema`, `subject`, `loader`; each of the last two is the existing closed `{path, sha256, size_bytes, mode}` descriptor. No tag allowlist, value overrides, review status, approval word, completeness field, tunable setting or arbitrary command is accepted.

`subject` must bind the exact libc hash/size above and operational mode `0o755`. `loader` must bind the exact loader hash/size above and operational mode `0o755`. The absolute canonical paths are authenticated plan inputs. Their names alone confer no role. The selected Python and Node pins remain unchanged. The same descriptor at an unrelated path or unused image row cannot receive the new parser route.

The existing fixed command `stdout_predicate` remains `linux-glibc-declared-closure-v1`; it describes the unchanged ldd-output grammar. No HOST/result/probe output field changes. The existing external plan digest authenticates the chosen bytes; it is not evidence of source-review quality. The current `resolution.rationale` descriptor must bind a later independent source/closure review that addresses this decision and the exact inputs. P13's external completeness boundary stays external. [S10, S11]

## 4. Role binding before raw admission

The new route exists only inside the new authenticated plan branch. It must be bound as follows before the private libc parser is used:

1. Preserve the existing external-digest, closed-shape, source-inventory, launcher and author-runtime checks. Derive the unchanged origin policy for the exact selected author Python. Read that Python's actual metadata through its existing origin route; its interpreter must agree with the bound author runtime.
2. The actual Python metadata must contain `DT_NEEDED` name `libc.so.6`. Its unique declared image row must resolve that name to one named path. That named path must be a declared inspector-runtime or shared-library role, and must be present in both the host and author-runtime alias maps. It must resolve to `libc_plt.subject.path`. This proves an actual selected dependency relation before considering the extra tags.
3. The complete host/author-runtime alias records for that named path must agree. Their resolved file bindings, the unique libc image row descriptor and `libc_plt.subject` must agree. An arbitrary same-hash image row, filename match or unselected alias is insufficient.
4. Resolve the already bound author-Python interpreter through the host and author-runtime aliases. Its complete alias/file bindings, unique loader image row and `libc_plt.loader` must agree with the interpreter obtained from the actual Python metadata. The libc subject cannot be the Python, Node, Git, inspector script/interpreter, ELF interpreter, or an author-extension role. The libc and loader canonical paths must differ.
5. Compare both agreed bindings to the fixed libc/loader pins. Then use the existing `_bound` file reader on the actual canonical subject and loader, retaining its descriptor, alias, size, mode, digest, callback and identity checks. Only after these checks may a private immutable policy dispatch this one libc path to the new raw primitive. No caller-supplied policy flag is operational authority.

The extra path binds the selected dependency role; it does not discover or choose a library. After metadata reading, the existing full image/needed-edge/interpreter/architecture/search/alias checks still decide the entire map. In particular, the libc's own needed edges must agree with the complete declared closure. A raw metadata result is never `STATIC_READY` or an accepted plan.

For the combined profile, perform this role/pin proof and complete existing origin/resolution/guard proof before `_load_helpers`, source Git reads or commands, as required by P11's early-validation order. The two existing author-runtime reads continue using the unchanged Python-origin semantics. The libc policy is created within resolution checking after actual Python metadata is available; it is not inferred from the earlier Python parser result alone.

Every complete `_recheck` repeats actual metadata, role, descriptor, pin and closure checks. It must not cache a previously accepted libc policy or raw result. Descriptor equality and the existing file snapshot already cover both files; no new resource or document is introduced. The final launch guard retains all current identity checks within the current command clock. Failures preserve the existing outer `CHI-DRIFT` wrapper and underlying cause. [S10]

## 5. Private metadata rule and exact ordering

The private helper is a data reader, not a host validator. Its synthetic controls can reach it without satisfying the real-image pins, precisely because they test only that primitive. No public generic allowlist, CLI switch, environment override or unrestricted callback policy may expose it as operational admission.

On that private path, run the existing ELF open/header/program-table/dynamic-table/mapping/terminator checks first. Then:

1. Require ELF64 little-endian x86-64 (`e_machine=62`) and `ET_DYN` (`e_type=3`). Existing initial format checks still run first. AArch64 is specifically excluded: `0x70000001` and `0x70000003` have different meanings there. [S03]
2. Apply the existing allowed-tag predicate with only the three exact numeric tags added on this path. Every other unknown tag, including the hole `0x70000002`, still raises the unchanged unknown-feature refusal. A general processor-range allowance is forbidden.
3. Require exactly one occurrence of each of the three tags. Missing/all-absent or duplicate occurrences refuse, including duplicate equal values. This is the conservative selected-profile policy, not an ABI assertion.
4. Apply the unchanged `DT_FLAGS`/`DT_FLAGS_1` predicate and every later existing metadata/string/path/identity check. Do not short-circuit to a successful metadata result after recognizing the trio.

Values are the unsigned 64-bit integers already decoded by the existing dynamic-table reader. The new rule does not interpret their magnitude, alignment, divisibility, mapping, relationship to each other, relocations, GOT entries or actual PLT bytes. It neither allocates from nor dereferences them. Zero, maximum unsigned values and internally inconsistent values therefore produce the same metadata result in a synthetic primitive positive, if all existing checks pass. Such positives make no claim that those synthetic images could safely execute or satisfy the exact operational pin.

The sole new traversal counts three fixed tags within the already bounded dynamic table. Preserve its current 65,536-byte table ceiling and all other finite ceilings; add no new value-based cap. Call the existing deadline callback during the new bounded scan and at its entry/final acceptance boundaries. Close the opened descriptor through the existing `finally` on every return/refusal/callback fault. The exception behavior of inherited I/O/parse faults stays unchanged.

New refusal selectors are fixed in `CONTROL-CONTRACT.md` and `EXPECTATIONS.json`. Existing refusals retain exact reasons and empty details where they previously had empty details. No new metadata output key is permitted.

## 6. Controls, implementation boundary and next gate

`CONTROL-CONTRACT.md`, `CONTROLS.json`, `EXPECTATIONS.json`, `CONSTRUCTION.json` and `FIXTURE-MANIFEST.json` freeze data bytes and independent expectations. The constructor writes synthetic ELF bytes with `struct`; it does not import production, implement the acceptance predicate, inspect host inputs or execute a target. The separate author audit checks byte construction, inventory and fixed expectations only. It cannot establish a passing runtime case.

`FUTURE-SURFACE.json` permits only a later selected edit of the inspection module and one new focused test file, plus its evidence. All existing tests/oracles remain unchanged. A later implementation must run the complete inherited 135 inspection + 40 mapping + 96 P13-applicable origin runtime controls and the new frozen controls, with exact source/input identities and independent review. The historical N57 oracle remains unchanged and separately accounted for as external review only.

No implementation, parser/test execution, current-host H0/H1, Node/ldd, installation, original-seven/full routine, native/model/hosted work, main integration or parent closure occurs here. The P15 refusal remains historical fact; current H0, the independent operational plan, all flag and later input gates, R03–R05 and parent closure remain unmet. After independent review and separate adoption, the next eligible work is a fresh bounded implementation phase of this exact surface. This design alone starts none of those gates.
