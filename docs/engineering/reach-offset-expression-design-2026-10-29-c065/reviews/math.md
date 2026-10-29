# C065 independent mathematics and source-expression review

## Result and boundary

The original P11 eye recipes contain real repeated offset arithmetic beyond the existing coefficient cache. Literal common-subexpression reuse can omit at most two exact multiplications per paired left/right visit. A stronger sign-aware transformation can omit up to four numerical operations per paired visit while retaining the original floor locations. This is a source-derived gross opportunity, not an observed saving or a positive complete-request result.

Original L03 provides no corresponding repeated nontrivial offset product under the same orientation. Its moving attachment lengths are one, and the current product helper already returns its first operand for multiplication by one.

Baseline: `a7452d0063b785c1bfb02c45844ef341e3e0bf0b`, tree `f063d6c54b0bbca286353169f6d7505cfaa8ccb8`. This review read source, existing tests and C064 records. It imported no OntoKin module, executed no product request or test, and changed no runtime file. The mathematical schedule below still needs a funded live-authority implementation before any runtime experiment is justified.

## Existing arithmetic remains in the baseline

In `ontokin/reach_reference_center.py:658–686`, a nonaxial offset under a single-axis quaternion uses

`D = w*w - s*s` and `C = 2*w*s`.

For plane coordinates `(x,y)`, its two outputs are

`floor128(D*x - C*y)` and `floor128(C*x + D*y)`,

where `floor128(v)` is exactly `floor(v * 2**128) / 2**128`. The coordinate along the rotation axis passes through unchanged. These are exact rational products and sums followed by two individual floors; no floor appears between an offset's two products and its sum.

The baseline already shares `D` and `C` for admitted repeated orientation sources. Preparation chooses sources and excludes separated one-off groups at lines 408–429; `_coefficients` implements the bounded shared-cache path at 592–655. C065 must preserve that baseline and cannot count the earlier coefficient improvement again. The actual two floors at 681–682, each node visit at 712, each node's recipe/parent admission, and position assembly at 739–744 also remain baseline work.

## Actual original-source opportunity

The P11 library's `Head` declares these eye offsets in `docs/language-design/planar-reach-v0.1/libraries/reach-assets.ok:54–65`:

| Eye | Original local vector |
| --- | --- |
| Left | `(-0.1, 0.05, 0.23)` |
| Right | `(0.1, 0.05, 0.23)` |
| Brow | `(0, 0.16, 0.2)` |

The head hinge uses the Y axis (`reach-assets.ok:115–124`). With axis index one, `_offset` orders the plane as `(local z, local x)` and the axial coordinate as `local y` (`reach_reference_center.py:669–670`). Thus the two side eyes use plane coordinates `(Z,-A)` and `(Z,+A)`, where `Z` and `A` denote the exact admitted rational values of source `0.23` and positive source `0.1`. They are not silently replaced with the mathematical decimal fractions `23/100` and `1/10`.

Both eyes inherit `rig.head.frame` orientation. C064's retained moving-plan order ends with brow, left eye, right eye, and the existing coefficient test checks all three eye recipes select `rig.head.frame` (`tests/test_reach_centered_coefficients.py`, `test_plan_selects_repeated_nonaxial_children_and_leaves_unique_sources_unmemoized`). This test was inspected, not rerun. A general compiler must still match the actual admitted topology; neither the source names nor the historical plan order is sufficient live authority.

P11's two arm hinge-tip offsets also have the same length `0.75`, but they belong to different independently owned shoulder orientations. Their equal length alone supplies no reusable exact product. The head base offset is axial, so its rotation products are already bypassed. Root/stationary offsets and zero-offset nodes provide no new multiplication opportunity for this candidate.

L03's source specifies `upper_length = forearm_length = 1` in `draft2-supplements/sources/l03-completed-action-new-owner.ok:14–25`. The upper hinge tip and tool mount therefore use plane vector `(1,0)` under the distinct shoulder and elbow orientation sources. In `_offset`, `product(D,1)` returns `D`, `product(C,1)` returns `C`, and products with zero return zero without an arithmetic tick (`675–677`). The coefficient computations and two floors remain, but this offset-product candidate cannot remove a multiplication that does not execute. The separate L03 phase does not change those lengths or merge its two source authorities.

The authored timelines keep this source scope finite. P11 has a fixed root and starts the head look plus both arm reaches at time zero; each lasts two seconds inside its three-second scene (`sources/p11-complete-segmented-character.ok:12–21`). L03 has a fixed root, starts the first two-second reach at zero, and starts its second one-second reach at time two inside its four-second scene (`draft2-supplements/sources/l03-completed-action-new-owner.ok:12–26`). Neither source adds later attachments, root motion or release events. This identifies the recipes throughout their authored tails; it does not claim that every later key was measured or that every coefficient was sampled as nonzero. The original recording request options, horizons and key counts remain separate retained evidence and are not replaced by scene duration.

## Literal reuse and the stronger signed schedule

Literal common-subexpression reuse identifies `D*Z` and `C*Z` in both side-eye offsets. Reusing just those results removes at most two right-eye multiplication calls. The `+A` and `-A` products are different exact expressions.

The stronger schedule preserves the left eye's existing product order and retains these four completed values:

| Retained value | Original left-eye expression | Last mathematical use |
| --- | --- | --- |
| `p` | `D*Z` | Right first-plane sum |
| `n` | `C*(-A)` | Right first-plane sum |
| `q` | `C*Z` | Right second-plane sum |
| `m` | `D*(-A)` | Right second-plane sum |

Left outputs remain `floor128(p - n)` and `floor128(q + m)`.

At the right eye's original evaluation position, after its ordinary recipe and parent checks and its existing coefficient path, the candidate outputs are

`floor128(p + n)` and `floor128(q - m)`.

Because exact native multiplication is sign-symmetric, `C*A = -n` and `D*A = -m`. Consequently the candidate arguments are exactly the original right arguments `D*Z - C*A` and `C*Z + D*A`. No new negation operation is required. The right first combine changes from subtraction to addition; its second changes from addition to subtraction. Both floors remain at their original coordinate locations, and no rounding is moved across an addition. The unchanged axial coordinate, parent-position additions, uncertainty flag and radius assignment then preserve the numerical centered pose under the stated premises.

This establishes rational equality only. Arbitrary custom arithmetic can observe the changed operation names. The candidate must establish native dispatch before using the identity and must preserve the existing fallback behavior when that premise does not hold.

## Gross charge bound and degenerate branches

When both `D` and `C` are nonzero, the two side-eye offsets perform eight exact multiplications, four exact additions/subtractions and four floors. The signed schedule performs four multiplications, the same four combine operations and the same four floors. Its raw reduction is four operations before any new preparation, storage, copying, lookup, admission or fallback charge.

This four-unit figure is a ceiling, not a claim that every supplied key executes those operations. `_offset` already bypasses zero vectors, exact zero-radius identity orientations and axial vectors. Stationary-cache hits can bypass the offset body. If either coefficient is zero, `product` and `combined` take different branches:

| Coefficients | Baseline right-eye numerical operations outside its two floors | Signed right-eye operations outside its two floors | Raw difference |
| --- | ---: | ---: | ---: |
| `D != 0`, `C != 0` | 4 multiplications + 2 combines | 2 combines | 4 |
| `D = 0`, `C != 0` | 2 multiplications + 1 negation | 0 | 3 |
| `D != 0`, `C = 0` | 2 multiplications | 1 negation | 1 |
| `D = 0`, `C = 0` | 0 | 0 | 0 |

The table assumes native exact values, unchanged nonzero `A` and `Z`, and reuse of the left products, with `combined` retaining its zero-input behavior. It excludes all new bridge work. It is a source branch calculation, not a product run. A restricted implementation may instead decline degenerate coefficient cases; then its failed-selection cost still belongs in the complete ledger.

The brow does not enlarge the four-unit opportunity under the selected multiplication/addition model. Its `0.2` planar coordinate can be related to `0.1` by a factor of two when the admitted rationals establish that relation, but deriving one product from the other requires a scale/division operation. Replacing a multiplication by another charged scalar operation does not remove a unit. No free integer shift, special floor identity or new scalar-operation exemption is credited.

## Numerical bounds and floor discipline

`_Arithmetic.exact` checks operand and prospective widths at `ontokin/reach_reference.py:120–139`. Native sign reversal changes neither numerator magnitude nor denominator. The signed schedule's right sums therefore have the same operand-width and prospective add/sub bounds as the original right sums, provided the retained values are the exact current products and the same operand limit is still active. This does not remove the obligation to perform the required live checks.

The candidate must not replace two separate floors with a floor of a merged translation. In general, `floor128(a) + floor128(b)` differs from `floor128(a+b)`, and sign reversal of a floored value differs from flooring the sign-reversed exact value. The signed product schedule avoids both transformations by retaining pre-floor products and preserving the four side-eye floor sites.

## Concrete lifetime and the unresolved implementation premise

A conservative candidate can compile a source-only edge from the left recipe to the right recipe and materialize one bounded four-value bridge during a single evaluation key. It must produce each retained value only after that original left multiplication returns, without evaluating or admitting the right recipe early. The first pair can die after the right first floor; the second can die after the right last floor. All temporary state dies on every failure or fallback and before a new key/phase. It contains no completed pose and is not a second cross-key numerical cache.

That lifetime bound does not establish free storage or immutable authority. The bridge introduces numerical value occurrences, selection, validation and ownership questions that the existing source graph does not pay automatically. In particular:

- Right recipe admission must stay at the original node. Reading and rejecting it while evaluating the left eye can change the first exception.
- A product retained across the rest of the left node and the right-node admission must not be trusted merely because its tuple or dataclass is frozen. Existing tests deliberately mutate Fraction leaves and frozen records.
- Native dispatch departures must be latched across actual callbacks, including a temporary replacement followed by restoration. `_coefficients` already has a separate completed-operation native latch; `_Guard.current` alone is not an equivalent proof.
- The right coefficients and source/parent operands must freshly match the retained product authority. Final source admission is necessary but does not authenticate every transient arithmetic receipt.
- Every added lookup, copied logical value, type/limit/claim check, rejected selection and fallback must appear in the cost ledger. A four-value bundle is not automatically one semantic operation.

Let `E` be the actual complete-request paired visits admitted by a concrete candidate, `g(e)` their source-branch reductions with `0 <= g(e) <= 4`, and `H` all newly required work, including preparation and unsuccessful paths. The strongest result of this review is

`complete-request saving = sum(g(e) for e in E) - H`.

This review does not assign `H = 0`, invent `E` from supplied-key counts, or extrapolate a successful tail from a failed recording. A fully funded bridge with four newly copied scalar values already consumes the four-unit best-case opportunity before its other costs; a different reference-only representation needs its own authority and accounting proof. The independent authority and cost reviews determine the selected design's disposition.

The caller contains one optional centered-reader call per `_key_comparisons` invocation (`reach_conformance.py:1997–2002`), and a normal `compare_certificates` traversal invokes that function once for its initial key and once for each remaining key (`3388–3401`). Therefore a normal single pass over the retained 52 P11 keys has a loose raw ceiling of `4*52 = 208`; skipped, stationary, fallback and degenerate cases can lower it. This is not an attained count or a successful-request saving. The code also permits a same-work certificate replay, so any whole-request argument must either establish that the actual original path does not replay or include every replay's costs and occurrences separately. The per-visit four-unit bound does not depend on that distinction.

## Reproducible offline derivation

A standard-library evidence script can verify this review without importing product code. Bind the named source files to their Git blob and SHA-256 identities; parse the Python AST as data to check the unchanged product/combine/floor ordering; and confirm the pinned source eye vectors and axis. Represent polynomials in formal rational variables `D,C,A,Z` as dictionaries from monomials to integer coefficients. Expand each original and proposed pre-floor expression and require exact equality of the coefficient maps. Each output then retains the same explicit `floor128` wrapper, which proves the floor argument is unchanged for all admitted rational inputs, rather than testing only selected angles. Report the branch-count table separately from this algebra proof. This calculation establishes a mathematical identity and source binding only; it establishes neither mutable-state authority nor a measured runtime saving.

## Conclusion

C065 has identified an actual additional P11 arithmetic identity and its finite raw opportunity. That is narrower than a proven optimization. The signed schedule is numerically sound under native exact, current-operand assumptions and retains all original floor locations. It supplies no positive complete-request saving until the bridge and every admission path are funded and authority-safe. L03 has no opportunity for this selected offset-product transformation. No runtime change or experiment is justified by the mathematical identity alone.
