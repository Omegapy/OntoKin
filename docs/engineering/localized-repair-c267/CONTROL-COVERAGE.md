# C267 independent comparison controls

The [control suite](test_hinge_compare.py) exercises the public
`compare_hinges(source_files, raw)` interface. Its
[fixture builder](comparison_control_fixtures.py) independently writes hinge
fields and expected joint/site identities from explicit recipes and the
unchanged [C260 contract](../localized-repair-c260/CONTRACT.md). The existing
[C266 fixture helper](../localized-repair-c266/binding_control_fixtures.py)
supplies only independently authored source/program/object provenance.
No observer result, product parser/evaluator/exporter, semantic sidecar,
expected-answer record or motion sample supplies an expected hinge value.

The suite checks the complete actual eight-field artifact row, its exact JSON
pointers, source witnesses, full identity/path pairing, source-only site
associations, input hashes and nonqualification flags on every accepted case.
Numeric expectations use an independent rational conversion with the exact
Pi64 constant and one binary64 rounding. Source-only numeric cases rebind all
required source/program/object provenance while retaining the old artifact
field. They therefore isolate field comparison from stale-input rejection.

## C260 mapping and limits

The table identifies relevant assertions; it is not a claim that the whole C260
contract or every H group is complete. The new suite has 25 test methods and
123 public API calls: 35 agreements and 88 typed refusals. Exact code/input
identities, environment, outcomes and preserved inputs are written by each
execution to `results.json`, `checked-code/`, `inputs.zip` and `unittest.txt`.
The task's result and integration records identify the authoritative runs.
Earlier development runs remain evidence for their own bytes only.

| Group | C267 comparison assertions | Remaining boundary or inherited controls |
| --- | --- | --- |
| H01 | Exact original before/after source and GLB bytes: eight hinges, one shared definition and sixteen source-associated sites; every field, pointer and identity checked. | Historical byte-admission API remains absent. This does not complete H01. |
| H02 | Supported source-only initial change, correctly rebound provenance, refuses `FIELD_MISMATCH`. | C265 separately checks the raw source result. |
| H03 | Artifact-only initial change refuses at the actual initial pointer. | C261 exposes the raw changed claim; historical admission remains unrun. |
| H04 | Paired initial change passes with actual changed source and artifact bytes. | Historical flag stays false; historical byte-admission refusal is not implemented. |
| H05 | Each lower/upper limit separately changes in source-only, artifact-only and paired cases. | C265/C261 retain their separate raw interface controls. |
| H06 | Initial at both closed boundaries, zero-width ranges, reversed limits and out-of-range source/artifact values. | No epsilon widens a limit. |
| H07 | Equivalent exact deg/rad values, negative zero, fractional degrees, adjacent binary64 values and smallest positive subnormal disagreement. | C265's independent unit-boundary controls cover further numeric conversion cases. |
| H08 | All six signed basis axes pass when paired; source-only and artifact-only sign reversal refuse. | No sign canonicalization or motion fitting. |
| H09 | Zero/nonunit source axes refuse as malformed; valid nonbasis unit vector refuses as unsupported. | Refusal does not redefine the full language. |
| H10 | Wrong axis length/type, bool/string, NaN/Infinity and tiny nonzero axis replacement refuse. | Exact equality has no axis tolerance or repair. |
| H11 | Computed axis, limits and initial refuse through the comparator. | C265 `test_h11_computed_numeric_fields_refuse` includes its wider unsupported-expression controls. |
| H12 | Joint lexical rename with stable key, key change with stable name, and stale artifact names/IDs. | Definition identity follows actual source keys. |
| H13 | Paired site lexical renames pass; stale parent or child path refuses; site-key changes retain path and expose new source-derived IDs. | GLB has no direct site key/ID field. A correctly rebound source-only site-key change is not falsely called a direct artifact mismatch. |
| H14 | Paired endpoint reversal passes; artifact-only reversal, wrong object's site, same-site paths and suffix-only paths refuse. Source same-object endpoints refuse. | Order is never sorted away. |
| H15 | Private own site and private own part with public child site pass; private external site refuses. | C265 additionally covers imported-class visibility and public defaults. |
| H16 | Implicit origin, keyed traversal, deeper chain and non-hinge source kind refuse. | C265's H16 tests cover scene joints, inheritance, overrides and nested declarations; C261 covers unsupported raw profile/kind. |
| H17 | Missing/extra artifact fields and duplicate row ID/path refuse. | C265 H17 controls cover duplicate/missing/extra source fields, declarations, collisions and constructor shadowing. |
| H18 | Empty interface, negative/computed size and unequal site sizes refuse. | C265 tests required site fields and exact length conversion. Site pose remains an unevaluated byte witness. |
| H19 | Changed membership counts/order, direct/helper/final overrides, dotted/underscore/hyphen keys, renamed roots/classes/modules/parts and shifted Unicode byte offsets pass. | C265 tests empty/duplicate/invalid/overlength keys and the 64/65 boundary. Empty **hinge** sets pass only when both source and artifact have no joints; this does not admit empty keyed inputs. |
| H20 | Original length-edit endpoints both pass; unrelated artifact ownership, follow, geometry, motion/display metadata remain explicitly unobserved. | C265 H20/H28 tests unrelated source geometry/length/pose changes. No full-source or other-component approval follows. |
| H21 | Missing/all-missing/extra joints, wrong owner, duplicate rows, wrong class/span/object table and mismatched ID/path pairing refuse. Node/joint/program-map reordering passes with actual pointers. | The full set comparison also admits a correctly paired empty set. |
| H22 | Entry/program revision, source pin, class and both repeated span claims are rejected when stale or contradictory. | Complete C266 public-API controls cover the full retained mapping and repeated claim leaves. |
| H23 | No direct site table, joint definition/span or artifact site-definition claim is invented. Source-derived sites remain separate from path claims. | Top-level module/scene/program collections remain explicitly unobserved under the scope decision. |
| H24 | Nonbyte/missing source closure, truncated/misaligned GLB, duplicate JSON keys and source/GLB byte caps refuse with bounded identities. | C265/C261 preserve the deeper token/definition/object/hinge/site/depth boundaries and exact finite limits. |
| H25 | Overlong numeric lexemes and out-of-bound exponents refuse; adjacent/subnormal field comparison stays exact. | C265/C261 independently exercise full declared numeric conversion/resource boundaries. |
| H26 | Not implemented or run as a historical admission interface. | Missing/wrong-size/hash/symlink/escape/permission behavior of historical inputs remains a later scope. Dependency-path controls below are not H26 admission evidence. |
| H27 | Changed supplied bytes pass or refuse according to actual fields; historical and unrelated qualification flags remain false. | No accepted-revision or trial claim. |
| H28 | Nontrivial source site-pose expressions and unrelated artifact transforms pass without pose evaluation or physical/world-alignment claims. | No new native/export/model execution. |

## Pinned dependency admission

The public API is loaded in an isolated temporary dependency layout. Exact
dependencies first pass. Each of the four pinned components is then changed
without changing its byte count, after a successful call to the same loaded API.
Every call refuses `INPUT_BINDING`; no stale imported module bypasses renewed
hash admission. Missing and symbolic-link dependency files also refuse.
These controls never alter the repository's actual predecessor files.

## Interpretation

Passing comparator controls and predecessor regressions qualify the finite
declaration-comparison increment only. They do not complete historical
admission, source/glTF validity, site/world behavior, accepted revisions,
invalid-edit atomicity, rebuild equivalence, native observations, model trials
or comparative authoring advantage. A high count does not replace the mapped
assertions, review, integration or required saved delivery.
