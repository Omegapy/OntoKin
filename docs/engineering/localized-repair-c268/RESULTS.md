# C268 candidate validation results

The identified candidate `734789521f82248d39b623c33aae9d3284ab4bce` passed all **12 groups, 281 test methods and 14 C253 corpus bindings** in a clean checkout on CPython 3.12.14 / Linux x86-64. Source commit/tree and all 155 explicitly identified input files stayed unchanged. [CHECKS.json](evidence/candidate/CHECKS.json) retains commands, interpreter identity, outcomes, logs and artifact hashes. All 30 output identities were checked after copying the evidence for publication.

| Group | Methods | Result |
| --- | ---: | --- |
| c253-corpus | — | passed |
| c255-oracle | 31 | passed |
| c256-reader | 29 | passed |
| c257-ownership | 23 | passed |
| c258-follows | 28 | passed |
| c261-hinge_glb | 28 | passed |
| c265-source_hinges | 49 | passed |
| c266-binding | 34 | passed |
| c267-comparison | 25 | passed |
| c268-endpoint | 34 | passed |
| workflow | — | passed |
| documentation | — | passed |

The C268 group repeated the independently authored 34-method/130-call controls: 12 historical admissions, 9 raw successes and 109 typed refusals. Both original endpoints return eight hinges, sixteen referenced sites and one shared definition. The raw changed-input comparison continues to work without historical admission. See [coverage](CONTROL-COVERAGE.md) and [implementation](IMPLEMENTATION.md).

## Independent review and remaining gates

The separate reviewer found that an overlong endpoint selector was hashed before rejection. A bounded length gate and an independent pre-lookup assertion are being added under R02. This original passing candidate remains historical evidence; the corrected candidate requires fresh checks and re-review. R05–R07 remain incomplete. Integration, fresh actual-main checks, branch disposition and verified saved delivery remain pending.

## Preserved failures and limits

The first control-author run had 12 test-author errors from treating a source pose witness as text instead of slicing the recorded byte offsets. That failed evidence and the later passing runs remain unchanged. Initial workflow-schema errors were corrected before scope publication and retained under [startup](evidence/startup/workflow-initial-failure.txt). The full whitespace diff reports a trailing space in the immutable failed unittest output; the source/documentation diff passes with that raw log excluded. [Whitespace evidence](evidence/whitespace/REVIEW.json) records both outcomes. No new reader behavior failure was observed in these runs.

This isolated standard-library observer changes no product parser, evaluator, exporter, prior component, historical contract/fixture, budget or hosted workflow. Full product aggregate, source conformance/export, native/visual/model trials and other Python/platform roles were not run. Historical failed/unrun product evidence retains its state.

The result qualifies exact historical byte admission followed by the finite C267 declaration comparison only. It does not close all C260 H01–H28 groups, evaluate sites/world behavior, authenticate accepted revisions, qualify invalid-edit atomicity or clean rebuilds, validate full source/glTF/C255 semantics, execute native routes/model trials or establish comparative advantage.

## Corrected published candidate — finalization phase

The published corrected candidate `e6f55b73fa71953aa648bcd34711a6796a7346b6`, tree `d94436a22552db903b8016f9d035985a7d8b6752`, passed **12 groups, 282 methods and 14 C253 bindings** on CPython 3.12.14 / Linux x86-64. This includes the 35-method C268 controls, with 131 calls: 12 historical admissions, nine raw successes and 110 typed refusals. All groups finished with zero failures, errors and skips; the 157 explicit input identities stayed unchanged.

[Fresh candidate receipt](evidence/finalization-20261119/candidate-published/CHECKS.json), [verification summary](evidence/finalization-20261119/VERIFICATION-SUMMARY.md) and [output audit](evidence/finalization-20261119/OUTPUT-AUDIT.json) identify the exact code, dependencies, commands, interpreter, inputs and outputs. The preliminary local candidate `52af987f…` had the same complete tree; its separate passing result and recoverable commit are retained as historical verification, not substituted for this fresh published run.

The original selector-length finding is resolved in the published candidate. Its failure/probe, original 281-method result, first control-author errors and prior interrupted audit records remain unchanged. R01–R05 acceptance is recorded by the independent final reviewer in [REVIEW](REVIEW.md). Integration, actual-main verification and saved delivery are subsequent gates recorded separately; this paragraph does not claim their completion.

Only the isolated engineering observer and its selected affected components are qualified. Runtime, fixtures, adopted language/contract files and hosted workflow definitions retain exact prior trees. Full product aggregate, source/export/conformance, other interpreters, native/visual/model trials and all C260 H-group qualification remain unrun or incomplete as previously recorded.
