# C068: the ordinary cold reader needs producer authority, not another eager scan

Date: October 29, 2026, America/Denver. Coordinator: `interactive-cold-admission-20261029-c068-7of9`. [Scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6511179345). Baseline: `7c1bf5d32d194f2faf7f38c9f3c153089f7a7b7e`, tree `f1bfe1c770fd1fc1c0aca5fbeabf54d4ac1f0aa5`.

## Decision and scope

The concrete eager admission schedule fails its operation-saving objective even when restricted to the shortest useful prefix and given credit for the current row's already completed source-type checks. Its required leaf checks alone exceed the maximum removable numerical work. Starting later does not repair that inequality.

The source does not establish a cheaper passive authority for the ordinary mutable stored-position list. Native construction history does not prove that the list and its rows are still unchanged at this cold call. Reusing the existing certificate gate would inherit C057's unresolved inspection and funding problem and would omit geometry-specific dependencies.

Accordingly, no runtime implementation, instrumentation or original-request execution is selected. [OK-PROP-COLD-ADMISSION-068/0.1.0](PROPOSAL-068.md) is a narrow **unadopted** producer-receipt and mutation-boundary proposal. It makes the missing authority and each class of added work explicit. It is not a working receipt implementation or a positive complete-request premise.

C068 advances C067 in three ways: it identifies the full producer-to-reader exposure, proves an entry-seam-independent rejection of the obvious prefix checker, and defines a concrete alternative decision boundary. It does not repeat C058's comparison M1 model or change that model's rejection.

## 1. The actual call and the state it receives

The source-artifact driver calls `compile_construction` and then `export_glb` with the compiler's existing reach work object. Construction creates `ReachExecutionWork(check=budget.tick)`. With the original driver arguments, the construction budget has no nested custom check. This identifies a potentially useful source-request path; it does not authenticate every later dispatch or establish a new trusted-host rule.

The relevant reader path is:

1. `validate_reach_export` calls `read_glb(data, check=work.tick, ..., work=work)`.
2. `read_glb` creates `DecodedGLB`, decodes every accessor, finite-checks its values and retains each decoded list in `_cache`.
3. Numeric-basis, program/reference, metadata and clock work runs before `_geometry_bounds`.
4. `_geometry_bounds` obtains the actual source mesh, retrieves the cached POSITION list, checks coverage, and validates the primitive's normals and indices.
5. `_vertex_extrema` checks its cache eligibility and calls the charged `work.lookup` before an ordinary cold miss reaches `_vertex_extrema_uncached`.

The precise definitions and line ranges are derived from the bound source in [derived-evidence](derived-evidence.json). `DecodedGLB.accessor` creates a native list of unpacked tuples on a miss, but on a hit it returns its existing cached list directly. The source sphere constructor produces tuple rows inside an outer tuple. Neither fact proves current list contents, native leaf types, callback absence or storage passivity after all intervening work.

The original helper iterates `zip(source_positions, stored_positions)`. It first charges the point, then checks row lengths and exact source-to-binary32 conversion/equality. Only afterward does it test all three source leaves for exact float type. Stored leaf types are not established by that equality: equal numeric values can have different types, and a foreign equality method can participate. The native branch then forms its existing upper bound, consults the current maximum and repeated-maximum witness, and performs any required exact fold. Component-error updates remain per point.

Agent execution may contain additional service and cancellation callbacks. A source-driver authority result cannot be transferred to that path without its own source and lifetime proof.

## 2. What must stay passive, and for how long

For C067's fixed future-seed screen, authority must hold from every new inspection that relies on it through seed inclusion and retirement. Stable native coverage during this prefix is sufficient for the seed argument; a claim lasting the whole cold scan is stronger and requires evidence for the suffix too. After retirement, the original suffix still runs. No authority receipt is reused on a warm hit, retry or later occurrence merely because object identities match.

The minimum subjects include:

| Subject | Required fact | Current gap |
| --- | --- | --- |
| Traversal | The retained source point will occur in the actual zipped prefix; source and stored row objects and list length remain suitable | A prior equal-length check cannot prevent a later callback from shortening the stored list |
| Rows and leaves | Reads, lengths, iteration, comparisons and arithmetic cannot invoke foreign behavior while omissions depend on the seed | Exact outer tuple/list types do not establish row or leaf types |
| Conversion and arithmetic | Actual `scene.float32`, struct operations, `math.nextafter`, `_Bounds`, Fraction access/arithmetic and their dependency state have their justified behavior | The certificate gate is not a complete geometry dispatch receipt |
| Work and guards | Same native work owner, native charge/guard/resource behavior, absent observer, full live 32,768-bit domain, supported native construction callback with no nested custom check | Public fields, dispatch and diagnostic dictionaries remain mutable |
| Inspection itself | Every lookup or query used by admission is already safe, bounded and correctly funded | A gate cannot assume the passive storage that it is trying to prove |
| Lifetime | Native counter changes remain allowed, while relevant foreign mutation, hooks or reentrancy cannot invalidate an outstanding claim | No current producer-to-reader epoch or enforceable borrow interval is supplied |

This is a dependency inventory, not a finite authenticated binding manifest. The exact manifest, its initialization and its changing native meter state need their own bounded design. Native operation/time checkpoints can move when real work is omitted or added. Foreign callbacks, observers and first exceptions must preserve their ordinary route and behavior; clearing a callback or turning an inspection exception into a benign rejection would change that behavior.

### The C057 dictionary witness still applies

`_certificate_term_native` inspects `function.__globals__.get(name, ...)` and builtin dictionaries for every captured `co_names` entry. The name `charge` belongs to `_tick`'s attribute access, but the gate also looks it up in the module dictionary. A colliding non-string key can run foreign equality during that optional lookup. Exact dictionary type and a saved `.get` alias do not remove that event. This remains a conditional source witness, not an executed recording failure.

A native dictionary-items traversal that checks each key's exact type before a keyed lookup could address this particular collision route. It still needs trusted finite iteration, a charge for each reached added step/check, native values where used, and storage lifetime. Native charge itself reads `counts.get(kind, 0)` and updates that dictionary, so the proof must allow its expected native mutations while excluding hostile keys and values. Checking the dictionary once without such lifetime authority is insufficient.

No circular claim is accepted: a mutable Python flag, a saved alias, a class identity or a newly named receipt cannot authenticate the code and state used to validate itself. C058's existing authority concern is preserved.

## 3. A sharper cost rejection for every entry seam

Freeze C067's nomination: the actual source row at zero-based index `s=133`, two downward `nextafter(a+b,0.0)` additions, strict `U < L`, unchanged source conversion and component errors, and a separately charged pending identity comparison. The lower bound is never returned as the radius.

Let `j < s` be the first original eligible native candidate seam at which an eager admission is attempted. The control and proposal have identical radius/floor/witness state at that seam. The eager schedule separately charges one unit for each of the three source and three stored leaf-type checks in every pair from `j` through `s`, inclusive. It establishes their relevant native facts before relying on the seed. Row types, row lengths, dispatch, dictionary safety, seed work and all other added work are additional.

At helper entry, the necessary leaf-check count for this schedule is

`T_entry(j) = 6*(s-j+1)`.

Give the schedule its most favorable placement: it begins after the current row's original three source-float tests have completed, and those exact checks need not be duplicated. Even granting this credit without charging the proof that the row itself is a native tuple,

`T_seam(j) = 6*(s-j+1) - 3 = 6*(s-j) + 3`.

Only rows `j` through `s-1` can lose exact folds. Each completed fold has three original decode and three original addition charges. Thus the gross ceiling is

`G(j) <= 6*(s-j)`.

Therefore `G(j)-T_seam(j) <= -3` for **every** `0 <= j < 133`. Before the current source checks, the corresponding deficit is at least six. At `j=133`, a visited/current seed provides no removable prefix benefit. An earlier alias of the seed shortens its useful prefix rather than increasing the ceiling.

| First seam | Pairs inspected through seed | Maximum gross saving | Added leaf checks after the three-check credit | Best residual before all other costs |
| --- | ---: | ---: | ---: | ---: |
| 0 | 134 | 798 | 801 | -3 |
| 64 | 70 | 414 | 417 | -3 |
| 132 | 2 | 6 | 9 | -3 |

The 804-at-entry and 801-at-first-seam figures are optimistic lower bounds for this declared admission schedule, not full implementation totals. Ordinary screens can only reduce its removable-fold opportunity. C067's fixed-bound fold-subset theorem does not make added seam decisions free.

This rejects the separately funded eager leaf-check family. It does **not** establish a universal minimum for all implementations, rule out legitimately retained producer facts, assign one unit to every Python instruction, or adopt a new composite accounting meaning. A fused proof, alias-aware retained fact or differently grouped semantic unit would be a different proposal with its own authority and complete funding obligations.

## 4. Complete funding boundary and all outcomes

For a completed, admissible request whose unchanged work is actually equal, let `B-K` be the actual number of removed completed exact folds, `S` the new candidate comparisons, `I` the pending seed-identity comparisons, `A` all other added admission/receipt/seed/state work, and `F` added restoration, replay or ordinary rescan work not already counted in those sums. Repeated optional events remain in their original `S`, `I` or `A` category; each concrete occurrence is counted once. Then

`saving = 6*(B-K) - S - I - A - F`.

Without that equality of retained work this is only an optimistic bound. An interrupted fold must be counted by its actual reached events, not six completed charges. None of `A` or `F` is assigned zero because an implementation is missing.

The [funding map](funding.json) identifies every category and continuation. [The proposal](PROPOSAL-068.md) defines prospective bounded unit bodies. It pays request-local preparation, current lookup/type/limit/coverage checks, issuance and consumption of receipts, every retained occurrence, seed reads/shape/domain/finite checks, three absolute values, two additions, two nextafter calls, comparisons, retirement and any fallback. No existing geometry tick is reassigned to new optional work. A bound formed from immutable values still has preparation and retention costs.

Rejected optional admission retains all completed added work and then runs the original dynamic path. An added charge refusal is a real failed request; fallback cannot erase it. A new optional inspection may not call a future foreign row or raise its exception before the original schedule. After an omission, falling back requires a proved reconstruction of the original pending state, including real cost; merely disabling the screen is insufficient. The selected eager design avoids that transition only under its unproved passive lifetime. A lazy replay design is not selected.

Warm hits, cache eviction, repeated cold calls and retries each keep their actual incidence. Neither 482 sphere vertices nor an aggregate numerical counter establishes `B`. C067's favorable abstract residual of 530 and adverse extra cost of 135 retain their limited meanings. No actual complete-request opportunity, savings, latency result or new original-recording success is measured here.

## 5. Proposed alternative and next decision

The narrow alternative is a reader-local, request-funded producer receipt that covers the actual source tuple and actual cached POSITION list across their real interval of use. It cannot be issued simply when the list is fetched at `_geometry_bounds`: that normally returns a list decoded much earlier. A proposed owner/epoch must either span those intervening stages or prove a new safe authority at the cold boundary without duplicating the losing scan.

The proposal keeps ordinary mutable list semantics, earlier bindings, foreign callers, source/error order, cache limits and the independent reader. It requires an explicit decision on any new mutation boundary or admission-unit definition. It neither authorizes borrowing a writer's certificate nor grants an uncharged trusted-host assumption.

[C069](NEXT-TASK.md) is therefore a finite source-level ownership design on the original source-artifact request path, beginning with the real compiler work object and following the actual decoded list through `_vertex_extrema`'s cache lookup. Its deliverable is a concrete authenticated, paid entry/lifetime mechanism or a source-bound rejection with the next alternative named. Repeating the same eager scan or renaming a gate does not advance that task. Instrumentation remains conditional on an authority-safe schedule and positive complete-request premise.

## 6. Evidence and preserved obligations

The [standalone derivation](derive_evidence.py) reads bound source bytes and ASTs and evaluates integer cost formulas. It imports no OntoKin module, invokes no product helper, generates no mesh and evaluates no trigonometric function. Its output enumerates all 133 candidate seams, verifies the source schedule and binds the actual call definitions. Independent reviewers examine authority, cost and producer provenance separately. [Validation](validation.json) records actual executions; review approval applies to the source record, not to the unimplemented receipt.

The unchanged documentation preservation/link checker is the integration gate. Candidate, actual merge and final-publication receipts name their own source identities and complete stable input inventories. Product suites are not run for this source-only change.

Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and 64 cursor updates. All 65 runtime files and every original test, fixture, horizon, frame rate, helper, equation, independent oracle, tolerance, contract, default and workflow remain unchanged. Historical recordings remain **24/28, failed**, with **P11/P16/P23/L03** unresolved; M1 rejected; C035 held including adverse timing. C057, complete reach acceptance and historical LFS migration remain open. The language, modeling, dynamics, purposeful movement and validated engine-delivery [goal](../../../GOAL.md) remains incomplete.
