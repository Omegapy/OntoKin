# C261 independent review: raw GLB hinge interface

## Decision

**Accept the selected raw-artifact interface at the exact reviewed source below.** No remaining blocking defect was identified in this bounded interface. Root still owns applicable repository regression, integration, actual-main verification and saved handoff delivery.

This approval applies only to `observe_glb_hinges(raw)`. It is not approval of the complete C260 hinge component or its source/artifact agreement. The source observer, comparator and historical endpoint admission remain unimplemented.

## Exact reviewed identity and execution

| Item | Binding |
| --- | --- |
| Source commit | `2c1ecf0649cc891fe0544eace2aab7ce9779bad5` |
| Source tree | `19171cf47f05aa804f059d096922e43e71532f18` |
| Reader | `docs/engineering/localized-repair-c261/hinge_glb.py` |
| Reader SHA-256 | `6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08` |
| Final independent controls | **217 passed; 0 failed** |
| Final independent assertions | **17,124** |
| Environment | Hosted Linux x86-64, kernel 6.18.57, glibc 2.41, CPython 3.12.14 |
| Scope of execution | CPU/standard-library raw byte observation only |

The reader hash was identical before and after the final run. A subsequent exact-byte comparison verified the tested file against the committed blob above. `SOURCE-BINDING.json` binds the reader, frozen C260 contract, final independent script and final report. No full-checkout immutability or different-platform result is inferred.

Command, executed from this session workspace:

```sh
python3 worker_results/independent-review/independent_controls.py OntoKin worker_results/independent-review/run-03
```

The process exited 0. `run-03.log` and `run-03/RESULTS.json` preserve the actual outcome. The script accepts repository/output-directory arguments so it can be rerun after restoration.

## Independence

The reviewer read the adopted C260 contract and control plan, then decoded actual original before/after GLB JSON using an independent standard-library fixture reader. All expected raw joint, object, source and program-excerpt claims come from those supplied bytes or deliberately mutated copies. No product parser, evaluator, exporter, source observer, C255 oracle, producer sidecar or implementation result supplied an expected hinge value.

The original input hashes were:
- before.glb: `d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534`.
- after.glb: recorded directly in `run-03/RESULTS.json`, alongside its exact size.

Every byte-input control records its SHA-256 and size. Retained procedural edits reproduce variants without duplicating large GLBs. Successful controls compare **every returned joint field**, all returned object claims, source metadata, selected program fields and their JSON pointers with independently decoded input. The review checks pointer escaping for an opaque path containing both slash and tilde.

The implementation imports only `hashlib`, `json`, `math`, `re`, `struct`, `unicodedata` and the language future annotation feature. Static review found no file/network lookup, product compiler call, producer-sidecar lookup, fixed original row table, original hash lock or runtime entry-point modification.

## Findings and dispositions

### 1. Added direct-site metadata was reported ambiguously

The first reader returned `directSiteTableObserved=false` even when supplied bytes contained `/extras/ontokin/sites` or `/extras/ontokin/program/sites`. The reviewer and root independently identified this from code. Two isolated executions of the retained original reader reproduced acceptance with the false flag.

**Correction:** both added tables now refuse with `UNSUPPORTED` at their actual pointers. Extra joint-row fields also refuse, so direct joint definition/span fields cannot enter the eight-field raw row without explicit refusal. README distinguishes the selected consumed fields from a claim about all unrelated extensions.

### 2. Nested identity claims needed explicit type handling

The first generic claim walker bounded identity arrays only when a value was already a list. A wrong-typed nested `element_id=true` could remain accepted. Since these known fields are now part of the selected structural profile, the reader explicitly requires bounded arrays for `element_id`, `definition_id`, `collection_id` and `collection_definition_id`; `declaration_definition_id` additionally permits null.

The original scalar case was reproduced in isolation. Sixteen malformed known-identity variants, one nullable case and one malformed nullable-field case pass the corrected independent controls. Sparse mapping dictionaries remain inspectable; complete nested source-schema validity is explicitly unqualified.

### 3. A refusal pointer used a synthetic report location

The author identified that malformed `program_occurrence` claims were walked using a synthetic `/nodes/.../program_occurrence` path. Returned successful-result origins were correct, but the refusal location did not identify the actual JSON field.

**Correction:** node-native claims and program occurrence claims are walked separately at their actual JSON locations. The final independent control uses the escaped object key `opaque/~object` and verifies the refusal pointer is exactly `/extras/ontokin/program/occurrences/opaque~1~0object/declaration`.

The corrected reader is the final reviewed hash above. Its preceding hash `bad680dd396ba7aa3aeb8762032879f970d1d9528b8220db45d9cda9f5eeed36` passed 216 earlier independent controls, which did not yet exercise this refusal pointer. That success is preserved rather than relabeled as coverage of the later case.

### 4. Reviewer execution mistakes are preserved

The first independent run executed 193 controls and reported 44 failures. Every failure was the same reviewer assumption: the `origins` dictionary was required to contain exactly eight keys. The API also accurately provided `limitLow` and `limitHigh` pointers. The corrected test requires every joint-field pointer and verifies these additional component pointers without prohibiting them. This was a reviewer test defect, not an implementation failure.

The separate original-finding reproduction script initially failed before product execution because `importlib.machinery` was not explicitly imported. Its original source and startup log are retained. Adding the standard-library import allowed all three intended historical reproductions to complete. A following metadata summary initially encountered the expected absent reproduction report after that startup failure; it performed no product execution. The final metadata summary succeeded after the report existed.

## What the controls establish

The final run checks both original artifacts, changed in-range numeric values, inclusive/zero-width ranges, adjacent binary64 boundary refusals, six signed axes, preservation of endpoint order, malformed numeric shapes, exact row fields, text/identity bounds, duplicate IDs and paths, zero/one/127/128 joint counts, 129-row refusal, node and row reordering, JSON pointer escaping, typed malformed-span refusal and selected object-shape failures.

Structural controls cover bytes-only arguments; GLB header, length, alignment and chunk ordering; UTF-8/JSON failures; duplicate JSON keys; excessive JSON depth; the exact 2 MiB JSON boundary and excessive JSON/GLB sizes. Numeric controls exercise the 64-character lexeme boundary, explicit exponent bounds including zero, adjusted exponent bounds, finite overflow refusal, negative zero, `1e-324` rounding to zero and `5e-324` remaining the smallest positive binary64 number.

The tests deliberately accept changed, sparse or stale-but-structurally-admitted provenance as **untrusted claims**, and verify that all qualification flags remain false. This demonstrates an observation boundary, not proof that the claimed source exists or agrees. The README states that JSON integers remain integers, source deg/rad conversion is absent, site paths stay opaque, required nested metadata completeness is not validated, and full glTF/BIN/accessor validity is not established.

## C260 control-plan disposition

**No complete H group is declared passed.** These are selected raw-interface subcases; all full-group obligations remain pending until their other interfaces and dependencies are implemented.

| Group | C261 independent disposition |
| --- | --- |
| H01 | Original raw before/after rows and object/source claims checked; source definitions/sites and historical admission unrun. |
| H02 | Source-only initial change and comparison unrun. |
| H03 | Artifact-only initial retained; comparison and historical refusal unrun. |
| H04 | Paired source/artifact change unrun. |
| H05 | Artifact ordered-limit changes checked; source/paired agreement unrun. |
| H06 | Raw inclusive bounds, zero width, reversed limits and out-of-range initial checked; source canonicalization unrun. |
| H07 | Raw negative zero and numerical boundary behavior checked; source deg/rad conversion and cross-input equality unrun. |
| H08 | All six raw signed basis axes checked; paired source axis reversal unrun. |
| H09 | Source unsupported-axis forms unrun; raw invalid vectors covered under H10. |
| H10 | Raw invalid shape/type/nonfinite/tiny-nonzero cases checked; valid opposite sign remains an untrusted raw value, with comparison unrun. |
| H11 | Source computed/parameterized expressions unrun. |
| H12 | Changed raw path/identity inspection checked; source name/key expansion unrun. |
| H13 | Source-derived site name/key association unrun. |
| H14 | Raw ordered endpoint swap retained; distinct-object/source binding unrun. |
| H15 | Source lexical/private access unrun. |
| H16 | Raw non-hinge kind refuses; source endpoint/joint syntax controls unrun. |
| H17 | Raw missing/extra row fields checked; source collisions/declarations unrun. |
| H18 | Source-only site compatibility unrun. |
| H19 | Opaque punctuated paths and serialized identity/text bounds checked; keyed source expansion/grammar unrun. |
| H20 | Unrelated follow metadata change does not manufacture hinge fields; source geometry/ownership agreement unrun. |
| H21 | Raw duplicate identities/paths, counts and reorderings checked; completeness against source unrun. |
| H22 | Raw span/known-ID shape checks and untrusted stale/sparse claims checked; source/program agreement unrun. |
| H23 | Exact raw pointers, missing-direct-authority behavior and added-site refusal checked; source-derived associations unrun. |
| H24 | Selected artifact structure/resource controls checked; source bytes/tokens/declarations and other source bounds unrun. |
| H25 | Raw JSON lexeme/exponent/canonical float controls checked; source unit-factor conversion unrun. |
| H26 | Historical filesystem/I/O/admission interface unimplemented and unrun. |
| H27 | Changed raw artifacts remain inspectable without historical/accepted authority; source/comparison interfaces unrun. |
| H28 | Raw unrelated motion metadata changes remain unqualified; no world/site/physical validity established. |

## Evidence and remaining work

- `SOURCE-BINDING.json`: exact reviewed source, contract, script and result hashes.
- `independent_controls.py`, `run-03/RESULTS.json`, `run-03.log`: final runnable controls and outcome.
- `run-01/`, `run-01.log`: first failed reviewer assertion attempt and exact original reader/script.
- `run-02/`, `run-02.log`: successful earlier reader run before the refusal-pointer correction.
- `ORIGINAL-FINDINGS.json`, `reproduce_original_findings.py`, `original-findings.log`: three independently reproduced original behaviors.
- `reproduce-original-startup-failure.py.source`, `original-findings-startup-failure.log`: preserved reviewer startup mistake.
- Author evidence separately retains pre-correction reader snapshots and authored tests.

No native application, product evaluator/exporter, source rebuild, model trial or comparison pilot ran in this review. Full C260 source/comparison/historical obligations, world/site pose authority, complete C255 semantics, revision/atomic-edit/rebuild authority and broader release gates remain pending. The appropriate next independent scope is the source-hinge observation boundary described by C261 NEXT-TASK, after this increment is integrated and its saved handoff is complete.

