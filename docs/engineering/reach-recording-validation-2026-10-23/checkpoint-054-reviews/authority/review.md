# C054 independent pi-certificate authority review

Reviewer: `/root/c054_authority`. Source: final C053 `6f6e16f2e26ac1885e5675a9d931ba385304e63c`, tree `2d6857bb63bf84dff0f27976fb6da29487a4f05c`. Owned review scope: [Issue 26 comment 6453812785](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6453812785). The inspected source identities and primary-source observation limits are in [input-binding.json](input-binding.json).

**T1 is NO-GO.** Its literal pi-only tag screen makes the proposed pi insertion passive, but does not make the route from insertion to the first pi consumer passive. The original route first performs a different parent-cache lookup, tagged `reference_pose`. An exact native resident tuple with that first tag passes T1 and can invoke a custom equality method in a later tuple component. That method can observe and alter the newly published pi value before its first use. This remains possible even if the value was independently authenticated and freshly copied at publication.

The counterexample rejects T1's claim of complete publication-to-use closure. It does not reject exact value certification generally. T2's linear exclusion of `pi`, `reference_pose`, and `sincos` repairs this particular parent-key route, but does not establish the remaining source-owner, charge, callback, storage, or lifetime premises. No exact pi endpoint constants, prospective-domain certificate, runnable gate, or complete positive cost are produced by this review.

## 1. Scope and evidence

The supplied [C054 scope](../../checkpoint-053-next-scope.json) requires cost and current-authority analysis before certificate generation. T1 keeps the complete original canonical calculation, all precision attempts and failures, both roundings, branch normalization, and closed joint-limit checks. Its optional publication starts only after a successful first128 calculation. It never computes a missing child pi and never uses parent pi to choose the canonical target.

For this authority counterexample, grant T1 every proposed numerical benefit: the certificate exactly equals the original native128 endpoints; the child's current value matches it; publication creates fresh native Fraction/Interval copies; original operand guards are proved; direct callable owners and fields are current; new precharges are safe; final admission follows the publication tick and domain synchronization; the parent has spare capacity; and the required later lookups genuinely miss. The source result still fails if the only admitted parent-key property is the literal four-predicate screen: exact tuple, nonempty tuple, exact native first string, and first string unequal to `pi`.

These grants isolate the defect. They are not completed proofs or zero-cost assumptions. The review does not assert that a complete current-function screen, safe precharge bootstrap, or certificate actually exists within the available budget. The separate cost review evaluates the selected schedules.

Executed work was source reading and file-hash metadata only. No OntoKin module, original or candidate request, numerical experiment, endpoint computation, collector, test, benchmark, archive driver, or hosted workflow was executed. Source files were read from the recovered immutable C053 snapshot and matched against its tree. The binding identifies selected inspected inputs; it is not a full-checkout or release-input-closure claim.

## 2. The original consumer order

The relevant source is [reach_reference.py](../../../../../ontokin/reach_reference.py):

1. `_canonical_targets(payload, arithmetic)`, lines 674–735, returns the original rounded target pair after success.
2. `_event`, lines 3495–3501, may store the pair in `self._targets`, assigns `active.targets`, and calls `_base_tip(action, active.targets)` before checking the residual.
3. `_base_tip`, lines 3730–3737, forms a key through `_PoseArithmetic._key` and calls `self.a.lookup(key)` before its first `sincos` call.
4. `_PoseArithmetic._key`, lines 837–838, constructs `("reference_pose", self.a.bits, self.a.operand_limit, operation, *values)`. For this call, `operation` is `base_tip`, followed by the lengths and target-coordinate tuples.
5. Native `_Arithmetic.lookup`, lines 358–368, ticks, synchronizes the operand domain, and calls `self.cache.get(key)`. Only a non-None hit is deleted and reinserted.
6. Native `sincos`, lines 612–621, performs its own `sincos`-tagged lookup. Only after a genuine nonzero miss does it call `pi`.

Therefore, the pi key is not the next cache key queried after early publication. T1's proof for equality against the first component `pi` does not establish safety against the first component `reference_pose`, or against `sincos`.

## 3. Exact source counterexample

Fix a successful native first128 canonical path. Let its target pair be the exact native float tuple `c = (first, second)`, with `first != 0`, and let `l` be its native lengths tuple. This is a conditional source path, not a claim that a named recorded request has been observed with these properties. Assume the original parent pi key, the actual base-tip key, and the first sine/cosine key are absent.

Before T1 begins, let the parent dictionary contain one resident key:

`r = ("reference_pose", 128, 32768, "base_tip", l, E)`.

The outer tuple is exact and native. Its first item is the exact native string `reference_pose`. Its associated value is harmless and native. The last component `E` is a custom object with these fixed behaviors:

- Its hash returns `hash(c)`. The returned native hash is stable.
- When compared for equality, it reads `parent.cache.get(("pi", 128, 32768))`.
- If that entry exists, it changes that Interval's `lo` and `hi` fields through `object.__setattr__` to fresh native `F(25, 8)` endpoints. A frozen dataclass interface does not prevent this explicit object-level write.
- It returns exactly `False`.

The resident key can be installed by an earlier permitted callback while the original target computation is active; that callback can retire before T1. Alternatively, this is simply a current dictionary state that T1's stated screen admits. No active callback, trace hook, profile hook, or modified native callable is needed during either tag scan or publication. Numerical certificate generation is not needed to describe `E`: `c` denotes the fixed target pair of the chosen source path.

Both complete T1 scans accept `r`. Its type is tuple, it is nonempty, its first component is a native string, and that string differs from `pi`. Native comparisons against the requested pi key stop at that first differing string, so T1 does not call `E.__eq__`. The parent has only one resident key and is below capacity. The final publication tick is inert in this witness. The final fresh admission passes, and `remember` appends an initially authentic, independently certified, freshly copied pi Interval. No replacement or eviction occurs.

After the original return and passive event assignments, `_base_tip` constructs:

`k = ("reference_pose", 128, 32768, "base_tip", l, c)`.

The two tuples have equal length and equal component hashes. Hence their complete native tuple hashes are equal. Their earlier components compare equal, and the last component of the stored resident key is `E`.

The reviewed [CPython 3.12.14 tuple source](https://github.com/python/cpython/blob/v3.12.14/Objects/tupleobject.c), `tuplehash` at lines 318–342, computes the hash from component hashes and tuple length. Its tuple equality path at lines 635–657 checks components from left to right. The reviewed [dictionary source](https://github.com/python/cpython/blob/v3.12.14/Objects/dictobject.c), generic lookup at lines 970–1008, compares a matching-hash resident key with the query in the orientation `PyObject_RichCompareBool(startkey, key, Py_EQ)`. Thus it reaches `E.__eq__(c)` with the resident component on the left.

In the original program, the pi entry is absent at this lookup. `E` makes no change and returns False. In T1, the early publication made pi present, so `E` changes the freshly published Interval and returns False. In both paths, the actual base-tip lookup still misses. The following nonzero sine/cosine call then reaches parent pi. The original cold path computes its native value, while T1's cache hit returns the altered value.

The effect changes only fields of the newly published Interval. It does not insert, remove, replace, or reorder any dictionary key or value. The resident key and table remain stable. The witness therefore does not depend on a dictionary iterator error, table-resize behavior, generic-lookup restart, eviction, finalizer, or observer-capture race. The internal pi query is passive against `r` because its first tag differs. Exact copied values at publication do not establish that those values stay unchanged through the later equality call.

The same history difference could be observed by a custom equality method without changing numerical values. The explicit Interval mutation shows why the missing premise also matters to numerical authority. No executed hostile request, measured residual difference, specific recording failure, or general impossibility is claimed.

## 4. Current authority and precharge graph

The required dependency graph has the following finite families. This list identifies what needs closure; it is not itself a safe executable screen.

| Family | Relevant source dependencies and current state |
| --- | --- |
| Parent arithmetic | Exact `_Arithmetic` class/MRO/storage; current parent `work`, `check`, `bits`, `scale`, `cache`, `_cache_operand_limit`, `_recording_after_tick`, `_recording_product_after_tick`; `tick`, `operand_limit`, `_sync_cache_operand_limit`, `lookup`, and `remember`. |
| Child value access | Safe current child cache and endpoint reads required by the selected authentication step. Exact value authentication and fresh copies do not inherently require checking the finished child's unused work/observer fields or reconstructing its earlier callback history. |
| Shared request work | Native `ReachExecutionWork.tick`, `charge`, and `resource`; `external_check`, operation/elapsed/operand limits, `operations`, `started`, `counts`, and `_source_after_charge`. Bound method owner and callable/code/default/global state matter independently. |
| External construction budget | Native `ConstructionBudget.tick` and `exceeded`; its nested `check`, `operations`, `limits`, `started`, and `time.monotonic`. A native outer bound method does not make its nested callback absent. |
| Charge storage | `ReachExecutionWork.charge` accesses `counts.get(kind)` and writes `counts[kind]`; `ConstructionBudget.tick` indexes the limits map. Exact dict type alone does not make arbitrary resident key equality or matched custom values passive. |
| Introspection and callable authority | Trusted raw storage access, native class/MRO/descriptor state, function code and the defaults/keyword defaults/closures/globals/builtins actually used. A generic metadata screen and a smaller used-state proof are different candidate schedules. |
| Certificate and new copies | Exact current child endpoint integer fields, fixed certificate representation/provenance, native Fraction normalization/storage and Interval construction/storage, copied/retained occurrences, and value stability through final admission. |
| Publication | Parent cache owner, current domain, occupancy, resident-key predicates, exact requested key, all precharges, the native remember tick/domain synchronization, and final admission before insertion. |
| Caller and first consumer | Current reference/pose/action/active/payload owners and target map; target-map insertion, old target-value retirement, `_PoseArithmetic._key`, `_base_tip`, `lookup`, `interval`, `point`, `guard`, `sincos`, and `pi`, including the relevant native cold-factory dependencies used for equivalence. |
| Runtime assumptions | No unclosed trace/profile hooks, dictionary watchers, concurrent mutation, or other observers of altered publication/lifetime history. The reviewed tuple/dict sources establish the stated hash/equality behavior only. |

The graph concerns state actually read by the selected original and replacement operations. It does not justify charging irrelevant finished-child metadata. A gate that retains the original fresh child and proves the current endpoint values may omit unused historical child fields after separately proving that they are irrelevant to the new access and lifetime.

The callback chronology is explicit. In [reach_reference.py](../../../../../ontokin/reach_reference.py) lines 110–117, arithmetic tick captures both arithmetic observers before calling `self.check`, then invokes the captured product observer followed by the captured general observer after normal return. In [reach_numeric.py](../../../../../ontokin/reach_numeric.py) lines 71–94, work charge captures `_source_after_charge` before `external_check`, performs the original resource and counter updates, and invokes that captured observer afterward. In [construction.py](../../../../../ontokin/construction.py) lines 75–88, the nested budget callback runs before construction work and elapsed checks. Original exceptions retain their object identity.

A final admission must follow every earlier precharge callback, the remember tick, and any domain-synchronization tick. Reading a currently empty observer slot while an earlier tick is still active does not cancel an observer already captured by that tick. The supported centered `_Guard.original` remains a separate real observer; its later placement does not supply retrospective authority for canonical setup.

Safe precharge is not supplied by a type test alone. The gate must identify which original shared charging operation runs, which callable and storage authority it relies on, what happens if that charge mutates its owners, and where each paid check reads fresh state. The current graph leaves those costs and sequencing obligations explicit.

## 5. Caller ownership cannot be inferred from the helper arguments

The original helper signature is only `_canonical_targets(payload, arithmetic)`. It has no reference, active action, target-map, or pose-owner argument, and `_Arithmetic` has no native back-reference to those caller objects. Yet the proposed publication occurs before `_event` accesses and writes those objects at lines 3496–3501.

The original target-map absence test occurred before canonical calculation. An intervening original callback can insert another value at the same key. The later assignment can therefore compare a custom resident key or replace a custom payload whose retirement is observable. Likewise, assigning `active.targets` can release an altered old value. Current arithmetic ownership does not certify either operation.

A narrower corridor could explicitly require current native reference, pose, action, active-action, and payload owners; a passive native target key; an empty native target map; `active.targets is None`; and native current storage/descriptor state. These would be additional checks with concrete argument access and costs. They are not properties already available for free inside the original helper. Passing an explicit context or moving the gate is a design change that needs its own frozen schedule.

## 6. What T2 repairs

T2 uses the same two-pass structure but rejects every first tag equal to any of `pi`, `reference_pose`, or `sincos`. For a literal linear sequence of comparisons, each admitted resident key reaches all three tag inequalities. The minimum predicate count is six per key per complete pass: tuple type, nonempty, first-string type, and three inequalities. Its two-pass floor is `6*(m_before + m_after)`, or `12*m` only when both passes have the same stable occupancy. At stable occupancy 14 this floor alone exceeds the 163-operation room. This is a bound for that literal screen, not a minimum for every possible membership-test implementation.

Under fixed native fields and no intervening mutation, T2 prevents the precise resident-tail collision above for the first base-tip, sine/cosine, and pi queries, because each query differs from every resident key at the first native string. It does not require recursively inspecting every tail merely to prove those three specific queries passive.

That local repair does not settle the target-map write, active-target retirement, payload/owner access, shared charging maps, observers, current function-state checks, fresh-copy costs, or later lifetime behavior. T2 is therefore unresolved as a complete feasible design. It is neither accepted nor disproved by the T1 counterexample.

The proposed D36 generic metadata inventory is also a distinct chosen schedule. Its accounting belongs to the independent cost review and the final frozen list. Counting generic empty/default/closure identity checks does not prove every safe used-state gate must execute them. This authority review supplies no universal 180-operation lower bound.

## 7. Continuation and preserved gates

The exact-value idea survives as an unproved source hypothesis. A principled narrower task is to analyze an exact native128 specialization at the existing cold `pi` miss boundary, after the original lookup and domain synchronization. That would avoid canonical-child transfer and early publication across the event/base-tip corridor, while retaining the original final `remember` placement. It still needs a fresh authority, callback, prospective-domain, storage, all-path cost, and independent numerical proof. It is a nomination only; no constants, implementation, collector, or replay is selected here.

Original28 remains historically 24/28, with P11, P16, P23, and L03 unresolved. C035 remains held, including adverse timing. The existing operation, elapsed, operand, cache, and cursor limits and all source/oracle/tolerance evidence remain unchanged. This review closes no regression, compatibility, destination, hostile-input, release, or resulting-main gate.
