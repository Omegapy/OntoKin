# Independent reach reference checkpoint

Owned implementation: `ontokin/reach_reference.py` and
`tests/test_reach_reference.py`. The module is new runtime verification work;
none of the frozen contract, schema, oracle or expected-result files changes.

## API and independence

`build_reference(model, *, end, work=None, check=None)` requires the caller's
remaining request work context or bounded check callback. It never constructs a
new numerical allowance. The returned reference captures source records and
interprets exact event, action-completion and force-completion clocks itself.
It imports no production simulator, IK solver, pose implementation, planner,
certificate generator, exporter, or preparation oracle.

The public interface is:

- `boundaries`: immutable exact `Fraction` clocks, including zero and prefix end.
- `sample(time, side="after")`: the complete source snapshot shape. Exact
  canonical joint targets, coordinates, rates, lifecycle fields, source
  identities and authority records remain exact. Derived pose, velocity and
  residual leaves are `Interval(lo, hi)` values.
- `boundary_states()`: the exact recorded-boundary field shape, including all
  before/after joint, action, pose-authority, impulse, force and reach maps, and
  complete saved incoming releases with source spans and reach contributors.
- `pose_enclosure(carrier, time, side="after", ideal=True)`: the independent
  mathematical world pose. `ideal=False` uses the separately rounded physical
  coordinates and retained actual-anchor enclosures. Quaternion comparisons
  must respect the equivalence of antipodal representatives.
- `phases(carrier, start, end)`: immutable records for every positively
  overlapping semantic phase. The record includes exact actual/ideal scalar
  paths and slopes, root coefficients, uniform derivative bounds, documented
  source path counts, coordinate discrepancy, extents and propagated anchors.
- `point_phase(carrier, time, side="after")`: the same independently derived
  basis for one exact state, including either boundary side and a final
  after-state that rematerializes an anchor. It does not add a positive-width
  phase or replenish the caller's work allowance.
- `geometry_expectations`: fresh copies of the captured complete source
  geometry/identity/placement/appearance/physical records.

The reader must apply independently identified source arithmetic allowances
when comparing derived source numerical records. A chosen interval midpoint is
never an exact expected source answer. The independent interval reference and
the production controlled dyadic algorithm need not share last-bit pose values.

## Numerical and lifecycle method

Admission classifies the exact annulus and exact signs of the shoulder's signed
radicals before interval refinement. An independent Cartesian shoulder equation
avoids subtracting two rounded inverse angles. Alternating arctangent sums,
Machin pi enclosures, exact midpoint Taylor sums with Lagrange/Lipschitz tails,
and rational square-root brackets give bounded enclosures. Monotonic Fraction
conversion proves one binary64 rounding cell for canonical targets. Unresolved
finite arithmetic fails explicitly; callback exceptions retain their identity.

The event ledger captures both incoming and staged outgoing states, finishes
natural actions and forces before source statements, and gives releases their
saved incoming topology. Paused actions hold claims; stopped/completed actions
retain immutable terminal records while another action may own the physical
coordinates. Continuous ideal joint starts survive canonical stop/restart
rounding. Force sums retain their exact ideal acceleration separately from
canonical net-force/acceleration values.

The common uniform source basis is reconstructed from topology using the
documented constant/inverse/compose rules in
`docs/engineering/reach-source-kernel.md`. The independent implementation exposes
every count and error primitive rather than accepting certificate labels. It
preflights the distinct H06 weighted source-history sum before retaining each
state pair, counts all repeated full reach/source identities, and rechecks the
actual boundary histories after materialization. The whole metadata and byte
budgets remain the separate reader's responsibility.

## Check status and remaining integration

Only AST parsing and whitespace/diff checks have been executed on this new
reference checkpoint. Its eight focused test methods are written and await
root's exclusive execution window. They cover exact signs and half-turns,
shared cancellation, forbidden production expectation calls, actual source
projections, stop/replacement history, a valid prefix before failed admission,
saved incoming release/forces, a fresh non-dyadic stop/restart variant, and exact
nonbinary completion/phase overlap.

This checkpoint is not delivery acceptance. Root must integrate the reference,
run these focused tests and inspect work consumption, reconcile any found
defects, and complete the supplied-byte reader, writer/native integration,
required Agent deliveries, external destination checks and visual release
evidence. In particular the actual and proof anchor clocks and tight common
source allowances need executed source/reference comparison after integration.
