# C192 independent numerical recovery review

## Verdict

**APPROVE preservation and integration of the C192 evidence record.** No numerical
or archive-integrity blocker was found in recovered commit
`0dd0e1fb44abb73d2fef65bc3a318c54ca2ea13f`. **All six participant builds remain
rejected.** This review is a new examination of retained evidence, with no prior
participant role. It ran no participant trial, native simulation, or receiving
application and changed no source, tolerance, or test gate.

The [verification receipt](verification.json) identifies the environment, exact
commands, hashes and checks. The isolated review used CPython **3.12.14**, NumPy
**2.3.5**, and Linux x86-64. Review output was written outside the checkout under
`/workspace/scratch/9c186c07eb69/c192-recovery-numerical-output`.

## Measurements and equality

The documented replay passed with **116 frozen inputs**, **801 final-archive
files**, **six rejected participant builds**, and **28 expected control outcomes**.
The independent supplemental check also verified all **86 first-phase archive
files** against their separately retained manifest. Both archive hashes and the
final archive's manifest hash match the published repository receipts.

| Target stop | Left travel, mm | Native-sample to final maximum, mm | Continuous raw-to-final bound, mm | Delivery |
| ---: | ---: | ---: | ---: | --- |
| 362.5 mm | 182.50000476837158 | 0.2446376567070452 | 0.2719610745598733 | Rejected |
| 372.5 mm | 192.49999523162842 | 0.2924162394357902 | 0.3226473129779241 | Rejected |

These values exactly reproduce [results.json](../../results.json). Both native
sample maxima exceed the unchanged **0.2 mm** limit. Raw-to-final distances at
recorded keys also reach 0.24462716831039522 and 0.2924208776018445 mm on the left
shoe. The failure therefore does not depend solely on a conservative bound
between keys. Final playback and source localization pass; every retained
delivery receipt still has `successful: false` and no accepted artifact path.

Direct byte checks confirm cross-route equality, four recorded coordinator
rebuilds, and both first-target regenerations for canonical input, native
transforms, native trace CSV, raw GLB and final GLB. Same-route rebuilt and
regenerated source bytes also match. All **12 retained build artifacts**,
including the two starters, carry the same **11 frozen implementation files**.
Native `.blend` byte identity across separate saves is neither claimed nor
required.

A separate standard-library GLB decoder checked every raw/final sampler time
array in those 12 artifacts, and both carriage translation tracks against the
native matrices. Times and translations agree at the format's float32 precision;
the final mapping preserves every carriage X sample. This supplements the formal
mapping checker, which correctly stops at its failed distance assertion before
its later field checks.

The replay count of **13 recorded reopens** is consistent with the narrative:
**ten coordinator inspections, two starter inspections, and one optional
participant inspection**. Each retained reopen matches all 481 native sample
rows, its identified saved scene/source/input hashes, and its successful command
receipt. The saved configuration has 13 objects, 240 Hz capture, ten substeps,
100 solver iterations and no transform actions. The pinned inspector records a
completed cache clear, unchanged configuration and no reconstruction. These are
verified historical records, not newly executed Blender inspections. The
corrected `fresh_rebuild_performed` / nullable `rebuild_exact` distinction is
consistent across the retained audit rows and consolidated results.

## Limits and continuation

- **Delivery acceptance remains blocked** by the two reproduced mapping failures.
  The C193 task can diagnose those exact witnesses without repeating C192 or
  changing its gates. Frame alignment remains a diagnostic hypothesis.
- **The inherited full legacy driver remains FAILED:** C191 recorded 4,239 passed
  methods and thirteen torque artifact-read methods not run after the original
  30,000 ms setup deadline. This recovery does not rerun or qualify that driver.
- **A fresh native rerun needs an external dependency.** The evidence archive
  contains saved native scenes and verification dependencies, but not the pinned
  Blender 4.5.3 Linux executable. Its required SHA-256 remains
  `5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`.
  An outgoing handoff must identify that requirement and carry the exact source
  repository; the evidence archive alone is not the complete replay program.
- **Historical native command paths are not relocatable as written.**
  `tools/verify_builds.py` reads the original absolute source path from
  `delivery.json`. Use the documented `shared/build.py` command with a retained
  source at its new path, or add a separate path-remapping facility. Do not edit
  sealed receipts. The documented recorded-evidence replay already works from
  the relocated checkout used here.
- The replay checks its internal archive inventory and reports the archive hash;
  it does not itself compare that hash to `evidence/archive.json` or reconcile all
  aggregate `results.json` values. This review's supplemental checks performed
  those comparisons. Future recovery should preserve that outer hash check.

These packaging limits do not block preservation of the failed experiment.
Fresh receiving execution, unexecuted compatibility roles, broader authoring
advantage and the full project goal remain outside this review. Remote
publication and main integration are the coordinator's responsibility; this
review makes no claim that the recovered local commit is already merged.

## Reproduction

From the exact recovered repository, run the two commands in
[tools/README.md](../../tools/README.md) with a new replay output directory. Then:

```sh
python3 -B docs/engineering/contact-comparison-c192/reviews/recovery-numerical/verify_recorded.py \
  --repo /absolute/path/to/repository \
  --replay /absolute/path/to/new-replay \
  --out /absolute/path/to/new-verification.json
```

The supplemental helper verifies retained bytes and decoded fields. It invokes
no native process and does not replace or loosen the frozen formal checks.
