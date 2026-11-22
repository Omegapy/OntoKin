# P13 finite boundary controls

Control version: `ontokin.c271.p13-review-boundary-controls/1`.
Mapping version: `ontokin.c271.p13-control-mapping/1`.
Status: proposed with `P13-RB-001`; neither is an operational schema.

## Original inputs and total mapping

Use the unchanged P11 candidate004 [fixture manifest](../../../loader-path-p11/design/candidate004/FIXTURE-MANIFEST.json), [expectations](../../../loader-path-p11/design/candidate004/EXPECTATIONS.json) and [candidate manifest](../../../loader-path-p11/design/candidate004/CANDIDATE-MANIFEST.json). Their exact sizes and hashes are in `INPUTS.json`. Do not regenerate the ELF images, rewrite JSON contexts, change historical modes or edit an expected result.

`CONTROL-MAPPING.json` lists all 97 original case IDs once. Each row preserves its original route, input path and expectation key. A `future_runtime_primitive` row references the corresponding original expectation without alteration. Its original synthetic/legacy/binding/recheck/fault scope still applies. This is a future obligation, not a run result or a claim that an adapter already exists.

N57 alone has class `independent_review_only`. Its original oracle reference remains present with status `historical_runtime_oracle_not_executable_under_p13`; its P13 runtime expectation is null. That null is **mapping metadata**, never a runtime policy value or admission signal. N57 is not passed, deleted, silently skipped or converted into a positive. Its source-completeness obligation is enforced by independent review under DECISION §3, outside runtime.

The mapping preserves all original outcomes while explicitly changing N57's applicability in a separate version. A later result must report runtime results for the 96 mapped runtime cases and the external-review obligation separately. It cannot report “97 runtime tests passed.” The original P11 record remains available to show precisely what changed and why.

## Eight static boundary controls

`BOUNDARY-CONTROLS.json` fixes literal expected observations for B01–B08. The author static validator reads repository files as data and does not import product code, run original fixture scripts, implement loader policy or execute a test adapter.

| Control | Exact check | Expected interpretation |
| --- | --- | --- |
| B01 | Recursively compare the original P01 and N57 JSON values. | Exactly one delta at `/variant_review/completeness`, with the two retained values. |
| B02 | Deep-copy each original context in memory and delete only that one member. Serialize each with sorted keys, compact separators, ASCII escaping and no trailing newline. | The two byte strings are identical: 3,338 bytes, SHA-256 `e33cb05c8e73031f7c720ecee68094ced82f5d3679af4bc1ebf95bca5b0eaa3c`. This is a logical comparison, not an operational plan projection or replacement fixture. |
| B03 | Compare the complete original `plan_selection`, `subject`, `kernel`, `image`, `variants`, `guards`, `absence_guards`, `search_directories`, closure and name-union fields, plus variant loader/source-review identities and suffixes. | Equal observations; no independent binding difference can explain the old N57 refusal. |
| B04 | Inspect the P11 closed variant keys and the existing source rationale-use statements. | Exactly four variant keys; rationale content is checked for nonempty bytes and hash/binding, not interpreted for completeness. No synthetic label is an adopted operational selector. |
| B05 | Inspect P01/N57's explicitly nonoperational contexts and P12's recorded absent actual plan/digest/source-review evidence. | Actual source completeness is `not_established_by_supplied_inputs` for **both** cases, independent of their labels. This is a review-evidence finding, not runtime refusal. |
| B06 | Compare all 97 fixture/expectation IDs and mapping rows; read/hash original payloads and supports. | All 97 retained; 96 future-runtime rows, N57 review-only; every original expectation and all 131 fixtures unchanged. External `REVISION-004.diff` is identified without a local-presence claim. |
| B07 | Read/hash every file in the unchanged P11 protected-source inventory and inspect the preserved reader/source-limit statements. | Protected source identities match; existing 16 MiB reader and 100,000-operation/30,000-ms source ceilings unchanged. No product execution follows from this check. |
| B08 | Inspect mapping and candidate status against DECISION §§2–4. | No adoption, actual review approval, host qualification, runtime result or 97-runtime-pass claim is produced. Independent review and Director adoption remain separate gates. |

B04, B05 and B08 include semantic obligations for the independent reviewer. The author validator can check their cited bytes, structure and literal metadata, but it cannot replace that review. A successful author report proves only the stated static checks.

## Future adapter obligations

After independent design acceptance, explicit Director adoption and selection of a later implementation phase, a future adapter must bind its implementation bytes and show how each of the 96 runtime cases reaches the named production boundary. The original expectation for each remains mandatory. The adapter must preserve all earlier P11 restrictions, including synthetic-byte/real-pin separation and exact callback identities.

No runtime mapping exists for N57's completeness label. The adapter must not dispatch on the case ID or label to synthesize its historical exception, inject a special failed policy, alter otherwise equal descriptors or add an approval field. The source-completeness gate has no test seam in the operational inputs. Removing the label for B02 is a static equality demonstration only; it does not relabel N57 as a passing P01 execution.

For the original synthetic runtime cases, author metadata about review completeness may describe the finite model but must not reach production as approval or refusal. The declared synthetic model supports only the private-rule scope. A new runtime-enforced review boundary would require another explicit decision and new independently authored controls.

The future review must retain all failed attempts and report exact implementation, input and oracle identities. Static document checks cannot substitute for the 175 inherited methods, independent implementation review, actual-loader completeness review, H0/H1 or later parent gates.

## Reproduction and limits

From the repository root, run the standard-library-only author validator with an unused report pathname:

```bash
python3 -I -B docs/engineering/localized-repair-c271/review-boundary-p13/design/candidate001/validate_static.py --repo . --report /tmp/p13-static-unique.json
```

The report records actual interpreter/platform, command arguments, candidate/input hashes, check outcomes and exclusions. It opens the report exclusively and does not overwrite earlier evidence. It does not modify source, fixture modes, task state, Git or the candidate. Documentation/workflow checks, protected-tree comparison, independent review, adoption, publication and saved handoff are Director-owned separate gates.
