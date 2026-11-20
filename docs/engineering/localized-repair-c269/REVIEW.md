# C269 independent candidate review

## Decision

**Approve the bounded coverage audit at commit `4258e001a567ff830b790a174f8bdde9d368f05a`, tree `63b4b6f367c1a548dc1e1e00b65a4bedc5b6bb1a`. No mandatory correction to this candidate was found.**

The audit supports **24 complete groups and four partial groups, H16/H20/H22/H24**, containing **99 material subcases: 94 complete and five partial**. Contract-wide C260 qualification remains **unestablished**. A complete audit can correctly report incomplete qualification. These counts describe the reviewed evidence classification; they are not a new behavioral execution or a product quality metric.

This review accepts C269 R01–R04 for the exact audit content. R05 integration and R06 final delivery/closure remain Director-owned gates. It does not mark the task complete, authorize a second phase, or certify a future ZIP. [Requirements](../../workflow/tasks/C269/REQUIREMENTS.md), [plan](../../workflow/tasks/C269/PLAN.md), [machine review](REVIEW.json).

## Candidate and review independence

Reviewer: `/root/state_audit`, separate from the two H-group investigators and the Director who synthesized the candidate. The reviewer inspected the immutable Git object rather than treating the working branch name as identity. The Director later reported a main lease renewal at `a255b8e2790f49df4b22074a9dfc3f8ee8a4e85b` and a deliberately dirty local STATUS file. Neither is substituted for the reviewed candidate. Current remote publication and integration checks remain attributed to their actual observers.

The full change inventory from baseline `23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb` contains **84 paths: 82 additions and two modifications**. Additions are confined to the C269 engineering evidence and task directories. The only modified pre-existing files are `STATUS.md` and `docs/workflow/CURRENT.json`; their diffs establish the active scope and lease. No implementation, test, fixture, contract, semantic, dependency, budget, or hosted-workflow file changes. The exact inventory is retained in [CANDIDATE-INSPECTION.json](evidence/independent-review/CANDIDATE-INSPECTION.json).

The combined [COVERAGE.json](COVERAGE.json) preserves both original investigators’ group/subcase data. Its only reconciliation additions are source-map bindings, stable missing subcase IDs, and default source revisions. The original maps and reports were read in full, alongside the full audit and next-task proposal:

- [H01–H14 map](evidence/audit-h01-h14/MAP.json) and [report](evidence/audit-h01-h14/REPORT.md).
- [H15–H28 map](evidence/audit-h15-h28/MAP.json) and [report](evidence/audit-h15-h28/REPORT.md).
- [AUDIT.md](AUDIT.md) and [NEXT-TASK.md](NEXT-TASK.md).

## Evidence identity and reuse

The earlier independent [READINESS.json](evidence/independent-review/READINESS.json) and [READINESS.md](evidence/independent-review/READINESS.md) remain applicable. That review made 1,139 static identity checks. It verified the actual original C268 main execution at `5084dd69312e8da5a49aadd33cf83ba56db7c058`, its runner, commands, environment, input/output identities, and method-log bindings. It did not rerun those methods.

The original cohort contained 159 input identities. Exactly 152 match the C269 baseline; seven original-to-baseline differences are historical documentation/state transitions. All 30 original output identities remain exact. The candidate adds only the two scoped canonical-state edits among those original inputs; protected behavioral inputs remain unchanged. The original 12 groups and 282 methods are historical execution evidence, not a substitute for the present subcase review. [Original receipt](../localized-repair-c268/evidence/finalization-a3de3dd23bbf/main-integration/CHECKS.json), [reuse assessment](evidence/EXECUTION-ELIGIBILITY.json).

The reviewer preserved two limits in the older detailed ledgers. C261 run-03 names a local execution revision unavailable in this checkout; its recorded implementation/control bindings and the available published reader equivalent are kept distinct. C265 run-06 retains precise code and input identities but no embedded Git execution revision. Identical source tests were later executed in the revision-bound C268 cohort. That later run is not relabeled as the earlier detailed run. Some older mutations retain deterministic recipes and hashes without a complete generated-byte archive; this is stated as an evidence-retention limit.

## Semantic coverage review

The reviewer checked actual mutation recipes, independent expected-value construction, assertions, typed outcomes, and interface boundaries. The C265 source controls build numerical expectations with separate exact arithmetic. C266/C267 fixtures construct source/provenance/hinge expectations from authored recipes rather than observer output. C268 supplies separately enumerated original hinge/site expectations and explicit changed-source/artifact recipes. The H20 observer-derived projection is identified below and is not promoted to full independent coverage.

The reviewer also decoded selected retained C267/C268 GLB JSON and source bytes using only the standard library. These checks confirmed source-only and paired initial changes, the H13 site-key mutation, the H20 singular `follow` field and bundled owner change, the H28 nontrivial pose, and the same artifact-only initial mutation across all three relevant interfaces. SHA-256 and byte-count checks bind those bytes to the original recorded outcomes. No observer was imported or called. [Inspection script](evidence/independent-review/review_candidate.py), [inspection result](evidence/independent-review/CANDIDATE-INSPECTION.json).

| Group | Reviewed classification | Independent assessment |
|---|---|---|
| H01 | Complete | Both exact originals have separately enumerated eight-hinge, sixteen-site expectations and complete field/identity checks. Raw interfaces keep historical authority false; C268 admits the fixed bytes. |
| H02 | Complete | The actual source initial becomes 0.25 with refreshed provenance while the retained artifact remains zero. Comparison records the expected initial-field mismatch. |
| H03 | Complete | The same one-row artifact mutation to 0.5 is observed raw, rejected by comparison, and rejected by historical admission with its actual hash. |
| H04 | Complete | Paired 0.25 changes agree under independent expectations. C268 separately rejects changed entry, leaf, and artifact historical bytes, preserving false accepted-revision authority. |
| H05 | Complete | Lower and upper limits each have source-only, artifact-only, and paired controls. The two paired successes check independent actual values; disagreement cases require the correct field refusal. |
| H06 | Complete | Lower/upper equality, zero-width ranges, reversed limits, and both out-of-range directions have explicit source/raw/comparison assertions. |
| H07 | Complete | Signed deg/rad conversion, negative zero, exact Pi64 arithmetic, halfway/fractional cases, and adjacent/subnormal disagreements are asserted independently. This is finite coverage, not exhaustive numerical certification. |
| H08 | Complete | All six basis axes and the paired reversal preserve explicit signs. One-sided reversals disagree; raw admissibility is not confused with source agreement. |
| H09 | Complete | Zero/nonunit malformed axes and source-valid nonbasis/near-unit unsupported axes have distinct typed assertions and retained outcomes. |
| H10 | Complete | Wrong shapes/types, booleans, nonfinite components and tiny replacement components are exercised. Opposite sign is correctly observable raw and refuses only when compared with a different source axis. |
| H11 | Complete | Literal-profile refusals cover parameter/reference, arithmetic, call, and conditional forms. A separately declared typed Angle parameter with the original zero default supplies the material parameter case. |
| H12 | Complete | Actual joint-name and key changes independently affect lexical paths and IDs; stale artifact claims are refused. |
| H13 | Complete | Endpoint names, keys, and part paths have separate authority. The actual site-key change modifies derived source IDs without a fabricated artifact site-key field. |
| H14 | Complete | Ordered swaps, paired reversal, same-object sites, wrong-object sites and suffix-only guesses have explicit assertions. Endpoints are not treated as an unordered pair. |
| H15 | Complete | Own/direct-part lexical access and public child access pass, while inaccessible private external sites refuse through source and comparison boundaries. |
| H16 | Partial | Unsupported origin/keyed/deeper/scene/non-hinge and hidden-declaration cases are supported. A genuinely declared or computed source-valid SiteRef remains unproved. |
| H17 | Complete | Missing fields/visibility, ambiguity, declaration/member collisions, constructor/self shadowing and quoted-syntax cases have actual whole-input refusal assertions. |
| H18 | Complete | Required site fields and literal interface/size compatibility are checked. Pose is retained as a source witness; no evaluated or world-space pose authority is inferred. |
| H19 | Complete | Independently enumerated actual keyed memberships, helper/override cases, opaque keys, and invalid/empty membership boundaries support the source/object/comparison sets. |
| H20 | Partial | Raw unrelated-field and bounded nonclaim evidence exists. The source expected projection is partly observer-derived, and actual owner/follows/motion comparison changes are not each isolated. |
| H21 | Complete | Omitted/extra/duplicate/renamed joints and objects, cross-pairing and reordering are exercised. Source-relative complete-set agreement belongs to comparison, not the raw reader. |
| H22 | Partial | Stale source/import pins, manifest/revision, repeated mappings and definitions have extensive exact controls. No isolated literal missing-import-digest execution is identified. |
| H23 | Complete | Raw claims, source witnesses and negative authority assertions keep absent direct artifact site/definition/span fields absent. |
| H24 | Partial | Structural and major resource limits have typed whole-input failures. Exact 128-hinge/256-site admission exists; an actual input exceeding 256 distinct sites is not established. |
| H25 | Complete | Numeric length, explicit/adjusted exponent, scaled-unit, overflow, and underflow cases have independent assertions. Static code also confirms bounds precede costly conversion. |
| H26 | Complete | Missing/size/hash, symlink/loop/escape, permission and related file-access cases have actual records. Reads are bounded, early refusal avoids comparison, and no ambient/network fallback is introduced. |
| H27 | Complete | Supported changed raw inputs are exercised with independent fields and explicit false authority. Their separate historical rejection does not invalidate raw behavior or confer accepted-revision qualification. |
| H28 | Complete | An actual nontrivial pose preserves declared hinge fields under independent expectations while pose/world/physical authority remains false. This satisfies the narrow nonclaim control without resolving H20. |

Every row is bound to the precise assertions and original record selections in [COVERAGE.json](COVERAGE.json). The reviewer’s machine record also retains per-group acceptance and support paths. The principal assertion sources are [C265 source controls](../localized-repair-c265/test_source_hinges.py), [C261 independent controls](../localized-repair-c261/evidence/independent/independent_controls.py), [C266 binding controls](../localized-repair-c266/test_hinge_binding.py), [C267 comparison controls](../localized-repair-c267/test_hinge_compare.py), and [C268 historical-reader controls](../localized-repair-c268/test_endpoint_reader.py).

## Why the four gaps remain open

**H16.02 — declared/computed SiteRef.** The source test uses undeclared `self.ref` and `site(self.pivot)`, and accepts either malformed or unsupported categories. The retained outcomes distinguish those two cases, but they do not prove a source-valid declared/computed SiteRef with an exact unsupported expectation. Existing well-formed origin/keyed/deeper cases do not fill that gap. [C265 control](../localized-repair-c265/test_source_hinges.py), [H16 map](COVERAGE.json).

**H20.01 and H20.03 — independent invariance.** The standalone source invariance control constructs its expected projection from the observer’s original result. Independent baseline/length controls and other nonclaim checks provide useful support, but do not independently assert each changed geometry/action case. The C267 bundled metadata control writes singular `follow`; the actual field named by the relevant controls is plural `follows`. Its owner/geometry/translation changes are bundled. C261’s separate raw `follows` and `boundary_states` mutations and C266’s binding-only result must retain those narrower boundaries. [C265 source controls](../localized-repair-c265/test_source_hinges.py), [C267 metadata control](../localized-repair-c267/test_hinge_compare.py), [C261 raw controls](../localized-repair-c261/evidence/independent/independent_controls.py).

**H22.02 — missing literal import digest.** Changing leaf bytes while retaining or refreshing an existing import digest tests stale-pin behavior. Missing fields in artifact provenance test a different input. Neither constitutes an isolated removal of the source import’s digest. The audit correctly leaves this subcase partial; static mandatory-digest parsing and generic malformed truncation are not represented as that execution. [C265 source controls](../localized-repair-c265/test_source_hinges.py), [C266 provenance controls](../localized-repair-c266/test_hinge_binding.py), [C267 provenance controls](../localized-repair-c267/test_hinge_compare.py).

**H24.04 — excessive sites.** With two endpoint references per hinge and a 128-hinge ceiling, more than 256 distinct referenced sites cannot reach the dedicated site-count guard after that earlier bound. This explains why the guard is redundant; it does not manufacture an executed excessive-site control. The audit separately records exact 256-site admission and the absence of a supplied excessive-site outcome. A later explicit decision about redundancy or a deliberately combined-limit control belongs to another phase. [Raw guard ordering](../localized-repair-c261/hinge_glb.py), [C265 resource controls](../localized-repair-c265/test_source_hinges.py).

Two potentially misleading interpretations were checked explicitly. H13 does not require a nonexistent direct artifact site key to disagree: actual retained source keys are `pivot.key-2` and `base.key-2`, while lexical artifact endpoints remain `.pivot` and `.blade.base`. H28 requires a nontrivial pose/geometry **or** motion case with no world/physics inference; C267’s actual `(999, -123, 0)` pose and quaternion `(0, 1, 0, 0)` satisfy that narrow control. It does not claim independent isolated invariance for all H20 fields. [Frozen control plan](../localized-repair-c260/CONTROL-PLAN.md), [actual C267 assertions](../localized-repair-c267/test_hinge_compare.py).

## Fresh verification and limits

The Director’s fresh checks on the clean exact candidate passed documentation preservation/navigation and workflow structure. The reviewer checked their candidate revision/tree, runner identity, success statuses, and the complete log hashes. The source-reference receipt is bound to the exact coverage-file digest and reports 218 input identities, 259 assertion references, 177 result references, and 1,865 selected-case references. These are structural checks; their own receipts explicitly reserve semantic truth for review. [Candidate checks](evidence/candidate-checks/CHECKS.json), [reference checks](evidence/candidate-checks/references.json).

The independent final inspection passed **1,882 static checks**. It rechecked all 218 input identities, both original maps’ preservation, the 159 historical input/30 output identities, each selected recorded outcome, the complete changed-file scope, source locations, selected actual retained payloads, and fresh-check bindings. Combined with source-level review, this resolves the final-readiness conditions. The checks did not execute the original behavior, an exporter, a native/model trial, or new controls.

The first independent inspection had one reviewer-helper failure: it guessed the renamed H13 keys as `parent-key`/`child-key`. The retained fixture and original authored test use `pivot.key-2`/`base.key-2`. The helper was corrected, and the original failed report and script are preserved. This is not a candidate defect. Other inspection lookup/formatting errors are recorded in [INSPECTION-NOTES.md](evidence/independent-review/INSPECTION-NOTES.md). Historical failing attempts remain untouched.

## Next action and acceptance boundary

The proposed [next task](NEXT-TASK.md) is appropriately bounded: in a separately authorized phase, establish one smallest source-valid declared/computed SiteRef control for H16. Freeze the input bytes and independent expected category first; justify the source form from adopted language rules; then test the source API and applicable comparator refusal with retained identities and no partial qualified set. If that reveals an implementation defect or source-rule ambiguity, retain it and propose a separate correction. It does not authorize a contract amendment, profile expansion, product qualification, or a hidden fix in C269.

The Director may now complete the existing integration and delivery gates. Preserve this candidate’s audit/map/next-task content and all historical evidence. Add the review/check/lease records under their actual identities, run applicable fresh documentation/workflow checks on the published and actual-main states, verify final delivery, release the lease, and stop. Any substantive alteration to the coverage judgments, evidence bindings, or proposed next scope requires renewed independent review. The four open groups remain open after this approval.
