# C038: complete P16 retained-clock census

Date: October 25, 2026, America/Denver. Status: completed diagnostic; no runtime change or candidate promotion.

**P16 reaches its original operation cap while attempting authored clock pair 160 → 161, exactly 31/10 → 78/25 seconds. All 206 retained clock rows were already parsed and checked for direct binary32 rounding. Independent offline analysis verifies the entire axis, its required boundaries and its maximum rounding shift. The failed request remains failed.**

## Evidence and source identity

This is the bounded diagnostic selected by [HANDOFF-037](HANDOFF-037.md) and reserved in [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6404961225). The [checkpoint](checkpoint-038.json), [complete analysis](checkpoint-038-analysis.json), [archive manifest](checkpoint-038-manifest.json), [reviews](checkpoint-038-reviews.json) and [handoff](HANDOFF-038.md) identify the actual evidence. The fresh P16 numerical results below come from the retained control/capture and standard-library analysis in that archive; source-verification receipts and named historical checkpoints support their separate claims.

| Identity | Value |
| --- | --- |
| Documentation parent | 6404b1e590a900e550ae216394e0f17d010bac9e |
| Documentation parent tree | 1660f227a8554122d39cd4aba58b102f4dec565c |
| Exact execution candidate | 4ca73909f861fe4bef9694787473621c1d21c140 |
| Execution tree | 87c949b238055af1ce368c694e1d5683c8aeacde |
| Program revision | sha256:0487f3f410944484f0a6aad7bef37e1a59a1d13464b19af85661251c430388f7 |
| Original manifest | docs/language-design/planar-reach-v0.1/p16.files.json |
| Manifest SHA-256 | 0d218a8b1245766fa3e4892ec5ccafd275ee92fd4195b3b852d5daaefa9e4070 |
| Frozen request driver SHA-256 | 15549876920d4a19e37b472c698a9ca2e821b40967d96b6c8fd0c2ea01eef064 |
| Frozen pair runner SHA-256 | dbeca0a2cdd51be725c7d2bf5d446004d40c11463c90762e6bd75871e85736b4 |
| Successful analyzer SHA-256 | fa21413aaecb12e451f0ab22383724fe2732d98612e3492b8611a41cd2205cbd |

Both checkouts were recovered without changing the older workspaces. Fresh complete GitHub trees matched every local tracked blob, size and executable mode, and the original Git commit objects were hash-verified. Documentation began with 2,082 files / 462,916,542 bytes. Execution used 1,986 files / 442,072,108 bytes. Runtime, tests, tools, workflows and the named adopted reach inputs agree between those revisions. The documentation history is shallow; the execution checkout reports non-shallow history. These are distinct source identities.

## Exactly two original requests

The root executor ran one unchanged control followed by one post-failure capture. Both loaded the original four-unit manifest, compiled at constructed level and requested ontokin.glb/0.6 with end 4 seconds, integer fps 1, helpers false, position tolerance 0.001 m, rotation tolerance 0.001 rad and time tolerance 1e-6 s. The original loading path was unchanged; compilation created the shared request budget, which export inherited. No additional loading allowance was introduced.

Limits remained 100,000 shared operations, 30,000 ms, 32,768 operand bits and 256 entries in the existing numerical caches. The separate category metadata bound remained 512. The 180-second outer driver timeout only bounded the diagnostic process; it did not replace the product's 30,000-ms limit.

The mode-specific capture began only after the original exception was retained. It read whitelisted bounded native locals, exact integer/Fraction storage and bytes. Unknown shapes would fail capture rather than produce a partial census. It did not install a trace, profiler, work hook, arithmetic wrapper or replacement reader. It did not advance the retained generator or resume the failed request. Copies made afterward belong to the external diagnostic and provide no runtime reuse implementation.

## Neutrality result

The successful analyzer passed 85 neutrality predicates before interpreting the census. These cover the entire common result, using exact JSON types and float bits, plus complete raw traceback bytes and all four source inventories. The only excluded common-result fields are mode, command, timestamps, elapsed duration and capture-specific output/status identities; the exact exclusion list is in the analysis.

| Observed item | Control | Capture |
| --- | ---: | ---: |
| Product exit code | 1 | 1 |
| Shared operation counter | 100,001 | 100,001 |
| Completed reach operations | 95,640 | 95,640 |
| Complete operation categories | 266 | 266 |
| Work-cache entries | 256 | 256 |
| Separate independent arithmetic-cache entries after cleanup | 116 | 116 |
| Decoded accessor-cache entries | 36 | 36 |
| Decoded clock-cache entries | 1 | 1 |
| Full traceback frames | 14 | 14 |
| Product elapsed seconds | 3.9354351589972794 | 3.597366113001044 |

Every category count and cache occupancy list matches. All categories sum to 95,640. The shared-minus-reach difference is 4,361, including the refused shared charge; it is not independently measured as a construction-only category. The raw traceback contains 13 product frames and one explicitly identified external driver frame. No frame was removed to manufacture equality.

Both requests report the original OntoKinError, OKL-E-RESOURCE, max_operations limit 100,000 and consumed 100,001. Before/after inventories in both requests are byte-identical, SHA-256 09a024b2c1064f27326d4f3496ec9f1b9b94fadba4c326be0008bdc6c8b5736c. Driver bytes stayed fixed. The post-observation state equals the post-failure state in each mode. Mutable cache and callback observations are explicitly after cleanup, not claimed as historical entry or refusal-time snapshots.

The expected construction-callback error identity flag is false because the construction budget itself raises the original error. The reference model is a native shallow copy, so its identity with the compiler model is also false; relevant validation model/work aliases agree. Neither flag is hidden or forced true.

Matching operation/path/input receipts establish diagnostic neutrality on these two executions. The durations do not establish elapsed neutrality, a speedup, a timing cohort or performance acceptance.

## Complete independent clock reconstruction

The capture retains all 206 ordered authored labels and parsed Fractions, 206 actual stored binary32 words, stored/semantic row labels, exact end, native float tolerance, completed maximum shift and the uniquely bound attempted comparison. The analysis passes 243 census predicates and retains a per-row reconstruction for every row.

The analyzer uses Python's standard library and does not import OntoKin. It parses the retained GLB's actual JSON and binary chunks, checks accessor ranges/strides, and reconstructs the common clock for all 14 animation samplers. It decodes binary32 sign/exponent/significand into exact rationals and constructs midpoint cells with round-to-nearest, ties-to-even membership. This is independent of the runtime's bounded integer-grid clock-cell implementation. Canonical authored decimal numerator/denominator labels must match the captured native Fractions exactly.

| Complete-axis property | Independent result |
| --- | --- |
| Authored and stored key counts | 206 each |
| Common input accessor | 0 for all 14 samplers |
| Exact authored axis | Strictly increasing from 0 to 4 seconds |
| Actual stored binary32 axis | Strictly increasing from 0 to 4 seconds |
| Direct rounding-cell membership | Every authored value belongs to its stored value's cell |
| Required semantic boundaries | 0, 2, 3 and 4 seconds, all present with correct labels |
| Maximum absolute rounding shift | 3/26,214,400 seconds = 0.11444091796875 microseconds |
| Native time tolerance | Float bits 3eb0c6f7a0b5ed8d; exact ratio 4722366482869645/4722366482869645213696 seconds |
| Maximum shift within actual tolerance | Passed |

The largest shift occurs at zero-based indices 111, 124, 136, 149, 161, 174, 186 and 199. The analyzer reconstructs the boundary set from this exact P16 source's literal schedule: travel and turn start at 0 and finish at 3, reach finishes at 2, release and a one-second force begin at 2, and the requested end is 4. This restricted source extraction is not a general language evaluator and does not call a producer or reference kernel for expected values.

The retained 2,216,332-byte GLB has SHA-256 fc08f9e00599de7cb5f832879636d4102b4632d89f788410abca48d5e4c8d5da. It is **unvalidated reader input from the failed request**, not an accepted export. Passing these clock-only checks does not validate its geometry, endpoints or certificates.

## Exact refusal and completed work

The retained generator and _Bounds.compare operands agree by native identity and exact value. Exactly one adjacent pair in the complete axis matches them: indices 160 and 161, 31/10 and 78/25 seconds. The outer row-loop index is 205 because the row loop already completed; it is not the failing pair index.

At reach_conformance.py:181, _Bounds.compare asks for independent_exact_compare work. ConstructionBudget.tick increments the shared counter to 100,001 and refuses. ReachExecutionWork has not yet incremented its completed counter/category. The operands' input-width guards finished; the prospective cross-product guards and actual comparison arithmetic did not run. The generator's comparison-result predicate did not run either.

All retained rows, their direct rounding-cell checks, stored/semantic row labels and the maximum-shift calculation completed in the product request. The start/end condition and 160 preceding authored comparisons completed. The final semantic-subset and shift-versus-tolerance predicates occur after the refused monotonicity pass and were checked only by the offline analyzer. The failed request never executed those later predicates.

The original source yields the following ledger for this observed native short-label/full-domain axis. It is a control-flow reconstruction reconciled against observed categories, not a live stage-entry measurement.

| Completed part of verify_retained_clocks | Charges |
| --- | ---: |
| 14 common-sampler checks | 14 |
| 206 row iterations: 13N − 1, with the zero row's cheaper cell | 2,677 |
| 160 completed authored-order comparisons | 160 |
| Completed function work before refusal | 2,851 |
| Refused shared charge, not added to completed reach work | 1 |

The observed exact-compare category is 572: 412 direct-cell comparisons plus 160 completed authored-order comparisons. Exact additions are 411, bound decodes 412 and exact subtractions 206. Parsing categories include one earlier supplied-end parse: 414 integer charges and 207 charges each for reduction and reduction-return, compared with 412/206/206 for the rows alone.

The resulting reconstructed entry positions are 97,149 shared / 92,789 reach at the clock function and 99,840 shared / 95,480 reach at authored monotonicity. These positions are not directly observed snapshots. read_glb already populated accessor data; the first clock() can populate its clock cache from those rows without another work tick. Post-failure clock-cache occupancy does not establish when that copy occurred by itself.

The complete axis has 205 adjacent pairs, of which 160 comparisons completed. There are 45 uncompleted pairs including the refused one. The downstream independent geometry, endpoint and interval-certificate validation stages follow the clock function; producer geometry/certification and the reader's initial certificate shape/count checks already ran. No unvisited verification work was resumed, and no complete-request operation deficit is inferred from this ledger.

## Preserved analyzer failure and successful correction

The first standalone analysis command exited 1 at Python parse time: a missing closing parenthesis at line 563 prevented analysis from starting. Its exact source SHA-256 is 70b8cfb57aacf07b8d41b3fc10518a9c62edc4b7251a7fe05f12cea76e1eadd1. Its source, closed command, full streams and stable input receipts remain in the archive. The first static review had missed this error and is retained unchanged.

The correction adds one closing parenthesis; no algorithm, input or predicate changed. A separate review and root syntax preflight passed. Analysis attempt 002 then exited 0 with 85 neutrality and 243 census predicates passed, unchanged complete source inputs and unchanged command files. Neither analysis attempt executed a product request. The original control/capture pair was not repeated.

## Next bounded question

The [next-scope record](checkpoint-038-next-scope.json) selects source-only feasibility review of an equivalent independent ordering proof. Distinct increasing finite binary32 values have ordered rounding cells. Adjacent cells may share a midpoint, but ties-to-even assigns that point to only one cell. Exact authored values independently proved to belong to those cells therefore have strict order.

This mathematical implication and the observed axis do not establish that the implementation can use it safely or cheaply. Review must establish current reader proof provenance, native dispatch and storage, source/work ownership, callbacks, mutation/reentrancy, smaller operand domains, cancellation/failure ordering, bounded lifetime and ordinary fallback. Direct calls to verify_retained_clocks can use custom readers, and native DecodedGLB objects and caches are mutable. An exact class check or an earlier read_glb call alone is insufficient: any future proof authority must bind the current invocation and exact current axis, with ordinary fallback elsewhere. Every new lookup, type/limit/claim check, copied logical value and storage action remains charged under [adopted budget-counting section 3](../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse), whose authority comes from [ADOPTION](../../language-design/planar-reach-v0.1/ADOPTION.md).

There are 205 gross authored-comparison sites in a complete pass. This is neither measured saving nor a proven net saving. Added per-row admission could consume that opportunity. No runtime optimization is selected by C038, and no complete P16 pass is predicted. A supported no-go is an acceptable result of the next source-only task.

The latest complete original suite remains C035's 24/28, with P11/P16/P23/L03 capped. C035 remains held, including its adverse L03 diagnostic timing. P11 component retention remains rejected under C037; L03 reseeding and P23 producer sampling remain separate scopes. The remaining reach release and full product goal are open.
