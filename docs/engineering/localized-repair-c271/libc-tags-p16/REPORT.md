# C271 P16: reviewed libc tag decision

P16 adopts a finite compatibility design and frozen inert controls. It changes no production or test behavior. The parent C271 task remains open because operational-plan adoption, host qualification, the required full routine and integration are still unmet.

## Adopted decision

The proposed inspection plan `/0.1.2` and `linux-glibc-declared-python-origin-rpath-libc-plt-v1` profile would recognize exactly `DT_X86_64_PLT`, `DT_X86_64_PLTSZ` and `DT_X86_64_PLTENT` on the selected x86-64 libc. The private reader treats their values as opaque dependency metadata. It must first bind the actual selected author-Python dependency, complete aliases and descriptors, and the exact retained libc/loader pair. It must repeat those proofs on rechecks.

The exact glibc source shows that these tags can drive Procedure Linkage Table rewriting, including instruction and page-protection changes. The design therefore makes no claim that they are universally harmless or that the reader validates executable safety. It preserves both earlier plan routes, all flag masks, later checks, pins, limits and output shape. See the [frozen decision](design/candidate001/DECISION.md), [control contract](design/candidate001/CONTROL-CONTRACT.md) and separate [Director adoption](ADOPTION.json).

## Evidence and review

The candidate manifest binds 169 payload files, 73 controls, 47 inert ELF images and 120 fixture files. Author verification recorded 810 static integrity and 46 source/package assertions. The [independent review](review/candidate001/REVIEW.md) reconstructed every ELF image and checked all controls through 1,493 static assertions, with no mandatory findings. It also matched 18 upstream source members, 80 active patch records and 31 protected source paths. These counts are not product-test passes.

Two review observations are retained without changing the frozen candidate. Each control's `image` descriptor selects its actual reader input; `actual_fixture_bytes` is a shared baseline reference and differs in 35 mutated contexts. A separate flags decision should precede implementation. The adoption records both dispositions explicitly.

Exact retained Debian package members bind the source analysis to the captured libc and loader. This is not a reproduced build, local signature verification, current-host observation or operational-plan approval. Supplemental raw web responses are omitted from distribution under [explicit exclusions](review/EXCLUSIONS.json); their identities, sources and failed retrieval are retained, while exact implementation source evidence is preserved.

## Boundary and next phase

P15 observed the first unsupported dynamic-tag refusal. Its later flags predicate did not run. The retained `DT_FLAGS=0x18` is outside the unchanged `0x8` mask; a later refusal follows by source comparison if tag recognition succeeds. P16 preserves that refusal, including its synthetic control, and implements no exception.

After verified P16 delivery, the next fresh parent chat should select one bounded source-backed DT_FLAGS/DF_STATIC_TLS compatibility decision for that exact libc. It may retain refusal. This ordering supersedes only the candidate's next-step sentence. No implementation, parser/product tests, new H0/H1, Node/ldd, installation, original-seven/full routine, native/model/hosted execution, main lease or merge is selected in P16.

The [phase record](PHASE.json) records acceptance gates and actual delivery state. Documentary/workflow/whitespace and protected-tree verification, conditional branch publication, final ZIP/prompts and the separate actual receipt finish this phase. The confirmed [early recovery receipt](EARLY-RECOVERY-RECEIPT.json) predates substantive work. Existing failures and historical unknowns remain preserved; the [learning review](LEARNING-REVIEW.json) reuses the existing source-versus-admission lesson without broadening it.

## Exact evidence storage

The complete frozen candidate and independent source evidence are preserved in verified archives, with readable records beside them. Follow [evidence materialization](EVIDENCE-MATERIALIZATION.md) before any later use. This keeps verbatim source and patch whitespace intact and preserves the failed documentary preflight separately.
