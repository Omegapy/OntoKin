# OntoKin C093 handoff

Date: November 3, 2026 (America/Denver).

## Current outcome

**The original A08 Agent export still fails its unchanged deadline. C093 is a
blocked development checkpoint, with one bounded runtime candidate retained.**
Its ownership controls pass, but the sole final export reaches 310,430 operations
and reports 30,001.007428 ms before returning `OKL-E-RESOURCE` with
`budget_reason=execution_deadline_exceeded` at `recording_export_readback`.
The independently inspected store contains zero artifacts and zero runs.
The agreed stop condition has been applied; no further runtime optimization or
A08 retry was performed.

The separate native-verifier correction implements the supported parent-site
marker route and retains the original verifier unchanged. All 67 fresh CLI
exports/repeats/helper variants passed on the published C093 candidate, and the
unchanged delivery audit confirms the exact required membership.
All 36 required native variants passed, including the full p28 parent-site helper case. The aggregate audit verified 219,462 executed clock-side rows, 1,859,723 carrier observations and 533,211 geometry scalar checks. All 108 actual gate captures received direct visual review with no reported visible blocking defect. Wide framing, tiny carriers and occluded markers limit fine visual claims; source geometry and bounded pose agreement are checked by the separate native numerical checks. This closes the identified current native scope while A08 remains failed.

The tested published commit is
`fab1137e7b3e24d656ed4ba7cfd55935b6b2f241`, tree
`1a96a35ab64d3e62743bfbc72525f94686f20a2b`.
The product package is
`sha256:46f6f5aa45866ceeb79f9065ff30412c822715815d5d928cf7faa98183ce2aaf`.
The source-pose basis remains version `0.4`, method
`ontokin.source-pose-projective-dyadic-torque/0.2`; its actual implementation
identity is `sha256:35752a65207742d7334b4ce539c55dc97bc306c94f34c67a46e6ed04d6e8a194`.
Its derivation identity remains
`sha256:11a74707f182e8ffb568f6246f5fae653d5a1d4d5098a752e55d98420856c1be`.
The exact closing documentary HEAD and its remote readback are in the outer
`PUBLICATION.json` and `C093-CHECKPOINT.json`. `PRODUCT-BINDING.json` proves that
all 189 Python product modules and both controlled destination modules have the
same bytes, native blobs and modes as the tested product.

Work remains on `work/c091-finite-torque`, draft
[PR 90](https://github.com/Omegapy/OntoKin/pull/90), owned for this bounded
continuation by `interactive-c093-export-20261103-root`. Main was observed at
`94a7796a54725ca764b2027deb43f09204f8a6de`. Shared STATUS is unchanged; no main
integration lease, main merge, hosted workflow or continuation schedule was
started. A saved observation does not establish future ownership.

## Bounded runtime change and its limits

The [scope](SCOPE.md) follows the exact [C092 next task](../canonical-spin-amendment-2026-11-03-c092/NEXT-TASK.md).
Product edits are confined to `ontokin/torque_canonical_spin.py` and
`ontokin/torque_runtime.py`. The implementation compiles fixed import-time identity
catalogs into direct ordered predicates. The catalogs contain owned native
objects; the generated source comes only from trusted templates and integer
indices. There is no request-derived or source-derived generated code and no
cached successful admission.

Every original admission still reads live state at the original boundary.
Strong owner references and exact comparison order remain. The generated
callables have no defaults or keyword defaults; their code, defaults and keyword
defaults are checked against private owning receipts before every dispatch.
Generated predicate bytecode performs no global/name/import resolution. Class,
descriptor and MRO checks remain before ordinary instance lookup. Original
source watches and detached operand watches remain unchanged.

Compilation is bounded to 4,096 primitive comparisons and 512 KiB of generated
text. A larger catalog uses the unchanged generic evaluator. It does not acquire
a new source refusal. Private-entry checks retain the separate slot,
keyword-dictionary-content and present-to-absent-binding groups; helper checks
retain absent-to-present ordering. Original callbacks, callback counts, real
work charges, cancellation/deadline handling, exception precedence, rollback,
cache admission and ownership rules remain in place.

The fixed 96-bit canonical rule, ordered 96/192/384/768/1536 precision stages,
numerical formulas and resource ceilings remain exact. The narrow native
immutable-owner/private-closure convention is the same as C092. These controls
do not establish a general hostile-Python sandbox.

The selected guard microbenchmark reports a combined ratio of 1.332704 for its
measured predicate groups. It is a local cost diagnostic. The A08 operation
prefix is larger in this environment, but the request still fails; neither
measurement establishes completed-export throughput or an end-to-end speedup.

## Executed runtime and preservation evidence

| Scope | Actual C093 result | Boundary |
| --- | --- | --- |
| Original focused and callback tests | 29 + 20 passed | Root-executed prepublication candidate bytes independently joined to the published candidate |
| Retained independent callback attacks | 31 passed | Old expected fields remain exact except traceback locations; foreign execution remains zero |
| New generated-callable controls | 30 mutations + one exception-precedence control passed | Ten actual generated receipt locations, each with code/default/keyword-default mutation |
| Compiler controls | Seven methods passed on each of CPython 3.11.17, 3.12.14 and 3.13.16 | 21 method runs; not the full inherited interpreter acceptance matrix |
| Immutable inputs | 24 authority files, 399 original inputs, 27 C091 overlays, 346 original tests and nine protected modules preserved | Actual published-source closure checked |
| Product and AST preservation | All 191 product files bound; 189 unchanged from C092; 59 runtime and 27 helper definitions unchanged | Includes source watches, point/cache/numerical paths, callback installation order and generic fallback structure |
| Original A08 baseline | Failed at 241,714 operations / 30,000.806062 ms | Exact recovered C092 product, fresh C093 observation |
| Sole C093 A08 candidate | Failed at 310,430 operations / 30,001.007428 ms | Actual immutable published C093 product; unchanged original request and limits |
| A08 durable integrity | Four closed schemas, exact stored payloads and SQLite integrity passed; zero artifacts/runs | Failed-request atomicity and source binding, not export acceptance |

The A08 response timing includes failure handling. Its candidate deadline
diagnostic records 30,000.006523 ms; the baseline diagnostic records
30,000.055278 ms. Both use the original 1,000,000-operation / 30,000-ms
production allocation. Candidate creation succeeded at 7,865 operations /
897.826587 ms; baseline creation succeeded at 7,865 operations / 949.228819 ms.
The exact unchanged 5,049-byte A08 probe has SHA-256
`f14f0327939f93a54c0c5e026d1d24109d78904e8bd3d6d083fd79fb85580b85`.
Its historical project identifier and uncommitted-draft wording are preserved.
Separate supervision and publication receipts establish the actual current pin.

The initial publication receipt's
`product_code_unchanged_from_tested_pin: false` records absence of the optional
comparison argument, rather than a failed equality result. The original receipt
is unchanged. `c093-publication/CANDIDATE-METADATA-CLARIFICATION.json` explains
the implementation of this flag and checks all 191 actual published product
blobs, bytes and modes. The closing publication passes the explicit tested pin
and performs the equality check. This clarification does not change A08's
failed status.

## Separate native helper correction

`tools/verify_torque_native_dense_c093.py` is a new identified verifier; the
original `tools/verify_torque_native_dense.py` remains byte exact. Its frozen
[design](NATIVE-ORACLE-DESIGN.json) derives expectations from the source/export
contract before reading C093 artifacts. The supported `joint_parent_site`
marker is checked against joint path, related source element, parent frame,
name and `physical_participation=none` metadata. Unknown helper kinds, altered
identity, geometry, material or native attributes still refuse.

The marker is a gold sphere of radius 0.025 m, 12 segments and six bands,
62 vertices and 120 triangles, without an axis bar. Its PBR base color is
`[0.9, 0.65, 0.08, 1]`, metallic factor zero and roughness 0.7. For p28's `hold`
joint it follows `carrier.tip.frame` at world position `(min(t, 1), 0, 0)` with
identity rotation. It remains at x = 1 after release and carries no active
constraint or released-ball following semantics.

All 11 focused positive/malformed controls passed. A separately labeled
historical control reproduces the old checker's `Unknown requested helper` on
the original C092 p28 artifact and validates its actual native geometry with
the corrected checker. That historical geometry control alone does not certify
new C093 delivery. Fresh C093 artifacts carry the actual current basis identity;
their exact manifest and the predeclared four disjoint native shards are
retained. Native offline work remains capped at 100,000,000 operations and
900 seconds per case; the original A08 request retains 1,000,000 operations and
30,000 ms. Ordinary production defaults remain 100,000 operations / 30,000 ms.
Native checks and visible-image review have distinct scopes. The actual native observation streams were rehashed and counted. The original runner does not persist its independent interval/bound detail rows; their recorded digests remain retained-only evidence and were not independently rehashed. The audit and contact-sheet headers retain their original pre-review labels; later visual receipts close that review separately.

## Evidence, failures and review ownership

[VALIDATION-SUMMARY.json](VALIDATION-SUMMARY.json) binds the exact executed
cohorts, pending release roles and acceptance status.
[REVIEW-MATRIX.json](REVIEW-MATRIX.json) distinguishes source-author validation,
root approval and the separate independent reader and recording/durable
reviews. [EVIDENCE-INDEX.json](EVIDENCE-INDEX.json) gives principal receipt
paths, byte counts and hashes. Those evidence paths are relative to the new
`c093-evidence` root in a completed recovery, unless explicitly labeled as
predecessor evidence. Original absolute execution paths remain provenance.

The source author supplied the guard implementation and author-side structural
proofs. The independent reader separately reviewed ownership, ran the retained
and generated mutation controls, and reconstructed the publication proof.
The recording/durable reviewer authored the separate native oracle, ran the
fresh CLI and native work, and inspected an exact copy of the root-executed
sole A08 store; the reader reviewed the correction and integrity bindings.
Root separately ran the original focused/callback cohort and reviewed the design. No author
review is represented as independent approval of that author's own code.

All earlier failed A08 attempts remain exact inside the full C092 predecessor.
New failed harness attempts are also preserved: the baseline store wrapper's
directory comparison encountered inspection sidecars; a subsequent wrapper had
a syntax mistake; the first publication audit expected `accepted` instead of
the API's `succeeded`; a recovery-guard harness expected a size refusal where
the changed same-length body correctly produced a hash refusal. The separate
corrected attempts retain their real outcomes. The stager's initial review
found output-overlap, linked-root and membership-change gaps; its revised
version passed six targeted controls and independent review. No failure is
deleted or relabeled as a successful product run.

The final evidence selection includes the ordinary files under every declared
C093 work/review/publication/packaging root, private validation outputs, native
capture records and selected exact prior delivery observations. Explicit
negative-test link and empty-directory recipes are retained. Dependencies,
duplicate checkout bytes, physical native pack wrappers, final assembly and
acyclic final delivery observations have stated exclusions.

## Recovery and continuation

The standalone handoff preserves the entire exact C092 ZIP, all new native
objects and source, all selected new evidence and the reviewed recovery helper.
Use its outer `README-START-HERE.md` and require a fresh successful recovery.
The helper runs the unchanged C092 recovery, restores its late failed-prefix
layer, records the verified source relocation, independently decodes the
nonthin C093 native delta, and checks source/index/refs/native history and all
six evidence layers. No product code or network dependency installation is
needed for archival recovery. Final sealed-archive recovery is a separate
post-seal observation; the archive cannot contain its own final hash receipt.

Follow [NEXT-TASK.md](NEXT-TASK.md) from the measured A08 blocker. The broad
Agent/durable, full small-chunk artifact reads, hostile-artifact, compatibility
and inherited release sequence was not rerun for C093 after the bounded stop.
Passing scoped controls and native evidence cannot stand in for that sequence.
The original acceptance contract remains the complete requirement.

[RETAINED-GATES.md](RETAINED-GATES.md) preserves Original28 at 24/28 and overall
failed, P11/P16/P23/L03, all 16 external attestations and every remaining GOAL
domain. This handoff records useful bounded work and an unresolved production
gate. It does not establish a torque release, named live-engine support,
measured authoring benefit or full OntoKin acceptance.
