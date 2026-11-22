# P12 independent blocker adjudication

## Verdict and phase boundary

**P12-N57-POLICY-BINDING-001 blocks implementation under the frozen P11 contract.** N57 requires an unsupported-variant refusal, but its only difference from positive P01 is a synthetic completeness label. The accepted operational variant document excludes that label and leaves source completeness to independent review. A faithful production input or admission result for this difference has not been specified. Stop technical P12 and preserve the control unchanged. No replacement policy or expectation is adopted here.

This is a static design/control binding finding, not a failed runtime test. Production code and both inherited test files remain byte-identical to the accepted P11 terminal source. No focused test file exists. Neither the 97 controls nor the inherited 175 tests were executed. C271 remains blocked and R03–R05 remain unmet.

## Exact source and control

The reviewed source is commit `79292cf456df6e0f49524fcb1fcfd1fd2f7b08ae`. The candidate004 manifest SHA256 is `e7b505aa768d0656db6c4dfaf7541e796aefee7148878a6fdf380d6ab0b911de`. Exact source copies and their hashes are bound by `ADJUDICATION.json` and `BASELINE-INPUTS.json`.

| Evidence | P01 positive | N57 negative |
| --- | --- | --- |
| Fixture SHA256 | `ffae051f6da02526bd8b5b52313d004063f900fa84ebe779f24aeb0df59d72de` | `85a0c7f2b1055f39328c42a3c95e405d474e67b6ba7e442eec4c271d018953a5` |
| `variant_review.completeness` | `synthetic_declared_complete` | `unsupported` |
| Every other parsed field | Identical | Identical |
| `plan_selection.external_digest_matches` | `true` | `true` |
| Variant and rationale descriptor-match observations | Both `true` | Both `true` |

After removing only the synthetic completeness key, each canonical logical context is 3,338 bytes with SHA256 `e33cb05c8e73031f7c720ecee68094ced82f5d3679af4bc1ebf95bca5b0eaa3c`. Both exact normalized files are retained. The same loader/review identities, suffix list, guards, image binding, subject, kernel observations and search directories remain. N57 also retains the synthetic positive assumptions; these do not provide a separately observable production distinction.

The frozen N57 oracle requires `CHI-UNSUPPORTED`, `stage=variant_review`, `rule_id=LP-VARIANT-SEMANTICS`, `state=REJECTED`, zero target starts and no host qualification. `CONTROL-CONTRACT.md` makes code, stage and rule ID normative and requires an adapter to show how each observation reaches actual production logic. Its portable context schema is explicitly nonoperational. [Sources: candidate004 `EXPECTATIONS.json`, `FIXTURE-MANIFEST.json`, `CONTROL-CONTRACT.md` paragraphs 15 and 25; exact records in the adjudication.]

## Missing operational binding

`DECISION.md` defines the separate variant document with exactly `schema`, `loader`, `source_review` and `suffixes`. The source review must explain the actual loader and justify a complete suffix union. Completeness remains an independent-review obligation; the tool checks the bound inventory and facts and does not infer loader semantics from a JSON assertion. The private immutable policy must be derived from source/plan binding. A caller-provided context flag is not admission proof. [Sources: candidate004 `DECISION.md`, paragraphs 49, 53, 55, 85 and 109.]

`n57-adjudication/OPERATIONAL-SCHEMA-PROJECTION.json` compares the logical evidence available for each permitted field. These projections are equal. They are **not operational documents**: the controls supply synthetic identities rather than actual loader and rationale descriptors. Likewise, equality of the digest-match flags is not a claim to have calculated an operational plan digest; neither actual plan bytes nor an external expected digest is supplied by these controls.

The existing `_check_resolution` validates the rationale descriptor, reads bounded bytes, requires nonempty content with the expected SHA256, and checks descriptor binding. It does not parse a completeness decision. Static AST inspection confirms the local `review` value is assigned once and read only for the nonempty/SHA256 condition. The exact source excerpt and observations are retained in `n57-adjudication/RATIONALE-SOURCE-EVIDENCE.json`; the full production source SHA256 is `0c2ef54a227e2e05a7eb1f71a4fedd934399aa27d98ec7a3845f93a4dbfbb612`. No module was imported to inspect it.

An unreviewed adapter could choose `policy=None` when it sees `unsupported`, directly raise the expected error, add a completeness/approval field, alter a descriptor or suffix list, or change the oracle. Each introduces a new decision or changes the frozen input. None proves that the adopted production boundary observes the specified N57 difference. This finding does not prohibit a future policy design; it identifies the absent contract needed to implement and test one faithfully.

## Preservation and limits

The independent materializer authenticated 146 candidate payloads and 29 explicitly bound support files, reconstructed the declared lossless transport envelope, and restored exact source bytes and modes under a fresh private root with mode `0700`. It preserved all 97 controls and the candidate manifest. Receipt: `MATERIALIZATION-RECEIPT.json`, 99,963 bytes, SHA256 `96382f1291ac7027c07a1efef061658281d16e0917b0cccee2281e1ffaf4c4c8`. No payload, checker or production test was executed; no original source path was written. This does not claim recursive restoration of every historical attempt.

Root's separate source-boundary record at documentary commit `74c9cdaeb7f92cc7d3e6957b8a92d798250b9e55` records all 942 protected files unchanged, the candidate manifest unchanged and no new focused test. This reviewer parsed all recorded rows; direct independent byte comparisons of the production module and both inherited test files are also retained. The root record SHA256 is `91d052696b9da296d8f56e4189916c61a88416361fbd5cd268a86bea87145b8d`.

The initial adjudication remains intact at `n57-adjudication/ADJUDICATION.json` with SHA256 `f13d9dadb7e2f93d8c0a8a6a63ab51fc896ca379470ba2596d551e601009171b`. Final machine-readable evidence records the local prior finding ID and the canonical blocker ID. Observation-only truncation/recovery events are recorded explicitly.

The remaining work in this phase is documentary closure and a verified partial handoff. A later independently reviewed clarification may define a source-review-to-policy boundary and faithful N57 mapping, or clarify its external-review status. That decision is not made here. Final publication and final package/save verification require later independent evidence and are not claimed by this report.
