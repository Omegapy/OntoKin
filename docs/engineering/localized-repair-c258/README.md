# C258 finite explicit-follow observer

C258 independently reads explicit follow relations from the existing public
`.ok` source and compares their constant offsets with the existing GLB metadata.
A follow states which frame a child follows and the rigid offset between them.
This relation differs from lifecycle ownership and the glTF transform hierarchy.

The observer uses the standard library and the exact pinned lexical/identity
utilities from [C257](../localized-repair-c257/README.md). It does not import the
product parser, evaluator, C255 expected semantics or producer sidecars.
The [contract](CONTRACT.md), [field origins](FIELD-ORIGINS.md),
[input hashes](INPUTS.json) and [results](RESULTS.md) define its finite authority.
The reviewed scientific revision is `2bca9f7d2cba8996043bbfeae0c2855def5d7076`:
28 authored methods and 119 independent controls pass on those exact inputs.
The separate structural review also approves the finite scope.
These checks establish this observation component; integration and saved
delivery require the main integrator's separate receipts.

## Run the preserved endpoints

From the restored repository root:

```bash
python3 -IB docs/engineering/localized-repair-c258/follows.py --repo . --endpoint before
python3 -IB docs/engineering/localized-repair-c258/follows.py --repo . --endpoint after
python3 -IB -m unittest discover -s docs/engineering/localized-repair-c258 -p test_follows.py -v
```

Both original endpoints contain eight follows. The CLI checks the original
source and artifact bytes before comparing the observations. Successful JSON
contains `followConsistent: true` and `historicalInputsBound: true`. A refusal
returns JSON with `status: REFUSED`, a code and detail, and exit status 1.
No native application, model trial, rebuild or revision promotion occurs.

## Four separate observation authorities

| API in `follows.py` | Meaning |
| --- | --- |
| `observe_source_follows(source_files)` | Derives supported follows from `main.ok` and `hinges.ok` bytes, with full identities and exact UTF-8 source spans. |
| `observe_glb_follows(raw)` | Reads untrusted actual follow rows and relevant property copies from GLB bytes. |
| `compare_follows(source_files, raw)` | Checks source/program/child associations and agreement of supported source and metadata claims, including supported changed inputs. |
| `read_bound_endpoint(repo, endpoint)` | Adds exact historical size/hash admission for `before` or `after`. |

Source and comparison records contain a relation ID and path, source-derived
definition ID, child occurrence and definition IDs, resolved parent frame,
translation in metres and WXYZ rotation. Raw artifact records contain the
reported relation and child identities, parent frame and offset fields. They
omit a relation `definitionId` and remain untrusted until source association
is checked. Parent frames identify the full object occurrence or explicit
`world`. The observer resolves initializer `self` in its lexical owner and
class defaults in the child. Ownership is used to recover lexical scope; its
edges do not determine follow values.

Source offsets record literal/key/default/initializer/helper origins. Actual
artifact values retain JSON pointers and the artifact digest. The GLB has no
direct follow-definition or follow-source-span authority. Those fields remain
explicitly absent; definition associations are derived through the verified
child class and relation key. There is also no separate encoded offset frame.

## Numeric and semantic limits

Supported length literals use exact m/cm/mm factors before one binary64
rounding. Source quaternion inputs must satisfy the adopted near-unit norm
condition. Accepted normalized components have exact midpoint rounding proofs;
Decimal arithmetic supplies candidates only. Artifact components remain
unmodified. Their comparison uses the explicit C258 eight-ULP policy with
strict zero components and one common sign. This policy is not an exporter
error bound and does not change C255 tolerances.

Unsupported expressions, ambiguous identities, unsupported follow-affecting
nested overrides, contradictory metadata and exceeded resource limits refuse.
The component qualifies the directly used child FrameRef/Vec3 property copies.
It does not qualify every property dump, physical declaration, source-language
construct or glTF field.

`completeC255Semantic`, `sourceValidityQualified`, `jointUnionQualified` and
`executionAllowed` remain false. `realTrialSuccess` remains null. Hinge
observations, joint-wide motion authority, world-motion agreement, authentic
accepted revisions, invalid-edit atomicity, clean rebuilds and comparative
advantage remain unmet. Complete the reviewed integration and saved handoff,
then stop at the [next-task boundary](NEXT-TASK.md).
