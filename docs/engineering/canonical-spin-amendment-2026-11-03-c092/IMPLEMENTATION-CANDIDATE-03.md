# C092 implementation candidate 03 — callback ownership, acceptance blocked

This candidate retains the separately adopted
`OK-LANG-022-CANONICAL-SPIN/0.1.0` arithmetic and independent reader. It repairs
the callback ownership failures found in candidate
`8762e740abd5e8175d015fb5c15b36fe0fbcbff6`. It is a reviewable development
checkpoint, not permission to integrate or a completed torque release.

## Actual changes

The .22 producer admits raw runtime attribute resolution before reading
instance storage. Its immutable receipt covers the effective native simulator
method graph, including direct recording dispatch. An original callback cannot
install a foreign storage descriptor, replace a helper method, or change a
guard entry function and execute that replacement before the ownership refusal.
The request guard captures its entry functions at module binding, before source
preflight callbacks can replace public aliases. The original callback, original
clock, consumed work, failure atomicity and exception precedence remain intact.

The completed guard uses native identity comparisons over strongly retained
objects. Shared namespace checks are deduplicated; present and absent members
are admitted separately. Repeated scans are removed only across intervals
containing no callback. The public admission still checks the complete graph;
the private post-entry body follows the same already-completed entry check.
Actual CPython 3.11.17, 3.12.14 and 3.13.16 probes establish that the native
function type and its globals, closure and builtins slots are read-only.
Code, defaults, keyword defaults and all previously checked mutable contents
remain freshly checked. The 84 interpreter probes are a narrow invariant
proof, not the complete interpreter test matrix.

The private immutable receipt tuples and request closure are trusted ownership
metadata. This mechanism does not claim to sandbox arbitrary manipulation of
the Python interpreter or replacement of that private owner state.

## Controlled correctness results before this publication

The final exact files passed all 29 focused regressions and all 20 original
callback tests. The independent recording reviewer replayed all 31 retained
descriptor, guard-code and direct-recording probes: every attempted foreign
entry refused before execution, and successful controls remained successful.
Earlier failed probes, harness corrections and slower repairs remain retained.

Final product file SHA-256 values:

| File | SHA-256 |
| --- | --- |
| `ontokin/torque_runtime.py` | `16dee91922f4f7570d517bb787b836a099020d69db06a34ae9b101025d97e0c6` |
| `ontokin/torque_canonical_spin.py` | `79e8991b84164f42cc97ceb126078eada19e6c6da8b2e5e1c9c3d56cd2a5e62b` |
| `tests/test_torque_canonical_spin_c092.py` | `6f9ca69c513c732834b8d4a4972198abc197d3bfe9d047f392602904f2fe9f44` |

## Original A08 allocation remains a blocker

The actual frozen Agent A08 source and request still fail their original
1,000,000-operation / 30,000-ms export allocation. The final uninstrumented
attempt reached **189,856 operations / 30,000.31 ms**, then returned
`OKL-E-RESOURCE`, `budget_reason=execution_deadline_exceeded`, at
`recording_export_readback`. No artifact was committed. Complete byte retrieval
at 1, 17 and 65,536 bytes therefore remains unexecuted for this candidate.

The two preceding ownership repairs failed at 58,613 and 107,112 operations
under the same original deadline. Their records remain failed. Candidate02's
earlier successful A08 export at 452,617 operations / 26,676.6 ms is historical
evidence for its less complete guard, not acceptance of this candidate.
The third draft's separate instrumented profile reached 130,884 operations;
profiling timings are diagnostic evidence only. The profile identifies repeated
ownership scans as the dominant remaining cost.

No frozen source, expectation, numerical tolerance, resource ceiling, callback
frequency, original work charge, cache capacity or protected predecessor module
was changed to obtain a passing result. Further optimization must preserve the
adopted meaning and all current ownership refusals. Raising an old allocation
or relabeling a prefix is not a recovery of this gate.

## Remaining verification and next action

After exact publication, run the independent original source/reference,
numerical/resource, production/destination and applicable inherited checks on
this immutable candidate. Record each executed result and each blocked or
unexecuted gate in the closing handoff. Those checks do not erase the A08
failure. Complete torque acceptance and main integration remain blocked.

The next implementation task is a separately reviewed reduction of guard cost
under the same original request and allocation. Preserve the current successful
mutation controls, the complete point rule and all failed performance attempts;
then rerun the full acceptance sequence on the resulting immutable candidate.
