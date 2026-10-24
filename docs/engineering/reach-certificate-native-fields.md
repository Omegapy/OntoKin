# Group-local native certificate field proofs

This bounded candidate starts at checkpoint 029, commit
`6afa8439a37f0b7387b77a13f174014963adca8c`. It changes the independent supplied-byte
reader in `ontokin/reach_conformance.py`. It does not change source motion,
certificate fields, the source or destination numerical basis, or the adopted
[complete inequalities](../language-design/planar-reach-v0.1/quantization.md).
The [checkpoint 029 handoff](reach-recording-validation-2026-10-23/HANDOFF-029.md)
identifies the complete-input opportunity and its limits. Implementation,
execution and acceptance are separate records.

## Two independent transformations

The first transformation reuses an earlier completed decode while constructing
one new group's 21 reported fields. The second proves a fresh required
comparison from the two current exact field pairs. They have separate helper
classes, separate actual admission categories and independent disable controls.
Neither transformation reuses a successful claim, changes a required minimum,
or adds a cross-group numerical cache.

### Earlier completed native decode

For an input integer, the key is its exact native type and integer value. For a
float, the key is its exact native type and its eight binary64 bytes. Thus an
integer and a numerically equal float are different keys; positive and negative
floating zero are also different keys. Eligible floats are finite and
nonnegative. Eligible integers are nonnegative with at most 2,048 bits. A
helper receives only the original bounded tuple. Receipt retention and reuse
require the next original typed key; other inputs use ordinary decoding.

The original `arithmetic.value` must execute and finish before its result is
eligible. The strict native gate holds before that call and after it returns.
Fields with no later typed match execute their original decode directly and
retain no receipt; they need no optional native-state scan. A duplicate's
entry gate covers the immediately following pure native receipt reads, and
the complete gate is repeated after its actual first admission charge.
The retained receipt contains its immutable input, the actual completed
Fraction object and the native integer numerator and denominator observed at
completion. A separate tuple retains the identity of each completed receipt;
replacing the lookup entry with a forged, internally consistent tuple cannot
make it an earlier executed decode.

An omission checks the current typed input, completed-result fields, receipt
identity, original arithmetic/work owners and current native environment. Equal
input bits under unchanged native decoding imply the same exact rational
result. The original integer input guard and decoded numerator/denominator
guards still execute. The first actual omission charges
`independent_certificate_decode_admission`, and the full gate and receipt are
checked again after that charge. Original resource or callback exceptions are
not caught or translated by this helper.

The result is a new native Fraction allocated from already admitted integer
fields. It does not alias the completed result or another returned field. The
helper dies when the one group's fields have been constructed. Subsequent
groups create their own helper, and their original first decodes execute.

### Fresh equality of current rational fields

Let the current reported value have fields `(an, ad)` and the current required
minimum have fields `(bn, bd)`. Native positive denominators and

`an == bn` and `ad == bd`

prove that their exact comparison returns zero. The proof reads both current
objects at every requirement. It does not call Fraction equality or retain a
previous comparison result. Unequal or unsupported fields take the original
`arithmetic.compare` path.

A bounded native slot filter can decline unequal or unsupported pairs before
the full native-state scan. It pins the original Fraction class and access
descriptors before reading native integer slots through a saved native getter,
and first declines through saved native trace/profile queries when a hook is
active, including a hook installed after context creation. The filter never
establishes a claim. Every potentially equal pair still runs the
complete gate and freshly reads both current fields through the original
reported-value/minimum field reader.

Write `B(n)` for the bit length of native integer `n`. The proof retains both
stages of the original comparison guards:

| Guard stage | Required field widths |
| --- | --- |
| Before first admission | `B(an)`, `B(ad)`, `B(bn)`, `B(bd)` |
| Prospective cross products | `B(an) + B(bd)`, `B(bn) + B(ad)` |

The latter guards remain required even though no cross product is allocated.
The first eligible equal comparison charges
`independent_certificate_compare_admission`; its owners, fields and full native
gate are rechecked after that charge. Later equal comparisons use the same
admitted context but prove their own current fields again. They retain both
guard stages. No tolerance or original finite limit changes.

One context is created per group in `flush` and is passed explicitly into that
group's complete algebra. It covers captured-minimum requirements, destination
requirements and the six complete-inequality requirements. The complete algebra
accepts the context only when it belongs to that same arithmetic object. Direct
calls without that context retain their original comparisons. Quarter-plan
comparisons, exact maxima and final tolerance checks remain unchanged.

## Native environment and fallback

Both helpers require the strict restrictions of `_certificate_term_native`:
original native arithmetic, Fraction fields and relevant method descriptors;
original function code, defaults, closures, referenced globals and builtins;
an unchanged work owner; no work observer; no active trace or profile hook; and
either no external callback or the original native construction-budget tick
with no nested custom check. Neither helper installs or clears a callback or
observer.

The additional field gate explicitly pins `math.isfinite`, `struct.pack`, the
raw-field reader and typed-key reader, including Python function state. Module
identity alone would not protect a replaced module attribute. It also pins the
term gate's identity and function state before relying on that gate. Descriptor
checks occur before optional reads of potentially foreign Fraction fields.

Only the full native 32,768-bit work domain permits omissions. A narrowed,
widened, foreign or changed live domain declines the optional proof. Eligible
decoded fields are at most 2,048 bits and equal-comparison prospective fields
are at most 4,096 bits; all original guards nevertheless execute. The unchanged
global arithmetic limit still applies when no work object exists.

If eligibility is lost, the ordinary decode or comparison executes. The
per-field fallback dynamically resolves `arithmetic.value` in the original
order; a foreign callback that replaces that method between fields must remain
observable. A foreign operation that restores itself during a call cannot
retroactively supply a native receipt. Mutated results or replaced receipts do
not support an omission. Fresh understated claims still fail their current
comparison.

The original member and threshold checks remain in their original positions.
In particular, both `thresholds.admit_continuation` calls around each flush
requirement remain, with `compared=True` and `equality_shortcut=False` on the
second call. Discarded threshold domains still require admission and can still
request ordinary replay. Both actual width squares, quarter plans, exact
maxima, independent minima, tolerances and final claim checks remain.

## Work accounting and acceptance protocol

The complete P09 input census found 78 duplicate typed decodes and 96 equal
field comparisons across 12 groups. If every site remains eligible, one decode
and one comparison admission per group would reduce 174 gross omissions to
150 net operations. That is a ceiling before execution, not a measured saving.
Any decline, replay or additional performed work reduces the actual saving.

The native optimized calculation changes its checkpoint schedule. Every
remaining operation and new admission is charged to the same shared request
budget. No identical native callback schedule is claimed. Foreign callbacks,
observers and dispatch preserve ordinary arithmetic and its original exception
behavior. An admission refusal is an actual failed request, not a result to
discard or relabel.

Before adoption, the separate decode-only and comparison-only candidates and
their combination must pass hostile/equivalence tests and actual successful
prefix controls. Use the original P09, P11 and L03 source fixtures at end `1/4`,
4 fps, helpers disabled and unchanged tolerances. For each transformation and
case, execute five alternating exact-control/candidate pairs. Retain every GLB,
complete export report, counter map, cache occupancy, elapsed time and failure.
The exact checkpoint 029 control functions retain their original global
resolution in the same identified process.

Require identical complete GLB bytes and export reports, observed native
admission, positive complete shared-request savings including admissions, and
a candidate median elapsed time no more than 10% above its control in each
case. This development screen is fixed before measurement; it is not a new
product limit or an elapsed-speedup claim. Prefix success cannot establish a
full original recording pass. The original full P09 baseline fails and therefore
cannot provide a successful complete-output comparison.

After acceptance, execute the related regression cohort and all unchanged 28
original source recordings on the identified integrated cut. Preserve the
100,000-operation, 30,000-ms, 32,768-operand-bit and 256-numerical-cache-entry
limits. The separate 512-category metadata inspection bound is unchanged.
Agent delivery, full regression, Python compatibility, independent rates,
native/browser/visual roles, formal release input closure and all R/Q gates
remain separate obligations. This bounded proof does not complete the release
or the full product goal.

## Identified development acceptance

[Checkpoint 030](reach-recording-validation-2026-10-23/checkpoint-030.json) records
separate and combined controls, hostile regressions and acceptance on published
source `d2f0088c4f3c1f570630334804a5a8f78e0105ac`. P09 passes at 99,975 operations
and the original suite is 24/28. Actual measurements and remaining failures are
identified in [HANDOFF-030](reach-recording-validation-2026-10-23/HANDOFF-030.md);
the earlier static 150-operation ceiling remains distinct from measured complete
baseline savings.
