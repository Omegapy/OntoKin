# Final after-state source bounds in recording certificates

The final retained key uses the fully committed **after** state at the requested
end clock. A natural completion, authored stop, release or another source event
at that clock may transfer numerical error into a new anchor. The preceding
positive-width phase does not necessarily bound that new numerical basis.

## Observed defect

On source cut `6b44da06e9c2303fb916c2a9930b725c0606341e`, the original P05
recording reached the unchanged independent certificate comparison at 99,898
operations. All six carrier rows for the final pair, `35/12` to `3` seconds,
understated `source_numeric_rotation_bound_rad`. Five descendant rows also
understated `source_numeric_position_bound_m`. The independent checker correctly
included its final after-state source basis; the writer considered only the
retained positive-width phases.

The root's spin completes at three seconds. Latching carries the preceding
exposed rotation error into the final orientation anchor. Applying the ordinary
constant-root source basis to that anchor adds one product allowance and another
exposure allowance. For this source, the exact difference is

\[
\epsilon_{q,\mathrm{final}}-\epsilon_{q,\mathrm{preceding}}
=2^{-50}+2^{-91}
=\frac{2199023255553}{2475880078570760549798248448}.
\]

The writer's root rotation claim was
`2199023386627/2475880078570760549798248448`; the independent endpoint minimum
was `1099511660545/618970019642690137449562112`. Descendant path terms are the
same on both sides of this comparison, so the same rotation deficit propagates
to each carrier. The larger rotation anchor also contributes to downstream
position allowances through the existing path-offset formula.

## Correction and scope

Before constructing interval certificate groups, the writer computes one ordinary
zero-width source bound at the final retained clock from the plan's explicit
`final_state`. It uses the existing selected recording-frame traversal, including
the actual source dependencies of those frames. It does not inspect an assumed
current simulator state or reuse the preceding phase as a final-state witness.

For any group containing the final key, the reported source position and rotation
allowances are the maximum of the existing selected phase allowances and the
new final point allowances. All coefficients using those allowances, including
endpoint conversion, arc and complete error inequalities, are recomputed by the
ordinary certificate calculation. Sharing a larger final allowance with other
rows in the same group is conservative because their formulas are monotone in
these nonnegative inputs.

The final point is not a positive-width motion phase. Authored and stored clocks,
keys, sampled poses, phase-index coverage, derivative bounds, operation/cache
limits, requested tolerances and all four mandatory quarter allocations remain
unchanged. The independent checker and its rejection criteria are unchanged.
The additional required proof consumes the original request budget; a subsequent
resource failure remains a failure.

## Verification scope

The focused regression cases use separately identified short test variants to
exercise natural spin completion, an explicit authored stop, and an unchanged
ordinary endpoint through actual supplied-byte validation. The release case
checks the writer's final after-state selection and exact outward maxima at the
completed certificate stage, without claiming an independently validated export.
They also cover explicit final-state ownership, selected-frame equality to the
complete source traversal, cancellation, live operand narrowing, and hostile
understatement of either final source allowance. Frozen acceptance sources and
settings are not edited. The full original P05 recording and complete source
suite require their own identified runs after integration.

## Separately exposed release enclosure discrepancy

A short P16 variant moves its authored release and force start from two seconds
to `1/8` second and requests that exact final clock. On the preceding source cut
`6b44da06e9c2303fb916c2a9930b725c0606341e`, its complete export already failed the
independent certificate check after 48,917 operations. The final payload row
understated both source position and rotation. On the endpoint-correction cut
`13334500e4383e3e6914a427ba6d3e49f4136375`, the complete export still failed after
49,318 operations, with the same exact independent position minimum. Rotation
now agrees; the remaining position deficit is approximately `5.02e-31 m`.
Both observed runs retained identical before/after implementation input hashes.

The remaining discrepancy has a different cause. The writer's dynamic point
basis uses the actual saved binary64 anchor magnitude. The independent reference
uses the supremum of an expanded interval anchor. At this release, their L1
position extents differ by

```
11570523268759427 / 5070602400912917605986812821504 m.
```

Multiplication by `2^-53` contributes to the force reanchor's position allowance
and again to the final point's exposure allowance. This explains the residual
without an omitted source phase. The raw baseline and corrected-cut observer
reports, source identities, rejected artifacts and complete failing test log are
retained separately. The frozen P16 acceptance source is unchanged.

This final-point correction neither fixes nor suppresses that dynamic-enclosure
issue. A future correction needs a derived position/velocity/angular-velocity
envelope through release and reanchor, including finite interval rounding.
Changing the independent minimum, adding an unproved epsilon, or relabeling the
failed complete export as a pass would not establish that proof.
