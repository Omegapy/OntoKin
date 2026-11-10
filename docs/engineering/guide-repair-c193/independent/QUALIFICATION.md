# C193 independent qualification

The independently reviewed native and numerical scope passes for all six frozen
cases. Fourteen fresh builds used the adopted source binding
`c193-experimental-0.1` and backend `blender-bullet-c193-0.1`: two `.ok` builds
for each case, plus direct Python builds for E and F. The independent reviewer
reopened all fourteen saved scenes with the pinned Blender 4.5.3 executable,
cleared their caches, and resimulated them without reconstructing or repairing
the scenes. Every one of the 481 samples in each scene exactly matches its
original native capture.

This result covers the numerical, source, native-scene and lifecycle obligations
described here. Receiving-application inspection and the complete legacy driver
are separate coordinator evidence. This report does not change the historical
failed legacy result or claim a new public participant comparison.

## Result by source case

Both mapping columns have the unchanged **0.2 mm maximum**. The continuous
column bounds raw-to-final vertex deviation between animation keys; it is not
only a sampled maximum. Values come from the historical independent numerical
readers, invoked by the frozen C193 checker.

| Case | Left stop near face (mm) | Shoe collider | Final left travel (mm) | Native sample maximum (mm) | Continuous mapping bound (mm) |
| --- | ---: | --- | ---: | ---: | ---: |
| A | 380 | Enabled | 200.000018 | 0.065791207 | 0.070776007 |
| B | 355 | Enabled | 175.000012 | 0.065791622 | 0.070777184 |
| C | 367.5 | Enabled | 187.500000 | 0.043390577 | 0.047696039 |
| D | 380 | Disabled | 250.000000 | 0.000016660 | 0.0000000012 |
| E | 362.5 | Enabled | 182.500005 | 0.105948485 | 0.116436993 |
| F | 372.5 | Enabled | 192.499995 | 0.165544488 | 0.181935687 |

The disabled D case passes through the would-be shoe contact and ends with a
signed left gap of approximately −50 mm. This is the required causal control,
not an enabled-collider penetration result. Enabled cases have at most
0.057511 mm near-face penetration. The right lane ends with a 14.999982901 mm
gap in every run.

E and F are the retained C192 failure witnesses. Their old continuous bounds
were 0.271961075 and 0.322647313 mm. The newly measured bounds pass without
changing the mapping allowance, key count, native X coordinates or sample times.
The worst new bound is 0.181935687 mm. This is evidence for the frozen case set;
it does not establish that every possible contact configuration will pass.

## What was independently checked

All fourteen artifact audits pass the source, native-to-final and continuous
raw-to-final gates. Each repeated `.ok` pair has identical canonical inputs,
native trajectories, raw GLBs and final GLBs. The direct Python build at E and
at F has those same four byte-identical artifacts as its `.ok` pair. Scene file
byte equality is not required across builds: all fourteen actual saved files
were separately reopened and checked.

The saved-scene inspector verifies source geometry and materials, the two 1 kg
moving mass owners, their compound shapes, solver authority, guide and motor
settings, source-driven stop geometry, full initial frames and absence of a
hidden motion schedule. Both guides use 400 override iterations. World and
motor iteration settings remain 100; capture remains 240 Hz with 10 substeps
and 481 samples. The guide and motor frames retain the declared carriage
centers. Every base and right-lane native world matrix and bound matches the
retained C192 baseline across all fourteen runs.

The provenance supplement checks the actual successful artifacts, not just the
candidate source diff. Every `.ok` and Python source manifest identifies the
new contract manifest, the exact backend and all fourteen contract dependencies.
Each artifact contains the reviewed eleven implementation files. Direct Python
receipts also carry the actual contract and backend hashes. This exercises the
pre-adoption provenance correction recorded in
[the candidate review history](evidence/candidate-review-attempts.json).

The versioned backend changes only the local guide iteration override from 100
to 400. Construction, native capture and projection function syntax trees remain
identical to the prior package. The fixed step count and all operation, byte,
deadline and cancellation limits remain as declared. The source operation
counter charges scheduled native substeps; it does not count Bullet's internal
constraint iterations. The adopted specification explicitly records this higher
per-substep work. No performance improvement is claimed.

All 474 pinned historical files, the original expectation freeze, the numerical
checker freeze and the supplemental provenance/lifecycle freeze still match.
The seventeen numerical/source guard controls, thirty-seven translated source
fixtures, two cross-binding controls and three provenance controls passed before
formal qualification. Historical expectations and checker bytes were not edited.

## Lifecycle evidence

The native worker executed the frozen translated lifecycle harness after all
fourteen builds succeeded. Its 42 controlled cases cover all nineteen inherited
failure methods. These checks use the successful A capture and controlled fault
workers, so they do not add native physics trials. Two additional store controls
verify rejection in both directions between the C191 and C193 namespaces.

The independent recorded review verifies all 42 actual diagnostic receipts,
their exact source spans and blocked levels, the corresponding failed-attempt
receipts, the frozen method coverage, the retained supervision settings and the
unchanged accepted A state and 33 artifact files. Cancellation returned in
522.436 ms, within the frozen 2,000 ms allowance; both cancellation and deadline
receipts record descendant reaping. All 42 lifecycle cases and both namespace
controls pass. The recorded review does not rerun the workers or retrospectively
observe operating-system process state.

## Retained evidence and replay

- [Qualification summary](evidence/qualification.json): all fourteen runs,
  per-case numerical values, equality and unrelated-part checks.
- [Qualification archive](qualification-evidence.tar.xz) and its
  [file inventory](evidence/qualification-archive.json): fourteen reopened
  native traces, scene configuration snapshots, command receipts and complete
  numerical/provenance reports.
- [Lifecycle review](evidence/lifecycle-review.json): all 42 recorded cases and
  the two namespace controls. Full lifecycle execution evidence belongs to the
  native worker's archive.
- [Recorded-only replay](replay_evidence.py): restores the supplied archives,
  verifies frozen inputs and formal source locks, repeats all fourteen artifact
  audits, compares repeated/routes' bytes and checks retained native replay
  receipts and all 481 samples against each original capture.
- [Recorded-only replay result](evidence/recorded-replay.json) and
  [final review receipt](evidence/FINAL-REVIEW.json): the retained formal and
  independent archives passed the complete audit again with zero native
  executions. Documentation preservation and navigation checks also passed.

From a restored complete repository, run this command with the native worker's
formal evidence archive (or its extracted `c193-native-qualification` directory):

```sh
python3 -B docs/engineering/guide-repair-c193/independent/replay_evidence.py \
  --formal docs/engineering/guide-repair-c193/native/formal-native-complete.tar.xz \
  --out /absolute/path/to/new-recorded-review
```

This default command never starts Blender. It requires Python 3.12 and NumPy,
as used by the retained independent readers. It writes a new report rather than
altering evidence. A fresh saved-scene replay must be explicitly requested with
`--blender /absolute/path/to/the/pinned/blender`; the published evidence already
contains the fourteen fresh replays required by this qualification.

The unchanged original failures, the failed anchor diagnostic, the N2
postprocessing failure and the pre-adoption provenance rejection remain in
their retained evidence. All fourteen formal builds and independent replays
succeeded on their first attempt.
