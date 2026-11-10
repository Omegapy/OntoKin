# C193: the shared guide correction passes its frozen cases

C193 repairs the native guide residual that rejected both C192 authoring
routes. The new, explicitly selected Blender/Bullet backend gives each guide
400 solver iterations instead of 100. This gives the solver more iterations
to enforce straight carriage motion during contact. World and motor iterations
remain 100. The source geometry, mass owners, guide frames and recorded-motion
rules are unchanged.

Both former failure witnesses now meet the original **0.2 mm** mapping limit.
Their continuous bounds fall from **0.271961075 to 0.116436993 mm** and from
**0.322647313 to 0.181935687 mm**. The independent native, numerical, lifecycle
and receiving checks pass. The [fresh legacy disposition](evidence/recovery/legacy/disposition.json)
records 4,239 distinct passing methods across a timed-out stock prefix and an
independently reviewed ordered continuation. The same thirteen experimental
torque-read methods remain NOT RUN after their unchanged setup deadline.
All six other core command stages pass. The stock driver and the supplemental
run remain FAILED; this is a bounded development result, not a full regression
or release pass. Main integration and its checks are recorded separately.

The interrupted-session [recovery record](RECOVERY.md) distinguishes the already
completed qualification from fresh recovery checks. Its independent recorded
replay reproduces all fourteen artifacts exactly and verifies the adopted bytes,
historical inputs, lifecycle and receiving evidence. Original local worker Git
histories remain unavailable; the published source and evidence are retained.

## What changed, and why

The retained C192 traces show a small carriage rotation at contact. Because
the shoe extends ahead of the carriage center, that rotation produces a larger
displacement at the shoe's farthest vertices. Four controls were frozen before
new construction experiments: original settings, collider removal, increased
guide iterations, and a moved guide anchor. Collider removal restored free
travel. Increasing guide iterations passed the worst witness; moving the anchor
still failed. All unsuccessful attempts are preserved.

The correction uses source `c193-experimental-0.1`, backend
`blender-bullet-c193-0.1`, and the separate
[v02 prototype](../../../prototypes/guided_contact_v02/README.md).
The original v01 package and its failed C192 outputs remain unchanged.
The [adoption](../../language-design/guided-contact-v0.2/ADOPTION.md) identifies
the exact contract, eleven implementation modules and independent freezes that
were published before formal qualification. A pre-adoption review caught and
corrected an old contract hash in the new source receipt; the failed review
and corrected actual-artifact provenance checks are retained.

## Measured qualification

Both mapping columns retain a 0.2 mm limit. The continuous bound covers every
raw-to-final animation interval. It does not describe unrecorded solver substeps.

| Case | Left stop (mm) | Shoe collider | Left travel (mm) | Native vertex maximum (mm) | Continuous mapping bound (mm) |
| --- | ---: | --- | ---: | ---: | ---: |
| A | 380 | Enabled | 200.000018 | 0.065791207 | 0.070776007 |
| B | 355 | Enabled | 175.000012 | 0.065791622 | 0.070777184 |
| C | 367.5 | Enabled | 187.500000 | 0.043390577 | 0.047696039 |
| D | 380 | Disabled | 250.000000 | 0.000016660 | 0.0000000012 |
| E | 362.5 | Enabled | 182.500005 | 0.105948485 | 0.116436993 |
| F | 372.5 | Enabled | 192.499995 | 0.165544488 | 0.181935687 |

E and F are the original failed C192 targets. D deliberately passes through
the intended contact and finishes with a signed gap of approximately −50 mm.
Enabled cases have at most 0.057511 mm penetration, within the unchanged 0.5 mm
limit. The right final clearance is 14.999982901 mm in every run.

The [independent qualification](independent/QUALIFICATION.md) establishes:

- Fourteen fresh builds: two `.ok` builds for each A–F case, plus direct-Python
  E/F builds. Each saved scene was independently reopened and resimulated.
  All 481 samples in every scene exactly match the corresponding original capture.
- Exact canonical-input, native-motion, raw-GLB and final-GLB equality in all
  six repeat groups and both route comparisons. Every base and right-lane
  native matrix and bound also matches the retained C192 baseline.
- Source geometry, two 1 kg moving mass owners, one solver authority per lane,
  native configuration, contact, settling, rebound, twenty unrelated-pair
  separation checks, and preservation of all carriage X values and timestamps.
- Thirty-seven translated source fixtures, two source-version rejection
  controls, seventeen checker controls and three provenance controls before
  formal qualification. All 474 pinned historical files remain unchanged.
- Forty-two lifecycle cases across nineteen inherited failure methods, plus
  two store-version rejection checks. The accepted A pointer and all 33 prior
  artifact files remain unchanged. These controlled workers reuse the captured
  native result and do not add physics trials.

## Actual receiving applications

[Receiving evidence](evidence/receiving/result.json) checks all twenty-eight
raw/final paths, containing eleven distinct GLB hashes. Khronos reports zero
errors and warnings, with twelve retained informational unused-sampler findings.
Three.js evaluates 84 poses. Blender imports the six distinct final cases,
checks their actual geometry against a separate decoder and renders eighteen
poses. All eighteen PNGs were visually reviewed.

The enabled cases visibly stop at the shoe contact; the disabled case shows
the required pass-through. Geometry, attachment and right-lane clearance remain
consistent. Those observations support the numerical evidence without replacing
it. The [receipt interpretation](evidence/receiving/INTERPRETATION.md) explains
the unchanged scripts' inherited labels and actual eight-thread CPU rendering
setting. No browser, GPU rendering or live destination-physics claim is made.

## Evidence, reproduction and limits

| Need | Record |
| --- | --- |
| Aggregate measured results | [Results](RESULTS.json) |
| Ownership and initial recovery | [Scope](SCOPE.md) and [observed starting state](evidence/coordination/startup.json) |
| Diagnostic controls, unsuccessful attempts and fresh builds | [Native investigation](native/README.md) |
| Independent freezes, native replays and recorded-only replay | [Independent qualification](independent/QUALIFICATION.md) |
| Exact adopted implementation | [Implementation inventory](IMPLEMENTATION.json) |
| Receiving archive | [Archive inventory](evidence/receiving-archive.json) and [complete archive](receiving-evidence.tar.xz) |
| Next bounded task | [C194 instructions](NEXT-TASK.md) |

The qualification ran on Linux x86-64 with CPython 3.12.14 and the pinned
Blender 4.5.3 executable. Ordinary execution defaults remain 100,000 operations
and 30,000 ms. Named qualification requests retain their explicitly authorized
1,000,000-operation and 80,000-ms ceilings. The guide work is bounded by its
exact setting and the native supervisor; the operation counter does not expose
Bullet's internal solver iteration telemetry.

This is a finite experimental-backend result for six cases. It is not a fresh
public participant comparison, proof that every admitted stop position passes,
a production backend, a general authoring advantage or completion of OntoKin.
The original C192 rejections and the separate legacy torque obligation remain
visible. Current full-driver and integration results must be read with their
identified source revisions.
