# C091 exact-axis completeness review

## Finding

**Eligible fixed-precision spin plans can change an exposed canonical off-axis zero. The current producer can select those different plans for the same source and requested clock according to earlier legal public work. A sound, complete source-and-clock-only exact-axis reader therefore cannot match every current producer execution.**

This bounded review made no production edits, no remote calls, and no changes to frozen expectations. The reviewed repository head is `e8e1f50`; complete commit, file hashes, interpreter, budgets, commands, and observed outcomes are retained in the JSON reports. The two uncommitted exact-recipe modules reviewed here are preserved as `reviewed_torque_axis_exact.py` and `reviewed_torque_axis_reference.py`. They were not integrated into `torque_reference.py` at the observed checkpoint.

The adopted requirements are SPECIFICATION.md section 3 (exactly zero orthogonal canonical components), sections 4–5 (ordered incoming release/torque and inherited rotation semantics), and RECORDING.md section 9 (source reconstruction without producer simulator state/planning tables). Both adopted documents are individually hashed in the reports.

## Independent exact counterexample

Let `v` contain the binary64 source scalars `(0.6, 0.8, 0)`. A prescribed parent spins at `v`. One hinge has the same canonical axis, starts at coordinate 1 radian, and tweens to zero over one second. Its incoming rate at the one-second boundary is exactly -1 rad/s. Thus the child has identity local rotation and canonical angular velocity

`RN96(v + RN96(R(q) * (-v)))`.

Here `q` is the inherited spin quaternion at one second, `R` is the exact homogeneous quaternion matrix, and `RN96` is the fixed 96-bit nearest-even grid. Final release exposure is binary64. The source hinge-axis normalization retains the authored binary64 `(0.6, 0.8, 0)` unchanged; the actual compiled axis is included in the controls.

With `G = 2^96`, independently reconstructed quaternion numerators are:

| Plan precision | q.w × G | q.x × G | q.y × G | q.z × G |
| --- | --- | --- | --- | --- |
| 96 | 69529253833134890245331416652 | 22790402691613502847048901949 | 30387203588818006607446292455 | 0 |
| 192, 384, 768, 1536 | 69529253833134890245331416652 | 22790402691613502847048901949 | 30387203588818006607446292456 | 0 |

The full source transfer gives:

| Plan precision | Released canonical omega | Torque about world_x |
| --- | --- | --- |
| 96 | `(0, 0, 0)` | Admitted |
| 192, 384, 768, 1536 | `(0, 0, 2^-96)` | Refused |

`2^-96` is exactly representable in binary64 (`0x1.0000000000000p-96`). This is an exact canonical distinction, not an uncertainty interval or tolerance. All five plans meet their finite error guard at elapsed one second. At horizon 16384 seconds, the 96-bit plan fails its argument-error guard and 192 is the first eligible precision.

`review_axis_completeness.py` evaluates these operations with the independent exact recipe implementation and guarded rational arithmetic before importing any producer evaluator APIs. Its `report.json` retains all candidate components, eligibility outcomes, bounded work count, and source hashes. `spin_rotation` returns `None` on these operands because the full candidates disagree. Testing only the final off-axis predicate instead of full quaternion equality still cannot resolve this example: that predicate itself differs.

## Two distinct runtime observations

### Source-contained earlier helper event

`no_helper.ok` starts the target spin and hinge tween at 16384 seconds, then releases the child and applies world_x torque at 16385 seconds. Ordinary native evaluation accepts, observes zero released angular velocity, and ends with a registered 96-bit plan of horizon 1.

`helper_force.ok` additionally gives the unrelated dynamic sibling the same spin vector and applies a genuine COM force to it at 16384 seconds. That inherited force transition requires a source angular bound at the helper's long elapsed time. Its registration retains a 192-bit plan of horizon 16384 for the shared omega key. Ordinary evaluation now refuses the target torque with `incoming_axis`. A valid before-side observation exposes `(0, 0, 2^-96)` on the target. Direct, segmented, and before-side controls all reproduce the refusal. Neither source uses plan injection or an arbitrary phase-bounds call.

These are **different programs**. They prove that looking only at the local spin recipe and its elapsed time cannot recover the producer's selected plan. The independent reader currently refuses both; the no-helper refusal is a concrete accepted-source completeness gap.

### Same source, earlier public request using the same admitted work

`same_source_history.ok` moves the target start to zero and its release/torque to one second, while the helper's force remains at 16384 seconds. The immutable source is identical in both paths:

- Entry SHA-256: `8d02d0fb3ca61f275bb85f019a45451c34e89925e488e7d2236432b6085fc27e`.
- Program revision: `sha256:a2e3fb4fc44349355ede9480cc35f5d699663de084e5bbbcd010d143aedb3b1e`.

The public API controls are:

| Path | Calls using one compiler model and its original admitted work | Result at one second | Cumulative operations |
| --- | --- | --- | --- |
| Fresh | `evaluate_prefix(model, "1", work=work)` | Accepted, after; omega `(0, 0, 0)` | 16,970 |
| Reused | `evaluate_prefix(model, "16384", work=work)` succeeds, immediately followed by `evaluate_prefix(model, "1", work=work)` | Refused `OKL-E-FRAME`, `incoming_axis`; valid prefix is one-second before with omega `(0, 0, 2^-96)` | 40,967 |

Both paths stay inside the unchanged 100,000-operation / 30,000-ms admitted defaults. **No cache lookup, plan inspection, callback replacement, or mutation occurs between the warming request and the second request.** The script performs the two public calls adjacently; final plan observations occur only after both have returned. The full result is sealed in `shared_work_report.json`, whose source hashes remained unchanged throughout execution.

This is stronger than the different-program observation: a function of the immutable source and requested clock has the same inputs in both paths but would have to return different exact admission answers. Replaying source semantic horizons alone cannot recover a prior completed request's shared numerical-cache history.

## Recommendation and completeness boundary

Keep the all-candidates or Boolean-support fallback explicitly conservative. The currently unresolved case must remain a visible incompleteness, and an interval merely containing zero must never become an exact-zero witness. Choosing 96, choosing the highest precision, or accepting if any candidate happens to yield zero would each disagree with one observed canonical execution. Carrying a finite set through the downstream arithmetic can prove additional unanimous cases, but this mixed case remains unresolved.

A sound and complete source-only solution first needs **one deterministic canonical spin calculation independent of retained request plans and cache eviction**. A concrete option is to specify the first certifying precision from the fixed schedule as a pure function of immutable omega and actual absolute elapsed time, while allowing an interval plan to certify a larger horizon without changing the sampled components. The producer and the independent reader can then separately implement that exact finite rule and the downstream 96-bit grid / binary64 operations. This requires a reviewed correction or versioned semantic decision under the inherited-preservation rules; this review does not choose or implement it.

An alternative would make the full execution/planning history an identified semantic input and independently replay every relevant plan registration and cache lifetime. That is a substantially different contract from the adopted source-only reference and remains sensitive to legitimate callback/work effects. Reading or trusting a producer plan is expressly not the independent solution.

After the deterministic rule is established, retain exact source recipe DAGs through action completion, release materialization, products, transported angular sums, and ordered impulses. Use Boolean zeros as a fast proof and exact directed arithmetic where cancellation matters. Then test the sealed witness under fresh/reused work, supported cache capacities, segmentation, and supplied-byte reconstruction. Do not alter the adopted frozen outcomes to conceal the issue.

No export or complete-release acceptance is claimed by this bounded review. Its evidence consists of source construction, public/native evaluation controls, and an independent exact mathematical counterexample.

## Reproduction

From the reviewed repository, with a fresh output directory already containing a copy of `no_helper.ok` for the second script:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 review_axis_completeness.py ROOT FRESH_OUT
PYTHONDONTWRITEBYTECODE=1 python3 review_shared_work_history.py ROOT FRESH_OUT
```

The first script writes `no_helper.ok`; running the scripts in that order supplies the second script's input. Preserve this sealed directory and use a new output directory for later implementation checks. `MANIFEST.json` binds every retained file except itself.
