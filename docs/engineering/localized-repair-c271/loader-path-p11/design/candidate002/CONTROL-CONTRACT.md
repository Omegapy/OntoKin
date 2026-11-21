# P11 portable controls: exact scope and interpretation

The 93 cases in `FIXTURE-MANIFEST.json` are independently authored design controls. Their expected outcomes are in `EXPECTATIONS.json`. No implementation is present or executed. The artifacts include 26 tiny ELF64 images, eight auxiliary-vector byte strings and 93 JSON contexts. Every file is an inert regular file with mode `0o600`; no actual alias, hardlink, FIFO, special file or executable image is created. Logical filesystem states live in JSON.

## What each route proves in a future run

| Route | Later adapter boundary | What acceptance means |
| --- | --- | --- |
| `legacy_metadata` | Existing public `read_elf_metadata` with the stored ELF as data. | Exact unchanged metadata or legacy refusal. No host/profile admission. |
| `origin_rule` | New private raw-metadata/origin/nonselecting rule, with the frozen synthetic filesystem and kernel observations supplied at explicit seams. | Only the rule's transformation/refusal on that finite context. All operational selected-image/source/host gates remain outside this synthetic positive. |
| `binding_rule` | Explicit external-plan/subject binding predicate before new token admission. | Named refusal; a synthetic ELF cannot satisfy the selected real Python hash/size/mode. |
| `recheck_rule` | Existing `_recheck` error boundary with the frozen before/after logical observation. | Outer `CHI-DRIFT` and retained cause. It is not an actual process or host drift observation. |
| `fault_contract` | New callback seam specified by `fault.at`. | Exact supplied callback exception propagates at the raw helper boundary. No production injection ran in P11. |

The contexts use `ontokin.c271.p11-portable-rule-context/1`, deliberately different from any operational plan. Their `operational:false`, logical identities, asserted synthetic suffix model and selected seam are not valid inspection-plan fields. A later test adapter must bind its actual source and show how each supplied observation reaches the actual production helper. It may not replace the real image pin with the synthetic hash in production or call an origin-helper result a whole-plan pass. No positive whole-profile/H0 fixture exists because the real origin/closure/variant inventory is not yet established.

The selected real Python descriptor in synthetic contexts identifies the external operational pin. The `subject.actual_bytes` descriptor truthfully binds the different synthetic image. `N25_synthetic_fails_real_pin` expects refusal if those bytes are submitted to operational subject admission. Other synthetic positives have an explicit private-rule precondition; they do not conceal this mismatch.

## Oracle construction and precedence

`build_controls.py` writes fixed ELF header/program-table/dynamic-table/string bytes directly with Python's `struct`. It never imports the inspection module, invokes a production parser, implements the acceptance predicate, queries host paths or launches a child target. `CONSTRUCTION.json` records exact offsets, field strings, bytes and metadata intended by construction. The expected mapping is literal author input. No postimplementation output can modify the expected result.

The old public reader retains its current ordering and error text. The new route's error stages are frozen as follows: authenticate externally supplied plan bytes; select the exact schema/profile/closed shape; validate finite collection-size ceilings; bind the subject and invocation role; retain existing ELF structural/tag/flag/metadata-uniqueness checks; enforce the one raw RPATH grammar before new-path processing; validate kernel/origin/derived-directory facts; validate exact name union and bound variant review/inventory; check nonselection; finalize identity/callback checks. Variant/name cardinality bounds apply before iterating contents, so the large synthetic bound cases have one defined early failure even though later contextual checks would also refuse. A new-profile repeated colon component fails the new exact raw grammar; the old route's duplicate search-path check remains unchanged.

`code`, `stage` and `rule_id` are the normative future selectors for new refusals. `rule_id` can be retained in the existing error `details` object; no error-schema change is needed. Where a legacy reason is supplied, it is exact and must remain unchanged. Callback sentinel tests operate at the new raw helper boundary so exception identity is observable; the existing top-level wrapper's behavior remains a separate preserved obligation.

The new subject can only be the one x86-64 Python. Other literal ELF images and the old AArch64 branch retain their existing source checks. Synthetic `P05_allowed_flags_preserved` tests only the existing mask at the private primitive; it does not claim those invented image bytes equal the selected Python.

## Positive and refusal coverage

The seven legacy cases include literal RPATH, literal RUNPATH, absent search paths, default token refusals, the dual-tag conflict and unsupported origin flags. Seven new positive primitives cover the exact expansion; harmless unrelated basename; a fully inventoried empty hwcaps alternative; an extension dependency added to the union; the unchanged flag masks; exactly 256 auxiliary pairs; and exactly 4,096 pre-normalization path bytes.

`P07_expansion_4096_bytes` has an **explicitly synthetic base-only suffix model**. It isolates the path-length boundary. It does not assert that any actual glibc loader has no hardware or TLS variants. Candidate001 mistakenly appended unrelated variant paths past the same length ceiling; that failed authoring attempt remains preserved. Candidate002 changes that one context, with the same mapping expectation and unchanged production source.

The 73 refusal primitives cover schema/profile separation; unknown/absent fields; external digest and referenced-document identity; wrong roles; explicit loader invocation; deleted/unavailable/mismatched kernel image; wrong origins; symlink/ancestor/hardlink contexts; synthetic versus real pins; secure/ambiguous/overbound auxiliary vectors; unsupported token spellings; RPATH/RUNPATH separation; dynamic flags/tags/duplicate metadata; wrong or unbound derived path; incomplete/extra dependency names; incomplete/foreign/unknown variants; changed absence; file/symlink/directory/special candidates; hwcaps/TLS candidates; extension candidates; tokens in needed/SONAME; second token-bearing image; and each new finite ceiling. Candidate entries refuse even when their target could be an already bound file.

Three recheck cases cover new candidate entries, origin inode drift and changed kernel executable. Three callback controls cover variant read, candidate scan and final identity. These are future fault-injection obligations, not executed-fault results. The larger size/product negatives isolate early bounds; they are not executable full plan templates.

## Static verification and preservation

`validate_artifacts.py` checks exact path/size/mode/hash inventory, complete case/oracle coverage, inert files, fixed construction bytes, raw metadata expectations, and positive declared lengths/cardinalities. It does not implement the origin policy or call production code. Candidate002 passed 1,084 such checks. That count is not a product-test count. Candidate001's one failed positive-length check and unchanged corpus remain recoverable.

Later implementation verification must consume these frozen controls without editing their expected outcomes, retain all failed attempts, execute all 175 existing inspection/mapping methods under their existing constraints, and independently check legacy/default source and consumer compatibility. Those future checks are not run in P11. Do not weaken P10's 40 controls or the original 135 inspection methods to accommodate opt-in behavior. Direct kernel reads and variant review remain unestablished on an actual eligible host until a later H0 phase.
