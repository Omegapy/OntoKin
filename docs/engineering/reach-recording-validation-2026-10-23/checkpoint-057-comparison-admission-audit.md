# C057: comparison admission does not establish an atan funding mechanism

Date: October 27, 2026, America/Denver. Owner: `interactive-reach06-comparison-admission-audit-20261027-c057-9f3c`. Branch: `work/reach06-comparison-admission-20261027-c057-9f3c`. [Declared scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6456810009).

**Decision: transfer is unproved and stops here.** The accepted C030 comparison mechanism performs native eligibility inspections before its first admission charge and repeats them on later comparisons. Its source and derivation identify one comparison-admission charge per group, but do not supply a complete contract-supported funding map for all new, repeated and rejected work. A separate conditional source witness also prevents treating the entire precharge inspection as necessarily passive.

This completes the bounded audit selected by C056. It does not revoke or relabel historical C030 acceptance, establish an observed recording defect, or prove all atan optimizations impossible. No new atan schedule, runtime change, endpoint calculation or collector is selected. The [event/funding table](checkpoint-057-event-funding.json), [counter ledger](checkpoint-057-cost-ledger.json), [source bindings](checkpoint-057-source-binding.json), [reviews](checkpoint-057-reviews.json), [actual validation](checkpoint-057-validation.json) and [next scope](checkpoint-057-next-scope.json) separate those claims.

## 1. Exact sources and authority

The accepted comparison source is C030 commit `d2f0088c4f3c1f570630334804a5a8f78e0105ac`, tree `1f0b08f8846f443b8bc573fe0c9d5e1e3c319c47`. The current source and branch parent are final C056 commit `8287be55a21c28320aa11895cadd29c68ae18f90`, tree `274acc026f2e0d5dee3eb4a754790cc420a354a0`. Both were retrieved separately and matched to their remote Git blobs. Materialization is not execution.

| Input | Accepted C030 versus current C056 |
| --- | --- |
| `ontokin/reach_conformance.py` | Byte-identical, 206,759 bytes; blob `f91cdbc43fe7134c4b11c73bd43cd033bf9d16ea`. All comparison-source line references below apply to both. |
| `ontokin/reach_numeric.py` and `ontokin/construction.py` | Byte-identical. Their charge and construction-budget behavior has the same source at both revisions. |
| `budget-counting.md`, `ADOPTION.md` and `adoption.json` | Byte-identical. The adoption record explicitly includes the 8,368-byte budget file with SHA-256 `055b6167cbf67dc420c99dc24f3e08d449ae9d8d993250fbddfb48cabb4f4d04` among effective normative inputs. |
| Native-field derivation | Current source appends only the ten-line historical acceptance section after C030 line 176. Its mechanism and accounting prose are unchanged. The appended acceptance narrative is not substituted for the C030 derivation. |
| `ontokin/reach_reference.py` | Current source adds initialization and invocation of the separate product observer. `_Arithmetic.tick` now runs that captured observer after `check` and before the ordinary observer. The `exact`, atan and pi bodies are unchanged apart from shifted lines. This difference is retained; C035 remains held. |

The [adoption record](../../language-design/planar-reach-v0.1/ADOPTION.md) establishes the effective OK-LANG-006/0.1.0 authority while retaining historical draft labels. Its lines 25–33 require serialized execution, shared remaining work, interruption identity and explicit versioning of future semantic changes. The old draft heading in [budget-counting.md](../../language-design/planar-reach-v0.1/budget-counting.md) does not cancel that adoption.

Budget section 3, lines 98–110, preserves smaller request limits, charges new lookup/type/limit/claim checks and copied logical occurrences, and permits omission of real numerical work actually avoided. It does not say that every Python instruction is a separate semantic unit. Nor does it define all optional eligibility work as one free or prepaid group operation. Both distinctions matter.

## 2. Ordinary comparison and the proposed replacement point

The ordinary `_Bounds.compare` is at [reach_conformance.py](../../../ontokin/reach_conformance.py), lines 174–184. It first converts unsupported operand types through `value`, retaining those decode charges. For already-native Fractions it reads the four operand widths and runs the original operand guard. It then calls `tick("independent_exact_compare")`, runs prospective cross-product guards, and computes the comparison.

One semantic comparison therefore contains several native reads and guards around its charge. That existing grouping is visible in source. It does not automatically assign every added optimization check to that comparison, especially checks on paths that subsequently execute the complete original comparison anyway.

`flush` retains its earlier `independent_certificate_group_check` at line 2627, threshold and owner checks, quantity/extent selection, and then creates the comparison context at line 2636. The audit does not erase that prior charge. Neither the adopted budget text nor the native-field derivation assigns that already-existing group-check unit to all newly added context inspections, later proofs and rejected attempts.

The requirement calls at lines 2637–2650 keep both threshold admissions around the relation, with `equality_shortcut=False` and `compared=True` after comparison. The complete-inequality caller at lines 535–548 accepts only the expected context type and same arithmetic owner. These are retained surrounding obligations, not new funding for the helper.

## 3. Source-bound event, funding and fallback table

Here, an admission charge means the explicit call at line 3029. "No helper charge" does not mean that the preceding group operation or other request work never charged. It means this event has no additional tick in the named helper chain and no complete documented attribution to a supported composite unit.

| Event | Actual source work | Funding and continuation |
| --- | --- | --- |
| Native reference preparation | Module-level `_TERM_*` and `_FIELD_*` tuples retain classes, descriptors, functions, code/default/closure/global references, field readers and trace/profile queries (2702–2760, 2840–2852). | Preparation is performed when the module is loaded. Its existence is not a request-local payment or proof that later mutable dictionaries are passive. No product import was performed by C057. |
| Context creation | `create` runs the full field/term gate; `__init__` stores arithmetic, work owner, callback and two flags (2976–2985). | No helper-specific setup tick. False returns `None`; callers dynamically use ordinary comparison. An inspection exception propagates. |
| Hook and operand filter | Read `self.arithmetic`; call saved trace/profile queries; check original Fraction class and exact operand types (2993–3004). | No comparison-admission tick. Each explicit rejection starts `arithmetic.compare(actual, minimum)`. |
| Native access filter | Scan saved class access descriptors; read four private slots through saved native accessors (3005–3012). | No admission tick. Only `AttributeError` raised inside these slot reads is caught and sent to ordinary comparison. Other inspection exceptions are not generally caught. |
| Bounded field filter | Check four exact native integer types, positive denominators, four 2,048-bit limits and equality of the two current field pairs (3013–3017). | No admission tick. Unequal or unsupported pairs start ordinary comparison. The filter proves no accepted claim by itself. |
| Current native authority | Test previous validity, full field/term gate, same work owner and same external callback (2987–2991, 3020–3021). | No admission tick. False uses ordinary comparison; a raised inspection exception occurs before fallback. |
| Fresh fields and original first guard | Read both current Fractions again through `_certificate_fraction_fields`, reject missing/unequal pairs, compute four widths and call `arithmetic.bits` (3022–3027; field reader 2201–2209). | No admission tick. These fresh proof reads are additional work; the first operand guard is retained original work. A guard exception propagates. |
| First eligible pair | If not already admitted, call `arithmetic.tick("independent_certificate_compare_admission")` (3028–3029). | One explicit request charge when work exists. The call can fail; a reached failed attempt is not necessarily a successful counter increment. |
| Successful-charge recheck | Set `admitted=True`, repeat current native authority and freshly read both fields (3030–3033). | No second helper tick. Rejection starts a fresh ordinary comparison, including its guards and ordinary charge. It does not resume an already-entered original comparison frame. |
| Accepted equal result | Retain prospective cross-product guards and return integer zero (3034–3036). | First eligible pair replaces one ordinary comparison tick with one admission tick. Later eligible pairs repeat their filters, current checks, fields and both guard stages without another admission tick. Complete funding of this repeated proof work is unestablished. |

No new returned Fraction or certificate-field copy is made by this comparison helper. It creates temporary tuples and stores context references/flags; the two field-reader calls return current integer-field tuples. These occurrences are identified, but this audit does not invent a new logical-value charging rule for interpreter temporaries. The separate decode-copy mechanism is contextual only and was not selected for optimization or a second audit.

### What the full native gates inspect

The table's full-gate row expands into the following actual work; calling it one check would conceal its unresolved accounting.

- `_certificate_fields_native` (2855–2879) checks term/raw/key reader identities, two module-attribute identities, and each saved function's code, positional defaults, keyword-default object and entries, closure values, referenced globals and builtins. It then calls the term gate.
- `_certificate_term_native` (2762–2799) checks exact arithmetic type and field-reader identity; scans saved class-storage/method descriptors and module attributes; queries trace/profile state; scans saved function code/defaults/keyword entries/closures/global and builtin bindings; reads the arithmetic instance dictionary and rejects instance overrides.
- If work exists, lines 2800–2814 check its exact type, instance overrides, absent observer, exact full operand domain, integer nonnegative operation/time fields, float start time, and a native category dictionary with at most 512 entries whose keys and values have the expected types. This 512-entry diagnostic bound does not change the separate 256-entry numerical-cache cap.
- If an external callback exists, lines 2815–2828 require the exact native construction-budget bound method and owner, no instance method overrides or nested custom check, native state, and a five-entry positive native limit dictionary containing operation and elapsed limits. A `None` work owner or callback takes its stated earlier return.

Each scan includes the raw reads, membership/identity/type/limit tests, iteration and temporary structures shown in source. The code contains no additional charge in these gate functions. Original semantic accounting permits some composite operations, but no complete map funds this entire optional chain on every path.

## 4. What the counters establish, and what they do not

The following table counts only explicit successful comparison/admission increments for one local call, with a real native work object, already-native operands and otherwise successful original comparator. It excludes the earlier group-check tick and all unrelated work. It is not the complete semantic cost of the gate.

| Local path | Admission increments | Ordinary-comparison increments | Compared with one ordinary native comparison |
| --- | ---: | ---: | --- |
| A precharge condition rejects | 0 | 1 | Same explicit comparator count; extra inspections still occurred. |
| First eligible equal pair succeeds | 1 | 0 | One category replaces another; no local tick saving. |
| Later eligible equal pair succeeds | 0 | 0 | One original comparison tick omitted; repeated proof work still needs valid funding. |
| First admission returns, then recheck rejects and ordinary comparison completes | 1 | 1 | One extra successful unit for this local completed path. |
| Any charge or guard raises | Path-dependent | Path-dependent | Stop at the actual event. Do not infer completed-path counts. |

`_Bounds.tick` calls `_tick`; `_tick` does nothing when `work is None` (lines 46–49, 69–70). That source case cannot supply a general funding theorem for atan, whose `_Arithmetic` requires either work or a bounded check callback. No no-work exemption is proposed.

`ReachExecutionWork.charge` in [reach_numeric.py](../../../ontokin/reach_numeric.py), lines 71–94, captures the work observer, calls the external check, applies operation/time limits, increments the reach count/category, then runs the captured observer. Under successful gate prerequisites that observer is absent. The optional native [ConstructionBudget.tick](../../../ontokin/construction.py), lines 75–87, increments its own count before testing its operation bound. Its nested custom check must be absent for this admission. The construction and reach counters can therefore differ on refusal; they are not interchangeable evidence of successful work.

The inherited C030 census ceiling of 174 gross sites minus 24 group admissions equals 150 explicit operation units under complete eligibility. It covers both the separately identified decode and comparison transformations. It is historical opportunity accounting, not a newly established complete-cost proof or a per-request result of C057. No missing-check cost is assigned zero, no per-bytecode cost is invented, and no revised numerical lower bound is claimed.

## 5. Conditional native behavior and the passive-storage gap

The equality theorem is sound under its prerequisites: equal current native numerator/positive-denominator pairs represent the same rational value. Both original guard stages remain. Under a stable passive native environment, the first equal comparison reaches its budget check after the operand guard and before the prospective guard, matching the ordinary comparison's broad stages. The native checkpoint schedule is explicitly allowed to change by the derivation's lines 145–150. This is narrower than arbitrary callback and exception equivalence.

The gate is intended to reject foreign callbacks, observers, dispatch and mutated function state before omission. Its broad statement that precharge inspection is passive still needs proof. A native dictionary can contain a non-string key whose equality method runs during a lookup for a colliding string. Exact dictionary type alone does not exclude that event.

### A conditional helper-entry witness

Assume the comparison context was created normally and its operands are equal, bounded native Fractions. Let work and its charge remain native, with adequate remaining limits and no hooks, observers or external callback. Before this helper call, suppose the mutable module global dictionary receives a key `K` with the same hash as the attribute-only name `charge`. Its equality method raises an existing exception `E` only when compared with that string and otherwise returns false. No numerical endpoint or actual hash value is needed for this conditional construction.

The source mechanism is specific:

1. `_term_functions` includes `_tick` as its first function (2722). `_tick` uses the attribute `work.charge` (46–49); the module has no global definition or import named `charge`.
2. `_term_function_state` snapshots every `co_names` entry through `namespace.get`, including attribute names (2737–2744). The saved entry for global `charge` is absent in the original state.
3. The comparison's current-gate scan repeats `function.__globals__.get(name, ...)` at lines 2790–2792. Looking up `charge` can reach the colliding key and raise `E` before the admission tick and before ordinary fallback.
4. The ordinary native comparison dispatches `work.charge` as an attribute. It does not perform that module-global lookup for the attribute name. Under the stated benign remaining assumptions, it does not encounter this `E` at that event.

This is an unexecuted source witness at a specified helper entry. It establishes a missing passive-storage premise for a general transfer claim. It does not establish that an original full recording naturally reaches this state, report an observed failing request, or retroactively alter C030's development result. If a supported mutation boundary excludes this state, that boundary needs an explicit source/contract justification. It cannot be inferred from the native dictionary type.

Saved bootstrap aliases, context state and their lifetime also need a defined trust boundary. C057 does not expand into every potentially mutable Python object: the documented funding gap already stops transfer, and the concrete lookup above is enough to withhold an unconditional passive-gate proof. The authority reviewer contributed this witness; root incorporated and separately checked its source path. Independent review is not represented as independent discovery by every reviewer.

## 6. Transfer to the atan continuation

C056's R56 seam is inside current `_Arithmetic.exact`, after its original tick returns and before the dynamic `F(a)` and `F(b)` calls ([reach_reference.py](../../../ontokin/reach_reference.py), 126–145). Original atan/pi frames, arguments and later lookups remain pending (370–395). This is materially different from comparing already-native field pairs.

| Property | Transfer decision |
| --- | --- |
| Prove a result from fresh current native fields and retain required operand/prospective guards | Useful proof pattern. A new atan site must establish its own inputs, functions, owners and current authority. |
| Restrict omissions to native callback/observer conditions and recheck after a charge | Transferable obligations. The existing `_Bounds` gate does not authenticate `_Arithmetic`, its mutable `F` binding, conversions or pending callers. |
| One group admission pays all setup and every later or rejected gate | Unproved. No complete supported funding map was found. |
| Rejected admission resumes the original pending frame | Not supplied by C030. Its helper invokes an ordinary comparison afresh; it does not solve R56's saved-frame repayment problem. |
| A charge before native comparison can move ahead of pending atan conversions safely | Not established. The conversions can have the earlier exception, and their original unit U has already been consumed at the R56 seam. |
| Native dictionary and function identities make every precharge inspection passive | Unproved; the conditional dictionary witness identifies one concrete missing premise. |
| Historical C030 acceptance licenses this new route | Not transferable authority. Historical evidence retains its own source and scope. |

C056's accounting remains unchanged: conditional whole-pi factory opportunity 163 with lookup/remember retained; post-square work 114/34; at the actual post-U seam only 113/33 original future charge units remain. These are inherited conditional figures, not new endpoint or incidence measurements. U cannot fund both a new inspection and the pending arithmetic. C030 supplies no source-proved exception to that boundary.

## 7. Next bounded action and preserved state

The next useful action is an explicit, narrowly versioned accounting and authority decision proposal for this one comparison mechanism. It must state which semantic work a unit covers, how setup/repeated/rejected paths pay before relying on checks, what mutable-state boundary makes inspection passive, and which lower-budget and exception behaviors must be preserved. Each clause must be traced to an existing adopted rule or labeled a proposed change. Merely adding a composite-operation label or moving the charge is not a proof.

The [C058 scope](checkpoint-057-next-scope.json) authorizes preparing that proposal and its required evidence plan only. It does not adopt changed rules, modify existing accounting, select an atan implementation, or reclassify old results. Any actual semantic change requires a separate explicit versioned adoption with retained failures and independent review.

Startup reconciled explicit C056 release [6455995010](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6455995010), both STATUS records, 102 preexisting branches, 32 open PRs, current governance and CI. Main remains `2bb4588e121fcfe99b4d42c734b15b38362f3642`; no main integration lease was acquired. Empty CI is not passed CI. All 65 current remote runtime blobs and modes match held C035.

Original28 remains **24/28 historical**, with **P11, P16, P23 and L03 unresolved**. **C035 remains held, including adverse timing.** Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries, 64 cursor updates, original horizons/fps/helpers, fixtures, independent oracles, equations and tolerances. Complete regression and Python compatibility, R01–R12/Q01–Q22 and mandatory source/Agent/native/browser/visual/hostile/inherited roles, formal input closure and resulting-main verification remain pending. The full OntoKin goal remains incomplete.
