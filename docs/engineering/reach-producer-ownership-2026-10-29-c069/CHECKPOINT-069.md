# C069: an existing cached-list receipt has no enforced ownership interval

Date: October 29, 2026, America/Denver. Coordinator: `interactive-producer-ownership-20261029-c069-7of9`. [Declared scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6511706076). Baseline main: `7c0bf98e48a641e30627b7fd261b6713d79e223c`, tree `a53acdaa3a65c8863a027ee407e1f291ffe4ae24`.

## Decision

Reject the C069 mechanism that would issue a producer receipt for the existing cached POSITION list, then authorize C067's future-seed omission using object identity and an unobserved generation counter. Neither the decoder nor the numerical cache supplies the required ownership mechanism. The first optional router operation also lacks an independent native/passive authority root. No authority-safe, completely funded schedule or positive complete-request premise has been established for this mechanism.

The result is narrower than an impossibility claim. It does not rule out a separately adopted, enforceable native execution boundary or a different algorithm. It also does not assert that the ordinary source request actually mutates its decoded list. The unmodified native path has no explicit POSITION mutation after decoding. Its construction callback meters the shared request; it does not itself edit geometry.

No runtime code, instrumentation or product experiment is selected. [C068's proposal](../reach-cold-admission-2026-10-29-c068/PROPOSAL-068.md) remains **UNADOPTED**. C068's losing eager scan is preserved as historical evidence and is not repeated as this checkpoint's result.

## What the full path establishes

The [source trace](SOURCE-TRACE.md) starts at the actual original source-artifact driver. It follows compiler and budget creation, exporter reuse, eager supplied-byte decoding, structural checks, reference/metadata/clock work, independent source construction, topology reads, the wrapper's charged cache lookup and the cold scan. The source bytes and definition ranges are bound in [derived evidence](derived-evidence.json).

Three facts determine the decision:

1. `compile_construction(..., level="constructed")` receives no custom check. It nevertheless creates reach work whose `external_check` is the native `ConstructionBudget.tick`. A router that requires a null external callback excludes the intended request. Agent service compilation adds a different callback chain and must be treated separately.
2. `read_glb` eagerly decodes every accessor. `DecodedGLB.accessor` returns the same cached mutable list on a later hit. POSITION is therefore old retained data when `_geometry_bounds` fetches it. NORMAL/index checks and `work.lookup` still occur before the cold scan. A receipt issued at this later fetch cannot claim new decoding or erase the earlier exposure.
3. `ReachExecutionWork._cache_generation` protects numerical-cache reentrancy, promotion, insertion and operand-domain resets. It has no connection to writes through POSITION aliases. The decoder has no mutation wrapper, generation field, borrow count or invalidation method. A proposed decoder counter updated only by its own methods misses writes that bypass those methods.

The independent source tuple has a different property: once its actual native producer and native tuple/float contents are established, retained references preserve those immutable values. That does not authenticate a mutable source-cache hit, the producer's dispatch or the stored POSITION list. The writer and independent reader use distinct cache namespaces; this is necessary separation, not proof of every cached value's provenance.

## Concrete failed mechanisms

| Mechanism considered | Source-bound reason it does not supply the required authority |
| --- | --- |
| List identity plus length at issuance | Item replacement can retain identity and length; later truncation can remove the nominated seed. Identity does not certify contents or future traversal. |
| Reuse `work._cache_generation` | Its increments concern `work._cache`; direct writes to `decoded._cache[index]` or the returned list do not call those methods. |
| Add a decoder epoch only to `accessor` | A returned native list permits item/slice writes and ordinary mutators without calling `accessor`. An unobserved write leaves the stamp unchanged. |
| Save callable aliases or a native flag | The router still needs to establish that the saved code, bindings, storage and payer are authentic before its first optional inspection or charge. The flag cannot establish its own authority. |
| Reuse the certificate native gate | C057's foreign-key lookup concern and paid-entry question remain, and the gate does not bind the complete geometry/decoder interval. |
| Install the existing source observer | The hook observes existing charge boundaries. It is neither a list lock nor an authenticated mutation monitor; its own checks and lifetime would require proof and funding. |
| Freeze or copy POSITION | A tuple-returning accessor or cold snapshot changes the current live-list behavior. A copied list also needs authentic current row facts. These are different semantic proposals, not this receipt. |
| Trust the existing post-scan extrema proof | Its block checks and snapshot occur after the cold result. They cannot justify an omission that already occurred earlier. |

The source-derived mutation matrix records which owner each transition actually reaches. It is a declarative analysis of bound code, not execution of injected mutations. We do not count an unimplemented protection mechanism as zero-cost.

## Conditional first-exception and lifetime witnesses

Two separate obligations must not be conflated.

**Entry.** Native `charge` reads a mutable `counts` dictionary using the category key. C057 also identifies optional module-dictionary lookups that can encounter foreign colliding keys. An added category, lookup or predicate may encounter a foreign operation before the original next operation would do so. A type check of the outer dictionary is insufficient. No new inspection is permitted merely because it is called an admission test.

**Lifetime.** On a generic/custom path, a callback holding a stored-list alias can truncate it after coverage was checked and before the future seed is reached. The original `zip` can terminate with earlier exact folds already accumulated. A candidate that omitted those folds in reliance on the future seed may terminate without inclusion or synchronization. Turning the shortcut off then does not reconstruct the omitted accumulator state. A valid design would need a separately proved restoration/replay path and would pay its actual work.

These are conditional source witnesses. C069 did not execute them, demonstrate a stock export failure or claim that the original native construction callback has such an alias. The purpose of a router would be to distinguish the safe path before taking the shortcut. The missing trusted entry and enforced lifetime are precisely what prevent this proposal from doing so.

## Receipt and accounting result

[RECEIPT-069](RECEIPT-069.md) fixes a proposed 24-field subject record and four-field seed record. It identifies every retained subject, publication point, use and invalidation obligation. The construction is deliberately explicit so that a named receipt cannot conceal a free namespace scan, cache proof or ownership assumption.

Under C068's **unadopted** operation catalogue, one empty 24-slot record plus one write per slot requires 25 proposed units before any capture, authentication or lifetime work. A separate four-slot seed record adds five. These are conditional counts for this declared layout, not an adopted operation definition, implementation cost or lower bound on every possible layout. Field reads, predicates, exact binding checks, repeated occurrences and retirement remain separately payable.

The complete matched-work equation remains

`saving = 6*(B-K) - S - I - A_router - A_producer - A_lifetime - A_admit - A_seed - A_retire - F`.

`B-K` counts removed completed exact folds; `S` and `I` count additional reached bound and seed-identity comparisons. Each `A` is a disjoint sum of actual added events. `F` contains only additional restoration/replay/rescan events not already counted. Partial folds use their actual reached charges. The retained work must first be shown equal before this equation can describe complete savings.

The fixed seed's historical 798 gross ceiling and favorable abstract 530 residual do not establish the missing terms. C069 neither proves this total nonpositive nor reports a numerical cost for the unavailable router. The route is rejected at authority and lifetime admission, before a complete cost claim is possible. Warm hits, failed partial admission, interrupted publication, repeats and retries cannot reuse an unauthenticated receipt or erase their reached costs.

## A different next scope

The next scope leaves the future-seed/borrowed-list route. [NEXT-TASK](NEXT-TASK.md) identifies the writer's exact angular certificate calculation: nine explicit arithmetic calls depend on four exact inputs, while its current whole-group cache key includes many additional positional and geometric inputs. Reuse across distinct whole groups could therefore be a different source of savings. Actual duplicate incidence, guard and first-exception preservation, cache displacement and complete costs are unproved. This is a concrete source-only feasibility target, not an approved implementation. A current-row leading-zero-addition alternative was also considered; its one-charge gross opportunity is too narrow to prefer before pricing its own admission.

## Evidence and preserved state

The standalone derivation reads bound bytes, parses Python ASTs and checks source ordering, assignment ownership and declared record arithmetic. It imports no OntoKin module and creates no mesh or numerical product request. Its result is independently reviewed against the source. The [validation record](validation.json) names actual execution attempts and output hashes; the [integration record](integration.json) records the publication state. Candidate, actual-merge and final-main checks are pending at this source-review cut; only subsequently retained actual receipts establish their execution.

The complete original C068 packet and ZIP were freshly verified: 3,663 source files / 622,197,405 bytes, zero omissions; ZIP 476,328,864 bytes / SHA-256 `7ee6edca85ac33944b08c8eda0d48e1cc8d21d7bcee35ff30d2ee50e4e01a09b`. Its historical C067 verification and older C066 source-recovery boundary remain unchanged. A local clone failure and initial ignored-file staging failure are retained in [preparation](PREPARATION.md); exact source reconstruction corrected both without inventing a commit or full history.

All 65 runtime files and every existing test, fixture, contract, default, limit and workflow remain unchanged. C069 executes zero product imports, requests, runtime suites, native trigonometric evaluations, generated meshes and hosted jobs. Historical original recordings remain **24/28, failed** with **P11/P16/P23/L03** unresolved. M1 stays rejected; C035 stays held including adverse timing; C057, complete reach acceptance and historical LFS migration remain open. Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries, 64 cursor updates and all original acceptance inputs. The full language, modeling, dynamics, purposeful movement and engine-delivery [GOAL](../../../GOAL.md) remains in progress.
