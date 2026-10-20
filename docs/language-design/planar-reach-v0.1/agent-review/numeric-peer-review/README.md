# Independent numerical proposal review

Reviewer: `/root/reach_final_contract_review13`. Reviewed numeric commit: `e7ead21bb0822bafafebe932c16724bc7dc149f7`. Decision: **no blocking findings for the proposed mathematical contract**.

This record persists the completed independent review of `interval_oracle.py`, `numeric-admission.md` and `verify_rounding.py`, together with the identity of `rounding-certificates.json`. The exact four file hashes before and after review are in [review.json](review.json). All four files matched the reviewed numeric commit.

## Findings and scope

The exact annulus and radical signs support the complex shoulder direction. Scaling both components by positive radius squared preserves their signs and argument. Exact cancellation, negative-axis handling, the shoulder's positive-Pi64 remapping and the independent elbow branch are consistent.

The directed dyadic operations, integer square-root bracket, arctangent reductions, Machin identity and whole-cell nearest-even inclusion support the reviewed rounding proof. The paired Taylor recurrence uses the correct residual remainder degrees. With `N >= 5`, the sine remainder is smaller than the selected cosine remainder because their ratio is `8 / (2*N + 1) < 1`.

The fixed precision schedule, cumulative counters and propagated cancellation provide finite helper behavior. Production must still implement complete shared-work accounting, actual source/claim/limit checks and atomic boundaries, and the distinct uniform source/destination numerical error contract. Recurrence counting does not waive any constituent interval operation.

Existing 54 coordinate-cell, 5 classification, 17 mathematical, 9 resource and 25 wrong-cell-mutation results support their stated fixed corpus. Counts alone do not prove universal admission or production readiness. The review combines the mathematical derivation, implementation inspection and the focused checks below.

No numeric or runtime files were edited. No source runtime, Agent, SQLite, export, full-suite or archive execution occurred. This review does not claim historical byte equivalence, adoption, implementation or release acceptance.

## Focused independent evidence

The [focused checker](focused-check.py) preserves the Python body of the inline command executed during review. Its [initial observed output](focused-output-initial.json) is the original captured stdout, preserved without relabeling it as a later run.

- 1,204 exact-rational rounding crosschecks against independent `Fraction` to binary64 conversion passed.
- 1,204 exact point/cell membership crosschecks passed.
- 16 axis and quadrant solutions across both branches passed. Native trigonometry supplied only a sanity comparison, not proof of correctly rounded transcendental values.
- Unit links and target `[0, 2^-1074, 0]` produced the required finite `NumericFailure`: its shoulder lies just above the half-smallest-subnormal midpoint, which this schedule cannot distinguish. The run used 4,620 recurrence steps, 18,555 interval operations and 33 declared exact helper operations.
- Cancellation after work began propagated at the 250th poll.
- The four reviewed file hashes remained unchanged.

A fresh persistence replay is separately recorded in [focused-output-replay-001.json](focused-output-replay-001.json) and [persistence-check-001.json](persistence-check-001.json). The replay must match the initial semantic results and exact input hashes; elapsed time is intentionally allowed to differ. The persistence report records the actual interpreter, platform, command, timestamps, input identities and output hashes.

To replay from the repository root after the numeric files are integrated, using the chosen verification interpreter:

```bash
python3 docs/language-design/planar-reach-v0.1/agent-review/numeric-peer-review/focused-check.py
```

The checker is a read-only mathematical preparation check. It prints JSON and disables bytecode writes. Do not use Python optimization flags, which disable its assertions.
