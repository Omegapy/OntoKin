# C087 scoped implementation and independent boundary review

**Outcome:** The independently reviewed core implementation and all **104 frozen runtime-boundary roles** pass this review. A concrete weakness in the partial Agent inspection reader was found, reproduced with three preserved schema-valid corruptions, and closed. This is a scoped engineering result. Full inherited validation, final documentation, integration, resulting-main verification, recovery and retained release gates have their own records.

## Exact source and input identities

| Role | Identity |
| --- | --- |
| Unchanged C086 predecessor | `5d83b07354296a891c1a6acd70efc77322d2127f` |
| C086 tree | `da00e3fe2c36cdd89dbd6e1469eceb1c4400f567` |
| C087 adoption | `2bdb81ece376144387da5581f8df91f59324dc2e` |
| Complete input freeze | `cd8c7fa2f84922ff4855de20f67b4be8d8866d5d` |
| Frozen tree | `d154891725e56d71bc00dc354ad3e37d03a7e7cc` |
| Implementation evaluated | `af585dd9a6d952a61a0ea8b45d3597ef6cc4b796` |
| Implementation tree | `82c9d138fb5aedc2f4ca12483caa96bb9ade3455` |

The specification SHA-256 is `2c72d8c104d8c6db924b3b42291c05431011df3e575e11d6a85f4b6f78cd4432`. The frozen input manifest is `b3a11de3aaaf4a6237e0526123b28da15e10ef5fa3a05353bd13885abb7187d4`, covering 546 files and 11,313,625 bytes. Original and effective expected-answer hashes remain identical: `83fb1b41189c7570f54a479c6a86c9d97c7f6ececee8023bfc78776581febbf4`. These corrections changed neither the frozen answer nor the production runtime.

## Implementation assessment

The static core review read the full new helper and compiler/budget differences from the frozen cut. It confirmed that only source `.20`-declared `String + String` selects the new path. Other operators and operand pairs retain inherited dispatch and diagnostics. Evaluation remains left then right, once each. Abstract checks return unknown String without scanning, reservation, result allocation or dynamic String stages.

The same admitted `SharedExecutionBudget` owns all four stages, its original cancellation callback, the elapsed-time clock and current operation authority. The helper uses scalar widths rather than constructing an operand encoding. It charges each operand's started 64-byte blocks, checks per-result overflow at the first excessive scalar, charges allocation authority before the cumulative check, reserves before native concatenation, and checks publication authority before returning the payload. Reservations are monotone; the helper restores the previous stage on success or failure.

The cache review followed both constant and parameter classification through enclosing expressions. Source `.20` plus nodes cannot disappear through those value caches. Existing guarded immutable member bindings remain reusable after their first actual computation; their later reads replay dependencies and generated-value restrictions. User helpers are outside the relevant builtin cache allowlists. No new public concatenation lineage or repair authority is introduced.

The core implementation was written by another agent, so this static assessment is independent of its author. This reviewer wrote the separate `.20` interface wiring. Its six focused interface tests passed under Python 3.12.14; those tests are self-verification, not an independent review of the bindings. The two initial attempts with missing `jsonschema` are retained. `CORE-INDEPENDENT-REVIEW.json` and `FOCUSED-VERIFICATION.json` bind the exact reviewed files and attempts.

## Independent audit of all 104 boundary records

The independent reader consumes the original frozen specification, source operands and actual retained helper values. It does not import the product implementation or use producer success flags as expected answers. It recomputes Unicode scalar widths, exact stage charges, first failing prefixes, cumulative reservations, result bytes and hashes, exception identity, diagnostic locations and guard effects. Raw and compressed operand receipts, the evidence inventory and all 163 recorded runtime files are checked against the locked implementation.

| Boundary family | Roles | Verified result |
| --- | ---: | --- |
| Actual operation caps | 87 | 20 successes and 67 exact refusals at the independently calculated first failing debit |
| Cancellation | 4 | Original callback object preserved at admission, scan, allocation and publication |
| Real elapsed-time deadlines | 4 | Original clock and debit order retained at all four stages |
| Current source, host and caller authority | 4 | Exact two admission refusals, full aggregate success and reduced-cap execution refusal |
| Missing admitted execution context | 1 | Exact inherited refusal and complete source span |
| Staged generated-value guards | 4 | Both new sources and both older literal controls retain guarded dependency refusal and memoized-value behavior |
| **Total** | **104** | **104 passed, zero findings** |

The high-authority aggregate request actually computes 64 maximum-size results. It reserves exactly 4,194,304 bytes and incurs 131,264 additional String operations. With a 100,000-operation caller cap, 48 results complete and the 49th attempt fails during scanning: 3,145,728 bytes remain reserved, the String work reached is 98,675 operations, and the actual shared ledger reports 100,001 consumed operations against the 100,000 limit. No counter was preloaded or reset to obtain these observations.

Cancellation before allocation leaves the new result unreserved. Publication cancellation retains the already reserved four bytes in its fixture. Cancellation occurs before the failing tick's debit; elapsed-time refusal retains the inherited debit-before-exhaustion behavior. Both distinctions were checked from the actual trace rather than inferred from a final status.

The successful report is `boundary-reader02.json`, SHA-256 `19da0073309051ed3910f73933d6cbb841a97b0df4be713079df64015d0d78ed`. The independent reader is `verify_string_concat_boundaries.py`, SHA-256 `8e67ce0202eb2c47708fbb927a196ffe9b3b83413f543c11ec365e0d7ed95d70`. The supplied producer boundary summary is SHA-256 `418ad86fba91c5ad1a273f28cedc485a92193c0d3db2a744b239fc6060438e13`.

Reader attempt 01 passed 99 roles and had five preparation failures: four staged manifest paths used the wrong parent directory, and the missing-context span used the final brace rather than the inherited EOF token including the trailing newline. The original reader and report remain available. Attempt 02 corrects those two reference conventions without changing product behavior or expected results.

## Partial-inspection gap and verified closure

The initial Agent reader assumed every object-value inspection returned the whole scene. Its first correction allowed a one-object response, but failed to require all of that object's typed values and lineage. This reviewer created three exact corrupted responses: changed `Keyed` and leaf types, removed required rekey lineage, and omitted `selected_total`. Each remained schema-valid. All bytes and exact expected semantic refusals were saved before running the corrected reader.

Reader commit `506be4a` accepted all three corruptions. The fix at `0f7b36924ac1654d775495994ec5aaa098624b27` independently checks a complete inspection for the same project and source revision against the frozen values, types, dependencies and origins, then compares the selected object's entire values dictionary. It retains the selector, cardinality and per-owner dependency checks. This reviewer reran the unmodified workflow auditor: the original 11 workflows passed, and all three corruptions were refused with the exact expected reason.

`PARTIAL-MUTATION-RESULTS.json`, SHA-256 `4d1485fe00249ac0be385002441624a1fdc385c377c2182e76228117a01fe1cf`, records the old and corrected observations. Commit `d2cb531` extracts the same comparison into a reusable helper and adds permanent regressions. Its retained result accepts the unchanged positive and rejects all three schema-valid corruptions. The scoped gap is closed; a schema-only pass was never accepted as sufficient.

## Other retained preparation corrections

The source reader's six refused-key count failures used an expected-output field that is empty for refused sources. It now derives canonical traversal from the frozen original input spans and keyed entries. Another six false comparisons treated `no_dynamic_concat_stage_reached` as a public diagnostic field; it remains an operational assertion, while the public diagnostic uses the exact inherited schema. Source reader attempt 02 reports all 118 source cases, 85 literal controls and 28 older negative controls passing. This reviewer checked the corrections and report; that complete execution belongs to the separate reader owner.

Agent workflow A11's three frozen patches each begin at the original source. The corrected reader requires exactly five revisions in the order reordered, base, inserted, base, removed, including the two necessary restorations. It still replays every successful edit and compares the three exact frozen patches. No transaction or source comparison was waived.

Two producer authority probes originally supplied caller caps to their ledger but omitted the identical runtime `budgets` argument. The inherited runtime correctly refused that mismatch before source admission. The corrected probe supplies the same unchanged frozen caps on both required surfaces. A separate serializer correction preserves the original exception traceback outside an `except` block. Fresh attempt 03 retains every actual helper operand and result as bounded compressed evidence; attempts 01 and 02 remain unchanged.

`CORRECTIONS-INDEPENDENT-REVIEW.json` records the exact source snapshots, hashes, findings, corrections and report receipts. It distinguishes the real partial-reader weakness from preparation errors and evidence completion. Later wire-level adversarial checks, hostile GLBs, native review and full inherited execution belong to their separately identified reports. None of these finite checks establishes complete experimental-feature release or full-product acceptance.
