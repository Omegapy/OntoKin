# C193 native guide investigation

The four frozen diagnostic controls select a guide-iteration change for review.
This checkpoint does not yet claim qualification of the new backend.

## What the retained traces show

Both C192 mapping failures peak at a far corner of the left shoe. The source
places that shoe well ahead of the carriage center, so a small carriage rotation
produces a larger displacement there. At the 362.5 mm stop, frame 352 has a
0.244637657 mm vertex error. At 372.5 mm, frame 370 has a 0.292416239 mm error.
The carriage rotations are approximately 0.00126425 and 0.00153236 radians.
The right lane has no transverse or rotational guide residual.

The source-to-native basis, centered body frame and compound child offsets are
consistent with the adopted construction. Two 1 kg compounds remain the only
moving mass owners. The measured error is predominantly angular; it is not a
missing conversion from millimetres to metres. Its timing near contact is an
observation. Capture-phase alignment has not been established as the cause.

## Frozen control results

All controls use the original 372.5 mm source design and pinned Blender 4.5.3.
The [plan](DIAGNOSTIC-PLAN.md) was committed before any control was executed.

| Control | Native-sample maximum | Continuous raw/final bound | Mapping result |
| --- | ---: | ---: | --- |
| N0, original construction | 0.292416239 mm | 0.322647312 mm | Fail; all native samples match C192 |
| N1, left shoe collider removed | 0.000016660 mm | 0 mm | Pass; left carriage travels 250 mm |
| N2, GENERIC overrides 400 | 0.165544488 mm | 0.181935686 mm | Pass in this diagnostic |
| N3, GENERIC anchors at shoe centers | 0.249242746 mm | 0.404395627 mm | Fail |

The removal control eliminates the off-axis response. Increasing guide
iterations reduces it while retaining the source frames and contact stopping.
The anchor alternative remains unsuccessful and is preserved. No combined
setting search or stop sweep was performed.

There were exactly four fresh native controls. N2's first postprocessor rejected
driver-variable ordering because the worker read a sorted backend serialization
while validation used the original dictionary order. The native run completed.
Its failed receipt remains unchanged. A separate postprocessing attempt used
the exact serialized backend and completed validation/encoding without another
native run. Named driver targets and expressions were unchanged. N3's inherited
pre-intervention implementation manifest remains preserved; its diagnostic
receipt and complete inventory identify the actual modified worker copy.

[Compact results and exact peak vertices](diagnostics/summary.json), per-control
receipts and artifact inventories identify every retained artifact. Full
native scenes/traces/raw/final files are staged for the coordinator's self-contained
evidence archive. The [retained analyses](retained/edit-residuals.json) and
[reuse analysis](retained/reuse-residuals.json) required no simulation replay.

## Proposed version and verification

The [new contract](../../../language-design/guided-contact-v0.2/SPECIFICATION.md)
selects `c193-experimental-0.1` and `blender-bullet-c193-0.1` through the separate
[v02 prototype](../../../../prototypes/guided_contact_v02/README.md). Only the two
GENERIC guide iteration overrides change physically. World/motor iterations,
body/guide frames, source geometry, capture cadence, budgets and all tolerances
stay fixed. New envelope/diagnostic namespaces identify the explicit version.

The [candidate boundary check](candidate/boundary-check.json) verifies six source
cases, direct-Python canonical equality at both failure witnesses, rejection
across old/new source selectors, the sole backend setting change, seven identical
constructor/capture function syntax trees and all ten identical projection
function syntax trees. The original v01 code and frozen records are untouched.

Independent review and published adoption of the exact bytes must precede formal
qualification. The planned suite contains two fresh `.ok` builds for each A–F
case and direct-Python E/F builds. All fourteen saved scenes require independent
cache-cleared resimulation. Receiving inspection is a separate coordinator gate.
The current diagnostic margin does not predict acceptance of every required case
or every stop position admitted by the finite source schema.
