# C087 bounded pure String concatenation

The next step selected by the C086 handoff implements **bounded pure String concatenation for reusable component namespaces**. The [adopted decision](../../language-design/string-concat-v0.1/ADOPTION.md), [source guide](../../language-design/string-concat-v0.1/README.md), [frozen corpus guide](../../language-design/string-concat-v0.1/CORPUS.md) and [Agent/0.20 guide](../../language-design/agent-v0.20/README.md) distinguish semantics from actual evidence. The [work scope](WORK-SCOPE.json) starts from C086 main `5d83b07354296a891c1a6acd70efc77322d2127f`.

Explicit bindings are source `0.20` / `string-concat-0.1`, Agent/0.20 and recorded GLB/0.20. Immutable bundle/files stay `0.2`; ordinary defaults and earlier declaring-version meanings remain unchanged. Both complete experimental-feature release and full-product acceptance remain false.

## Published implementation and independent evidence

Runtime commit `af585dd9a6d952a61a0ea8b45d3597ef6cc4b796`, tree `82c9d138fb5aedc2f4ca12483caa96bb9ade3455`, implements exact `String + String` with left-then-right evaluation, no conversion or normalization, a 65,536-byte UTF-8 result ceiling and 4,194,304 cumulative logical result bytes per request. Real admitted-ledger work and cancellation precede scanning/allocation/publication. `.20` concatenation results are not reused through value caches; abstract checks retain unknown String without dynamic concatenation. Existing stable-key validation, payload identity and provenance remain separate from general String validity.

Adoption and frozen inputs were published in `2bdb81ece376144387da5581f8df91f59324dc2e`; the separately identified lossless PNG readback transport was published in `cd8c7fa2f84922ff4855de20f67b4be8d8866d5d`. The complete freeze gate passed before runtime work. All 546 frozen files / 11,313,625 bytes remain unchanged. The [preflight record](../../language-design/string-concat-v0.1/freeze/PREFLIGHT-GATES.json) binds 122 passing C086 observations across 115 distinct states.

Actual current-scope results at the runtime above are:

| Scope | Result |
| --- | --- |
| Source and literal controls | 118 source states, 85 explicit `.19` literal controls and 28 inherited negative controls passed independent checks. |
| Resource boundaries | All 104 records passed independent scalar, charge, stopping-prefix, reservation, cancellation/deadline and current-authority checks. |
| Agent lifecycle | Eleven workflows, 224 raw exchanges, 217 durable request identities, ten durable artifacts and fourteen retrieved complete artifact roles passed the hardened independent reader. |
| Hostile evidence | 75 supplied-byte GLB adversaries and two coherent Agent-history mutations were rejected as required; positive controls passed. Three additional schema-valid partial-inspection corruptions are also rejected. |
| Native destination | Seven source plus fourteen Agent roles passed Khronos/Three.js validation, 21 actual PNG decodes and five recorded poses per role. All 42 captures were directly reviewed. |
| Original literal controls | All seven current `.19` panel-control GLBs are byte-identical to their original pre-implementation C086 exports. |
| Focused runtime checks | Eighteen focused tests passed: six current binding tests and twelve immediate-predecessor interface tests. |

The complete current evidence assembles **three separately executed sections**: source attempt02 and Agent attempt01 with producer v01, and boundary attempt03 with producer v03. All use the same unchanged published runtime. Exact code snapshots, derivation patches and per-scope dependencies are retained; this is not one invocation or a claim of one identical harness version.

The [selected review inventory](review/MANIFEST.json) preserves exact core, binding, boundary, reader, visual, literal-comparison and producer-lineage reports. The core author independently reviewed the separate interface implementation, including exact structural derivation of all three `.20` schemas. The bindings author independently reviewed the core and all 104 resource-boundary observations. The separate source/Agent/destination reader owner supplies the complete supplied-evidence checks. Complete raw logs, artifacts, earlier reader versions and failures remain in the final handoff under their recorded roles; absolute paths inside copied reports identify their original execution locations.

The complete immediate-predecessor `.19` corpus also passed: 184 source states, 122 controls, ten workflows, unchanged independent source/Agent readers and fifteen native roles. All 30 captures were directly reviewed. All **88 complete GLB role streams (74 unique streams)** are byte-identical to retained C086, including raw JSON, BIN, framing, padding and hostile suffixes. There is no normalization or metadata allowance. These overlapping scopes are not additive release totals.

## Completed inherited development gate

The original inherited `--full --force-agent` invocation at the unchanged runtime remains **failed: 33 of 34 roles passed**, and the documentation role found one nonexistent link in this new engineering README. All **3,979 unit tests**, the separate **106-test Agent cohort**, and all six browser roles passed, with zero skips or expected failures. All **35 browser captures were directly reviewed** with no blocking findings. Complete before/after inventories preserve all **8,757 tracked files** and Git identity. The sixteen external-attestation cases remain pending.

The separately published documentation repair at `07117b02517dd920a8ebc8539943e01ee1075039` changed no production code, tests, inherited tools, workflows, examples or frozen inputs. A fresh execution of the unchanged preservation/link checker passed: 29 preserved sources, 233 sections, 499 documents and 3,087 local links, with zero failures. All 8,800 tracked files and modes at that recovery cut remained exact. The [independent recovery decision](inherited-recovery/SCOPED-DOC-RECOVERY-DECISION.json) and [completed independent closure](inherited-recovery/SCOPED-DOC-RECOVERY-CLOSURE.json) establish **33 original passing roles plus one separately recovered documentation role**. A single full invocation did not pass. The failed original summary and log are retained as exact copies in the [inherited proof inventory](inherited-recovery/MANIFEST.json), alongside the passing recovery and finite visual review.

The [validation summary](VALIDATION-SUMMARY.json) binds the actual source cuts, observations, review and retained limits. The [integration record](integration.json) records the bounded expected-head lease and the pending exact-candidate review, PR #86 merge and resulting-main checks. Archive sealing, fresh recovery, actual-package audit and durable save/readback remain separate delivery steps until their external completion records exist.

## Preserved corrections and limits

Original input drafts and failed preflights remain separate from the adopted freeze. Runtime and frozen expected bytes have not changed after their publication. Two boundary-producer caller-cap wiring omissions were corrected in the harness; the original context-mismatch refusals remain preserved. A later run records complete actual operands for independent audit. Source/Agent readers corrected preparation assumptions without rewriting expected semantics.

Independent review found that an earlier Agent reader accepted incomplete or mistyped partial inspection projections. The hardened reader rejects three separately frozen corruptions, while the unchanged full workflow and one-object positive controls pass. The earlier pass is retained as incomplete-reader evidence. The first hostile Agent copy attempt also modified reader-created, uninventoried SQLite WAL/SHM auxiliaries; all 724 inventoried producer files and the main database remain exact. Its observed auxiliary bytes and failure are retained. The pre-write transient 32 KiB SHM was fingerprinted but not saved, so those former auxiliary bytes are unavailable. Fresh hostile checks use a clean combined baseline, private SQLite copies and immutable read-only inspection.

All [retained gates](RETAINED-GATES.md) remain binding, including the failed Original28 gate, external attestations, unexecuted interpreter matrix, broader reach/physics/engine work, original storage failures and disclosed unavailable history. No hosted workflow or continuation schedule was started. Finite exports and browser poses establish no Unreal import, live engine physics or measured authoring benefit.

After verified C087 integration and complete delivery, [the proposed C088 task](NEXT-TASK.md) reviews exact membership inspection for sparse dimension overrides. Its [supporting source and workaround evidence](next-task-basis/SOURCE-BASIS.json) preserves the existing reduction/conditional workaround; this proposal is not an adoption or implementation.
