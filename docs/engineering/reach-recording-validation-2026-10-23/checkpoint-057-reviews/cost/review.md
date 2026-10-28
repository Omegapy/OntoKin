# C057 independent cost review

Reviewer: `/root/package_and_cost_review`. Scope: the existing `_CertificateFieldComparisons.compare` mechanism, its two native gates, its ordinary comparator, and the bound accounting text. This is source inspection and file-hash verification only. No product code was imported or executed.

## Decision

**Funding transfer is unproved.** The source provides one explicit comparison-admission charge for the first eligible equal pair of a normally maintained group context. It executes substantial new inspection before that charge, on rejected paths that never reach that charge, and on later successful proofs that do not charge it again. The bound contract and derivation do not identify a semantic-operation grouping or another charge assignment covering those distinct paths. This is a narrow accounting gap in the proposed transfer argument. It does not retroactively reject the recorded C030 acceptance, invent a per-Python-operation unit, establish an implementation defect by execution, or prove that all optimization is impossible.

The source also supplies useful site-specific behavior: ordinary comparison has precharge operand guards and postcharge prospective guards, the optional route requires small already decoded native fields, and the route excludes foreign callbacks and work observers before an omission. Those conditions do not by themselves authenticate or fund inspection inside atan's pending `F(a)` / `F(b)` corridor.

## Source identities and differences

The separate local inputs were checked against their root-retrieved immutable Git tree entries. All fourteen file/revision pairs match the recorded Git blob and byte count. `source-binding.json` records byte lengths, SHA-256, Git blob and mode for each pair.

| Input | Accepted C030 versus current C056 |
| --- | --- |
| `ontokin/reach_conformance.py` | Identical complete file, 206,759 bytes, Git blob `f91cdbc43fe7134c4b11c73bd43cd033bf9d16ea`. All comparison source ranges below therefore identify both revisions. |
| `ontokin/reach_numeric.py` | Identical. |
| `ontokin/construction.py` | Identical. |
| `budget-counting.md` | Identical. |
| `ADOPTION.md` | Identical. |
| `reach-certificate-native-fields.md` | Current file appends the historical acceptance section at lines 178–186. The original operational/accounting text through line 176 is unchanged. |
| `ontokin/reach_reference.py` | Current source adds the separate `_recording_product_after_tick` field and its captured invocation before the ordinary observer. This is relevant to the atan contrast and is not part of the unchanged comparison implementation. |

Accepted C030 is commit `d2f0088c4f3c1f570630334804a5a8f78e0105ac`, tree `1f0b08f8846f443b8bc573fe0c9d5e1e3c319c47`. Current C056 is commit `8287be55a21c28320aa11895cadd29c68ae18f90`, tree `274acc026f2e0d5dee3eb4a754790cc420a354a0`. The appended current acceptance paragraph is not substituted for the earlier derivation.

## What the counting text actually supports

The accounting document names semantic operations, not Python bytecodes, as the source-work unit. Section 3, lines 103–110, permits genuine omitted numerical work while requiring new lookup, type/limit/claim checks, output occurrences and copied logical values to remain charged. It forbids stale authority and removed cancellation checkpoints. Lines 100–101 preserve the meaning of smaller budgets. The frozen draft label is read with the separate adoption record; it is not a reason to discard the adopted obligations.

The independently retrieved `adoption.json` is the same 56,183-byte Git blob `61547fa798ffb0ab06cfaba165dce63dc003ec03` at both source revisions. It explicitly lists `budget-counting.md` among `effective_normative_inputs` and freezes its 8,368 bytes and SHA-256 `055b6167cbf67dc420c99dc24f3e08d449ae9d8d993250fbddfb48cabb4f4d04`, exactly matching both local files. Its `draft_status_policy` states that the frozen draft labels are historical and that this record with `ADOPTION.md` establishes the adopted 0.1.0 authority. The local copy is `adoption.json`; this is an additional identity check, not an execution of an archived validator.

The original `_Bounds.compare`, lines 174–184, is an actual example of semantic grouping: optional input decodes, four operand-width guards, one `independent_exact_compare` tick, two prospective cross-product guards, then `(a > b) - (a < b)`. Multiple Python reads/operators occur around one comparator tick. This does **not** authorize counting every individual Python instruction as a new unit, and it does **not** define the newly added native gate as an extension of that already existing unit.

The derivation, lines 86–91, explicitly describes a first eligible comparison admission and repeated current-field proofs without another group admission. Lines 139–143 give the old conditional combined screen: 78 duplicate decodes plus 96 equal comparisons across 12 groups, less two admissions per group, produces 150 net charged operations. Lines 145–150 acknowledge a changed native checkpoint schedule and require remaining work and admissions to use shared work. None of those passages defines the raw inspection's semantic grouping or maps its rejected prefixes to funding. Its 150 figure is a conditional accounting ceiling under the recorded model, not proof that all performed inspection has a complete contract mapping.

## Event and funding table

Source ranges in this table refer to `ontokin/reach_conformance.py` unless another file is named. “No helper charge” means no explicit helper `tick` or `charge` at that event. It does not mean free work, and does not mean no earlier caller charge ever occurred.

| Event | Actual performed work and guards | Explicit charge and exact continuation |
| --- | --- | --- |
| Caller entry, 2624–2636 | `flush` charges a group check, reads thresholds and current quantities/extents, then creates a comparison context. | The preexisting `independent_certificate_group_check` is at 2627. No bound document assigns that unit to all new context/per-comparison work. It cannot silently be spent twice or extended by inference. |
| Context creation, 2977–2985 | Run full `_certificate_fields_native`; if it succeeds, allocate context, retain arithmetic/work/external references and set `valid=True`, `admitted=False`. | No helper charge. Failed gate returns `None`; callers at 2641–2642 use ordinary comparison. No receipt of a completed comparison is retained. |
| Field gate, 2855–2879 | Check three helper identities; inspect two module attributes; inspect saved function code/defaults/keyword contents/closure contents/referenced globals and builtins; then call the term gate. | No helper charge. Any false predicate returns false. Unexpected exceptions are not generically caught. |
| Term gate, 2762–2828 | Check exact arithmetic class and field reader; scan saved class descriptors and module fields; query tracing/profiling; scan saved function state; read native arithmetic dictionary and reject method shadows; inspect owner, observer, full operand domain, numeric state and diagnostic counts; inspect allowed callback and construction-budget state. | No helper charge. Counts inspection is bounded at 512 entries; that is an inspection bound, not a numerical-cache bound or funding allowance. Owner `None` and callback `None` are separate early true returns. |
| Per-call hook/type/descriptor filter, 2993–3007 | Read context arithmetic; query saved trace/profile functions; test Fraction class and exact operand types; scan saved Fraction access descriptors. | No helper charge. Every rejection dynamically calls `arithmetic.compare(actual, minimum)` from the beginning. |
| Raw slot read/filter, 3008–3017 | Read four native slots; test four exact integer types, positive denominators, four 2,048-bit caps and pair equality. Construct local field tuples for comparison. | No helper charge. Slot `AttributeError` is specifically caught and falls back. Other exceptions are not generically suppressed. Unsupported or unequal fields fall back. |
| Current context, 2987–2991 and 3020–3021 | Check valid flag; repeat the complete field/term gates; check work-owner and external-callback identity; update valid flag. | No helper charge. False invokes ordinary comparison. A failed current check makes the normal context invalid for later current checks. |
| Fresh public fields, 3022–3026 and 2201–2209 | Read both current field pairs again through the original reader; each reader checks exact Fraction type, native integer fields, positive denominator and bit caps. Compare current pairs and compute four bit lengths. | No helper charge. Missing or unequal fields fall back. These tuples retain references to native integers; the comparison helper does not create a replacement Fraction or an output projection. |
| Original first guard, 3027–3028 | Execute `arithmetic.bits(an, ad, bn, bd)`, then inspect `admitted`. | `bits` at 123–127 calls `guard_bits`, then the global maximum check; neither creates a work increment. A guard error propagates before optional admission. These guards are retained original comparator obligations. |
| First eligible admission, 3029 | Call `arithmetic.tick("independent_certificate_compare_admission")`. | With work present, `_Bounds.tick` → `_tick` → `work.charge`, one explicit unit. With no work, `_tick` is a no-op. A thrown callback/resource/observer error is not caught here, and `admitted=True` has not yet executed. |
| Successful admission bookkeeping and recheck, 3030–3033 | Set admitted true; repeat complete current/native gates and both fresh field reads; compare against precharge pairs. | No additional helper charge. Failed recheck dynamically invokes ordinary comparison from its beginning; the completed admission unit remains consumed. The flag is already true even when that fallback occurs. |
| Successful equality tail, 3035–3036 | Execute original prospective guards using the previously computed width sums, then return integer zero. | No helper charge. First eligible normal path has one admission instead of one exact-comparison tick. Each later eligible equal call repeats its fresh checks and both guard stages but skips 3029–3033 once admitted. |
| Ordinary fallback, 174–184 | Resolve ordinary comparator dynamically; perform any required decodes; read current fields and first guards; tick; read prospective fields and guards again; execute the actual comparisons. | A normally completed native-Fraction fallback retains one `independent_exact_compare` tick. Foreign operands may require separate `value` decodes, each with its own tick at 130. This is a fresh comparator call, not resumption inside an already active original comparator frame. |

The field gate's function-state collections and term gate's class/global/function snapshot tuples are themselves inputs to the inspection. Enumerating their traversals is not a proof that their provenance, current authority or full lifetime is secure. The authority reviewer owns that separate question. Neither this cost table nor earlier test acceptance grants those predicates free execution.

## Branch accounting without a new unit definition

For a normal unchanged helper context and native Fraction inputs, the explicit local tick schedule is:

| Path | Comparison-admission tick | Original exact-comparison tick |
| --- | ---: | ---: |
| Creation rejects; ordinary comparator completes | 0 | 1 |
| Any per-call filter/current/field reject before admission; comparator completes | 0 | 1 |
| First eligible equal proof completes | 1 | 0 |
| Later eligible equal proof completes | 0 | 0 |
| Admission completes, postcharge recheck rejects, ordinary comparator completes | 1 | 1 |
| Admission attempt fails | Attempted; successful reach increment depends on failure location | 0 |

Counts are local to the named comparison categories and exclude the already existing caller group tick, optional decodes, and all unrelated surrounding work. They are not a complete semantic cost for the inspection. External mutation of `admitted` or helper state would require separate authority analysis; this table does not certify arbitrary tampered helper objects.

The table assumes a native work object and normally completed ticks when it reports successful increments. If `_Bounds.work` is `None`, the term gate can accept at 2798–2799 but `_tick` at 47–49 does nothing. A source-level admission call then establishes no reach or shared-work increment. This helper mode cannot justify funding an atan route: `_Arithmetic.__init__`, current `reach_reference.py:72–76`, requires either shared work or a bounded check callback.

Conditionally, if `E` native equal comparisons in a group all omit their original tick and exactly one admission succeeds, the observed local category difference is `E - 1`. A postadmission fallback supplies no omitted-comparison credit for that call. All precharge declines still perform some added inspection and then retain the ordinary comparator. The contract mapping for those added checks remains missing even though their explicit optional admission count is zero.

No numerical lower bound for the complete gate follows from source predicate counts. The 512 diagnostic-entry limit is not permission to charge zero for that scan, but it is also not evidence that the contract charges exactly 512 semantic units. Both an invented per-Python-operation count and an invented one-unit whole-gate grouping would overstate the evidence.

## Charge failures and the R56 contrast

`ReachExecutionWork.charge`, `reach_numeric.py:71–94`, captures its observer, invokes the external callback, checks operation and elapsed limits, increments the reach operation/category counters and then invokes the captured observer. A callback or resource refusal can occur before the reach increment. The native comparison gate rejects a nonempty work observer and foreign callback, but that is a prerequisite that must itself hold under the gate's real authority assumptions.

The admitted native construction callback has its own sequence in `construction.py:75–87`: optional nested check, construction counter increment, then construction operation/elapsed checks. Its native gate requires the nested check to be absent. A construction resource failure can therefore advance the construction counter without advancing the reach counter. These counters must not be conflated.

The comparison site starts with already decoded exact fields. Its retained first guard precedes the admission, as it precedes the ordinary comparator tick. It performs a fresh comparator on fallback; it does not displace an already-paid pending arithmetic frame. By contrast, current `_Arithmetic.exact`, `reach_reference.py:126–145`, charges first, then performs pending dynamic `F(a)`, `F(b)`, guards and operator lookup. R56 moves into that suspended frame after U and would need to authenticate the pending operations without hiding their first failure.

A copied C030 pattern would not prove native/passive authority before the pending conversions, supply funding for every new and rejected check, or repair the additional V/W failures from C056. Its lack of a foreign callback on the admitted route is a useful condition to prove elsewhere, not a property supplied to atan by calling an existing gate.

The C056 boundaries remain unchanged: 163 is an inherited conditional whole-pi opportunity; after U the original future charge count is 113/33 while numerical work still pending is 114/34; a fully resumed rejected R56 prefix uses two extra successful units; failed attempted charges need not increment reach. No endpoints, incidence, whole-request saving or new schedule is established here.

## Review limits and next decision

The precise unresolved question is which existing semantic unit, if any, covers each new lookup/type/limit/claim check on creation, every early rejection, first proof, repeated proof and postadmission fallback, with a funding position compatible with interruption. The currently bound contract and derivation do not answer it. A further record may establish an existing interpretation from authoritative evidence; a changed unit or exception contract would require a separate explicit versioned decision. This audit makes neither change.

Stop transfer to atan on this evidence. Preserve C030's historical acceptance and current source unchanged, and preserve C035's hold and the four unresolved original recordings. Documentation/metadata execution and immutable publication are root's later tasks, not claims established by this review.
