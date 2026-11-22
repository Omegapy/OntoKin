# Final package mode diagnosis

The initial FP12 failure compares two different mode dimensions. The final ZIP
deliberately stores inert regular payloads with transport mode `0644`.
`RECOVERY-FILE-MAP.json` separately records each original physical `source_mode`.
The affected author files were authored `0600`; those original files and their
recorded modes remain unchanged. Exact dimensional counts and paths are in
`MODE-DIAGNOSIS.json`.

The builder verifier checked payload sizes/hashes and checked the current original
files' sizes/hashes/physical modes against that recovery map. It did **not** apply
the recorded modes to freshly extracted payloads. The earlier engineer summary
“original physical recovery modes” was imprecise: it described the original-file
comparison, not a completed materialization of restored permissions.

## Frozen guidance

`RECOVERY-STATUS.md` states: “Original modes are evidence; ZIP payloads are inert
regular files.” The frozen README/HANDOFF distinguish Git transport mode from
physical recovery modes and direct the reader through `GIT-TRANSPORT.md` and
accepted `candidate004/MATERIALIZATION.md`.

The accepted materialization procedure explicitly directs a fresh private copy,
application of each authenticated manifest mode (`0600` or `0644`), and verification
of size, SHA-256 and resulting mode before consumption. Its sibling-support rule
also binds prior candidates and support files to authenticated references. The
root recovery map supplies an original mode for every generic recovery row, but
the root application text does not explicitly instruct a chmod of every such row.

The accepted candidate's restoration guidance is explicit. The broader archive
preservation boundary is metadata plus exact bytes, rather than automatic original
mode restoration by a generic ZIP extractor. The independent reviewer is checking
private restoration across the affected rows. That check and the reviewer/Director
disposition must remain separate evidence; this diagnosis does not waive a gate.

No archive, candidate, original author file, canonical source or existing package
output was changed. A rebuild is not performed or assumed by this diagnosis.
