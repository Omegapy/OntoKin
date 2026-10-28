# C058: an explicit comparison accounting and authority proposal

Proposal identity: **OK-PROP-COMPARE-058/0.1.0**. Status: **UNADOPTED; activation and implementation remain blocked**. Date: October 28, 2026, America/Denver. Owner: `interactive-reach06-accounting-authority-20261028-c058-7f2a`. [Declared scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6474322587).

## 1. Decision offered for review

C058 specifies one conditional accounting model, **M1**, for the existing comparison-admission mechanism. M1 charges each reached bounded inspection, every repeated proof and rejected attempt, and the dynamic preparation that supports them. It keeps the existing first-admission event and ordinary fallback distinct. Its passive-entry and lifetime requirements are explicit and unproved by the current source. This document does not adopt M1 or claim that a safe implementation exists.

**Recommend HOLD.** M1 makes the costs explicit but cannot produce positive comparison-only semantic-operation savings under its own proposed units. Its full native gate alone visits at least 115 class/module binding claims, each priced at one M1 operation. An ordinary native comparison retains its existing one-operation unit. The authority needed to enter and charge those inspections without introducing foreign behavior also remains unestablished. Neither result selects an atan gate.

This is a new, reviewable decision proposal. It is not a retrospective invoice for C030, a new recording result, or a revision of adopted authority. Historical C030 acceptance, C057's audit and every failed or held result retain their identities. The [matrix](checkpoint-058-semantic-matrix.json) specifies unit bodies, source-event coverage, failure continuations and authority. The [evidence plan](checkpoint-058-evidence-plan.json) separates work done here from evidence required later. Exact source and proposed-text identities are bound separately in [source binding](checkpoint-058-source-binding.json) and the [proposal identity manifest](checkpoint-058-proposal-identities.json).

## 2. Existing authority and exact scope

The source parent is final C057 `3b82b5bd74495850e08cf8b4f51daca0342f9882`, tree `37e4a53d6bb6a052bd2a53e74b73d720633b467e`. Historical accepted C030 is `d2f0088c4f3c1f570630334804a5a8f78e0105ac`. C057 established that their comparison source and adopted accounting inputs are identical. C058 separately retrieves and binds the named sources; acquiring a complete file does not imply auditing every function in it.

The effective authority is [OK-LANG-006/0.1.0](../../language-design/planar-reach-v0.1/ADOPTION.md). Its [adoption record](../../language-design/planar-reach-v0.1/adoption.json) includes [budget-counting.md](../../language-design/planar-reach-v0.1/budget-counting.md), [numeric-admission.md](../../language-design/planar-reach-v0.1/numeric-admission.md) and [numeric-counter-units.md](../../language-design/planar-reach-v0.1/numeric-counter-units.md). Their historical draft headings do not withdraw that adoption.

| Clause | Status | Authority or proposed effect |
| --- | --- | --- |
| R01: consume remaining shared request work; retain lowered limits and identify the exhausted unit/bound | Retained | Budget section 3; numerical admission sections 1 and 8; ADOPTION implementation obligations |
| R02: account for new lookups, type/limit/claim checks and copied logical occurrences; omit only work actually avoided | Retained | Budget section 3; numerical counter clarification |
| R03: keep current claims, source identity, guards, cancellation and output accounting | Retained | Budget section 3; ADOPTION; native-field derivation |
| R04: native checkpoint schedules may differ; foreign callbacks, observers and dispatch retain ordinary behavior and original exceptions | Retained, with its original limited scope | [Native-field derivation](../reach-certificate-native-fields.md), native environment and accounting sections |
| R05: admission refusal is a failed request; actual exceptions and failures remain recorded | Retained | Native-field derivation and adopted numerical admission |
| R06: require an explicit versioned decision, exact old/new identities and independent review for semantic changes | Retained | ADOPTION final paragraph; AGENTS preservation rules |
| P01: the M1 unit catalogue and its bounded composites | Proposed semantic definition | Defines new accounting granularity; not inferred from the existing ordinary-comparison unit |
| P02: request-funded, group-local dynamic preparation with no cross-group amortization | Proposed setup regime | Replaces reliance on uncharged import-time preparation for this candidate; no new budget allowance |
| P03: complete passive storage, provenance and lifetime conditions | Proposed eligibility premises; proof absent | Stronger than the current checks and not an existing restriction on supported ordinary behavior |
| P04: explicit event-by-event payment and rejection conventions | Proposed accounting schedule plus retained failure obligations | Adds real native checkpoints; does not authorize new foreign exceptions |
| P05: complete implementation/interpreter identity and evidence gates | Proposed candidate acceptance conditions | Supplementary to every retained release requirement |

Only `_CertificateFieldComparisons`, its preparation/gate chain, its existing caller seam and ordinary comparator are in scope. The separate decode transformation is read only where it shares source definitions. It is not repriced or changed. The current reference's separate product-observer addition remains distinct from accepted C030 behavior. No runtime, existing budget, ADOPTION, fixture, oracle, tolerance, workflow, shared STATUS/navigation or historical evidence is edited.

## 3. M1 unit definition and funding

### 3.1 What one proposed unit means

Each reached added M1 operation costs **one** shared semantic operation immediately before its bounded body. Its successful charge authorizes only that occurrence. A later occurrence, including an identical repeated check or a rejected proof, receives its own charge. Unreached short-circuit work is not charged as though executed. M1 selects individual precharges; it does not select a reservation, refund, pooled allowance or speculative debit scheme. A is the existing charge event itself. O retains its original execution and charge positions: an ordinary operand guard or decode may already have executed when its later comparison charge refuses.

These are proposed semantic operations, not Python bytecodes. A binding claim deliberately groups one native named lookup with one identity comparison. The exact body is stated so that no scan, nested entry traversal or copy can be hidden inside it. A native ordinary comparison remains its existing composite operation. The coexistence of those units is an explicit proposed choice, not a claim that the adopted text uniquely determines M1.

| Unit | Precisely covered body | Multiplicity |
| --- | --- | --- |
| B: binding claim | One lookup of one named class/module/instance/global/builtin binding in already justified passive storage, followed by one identity or declared presence/absence test; fixed native access to that namespace is included | One per actual lookup or membership/absence claim; global and builtin lookups are separate; repeat on every scan |
| R: raw read | One native field, slot, sequence entry or context-state read without a value predicate | One per actual read not already inside a named B or G body |
| T: scalar/shape test | One exact-type, identity, bounded native scalar/string value equality, sign, scalar bound or container-length predicate on already available native values | One per predicate, including keyword-name equality; exact native types and manifest bounds are prerequisites; a conjunction is several tests |
| Q: current equality claim | The fixed comparison of the two current native integer field pairs, at most two integer equalities, with source short-circuit order | One per fresh attempted pair claim; the fixed two-field grouping is explicitly proposed |
| N: native query | One pinned trace/profile query or one optional native bit-length query | One per reached query; original guard widths belong to G instead |
| I: traversal step | One native iterator creation or one advance, including an exhausted advance when reached | Each creation/advance separately; no entry validation or copy is included |
| C: bounded record creation | Allocate one empty, bounded proof/context/manifest record of its declared shape | One per actual record; entries and flags are W work |
| W: record occurrence | Store or copy one bounded reference, native scalar or flag into one declared proof/context/manifest slot | One per actual written occurrence; repeated copies count again |
| D: deduplication entry | One bounded native lookup and conditional insertion for one incoming exact-string or original native-function identity key in a preparation-only uniqueness table | One per input key, including duplicates; the conditional table insertion is included, while the empty table and later output copies use C/W |
| G: retained guard stage on a successful-proof attempt | Perform one original comparison guard stage, with its original native width reads/width sums and guard invocation; either four operand widths or two prospective widths | One per reached stage on the proof route; ordinary fallback uses its original comparison composite instead |
| A: first admission | The existing `independent_certificate_compare_admission` charge event itself | Once when reached while unadmitted; it is not also a payment for preceding inspections |
| O: retained original operation | The existing group, decode, comparison, threshold or caller operation under its existing accounting and guard order | Existing source schedule; no new M1 charge wrapped around the same original occurrence |

R/T/N/I/C/W/D also cover manifest preparation. A function header is decomposed into its actual R/B/T subjects. Keyword-default and closure entries have their own R/T/I occurrences. No function-header unit absorbs every entry. Source-created tuples and dictionaries have a C occurrence and their actual W occurrences, including both early field-pair tuples and every reached empty-dictionary fallback in `(function.__kwdefaults__ or {})`. D includes its one conditional uniqueness-table insertion, so that insertion is not charged again as W. A later tuple of the unique entries has its own C/W occurrences. Fixed iterator-internal cursor/pair bookkeeping is inside the declared I body; an explicitly materialized retained tuple/dictionary remains C/W. This distinction does not assign a separate unit to every interpreter temporary or treat such temporaries as materialized source values. Source-value, Agent JSON, retained-record and GLB-entry regimes remain separate and unchanged. A future implementation must also apply those regimes whenever it actually creates their logical values.

Each source occurrence has one owner in this map. A read included in B is not also R. Width reads included in G are not also N. Two physically repeated reads are two occurrences, even if they inspect the same object. Ordinary comparison guards are inside O when ordinary comparison runs; a prior failed optional proof's G occurrence is separate work and is not refunded. The native charge primitive retains its existing administrative implementation; M1 does not recursively charge every instruction of the meter. Authentication of that meter and additional candidate instrumentation remain explicit requirements, not administrative exemptions.

### 3.2 Payer, preparation, incidence and bounds

The payer is the **existing request's remaining shared work context**, including its native construction callback when applicable. There is no second 100,000-operation allowance. M1 does not activate with `work=None`, a foreign meter or an unauthenticated route. That is an eligibility rule for this candidate, not a change to the supported ordinary comparison.

P02 selects the following setup regime. Every dynamic capture, validation, deduplication, allocation and copy needed only for this comparison proof is performed and precharged inside the owning request, separately for each attempted group context, before its result is used. Its exact seam is **after** the original E01 group-check tick, threshold/member checks and quantity/extent selection, **immediately before** the E02 context-create call at `reach_conformance.py` line 2636. Those original earlier failures therefore precede funded preparation. The proposed order begins E01, funded E00, E02; E00 is the inherited source event label, not its new chronological position. Setup that returns no context still consumes its reached units. The lifetime ends when that group ends or its context is invalidated. There is no cross-group or cross-request amortization and no later successful pair pays for earlier work.

Current `_TERM_*` and `_FIELD_*` snapshots are built during module loading. **They are not funded candidate receipts.** M1 does not charge a later request retroactively for those past events. A future M1 implementation would have to place all dynamic proof-specific preparation inside its funded request boundary and account for its actual execution. Leaving the old pre-request builders in service while billing a later copy would not meet P02. Fixed expected program identities may be inputs to the provenance proof; dynamically capturing a mutable value does not make it the expected authority. C058 neither moves those builders nor selects a runtime layout.

The complete subject manifest must be fixed by the exact implementation, interpreter and standard-library identities before any later activation. It enumerates all class/module bindings, functions, code/default/closure subjects, global and builtin names, storage records and record layouts. Its finite lengths determine the finite sums. Current diagnostic-category iteration is bounded at 512 entries and construction limits at exactly five; these do not change the 256-entry numerical-cache limit. Every reached iterator transition and visited entry still has its own charge.

Before traversing a mutable container, its trusted native access, type and declared length bound must be established at paid R/T occurrences under the passive-entry premise. Growth, stale shape or identity changes decline the optional proof before an unbounded traversal. A manifest may not merely assert an unmeasured cross-version bound. Exact function/default/closure/name cardinalities and storage bounds remain required evidence, not filled-in zeroes. Fixed static binding counts in section 6 supply a lower bound only.

## 4. Event order, rejection and failure

After placing funded preparation at the explicit E01-to-E02 seam, M1 preserves the named C057 comparison-stage order and inserts the listed precharges immediately before their added bodies. It does not move a guard, call a pending conversion early, or pay retrospectively. Event IDs in the table are source labels; the proposed chronological prefix is E01, funded E00, E02. The [machine-readable matrix](checkpoint-058-semantic-matrix.json) covers every E00–E11 event and G1–G4 gate expansion.

| Event | Candidate payment | Continuation |
| --- | --- | --- |
| E00: reference preparation | At the E01-to-E02 seam, all dynamic R/T/B/N/I/C/W/D occurrences under P02 before their bodies; current import-time snapshots supply no candidate credit | Refusal stops the request after earlier original E01 work; no partially prepared object authorizes a proof |
| E01: original group entry | Retained O, including the real group-check charge | Original surrounding threshold/member work remains |
| E02: full setup gate and context | Every reached full-gate occurrence, followed by C and actual W context slots | False returns no context; later comparisons take ordinary dispatch; completed setup costs remain |
| E03–E05: context/hook/type/descriptor/slot/bounded-pair filter | Actual R/N/B/T/I and Q occurrences in source order, plus C/W for the two early field-pair tuples when reached | A declared false condition starts ordinary comparison; no accepted equality follows from this filter alone |
| E06: current authority | Full repeated B/R/T/N/I/C/W, including reached empty-dictionary fallback creation and owner/context reads/writes | False starts ordinary comparison; all reached costs remain |
| E07: fresh fields and first original guard | New field R/T/N/I/C/W, including each field reader's optional 2,048-bit query, then fresh Q and one separate G operand stage | Missing/unequal fields start ordinary comparison; guard exception propagates |
| E08: first admission | A, then W for the admitted-state write only after A returns | A failure stops; admitted is not written; failure of the later W also stops |
| E09: postcharge recheck | Repeat current authority and fresh field work; each reached occurrence pays again | False starts ordinary comparison afresh, retaining A and all completed optional work |
| E10: prospective guard and equal result | One G prospective stage; return the proved integer zero | Guard failure propagates; no stale previous equality authorizes the result |
| E11: ordinary fallback | Original O decode/compare chain, including its own guards and charge | Exactly one fresh dynamic ordinary call from this rejection edge; no saved-frame claim |

The full source allows only the specified `AttributeError` catch around the four early native slot reads. M1 retains that catch at that location. It does not turn arbitrary inspection exceptions into rejection. If an optional inspection can introduce a new foreign exception before ordinary dispatch, the passive-entry/routing obligation has failed; propagating that exception would not make the candidate equivalent. No such path is certified here.

The charge event is not interchangeable with its counter increment. `ReachExecutionWork.charge` captures its observer, invokes the external check, checks operation/time bounds, increments reach operations/category, then invokes the captured observer. Native `ConstructionBudget.tick` increments its own operations before checking refusal. A failed attempt can therefore have different construction and reach counts. C058 preserves those orders and original exception objects/effects; it does not normalize counts or invent successful increments for refused bodies.

For an added unit whose charge refuses, the unit body is not performed and the request fails at that actual charge. An ordinary retry cannot erase refusal. If charge succeeds and the unit body raises, the consumed charge remains and the actual exception follows the explicitly permitted source rule. A boolean rejection consumes completed optional work and then pays for the fresh ordinary comparison. Postcharge rejection is thus an extra-cost path. It does not resume an original comparison frame and cannot repay the pending atan expression.

### Lower limits and exception identity

The original 100,000-operation, 30,000-ms, 32,768-bit, 256-cache-entry and 64-cursor-update limits remain. Lower requested operation/time bounds remain real bounds. Extra native work can exhaust them earlier under the derivation's native checkpoint allowance; a proposal cannot promise identical successful requests at every lower limit after adding charged work. No budget is reset, raised, refunded or shared with a fictitious allowance.

Only the original full 32,768-bit work domain permits the existing omission. Lowered, widened, foreign or changed operand domains decline it. The 2,048-bit field filter and possible 4,096-bit cross products do not replace either original guard stage. Cancellation remains cancellation; resource exhaustion keeps its actual resource identity; neither is a successful decline. No original callback/resource exception is caught, translated or reconstructed by this proposal.

Native checkpoint flexibility does not waive original non-resource diagnostic precedence or foreign behavior. The ordinary route must preserve dynamic decoding/comparison, callbacks and its first exception before any optional work can introduce a competing foreign event. A future implementation must prove this entry distinction, including the cost and behavior of any dispatcher. The current gate does not supply that proof.

## 5. Passive authority and lifetime

P03 is a **proposed eligibility premise with missing implementation evidence**. It is not a declaration that all currently supported mutation becomes unsupported. Outside a proven candidate domain, ordinary behavior must remain available with its original dynamic dispatch and exception behavior. If a safe, funded route cannot make that distinction, M1 stays inactive.

A complete provenance argument must identify the actual trust root for code, access primitives, the meter and expected identities. It must terminate outside the mutable objects being checked. A saved alias, tuple, function identity, import-time observation or caller-supplied flag cannot certify itself. Any runtime work establishing or checking that provenance is priced by the same map and must itself have an already justified safe entry; an infinite chain of self-checks is not an implementation.

The proposed passive interval starts **before the first optional lookup or candidate charge** and extends through each use, the original guard, admission and any postcharge proof or fallback decision. A native charge boundary is not automatically a trusted lifetime boundary. The proof must account for the native construction callback, reference lifetime, reentrancy and possible mutation between observations and uses. Project worker serialization alone does not prove that a Python process cannot experience hooks, interleaving, asynchronous activity or object finalization.

The storage inventory includes function globals/builtins/keyword defaults, closure contents, class/module dictionaries, arithmetic/work/callback-owner dictionaries, diagnostic categories, construction limits, context fields and saved reference stores. Exact built-in dictionary type is insufficient. For every actual lookup, the proof must establish native key behavior, finite shape, access primitive identity and stability through use. The proposed lookup domain requires exact-string-only keys, identity/shape bounds and exclusion of outside mutation for the relevant interval. Preparation-only uniqueness tables instead permit the explicitly bounded exact-string/native-function keys of D. These are stronger proposed eligibility premises, not facts established by current source; an alternative premise would require its own reviewed version.

The interval must permit the **meter's required native writes**. A successful reach charge increments `operations` and its category value; native construction tick increments its own `operations`, including the defined refusal case. These transitions are allowed only under their pinned native implementation and actual counter order. They do not authorize owner/limit/code/callback replacement or outside writes. Context flags and proof-record writes are separately paid W operations at their declared stages; their own reads must account for those transitions.

In particular, charging during a live `counts.items()` traversal may change category values. That is compatible only with a proved native iteration rule and the predicate being checked; it cannot be treated as an immutable snapshot of exact counts. **No category key insertion or deletion may occur while that iterator is live.** Any required category registration must complete at a separately paid, bounded safe point before iterator creation, with the resulting shape checked before traversal. If admission adds a category, it must occur after that scan ends and before a new scan's shape check. The proposal does not select a registration implementation or category naming scheme. A concrete finite schedule meeting these obligations, including its initialization costs and behavior at the 512-entry eligibility bound, remains an activation blocker. A checker that forbids all meter mutation would exclude its own precharges; a checker that ignores topology changes would be unsound.

In particular, `_tick` uses `work.charge` as an attribute. Its `co_names` also contains `charge`, and the old gate looks that name up in function globals/builtins. A colliding non-string dictionary key can run equality at the extra global lookup. M1 prices both namespace lookups if they are performed, including attribute-only names. Paying for them does not prove them passive. Silently removing attribute names is not selected by this proposal and would still require exact dependency evidence for the remaining lookups.

The C057 witness remains conditional and unexecuted. No natural original-recording reachability or observed recording failure is asserted. The provenance obligation is broader than that one witness: an attacker-controlled saved getter or mutated context can affect the authentication path itself. A key scan also needs paid, trusted, finite iteration and a protected lifetime; it cannot first perform the hostile lookup it purports to make safe.

The same owners and fresh fields remain necessary at every comparison. A context retains owner identities and paid preparation, never an accepted prior claim. No observer or callback is installed, cleared or suppressed to create eligibility. Trusted native construction tick with no nested custom check is the only non-null callback allowed by the existing native domain. Any new support boundary, sandbox or mutation restriction would require its own explicit versioned decision; none is adopted here.

## 6. What M1 costs, and why it is not an operation-saving candidate

The following are syntax-derived binding occurrences in the unchanged source. Their calculation parses the source text without importing the product or constructing its runtime tables.

| Table | Binding occurrences |
| --- | ---: |
| `_Bounds` class fields | 17 |
| Native work class fields | 16 |
| Construction budget class fields | 11 |
| Fraction class fields | 25 |
| ABCMeta class fields | 7 |
| Rational, Real, Complex and Number class fields | 6 each, 24 total |
| `_TERM_CLASS_FIELDS` total | 100 |
| `_TERM_GLOBALS` | 13 |
| `_FIELD_GLOBALS` | 2 |
| Successful full gate's named class/module bindings | **115** |
| Early Fraction-access filter | **9** |

Under M1, each of those visited binding claims costs one B. Therefore a successful full gate costs **at least 115 proposed units**, before function/default/closure/namespace scans, hook queries, owners, dictionaries, iteration and copies. Context creation performs one full gate; every potentially accepted equality performs another; the first admitted equality performs a further postcharge recheck. The nine early Fraction-access bindings are additional work on each successful comparison filter. This is a strict lower bound under M1, not 115 observed ticks, a full implementation total or a latency measurement.

For an otherwise completed native group, let `S` be all paid optional preparation/setup, `P_i` all reached optional inspection/record/guard work for pair attempt `i`, `A` the successful first-admission increments, and `E` the number of ordinary one-unit comparisons actually omitted. Retain the same original surrounding work and ordinary fallbacks in the reference total `C_original`. Then the candidate accounting is

`C_M1 - C_original = S + sum(P_i) + A - E`.

Every accepted pair has a completed full gate, so `P_i >= 115` under M1, even ignoring its early filter, fields and guards. Rejected attempts have nonnegative paid work and omit no ordinary comparison. Thus

`C_M1 - C_original >= S + 114*E + A`.

Whenever at least one comparison is omitted, M1 is strictly more expensive in shared semantic operations. Setup or rejected attempts can also make a group more expensive when no comparison is omitted. A disabled route that performs no optional work remains the ordinary route. The formula applies to completed native paths only; a refusal must use its actual stopping trace rather than completed-path algebra.

This conclusion is deliberately limited. It rejects **M1 as a comparison-only operation-saving design**. It does not prove every possible versioned semantic model or atan optimization impossible. A coarser composite would be a different proposed meaning requiring an explicit decision and evidence, not an undisclosed correction to this cost table. Elapsed cost and whole-request feasibility are unmeasured.

C030's historical 150-unit combined decode/comparison ceiling and actual development results remain tied to their executed source and schedule. C057's local admission/ordinary increment pairs remain 0/1, 1/0, 0/0 and 1/1 under their stated successful-path assumptions. None is relabeled as an M1 measurement. The inherited conditional atan opportunities of 163, 114/34 and 113/33 remain unchanged and do not finance this proposal; the already-paid unit U cannot be spent twice.

## 7. Exact identities, independent evidence and decision boundary

The old-input record binds separately acquired accepted C030 and current C057 source/authority bytes, the actual C057 parent/tree, current main and both STATUS records. The proposal identity manifest hashes the exact new proposal, matrix, evidence plan, handoff and next-scope text without a self-referential hash. The containing immutable Git commit supplies the final identity of that manifest. There is **no new adopted budget, ADOPTION or runtime identity**: those files remain byte-identical parent entries. New authoritative identities can only be created by a later explicit adoption.

Independent review must check unit coverage and non-overlap, all failure edges, the 115-binding lower bound, retained authority, setup payer/incidence, storage/lifetime assumptions, the distinction between conditional specification and implementation, and impact on existing results. Review of this document is not a proof that a runtime establishes P03. The [evidence plan](checkpoint-058-evidence-plan.json) names separate future source/host/interpreter identities, hostile and lower-limit probes, original/candidate traces, full cost/incidence and retained release evidence. Those probes are specified, not executed by C058.

C058 performs only exact source acquisition, text/static metadata analysis, independent document review and actual documentation/metadata validation. No product import, endpoint calculation, numerical replay, original/candidate request, collector, runtime test, benchmark, archived-driver execution, hosted dispatch or main integration is selected. The validation and publication records state their actual results separately.

The proposal is complete as a conditional decision artifact when its clauses and matrix are independently reviewed and its publication is verified. Adoption and activation remain blocked by: no independently grounded passive entry/routing mechanism; no complete interpreter-bound manifest/finite storage proof; no concrete accounted initialization implementation; no required runtime failure/equivalence evidence; and M1's proved unfavorable operation-count consequence. A review pass closes document defects only.

The next bounded action is a separate explicit versioned decision on this exact proposal: reject M1 for the optimization objective, or commission a specifically identified revision with a stated reason and fresh review. Any such revision must name its changed unit granularity or authority premise. It must not automatically proceed to atan, implement an unfunded gate, or silently change supported mutations. [The next-scope record](checkpoint-058-next-scope.json) preserves that boundary.

Original recordings remain **24/28 historical**. **P11, P16, P23 and L03 remain unresolved. C035 remains held, including adverse timing.** Original horizons, fps/helpers, fixtures, independent oracles, equations, tolerances and all outstanding regression, compatibility, rate/native/browser/visual, Agent delivery, formal input-closure and R01–R12/Q01–Q22 release obligations remain. The full OntoKin goal is incomplete.
