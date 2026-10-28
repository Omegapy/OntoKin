# Independent recorded reach validation

Implementation checkpoint: October 20, 2026. This describes the new
`ontokin/reach_conformance.py` supplied-byte reader. It is implementation work
under the [adopted reach contract](../language-design/planar-reach-v0.1/ADOPTION.md),
not a completed delivery or release result. Actual executions belong in the
[runtime validation record](https://github.com/Omegapy/OntoKin/blob/767ae3203d56845f8c0b8fac985fbfa406dcf014/docs/engineering/reach-runtime-validation/README.md)
on the combined implementation branch. The isolated delivery branch does not
yet contain that record.

## Independent expectations

The reader asks `ontokin/reach_reference.py` to reconstruct exact event clocks,
admission, action lifecycle, incoming releases, both boundary sides, ideal
carrier motion and uniform phase bounds from the immutable source model. The
reference uses its own guarded rational intervals and event ledger. Neither
the reader nor the reference calls the production reach solver, evaluator,
pose sampler, planner or certificate generator to establish an expected motion
answer. The existing geometry constructors still define the inherited native
geometry contract; their reuse does not supply a motion expectation.

Derived source numbers are compared with independent interval enclosures and
the identified controlled-source allowance. An interval midpoint is never
treated as an exact expected source pose. Joint targets, action controls,
identities, source revisions and other canonical values remain exact. Recorded
quaternion signs are compared as equivalent physical orientations.

## Binding the proof to supplied bytes

The bounded GLB reader checks structure and accessor expansion before the
reach reader constructs expectations. Every animation sampler must use the
same actual stored time axis. Each authored time is a reduced, nonnegative
exact rational, and its metadata must match its accessor's binary32 bits.
Direct ties-to-even conversion is checked with exact adjacent rounding-cell
midpoints, independently of the writer's integer quotient rounding algorithm.
This distinguishes the Q18 direct-rounding answer from an internally
consistent double-rounded label.

Every source occurrence, helper identity, geometry buffer, native material,
relationship, source revision, boundary side and incoming release is checked.
All source vertices and source sites contribute to the independently computed
landmark radius. The independent native mesh is passed to the existing geometry
validator so it need not be constructed twice within one request.

The reader requires exactly one complete certificate for each actual carrier
and adjacent retained key pair. It independently reconstructs authored and
stored interval widths, endpoint time shifts, neighboring phase coverage,
derivative bounds, source numeric allowances, actual normalized endpoint
errors, the stored short arc, landmark radius and local vertex conversion
error. Both mandatory quarter-allocation plans and every final dependent
inequality use the reported upper bounds. Thus a certificate cannot pass by
understating an intermediate quantity or by publishing a final total that
does not include its own reported terms.

The source numerical basis resolves five ordered implementation inputs and
two derivation inputs to bounded current file hashes. The destination basis
resolves the actual controlled player and its derivation. Unknown identities,
unproved numeric domains, missing phases and unsupported reference behavior
reject delivery. A Boolean assertion that values were independently checked
is validated as metadata and supplies no evidence by itself.

## Resource and cancellation behavior

The reader requires the caller's existing reach work context. Compilation,
source execution, encoding, supplied-byte checks and independent expectations
do not receive separate numerical allowances. Exact scalar operations are
charged and prospective integer growth is checked before products or shifts.
Integer square roots and decimal reduction poll cancellation after the native
operation as well as before it. Original callback exceptions propagate without
being relabeled as conformance failures.

Clock integers are decoded in bounded decimal chunks; no process-global
integer-string setting is changed. Quaternion inputs consume at most the first
invalid fifth component. Basis files use bounded reads. Declared key, pose,
certificate, vertex and repeated accessor counts are checked before the
corresponding materialization.

## Verification status

This checkpoint has passed Python AST parsing and whitespace/diff checks only.
Its nine focused methods cover exact clock cells, double rounding, canonical
clock records, dependent inequalities, both quarter plans, prospective operand
limits, post-square-root cancellation and bounded quaternion inputs. They have
not executed at this checkpoint. The independent reference and pose recording
sampler are separate worker checkpoints awaiting combined runtime verification.

These focused probes do not satisfy actual hostile-byte cases, source and Agent
delivery workflows, the independent native player, browser captures, visual
review, compatibility, inherited roles or the complete R01–R12/Q01–Q22 gate.
Successful continuous supplied-byte validation will describe its exact source,
bytes and identified destination arithmetic; actual destination execution and
visual evidence remain separately required. The complete product GOAL remains
in progress.
