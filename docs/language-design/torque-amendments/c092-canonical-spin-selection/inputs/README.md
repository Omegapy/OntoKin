# Independent C092 source and numerical additions

These inputs were authored and evaluated before any C092 producer or reader
implementation. They supplement, and do not replace, the 399-file C090 freeze
or the three separately reviewed C091 overlays. The final authority manifest
must bind this directory unchanged before implementation.

`EXPECTED-SELECTOR-RESULTS.json` comes from `derive_expectations.py`, the retained
C091 independent guarded kernel `reviewed_torque_axis_exact.py`, and the
unchanged independent `reach_reference._Arithmetic`. No producer numerical
kernel, runtime evaluator, producer plan, or output artifact supplies its
expected values. `DERIVATION-INPUTS.json` binds the original arithmetic/source
bytes. The calculation uses 11,322 bounded scalar steps, below its independently
specified 100,000-step cap, and retains the 32,768-bit operand ceiling.

The old WIP kernel's all-eligible-plan `spin_rotation` is not the new selector
and is never called to establish C092 results. The derivation uses its separate
sqrt, Machin-pi, polynomial, reduction, homogeneous rotation, grid-rounding and
binary64 primitives. It implements the proposed ordered guard search as
mathematical evidence, not as a product module.

## What is fixed here

- Thirty exact transition cases cover below, at and above each of the five
  stage boundaries, with both elapsed signs. The last stage's equality/above
  points have a finite selector refusal. The five exact pi enclosures prove
  their positive range below 22/7, supporting the uniform reduction theorem.
- All five original history-witness candidate quaternions and angular vectors
  are independently reconstructed. The proposed selector chooses stage 96 at
  elapsed one and exact zero angular velocity; an unrelated long request cannot
  choose another stage for that point.
- Stationary/zero-elapsed cases retain the complete anchor, not merely its
  public quaternion. Nearest-even ties, exact quaternion permutations, a
  nonzero parallel cross-product cancellation, and signed true off-axis
  components have explicit mathematical expectations.
- The six unchanged C3 source literals have a stage/stationary proof. The
  spinning cases use omega=(0,0,0.5) over at most three seconds and certify at
  stage 96 throughout; the other cases have zero canonical angular speed.
- The zero-force source-origin case uses omega=(0,0,0.25), a zero force from
  0.5 through 0.75 seconds, and a zero world-Z torque latch at one second.
  Its rotation keeps source origin zero. Incorrectly composing two half-time
  rotations differs in both nonzero private quaternion components by one
  grid unit. This is a discriminating origin-preservation test.
- The paused/resumed prescribed source reaches its release at absolute time
  1.5 seconds with accumulated action elapsed exactly one second. Both spin
  and hinge tween pause at 0.25 and resume at 0.75. The incoming angular vector
  is exactly zero; subtracting the original start time would be wrong.
- The preserved evolving-permutation source has parent quaternion `(a,b,b,a)`
  at release, which maps its self X axis exactly to world Y. Its parent rate
  one and hinge rate one half give exactly `(0,1.5,0)`, and world-Y torque is
  admitted. The old independent reader refusal remains a completeness defect.
- The nonzero parallel-impulse literal uses the exact cyclic quaternion
  `(0.5,0.5,0.5,0.5)`. It maps self lever `(1,2,3)` to world `(3,1,2)`, exactly
  parallel to the nonzero world impulse. The angular cross product is zero;
  the actual linear impulse and complete independent error transfer remain.

`LITERAL-SOURCES.json` binds nine exact source files. The original three C091
witness sources remain byte-identical. The six additional literal sources
use the immutable module/image closure of the original
`docs/language-design/torque-v0.1/freeze/p28-release-then-torque.files.json`.
To run one, replace only the entry bytes in that loaded source bundle and
retain its module/image bytes and declarations. Bundle revision identities
must be recomputed by the ordinary immutable-source procedure.
`ADDITIONAL-SOURCE-BINDINGS.json` separately binds the exact retained
evolving-permutation evidence and original parallel-impulse test recipe.

## Error and refusal scope

The constructor, product, public materialization and Euclidean vector
allowances are exact inherited constants. Every complete source-DAG error,
ordered transfer, reference/error origin and materialized anchor still has
to be reconstructed and checked. Canonical cancellation does not prove zero
uncertainty. This finite calculation does **not** claim to have derived a full
final torque error projection, run an independent general source reader, or
passed a runtime/recording/Agent release gate. The normative continuous proof
and unchanged complete gates remain necessary.

The deliberately wide `[-1,1]` reducer input is a negative primitive control.
It demonstrates the terminal failure disposition for a malformed selected
enclosure. It is not a claimed supported source witness: the analytical
selection theorem guarantees the later reduction bounds for correctly
constructed immutable admitted operands.

Negative elapsed values here exercise the mathematical primitive where
already supported. They do not authorize public backwards simulation. Huge
exact transition clocks are numerical-domain examples; no ordinary source
budget or output format is presumed to admit all their complete scenes.

## Reproduce the independent derivation

Use the verified original C091 source at
`ee00c5891dacc7dbe318722e5058696b2bbc8343`, not a changed implementation tree.
The helper checks all bound input hashes before importing the independent
arithmetic. Use a fresh output filename:

```sh
python3 -B derive_expectations.py /absolute/original-c091-repository /absolute/new-expectations.json
```

The output includes interpreter/platform observations and the helper hash.
Compare its mathematical fields with the frozen report; environment strings
are observations about each actual run. The exact original report is retained
as evidence of this run. Earlier drafting corrections and the invalid first
dynamic-parent source attempt remain in the separately retained source-review
directory; they are not active frozen regression inputs.
