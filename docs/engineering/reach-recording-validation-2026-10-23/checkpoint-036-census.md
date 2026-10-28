# Checkpoint 036: full P11 quaternion failure census

## Result

The unchanged full P11 request fails while comparing the **right forearm** at
key **36**, exact time **36/25 seconds**. The refused operation is the addition
of the completed z-component error to the completed w-component error in the
independent quaternion L1 distance. The product did not execute that addition.

The post-failure capture is neutral against the separately executed normal
request: both consume **100,001 shared operations / 93,277 reach operations**,
with the same **279-category map**, **256 work-cache entries**, **171 independent
arithmetic-cache entries after cleanup**, exact request settings and limits,
source units/revision, exception/diagnostic and all **18 product traceback
frames**. Their single external driver frame is identified and also matches.
Both complete raw tracebacks are byte-identical. All four source inventories
are identical: **1,986 files / 442,072,108 bytes**.

There is **no matching completed whole quaternion comparison** among the
available records. One identical charged scalar conversion is reconstructed:
both forearms decode their same supplied w component to `442671/524288`.
However, the existing proof record does not retain that decoded Fraction as
an independently reusable field. This observation selects no runtime change
and establishes no complete-request saving.

## Source and experiment identity

| Item | Exact identity |
| --- | --- |
| Executed held candidate | `4ca73909f861fe4bef9694787473621c1d21c140` |
| Complete execution tree | `87c949b238055af1ce368c694e1d5683c8aeacde` |
| Publication parent | `d485c9bc81a5bdc8500c93d70eeb6b738f1fba97` |
| Publication-parent tree | `c146832a29d4d5be738ddd0128c88186cdef36b9` |
| Centered implementation blob | `e1017c79786066e263bdc7877e318003cb61bbc0` |
| Independent comparison blob | `f91cdbc43fe7134c4b11c73bd43cd033bf9d16ea` |
| External request driver SHA-256 | `a6c788e30c0d70c42c3e2345c2b721eb03ec38a0bbcac2402e72fe9b96127815` |
| External pair runner SHA-256 | `b14d8ba16cb546f5d2065d6d28edf784400f067e3d23ad7aa4e5f3490566bd07` |
| Before/after inventory SHA-256, both requests | `09a024b2c1064f27326d4f3496ec9f1b9b94fadba4c326be0008bdc6c8b5736c` |
| Accepted reach runtime, unchanged | `d2f0088c4f3c1f570630334804a5a8f78e0105ac` |

The candidate checkout was clean, with every tracked file checked against its
original Git blob and mode. It was separate from both the publication branch
and the external drivers/receipts. Execution used CPython **3.12.14** on Linux;
the request receipts also identify the interpreter executable bytes.

The frozen plan executes exactly one control, followed by exactly one capture.
Both use the original P11 source manifest and program revision, end `3`, integer
fps `1`, helpers `false`, tolerances `0.001 m`, `0.001 rad` and `1e-6 s`. Limits
remain **100,000 shared operations, 30,000 ms, 32,768 operand bits and 256
numerical-cache entries**. The category metadata bound remains separate.
The 180-second outer command allowance changes no product limit.

Both modes use the same source loading, constructed compilation and export
statements. No profiler, trace hook, work callback, arithmetic wrapper,
observer replacement or participating reader replacement is installed. The
only mode-dependent observation starts after the original exception has
reached the external driver. The original error remains a failed request.

The request driver has fixed bounds on frame count, native shape/depth,
container size, scalar width, identity tokens and output bytes. It reads
whitelisted frame locals and native stored fields; it does not dump arbitrary
object graphs or invoke foreign getters or representation methods. A bound
or metadata failure would retain its own failed receipt rather than silently
truncate the census. The executed capture has no such failure.

## Observed failure and retained operands

The source frame is `rig.arms["right"].forearm.frame`, carrier **7**. It lies
in source phase **0**, side `after`, spanning **0 to 2 seconds**. The request
clock is exact `36/25`; the preceding key is `7/5`. The retained plan/context
and history-state relationships agree. The source frame was an actual target
of the prepared plans.

The supplied quaternion uses XYZW ordering. Its values retain these exact
binary64 representations:

| Component | Binary64 bits | Hexadecimal floating-point value |
| --- | --- | --- |
| x | `0000000000000000` | `0x0.0p+0` |
| y | `0000000000000000` | `0x0.0p+0` |
| z | `bfe1257e40000000` | `-0x1.1257e40000000p-1` |
| w | `3feb04bc00000000` | `0x1.b04bc00000000p-1` |

The sign-selected expected quaternion is:

```text
x = 0
y = 0
z = -91166205027556694244232386454111688115 / 2^127
w = 143654952473635747543247008573090864969 / 2^127
```

The orientation radius is exactly `2^-104`. The current rotation claim is an
exact native float with bits `3e8c899b26ffe622`, hexadecimal value
`0x1.c899b26ffe622p-23` (approximately `2.1262112026559046e-7`).

The retained inner `l1` frame identifies the fourth component, w. Its decoded
`value` is `442671/524288`. Its `point` is the expected w Fraction above. The
completed absolute error is:

```text
error = 192893670028579450211420954807 / 2^127
```

The accumulated distance before the refused addition is the completed
z-component error:

```text
distance = 1237730583695813100463575755341 / 2^127
```

The original `_Bounds.add(distance, error)` requests another shared operation.
The construction budget refuses at **100,001**, before the scalar addition,
its prospective-width check and its result. The two arguments are retained;
no completed addition result, complete current quaternion bound or successful
claim check follows from this failure. Offline arithmetic descriptions remain
separate from product execution.

## Available completed comparisons and reuse decisions

The geometry and observed carrier order is `0` through `19`. Before the
current failure, the result-map order is:

```text
0, 2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 1, 4
```

The centered pending list was `1, 4, 7, 17, 18, 19`. Carriers 1 and 4 completed;
carrier 7 is in progress. Carriers 17–19 remain after it. No earlier centered
comparison in this pending list returned the optional fallback result. The
full pending list remains in the failing frame; it is not an unvisited list.

There are **16 completed comparison records**, of which **two contain centered
orientation proofs**. The other 14 supply no such proof. They must not be
described as 16 available orientation proofs.

The offline reconstruction follows `reused()` in literal source order: proof
shape, payload shape, seal, typed actual quaternion values, expected center,
radius, claim type, claim value, operand domain, completed error type and
magnitude type. It does not invoke the live helper. Checks after a first
mismatch are explanatory comparisons, not claims that the original predicate
evaluated them.

| Completed carrier | Available centered orientation proof | First rejecting condition |
| --- | --- | --- |
| 0, 2, 3, 5, 6, 8–16 | None | Proof unavailable |
| 1, head | Present; exact seal verifies | Actual quaternion differs |
| 4, left forearm | Present; exact seal verifies | Actual quaternion differs |

The left forearm has the opposite z component and the same supplied w
component. Its source center is **not an exact mirror** of the right forearm's
center. With both centers expressed on the `2^-128` grid:

```text
right_expected_z + left_expected_z = -97 * 2^-128
right_expected_w - left_expected_w = -40 * 2^-128
```

The left forearm's radius, typed rotation claim and operand domain do match
the current values. Therefore a different claim is **not** the reason reuse
declines. Equal geometry or near-mirrored centers cannot replace the exact
operand predicate. The completed proof errors independently reconstruct from
their own captured operands and radii, but neither is the same complete
calculation as the current comparison.

The source vector predicate uses exact component types and Python value
equality, not bit equality. The census preserves both, including signed-zero
bits, and does not silently strengthen or weaken that predicate.

## Exact scalar repetition and its limit

The left forearm's completed comparison and the current right forearm both
decode the native float w bits `3feb04bc00000000` to `442671/524288`. For the
left forearm, the earlier result order and unavailable/different prior proofs
establish the ordinary `l1` route by source reconstruction. For the right
forearm, the completed decoded value is directly retained in the failing
frame. Its charge has already succeeded before the final addition refuses.

This is one exact repeated charged conversion. Zero x/y components take
existing shortcuts and supply no duplicated decode, subtraction or addition
charges. The unequal exact w centers prevent treating the w subtraction/error
as repeated; the unequal mirrored z centers also prevent transferring the
whole accumulated error.

The existing seven-field orientation payload retains raw quaternion floats,
the expected center, radius, typed claim, total completed error, magnitude
placeholder and domain. It does **not** retain each decoded Fraction. Thus
the observation is not an immediately reusable result in the current payload.
Any future proposal must first account for retaining and admitting such
operands, all callbacks/guards, publication and retrieval costs, and fallback
behavior. If those costs consume the one skipped decode charge, there is no
net saving for this occurrence.

## Cleanup and remaining uncertainty

The original error unwinds through `_SourceBatch.__exit__`. The census sees
`active=false`, `reference._recording_batch=None`, an empty cursor ledger,
88 retained receipts and two retained plans. The independent arithmetic cache
has **171 entries after cleanup**. These mutable values do not establish their
exact refusal-time state or how many cursor entries cleanup removed.

The detached Fraction operands in the failing comparison/`l1` frames retain
their exact values. Both source-plan context/state links and saved owner
relationships are recorded separately. Raw process addresses are not used as
cross-run identities.

The completed `reused()` calls have already returned and their individual
frames are absent. Their first-mismatch decisions are reconstructed from the
captured current operands, seals and ordered completed records. No evicted or
unretained earlier proof is inferred. This census does not estimate remaining
complete-request cost, identify a global bottleneck, execute an unvisited tail,
or establish elapsed-time neutrality.

## Disposition and evidence

The bounded diagnostic is complete. No runtime, test, fixture, limit, oracle,
workflow or shared overview changed. The candidate remains held in draft
PR #32, and accepted runtime `d2f0088c` is unchanged. Checkpoint035's original
recording result remains **24/28**, with P11/P16/P23/L03 blocked. Its 3,093-test
regression and seven local checks remain prior evidence for their exact source;
this diagnostic does not rerun them or extend release acceptance.

[The checkpoint](checkpoint-036.json) identifies the closed executions, archive
parts, manifest and analysis. [The next scope](checkpoint-036-next-scope.json)
is limited to a source/control-flow and complete-cost feasibility derivation
for repeated same-key quaternion component decoding. An implementation is not
selected by this census. [HANDOFF-036](HANDOFF-036.md) supplies the continuation
instructions and remaining gates.
