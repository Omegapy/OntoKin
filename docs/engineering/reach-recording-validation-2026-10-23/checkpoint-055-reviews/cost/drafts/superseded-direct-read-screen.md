# C055 independent cost and rejected-path review

Reviewer: `/root/c055_cost`. Source: final C054 commit `2aca5afb05a0320971ccaf9d9ce30904d120e249`, tree `7082ceb840e0ce4c2f30baccbdb527913e9fa2ca`. This review reads source only. It does not import OntoKin, execute a candidate, compute endpoint constants, replay numerical work, collect requests, or certify runtime compatibility.

## Findings

The available factory opportunity is 163 operations on the stable native128 path. Original key construction, lookup/domain synchronization, the warm-hit return and final `remember` remain part of the program. They provide no additional saving.

A deliberately explicit use-sensitive screen can still exhaust that opportunity. The concrete direct-read design below has a lower bound of 164 charged reads and predicates before defaults, globals, safe bootstrap, certificate access or fresh copies. This rejects that particular design. It is not a lower bound for every possible authority test, and it does not repeat C054's five-metadata-predicates-per-function argument.

Independently, eager charging before the screen can change original exception order. The source witness below rejects a precharge-first screen with a fresh-expression fallback even if its successful path were made cheaper. No complete safe admission or positive all-path bound is established. Numerical endpoint work therefore remains gated.

## 1. Factory accounting

`ontokin/reach_reference.py` lines 370–395 contain the series and pi factory. On a native positive call with the inherited first-stop candidates N5=28 and N239=8, each small-atan call has one square charge, four exact-operation charges per term, one final enclosure-addition charge and one grid charge. Its count is `4*N + 3`.

| Native factory component | Charges |
| --- | ---: |
| Small atan for 1/5, conditional on N=28 | 115 |
| Small atan for 1/239, conditional on N=8 | 35 |
| Multiplication by 16 | 5 |
| Multiplication by 4 | 5 |
| Final subtraction | 3 |
| Factory total | 163 |

Each nonpoint multiplication uses one scalar `point`, its own `tick`, two selected `exact` products and one `grid`. The final subtraction uses its own `tick`, two `exact` subtractions and the dyadic `_sum_enclosure` return, which adds no grid charge on this native path. The preserved lookup and final remember contribute one each, explaining the inherited 165 cold-call count.

This is structural operation accounting conditional on the native stop/branch assumptions already nominated by the handoff. It is not a new proof of the endpoint integers, strict first stops, prospective operand bounds or complete request behavior. No endpoint arithmetic was executed.

## 2. A concrete use-sensitive screen that is already too large

Consider a narrowly chosen native `ReachExecutionWork` route whose `external_check` is `None`. This intentionally excludes the ConstructionBudget route; supporting that route adds separate authority and callback obligations.

The design inspects only actually used callable state. For each of the 36 callable entries below, it performs four separately charged actions: read the currently used binding, compare that binding with its expected callable, read that function's `__code__`, compare that code with its expected code. Expected-reference retrieval and descriptor safety are optimistically not counted in this subtotal. Underlying Fraction delegates are read from the actual forward-wrapper closure cells, not from unused class attributes with similar names.

| Family | Count | Used entries |
| --- | ---: | --- |
| Arithmetic factory | 14 | `operand_limit.fget`, `_dyadic_denominator`, `tick`, `guard`, `exact`, `point`, `grid`, `_grid_domain`, `_sum_enclosure`, `interval`, `sub`, `_corner_domain`, `mul`, `_atan_small` |
| Interval construction | 2 | generated `Interval.__init__`, `Interval.__post_init__` |
| Fraction construction, descriptors and arithmetic | 18 | `Fraction.__new__`; numerator/denominator getters; four forward wrappers for addition/subtraction/multiplication/division; their four actual captured rational delegates; `_from_coprime_ints` underlying function; `__bool__`, `__eq__`, `_richcmp`, `__lt__`, `__gt__`, `__ge__` |
| Native shared charge path | 2 | `ReachExecutionWork.tick`, `ReachExecutionWork.charge` |

The subtotal is `36 * 4 = 144`.

The same declared design separately reads ten live state fields and applies one predicate to each. The order may put these before the callable screen to reject cheaply; the completed-pass subtotal is unchanged.

1. `arithmetic.bits`: exact native integer type.
2. `arithmetic.scale`: exact native integer type.
3. `arithmetic.work`: exact native ReachExecutionWork type.
4. `arithmetic.check`: exact native bound-method type.
5. `arithmetic._recording_after_tick`: `None`.
6. `arithmetic._recording_product_after_tick`: `None`.
7. `work._source_after_charge`: `None`.
8. `work.external_check`: `None`.
9. `work.operations`: exact native integer type.
10. `work.max_operations`: exact native integer type.

These ten current field reads plus ten separate predicates add 20. The completed screen therefore costs at least `144 + 20 = 164`; its local factory saving is at most `163 - 164 = -1` before everything omitted below.

This lower-bound schedule is intentionally not represented as a safe complete executable gate. A method-type predicate does not prove the check's owner/function; integer-type predicates do not establish bits=128, the correct scale, valid counters or remaining headroom. Those are additional checks. They have not been silently folded into the 164 subtotal.

### Why these entries are relevant

The 14 arithmetic methods are reached by the two small-atan calls, the two positive interval multiplications and final subtraction. The typed work and check fields supply the shared callback and operand domain. Both arithmetic observers are read before each callback; the work observer is captured before the external check. Current counters can have effects unless their native representation and storage are established.

Native Fraction forward wrappers call mutable captured delegate cells. Each delegate calls the currently resolved `_from_coprime_ints`; relational wrappers delegate to the current `_richcmp`; the constructor and guards read numeric properties. Merely checking a stable forward-wrapper object does not authenticate the code or captured function it uses.

### What this screen excludes or leaves additional

It does not screen `sincos`, caller target maps, active targets, finished-child observers, early parent publication, two-pass cache tags or a canonical-to-consumer corridor. Those are absent from the new factory boundary. `pi` is the modified entry boundary; preserved lookup/remember behavior does not automatically require adding their functions to this counterfactual factory subtotal. Their original binding/capture order must still be retained.

It does not impose generic defaults/kwdefaults/closure-reference predicates. In particular, no-argument defaults on arithmetic helpers cannot affect calls that supply all arguments. Fraction's default numerator is unused, whereas its default denominator is consumed by the many one-argument Fraction calls. Native `work.tick` invokes `charge()` with the actual `kind` and `amount` defaults, so those defaults matter. The generated frozen Interval initializer's used closure and all used globals/builtins, class descriptors, Fraction class/metaclass/MRO authority, number-ABC behavior, native storage, safe charged reads, clock/elapsed failure behavior, certificate storage, fresh copies and retained logical occurrences remain additional obligations.

Each captured Fraction delegate was counted once among the 36 callable entries. This review does not count its closure-cell read and identity test again as a separate four-delegate surcharge.

### Scope of rejection

The 164 floor rejects exactly this direct-read/function-identity/code-identity plus ten-state-predicate schedule. A different use-sensitive authority design could combine or omit checks if its source proof justifies that omission. The floor is not a claim that all valid designs require 36 function identities, 36 code identities, or this field inventory. There is no measured implementation cost or request prediction.

## 3. Precharge-first exception-order witness

The unchanged original evaluates `self.remember`, `self.sub`, the first `self.mul` and `_atan_small` call target, then evaluates `F(1,5)` before reaching the factory's first `exact.tick`.

Choose an otherwise passively readable state with an empty native cache, native key/domain methods, no observer hooks and a bounded check callback. The original lookup's first callback returns normally. A later call to the callback raises an existing exception object B. Let the current module binding `F` be a callable that raises a distinct existing exception object A when invoked for `F(1,5)`.

The original cold path raises A before its first post-lookup callback. A new gate that calls `self.tick()` to precharge its first authority inspection instead calls the callback first and raises B before inspecting or rejecting the changed F binding. Catching or translating B to continue would itself change the original callback's exception identity/behavior.

This is a conditional source witness, not an executed hostile request. It rejects that eager-precharge schedule. It does not establish that every design must precharge at that point, nor justify free preliminary checks. A different placement must prove both the accounting and the original order of callable capture, callbacks and failure. The authority reviewer has independently supplied a stronger normal-precharge-return/rejected-fallback capture witness; this report does not substitute for that review.

## 4. All-path cost and failure ledger

| Path | Required accounting and result |
| --- | --- |
| Original lookup returns a warm value | No new gate work; original return remains. |
| Original lookup/domain synchronization fails | No invented factory credit; preserve the actual prefix and exception. |
| All 36 callable and ten state checks complete | At least 164 new charges under the declared screen, before certificate/storage/copy work; at most -1 local saving. |
| A gate predicate rejects after a reached prefix | Every reached new read/check charge remains. A return to the original factory supplies no omitted-factory credit. Its behavior is not assumed unchanged after callbacks. |
| A precharge/callback/resource check fails | Record the actual attempted/reached prefix and error identity. Do not append unexecuted gate or factory work or apply a completed-cost formula. |
| A different unsupported precision/domain reaches a gate | Discriminator/rejection costs remain; no native128 factory credit. |
| Multiple cold calls in a request | Count each actually admitted replaced factory and every rejected prefix; do not multiply by target count or a hypothesized setup incidence. |

For completed matched executions the appropriate bookkeeping identity remains `saving = 163*J - A_new - Delta_remaining`. `J` counts actually replaced completed cold factories, `A_new` includes every new gate, precharge, certificate, copy and retained-occurrence charge, and `Delta_remaining` is the disjoint signed difference in all other work. A complete convergence proof is needed before setting that last term to zero. None is established here.

## 5. Evidence and limits

The main source has Git blob `0e98ba4c2ba0c49dbf9672ecb1c0f0fd50079dbb`, SHA-256 `db2fa3853e231e399ca2d48e5dea04455aeb0f80f11b4f42a478c34e0c717dc6`, 259,809 bytes. All fetched local source bytes were reconstructed and checked against their provider Git blobs. `source-binding.json` lists the named sources and attachment hashes.

Fraction dependency reasoning uses CPython v3.12.14 `Lib/fractions.py`, Git blob `e3a8bbcfb3ea5e016b218a69487983b97250433d`. This is source evidence for the selected callable inventory, not runtime observation or a CPython 3.11/3.13 compatibility result. No product source, fixture, oracle, tolerance, cap, workflow or repository branch was modified by this reviewer.

Original28 remains 24/28 historical; P11/P16/P23/L03 remain unresolved and C035 remains held including adverse timing. This review cannot repair the observed P23 producer-side refusal, which precedes the independent-reader entry. Whole-request savings and actual setup incidence remain unknown.
