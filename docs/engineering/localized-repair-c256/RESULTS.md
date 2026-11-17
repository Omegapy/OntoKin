# C256 executed reader results

The reviewed code is author commit
`97e8942071502044cb3baedac71622c151e52283`, based on published C255 main
`9b9d72e0b411f5f84dd815638edcf364488d26c4`. Reader SHA-256:
`5993d1a9ca1cbccd4518ed6f113238d18f6b71ba02befd59900b93fe47ef6e6a`.
Later documentation/evidence commits do not change those implementation bytes.
Publication and resulting-main checks are recorded by the integrator.

## Observed qualification

- **29 author methods pass**, including both exact historical endpoints
  through the unchanged C255 geometry and delivery-pose predicates.
- **95 independent controls pass** on the corrected reader. They compare
  eighteen mesh observations, full occurrence/definition associations and 126
  poses for each endpoint against a separate standard-library traversal and
  frozen mathematics. Every accessor and animation origin is resolved.
- Changed geometry, translation, rotation and valid animation times change
  measured output. Invalid structures, nonunit rotations, ambiguous identities,
  wrong source joins and changed historical proof bytes refuse. Relocated
  accessor data and interleaved stride exercise actual offset handling.
- The independent reviewer also reran all **29 authored methods**, the
  unchanged **31 C255 methods** and C253's **14-file, three-case manifest
  check**. All passed on hosted Linux CPython 3.12.14.
- A separate static reviewer approved bounded inputs, exception handling and
  decoding limits. That review did not execute the reader and adds no second
  numerical observation.

The independent baseline's largest observed discrepancies against the frozen
mathematics are about **4.77e-8 m in position, 3.65e-8 rad in orientation and
2.39e-8 m in geometry**. These describe two original binary32 artifacts, not
new tolerances. All C255 tolerances remain unchanged.

## Preserved failures and corrections

The first independent attempt passed 89 of 93 controls. Four malformed JSON
object shapes escaped as `AttributeError`: asset, global metadata, node
metadata and source manifest supplied as lists. The corrected public boundary
turns them into explicit `Fault` refusals. Original results and four exact
corrupted inputs remain in the independent evidence.

Static review identified a JSON integer-limit `ValueError`, unbounded pre-hash
file reads and allocation amplification through aliased accessors. The final
source converts malformed JSON failures to explicit refusal, checks exact
source/input sizes before bounded reading and hashing, and imposes per-role
element limits plus a cumulative scalar budget. Targeted author controls
execute the corrected cases. Original findings remain recorded.

## Evidence and interpretation

[Author evidence](evidence/author-results.json) identifies source hashes,
interpreter/platform, commands and logs. The [independent review](evidence/independent-review/REVIEW.md)
and [static correction](evidence/structural-review/correction-review.json)
retain separate scopes. The [evidence location map](evidence/EVIDENCE-LOCATIONS.json)
preserves original names and hashes; historical Markdown snapshots use a
`.txt` suffix to preserve their bytes without treating old relative links as
current navigation. [Specification provenance](evidence/specification-provenance.json)
binds the consulted Khronos revision and content.

No product runtime, frozen C253/C255 file, native route, model, asset corpus,
semantic graph, accepted revision, rebuild or trial state changes. These
checks qualify only finite geometry/pose reading and source identity
association. Full semantic observation, external revision authority, R07/R08,
normal fidelity and comparative advantage retain their prior limits.
