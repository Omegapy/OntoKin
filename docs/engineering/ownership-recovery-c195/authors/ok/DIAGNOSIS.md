# C195 OntoKin ownership recovery

## Observed result

The malformed candidate was rejected before native execution. One local owner
repair produced the 365 mm design, and one separate regeneration reproduced the
preserved accepted 375 mm design. Both actual builds pass the unchanged C194
artifact checker. This is the first formal submission, pending coordinator audit.

The author used the supplied public candidate and defect description. This is a
recovery exercise with a known defect, not a blind diagnosis or evidence of a
language or cost advantage.

## Relationship conflict and exact repair

`follow.left` makes `left_shoe` follow `left_carriage`. `body.left` owns that
carriage and supplies its physical motion. Therefore the left shoe's collider
must have `body.left` as its mass owner. The candidate instead assigns
`contact.left_shoe` to `body.right`, while leaving the follow relationship on
the left. Spatial following and physical ownership describe different
relationships, but they must agree on which body supplies this collider's
mass and motion. Assigning the right body does not move the follow relationship.

The actual run returned `C193_E_OWNERSHIP`, phase `validate`, with the message
“Collider is assigned to the wrong mass owner”. It identifies `candidate.ok`
line 81, columns 17–29, bytes 2400–2412: the `"body.right"` owner token.
The negative command exited 1, as expected. Its levels were:

| Level | Result |
| --- | --- |
| represented | true |
| constructed | false |
| evaluated | false |
| exported | false |
| destination_validated | false |

The result consumed 921 charged operations (827 source tokens, 82 field checks,
12 reference checks). It scheduled zero native substeps, reported zero native
elapsed time, zero native result/log bytes and zero staged output bytes.
`artifact_directory` was null and `artifacts` was empty. The sole store addition
was its failure receipt. No native construction or retry occurred for rejection.

The repair changes only the candidate's left-shoe owner from `body.right` to
`body.left`. There were no incorrect repairs or intermediate alternative sources.
The original malformed bytes remain in `candidate.ok` and in the frozen fixture.
Compared with the accepted baseline, `repaired.ok` differs only at `left_stop`:
`at = [375, 130, -220][mm]` becomes `at = [365, 130, -220][mm]`.
`candidate-repair.patch` and `source-delta.patch` record both comparisons.
The repaired file was made by editing the supplied malformed bytes; a prepared
positive source or artifact was not copied into either delivery.

## Preservation and regeneration

The original accepted revision and previous revision both remained
`2143515f358e36c1dd9a1deef83dba2519a99be6141b64d8bd9dae987761fbd0`.
Before and immediately after rejection, and again at submission preparation,
all 47 existing preserved files (2,935,277 bytes) match in hash, size and mode.
That closure includes the accepted source, C194 acceptance record, state
pointer, all accepted artifacts and original receipts. The existing lock file
also remains unchanged. One new failure receipt was added; nothing was removed
or modified. `PRESERVATION.json` binds the full before/after manifests.

Both positive constructions used the unchanged C193 `native/build.py` recorder,
the pinned Blender executable, 1,000,000 operations, 80,000 ms and its existing
100-second outer watchdog. The 365 mm build used this author's repaired source.
The 375 mm build used the supplied `accepted-source.ok`. They ran in separate
fresh stores. The original accepted store was not advanced to the repaired
revision.

| Actual output | Left stop | Checker | Native sample error | Continuous mapping bound |
| --- | ---: | --- | ---: | ---: |
| repaired-01 | 365 mm | G passed | 0.067812002 mm | 0.074516468 mm |
| baseline-regenerated-01 | 375 mm | H passed | 0.105950345 mm | 0.116442263 mm |

Both bounds are below the unchanged 0.2 mm limit. Both readers evaluated 481
native samples and all 20 unrelated pairs. Each run retained the actual saved
scene, canonical input, native records, raw and final GLBs, implementation copy,
manifest, command and receipt. The 375 mm canonical input, native transforms,
raw GLB and final GLB are byte-identical to their original accepted counterparts.
Their original hashes also match the supplied C194 acceptance record.

Each build consumed 450,690 operations, including 4,800 scheduled native
substeps. The recorder elapsed times were 3.577691317 seconds for repaired-01
and 3.223345757 seconds for baseline-regenerated-01. The negative transaction
and these builds consumed 902,301 charged operations in total. Read-only check
and evidence-management work is recorded separately, without inventing an
operation count for tools that do not provide one.

## Evidence and limits

`BUILD-RESULTS.json` identifies both actual runs, sources, artifact directories,
hashes, complete operation components and checker results. `ACCOUNTING.json`
records dispatch, completion, commands, failures, allowances and telemetry
limits. `SUBMISSION.json` is the immutable first submission. Detailed command
logs and full closures remain under the provisioned C195 author output path.

One initial read/search shell command exited 2; it included a missing inspection
glob and suppressed stderr, so the precise error text is unavailable. It made
no edits and launched no native work. The expected ownership rejection is the
only failed formal attempt. All such commands are retained in the accounting;
no failed attempt was overwritten or retried.

There was one repaired native build, one baseline native build, one intended
source repair, zero incorrect repairs, zero native retries and no author
delegation or model override. Provider token totals, provider costs and exact
model snapshot are unavailable. The shared environment and prepared backend
limit conclusions from this single pair. Coordinator scene replays, receiving
checks, visual review and independent acceptance are separate and pending.

The inherited legacy driver/tail remain FAILED, and thirteen torque methods
remain NOT RUN. This exercise changes no runtime, checker, backend, tolerance,
contract, original gate or shared STATUS, and makes no full-release or general
contact claim.
