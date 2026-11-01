# C086 separately adopted input corrections

[AMENDMENT-C086-001](AMENDMENT-C086-001.json) corrects exactly eleven canonical type fields across three Point3 cases. The frozen source spelling remains `Point3`; the inherited resolved type is `Point3<Length>`. The [independent adoption review](ADOPTION-001.json) verifies this against the retained unchanged-C085 control results in `evidence/`, before any C086 runtime execution.

The original [input freeze](../keyed-rekey-v0.1/INPUT-FREEZE.json) and [expected values](../../../examples/keyed-rekey/expected.json) remain byte-exact. Readers apply only the enumerated reviewed replacements, require every original field value, and verify the distinct effective expectation hash. The proposed-state label in the unchanged amendment records its draft history; exact publication and the separate adoption review establish authority. The first independent reader self-check failure and its source cut remain retained. This changes no source, key, payload, location, diagnostic, budget, tolerance or runtime meaning.

Implementation, actual candidate validation, integration and complete release acceptance remain separate.
