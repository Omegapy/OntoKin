# Independent review of P11 Git evidence transport

**Verdict: pass.** The adjustment is a lossless representation of three raw evidence paths through two authenticated base64 envelopes. All **52 independent checks passed**. No design, candidate manifest, control oracle, original raw file, Git setting or whitespace rule was changed by this review.

## Exact checked records

The mapping is `OntoKin/docs/engineering/localized-repair-c271/loader-path-p11/GIT-TRANSPORT.json`: 2,233 bytes, SHA-256 `19cd1889972985c10b5b346a12773fd7b279ec3e608acc00fff57082cb115f43`.

The instruction is `GIT-TRANSPORT.md`: 1,556 bytes, SHA-256 `007a4c04c648eebcf6e9e9b802680d90e4aa0fd22cee6c0c2c06ec6fb0d22d32`.

| Materialized path relative to the P11 directory | Decoded bytes | Decoded SHA-256 |
| --- | ---: | --- |
| `design/candidate004/REVISION-004.diff` | 38,093 | `2c08bfced30e1ddbf6f4584d8c5081db817aa3b8c5f68c4144265be1d1e5b417` |
| `review/candidate004/INDEPENDENT-DOCUMENT-DIFF.diff` | 38,093 | `2c08bfced30e1ddbf6f4584d8c5081db817aa3b8c5f68c4144265be1d1e5b417` |
| `evidence/technical-candidate/whitespace.stdout.txt` | 8,718 | `aa1edcfbcf800cbbe9fdd9aa66bdb574f97b0a3c4d2e8b9da43d233ba68d3c5b` |

The shared diff envelope is 51,014 bytes, SHA-256 `70f9c5dd9813dccdb8b07fdea99a34b4f59d30d79d6d6116c268d0b4f21c232a`. The failed-check-output envelope is 11,845 bytes, SHA-256 `9b181e50b5745299b77edd88436a37ee57000f1a26547342c2dcef9dbe09d092`. Every restored file retains mode `0o644` and remains nonexecutable.

## What was independently verified

The reviewer required exact closed mapping and envelope fields, rejected duplicate JSON keys, checked the explicit schema and encoding, decoded base64 with strict validation, and checked canonical base64 round-trip equality. Every decoded byte count and SHA-256 agrees with the mapping, envelope and corresponding original recovery file. The candidate diff also agrees with the already accepted candidate payload manifest. The independent reviewer diff is byte-identical to the author diff.

The original accepted candidate manifest remains 35,041 bytes with SHA-256 `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de`. The control oracle remains SHA-256 `dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137`. Repository transport copies of those two documents are byte-identical to the frozen originals.

The reviewer restored all three decoded files into a fresh private evidence tree with exclusive creation, safe relative paths, checked nonsymlink parent directories and nonexecutable regular-file modes. The resulting files match exact bytes, size, hash and mode, with one link each. Checked original inode, link count, modification/change timestamps, size, hash and mode remained unchanged before and after this operation. No logical host or runtime path was accessed.

The written instructions require an exact reviewed Git revision, authenticated envelope hashes, strict decoding and comparison with the frozen manifest. They reject absolute/parent/empty path components, aliases, special files and existing destinations. They require the complete candidate's existing `MATERIALIZATION.md` procedure afterwards and an external materialization receipt. The instructions grant no execution authority and do not alter the real Python pin or permissions.

## Whitespace guard and preservation

The reviewer ran the ordinary read-only command `git diff --cached --check`, with no suppression flags. It returned exit 0 with empty stdout/stderr. No `core.whitespace` override was configured, the envelope paths had unspecified whitespace attributes, and no staged whitespace-attribute/configuration waiver was present. These observations describe the reviewed index snapshot; root still owns final publication checks.

The original failed whitespace output remains preserved exactly, even though its own raw lines contain the same intentional spaces that caused the initial gate failure. Encoding that evidence does not erase or reinterpret the failure. Root's provenance record names the same exact mappings independently verified here.

`REVIEW.json`, `CHECKS.json`, the reviewer script and `RUN001`/Git-read logs retain the complete audit. The `fresh_materialized/` files are exact reproducible copies of the three named original recovery files. Preserve them in recovery or map them to those exact sources; copying those raw derived files into Git would unnecessarily reintroduce the same whitespace condition.

This was a transport review only. No product implementation, product test, author validator, target execution, host qualification, index mutation or external publication occurred.
