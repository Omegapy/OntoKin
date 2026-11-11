# C195 direct Python ownership repair

## Reached result

The supplied malformed candidate was rejected before native execution. One local
source repair then produced the 365 mm design. One separate native construction
regenerated the preserved accepted 375 mm design. Both actual outputs passed the
unchanged C194 artifact reader. Coordinator scene replay, receiving checks and
independent acceptance are pending at this author submission.

This is a supplied public recovery exercise in a shared environment. It is not
blind diagnosis, and this single result establishes no authoring or cost advantage.

## Observed diagnostic and physical conflict

The unchanged C193 direct runner returned exit status 1 and this actual message:

```text
ValueError: $.colliders.contact.left_shoe.owner: differs from frozen constant
```

The candidate's `follow.left` makes `left_shoe` follow `left_carriage`.
`body.left` names that carriage and supplies its solver motion authority. However,
`contact.left_shoe.owner` was `body.right`, whose body part is `right_carriage`.
That assigns the left shoe's physical contact to a different carriage from the
one it follows. Changing the left-stop coordinate cannot resolve that conflict.

For this finite assembly, the direct schema requires the constant `body.left` at
that owner field. Its rejection is a concrete schema diagnostic; it is not a
claim that this direct schema infers arbitrary ownership from follow relations.
The 365 mm stop is the intended design edit and remains in the repaired source.

The negative receipt charges 25 `schema_values` operations, no
`scheduled_native_substeps`, and 0 native elapsed milliseconds. The negative
output contains exactly `build-receipt.json` and `manifest.json`. No native
artifact, source staging or canonical input was produced by the rejected attempt.

## Local edit and preserved sources

[Candidate](candidate.py) is the original malformed source, retained unchanged.
[Repaired source](repaired.py) was made from that candidate by replacing only the
left-shoe owner token `body.right` with `body.left`. There was one repair and no
incorrect source repair. [Repair delta](repair-delta.patch) records that edit.

[Accepted source](accepted-source.py) is a byte-identical review copy of the
provided 375 mm source. The [source delta](source-delta.patch) proves the repaired
source differs from the accepted source only in `left_stop.at_mm[0]`, from 375 to
365. Both native positive runs used the unchanged C193 `native/build.py` recorder;
the baseline regeneration used the original supplied `accepted-source.py` path.
No prepared C194 positive source or artifact was substituted into either run.

## Preservation and regeneration

The accepted source, C194 acceptance record and entire existing accepted-run
closure were hashed before rejection, immediately after rejection and after the
positive checks. The 41-file closure totals 2,844,039 bytes and remains unchanged.
Its canonical inventory SHA-256 is:

```text
c8ddd5398254c1fbd286ec8329d1c73a1b5d1d6d738ec4736c493add8cd2fe24
```

The fresh 375 mm build reproduces the original accepted `canonical-input.json`,
`native-transforms.json`, `raw.glb` and `final.glb` exactly. The full scenes,
implementation copies, manifests, receipts and native evidence remain in each
actual run directory. Ordinary files and Git staging preserve the direct route;
no OntoKin-specific store or atomic-transaction guarantee is claimed.

## Checks and accounting

| Check | 365 mm repaired | 375 mm regenerated |
| --- | --- | --- |
| Native producer | Passed, first attempt | Passed, first attempt |
| Unchanged C194 artifact reader | Passed | Passed |
| Continuous mapping bound | 0.07451646802035088 mm | 0.116442262620993 mm |
| Frozen mapping allowance | 0.2 mm | 0.2 mm |
| Producer operations | 449,664 | 449,664 |
| Scheduled native substeps | 4,800 | 4,800 |
| Build recorder elapsed time | 3.6337697505950928 s | 3.338125228881836 s |

All 618 frozen C195 input files passed byte/hash verification. The author made
exactly one rejected static attempt, one repaired native construction and one
baseline native construction, with no retry. There were no author scene reopens
or receiving jobs. The two builds retain the 1,000,000-operation request,
80,000 ms host computation request and unchanged 100-second outer watchdog.
The two-second modeled duration is a separate design value.

An evidence-recording correction is retained explicitly: the first
`negative-verification.json` looked for operation charges under the wrong JSON
keys and reported the scheduled charge as `null`. The unchanged actual receipt
uses `operation_components`. The supplementary
`negative-verification-complete.json` reads that field and records zero. This
was a reporting correction, not a source repair or a repeated attempt.

`ACCOUNTING.json` identifies timing, commands, exact costs and limits.
`SUBMISSION.json` binds the actual source and run paths, hashes and
preservation evidence. Detailed raw evidence is retained under
`/workspace/scratch/3cb1527378cd/c195-runs/python`, including failed command output,
all evidence scripts and both intermediate verification records.

Provider token totals, billed cost and exact model snapshot are unavailable.
The available operation counts are harness charges, not provider tokens or model
cost. Coordinator setup, replay, rebuild and receiving work are separate. This
author result changes no inherited gate: the legacy driver and supplemental tail
remain FAILED, thirteen torque methods remain NOT RUN, and no full release or
general contact claim is made.
