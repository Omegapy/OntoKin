# C268 exact-candidate independent review

## Verdict

**Eligible for R01–R05 acceptance and the Director's reviewed integration.** No unresolved mandatory implementation finding remains. The original endpoint-selector resource finding is resolved on the exact reviewed bytes. This review does not perform or accept R06 integration, resulting-main checks, branch disposition, or R07 saved delivery.

Reviewer: `/root/review_c268_final`, an actual separate worker from the implementer and control author. The Director is `c268-final-ee457d84062e`. The reviewer made no implementation edits, commits, external writes, lease changes, or child-worker assignments. All execution used a separate local clone; only review artifacts were written.

## Candidate, scope and policy

| Identity | Value |
| --- | --- |
| Assigned local candidate | `52af987fd5705c034bf264e2fe3fbc9fa1f146ae` |
| Published candidate reported by Director and used by fresh cohort | `e6f55b73fa71953aa648bcd34711a6796a7346b6` |
| Independently verified common tree | `d94436a22552db903b8016f9d035985a7d8b6752` |
| Reviewed current-main base | `409ef18e0cb992ad1ab771c1258e989d5ef1c765` |
| Prior mandatory-finding candidate | `734789521f82248d39b623c33aae9d3284ab4bce` |

The reviewer independently checked both Git tree objects, an empty whole-tree diff between local and published candidates, and base ancestry. The review therefore applies to the published candidate through exact tree equality. The Director owns remote readback; this worker did not independently query GitHub. The final cohort independently records the published commit and common tree before and after execution.

All 116 cumulative changed paths against the supplied current-main base are within `docs/engineering/localized-repair-c268/` or `docs/workflow/tasks/C268/`. Source dependencies C257/C261/C265/C266/C267, historical sources/GLBs, C260 contract/control plan, product implementation, hosted workflows, and C262 are unchanged. Apparent predecessor code additions in the diff are copies under C268 evidence, not replacements of those components. [COHORT-AUDIT.json](COHORT-AUDIT.json) records the complete path inventory and identity checks.

Full AGENTS, GOAL, ROLE, workflow PROTOCOL/worker template, C268 requirements/plan/task, C260 CONTRACT/CONTROL-PLAN/INPUTS, C268 implementation/coverage/input records, implementation, control fixtures, all 895 test lines, check runner, prior finding, relevant evidence and complete transitive code closure were read. The candidate tree contains only the root `AGENTS.md`; there are no applicable nested AGENTS files. Exact read identities are in [READ-SET.json](READ-SET.json).

The approved scope expressly excludes full product tests and selects the complete isolated observer cohort. This fits OK-ENG-006 section 2's actual-change selection and OK-ENG-009 section 3's affected-regression requirement: no shared product or release machinery changes here. The generic AGENTS routine-driver instruction is narrowed by the current specific C268 scope and the Director's explicit assignment. No unresolved concrete policy conflict was found. The standalone `tools/check_local.py`, full product discovery/conformance/export, native/visual/model roles, other interpreter compatibility and hosted workflows were not executed or credited. This is not a release or whole-product qualification.

## Requirement findings

| Requirement | Review disposition and evidence |
| --- | --- |
| R01 historical identity | Eligible. Literal immutable reader pins match all five C260 byte identities and C253 matching pins. Only the selected endpoint's main source, shared leaf and GLB are read. Runtime manifests, alternate endpoints, sidecars, network and expected-record substitutes cannot provide admission authority. Independent original-source expectations pass for both endpoints. |
| R02 safe bounded access | Eligible within the finite documented POSIX API. Exact selector type/length is checked before membership. String paths are checked for length, encoding, components and traversal. Descriptor-relative `O_NOFOLLOW` opening checks every root/input ancestor and leaf; regular type and exact size precede the single size-plus-one read. Hash, size changes, short reads and timestamps are checked before comparison. Refusals contain bounded available identities and no qualified partial set. The existing independent controls cover actual and injected permissions, symlinks/loops/ancestors, FIFO/nonregular files, growth/shrink/read faults, cleanup and path bounds. Optional native-Path preprocessing note O01 is below. |
| R03 comparison and authority | Eligible. Every dependency is captured and hash-admitted before any is compiled. Private per-call acquisition adapters supply the captured modules; comparison bodies remain exact. Post-capture dependency-path replacement succeeds solely on captured code, and the next call refuses the replacement. Original whole-result parity is exact after removing only the declared wrapper additions and replacing its one historical-limit sentence. Source-only site compatibility, absent direct artifact provenance, all false qualification flags and comparison refusal details remain intact. |
| R04 independent controls | Eligible for the historical portions of H01/H03/H04/H26/H27. Separate controls plus independent reviewer probes exercise original endpoints, changed raw bytes and isolated historical-stage refusals. Neither test counts nor these results claim complete H01–H28 qualification. Each original endpoint has eight hinges, one shared joint definition, sixteen endpoint sites and eighteen objects. |
| R05 exact verification/review | Eligible. Fresh published-candidate cohort: 12 groups, 282 methods, 14 C253 bindings, zero failures/errors/skips. The reviewer verified all 157 input identities against candidate Git blobs, all 30 output receipts and their published-evidence copies, runtime/runner identities, full C268 per-call accounting and retained failed evidence. Mandatory finding re-review and separate exact-candidate scrutiny are complete. |

### Required finding resolved: endpoint-selector lookup bound

The prior 14,883-byte reader, SHA-256 `f615f14f5d4bcee3a3ecdb20466fd60b0a04df2dcd13095d993baf20b1430086`, consulted `PINS` immediately after its type check. Hashing a newly supplied long built-in string could scan its full length before refusal. The mandatory original [finding](https://github.com/Omegapy/OntoKin/blob/e6f55b73fa71953aa648bcd34711a6796a7346b6/docs/engineering/localized-repair-c268/evidence/review/ENDPOINT-BOUND-FINDING.json) remains in candidate history.

The current 14,914-byte reader, SHA-256 `a7bb1f67398a54922e647d6d43062f89acb32c6e05a2fc653f5c30160f888157`, adds only `len(endpoint) not in (5, 6)` before membership. An exact byte replacement proves this is the sole reader delta from the preserved prior source; that source snapshot also equals the prior commit's Git blob. The test change is additive: fourteen inserted lines, no removed assertions.

The fresh deterministic [selector probe](selector-guard.json) shows that lengths 0, 7 and 1,000,001 never reach the pin-membership spy; an invalid five-character selector reaches only the bounded lookup and then refuses. No timing threshold is involved. Both accepted endpoints retain their original semantics. The full 35-method control suite includes a separate long-selector membership spy and passes on the exact fixed bytes.

### Optional suggestion O01: native Path preprocessing

`_root_path` converts an exact native `pathlib.Path` to text before applying `MAX_PATH_BYTES`. On the qualified CPython 3.12 runtime, a lazily represented Path can therefore parse a long original representation first. A labeled probe observed native parsing of 200,001 characters, followed by the expected `RESOURCE_LIMIT/PATH_LIMIT` refusal with no file open. Built-in string roots receive the early cap before scanning.

This does not bypass historical admission, descriptor anchoring, file-size limits or comparison authority. C260 does not state an end-to-end allocation/deadline guarantee for native Python Path rendering, so this is **optional hardening, not a mandatory C268 finding**. If a future caller accepts adversarial Path objects, document that preprocessing boundary or define a separate input contract that bounds it. No API change is requested in this finalization phase. [Independent probe observations](independent-probes/RESULTS.json) retain the exact mechanism and runtime source excerpt.

## Independent semantic and path/dependency scrutiny

Expected memberships and endpoint associations were derived from the actual source declarations, not from an observer or expected-record helper. `first` has `lower/middle/upper`; `second` has `bottom/lower/middle/upper/top`. Each Finger owns a `flex` hinge, parent `pivot`, child `blade.base`, basis axis `(0,0,1)`, exact one-round Pi64 limits of ±45 degrees, and initial zero. The source site interface is `hinged.part`, size zero; the child pose expression remains unevaluated. Both before and after pass these independently stated expectations.

A newly authored paired change uses axis `(1,0,0)`, updates the actual leaf bytes, entry import digest, source digests and canonical program revision, and changes all eight GLB axis claims without changing byte lengths or declaration spans. All three raw interfaces expose/compare the changed inputs while leaving historical authority false. Installing those same bytes into a temporary historical layout fails at each isolated main-source, leaf and GLB hash boundary. The comparator is forbidden during each failed admission. The changed input bytes and recipes are retained with [the seven new probes](independent-probes/RESULTS.json).

The separately rerun [capture probes](capture-probes/RESULTS.json) establish exact complete-result parity with the original C267 API for both endpoints, fresh admission of all five dependencies before compile, refusal of every individually mutated dependency, captured-code operation after all dependency paths are replaced, rejection on the next call, restoration recovery, a final-dependency FIFO refusal, actual C267 fault translation, descriptor/module cleanup and eight overlapping calls. Fourteen cases passed: 21 historical API calls, thirteen admissions, eight typed refusals and no unexpected exception. The existing script's embedded reviewer label names its original author `/root/state_audit`; the executing reviewer for this new run was `/root/review_c268_final`. No newly launched worker is implied.

Inspection confirms the dependency graph contains only the pinned C267 comparator, C266 binding, C265 source observer, C261 artifact observer and C257 lexical/module/occurrence utilities. The wrapper adapts only acquisition hooks and private C265 dependency state. It does not invoke C257's separate file reader, ownership comparison, product parser/evaluator/exporter, native program or model. Python and its standard library remain trusted runtime prerequisites.

## Fresh cohort and evidence audit

The fresh run executed on published candidate `e6f55b73fa71953aa648bcd34711a6796a7346b6` from 2026-11-19 17:42:09 to 17:43:17 UTC. The receipt SHA-256 is `157aad3073c38367d2cd883b8f2d855692e60947e4ba7608c2fdf85e7ebc08a8` (93,146 bytes). Its durable candidate location is `docs/engineering/localized-repair-c268/evidence/finalization-20261119/candidate-published/CHECKS.json` after Director adoption. The audit's original command records the copied folder's earlier name, `candidate`; the Director subsequently renamed it to `candidate-published`. The final review records both names and verifies the renamed payload identities.

| Cohort group | Methods | Result |
| --- | ---: | --- |
| C253 corpus | 14 file bindings / 3 tasks | Passed |
| C255 oracle | 31 | Passed |
| C256 reader | 29 | Passed |
| C257 ownership | 23 | Passed |
| C258 follows | 28 | Passed |
| C261 artifact hinges | 28 | Passed |
| C265 source hinges | 49 | Passed |
| C266 binding | 34 | Passed |
| C267 comparison | 25 | Passed |
| C268 historical endpoint | 35 | Passed |
| Workflow structural check | — | Passed |
| Documentation preservation/navigation | — | Passed |

The reviewer read the receipt and control records and recomputed their accounting. C268 has 131 actual ledger entries: 121 historical calls and ten raw calls; twelve historical admissions, nine raw successes and 110 typed refusals. Real mode-000 permission denial occurred at effective UID 1000; injected permission/read/stat cases are labeled separately. All checks ran on clean tracked and untracked state, with unchanged commit/tree and input inventory. There are no skipped obligations in the selected cohort.

The original failed control run is retained: 34 methods, twelve `KeyError: 'text'` control-author errors, zero test assertion failures. Later tests correctly slice source witness byte offsets; expected meaning was not relaxed. The old 281-method candidate evidence remains historical. The reviewer verified its thirty referenced outputs after recovery rather than treating it as fresh evidence for the corrected candidate.

The review's first evidence-audit attempt incorrectly treated newly added recovered cohort files as alterations of preexisting evidence. That assertion failed while all candidate/cohort identity checks passed. The original audit source, report and log are retained as `evidence_audit.py.before.txt`, `COHORT-AUDIT-attempt01.json` and `cohort-audit-attempt01.log`. The corrected check allows additions, forbids changes/deletions of existing historical evidence, and independently verifies recovered output hashes. The [final audit](COHORT-AUDIT.json) passes all assertions. This was a reviewer-audit mistake, not an implementation or cohort failure.

## Runtime and reproduction

Runtime: CPython 3.12.14, Linux 6.18.57 x86-64 with glibc 2.41, Clang 22.1.3, runtime bundle `26.1117.11355`. Interpreter binary SHA-256: `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7` (30,894,944 bytes). No dependency installation or hosted execution was needed.

Commands executed by this reviewer from the clean local candidate clone:

```sh
python3 -B docs/engineering/localized-repair-c268/evidence/review/review_c268.py --repo REVIEW_CLONE --output NEW_CAPTURE_OUTPUT
python3 -B docs/engineering/localized-repair-c268/evidence/review/endpoint_bound_probe.py --repo REVIEW_CLONE --output NEW_SELECTOR_JSON
python3 -B independent_probes.py --repo REVIEW_CLONE --output NEW_INDEPENDENT_OUTPUT
python3 -B evidence_audit.py --repo REVIEW_CLONE --identity-repo PUBLISHED_OBJECT_CHECKOUT --cohort FRESH_COHORT --copied-cohort COPIED_COHORT --output NEW_AUDIT_JSON
```

The original full argument vectors and hashes are retained in the structured receipts. The independent probe and audit programs are delivered alongside this report. The existing capture and selector programs remain in the identified candidate. Use new output destinations; the probe runners intentionally refuse replacement of prior evidence.

The separately executed cohort command was:

```sh
python3 -B docs/engineering/localized-repair-c268/evidence/run_checks.py --repo IDENTIFIED_CHECKOUT --phase candidate-finalization --output NEW_COHORT_OUTPUT --c268-methods 35
```

## Checked code identities

| Path relative to `docs/engineering/` | Bytes | SHA-256 |
| --- | ---: | --- |
| `localized-repair-c268/endpoint_reader.py` | 14914 | `a7bb1f67398a54922e647d6d43062f89acb32c6e05a2fc653f5c30160f888157` |
| `localized-repair-c268/test_endpoint_reader.py` | 52981 | `d7c426870348ab9e0976d46ee64b8624eb39c3e0b2f84a2159d2a91f66bf46c9` |
| `localized-repair-c268/endpoint_control_fixtures.py` | 9181 | `b062555ea7816cb8425b1d73db949974838d6e00afe549dce91ab2b9ad22439d` |
| `localized-repair-c268/evidence/run_checks.py` | 14667 | `9c6c67a2bb1ce9e7a238b53e185f34d25f794ce7a1bb6e17753d7a9c187b3a3a` |
| `localized-repair-c267/hinge_compare.py` | 12382 | `f98b9eab7a7f0cc75afa26eab0b672356d7e3275e3d713d16df214e68e69d71d` |
| `localized-repair-c266/hinge_binding.py` | 17639 | `68849dbe3339c158eac7ec43fb1defcbd2993c37c6a0a5ee813d2da71fb03dda` |
| `localized-repair-c265/source_hinges.py` | 37570 | `04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e` |
| `localized-repair-c261/hinge_glb.py` | 14036 | `6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08` |
| `localized-repair-c257/ownership.py` | 35942 | `c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1` |

Full contract, corpus, source/GLB, helper/test and artifact hashes are in [REVIEW.json](REVIEW.json), [READ-SET.json](READ-SET.json), the probe records and [ARTIFACTS.json](ARTIFACTS.json).

## Remaining Director gates and limits

The Director may adopt this review and fresh cohort evidence, update current result/task records, reconcile actual main and lease state, perform conditional integration, execute resulting-main checks, verify branch disposition and save the final handoff. These remain separate gates; this review does not certify them in advance. A changed implementation, dependency, fixture or test requires affected re-review. Later evidence/documentation-only commits need their applicable checks and explicit identity continuity.

No site-pose or endpoint world-alignment evaluation, physical validity, joint motion/cycles, full source/glTF/C255 validity, accepted revision, invalid-edit atomicity, rebuild equivalence, native behavior, model-trial result, complete H01–H28 qualification or comparative advantage is claimed. No active review process or uncertain write remains. This worker stops after delivering these artifacts.
