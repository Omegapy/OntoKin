# P12 author result: stopped at the admitted-surface blocker

**Verdict:** stopped at `P12-N57-POLICY-BINDING-001`, as directed after independent adjudication. No production or test source was changed. No implementation, adapter, product import, product behavior run, or product test run was performed.

## Why this prevents faithful implementation verification

The selected P11 candidate004 freezes 97 controls against its proposed private production rule. Control `N57_source_variant_unknown` requires `CHI-UNSUPPORTED`, stage `variant_review`, rule `LP-VARIANT-SEMANTICS`. Its input differs from the positive `P01_nonselecting_base` in exactly one field:

| Field | P01 | N57 |
| --- | --- | --- |
| `variant_review.completeness` | `synthetic_declared_complete` | `unsupported` |

The accepted operational variant document has exactly four fields: `schema`, `loader`, `source_review`, and `suffixes`. It has no completeness field. The decision assigns completeness of the loader's suffix inventory to independent source review. Both frozen contexts have the same loader/source-review identities, suffixes, external-digest-match observation, image bytes, kernel observation and filesystem observations. Their sole distinguishing label does not reach a specified production predicate.

Consequently, a faithful adapter cannot exercise the specified production rule and obtain these different outcomes. A new completeness flag, review schema or semantic admission mechanism would expand the accepted surface. Changing a bound descriptor, suffix list, schema or digest solely for N57 would substitute a different observation. Having the adapter reject the label itself would test the adapter's asserted outcome, not the implemented production rule. These are not permitted repairs.

The exact comparison and input hashes are in `N57-SURFACE-QUESTION.json`; `N57-SURFACE-QUESTION.md` retains the original pre-adjudication question. Those records are preserved unchanged. The Director subsequently relayed independent agreement and ordered this technical stop. The Director/reviewer own the separate adjudication evidence and canonical task state.

## Exact inputs and preservation

The authentic checkout and selected candidate were supplied at revision `79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae`, branch `work/c271-missing-import-digest-control`. The independently adopted candidate manifest is SHA-256 `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de`. The expected-outcome file is SHA-256 `dfb285f41a58a1f7254aaae4aa022f91afdc72fb7d5dad2f3d6b1e8257d14137`; the fixture manifest is SHA-256 `ea377d25e96631b70cd8909a5375fa3fd0feadf7f017f0673d8a094335186594`.

Materialization authenticated and restored 178 inert files, including all 131 fixture files and all 97 input/oracle records. The three mapped Git envelopes were strictly decoded with their exact schema, base64 encoding, byte counts and hashes checked. The adopted candidate's raw diff and the corresponding independent-review diff were byte-identical and matched the independent recorded identity. Copies used exclusively created regular files under the private evidence tree; every frozen `.bin` remained nonexecutable. Frozen repository bytes were not rewritten. No fixture generator or product module was executed.

`MATERIALIZATION-RECEIPT.json` contains every copied path/hash/size/mode and the transport identities. `MATERIALIZATION-ATTEMPT001.json` retains the exact command, interpreter/platform, relevant environment, exit code and log/script identities. `SOURCE-PRESERVATION.json` compares all 22 previously frozen protected-source identities with current bytes and checks that the proposed new test file remains absent. This is source-preservation evidence only.

## Observed checks and limits

- Inert materialization and fixture/oracle coverage: passed, exit code 0.
- Single-field P01/N57 comparison: established by a recursive, type-sensitive JSON comparison.
- Protected-source bytes: compared separately; results retained in `SOURCE-PRESERVATION.json`.
- The 97 frozen behavior controls: not run.
- The 175 existing inspection/mapping methods: not run; their existing source files were preserved.
- H0/H1, Node/ldd, preparer/installation, actual source Git processes inside inspected operations, original-seven/full-routine, native/model/hosted execution, integration and parent closure: not performed.

There were no failed materialization attempts and no failed product tests. Several read-only display calls exceeded output budgets; the required source/contract windows were reread in bounded calls. Those presentation limitations are recorded in `MATERIALIZATION-ATTEMPT001.json` and are not relabelled as passing product checks. No failed output was deleted.

## Recovery and ownership

The worker has no active process, pending write, unknown operation, Git/index/ref change, publication or integration. This statement applies only to this worker's operations; it does not establish termination of earlier sessions' processes or resolve their retained unknowns.

All authored recovery bytes are under this `implementation/` directory, inventoried in `AUTHOR-MANIFEST.json`. Root owns canonical records, Git/publication, the independently verified final partial handoff and the next task. Technical work stops here. Any correction to the accepted decision/control relation requires a separately selected review phase; this worker has not supplied or implemented such a redesign.
