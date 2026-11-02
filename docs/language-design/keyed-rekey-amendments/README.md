# C086 separately adopted input corrections

[AMENDMENT-C086-001](AMENDMENT-C086-001.json) corrects exactly eleven canonical type fields across three Point3 cases. The frozen source spelling remains `Point3`; the inherited resolved type is `Point3<Length>`. The [independent adoption review](ADOPTION-001.json) verifies this against the retained unchanged-C085 control results in `evidence/`, before any C086 runtime execution.

The original [input freeze](../keyed-rekey-v0.1/INPUT-FREEZE.json) and [expected values](../../../examples/keyed-rekey/expected.json) remain byte-exact. Readers apply only the enumerated reviewed replacements, require every original field value, and verify the distinct effective expectation hash. The proposed-state label in the unchanged amendment records its draft history; exact publication and the separate adoption review establish authority. The first independent reader self-check failure and its source cut remain retained. This changes no source, key, payload, location, diagnostic, budget, tolerance or runtime meaning.

Implementation, actual candidate validation, integration and complete release acceptance remain separate.

## Amendment 002: original Unicode text in the supported lexical form

[AMENDMENT-C086-002](AMENDMENT-C086-002.json) follows the preserved first C086 producer failure. Its RK108 fixture encoded the intended invalid stable key using an unsupported Unicode escape, so the inherited lexer refused the source before the intended key-validation step. The [independent adoption](ADOPTION-002.json) preserves the original source, source snapshot, failed observations and expected diagnostic, and publishes a separate corrected source root.

The sole token edit replaces the escaped spelling with the exact raw UTF-8 text `café`. Four independently declared lexical checks against exact native C085 source confirm the old spelling is unsupported and the raw spelling is accepted; they do not use candidate output as the expected value. Eight source/bundle revision identities and four end-byte offsets change through exact preconditioned replacements. The diagnostic codes, category, message, key detail and precedence remain unchanged. Every other original input and control remains byte-exact.

The effective expected SHA-256 after both amendments is `00655ca2b6aff89116f433236d0861e45ba649fe6b615a324283407eef66f7b3`. Original-lineage readers explicitly stop at Amendment 001; they do not reinterpret the original producer as a pass. The new corrected producer, its strict independent readers and actual delivery checks have their own source cuts and report identities in the [C086 engineering record](../../engineering/keyed-rekey-2026-11-01-c086/README.md).
