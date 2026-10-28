# C060 independent auditor source review

## Scope and conclusion

Reviewed on 2026-10-28 by the independent source-integrity reviewer. This review consisted of source reading, syntax parsing with `ast.parse`, file hashing, and reading retained JSON and command output. The reviewer did not import or execute the auditor, import OntoKin, run product requests or tests, resume a failed request, or edit the repository worktree. The coordinator executed the retained audit and negative-check commands separately.

No blocking correctness issue was found for the auditor's stated purpose: checking the consistency of the two failed P11/L03 control/capture pairs and reconciling their executed prefixes. The final version closes the command-provenance gap identified during review. Passing this auditor does not establish release acceptance, a valid exported artifact, complete source semantics, timing neutrality, or the cost or savings of an unexecuted tail. The documentation gate remains failed for the precisely identified historical archive omissions below.

## Exact reviewed versions

| Version | Bytes | SHA-256 |
| --- | ---: | --- |
| Initial auditor, retained as `analysis-implementations/auditor-attempt001.py` | 70,814 | `b928b033522c998396f3d703a2cdc55000eaf8364e44b78c0abed3a446d04725` |
| Final auditor, `.recovery/audit_reach_recording_work.py` at review time | 71,385 | `5a1ece268ba6f8bf71f2f62fbe2963da34175280797ec66be668261b2886b0cf` |

Both versions passed syntax parsing. A complete textual comparison showed that the final version adds only eight lines in `audit_command()`.

The reviewed evidence names executed candidate commit `5170bb99bfb045c651e1aabb1ac5f24c9d2259dc`, tree `ed848bced2c9f8cf4027ffd278b6bf9e0be606e6`, with original main `b37b39102aea67eb81bd9e38518352403a844e99` as its parent. Historical request snapshots contain 488 materialized files, 9,364,004 bytes, and 2,841 explicitly omitted tracked paths. Later hydration for documentation checking does not rewrite that execution-time inventory. The separate source-integrity review covers the original-main comparison; this auditor verifies the commit/tree identified by its supplied evidence and does not hardcode the historical commit ID.

## Fail-closed comparisons and execution boundary

- `require()` raises on failure independently of Python optimization flags. The main audit records failure and returns a nonzero exit after a caught exception. JSON parsing rejects duplicate object keys and explicit nonfinite constants; canonical comparison rejects nonfinite values and distinguishes JSON booleans, integers, and floating values.
- The four before/after input snapshots for each pair must match exactly. Materialized and omitted entries jointly reconstruct the complete Git tree; the exact commit object must bind that tree. Every declared materialized file is checked for length, SHA-256, Git blob identity, and executable mode. All tracked runtime files and the required numerical-basis/destination files must be included. Omitted payload bytes are explicitly unverified.
- The pair comparison checks original settings and limits, the complete work maps and final cache occupancy, construction observations, diagnostic details, loaded OntoKin module identities, failure type/message, normalized frames, formatted traceback, causal exception graph, and all three retained copies of reader-input bytes. Wrapper removal is restricted to named functions inside the verified collector's AST spans. Required capture and per-key identity observations must be true.
- The ledger checks one uninterrupted key prefix ending in a raised partial key, exact authored clocks and retained binary32 track bits, category deltas, stage-marker charges, and source-batch/cursor observations. Disjoint segments must telescope to the complete executed shared and reach totals. The refused shared tick remains distinguished from admitted reach work.
- Inputs must be bounded regular files without symlink traversal; descriptor paths must be canonical relative paths. Every recorded analysis input is reread for stability before outputs are written. Outputs use exclusive creation in a fresh directory. The only subprocess in the reviewed auditor is argument-list invocation of `git cat-file commit`; no product module, source fixture, historical script, shell command string, or failed product continuation is executed.

The output directory remains caller-selected: the tool rejects an existing directory and symlink parents but does not independently prohibit a new directory inside a repository. The actual `audit-001` and `audit-002` directories are outside the repository worktree. That invocation condition should be retained. The tool also deliberately requires the original absolute source/evidence locations and commit object to be available; a portable replay needs those dependencies or an explicitly designed relocation procedure.

## Command-provenance finding and final addendum

The initial version verified an absolute interpreter path, the exact script and options, source commit, working/output directories, raw exit status, timing fields, stream hashes, and the failed-request stdout line. It did not compare the interpreter or full argv against the internal diagnostic report. Independent reading showed the four existing receipts already agreed, so this was a gap in what the auditor enforced rather than an observed discrepancy in C060.

The final eight-line change now requires the receipt executable to equal `report.execution.executable`, the receipt argv after removal of the recorded `-B` to equal `report.command`, and the capture's `actual_driver_command` to equal that same command. These reads use the existing stable-input reader. The new condition closes the identified gap without changing product inputs or execution.

Retained coordinator results were read, not rerun by this reviewer:

| Final audit | Recorded status | Internal check count | Shared / reach operations |
| --- | --- | ---: | --- |
| P11 `audit-002` | passed | 285,236 | 100,001 / 93,277 |
| L03 `audit-002` | passed | 445,534 | 100,001 / 95,767 |

The initial three negative probes rejected a counter mutation, a retained-GLB byte mutation, and an input-inventory hash mutation. The final version's fourth probe changed the recorded executable to `/different/python3` and rejected it with the intended executable/argv mismatch. These are focused rejection checks, not exhaustive coverage. No additional product request was needed for this metadata-only revision.

## Claim limits

The reported census and ledger concern supplied bytes and retained observations. Structurally reconciled numerical certificate fields are not independently certified source mathematics. Captured identities and matched counters support observation neutrality for these pairs; they do not prove timing neutrality or future behavior. The source batch is observed active and unprepared at the retained key boundaries; no completed source batch or successful final admission is claimed. Complete request cost, unexecuted-tail cost, optimization savings, and speedup remain explicitly unset or false. Retained exception locals remain observations. The original product requests still failed, and their retained GLBs remain unvalidated.

This review did not establish full-suite, full-corpus, compatibility, destination, or release conformance. It also does not turn historical shallow/clean-worktree metadata into a newly measured current-worktree state.

## Documentation gate

The unchanged checker is 26,640 bytes with SHA-256 `f25feaee2f1263b3508b4118eb41a7c306c92b04eaa97829def92c89c3b6a2e9`. The reviewer read `documentation/baseline-001/command.json` and independently verified the retained stdout/stderr lengths and hashes against that receipt. Its raw exit code is 1 and its JSON status is `failed`.

The checker verified all 29 original sources, 233 sections, the reconstructed baseline tree, and exact registry rows. It inspected 269 documents and 2,009 local links, including 93 anchors. All 12 reported failures are `local_link` failures for absent historical archives; the known remote-tree sizes total 74,915,834 bytes:

- `docs/engineering/impulse-release-validation/evidence.tar.xz`
- `docs/engineering/local-validation-2026-10-19/evidence.zip`
- Nine archives under `docs/engineering/reach-recording-validation-2026-10-22/`: `checkpoint-001.zip`, `checkpoint-002-verified.zip`, and `checkpoint-003.zip` through `checkpoint-009.zip`.
- `docs/engineering/surface-release-validation/evidence-80d59bb.zip`

The unchanged checker's `check_link()` requires the target to exist within the repository. A remote Git identity, manifest entry, or successful C060 diagnostic audit cannot satisfy that local-payload requirement. These are execution-time environment omissions, not evidence that the upstream repository lacks the objects. No placeholder files, changed links, omitted checks, or fabricated archive contents were proposed or used in this review. The failed baseline result must remain visible; a reviewable draft publication is compatible with that disclosure, while a claim that the documentation gate passed is not.
