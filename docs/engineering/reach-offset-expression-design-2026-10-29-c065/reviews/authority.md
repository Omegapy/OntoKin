# C065 independent authority review: signed eye-offset product sharing

## Scope and finding

This review covers the proposed four-product bridge between the original P11 left and right eye offsets. The pinned baseline is commit `a7452d0063b785c1bfb02c45844ef341e3e0bf0b`, tree `f063d6c54b0bbca286353169f6d7505cfaa8ccb8`. The full product goal remains editable source-driven 3D assets and behavior with validated destination delivery; this review addresses only one independent-reader calculation.

**Reject the selected detached four-product bridge.** Its signed algebra preserves the original floor arguments under stable native inputs, but the selected producer schedule creates four detached copied scalar occurrences to avoid at most four original multiplications. Paying each copy once already exhausts that favorable arithmetic ceiling, before new live admission or other overhead. The authority review also rejects treating a single entry check as sufficient for reuse across callbacks. This is a finite decision about the specified detached-copy schedule, not a theorem that every expression graph must make those copies or that every sharing representation fails.

I inspected pinned source, the adopted budget text and adoption record, existing mutation/dispatch tests, C057's authority finding, and C064's authority review. I imported no OntoKin module, ran no product request or test, changed no runtime file, and measured no operation count or timing. The counterexamples below are conditional source arguments, not executed tests or observed P11 failures.

## 1. The exact candidate and its mathematical boundary

P11's head hinge rotates about axis 1. `_offset` therefore projects onto coordinate order `(z, x, y)`. The two eye recipes have planar coordinates `(Z, -A)` and `(Z, A)`, where `A` and `Z` mean the actual admitted exact source values corresponding to the authored `0.1` and `0.23`. This notation does not replace those values with the decimal rational numbers `1/10` and `23/100`. The source definitions are `libraries/reach-assets.ok` lines 54–66 and 110–124, relative to `docs/language-design/planar-reach-v0.1/`.

Let `D` and `C` be the currently admitted diagonal and cross coefficients from the existing `_coefficients` route. The proposed bridge retains the left eye's completed exact products at their existing arithmetic positions:

| Retained result | Original left operation |
| --- | --- |
| `p` | `D * Z` |
| `n` | `C * (-A)` |
| `q` | `C * Z` |
| `m` | `D * (-A)` |

The left eye retains `floor(p - n)` and `floor(q + m)`. The right eye uses `floor(p + n)` and `floor(q - m)`. Since `n = -(C*A)` and `m = -(D*A)`, these are exactly the right eye's original unrounded floor arguments. No new negation is needed. The two right floors stay at their original coordinate boundaries; the unchanged axial coordinate and parent-position additions remain separate.

This proof applies to exact, unrounded products. Sharing a rounded left coordinate, combining source translations before an existing floor, or removing a floor would need a different proof. For a non-grid value, negating a rounded-down result is generally different from rounding down its negative.

The original `_Arithmetic.exact` prospective guards use absolute numerator bit lengths and denominator bit lengths. Under unchanged native arithmetic, changing `C*A` to the already completed `C*(-A)` preserves those widths; the corresponding add/sub formulas use the same width expression. Equal floor inputs also retain the original grid-domain obligation. This establishes a numerical compatibility premise under stable inputs; it does not establish that an earlier guard remains authority after a callback narrows the operand limit.

Relevant source: `ontokin/reach_reference_center.py` lines 658–686 and `ontokin/reach_reference.py` lines 120–139. The maximum of four removed multiplication ticks applies only when those original products actually take the charged multiplication branch. Identity/axial paths and zero coefficients may remove some or all of that opportunity before any new bridge overhead is counted.

## 2. Original protections that must remain

| Protection | Baseline location | Required treatment |
| --- | --- | --- |
| Recipe type, vector domain, flags and value seal | `reach_reference_center.py` 701–708 | Admit the right recipe at its existing node boundary. A preparation-time pair descriptor cannot replace the current recipe check. |
| Detached source leaves and parent pose | `_Guard.freeze`, 164–172; `_Guard.pose`, 192–207 | Preserve the original copies and live watches. Equal values are not permission to share mutable operand objects. |
| Original node tick | `evaluate`, 712 | Keep this node evaluation and its callback boundary. The proposal removes arithmetic within the node, not the node itself. |
| Live owners, source leaves, records and numerical domain | `_Guard.current`, 209–235; `checked`, 237–241 | Recheck after every surviving callback. Do not defer a mutation failure until final source admission. |
| Fresh coefficient production/admission | `_coefficients`, 592–655 | Keep existing orientation/coefficient reuse in the baseline. A common source marker alone does not establish equal current coefficient operands. |
| Current source-batch and cursor admission | `evaluate`, 755–763; `admit_source`, 432–448 | Preserve final source authority and original owned-cursor cleanup. They do not validate arbitrary new bridge results. |

The evaluator creates a new `_Guard` for each node. Its records are not automatically inherited by the next node. Therefore four products retained from the left eye cannot be considered watched by the right eye merely because the left guard originally admitted them.

The maximum private lifetime can be stated precisely: start only when a left product has completed, retain at most four exact product values for this one source pair, consume them only at the matching right node in this same key/phase, and discard them on completion, rejection, fallback or exception. Retaining poses, crossing keys or phases, or accumulating products for arbitrary nodes would define a broader storage mechanism. Even this bounded lifetime does not exempt storage, copied logical occurrences or new checks from accounting.

## 3. Current dispatch and first-exception behavior

`_Guard.current` verifies arithmetic/pose owners, work and callback identities, watched fields and the numerical domain. It does **not** by itself prove that `guard.exact`, `a.exact` or their other participating methods still have the original dispatch. The existing coefficient optimization has a separate `_coefficient_domain` check for native methods and a latched departure across completed arithmetic (`reach_reference_center.py` 542–566 and 632–649). A new result bridge cannot borrow that proof for later offset products or changed right-eye add/sub calls.

### Conditional witness A: restored dispatch does not authenticate an earlier product

Assume a native coefficient calculation has completed. A callback during the left-eye product sequence installs custom exact-arithmetic dispatch for a subsequent product. That dispatch returns a bounded native Fraction which differs from the native product. A later callback restores original dispatch before the right eye begins. The source recipes, owners and final source receipts remain otherwise unchanged.

The original evaluator can use the custom result in the left eye, then recompute the right products through restored native arithmetic. A bridge that checks native dispatch only when the right eye consumes its retained products can reuse the earlier custom result and change the right eye's value. Present native dispatch is not evidence that each saved result was produced by native arithmetic.

The safe design obligation is to establish and retain authority for every producing operation and to latch any departure across the actual callback boundaries. This is the same reason that the existing coefficient route does not publish a native receipt after a temporary dispatch change. It is not enough to check the producer once before all four products or only after the complete left node.

This witness is source-level and unexecuted. It identifies a hole in an insufficient bridge guard; it is not a claim that the original P11 request installs custom arithmetic.

### Conditional witness B: native product receipts do not authorize changed combine dispatch

The original right coordinates request a subtraction and then an addition. The signed bridge requests an addition and then a subtraction, with sign-related exact operands. Those native operations have equal results and prospective widths, but custom dispatch can distinguish their operation names or operands.

Consider an otherwise admitted pair whose two second-coordinate terms are nonzero. At the existing callback belonging to the right eye's first floor, install custom `a.exact` dispatch which raises a retained exception `E` for a subtraction and delegates all other operations to the saved native method. Both source recipes and all numeric operands remain unchanged. This is a conditional event-position witness, not a claim tied to a measured callback count.

The original right second coordinate now performs two multiplications and an addition. None invokes the custom subtraction failure. The signed bridge instead requests `sub(q, m)`, so it raises `E`. The earlier first-coordinate subtraction has already completed before this callback. `_Guard.current` alone does not reject the method substitution, because the arithmetic owner, work, callback, leaves and watched records are unchanged. Thus an entry-only gate can introduce a new first error at this helper even though the mathematical values would be equal under native arithmetic.

Native authority is therefore needed at the actual transformed operation, with the original expression used on a departure. If departure occurs after earlier operations have completed, a concrete design must describe the remaining original continuation and charge it accurately. Restarting the whole node or calling an ordinary helper again does not automatically preserve the first exception, callback sequence or lower-budget behavior.

The source already preserves outer method binding in `_direct_coefficients` because Python binds an outer callable before evaluating inner calls (569–589). A replacement expression must analyze its own binding/evaluation order instead of assuming that algebraic equality preserves dispatch behavior. Existing tests at `tests/test_reach_centered_coefficients.py` 166–250 cover this distinction for the coefficient route; those tests were read, not executed here.

### Other first-error obligations

Do not inspect or reject a later right-eye recipe before the original right node is reached. For example, an eager right-recipe identity failure could overtake an original earlier left arithmetic or callback exception. The already adopted per-node admission order avoids that change.

An original exact operation ticks before dynamic Fraction conversion and prospective operand guards (`reach_reference.py` 120–139). A newly inserted bridge admission can also invoke a callback. If that callback changes the cap, precision, arithmetic dispatch or a watched operand, the design must state the actual next failure and cannot simply label every such departure a harmless retry. `_Guard.original` and the evaluator's `_OriginalFailure` handling preserve inherited oracle errors separately from optional-domain rejection (243–272 and 765–775).

The proposal is not required to invent removed arithmetic as executed work. It is required to preserve the adopted cancellation and interruption contract for its actual operations, including the first real exception and any required source/operand rejection. A lower count of callbacks is not, on its own, proof of a correct optimization.

## 4. Retained values need live authority

A frozen dataclass or tuple does not prove its Fraction leaves immutable. The current code explicitly protects against alias mutation with bounded integer seals and detached values (`_integers`, 93–106; `_Guard.freeze`, 164–172). Existing tests deliberately mutate a Fraction's private fields through `object.__setattr__`; this is part of the inspected source's defensive behavior, not a new threat model invented by this review.

A concrete bridge needs to bind all of the following:

- Its exact source pair, plan/context and current key/phase.
- The actual admitted right vector and sign relation to the producing left vector.
- The actual current diagonal and cross coefficient operands, not merely their source path.
- Every retained result's native shape, bounded numerator/positive denominator and relation to its original producer receipt.
- The same arithmetic/work domain and the validity of any required native dispatch assumptions.
- Fresh result/operand protection through both right floors and all intervening callbacks.

Copies at publication and consumption, seal/field comparisons, new type/limit/claim checks and access to retained results are semantic work whose funding must be explicit. A result cannot be declared valid merely because final source admission passed: that gate checks source receipts and retained cursors, not this proposed private product bundle.

Existing controls demonstrating the relevant categories are `test_reach_centered_coefficients.py` 265–380 (cached shape and Fraction mutation, cold-publication mutation, cancellation/domain changes at each offset callback, and live warm receipts) and 471–518 (recipe mutation and final batch rejection). They support the required review coverage. Their historical passing status is not a test result for this unimplemented bridge.

## 5. Accounting and C057 remain separate obligations

The effective budget rule is section 3 of `docs/language-design/planar-reach-v0.1/budget-counting.md`. Its historical draft heading is preserved; `ADOPTION.md` and `adoption.json` establish the adopted input authority. Exact bounded reuse may omit real numerical work that it avoids. Every new lookup, type/limit/claim check, output occurrence and copied logical value still needs a charge, and source/cancellation obligations remain.

The strongest arithmetic premise here is four removed scalar multiplications per eligible pair. The selected schedule explicitly creates detached copies of `p`, `n`, `q` and `m` for its producer bundle, with one new scalar-copy charge for each. These are four copied logical occurrences, not four arbitrary Python instructions. They remain four occurrences even if some numerical values happen to coincide. Therefore producer copy work alone is at least four charges, while removed product work is at most four. New consumer access, type/limit/claim checks, preparation, fallback or finalization cannot make this nonpositive difference strictly positive.

This argument depends on the selected representation and charge schedule. A proposal that extends the lifetime of the original result objects without copying them, or introduces an immutable native-integer representation, is different. This review does not assert that such alternatives mathematically require four detached scalar copies. They would need their own explicit storage/lifetime boundary, proof of current native semantics and retained-value integrity, and complete funding. Calling them private temporaries does not supply those missing proofs.

Placing the four products inside an existing `_CenteredCoefficients` LRU row also does not make their publication pre-existing work. The ordinary coefficient lookup, five cold coefficient operations and possible row write finish before `_offset` computes these vector-dependent products. The current row contains only `scalar`, `active`, `diagonal`, `cross` and its seal. A larger row would require a new vector/input identity, later publication or update, and live admission of the new fields. The old lookup's ordinary bounded bookkeeping cannot automatically be credited against newly added proof or copied occurrences. Such a row extension is outside the selected detached bridge and is unproved here.

C057 found incomplete funding and a conditional passive-storage gap in one accepted comparison mechanism. It did not prohibit all finite reuse, invalidate all existing helpers, or establish a rule that this bridge must reuse that mechanism. It does mean that a new design cannot cite earlier comparison acceptance as proof that its new scans or repeated current checks are free. If a new admission gate examines mutable dictionaries, native `dict` type alone does not prove all lookups passive: the specific colliding-key witness in the C057 authority review remains a caution about that added inspection route.

The complete-request analysis must retain preparation, every key/phase, inactive or ineligible pairs, fallback, finalization and any cache consequences. No raw multiplication ceiling is a measured complete-request saving or proof of completion under 100,000 operations.

## 6. Disposition

The selected signed expression is algebraically valid under its stated native, stable-input premise. **The concrete detached-copy bridge is rejected before implementation because its four funded producer copies already consume its at-most-four-operation opportunity.** It also has no authority to omit live producer/consumer checks: entry-only reuse can accept a result produced during transient custom dispatch, miss a live value mutation, or expose a changed combine operation to custom dispatch.

A different surviving design would need an explicit bounded representation, paid producer and consumer authority, operation-local dispatch handling, faithful fallback/exception behavior and a positive full-request cost argument. None of those costs can be assigned zero solely because the representation is private or short-lived. The finite rejection here does not close every zero-copy graph, coefficient-row extension or larger arithmetic transformation; it supplies no positive premise for any of them either.

All original limits, fixtures, horizons, equations, independent oracles, tolerances, defaults and historical failure meanings remain unchanged. This review establishes no new recording success, runtime improvement or release acceptance.
