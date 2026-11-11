# C195: ownership-error recovery with a preserved accepted design

Both authors completed the public recovery exercise on their first formal
submission. Their malformed candidate was rejected before simulation. Each
author corrected the collider owner, produced the intended 365 mm design,
preserved the accepted 375 mm source and outputs, and regenerated that design
exactly. [Acceptance](evidence/ACCEPTANCE.json) binds the actual submissions,
independent numerical checks, author audit and twelve reviewed render panels.

This qualifies one supplied recovery workflow on the prepared two-carriage
assembly. The defect and expected diagnostics were public. It does not measure
blind error discovery, statistical reliability, language advantage or a full
production physics backend. [Frozen protocol](PROTOCOL.md)

## What failed, and what the authors repaired

The left shoe follows the left carriage. Its collider therefore belongs to
that carriage's mass owner, `body.left`. The unaccepted candidate incorrectly
assigned `contact.left_shoe` to `body.right`, while also moving the left stop
from 375 to 365 mm. Neither route simulated that malformed relationship.

| Observation | OntoKin source | Direct Python |
| --- | --- | --- |
| Actual diagnostic | `C193_E_OWNERSHIP`, wrong mass owner | `ValueError`, left-shoe owner differs from the schema constant |
| Location | Owner token at line 81, columns 17–29 | `$.colliders.contact.left_shoe.owner` |
| Negative native work | None | None |
| Original accepted files preserved | 47 | 41 |
| Formal submissions | 1 | 1 |
| Repaired constructions | 1 | 1 |
| Preserved-design regenerations | 1 | 1 |
| Incorrect source repairs | 0 | 0 |

The different file counts include each route's own accepted run, source and
acceptance record. They are not comparative quality scores. OntoKin derives
the ownership requirement from the physical relationships; the direct schema
fixes the owner for this finite assembly. The original schema rejection is
shared setup and cannot establish a language advantage.

The OntoKin author exercised rejection against a copy of the actual accepted
store. Its accepted pointer, previous revision and existing artifact closure
remained unchanged; a separate failed-attempt receipt was retained. The Python
author used ordinary file staging and preserved its complete accepted closure.
Both positive builds then used fresh output directories. C195 therefore does
not demonstrate promotion of the repaired design in the same accepted store.

Both repaired sources differ from their accepted baselines only in the intended
stop coordinate. The original malformed sources and the one-token owner
repairs remain inspectable in [the author records](authors/).

## Independent delivered-output checks

| Target | Continuous native-to-recorded mapping bound | Unchanged allowance |
| --- | ---: | ---: |
| Repaired 365 mm design | 0.07451646802035088 mm | 0.2 mm |
| Regenerated 375 mm design | 0.116442262620993 mm | 0.2 mm |

All four actual submissions passed the inherited source, configuration,
geometry, contact, provenance and numerical gates. Four independently reopened
saved scenes reproduced all 481 decoded samples without reconstructing the
scene. One clean coordinator build per submitted variant reproduced canonical
input, native motion, raw GLB and final GLB exactly. Both 375 mm regenerations
also match the actual accepted C194 outputs. The two routes match each other
at each target. Saved Blender file byte identity is not required.

Receiving checks cover eight raw/final GLB paths with zero Khronos errors or
warnings and four retained informational findings. Three.js checks twenty-four
poses. Four actual Blender imports produced twelve panels, all directly
reviewed. The images show intact geometry, attached shoes, the expected contact
poses and independent motion in the other lane. Numerical acceptance comes
from the readers, not visual appearance. [Exact results](results.json)

The first automated result deliberately leaves author acceptance pending.
The separate [finalization](evidence/FINAL-AUTOMATED-RESULT.json) attaches the
completed independent author audit without repeating any native or receiving
work. The final acceptance binds both receipts and the visual review.

## Accounting and limits

The independent author audit passed 867 evidence assertions. Its conservative
elapsed bounds through the committed dossiers are 281.178940 seconds for
OntoKin and 326.690177 seconds for Python, both inside twenty minutes. Earlier
self-recorded submission times mark the start of sealing and are retained
separately. These shared-environment observations from one supplied pair do not
establish speed or cost superiority. Provider tokens, cost, exact model snapshot
and hidden internal turns are unavailable.

The original command records retain an OntoKin read-only search failure and a
Python accounting extraction that initially reported a null native-substep
field. Its explicit supplement reads the unchanged underlying receipt and
confirms zero native work. There was no incorrect source repair, positive-build
failure, native retry or human intervention.

Prepared setup, the two authors, coordinator builds, saved-scene replays and
receiving checks have separate records. The original author Git objects are
retained in [their bundle](evidence/original-worker-history.json). Connector
publication commits have distinct identities. During coordinator validation,
one completed author text dossier was committed; the exact frozen implementation
bytes stayed unchanged. Each build retains its actual Git identity.
[Provenance disclosure](evidence/COORDINATOR-PROVENANCE.json)

## Recover without repeating the experiment

The evidence archive retains complete author outputs, accepted baselines,
negative attempts, command receipts, independent rebuilds, scene replays,
receiving results and visual observations. The explicit replay map relocates
old absolute paths without rewriting historical receipts.

With Python 3.12 and NumPy, run:

```sh
python3 -IB docs/engineering/ownership-recovery-c195/recorded_replay.py \
  --repo /absolute/path/to/current-checkout \
  --out /absolute/path/to/new-recorded-replay
```

This verifies the archive and re-executes only recorded numerical/provenance
readers. It launches no native simulation, scene resimulation, receiving
application or author. Do not rerun `verify_deliveries.py` to recover context;
that coordinator invocation is already reserved and complete.

The replay helper's independent review identified and corrected an initial
receiving-label identity gap before its first archive replay. The rejected
version and corrected version remain separately identified.
[Tooling review](evidence/REPLAY-REVIEW.json)

## Project state

C193 was already complete when this continuation began. Its supplied ZIP passed
all 704 manifest-file checks. C194's original trials had also finished; their
1,038 archived files and 1,755 recorded assertions were independently verified,
then the published candidate was integrated through PR #129 without replacing
an author or repeating a trial. Its actual main merge passed the same recorded
audit and documentation checks. [C194 resulting-main verification](evidence/C194-MAIN-VERIFICATION.json)

C195 changes no inherited runtime, schema, solver, tests or hosted workflow.
The inherited legacy driver and supplemental tail remain **FAILED**, with
4,239 distinct passing methods and thirteen torque-read methods **NOT RUN**
after the unchanged 30,000 ms setup failure. This evidence work does not rerun
or relabel that cohort. General contact, a production backend, live destination
physics, broader compatibility and external roles, comparative authoring benefit
and the full [GOAL](../../../GOAL.md) remain open.

Read [the next bounded task](NEXT-TASK.md) only after reconciling actual main,
open work and the integration lease. Preserve these completed trials.
