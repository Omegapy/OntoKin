# C270 refusal classification correction

## Scope and decision

The [frozen C270 finding](../FINDING.json) records an independently authored,
source-valid `SiteRef` parameter that the finite source observer incorrectly
classified as `MALFORMED`. This correction changes that refusal to
`UNSUPPORTED_SOURCE_FORM`. It neither observes the parameter's value nor adds
successful endpoint support. The unchanged [C260 contract](../../localized-repair-c260/CONTRACT.md)
sections 1, 3.3 and 6 require this distinction.

The change is local to C265 `Source.site()`. It recognizes an existing parameter
only when its authored declaration includes explicit visibility and its complete
type consists of one identifier token, `SiteRef`. The check uses token kind as
well as spelling. Strings, qualified names, generic type applications and extra
tokens cannot satisfy it. External access is checked before returning the new
unsupported-form refusal.

`scan_class()` retains one additional fact, `explicitVisibility`, for parameters.
Its existing visibility fallback remains unchanged. The new classification uses
this fact because the adopted construction grammar requires visibility on a
property declaration; an omitted modifier must not become a valid declared form
through that fallback. No other consumer or existing default changes.

The [core rules](../../../language-design/OK-LANG-001-core-language-specification.md)
sections 5.1, 6.1–6.3 and 10.2 establish nominal `SiteRef` identity, lexical member
lookup and access. Private members are accessible in their declaring class;
private external members are inaccessible. The
[construction grammar](../../../language-design/construction-v0.1/ontokin-construction.ebnf)
and [construction rules](../../../language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md)
retain those distinctions for the supplied pinned module.

## Observable behavior

| Terminal member in an existing endpoint path | Result |
| --- | --- |
| Explicitly public or private own parameter with exact nominal type `SiteRef` | `UNSUPPORTED_SOURCE_FORM` |
| Public `SiteRef` parameter on the existing direct part | `UNSUPPORTED_SOURCE_FORM` |
| Private external `SiteRef` parameter | `MALFORMED` |
| Missing terminal member | Existing `MALFORMED` |
| `Length`, `FrameRef` or another non-site member | Existing `MALFORMED` |
| `SiteRef<Real>`, `mech.SiteRef`, a quoted token, multiple type tokens or `Ref<SiteRef>` | Existing `MALFORMED` |
| Parameter with omitted authored visibility | Existing `MALFORMED` |
| Explicitly declared site | Existing finite site observation and access rules |

The source exception carries a nonempty reason and the supplied source hashes
and sizes. C266 and C267 already preserve the exception's code, reason and cause;
their logic does not change. Their supplied artifact hash and size also remain
available. No qualified records are attached to any refusal, including when the
parent site was inspected before an unsupported child endpoint was reached.

The parameter's initializer is not evaluated, resolved or type-checked by this
new branch. Recognizing its declared form does not certify whole-source validity
or the validity of its expression. This retains C260's limited observer boundary.
Existing intermediate traversal classifications remain unchanged.

## Dependency pins and preservation

[PIN-CHANGES.json](PIN-CHANGES.json) records every prior and corrected byte count
and SHA-256. Nine current dependency entries change: C266's C265 pin, C267's C265
and C266 pins, and the three affected pins in each of C268's reader and current
fixture helper. Their admission checks remain intact. No further pin path was
needed. C257, C261, the independent C266 fixture recipe and all historical input
pins keep their exact identities.

The C260 contracts, C270 frozen source/oracle/runner, original tests and all
earlier execution evidence are unchanged. The original failed C270 result
remains the record of the earlier implementation's behavior.

## Supplementary verification

[test_refusal_classification.py](test_refusal_classification.py) supplies eight
plain `unittest` methods, with 16 source variants and 48 public-interface calls.
These are implementer controls, separate from the independent frozen oracle.
Their expectations follow the language's declaration, nominal-type and access
rules. They check exact categories, retained source/artifact identities, equal
propagated reasons, originating source exceptions and absence of partial records.
The public external case reaches its refusal after the original parent site has
already been inspected.

Run from the repository root:

```sh
python3 docs/engineering/localized-repair-c270/correction/test_refusal_classification.py
```

The implementer preflight passed all eight methods on the exact uncommitted
corrected bytes. Its checked-code snapshots, interpreter/platform, command,
output, exit status and unchanged-input check were preserved outside the
repository in `implementation/c270-classification-attempt-01`. Candidate and
actual-main checks, frozen H16 execution, full affected regression evidence,
independent acceptance, integration and saved delivery are Director-owned gates.

No compiler, evaluator, exporter, native application or model trial was run by
this correction worker. This correction does not close broader H16 alternatives,
H20, H22, H24 or full C260/product/site/world qualification.
