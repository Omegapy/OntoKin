# Captured clock identities and fixed hinge inputs

This bounded producer candidate starts from `1e1b5aaec48bb9e36e79ac173964725392fb9e9e`.
It changes only the captured recording producer. The authoritative source,
independent supplied-byte reader, sampling, numerical tolerances and release
limits are unchanged. The earlier identity-placement candidate remains in the
base.

## Exact root clocks

The source root clock is `saved_elapsed + (time - running_since)`. Its existing
arithmetic uses exact rational subtraction and addition with prospective
numerator/denominator limits. The identities `time - 0 = time` and
`0 + offset = offset` therefore preserve the exact value, but omitting a call
is safe only when its prospective finite-bound check is already established.

The optional path requires all three inputs to be native `Fraction` values
with native integer fields, positive denominators and at most 1,024 bits per
field, under the unchanged 32,768-bit cap. The ordinary subtraction has
prospective width at most 2,049 bits. Its result and the possible subsequent
addition also fit the full cap: even treating all resulting fields at their
prospective 2,049-bit width gives an addition bound of at most 3,074 bits.
This includes the two zero identities. No tolerance or floating-point
approximation enters this proof.

An unsupported scalar, a larger field or a pre-existing narrower cap retains
the original expression. A remaining subtraction still invokes the original
helper and callback. If that callback narrows the cap, the subsequent zero-add
also invokes the original helper, preserving its prospective failure. A
paused root keeps its existing guard and value behavior. Every operation
actually performed retains its original charge and callback; no accounting
constant is reduced.

At source capture, the two native clock leaves are copied from their integer
fields after the current source-witness comparison and before another
callback. The optional clock path copies all three admitted operands again
before its first remaining callback. A mutation through a live source or
clock alias cannot change those arithmetic operands. The original final
source receipt still rejects a persistent change before cursor publication.

## Unclaimed fixed hinges

A captured hinge with no coordinate claim has one exact source coordinate
throughout its captured phase. Its existing path already chooses the direct
fixed-axis kernel rather than a history cursor. Repeated samples nevertheless
decode that coordinate, admit/decode the same axis and construct an unused
cursor key before reaching the existing pure axis-projection cache.

The new captured descriptor contains the exact source coordinate and axis,
their native integer seal, and their source-arithmetic/work owners. It stores
no rotation or numeric result. The descriptor accepts only a bounded native
source scalar tuple and the already supported Cartesian-axis domain. It uses
the original `rational` and `_recording_vector` helpers at capture, then
detaches their returned `Fraction` leaves from both source and cache owners.
Raw source types and binary64 zero signs remain in the unchanged complete
source witness. The descriptor's canonical exact operands match those the
original helpers supplied to the kernel.

The capture traversal distinguishes a structural lookup/type failure from the
exact exception retained as `work.callback_error`. A one-shot caller refusal
from the new charged capture helpers propagates unchanged, including a
`TypeError`, `KeyError`, `AttributeError` or `IndexError`; it cannot be swallowed
as optional structural fallback. Independent code review identified this
boundary before execution, and the first unexecuted cut `05c902b1` is retained.

Every use admits the original native domain, context/path/step bounds, owner
identity, descriptor field identity and integer seal. Fresh arithmetic copies
are made before callbacks. The axis and coordinate retain their ordinary
finite guards. The actual rotation still goes through `_axis_rotation`, with
the same complete key, projection, source kernel and existing 256-entry LRU.
Eviction therefore reruns the original kernel. The descriptor cannot extend
the lifetime of a computed rotation beyond that cache.

Only an absent claim gets this path. An active affine law, including one with
equal endpoints, retains its existing endpoint and sample-clock work. Native
child poses for eligible fixed hinges are detached before the new capture
callbacks. The original final graph receipt still checks every actual source
row, owner, claim, child placement and topology edge. A callback failure or a
failed final admission cannot publish a partial group of phase cursors.

## Evidence status

The first focused attempt on `3b7c3117619ef8e6d9671f7c1342239de8d19d33`,
tree `13396b1c4ad4d088df32029e33a2dd0a63cd49f8`, is preserved as
`evidence/captured-inputs-focused-001`: 18 of 19 methods passed, with stable
tracked inputs, no assertion failure and one test harness error. The warm-cache
test indexed a promotion counter absent from its cold setup. The separate
test-only correction treats the absent initial counter as zero and retains the
same expected increase of one. No production correction followed this run;
the combined cohort and full original P16 have not run on this candidate.

Its dedicated module is
`tests/test_reach_recording_captured_inputs.py`, with 19 methods covering:

- Exact clock equality, original prospective failures and a cap change between
  subtraction and a zero-add that would require one extra bit.
- Copied live clock/source operands, transient descriptor mutation and final
  persistent-source rejection.
- All supported Cartesian axes, native scalar types, signed zeros, unsupported
  inputs, original callback-exception identity and unchanged cache eviction.
- Actual original P16 phase native bits and numerical allowances, plus complete
  source-to-GLB prefix bytes and the independent validation report.

The preserved neutral P16 trace at `e293d27f` observed 153 root-pose evaluations,
each with both a move and a spin clock. Both clocks had zero saved elapsed and
zero running-since throughout those samples. Eliminating those four exact
identity operations projects a saving of 612 operations. The same trace
observed 98 constant-hinge evaluations after reach completion. Their repeated
coordinate/axis decoding and unused cursor domain suggest up to approximately
588 removed operations before the new bounded capture preparation. These are
projections from an earlier cut, not measured candidate savings; source
planning, cache effects and the unchanged full recording must be measured on
the exact committed candidate.

The original 100,000-operation budget and all five remaining recording
failures remain the acceptance baseline until a fresh complete run establishes
otherwise. This candidate does not establish Agent delivery, full regression,
Python compatibility, independent external verification or browser acceptance.

## Executed worker validation

Exact source `d891f8c5264cfd7b96430e162e99f43712b360d0`, tree `95ac09694f689f8e0957d6bfe2867d2bf511e5f5`, passed **19/19** dedicated methods and **173/173** related methods with stable inputs and no failures, errors or skips. The unchanged original P16 recording still exhausts the 100,000-operation cap at100001. These separate cohorts are not a complete regression claim. The initial focused attempt at `3b7c311` passed18 methods and exposed an absent-counter test-harness error; its raw log remains preserved. The one assertion was corrected without changing production or the expected cache promotion. Root integration and its complete original28 run retain their separate source identities.
