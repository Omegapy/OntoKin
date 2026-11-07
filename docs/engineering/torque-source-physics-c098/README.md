# C098 · Frozen torque physics at the tested product revision

OntoKin reproduced all 204 expected torque-state observations across 31 source programs at product commit `fab1137e7b3e24d656ed4ba7cfd55935b6b2f241`. The programs exercise a spinning sphere under applied torque, including braking, cancellation, numerical underflow, and a change of motion at release. The 74 before-boundary and 130 after-boundary observations use the original clocks, source programs, budgets and numerical tolerances. Each returned state contained the target object. Every saved record matched the original C092 candidate03 record after excluding the measured elapsed time. [Frozen physics cases](../../language-design/torque-v0.1/freeze/physics-cases.json)

| Verification role | Result on CPython 3.12.14 |
| --- | --- |
| Source runtime | 31 programs, 204 observation points. A separate readback of the returned states checked 2,652 exact fields, 663 binary64 encodings and 408 error constraints. |
| Reference reader | 14,172 recursive comparisons passed on the same 204 points. The count includes container and scalar comparisons. An independent authoring script reproduced the expected state table byte for byte. |
| Seven numerical cases | All 60 original assertions passed. The seven generated test programs and their assertion results matched C092. Four supplemental checks confirmed that the public error bounds covered the frozen speed and angle discrepancies for the rounding and underflow cases. |

The reference reader reconstructs motion history separately from the runtime evaluator. It uses the same source loader, budget admission and construction compiler. The standalone mathematical input checker uses only the Python standard library and passed 2,906 assertions, including checks relating to 128 reference samples. These roles share fixtures and their counts describe different units. [Expected states](../../language-design/torque-v0.1/freeze/state-expectations.json) · [Numerical fixtures](../../language-design/torque-v0.1/freeze/numerical-cases.json)

The intact C092 evidence supplied the original seven-case driver. Two of its input programs adapt literals in the base sources. The replay changed only the old checkout path and revision guard. For the offset marker, the driver checks exact analytic chord terms and requires the full producer and reader bounds to cover them. For the non-dyadic zero crossing, it checks that the speed reaches zero at exactly one third of a second and that this instant adds no semantic event. [C092 implementation record](../canonical-spin-amendment-2026-11-03-c092/README.md)

## Next checkpoint

Repeat the canonical spin history and origin regressions, followed by the frozen direct domain and refusal cases, at the same product revision. Record each original input, budget, diagnostic and boundary side. Preserve remaining stream comparisons and the four missing predecessor GLBs as explicit obligations. The original fixed-budget export failures, complete one-byte GLB read, interpreter and release checks still have their own gates. The unified C098 handoff contains both old and new receipts and the complete C097 ZIP. [Previous checkpoint](../torque-hostile-c097/README.md) · [Draft PR 90](https://github.com/Omegapy/OntoKin/pull/90)
