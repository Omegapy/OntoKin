# C193 native guide investigation

Fourteen fresh builds pass the unchanged native/output checks under the adopted
guide-iteration correction. All forty-two inherited lifecycle controls and two
store-version checks also pass. The original backend, its failed C192 deliveries
and both unsuccessful diagnostic controls remain preserved.

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
native scenes, traces, raw/final files and the failed N2 postprocessor are retained
in the [complete diagnostic archive](diagnostics-complete.tar.xz), with its
[exact file inventory](diagnostics-archive.json). The [retained analyses](retained/edit-residuals.json) and
[reuse analysis](retained/reuse-residuals.json) required no simulation replay.

## Adopted version and verification

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
Independent review caught a copied source-manifest fallback that still named
the C191 contract. The [pre-adoption correction](candidate/pre-adoption-provenance-fix.json)
changed that v02 receipt hash before any formal build. Direct-route receipts also
bind the actual verified contract and backend hashes.

The coordinator published and read back the [exact adoption receipt](qualification/adoption-receipt.txt)
before the first formal run. Its SHA-256 is
`43914daa1d93ed8f5bad4645909b4af2ff14a0b44558c6dacf6ceb71ddb5fb69`.
All runs used implementation `61d20e9a941b14cea091dc38ed1e43232280ecb5`,
contract manifest `d5ce5afa4e1a548f493b9b0184798bfe8e88f954a2f57771e2d20e0256037037`,
and backend `9ce64fd758b4e7f659ddd9d4bb3bcf7a0faa6a1883cc018c673e10536fe0aefe`.
The [input lock](qualification/INPUT-LOCK.json) records every executed package,
contract, direct-source and command-recorder byte.

### Formal native builds

Two fresh `.ok` builds cover each A–F case. Additional direct-Python builds cover
E and F. Within each case, canonical solver inputs, all native transform records,
raw GLBs and final GLBs are byte-identical across repeats and authoring routes.
All right-lane native samples also match the retained C192 reference exactly.
Every build retains all 481 native X/time keys. No unsuccessful formal build was
discarded: all fourteen passed their source transaction or direct-runner checks.

| Case | Stop / collider | Left travel | Native vertex maximum | Continuous producer bound |
| --- | --- | ---: | ---: | ---: |
| A | 380 mm / enabled | 200.000018 mm | 0.065791207 mm | 0.070776006 mm |
| B | 355 mm / enabled | 175.000012 mm | 0.065791622 mm | 0.070777183 mm |
| C | 367.5 mm / enabled | 187.500000 mm | 0.043390577 mm | 0.047696038 mm |
| D | 380 mm / disabled | 250.000000 mm | 0.000016660 mm | 0 mm |
| E | 362.5 mm / enabled | 182.500005 mm | 0.105948485 mm | 0.116436992 mm |
| F | 372.5 mm / enabled | 192.499995 mm | 0.165544488 mm | 0.181935686 mm |

The largest observed attempt consumed 450690 counted operations and approximately
2182 ms, within the unchanged explicit 1000000-operation / 80000 ms ceilings.
These measurements describe this environment and workload; they are not an
authoring-effort comparison. [Measured build summary](qualification/build-summary.json)
and [fourteen-build manifest](qualification/formal-builds.json) retain exact
identities, commands, costs and per-case values. The
[formal archive](formal-native-complete.tar.xz) and its
[file inventory](formal-native-complete-manifest.json) contain the complete stores,
editable scenes, raw/final motion and attempt receipts.

Independent numerical, source/provenance and saved-scene replay evidence belongs
to the independent reviewer. Receiving-application evidence belongs to the
coordinator. Those records remain separate from the producer checks reported here.

### Lifecycle and version separation

The [lifecycle summary](lifecycle-results/summary.json) records **42 passing
attempts covering all 19 inherited failure methods**. It exercises actual
supervision, validation, projection and atomic publication with controlled workers
that copy the already captured A result. It performs no new physics simulation.
Cancellation returned in 522.436 ms, within the unchanged 2000 ms limit, and both
the worker and descendant were reaped. The two-second running deadline returned
in 2508.076 ms, including forced shutdown. All previous accepted pointer and
artifact bytes remained unchanged after every rejected attempt.

The [store-namespace checks](lifecycle-results/store-namespace-summary.json)
confirm the real accepted A store uses `ontokin.c193.store/0.1`. Both APIs reject
the other store version before source admission or native execution and preserve
its bytes. The [complete lifecycle archive](lifecycle-complete.tar.xz) and
[inventory](lifecycle-complete-manifest.json) retain all failed stages, injected
faults, command records, logs, rejected state copies and unaccepted publication
candidate. Frozen harness and input translations remain under [lifecycle](lifecycle/TRANSLATION.json).

## Reproduce the record

Extract the three archives into a fresh directory. Inspect the receipts before
executing another native trial. Absolute command paths record the original run;
adapt only invocation paths when replaying a restored source checkout. Keep the
recorded receipts and source/constructor/settings bytes unchanged.

The producer summary is read-only and does not invoke Blender. It resolves the
retained artifact paths relative to the supplied formal manifest, preserving
the original absolute paths as provenance:

```sh
python -B docs/engineering/guide-repair-c193/native/summarize_builds.py \
  --formal /restored/c193-native-qualification/formal-builds.json \
  --retained /restored/c192/deliveries/python/reuse \
  --out /new-output/build-summary.json
```

The independently supplied archive replay tools check the delivered bytes and
retained native replay results without another native solve. For a future
concrete construction change, the documented v02 CLI builds into a new store
and reopens a saved scene explicitly. Do not rerun completed participant
authoring trials to recover context.

## Remaining scope

The worst continuous bound is approximately 0.181936 mm, leaving about 0.018064 mm
under the original limit. Passing these six cases does not qualify every stop
position admitted by the finite source schema, an exact analytic guide, arbitrary
contact geometry or general dynamics. Solver impulses and manifolds remain
unobserved. This correction does not retroactively accept the original C192
deliveries, demonstrate comparative authoring advantage, complete a production
backend or resolve the separately recorded legacy torque deadline failure.
