# C270: one source-valid declared SiteRef control

## Frozen purpose and independence

This control addresses only [C269's H16.02 gap](../../localized-repair-c269/COVERAGE.json): a genuinely declared `SiteRef` used as a hinge endpoint. The independent fixture investigator `/root/fixture` authored its source bytes and [literal expectation](EXPECTED.json) from adopted language rules, the unchanged [C260 contract](../../localized-repair-c260/CONTRACT.md), and the original source bytes at `254e481351239b536394c182b6761ec4c8662764`. The investigator did not read the C265/C267 implementation or execute any observer, product parser/compiler, evaluator, exporter, native application, or model trial.

The Director confirmed the early recovery save before fixture construction. This is one input, with one predeclared expected classification. An unexpected result must remain evidence; no replacement input or revised classification may turn it into a pass.

## Exact source change

The copied dependency [hinges.ok](hinges.ok) adds this member immediately before `Finger.flex`:

```ontokin
private param parent_site_ref @ "parent-site-ref": SiteRef = self.pivot;
```

That joint's `parent = self.pivot;` becomes `parent = self.parent_site_ref;`. The copied [main.ok](main.ok) changes only its exact import digest. Every other original source byte is preserved. The new parameter is not overridden anywhere in the supplied closure. There is no invented built-in `site(...)`, undeclared identifier, added function call, keyed endpoint traversal, or change to a site declaration.

## Rule-based validity argument

The adopted [construction grammar](../../../language-design/construction-v0.1/ontokin-construction.ebnf) admits a `property_decl` as a class `member`, with visibility, `param`, name, stable identity, type, and expression. `SiteRef` is a valid type name; `self.pivot` and `self.parent_site_ref` use the permitted member-access expression production. Both assignments terminate with semicolons. This establishes the changed syntax; the following rules establish its meaning.

| Adopted rule | Application to this exact change |
| --- | --- |
| [OK-LANG-001 §5.1 / LANG-003](../../../language-design/OK-LANG-001-core-language-specification.md) | `SiteRef` denotes an identified attachment site. Copying a reference retains its identity. The parameter holds the existing site reference; it does not create a site or object. |
| OK-LANG-001 §6.1 / LANG-007 | `self.member` resolves in the enclosing class occurrence. `Finger` already declares `pivot`; the new member name and key are unique and do not shadow a predefined symbol. Each `Finger` occurrence resolves its own `pivot`. |
| OK-LANG-001 §6.2 / LANG-008 and §10.2 / LANG-022 | Private members are accessible within their declaring class, and object references expose accessible user members. `Finger.flex` reads `Finger.parent_site_ref` from that same class. No outside access to a private member is introduced. |
| OK-LANG-001 §6.3 / LANG-009 | A parameter default is resolved once per elaborated instance. The new dependency is `flex.parent` → `parent_site_ref` → the already declared `pivot`. The site's existing description does not depend on the new parameter or on `flex`, so this introduces no dependency cycle or state query. |
| OK-LANG-001 §§7.2–7.3 / LANG-012–013 | A joint parent has type `SiteRef`. The typed parameter preserves precisely the original parent site. The unchanged child is `self.blade.base`, on the separate blade occurrence. Both existing sites retain interface `"hinged.part"` and size `0[m]`; axis, limits, initial coordinate, and all site poses remain unchanged. |
| [OK-LANG-002 §§1 and 3.1](../../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) | Construction retains the baseline reference/member rules and the declaring module's lexical context. The new member is in the pinned leaf's existing `Finger` class; no caller or scene scope is captured. |
| OK-LANG-002 §3.2 | The entry pin equals SHA-256 of the new dependency's exact bytes. Its package/version, two-file closure, filenames, and declaration visibility are unchanged. The independent program identity in `EXPECTED.json` follows the adopted canonical-manifest formula. |

Together these rules make the changed expression a declared, typed site-reference alias to the original endpoint. This is a source-level derivation, not a claim that a product validator accepted or evaluated the modified program. No runtime result supplies this argument or any expected field.

## Why the finite observer must refuse

[C260 §3.3](../../localized-repair-c260/CONTRACT.md) admits `self.SITE` only when its terminal name denotes an explicitly declared **site**. Here `parent_site_ref` denotes a parameter whose value is a site reference. The same section explicitly excludes parameter and computed `SiteRef` forms. C260 §1 distinguishes unsupported valid forms from invalid OntoKin, and §6 requires typed refusal with retained identities and reason and no qualified partial set. The [H16 control-plan row](../../localized-repair-c260/CONTROL-PLAN.md) and C270 requirements fix the exact expected category as `UNSUPPORTED_SOURCE_FORM`; `MALFORMED` does not satisfy it.

Both the source observation and comparison must refuse with that exact code. The comparison must retain the source refusal's code and reason, both source hashes, and the supplied artifact hash. Neither operation may emit successful or partial qualified hinge/site records. C260 does not prescribe literal English diagnostic wording, so the oracle requires a retained nonempty reason rather than an invented exact message.

The comparator input is the unchanged original `before.glb`. It intentionally retains original provenance and is **not** a source-matched paired artifact. This control tests propagation of the source refusal only. Execution evidence must establish that the comparison failure originates from this source refusal; a stale-provenance refusal or artifact-field mismatch cannot pass the control. No agreement, historical admission, or artifact qualification is expected.

## Exact identities and reproduction

All hashes are SHA-256 of original file bytes; no normalization occurs.

| Input | Bytes | SHA-256 |
| --- | ---: | --- |
| Original `before.main.ok` | 1708 | `73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123` |
| Original `hinges.ok` | 1911 | `1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a` |
| Frozen `main.ok` | 1708 | `f7e22c5bb8c42dadc475b970d16c1ce0503dc2333ed359387d85e5e6638b584d` |
| Frozen `hinges.ok` | 1998 | `dd5b49760121c0fe8ee5e707fe60e1d269be954896951f991887f195b0686e97` |
| Original comparator `before.glb` | 185276 | `d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534` |

The new import digest is `sha256:dd5b49760121c0fe8ee5e707fe60e1d269be954896951f991887f195b0686e97`. `EXPECTED.json` also records the original input paths, exact source descriptors, canonical program manifest/revision, and hashes of every governing reference used.

[build_control.py](build_control.py) uses only Python's standard library to check the original identities, perform the two explicit dependency edits and one pin replacement, and write the frozen source/oracle files. It contains no language parser, evaluator, observer import, or hinge-value oracle. Run `python3 docs/engineering/localized-repair-c270/control/build_control.py --check` from the repository root to compare the independently reconstructed bytes with these files without modifying them. The Director owns observation, exact-candidate review, publication, and closure decisions.

H20, H22, and H24 remain open. This one refusal control cannot establish site/world behavior, physical correctness, motion, accepted revisions, broader contract coverage, or whole-product qualification.
