# Source resource preparation evidence

`EVIDENCE.zip` preserves the source resource repair, its failed preparation
controls, the independent slice-assignment defect, and the final 31-method CPU
result. It contains retained source snapshots, logs, actual input receipts,
source commands, and an index of the unchanged C198 compiler files. This is
preparation evidence; it establishes no native export or receiving result.

The sequence remains visible:

| Cohort | Result | Meaning |
| --- | --- | --- |
| Initial resource controls | 7 passed, 3 failed | The new tests made incorrect assumptions about tracing, aggregate work, and callback position. |
| Corrected resource controls | 11 passed | The corrected controls passed before the final directory-scan bound. |
| Existing source controls | 18 passed | Accepted geometry, rotations, boundary rejection and diagnostic classes remained intact. |
| Combined resource repair | 29 passed | Exact source snapshot `920b8691…` is retained. |
| Independent slice probe | Incorrectly accepted | The original 12,288-entry list and review report are retained. |
| Assignment repair | 31 passed | Exact source snapshot `c785153c…`, inputs and receipts are retained. |

The initial temporary inputs were cleaned by the test harness. Most recur with
identical bytes in the later retained corpus. The unique `sum(range(4096))`
input is explicitly marked as a deterministic reconstruction. It was not rerun
or relabeled as an original capture. The earliest modified executable source
hash was not separately captured; the manifest states this limitation. The
original logs remain unchanged. Runtime information measured during packaging
is also identified as a later observation, not a retrospective attestation.

## Archive format and verification

The ZIP is content-addressed. `FILES.json` maps each logical evidence path to its
SHA-256, size, original POSIX mode, and stored blob or existing archive member.
Byte-identical members of the original source corpus and independent review
archive are referenced only after their bytes and archive hashes were verified.
`MANIFEST.json` beside this README binds the ZIP and those dependencies.

Directories, symlink targets and hardlink groups are preserved in the logical
manifest. This includes the hardlink identity used by the source alias control.
Unpacking `blobs/` alone does not recreate the logical directory tree. A consumer
that materializes it must apply the manifest paths and modes, create recorded
hardlinks, and create symlinks last without following them. The evidence does
not require executing any retained source.

From the repository root, verify this bundle and the reader bundle with:

```sh
python3 -IB docs/engineering/static-tray-qualification-c199/evidence/source-resources/verify_evidence.py --bundle docs/engineering/static-tray-qualification-c199/evidence/source-resources
python3 -IB docs/engineering/static-tray-qualification-c199/evidence/source-resources/verify_evidence.py --bundle docs/engineering/static-tray-qualification-c199/evidence/reader-layout
```

Verification reads hashes and archive members only. It starts no native,
receiving, lifecycle or test process.
