# C048 independent final source and claim review

**The four reviewed C048 proposal/handoff files are mathematically consistent with the inspected source and support the two narrowly stated NO-GO conclusions. No positive candidate saving or runtime acceptance is established. Final documentation and publication validation remain root's pending work.**

Reviewer: `/root/bundle_audit`. Prior roles were the portable-bundle integrity audit and the fresh retained-data audit in C048. This reviewer did not propose the affine equation or author the root proposal. It read the numerical and cost reviews; this is a separate review, not a blind one. Work was limited to source, text, JSON, hashes and link targets. No OntoKin import, numerical candidate replay, product/test execution, archive operation, archived-script execution or GitHub mutation occurred.

## Mathematical and charge findings

For genuine factorials, `F=(2D+1)!`, `f_i=(2i+1)!`, `Q=F*2^(2eD)`, and `L=2^bit_length(Q)`, the original packed coefficient is

`C_i=(F/f_i)*2^(2e(D-i))*(L+2i+1)`.

Because `f_i` divides F, multiplication can precede that exact division. Defining `N_i=F*(L+2i+1)` gives `N_i-N_(i-1)=2F`, and then `C_i=(N_i/f_i)*2^(2e(D-i))`. Forming the final coefficient directly as `L+2D+1` preserves its exact value. The original degree search, stopping comparison, Horner evaluation, lane extraction and remainder can remain unchanged.

The original construction has two setup shifts, three index-0 operations, four per interior, and two at the last index: `4D+3`. Lookup/publication make `4D+5` for a fixed-domain complete miss. The proposed affine schedule has six initial operations, three per interior, and the final add: `3D+4` construction and `3D+6` complete miss before new admission. The gross difference is `D-1`. These formulas include zero-distance shifts when `e=0` and apply to the stated positive-degree genuine-factorial domain.

The five observed completed degrees give `6+7+12+16+15=56` gross arithmetic operations. Before the corresponding index-7 division, the original count is `2+3+6*4=29`; the affine schedule gives `6+6*3+1=25`. Thus four gross operations precede that corresponding point. The full degree-14 difference of thirteen concerns an unexecuted completion. The documents correctly avoid treating these numbers as measured request savings.

## Fixed-domain operand proof

Let `b=bit_length(F)`, `s=2eD`, and `q=b+s`. For `D>=1`, `2i+1<=2D+1<=F<L`, so `bit_length(L+2i+1)=q+1`. The initial numerator multiply needs at most `b+q+1` prospective bits; a recurrence addition needs at most `b+q+2`. Dividing cannot increase the positive numerator's width. Its subsequent shift needs at most `b+q+1+s=2q+1`. The final add needs `q+2`, and delta needs `b+1`. Shift-count operand widths also fit this bound. Therefore `2q+2` covers every new prospective width.

With `H=2*limit+1`, the factorial bound gives `b<=H*bit_length(H)`. Since `2D<=H-1`, `q<=H*bit_length(H)+(H-1)e=W-e-1`, hence also `q<=W`. The unchanged caller admission `max(2W+2e+5,W+bits+11)<=operand_limit` dominates `2q+2`. The proof is sound for the stated fixed native domain. It cannot replace any actual prospective guard or survive an unreviewed later cap change. The proposal makes those limitations explicit.

## Authority and scope of rejection

The division-order identity is not valid for arbitrary cached integer tuples. For the reviewers' symbolic `F=120`, interior divisor 7, and `L+3=131`, the original floor order gives `17*131=2227`, whereas the affine floor order gives `floor(15720/7)=2245`. Native tuple/integer types therefore do not prove the needed factorial origin. This is a symbolic counterexample, not an executed corrupt-cache request or an allegation about C047.

The source has no factorial-origin receipt on `_series_factorials` cache hits. The current centered/product checks do not pin all four series methods or establish that provenance. At the actual nonadvance target, `_orientation` calls `guard.original(body.direct, clock)`. `_Guard.original` installs its non-null `observed` closure for that call. A screen requiring an absent `_recording_after_tick` excludes this target. This is a source-bound conclusion from the retained failure route, not an inference from restored boundary observers.

The two rejection bounds are properly limited:

- The literal endpoint design retains two original charged callback/guard checkpoints, consuming its two gross arithmetic operations before any screening.
- The concrete affine design adds one guarded divisibility operation for each of `D-1` interiors, consuming its `D-1` gross arithmetic opportunity before other nonnegative admission/storage costs.

Neither bound proves that every native admission or factory-origin design is impossible. Neither establishes a safe generic implementation. The documents preserve both distinctions, require a complete future ledger, and keep the already resident factorial table's eligibility unresolved.

## Metadata and publication limits

[The accompanying metadata result](result.json) records seven passing grouped checks over eighteen stable inputs. The two runtime source files and two contract files match the recorded C047 Git tree. All three prior review files match their review-index hashes. All **eleven relative Markdown links and twelve explicit structured path references** resolve against the recorded base tree plus the twenty-two current planned additions. There are no relative link fragments requiring anchor checks. External URLs were not fetched, and this scoped check is not the repository documentation checker.

One publication-status wording issue was reported to root: the reviewed handoff anticipates a recorded incomplete/failed documentation-checker gate, while its validation JSON is still pending. Root acknowledged that the actual checker command, exit and output will be recorded before publication. If that command does not run, the wording must instead say not run/unverified. This review certifies no full documentation pass and no complete checkout; the twelve historical archive inputs are a reported recovery limitation.

Root must bind final validation, any subsequent edits, immutable publication identity and ownership closure separately. Original28 remains 24/28; C035 remains held. There is no selected runtime candidate, successful L03 export, timing result, main integration or release acceptance.
