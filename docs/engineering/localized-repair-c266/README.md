# C266 source/program/object input binding

`bind_hinge_inputs(source_files, raw)` checks whether the supplied source bundle
and GLB's retained object provenance refer to the same source declarations.
This is the input-association prerequisite for the later C260 hinge comparator.
It does not compare hinge values, joint sets or ordered site endpoints.

The isolated [implementation](hinge_binding.py) uses the exact pinned C265
source observer, C261 raw artifact reader and permitted C257 lexical/module/
occurrence utilities. [Input identities](INPUTS.json) bind those dependencies.
No product compiler, evaluator, exporter, producer sidecar or existing
ownership/follow comparator supplies the expected object mappings.

## Verified association

The API receives exactly `main.ok` and `hinges.ok` bytes plus supplied GLB bytes.
The predecessor interfaces first enforce their finite source and artifact
profiles. The new layer derives and checks:

- Exact source hashes and import pin, canonical bundle manifest/program revision,
  entry identities and the complete source-unit map.
- The complete one-to-one object ID/path set, owning class identity and each
  node's repeated program revision. Node order does not establish identity.
- Both complete `source_mapping` and `program_occurrence` records against
  independently derived source facts, including declaration/definition byte
  spans, root/owner paths, typed path steps, declaration definition IDs,
  generated collection/key/input/full input-entry spans and generated ancestry.

A repeated claim must match source even when both artifact copies agree with
each other. A keyed input-entry span covers the full key-value expression,
excluding its separator comma; the quoted key's span alone is insufficient.
Paths are rendered from actual member and key steps. Dots inside a legal
quoted key remain part of that key.

Supported changed source can bind when all required artifact provenance is
updated consistently. The tool neither restricts inputs to original hashes
nor assumes eighteen objects. It does not execute changed source or endorse
any unobserved property of the resulting artifact.

## Result and refusal

The result schema is `ontokin.c266.hinge-input-binding/0.1`. `records` contains
bound **object** mappings, source witnesses and actual artifact JSON pointers.
`inputBindingVerified` is true. `hingeComparisonVerified`,
`hingeSetAgreementVerified`, `endpointAgreementVerified` and
`historicalInputsBound` remain false. There is no qualified hinge set.

The typed `Fault` carries a category, detail, pointer or source origin when
available, and bounded source/artifact byte counts and hashes. Categories are
`MALFORMED`, `INPUT_BINDING`, `UNSUPPORTED_SOURCE_FORM`,
`UNSUPPORTED_ARTIFACT_FORM`, `RESOURCE_LIMIT` and `IO_ERROR`. Missing fields,
wrong primitive types, contradictory claims and out-of-profile complete
mapping fields refuse the whole binding. Boolean and integer values are never
interchangeable. Oversized inputs are not hashed merely for a diagnostic.

The exact dependency files are checked for size/hash on every call. Missing,
changed or symbolic-link dependency paths refuse; no ambient import fallback
is used. Source/resource/numeric limits and C265's unsupported bare-CR comment
form remain unchanged.

## Explicit unobserved fields

C261's public excerpt omits top-level module/scene and program collections.
Those fields, source URI/prose annotations, node display names/transforms,
geometry, motion and metadata outside the retained object mapping are not
verified here. The source-unit module names/keys within the retained excerpt
are verified. A later full comparator must address any additional association
obligations explicitly.

Changed or omitted hinge rows can still pass this prerequisite when the raw
reader's own shape rules permit them. Independent controls demonstrate that
limit. Site definitions, poses, interface/size and joint definition/spans do
not become direct artifact observations. Historical endpoint admission,
complete source/glTF/C255 validity, accepted revisions, edit atomicity,
rebuilds, native/model trials and comparative advantage remain unqualified.
No complete C260 H group is closed by this component.

## Verification and next step

Run the independent controls from the repository root with a fresh output path:

```sh
python3 -B docs/engineering/localized-repair-c266/test_hinge_binding.py --evidence-dir /tmp/c266-new-run
```

[Requirements](../../workflow/tasks/C266/REQUIREMENTS.md) and the
[implementation plan](../../workflow/tasks/C266/PLAN.md) define acceptance.
Results, review, integration and saved delivery are separate evidence records.
After C266's verified saved handoff, a new continuation may select complete
hinge-field/set/ordered-endpoint comparison under unchanged
[C260](../localized-repair-c260/CONTRACT.md). Historical admission remains a
separate interface.
