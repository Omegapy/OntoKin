# Published C088 equivalence audit

**Passed.** Published commit `de7f22e73d7e54886734fbf85e399a5bcb4bc5c2` preserves the tested production/source-facing surfaces exactly from runtime `39afec7971b9221fe58cf7c7d002505d172dd64f`. This is a read-only native-source audit, with no product imports, tests, worktree writes or Git mutations.

## Exact preservation

The full native tree inventories and freshly streamed blob bodies establish identical bytes and modes for all 170 production module files, 74 versioned schemas, 4,410 example files, 335 tested test files, both hosted workflows and all 905 original frozen-packet files. The new interface-test file is identical to the tested cut. All 334 original C087 test files, 158 original tools and two original workflows are unchanged.

The audit streamed all 8,706 distinct blobs present across C087, runtime39af and de7f22e: 638,976,132 body bytes. Every blob passed independently computed native SHA-1 and SHA-256 checks. Full per-path inventories retain native object IDs, modes, byte counts and SHA-256 identities for all three cuts.

## Every post-runtime difference accounted for

There are exactly 951 post-runtime changed paths: 948 additions and three modifications. The three modified files are:

- `README.md`: the explicit .21 usage and contract links, with experimental/release limits retained.
- `docs/engineering/keyed-membership-2026-11-02-c088/README.md`: actual verification, preserved failures, corrections and still-open gates.
- `tools/run_keyed_membership_sources.py`: the separately verified `candidate-controls` mode; the original C087-only predecessor-control guard remains.

The complete path-level record is `ALL-POST-TESTED-DIFFERENCES.json`. Each path has its exact before/after native identity, byte hash/mode, category, rationale and publication/review basis. The categories are 911 reviewed amendment files, nine verification tools, 25 review/evidence records, four proposal-only documents and two documentation updates. No prefix grants permission to ignore modifications: the actual native diff must equal the exact enumerated set. Protected-scope prefix checks only prohibit changes and additions.

The effective Agent overlay is an additional tree. The original freeze remains exact. The effective manifest passes its own pin and every one of its 904 data-file identities. Of those, 903 equal the original, and the only changed data file is `agent/request-workflows.json`. Independent replay of all seven test/replace pairs produces exactly the effective JSON, with no source, span, replacement-text, semantic, resource or geometry answer changes. The unchanged original amendment document still carries its historical pending-review status; later review/publication records provide the adoption chronology.

## C087 boundary

Of 8,812 original C087 paths, 8,798 are unchanged and none is removed. The fourteen modified original paths are the twelve already reviewed runtime modules plus root `README.md` and `docs/README.md`. The complete list and per-path identities are in `ALL-ORIGINAL-C087-MODIFICATIONS.json`. The current tree adds 1,960 paths after C087; all post-runtime additions are individually enumerated in this audit.

## Reuse and remaining gates

`audit_final_equivalence.py` is a bounded comparison helper. It reads native Git trees/blobs with network, replacement objects, hooks, fsmonitor and optional Git writes disabled. The exact comparison basis is retained as `EXPLICIT-COMPARISON-BASIS.json`. For a later final candidate or resulting main, supply a newly reviewed exact per-path basis and a fresh absent output directory. The helper refuses unaccounted differences and preserves the fixed C088 original/amended input pins.

This audit does not replace the complete inherited run, final integration/resulting-main comparison, or the actual ZIP member/source/native/ref/recovery audit. Those remain separately required. The helper execution is recorded in the sibling `final-equivalence01-command` directory. `MANIFEST.json` is the original executed audit inventory; `PACKAGE-MANIFEST.json` additionally includes this explanatory report.
