# C093 candidate design: specialize fixed authority identity predicates

**Decision requested:** approve one bounded implementation candidate, preceded by an isolated predicate benchmark. This is a design, not an implementation or a claim that A08 will pass.

## Starting evidence and ownership

The C093 isolated repository is `/tmp/ontokin-c093-work-eb22vdm9/OntoKin`, at documentary commit `cddecad5db3a73d73bb042773476967b6bd1793a`, tree `9a44f1b873e376a4bbf4eb578b274321176be496`. Its product is the tested C092 `68898e9b73efd20b37842897cbdfb2f61d4801ca`. The C093 workspace receipt binds the completed C092 recovery and unchanged archive. All C092 paths remain read-only.

Reviewed starting files:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `ontokin/torque_runtime.py` | 82,439 | `16dee91922f4f7570d517bb787b836a099020d69db06a34ae9b101025d97e0c6` |
| `ontokin/torque_canonical_spin.py` | 23,446 | `79e8991b84164f42cc97ceb126078eada19e6c6da8b2e5e1c9c3d56cd2a5e62b` |
| `ontokin/execution_budget.py` | 28,326 | `b35a42726e47f64537f20355fc678c0ebbe46274ba58fbe7e3445591751064e5` |
| `ontokin/reach_numeric.py` | 40,616 | `70f47e092c892fc4909b00d1af75d33aea9145dd0313248bb76f7cd2578d31a9` |

The last two files are inspection inputs only. The implementation scope is **only `torque_canonical_spin.py` and `torque_runtime.py`**, plus a new C093 test file if needed. No existing test or adopted input changes. I authored part of the C092 runtime guard; the reader agent independently reviews this design and any implementation, and root reviews the concrete diff before safety runs.

## Why this candidate

The preserved exact C092 profile is a diagnostic, not an acceptance run. Its summary is 17,504 bytes, SHA-256 `db8147edfa52cebf329f336b0bdcecb8b7278f288d1c35e483948f67f898d4da`; its raw pstats file is 392,878 bytes, SHA-256 `a27158e700f507cab9a20df7454e237feda9f8378405f11ca5d8390087c6709e`. Both are below recovered `c092-evidence/c092-reviews/recording-durable/implementation/descriptor-probes-draft03-attempt03/`.

Within the 31.8966-second instrumented run, the private guard ran 130,091 times and accumulated 21.0449 seconds. `_functions_current` ran 132,699 times, accumulated 4.7748 seconds, and made 2,239,053 `all` calls, mostly from its separate keyword-dictionary loops. `_bindings_current` accumulated 3.5044 seconds. The source-watch scanner accumulated another 5.9947 seconds and stays unchanged in this candidate. These cumulative times overlap; they must not be added as independent savings.

Root's fresh C093 original A08 baseline also failed: 241,714 export operations, the unchanged 30,000-ms deadline, and no completed artifact. The original complete candidate02 comparator required about 452,617 operations. That suggests about 1.87 times the present throughput is needed, but the comparator's weaker guard cannot certify this implementation. The C093 baseline receipt is `/tmp/ontokin-c093-validation-r52zdoa4/baseline-a08-attempt01/RESULT.json`, 41,955 bytes, SHA-256 `6dc9c317b9fdfd0ce96fc88b6e93cdf446cc982e34c96e6998c9035860cf1308`.

The candidate replaces interpretation of fixed identity records through repeated `map`/`chain`/`attrgetter`/`all` objects with short, generated straight-line predicates. Every original operand is still read and compared at each existing admission. It caches executable shape and owning operands, **never a successful admission result**. A keyword-loop-only collapse is narrower but cannot honestly be expected to close this throughput gap. Even the proposed broader static specialization has no demonstrated speedup yet and may still be insufficient.

## Exact change scope

### 1. A bounded compiler in `torque_canonical_spin.py`

Add one internal compiler for a closed set of identity operations. Its inputs come only from the import-time function, namespace and descriptor receipts already constructed by `_authority_snapshot`, `_compiled_authority` and `bind_simulator_type`. No model, source text, elapsed time, caller-provided names, runtime cache values or numerical results enter the compiler.

The compiler emits only fixed templates and generated local identifiers such as `v0`; original objects are passed to a one-time factory as values. It must never interpolate `repr` or source text from an owned object. Supported operations are:

1. Read one of the three literal native function slots `__code__`, `__defaults__`, `__kwdefaults__`, and compare with `is`.
2. Read an original native keyword dictionary's length, iterate its native `dict.items` in order, and compare each key then value with `is`.
3. Test an absent key with the supplied captured native dictionary or mapping-proxy `__contains__` operation.
4. Read a present binding with the supplied captured native dictionary or mapping-proxy `get` operation and the original distinct missing sentinel; compare the result with `is`.

Use individual `if ...: return False` statements, not one recursively nested expression. Bound each generated predicate to a fixed maximum of 4,096 primitive comparisons and a fixed maximum generated-text size, proposed 512 KiB. If the static receipt exceeds either limit or has a shape outside these templates, retain the **exact current generic predicate** for that receipt. This is an optimization fallback, not a new source-domain rejection. Compile errors in an eligible template are implementation defects and must not be disguised as an accepted result.

Retain the existing raw owning records and original vectors in their existing positions. Append a generated-predicate receipt to the compiled representation; do not replace strong ownership with bare integer IDs. The raw first five authority fields and their function/default/global/class objects remain strongly retained.

### 2. Specialize function receipts

`_compile_functions` adds an optional generated predicate; `_functions_current` admits and invokes it when present, otherwise executes the existing generic body.

The generated order is exactly the existing order: all original functions in record order, each code/default/keyword-default slot in that order, followed by keyword dictionaries in record order. Within a dictionary, length is checked first, then each key and value in the original iteration order. Do not flatten all dictionaries before checking the first one. Do not substitute value equality, hashing, `dict ==`, tuple equality over foreign values, or a content digest for identity.

Illustrative emitted code, with all symbols captured from the owning factory:

```python
def predicate():
    if function0.__code__ is not code0:
        return False
    if function0.__defaults__ is not defaults0:
        return False
    if function0.__kwdefaults__ is not keywords0:
        return False
    # Remaining functions' same three checks follow here.
    if native_len(keywords0) != original_length0:
        return False
    iterator0 = native_iter(native_dict_items(keywords0))
    pair0 = native_next(iterator0)
    if pair0[0] is not original_key0:
        return False
    if pair0[1] is not original_value0:
        return False
    # Remaining pairs and dictionaries follow in original order.
    return True
```

The pair is the native tuple already produced by `dict.items`; accessing its members cannot invoke the key's or value's methods. The generated code does not read a later pair after an earlier mismatch. A zero-length dictionary still receives its original length check.

### 3. Specialize binding receipts, retaining their two different orders

`_compile_bindings` adds an optional generated binding predicate; `_bindings_current` admits and invokes it or runs its unchanged generic fallback. Its ordinary helper path keeps **all absent-key checks before all present-binding checks**, preserving existing short circuit order. The original passed native `getter` and `contains` callables remain the operations used. Dictionary and mapping-proxy receipts must not be conflated.

The private runtime entry has a different existing order: present bindings first, then absent shadows. Its separate generated entry predicate preserves that order. In particular, a planted `_MISSING` value cannot conceal an unexpected key: absence continues to use native membership tests. The present fallback remains a distinct privately owned sentinel.

Illustrative binding statements:

```python
if native_contains(absent_owner0, absent_name0):
    return False
if native_get(present_owner0, present_name0, missing) is not expected0:
    return False
```

Keep `_classes_current`, runtime MRO/base/type checks, raw class descriptor resolution, subclass resolution, instance shadow refusal, full arithmetic/module/Fraction admission, `_PointScope`, operand watches and the cache adapter unchanged. Specializing a descriptor **comparison** must never move its call after an instance attribute lookup.

### 4. Preserve the private entry's three failure groups

Add three optional generated predicates to `_CANONICAL_POINT_ENTRY`: function slots, keyword contents, and present-then-absent bindings. The request-private `guard` retains its three distinct checks and original error construction, then invokes the captured original `admit_simulator_after_entry` and original context body exactly as before. Each generated predicate is admitted immediately before its own dispatch. If specialization is unavailable, the existing private entry body remains the fallback.

The first request guard still executes before inspecting mutable source/work fields. The second guard still executes after the original zero-charge constructor callback. Public `_context`, `_guard_context`, `_advance_orientation`, ledger guard installation and all callback positions remain unchanged.

## Generated executable admission: no new unchecked callable

A generated predicate is a native `FunctionType` with no defaults or keyword defaults; factory dependencies are captured as private closure values. Its receipt strongly retains the function, original code, defaults, keyword defaults, closure, globals, builtins and original owning records. Those private cells and immutable receipt tuples remain within the already declared private-owner convention, with no new caller-controlled authority.

Before **every** generated dispatch, compare its current `__code__`, `__defaults__` and `__kwdefaults__` with the retained originals using native identity reads. A changed function body must be refused before executing any replacement body. Do not rely only on the callable object's identity. At the private runtime entry these three checks must be inline and use the bootstrap's captured native primitives; an unadmitted helper cannot establish its own authority. Elsewhere, the sealing helper belongs to the normal point authority catalog and is admitted before its use.

The compiler must reject generated code containing global/name/import resolution or mutation instructions. Inspect the generated function's actual instruction stream, not only its source string: no `LOAD_GLOBAL`, `LOAD_NAME`, `IMPORT_NAME`, `IMPORT_FROM`, `STORE_GLOBAL`, `STORE_NAME` or `DELETE_GLOBAL`/`DELETE_NAME` in the predicate. The template must not emit nested executable code. Native functions needed by the predicate are captured in private closure cells, so changes to its globals dictionary cannot become executable authority. The code-object identity check catches any replacement that adds such instructions.

Normal helper compiler/admission functions and their module/global/builtin dependencies enter `_authority_snapshot` just like the existing functions. Do not add a special exemption for mutable compiler aliases. Keep original static receipts alive so object-ID recycling is irrelevant. Do not use `ctypes`, private object offsets, dictionary version tags, pointer casts, dynamic bytecode patching or interpreter caches.

## Required invariants

- Every original ledger callback and clock read occurs at the same site and frequency; `SharedExecutionBudget.tick` and `ReachExecutionWork.charge` are untouched.
- Every existing ownership admission still occurs. Only interpretation of its fixed record changes; no guard success survives a callback.
- Native function mutable slots, ordered keyword dictionary contents, relevant global/builtin values and explicit absences remain freshly observed.
- Raw runtime descriptor and MRO checks still precede any instance lookup; supported subclass behavior and native method shadow refusals are unchanged.
- Original source watches and detached numeric operand watches remain on their current implementations. There is no request-specific code generation or new source-size refusal.
- `_PointScope` still admits the full arithmetic authority, module contents, Fraction slots and original-plus-detached inputs at its existing boundaries.
- Original callback exceptions retain identity and precedence. Original counters, clock allowance, rollback, transaction ownership, cache capacity/provenance and refusal categories remain unchanged.
- Precision stages, first-certifying selection, all arithmetic/error formulas and work/resource ceilings remain exact.
- The 24 amendment files, 399 original inputs, 27 C091 overlays, 346 original tests and nine protected predecessor modules stay exact. Adapt the preserved immutable checker only into a new C093 evidence output.

## Interpreter assumptions and verification sequence

The candidate uses standard Python `compile`/`exec`, native identity operations and public native container APIs. It relies on the same proved native FunctionType read-only slots and immutable owning references as C092. It introduces no private CPython layout or new read-only-slot assumption. The original 28-check probes across 3.11/3.12/3.13 need repetition only if implementation changes those assumptions. Run small generated-predicate equivalence/admission checks on those interpreters because compiler behavior is new.

After independent design approval, perform one isolated benchmark of the original predicates versus the proposed compiler using the actual fixed receipt shapes and unchanged original objects. Preserve source hashes, original and emitted code, interpreter/platform, iteration counts, timing windows and results. Do not run a scene, alter caps, or call this acceptance evidence. Require matching boolean/refusal results and zero foreign execution for changed generated code/defaults/keyword defaults, changed original function metadata, changed keyword contents, present binding replacement and absent-key planting. Also check the size fallback against the original generic behavior. A slower predicate is not an improvement merely because compilation succeeded.

Only then apply the reviewed candidate to the two allowed modules. Root reviews the diff. Run the unchanged 29 focused tests, 20 original callback tests and 31 independent attacks, plus the small new generated-executable/fallback controls. Root owns the sole final uninstrumented original A08 attempt under 1,000,000 operations/30,000 ms. An actual complete committed artifact and the required independent supplied-byte validation are necessary; throughput extrapolation and a longer diagnostic run cannot substitute.

If original A08 still fails, retain that exact result and stop this bounded performance attempt. The profile does not justify promising that static specialization alone will remove enough cost, and unchanged source-watch scanning remains a substantial floor.
