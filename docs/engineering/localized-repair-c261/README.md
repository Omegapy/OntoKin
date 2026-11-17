# C261: raw GLB hinge claims

This increment implements **only** `observe_glb_hinges(raw)` from the
[C260 contract](../localized-repair-c260/CONTRACT.md), version 0.1.0. A hinge
declaration identifies two ordered sites, a signed basis axis, angular limits
and an initial coordinate. The reader extracts these fields from supplied GLB
bytes. Its output remains **untrusted artifact metadata**.

The source observer, source/artifact comparator and historical endpoint reader
are not implemented here. No successful call verifies `.ok` declarations,
program identity, endpoint association, physical validity or an accepted
revision. The [remaining control obligations](CONTROL-COVERAGE.md) are explicit.

## API and observed fields

Load [hinge_glb.py](hinge_glb.py) with Python's standard `importlib` or import it
from its directory, then call `observe_glb_hinges(raw_bytes)`. It performs no
file or network access and has no runtime or other observation-component
dependency. The original [C260 input bindings](../localized-repair-c260/INPUTS.json)
remain unchanged; no producer sidecar or baseline answer table supplies results.

The result schema is `ontokin.c261.glb-hinge-observation/0.1`:

| Result | Meaning |
| --- | --- |
| `artifactSha256`, `artifactBytes` | Identity of the actual supplied bytes; no historical admission |
| `records[i].claims` | The actual eight joint fields, with array order and endpoint order retained |
| `records[i].origins` | Actual JSON pointers for those fields and each ordered limit |
| `objects[i].claims` | Node path/ID/class/revision/source mapping and the program occurrence at that exact claimed path |
| `objects[i].origins` | Actual node and escaped program-occurrence pointers |
| `sourceClaims.source` | The actual source metadata object |
| `sourceClaims.program` | Actual revision, entry source ID, manifest and source-unit claim excerpts |
| `sourceOrigins` | Exact source pointer and per-field program pointers matching those excerpts |

The reader checks object/path uniqueness and node-to-program **claimed path-set
coverage**, not source correspondence. It checks that retained source spans
are bounded ordered integer values. It does not determine whether they point
to real source declarations or whether repeated source hashes, definition IDs,
class claims, source maps and revisions agree. Well-formed stale or contradictory
provenance remains inspectable and untrusted. A later comparator must supply
those checks against actual source bytes.

Nested mapping completeness is also unqualified: sparse dictionaries are
retained. Known identity fields, when present, must be bounded arrays
(`declaration_definition_id` may be null), but this is not a complete metadata
schema validator. The later comparator must require every mandatory nested
field, validate its role and type, and reconcile repeated claims with source.

Site paths stay opaque strings; the reader never splits them on dots or
manufactures site IDs. Zero, one or up to 128 distinct joint rows can be
observed; a missing or added row relative to source cannot be detected by this
raw interface. Renamed keys, endpoint swaps and supported different values
remain raw claims, not an agreement result.

`historicalInputsBound`, `sourceAgreementVerified`, `completeC255Semantic` and
`executionAllowed` are always false. No direct site records or joint
definition/span values are manufactured. A `sites` table at either
`/extras/ontokin/sites` or `/extras/ontokin/program/sites` is outside the selected
profile and explicitly refuses. Extra joint-row fields also refuse. The false
observation flags describe this reader's selected fields; unrelated locations
and extensions are not a claim of complete metadata absence or glTF validity.

## Numeric, structural and resource boundary

Only GLB 2 with exact header length, one aligned JSON chunk followed by one
aligned BIN chunk, glTF asset `2.0`, target `ontokin.glb/0.2`, schema `0.2` and
profile `construction-0.1` is admitted. A structural pass does not validate BIN
contents, mesh/accessor consistency or required extension semantics.

Each joint has exactly `path`, `element_id`, `kind`, `parent_site`, `child_site`,
`axis`, `limits` and `initial`. Kind is `hinge`. The axis is exactly one signed
coordinate basis axis; no normalization or tolerance is applied. Limits are
ordered, and initial lies in their inclusive range. Zero-width ranges are
allowed. JSON floats are converted once by Python's binary64 decoder; JSON
integers remain integers. Neither values nor axis signs are subsequently
changed. Positive and negative zero compare equally; decoded negative float
zero is retained. This API does not perform source deg/rad conversion.

Bounds are 4 MiB GLB, 2 MiB JSON, 32 JSON nesting levels, 128 object nodes and
program occurrences, 128 joints, 256 distinct endpoint path claims, two source
unit claims, 32 identity components and 512 Unicode scalar values per consumed
text. Consumed text excludes control and surrogate characters. Source byte
spans require actual integers within 0–65,536; booleans and fractional numbers
refuse. These are representation bounds, not a source-key grammar check.

Before number conversion, every JSON numeric token is limited to 64 characters
and explicit exponent −400 through 400. Nonzero tokens must have adjusted
decimal exponent −324 through 308. Nonfinite results refuse. This global JSON
guard bounds allocation even in unobserved metadata. At the underflow boundary,
`1e-324` decodes to zero and `5e-324` to the smallest positive binary64 value;
the latter cannot replace a zero axis component. Duplicate JSON keys refuse.

## Refusals and verification

The API raises `Fault`, a `ValueError` subclass, with `code`, `detail` and
`pointer`. Codes are `MALFORMED`, `RESOURCE_LIMIT` or `UNSUPPORTED` for this raw
slice. Source disagreement, unsupported source forms, historical mismatch and
I/O categories belong to the unimplemented interfaces. No refusal returns a
partial result. For byte inputs, `artifactBytes` is attached; SHA-256 is attached
only within the 4 MiB size bound so an oversized refusal does not start an
unbounded hash pass. Host UTF-8/JSON/shape/recursion errors become `Fault`.

Run the authored controls with:

```sh
python3 -IB docs/engineering/localized-repair-c261/test_hinge_glb.py
```

The initial authored test used `None` as both a default argument marker and a
deliberate invalid input; its one failing subtest was a test-construction error.
The corrected test uses a distinct marker. Independent review also identified
the need to refuse added direct-site tables rather than return an ambiguous
absence flag; that correction and its controls are retained. Execution receipts,
review findings and integration state are reported separately by the integrator.

This component supplies neither site pose/world alignment nor combined motion
authority, complete C255 semantic qualification, revision/rebuild authority,
native observations, model trials or a comparative benefit. Existing failures
and unrun gates retain their meanings. See the [next bounded task](NEXT-TASK.md).
