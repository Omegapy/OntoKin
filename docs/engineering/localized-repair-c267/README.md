# C267 finite source and artifact hinge comparison

`compare_hinges(source_files, raw)` compares the declared hinges in supplied
OntoKin source with the hinge metadata in supplied GLB bytes. It implements the
third interface of the unchanged [C260 contract](../localized-repair-c260/CONTRACT.md).
The component is an isolated engineering observer, not part of product runtime.

## What agreement means

The exact pinned [C266 binding](../localized-repair-c266/README.md) first verifies
the retained source/program/object associations. [C265](../localized-repair-c265/README.md)
derives source hinge declarations independently, and [C261](../localized-repair-c261/README.md)
reads actual artifact claims. [INPUTS.json](INPUTS.json) records their byte identities.
No product parser, evaluator, exporter, semantic sidecar or motion sample supplies
an expected hinge value.

The comparator requires an exact one-to-one hinge occurrence ID and display-path
set. It checks each owning object and class, then kind, signed basis axis, both
ordered closed limits and initial coordinate. Numeric equality is exact under
C260's canonical literal policy; it adds no tolerance, normalization or clamping.
Parent and child endpoint order is preserved. Whole source-derived site paths
and stable identities are associated with already bound objects; dotted keys
are never split into guessed path components. Reordering nodes or joint rows
does not change identity.

Supported changed sources and artifacts can agree after exact provenance
rebinding. The original eight hinges are one input, not a fixed required count.
An empty complete hinge set is permissible when independently observed from
supported source and artifact inputs; it establishes no hinge existence claim.

## API result and refusal

The output schema is `ontokin.c267.hinge-comparison/0.1`. Each record keeps source
byte witnesses, actual artifact claims and JSON pointers, owning-object binding
and separate ordered endpoint associations. Source/artifact byte counts and
SHA-256 identities remain attached. `inputBindingVerified`,
`hingeComparisonVerified`, `hingeSetAgreementVerified` and
`endpointAgreementVerified` are true only for a whole successful comparison.

`Fault` refuses the whole input. `FIELD_MISMATCH` distinguishes supported
field/set disagreement from inherited malformed, input-binding, resource,
unsupported-source/artifact and I/O outcomes. Faults retain bounded available
input identities and the source witness or artifact pointer where available.
Oversized inputs are not fully hashed merely to construct a diagnostic.

## Limits of the observation

The artifact has no direct site table, site/joint definition IDs or their source
spans. Those remain explicitly source-derived associations. A site key change
with the same lexical path can agree after correct provenance rebinding because
the GLB supplies a site path, not a site ID. Site pose expressions remain
uninterpreted source witnesses. Agreement does not establish world alignment,
physical validity, complete source/glTF/C255 validity, accepted revisions,
edit atomicity, rebuild equivalence, native behavior, model-trial success or an
authoring advantage.

C266's unobserved top-level module/scene and program collections remain
unobserved. Other retained object/source/program fields required by C260 still
must bind. Historical input admission is false; `read_bound_endpoint` is a
separate future interface. The original C262 archive remains unchanged.

## Verification and task state

[Requirements](../../workflow/tasks/C267/REQUIREMENTS.md) and
[plan](../../workflow/tasks/C267/PLAN.md) define the acceptance gates.
Run the independently authored controls with a fresh evidence directory:

```sh
python3 -B docs/engineering/localized-repair-c267/test_hinge_compare.py --evidence-dir /tmp/c267-new-run
```

Implementation, independent verification/review, actual-main integration and
saved delivery are separate gates tracked by the [task](../../workflow/tasks/C267/task.json).
