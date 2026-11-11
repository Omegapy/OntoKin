# C194: accepted contact edit and reuse

Both original authors completed the public comparison. The OntoKin source and
direct Python routes each moved the left stop from 380 to 365 mm, then created
the 375 mm variant from their own accepted first source. Each phase passed on
its first formal submission. Both authors preserved the first source and
regenerated its canonical input, native motion, raw GLB and final GLB exactly.

This is a measured result for one seven-part, two-carriage assembly using the
prepared common constructor. It establishes literal-source editing and reuse
on these targets. It does not establish general classes or libraries in this
prototype, a comparative authoring advantage, cost superiority or a production
physics backend. [Frozen public brief](frozen/BRIEF.md)

## Measured results

| Check | First edit | Later reuse |
| --- | ---: | ---: |
| Left-stop near face | 365 mm | 375 mm |
| Ideal left travel | 185 mm | 195 mm |
| Ideal contact time | 1.480 s | 1.560 s |
| Continuous playback mapping bound | 0.074516468 mm | 0.116442263 mm |
| Unchanged mapping allowance | 0.2 mm | 0.2 mm |
| OntoKin source delivery | Accepted | Accepted |
| Direct Python delivery | Accepted | Accepted |

The right lane retains 300 mm travel and approximately 15 mm final clearance.
Both routes produce identical canonical inputs, all native pose records, raw
GLBs and final GLBs at each target. All 481 samples retain the unchanged source,
native contact, configuration, geometry and continuous-mapping gates. Actual
submitted scenes were independently reopened and resimulated without rebuilding
their geometry. [Exact results and artifact identities](results.json)

The completed evidence contains four preparation builds, six author builds and
six independent coordinator rebuilds. Ten independently reopened saved scenes
reproduce their complete 481-sample records. Khronos checks cover twenty raw and
final paths with zero errors or warnings; Three.js checks cover sixty poses.
Thirty original Blender import panels have recorded visual review. Twelve of
those panels were reviewed during recovery. [First acceptance](evidence/FIRST-ACCEPTANCE.json)
and [reuse acceptance](evidence/recovery/REUSE-ACCEPTANCE.json) bind the actual
source, artifact, visual and independent-review identities.

## Author accounting

| Self-recorded phase elapsed time | OntoKin source | Direct Python |
| --- | ---: | ---: |
| First edit | 148.045 s | 148.336 s |
| Reuse and first-result regeneration | 148.671 s | 140.919 s |

Each author used one native build for the first edit and two during reuse,
including first-result regeneration. There were no invalid source attempts,
failed native builds, formal repair turns or human interventions. Two failed
read-only search commands are retained in the accounting. Provider token totals,
cost, hidden turns and exact model snapshot are unavailable. Shared-environment
timings for one pair cannot establish a cost or reliability advantage. Prepared
setup and independent validation are excluded from these author phase timings.
[Independent source and accounting audit](evidence/recovery/REUSE-SOURCE-ACCOUNTING-REVIEW.json)

## Recovery and reproducibility

The interrupted session had already completed preparation, both authors and
the automated reuse checks. This continuation recovered their original Git
histories and outputs, reviewed the twelve pending images, completed explicit
reuse acceptance and independently audited the retained evidence. It dispatched
no replacement author and ran no new native build or receiving application.
[Recovery record](RECOVERY.md)

The original preparation and first-validation archives remain unchanged. The
completion archive retains the original author runs, reuse validation, reviews
and recovery receipts. Original absolute paths remain historical provenance;
the recorded replay maps them to extracted copies without rewriting receipts.
The original fifteen C194 commits are retained in the
[worker history bundle](evidence/original-worker-history.bundle), with its exact
prerequisite and heads in the [descriptor](evidence/original-worker-history.json).
Connector publication and actual-main verification have separate identities.

To audit the retained evidence from a clean current checkout with Python 3.12
and NumPy, choose two new output directories:

```sh
python3 -IB docs/engineering/contact-comparison-c194/extract_evidence.py \
  --repo "$PWD" --out /absolute/path/to/c194-evidence
python3 -IB docs/engineering/contact-comparison-c194/recorded_replay.py \
  --repo "$PWD" --evidence-root /absolute/path/to/c194-evidence \
  --out /absolute/path/to/c194-recorded-audit
```

The first command verifies and extracts three recorded archives. The second
reruns the independent numerical readers, identities and receipt checks. It
does not construct a native scene, resimulate a scene, dispatch an author or
execute a receiving application. Do not use `verify_deliveries.py` for recovery:
that original orchestration runs fresh native validation.

## Limits and next task

The inherited legacy driver and supplemental tail remain **FAILED**. Their
existing disposition records 4,239 distinct passing methods and thirteen torque
artifact-read methods **NOT RUN** after the original 30,000 ms setup failure.
C194 changes no historical runtime, tests, backend, contract or workflow and
does not rerun or relabel that cohort. [Inherited regression disposition](../guide-repair-c193/evidence/recovery/legacy/REGRESSION.md)

General contact, a production backend, live destination physics, other pending
compatibility and external roles, comparative advantage and the full
[GOAL](../../../GOAL.md) remain open. The next bounded task is
[C195: diagnose and recover from an ownership error](NEXT-TASK.md). Qualify its
negative input statically before dispatch. Reuse the accepted positive C194
evidence; do not repeat these trials to recover a conversation.
