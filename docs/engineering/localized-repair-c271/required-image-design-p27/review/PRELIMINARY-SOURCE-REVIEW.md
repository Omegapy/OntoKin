# P27 independent source assessment before candidate review

Reviewer: `/root/design_review`. This is preparation for exact-candidate review, not adoption or implementation approval.

## Necessity and portability

P26 records a bounded, source-backed counterexample. Under its fixed direct Node command, environment, cache observation and existing kernel trust boundary, Node's first declared dependency selects the retained `libdl.so.2`. The current inspector requires a complete image/edge closure but sends that non-libc image to its ordinary dynamic-tag predicate, which excludes the observed trio. The private libc route has different exact role, size, hash and loader requirements. Omitting libdl or assigning it the libc role would violate the adopted contract. This remains a source deduction; no product refusal or whole-plan failure order was observed in P27.

`RETAINED-BYTE-AUDIT.json` independently decodes the already retained binary package as data. All five relevant members equal P26's corresponding image sizes, hashes, full dynamic tables and named metadata. The libdl member also equals the saved inert handoff fixture. The first audit attempt wrongly required OSABI zero for every image; libm has OSABI three, already allowed by the existing parser. The original script, failure and focused correction are preserved. No installed host library was opened.

The selected Python's retained actual `DT_NEEDED` list contains all five names directly. This gives a finite root relation for a five-member catalog. Fresh actual metadata, corresponding unique declared target edges, role/alias/file agreement and immutable package-derived pins must still be checked. Those relations do not mechanically prove the loader's choice; the complete independent source/closure review remains external and unfinished.

## Source semantics

`PRIMARY-SOURCE-BINDINGS.json` verifies the exact 20,323,540-byte upstream archive against SHA-256 `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998`. Selected author extractions and retained P16 copies equal exact archive members. `PATCH-AND-SOURCE-ASSOCIATION-AUDIT.json` independently verifies the retained `.dsc` checksum association and indexes all 80 active patches. This is neither signature verification nor a reproduced build.

The three numeric tags are x86-64 PLT metadata. `elf/elf.h` defines them; `sysdeps/x86_64/dl-dtprocnum.h` and `elf/get-dynamic-info.h` show architecture-specific indexing. AArch64 uses colliding numbers for different features. `sysdeps/x86_64/Makefile` and `configure.ac` enable `mark-plt` when supported and explicitly disable it for the loader. The PLT consumer can change memory protection and rewrite branch instructions after relocation. Its feature state is initially disabled and the inspected setter requires an explicit nonzero tunable. The fixed five-variable launcher environment excludes that tunable. This supports narrowly scoped metadata recognition, not executable PLT, relocation or runtime-safety validation.

Libm's `DT_FLAGS=0x18` combines bind-now and static TLS. The exact flags handler and x86-64 relocation/static-TLS helpers support the P17 distinction between recognition and runtime allocation. Static allocation can fail. A new libm rule must add the exact value 24 only; lone 16 and additional bits must remain refused.

Librt's `DT_FLAGS_1=0x9` combines now and nodelete. `rt/Makefile` explicitly links librt with `-z,nodelete`, and no active patch changes that file. `get-dynamic-info.h` sets pending nodelete; `dl-open.c` activates it after fallible setup; `dl-close.c` retains active maps and their dependencies. `dl-lookup.c` uses this state in relocation dependency accounting. These are real lifetime effects and may preserve objects for later lookup. The finite metadata decision must not call the flag universally inert or certify arbitrary future loading/unloading. An exact added value 9 on the bound librt slot is distinguishable from a widened flags-1 mask.

## Alternatives and review conditions

Retaining the current refusal is sound if the exact new policy cannot be specified or reviewed. A different already conforming same-pin runtime/library/layout route is conceptually available but is not established by these artifacts; searching a disposable host or replacing arbitrary libraries would not resolve the durable design requirement. A universal processor-tag allowance, filename-based glibc allowance or transfer of libc's private exception would exceed the evidence. Changing the selected runtime, original test cohort, dependency contract or command protocol would change the task.

A coherent finite package-associated catalog is therefore supportable in principle. Acceptance still requires the exact candidate to preserve every old profile and oracle, bind all five real dependency roles before private parsing, retain existing alias/path and source checks, specify separate libm/librt predicates, preserve finite budgets, and provide literal positive/refusal/boundary controls. Source mismatch, orphan rows, role collisions, changed pins, old-route behavior, callback faults and recheck drift must be explicit. N34 and historical N57 remain external review obligations; no metadata primitive can establish them.

No implementation, product import or parser/test invocation, H0/H1, Node/ldd, installation, original-seven/full-routine execution, integration or parent closure is part of this review.
