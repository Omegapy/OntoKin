# C257: independent ownership observations

C257 derives immediate lifecycle ownership from actual `.ok` declarations and
compares it with owner fields read from the existing C210 GLBs. Ownership means
which object contains a part for lifecycle purposes. A transform parent, follow
relation or mechanical connection does not establish that owner.

For both original endpoints, the source observer finds **18 objects, 2 ownerless
scene roots and 16 ownership edges**. Both artifacts contain 18 glTF scene
roots because their transforms were baked into world coordinates. Reading that
transform structure as ownership would lose all 16 actual ownership edges.
The comparison instead checks three explicit owner declarations per object,
their full occurrence identities, reused definition identities and exact source
associations. [FIELD-ORIGINS.md](FIELD-ORIGINS.md) identifies each input field.

This is one semantic component. C256 continues to supply its independently
measured geometry and sampled poses. C257 supplies ownership observations,
with no follow/hinge output or complete C255 semantic record. It does not
authenticate an accepted revision, invalid-edit atomicity, a clean rebuild,
native behavior or a model trial. Frozen formulas, tolerances and predecessor
files are unchanged.

## Run in the hosted checkout

The reader uses only the Python standard library. From the repository root:

```sh
python3 -IB docs/engineering/localized-repair-c257/ownership.py --repo . --endpoint before
python3 -IB docs/engineering/localized-repair-c257/ownership.py --repo . --endpoint after
python3 -IB docs/engineering/localized-repair-c257/test_ownership.py
```

The command prints a JSON ownership comparison only after exact original file
sizes and hashes match. A refused input exits with status 1 and a `REFUSED`
JSON result. `ownershipConsistent: true` means agreement of the supported
ownership fields; `historicalInputsBound: true` adds the original-byte check.
Both values leave `sourceValidityQualified`, `completeC255Semantic` and
`executionAllowed` false, and leave `realTrialSuccess` null.

## Inspect independent raw observations

The [contract](CONTRACT.md) defines four APIs. `observe_source_ownership` reads
literal source keys and declaration containment. `observe_glb_ownership`
reports untrusted metadata claims. `compare_ownership` checks the two, and
`read_bound_endpoint` adds the original-byte restrictions. This separation
lets controls alter real ownership or identity bytes and observe the result
before historical admission refuses the modified artifact.

The source parser supports a finite subset of this family: scene objects,
ordinary parts, generated parts over `self` keyed parameters, literal keys,
direct literal-return helpers and final direct parameter overrides. It resolves
classes in their actual module and checks imported visibility. Unsupported
ownership forms, ambiguous keys, nested shape overrides and cycles refuse.
It does not evaluate numeric values or establish complete source validity.

A controlled relocation of the Blade declaration from Finger to Rack changes
the observed graph to 12 objects and 10 edges. Coordinated owner metadata can
agree with that changed graph through the raw APIs. Such a result qualifies
only the measured ownership fields; the modified source's remaining
relationships and the retained artifact geometry are not qualified.

## Evidence and stopping point

[RESULTS.md](RESULTS.md) records authored and independent outcomes, preserved
failures and the exact reviewed source. [INPUTS.json](INPUTS.json) retains input
hashes and the unchanged language-contract references. The next separately
scoped task is described in [NEXT-TASK.md](NEXT-TASK.md).

Integration, actual-main verification, branch cleanup and the saved successor
handoff remain the main agent's responsibilities. A reader commit alone does
not prove those operations occurred.
