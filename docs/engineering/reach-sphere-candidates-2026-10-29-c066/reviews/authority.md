# C066 independent authority and exception-order review

## Scope and result

This is a source-only review of a fixed vertex-index shortlist for the cold native-sphere exact L1-radius calculation. No OntoKin module was imported, no sphere was generated, and no product request, test, numerical replay or benchmark was run.

The reviewed runtime files are exact C065 blobs at commit `b7357df3bc296cc1cd728bdf52dbeaf2697da85b`. They were read from the recovered C064 source and independently matched against the uploaded C065 source index. The initial `/tmp/c066-source/` transport copies were used for navigation only.

**Finding: shape and current native dispatch alone do not authorize a constructor-dependent shortlist.** The current cold helper receives no sphere recipe or producer receipt. A proposed implementation needs a funded connection between the actual immutable source coordinates and the candidate theorem. It also needs a restricted, currently native arithmetic/work domain or an untouched fallback for foreign callbacks and dispatch. No such complete schedule is established by the existing helper.

This is a missing premise for the proposed optimization. It is not a proof that every shortlist, actual-coordinate certificate or restricted-domain implementation is impossible.

## Source bindings

| File | Git blob |
| --- | --- |
| `ontokin/geometry.py` | `c060ffb3b88023aa1521ef74777377a3ab47df7c` |
| `ontokin/reach_conformance.py` | `f91cdbc43fe7134c4b11c73bd43cd033bf9d16ea` |
| `ontokin/scene.py` | `e35942ed86fbe48be720ace7c0a5639ad4a63c59` |
| `ontokin/reach_numeric.py` | `c552b085106a02b612a24a4884d8096f9733ee40` |
| `ontokin/construction.py` | `0b1a6b3d1ab4bed103d9e3477dc32b935759aad1` |
| `docs/language-design/planar-reach-v0.1/budget-counting.md` | `d2113ebd1f44bbf78ba484a5f971d62741dab715` |
| `docs/engineering/reach-certificate-native-fields.md` | `7d08e965e48cc05752459ff69457f8c8aa2efbe4` |
| `docs/engineering/reach-recording-validation-2026-10-23/checkpoint-057-comparison-admission-audit.md` | `aed6d218b9a893e9a186e6f3cc171931137e2929` |

These are content checks, not an independent attestation of GitHub's current ref or the complete portable C065 packet.

## 1. What current source actually establishes

`geometry.py:47–75` exposes `sphere_mesh(radius, segments=32, rings=16)`. The defaults describe the ordinary primitive recipe, but the function also accepts other segment/ring counts. `joint_marker` calls it with 12 segments and 6 rings. A mesh name of `sphere`, tuple storage, or native float leaves does not select the ordinary 32-by-16 recipe by itself.

`scene.py:349–373` captures exact native primitive inputs. The sphere key contains the kind and the typed radius; a float radius is keyed by its binary64 bytes. `scene.py:376–416` separates writer/independent namespaces, calls the selected constructor, and rechecks recipe identity across lookup and cache insertion callbacks. These are useful existing guarantees. They do not create a candidate-set receipt or bind the constructor's function/default/global/math state into the mesh cache key.

`reach_conformance.py:728–796` caches completed extrema by source-position identity and operand cap. Its warm path rechecks every current supplied position in bounded blocks, and its cold publication rechecks native source/stored rows and current binary32 conversions. This is an extrema proof created only after the cold calculation succeeds. It is not prior authority for shortening that same cold calculation.

`reach_conformance.py:799–847` receives only `source_positions`, `stored_positions` and `work`. It serves primitive, helper and surface meshes through the common call at line 934. It cannot infer a sphere recipe merely from its formal parameters.

A tuple of exact tuples containing exact built-in floats has stable coordinate values under ordinary Python callbacks. The review does not allege that such floats or tuples can be mutated in place. A variable can be rebound, mutable stored rows can be replaced, and dispatch or work state can change at callbacks; those are separate authority questions. If actual immutable coordinate values themselves support a theorem, their stability can be used without claiming producer history that was not recorded.

## 2. Original cold order

For each paired source/stored vertex, the source does the following in order:

1. Fetch the paired rows through `zip` and run `independent_geometry_point`.
2. Check row lengths and each actual source-to-binary32 conversion; a mismatch raises `OKE-E-GEOMETRY`, while an unrepresentable coordinate raises through `float32` first.
3. On the exact-float branch, compute magnitudes, the upward float screen and repeated-incumbent witness.
4. If the screen requires a new candidate, decode and fold that point's three components using the existing generator passed to `_Bounds.total`.
5. Update radius and the attaining component witness, then accumulate component conversion errors.

After every vertex, the helper decodes the three maximum float errors and computes the norm. Site-radius work occurs later in `_geometry_bounds:935–938`. Moving that work or the error calculation is outside the proposed optimization.

For the candidate generator, `_Bounds.total` takes its direct path because the input is a generator, not a native tuple. Each of the three values is decoded before its corresponding addition. `_Bounds.value:129–141` charges before finite/type/operand admission; `_Bounds.op:144–171` charges before prospective operand checks and arithmetic. These charged calls can invoke the request callback.

`ReachExecutionWork.charge:71–94` invokes the external callback, then checks operations/time, updates counters and invokes the captured observer. Callback exceptions propagate unchanged. `guard_bits:105–107` performs the current operand-limit check. These are explicit extension points, not invented asynchronous concurrency.

## 3. Conditional source witnesses

The following are unexecuted helper-entry witnesses. They identify specific schedule obligations. They are not claims that an original P11/P16/P23/L03 request naturally enters the illustrated state.

### A. Eager future-candidate arithmetic can precede an earlier geometry failure

Suppose an otherwise valid native sphere source is paired with an invalid first stored vertex. Under the original helper, the first geometry-point callback returns, then the conversion comparison raises `OKE-E-GEOMETRY` before any radius decode. Suppose a candidate schedule instead computes a future shortlisted vertex's exact sum before validating the first stored vertex. Let a custom request callback return on its first invocation and raise an existing sentinel exception on its second. The new candidate's decode/add sequence can reach that second invocation before the original first-vertex comparison. The first exception can therefore differ.

This witness rejects an unrestricted eager schedule. It does not reject in-order candidate processing or a separately proved passive-native restriction.

### B. In-order omission still needs a foreign-callback fallback

At the ordinary positive-radius sphere's first pole, the baseline upward screen exceeds the initial zero radius, so it enters the exact three-component fold. Consider a shortlist that omits that first pole's fold and a mismatching next stored vertex. A custom callback can return for the first geometry tick and first decode, then raise at the baseline's first addition. The omission schedule instead reaches the next geometry tick and its stored-value mismatch before the corresponding later callback invocation. The resulting first exception differs.

This illustrates why keeping all geometry ticks is insufficient to claim arbitrary callback equivalence. It does not require preserving the number of native budget checkpoints when an admitted optimization removes actual numerical work.

### C. A later native check cannot reconstruct producer history

Assume a sphere constructor or a trigonometric binding is temporarily changed while a mesh is produced, and restored before the candidate consumer inspects current bindings. The result may still be an exact tuple of exact native float triples. `_source_primitive_mesh` currently records typed radius and namespace, not the constructor's historical dispatch. A consumer-only check cannot distinguish that history from an ordinarily generated mesh by recipe key and native leaf types alone.

This is a conditional Python source-state witness. A supported threat/domain restriction might exclude it, but that restriction must be stated and justified. An actual-coordinate proof avoids relying on unrecorded constructor history, at its own charged cost. C066 should not present this witness as an observed product failure.

### D. Narrowed operand domains cannot silently receive the broad-domain shortcut

The wrapper already sends nondefault operand caps to the cold scalar path. Inside that path, decode and prospective addition guards can reject even small represented values under sufficiently narrow caps. A callback can also narrow a cap before a current point's candidate work. Omitting that work without a current admissible-domain proof can suppress the earlier guard and expose a later geometry error instead.

A full-cap, native, passive request can exclude this case with a proved finite bound for every omitted intermediate and a justified stability interval. Requiring that proof is different from claiming that the 32,768-bit cap must be raised or that all native optimizations are forbidden.

## 4. What a valid bounded schedule would need

A defensible candidate schedule would keep each vertex's original tick, conversion comparison and error accumulation in source order. It would evaluate retained exact candidates only at their original positions. Any skipped prefix candidate needs a theorem that the final exact result remains unchanged; it cannot use an unvalidated future stored vertex as evidence.

The omission must be limited to coordinates, math behavior and recipe assumptions actually covered by the mathematical proof. All other sphere resolutions, helpers, surface meshes, nonnative values, unsupported work owners, changed callbacks/observers/dispatch and narrowed domains need their existing path. An admission failure or exception is not permission to restart invisibly with erased charges.

The source contains extensive native-authority machinery in `_certificate_term_native:2762–2828`. It checks exact classes, relevant descriptors and function state, current work/limit/counter shapes, absent observers, and callbacks restricted to none or an unmodified native construction budget without its own foreign callback. This supplies a possible checklist of concerns, not a free reusable certificate for sphere geometry. It does not bind this constructor's history. Its setup and repeated inspections would be additional geometry work.

C057 also leaves the funding and passive-storage premise of transferring the existing gate unresolved. Exact dictionary type does not alone prove every lookup passive. C066 must not treat the old gate's presence or earlier development acceptance as closing that issue.

The historical native-field derivation explicitly allows the optimized native checkpoint schedule to change, while keeping foreign callbacks, observers and dispatch on ordinary arithmetic. Therefore this review does **not** impose identical native callback counts or turn ordinary operation savings into an automatic failure. New setup, selection, validation, fallback and replay costs still need complete accounting, and actual admission refusals remain failures.

## 5. Decision boundary

No authority-safe, fully funded shortlist implementation follows solely from the current recipe cache or extrema cache. An eager unrestricted schedule has the concrete order problem above. An in-order schedule in a sufficiently defined native/passive domain remains possible in principle, subject to the exact-coordinate mathematics and positive whole-request accounting.

This review authorizes no runtime edit or experiment. It establishes no measured savings, successful recording, release acceptance or universal impossibility. All original caps, fixtures, failure records and remaining gates retain their prior meaning.
