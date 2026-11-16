# C255: offline localized-repair observation checker

This component checks the three existing C253 cases: a 0.65→0.75 m edit,
the reverse edit, and rejection of the 0.75 kg length candidate. It derives
the frozen family's meaning and sampled motion from raw authored keys and
closed-form equations. It checks supplied records for all 18 objects,
34 sites, eight follows, eight hinges, two actions and 126 poses.

The result is **inert record consistency only**. It does not read a native
artifact, rebuild source, promote a revision or run a trial. Even a passing
result has `realTrialSuccess: null`, `executionAllowed: false` and
`artifactReaderQualified: false`. The original public fixture, model and route
qualification gaps and unresolved comparative-advantage question remain.

## Use and verification

Read [CONTRACT.md](CONTRACT.md) for the exact API, observation schema,
caller-byte boundary, original tolerances and limitations. The implementation
is [oracle.py](oracle.py); its meaningful positive, boundary and fault controls
are [test_oracle.py](test_oracle.py). Independent review and publication records
are separate from the authored suite.

From the repository root:

```sh
python3 -IB docs/engineering/localized-repair-c255/test_oracle.py
python3 -IB docs/engineering/localized-repair-c253/verify_manifest.py
python3 -IB docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The checker accepts an observation file and a **separate** authority file whose
file maps carry actual bytes encoded as lowercase hex. For example:

```sh
python3 -IB docs/engineering/localized-repair-c255/oracle.py \
  --repo /absolute/OntoKin --case V1 \
  --observation /absolute/inert-observation.json \
  --authority /absolute/inert-caller-records.json
```

Exit zero means the finite component predicates passed; it never means an
artifact reader, real acceptance decision, clean rebuild or trial was verified.
The API takes actual Python bytes instead of CLI hex envelopes. No caller may
supply alternate tolerances. Unknown fields, duplicate identities, malformed
numbers and widened authority documents are rejected.

## Scope of the checks

Source and dependency files must match the exact frozen two-file closure.
The checker independently derives stable occurrence and definition identities,
ownership, parameters, primitive dimensions, sites, follows, hinges, appearances,
zero matter, actions/events and seven-time rigid poses. The original
`expected.json` corroborates these formulas; it never provides their answers.
A direct native-source decoder is not implemented.

Mesh records must contain actual-coordinate-shaped vertex and triangle arrays,
not a bounding box or an author's success flag. Geometry, raw matrices,
decomposed transforms and provenance are checked independently. Quaternion
sign equivalence and legitimate new accepted-record/artifact identities are
allowed when their recorded byte bindings agree. Rebuild records face the same
full predicates. N1 must preserve the accepted bytes and retain a classified
route rejection before replacement; common-harness protection receives no
language-specific credit.

All caller-provided execution/history/origin facts are still inert. Resolving
native paths, proving reader independence, observing transient accepted state,
sealing rebuild workspaces and authenticating external authority are later
qualification obligations. The separate accounting helper tests declared
failure denominators without starting or scoring real attempts. The component
cannot make the current exposed single family an unseen comparison corpus.
