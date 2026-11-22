# P17: exact static-TLS flags on the selected libc

Decision: `ontokin.c271.libc-static-tls-flags-decision/1` (`P17-FLAGS-001`).
Author: `/root/flags_design`. State: proposed and frozen for independent review; a separate Director adoption is required. This phase supplies no implementation or product execution.

## Decision

Add one future, explicitly selected inspection-plan/profile pair. On its already bound x86-64 libc dependency only, the private metadata reader may accept a single `DT_FLAGS=0x18` in addition to the existing absent, zero and `0x8` cases. `0x18` combines `DF_BIND_NOW=0x8` and `DF_STATIC_TLS=0x10`. TLS means thread-local storage: separate storage for each thread. The added recognition says that the flag describes a reviewed form of metadata in these exact libc bytes. It does not establish that a loader can allocate the required TLS, perform the relocations, or execute the image successfully. [S01–S05]

This is an exact extra value, not a mask change to `0x18`. A lone `0x10`, any additional bit, and every duplicate `DT_FLAGS` entry remain refused. The `DT_FLAGS_1` mask and multiplicity remain exactly as before. Absent, zero and `0x8` remain private-primitive positives to retain the previous reader's accepted cases; the actual pinned operational libc has exactly `0x18`. No synthetic variant can meet its operational digest. [S01, S06]

| Route | Permitted `DT_FLAGS` presence/value | `DT_FLAGS_1` |
| --- | --- | --- |
| Public/default; plan `/0.1.0`; plan `/0.1.1`; P16 plan `/0.1.2` | Absent or exactly one of `0`, `8` | Absent or one value with no bits outside `0x08000001` |
| New `/0.1.3`, after exact dependency-role and libc/loader binding | Absent or exactly one of `0`, `8`, `24` | Same unchanged rule |

The deliberate exclusion of `0x10` alone is this selected-image policy, not an assertion that the ABI makes it invalid. The proposal introduces no general static-TLS support, TLS parser, relocation interpreter, new memory bound, or TLS success claim.

## Source and exact applicability

The historical inert libc is 1,995,216 bytes, SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`. The associated loader is 225,672 bytes, SHA-256 `c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307`. A fresh data-only package extraction matches both to the corresponding members of retained Debian package `libc6_2.41-12+deb13u4_amd64.deb`. Package control and the checksum-bound `.dsc` associate the build with glibc source `2.41-12+deb13u4`, amd64. This association does not include a verified signature, reproduced build, build log, or compiler-output proof. No current-host path was opened. [S01, S02]

The exact glibc source defines the bits, stores `DT_FLAGS`, and converts `DF_BIND_NOW` into the older bind-now indicator. Its bootstrap branch permits only bind-now for the loader itself; that branch is not a reason to allow static TLS on the loader role. The proposed subject remains the selected libc dependency, never the ELF interpreter. [S03]

The static-TLS helper checks whether a referenced object's TLS offset is already static, or tries to allocate suitable surplus. The x86-64 `R_X86_64_TPOFF64` relocation invokes that helper. Allocation can fail. These are runtime behaviors whose feasibility cannot be inferred from `DT_FLAGS`. The exact-token source scan finds the `DF_STATIC_TLS` definition and explanatory helper comment, not a separate current-code branch testing that macro. That scan is supporting evidence with an explicit textual scope, not a whole-program proof. [S04, S05]

For dependency metadata, accepting this one bit combination adds no dependency name, search directory, alternate file selection, pointer dereference, allocation, or value-sized scan. Existing ELF parsing already does not establish general relocation or executable-code safety. Requiring TLS layout or allocation validation here would expand that contract beyond this phase. The inherited complete source/closure review, all actual-host checks, and later observation and qualification gates remain required. [S03–S07]

## Separate version and exact relation to P16

The new pair is:

| Member | Exact value |
| --- | --- |
| Plan schema | `ontokin.current-host-readback-inspection-plan/0.1.3` |
| Resolution profile | `linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-v1` |

It uses exactly the P16 resolution keys, including the unchanged `origin_rpath` and `libc_plt` objects. `libc_plt.schema` remains `ontokin.current-host-readback-libc-plt/0.1.0`; its exact keys remain `schema`, `subject`, `loader`. Subject and loader retain the closed `{path, sha256, size_bytes, mode}` shape and exact P16 pins, with operational mode `0o755`. The pair alone selects the fixed additional flags rule. No `allow_static_tls`, flag mask, approval word, completeness field, tunable, extra command, or new resource document is accepted.

P16 is an adopted **design**, not an implemented route at the retained source revision. Its `/0.1.2` pair, all 73 controls, all expectations, and its `N16_flags_0x18_preserved` refusal remain unchanged. Both older implemented routes remain unchanged as well. The new profile can share internal structural code while choosing a separate fixed predicate. It must not mutate the plan's schema to impersonate P16, rewrite the plan descriptor, modify the public signature/default, or widen a global mask. P16's three-tag architecture, unknown-tag and exactly-once-trio rules apply unchanged on the new route. [S06, S07]

The fixed `shared_libraries` command's `stdout_predicate` remains `linux-glibc-declared-closure-v1`. P06 consumer schemas and output shapes remain unchanged. P13 source-completeness review stays external; no synthetic control label becomes an operational input.

## Binding, order and rechecks

Every P16 dependency proof is mandatory for the new pair. Actual selected author-Python metadata must name `libc.so.6`; its unique selected edge, dependency-role membership, complete host/runtime aliases, file descriptors and unique libc image row must agree. The actual Python interpreter, corresponding loader image, host/runtime bindings and exact loader pin must agree. Subject and loader paths must differ. Python, Node, Git, shell, inspector, ELF-interpreter and extension roles cannot receive this exception. Merely supplying a filename, same hash in an unused row, or caller policy object is insufficient. Use the unchanged real `_bound` checks before the subject's raw reader. [S07]

For the new pair, complete this proof and inherited origin/resolution/guard proof before `_load_helpers`, source Git reads or commands. Other images use their existing reader. Each complete `_recheck` must derive the policy anew from fresh actual metadata and bindings; no cached accepted policy or result. Both pinned files remain in existing snapshots and launch guards. Existing outer `CHI-DRIFT` and underlying causes remain unchanged. [S06, S07]

Within the subject-only private reader, ordering is normative:

1. Existing file, ELF, table, mapping and terminator checks.
2. P16 x86-64 `ET_DYN` restriction, precise tag allowlist, then exactly-once complete trio.
3. The fixed P17 flags rule above, including unchanged `DT_FLAGS_1` checks.
4. Every remaining string, needed-name, path, identity and final callback check.

All flag failures retain `CHI-UNSUPPORTED / Unsupported dynamic flags`, `REJECTED`, empty details and no cause. Earlier unknown-tag/trio/architecture failures stay earlier. A later string or path failure still refuses after `0x18` recognition. Metadata output remains the existing nine-key dictionary. No TLS result field is added.

The fixed flags scan runs only inside the existing bounded dynamic table; no new cap is introduced. Preserve the 65,536-byte dynamic-table ceiling, all file/string/mapping/path limits, 16 MiB document reader, and source execution ceilings of 100,000 operations / 30,000 ms. New callbacks before and during the fixed flags scan use the existing zero-argument `check`; old routes receive no extra calls. Same-object callback propagation and exactly-once close of the actual opened descriptor remain required on success, refusal and faults.

## Controls, limits and next gate

The corpus is inert, independently frozen before any product execution. New metadata cases use small data-only ELF files with mode `0o600`. The main positive intentionally has no TLS segment; it tests metadata recognition only and cannot satisfy the real-image pin. Binding/dispatch cases supply labelled mocked observations. Their positive results prove no actual file binding or whole-plan admission. `CONTROL-CONTRACT.md` describes each boundary; literal expectations are separate from construction and the integrity checker.

P15 observed the earlier tag refusal. Its flags predicate did not run. The P16 comparison and this phase's raw-byte observation establish a static inference about a later predicate, not a new observed product failure. This proposal supplies no later product outcome for those retained libc bytes. H0, the complete operational plan, H1, original-seven/full-routine execution, R03–R05 and parent completion remain unmet.

After independent exact-candidate review and separate adoption, a fresh phase may select the bounded implementation of both the adopted P16 tag route and this P17 extension. That implementation must consume all unchanged inherited/P16 controls plus this corpus and obtain independent exact-source/adapter review. It stops before H0/H1 or runtime preparation. No second technical phase starts in this chat. `FUTURE-SURFACE.json` bounds that future work; any missing design requirement stops it for a separate decision.

Source IDs refer to `SOURCE-EVIDENCE.md`; exact bodies, ranges, hashes and inherited contracts are bound by `READSET.json`, `INPUTS.json` and the candidate manifest.
