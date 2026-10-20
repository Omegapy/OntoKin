# Reconstructed Draft 2 lifecycle and recording preparation

This directory is **expected preparation, unadopted and unimplemented**. It
contains eight exactly recovered files plus newly authored replacements for
lost preparation. It establishes no source execution, Agent result, GLB
validation or finite release acceptance. The complete product goal remains open.

## Provenance and fixed inputs

[reconstruction.json](reconstruction.json) distinguishes every recovered member
from new reconstruction. The five entry sources, `l01.files.json`,
`q16.files.json` and [recording-probes.json](recording-probes.json) match their
independently retained historical identities. All three local libraries match
the original proposal library bytes. Every transport manifest is contained in
this directory, with no parent traversal. Bundle revisions retain the original
L01–L04 and Q16 identities.

The previous acceptance file, protocol rows, generated-member inventory and
complete author/check scripts were lost. Their hashes and byte lengths are
historical references in the provenance record. The files newly written under
those names have new hashes and are not claimed to be those historical files.
The original Q16 record is preserved verbatim: its references to the three lost
files and its statement about preserving the old supplement commit describe
the historical addendum. The new Q16 checker explicitly verifies this distinction.

[effective-recording-probes.json](effective-recording-probes.json) is the
separately named current binding. It records every old/new base-input identity
and retains the complete unchanged Q16 source, clocks and future mutation. Its
[recording-probe-inputs.json](recording-probe-inputs.json) closure replaces the
lost historical inventory role without creating a circular hash. The exact
old record is retained as history; its unavailable hashes are never silently
treated as matching the new preparation. The final adoption freeze must name
the effective binding and its complete member closure.

The original [41-case corpus](../acceptance.json), [oracle](../oracle.py), source
libraries and all original expected values remain unchanged. The new author
script uses the original independent Decimal/Fraction equations, not the
production parser, reach solver, evaluator or exporter. The separate checker
does not import either author script or the oracle; it checks explicit case
equations, exact rounding cells and independently calculated forward kinematics.
Its `2e-12` libm comparison tolerance is an internal preparation cross-check,
not a changed source or destination acceptance tolerance.

## Fixed lifecycle coverage

The new [acceptance.json](acceptance.json) contains complete source-recording
reach projections, exact rational sample clocks, source spans, admitted starts
and targets, physical coordinates/rates, per-action rates, claims and terminal
results. Observation run IDs are null because these are expected source
records. A future real Agent sample must use its actual run identity.

| Case | Fixed semantic coverage | Sample sides | Action states |
| --- | --- | ---: | ---: |
| L01 | Both joints move toward `(0,1,0)` over two active seconds; pause at `0.5`, resume at `1.5`, complete at `3`. | 16 | 16 |
| L02 | Stop A at `0.5`; B captures the actual quarter coordinates and reaches `(1,1,0)` on the negative branch in one second. A's interrupted result stays latched. | 14 | 28 |
| L03 | A completes at `2`; B starts at that same boundary and completes at `3`. A's satisfied result stays latched as B changes the physical coordinates. | 14 | 28 |
| L04 | The staged stop of A and unreachable start of B at `0.5` roll back together. A still runs with both claims, B stays pending, and no valid after-side exists. | 7 | 14 |
| Total | All named actions occur in every retained sampled side. | **51** | **86** |

The sample grid is **newly fixed**, not an exact recovery of the lost grid.
It preserves the retained semantic boundary requirements and the previous
51-side/86-state inventory. Equal counts do not establish historical content
equality. Both sides of start, pause, resume, successful handoff and completion
are present, with interior moving/paused observations and the valid incoming
failed-boundary side. No failed admission becomes a current action outcome.

The checker verifies exact binary64 targets against original P16/P02,
correctly rounded exact-rational affine samples and rates, the bench's actual
`(0,1,0)` arm mount, both joints' ownership, and immutable stopped/completed
terminal results. Physical coordinates and rates remain current even when the
selected action has stopped or completed.

## Protocol requirements and extra release probes

[protocol-cases.json](protocol-cases.json) is a new reconstruction of the
retained 42 semantic requirements. It fixes concrete source revisions, exact
UTF-8 patches, requested levels, expected results and immutable-history checks.
It does not claim exact recovery of the former row wording or grouping.

| Group | Requirements | Fixed purpose |
| --- | ---: | --- |
| LP01 | 9 | L04 failure, valid prefix, unavailable samples/continuation, reset and fresh `0.25` prefix; no export. |
| LP02 | 9 | Exact P13→P20 root initializer repair, rejection of generated/property authority, retry/status and unchanged siblings, libraries and old run. |
| LP03 | 5 | Constructed N06 acceptance, admission failure, exact P10 limit repair and retained failure history. |
| LP04 | 7 | Actual P24 run at `1.5 after`, all 128 complete action items, measured complete response `N`, success at `N`, final publication failure at `N−1`, bounded tiny-budget receipt and unsupported field rejection. |
| LP05 | 12 | Never-accepted candidate distinction, unsampled versus actual before-zero state, rejected ordinary operations, later constructed acceptance, immutable old candidate run/receipt and fresh reset. |

The request templates explicitly identify runtime bindings. `$fixture_bundle`
loads the named fixture's exact transport source bytes; `$binding` substitutes
a value from an actual prior response; `$binding_minus_one` subtracts one from
the measured integer. These templates are not already executed wire requests.
LP02's sibling/source preservation has explicitly enumerated bounded evidence
reads inside its existing semantic requirements. All such reads, status polls
and artifact chunks must appear in future actual logs; they do not alter the
42-row semantic inventory. LP04 permits no adaptive smaller query or omitted
action data to fit the budget.

[release-probes.json](release-probes.json) keeps two additional gates separate:

- L04's **tenth Agent artifact** follows the successful reset/prefix workflow.
  An actual export with `options.end: "0.25"` establishes a fresh delivery run
  and retrieved artifact bytes under the unchanged L04 program revision.
- Q22 performs one authorized action-expression edit from accepted L04 to
  the exact L02 source **in the same project**, then rejects a query binding
  the old L04 failed run to the new L02 revision. A control query still reads
  the old L04 history with its correct revision. A failed create precondition
  cannot satisfy this stale-history gate.

## Q16 exact clock witness

Q16 changes only L01's pause/resume literals to `0.50000002` and `1.50000002`.
Those literals first round to canonical binary64; their exact rational values
then define the event clock. Completion is exactly
`3 + 1/9007199254740992`, which must not be rounded back to binary64. Direct
binary32 storage rounds the pause to `0.5`, the resume to `1.5` and completion
to `3`.

The enclosing interval between the actual source/stored pause and an interior
paused key includes a positive-width moving segment of
`180143985/9007199254740992` seconds. Both incoming joint rates are nonzero.
The future hostile probe removes that incoming phase from one otherwise valid
forearm interval certificate while preserving all unrelated artifact content.
The pure arithmetic check does not create that artifact or establish that the
future supplied-byte reader rejects it.

## Reproduce the preparation checks

Run from the repository root:

```bash
python3 docs/language-design/planar-reach-v0.1/draft2-supplements/author_supplements.py
python3 docs/language-design/planar-reach-v0.1/draft2-supplements/verify_supplements.py
python3 docs/language-design/planar-reach-v0.1/draft2-supplements/verify_recording_probes.py
```

The author script's default mode compares generated bytes; only explicit
`--write` regenerates its ten named new files. It never rewrites recovered
source/probe files, original corpus files or library inputs. The two checkers
are read-only and standard-library-only. Their stdout results must be retained
as fresh preparation evidence. The new strict projection schemas are checked
separately when all recovery branches are combined. A published adoption and
actual source/Agent/destination acceptance remain subsequent requirements.
