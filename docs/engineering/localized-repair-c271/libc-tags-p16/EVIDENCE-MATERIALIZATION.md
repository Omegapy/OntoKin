# Exact evidence archives and readable mirrors

`design/CANDIDATE001.zip` is the authoritative complete frozen candidate. It contains all 169 payload files plus the unchanged candidate manifest under `candidate001/`, preserving every original byte and inert file mode. The nearby `design/candidate001/` directory is a readable mirror of the top-level records only. It is not a complete materialization and must not be supplied directly to an adapter or constructor.

For a later authorized phase, extract the complete candidate to a fresh private directory, verify safe paths, CRC, exact inventory, every recorded size/hash and inert mode against `CANDIDATE-MANIFEST.json`, and follow the original `MATERIALIZATION.md` for directory and fixture-mode restoration. Treat all scripts and ELF fixtures as data until that future phase authorizes their particular use. Do not execute a recovered ELF or change a frozen expectation.

`REVIEW-EVIDENCE.zip` preserves the complete independent review and retained implementation-source evidence under `review/`, with the explicit two-web-response exclusions and metadata at its root. Readable review reports, inventories and assertion results remain beside the archive. The source-review manifest is original: the two excluded supplemental web bodies cannot be reconstructed from metadata; all exact implementation source and patch bytes used for the decision remain preserved.

This publication representation avoids altering verbatim source and patch whitespace. The first documentary candidate failed the UTC timestamp format check and Git whitespace check on four raw upstream/patch files. Its exact changed-path snapshot, all logs and the original staged-tree identity are preserved in the final handoff under `recovery/session/verification/core-preflight001/`. The timestamp was corrected. No whitespace setting, check, source byte, candidate expectation or technical rule was weakened or changed.

The archive identities and root verification are recorded by `ADOPTION.json` and `PUBLICATION-MATERIALIZATION.json`. A final independent documentary review must verify this representation before publication.
