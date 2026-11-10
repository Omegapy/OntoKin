# C193 finite guided-contact contract, version 0.2

This contract is effective only through a separate reviewed adoption receipt
published before qualification. A source validation or successful diagnostic
does not establish delivery acceptance.

## Explicit selection

| Surface | C193 binding |
| --- | --- |
| Source | `ontokin "c193-experimental-0.1"` |
| Profile | `guided-box-contact-0.1` |
| Backend | `blender-bullet-c193-0.1` |
| Recorded output | `glb-guided-contact-0.1` |
| Invocation | `python -m prototypes.guided_contact_v02` |
| Native result envelope | `ontokin.c193.native-result/0.1` |
| Store envelope | `ontokin.c193.store/0.1` |
| Diagnostics | `ontokin.c193.diagnostics/0.1`, prefix `C193_` |

The new source and backend are explicit selectors for the guide-convergence
correction. They do not alter the original `c191-experimental-0.1` source,
`blender-bullet-c190-0.1` backend, prototype v01, standard parser, Agent interface,
or ordinary execution defaults. Old and new source selectors are rejected by
the other prototype. Use a distinct store for the new store envelope.

The physical profile and recorded-output meanings remain unchanged. The native
result/store/diagnostic namespaces identify the new invocation; their field
structure and rejection meanings are inherited, with only the prefix changed.
The literal grammar retains its prior forms. This is not a general language
extension, production backend or live destination simulation.

## Inherited requirements

The original [C191 specification](../guided-contact-v0.1/SPECIFICATION.md),
SHA-256 `3e9fdd37732771cb639c358f0ad6902cebb180e94e0d389acd4270b0b7670301`,
remains the normative basis except for the explicit selector and guide setting
changes in this document. The copied [grammar](GRAMMAR.ebnf),
[source schema](source.schema.json), [native-result schema](native-result.schema.json),
[output schema](output.schema.json), [diagnostics](diagnostics.json), and exact
[backend](backend.json) provide the new selected bytes. The
[C191-A1 bounded-source clarification](amendments/C191-A1.md) is inherited without
changing its original bytes or diagnostic semantics; its C193 equivalents use
the `C193_` prefix.

The source still owns exactly seven visible boxes, two 1 kg carriage mass owners,
four shoe/stop contact boxes and two massless follow relationships. Identity,
ownership, one solver motion authority per lane, units, initial poses, body and
guide frames, compound child geometry, collider groups, source limits and stable
keys keep their original meanings. The only admitted design edits remain the
left stop's X coordinate in 200–495 mm and left-shoe collider enablement.

## Sole physical backend change

| Setting | Original backend | Selected C193 backend |
| --- | ---: | ---: |
| GENERIC guide override iterations, both lanes | 100 | **400** |
| World solver iterations | 100 | 100 |
| MOTOR override iterations | 100 | 100 |
| Frames per second | 240 | 240 |
| Substeps per frame | 10 | 10 |
| Motor maximum impulse | 100000 | 100000 |

Each guide keeps its initial centered-carriage frame, base/carriage ordering,
free X translation, zero transverse/angular limits and collision suppression.
Each motor keeps its original centered-carriage frame, source-derived constant
feed target, impulse cap and speed-property driver. Body frames and compound
children do not change. No solver property, geometry or driver other than the
two guide iteration overrides changes. Backend binding/status fields identify
this new selection and have no solver effect.

The constructor and capture functions are copied without algorithm changes.
They read the selected backend value when assigning each guide's override.
The native worker's envelope/console labels identify C193. The recorder uses the
same algorithm, with a C193 generator label. It captures all 481 sequential native
poses; it neither creates nor replaces a stopping response.

Both `.ok` and direct Python routes must supply the same canonical model to this
same constructor and backend. Their canonical solver bytes, native samples,
raw GLBs and final GLBs must agree for the compared cases. The direct runner
does not parse `.ok` or claim an Agent interface.

## Unchanged output and acceptance

The projection may remove carriage rotation channels and replace transverse
translation values with their initial values. Every native carriage X value and
all 481 frame/240 timestamps retain their float32 encodings. No retiming, key
insertion/removal, hidden trajectory, time-dependent stop, tolerance widening,
mesh change or source-frame adjustment is allowed.

The native-sample vertex, raw-sample vertex and conservative continuous raw-to-
final mapping limits all remain **0.2 mm**. The continuous method is the original
rotation/translation interval bound; it makes no claim about unrecorded native
substeps. Positive cases retain 0.5 mm maximum penetration, 25 ms settling,
0.5 mm/s residual speed, 0.1 mm rebound, initial/fixed/attachment checks and all
twenty unrelated-pair swept-separation checks. A plausible final image cannot
override any failed gate.

Ordinary limits remain 100000 operations and 30000 ms. Qualification examples
request 1000000 operations and 80000 ms, authorized separately by the host.
All 13-object, 9-component, 481-sample, 4800-scheduled-substep, source, byte,
deadline, cancellation and atomic-state requirements remain unchanged. The
operation count charges commanded native substeps; it does not expose or claim
to count Bullet's internal solver iterations. The higher guide override is still
bounded by its exact setting and the same supervised wall-clock deadline.

## Diagnostic basis and qualification boundary

The [frozen four-control plan](../../engineering/guide-repair-c193/native/DIAGNOSTIC-PLAN.md)
used the retained 372.5 mm failure. Original construction reproduced all native
samples. Removing only the left shoe collider restored 250 mm travel and removed
guide residuals. Guide overrides of 400 reduced the diagnostic native vertex
maximum to 0.165544488 mm and the continuous bound to approximately 0.181935687 mm.
Moving the guide anchor to the shoe center still failed. The original N2
postprocessing failure and its separate no-rerun correction remain preserved.

These observations support the selected bounded convergence change. They do
not establish that capture-phase alignment caused the original residual, nor
qualify every admitted stop position. Native contact manifolds, impulses and
direct velocities remain unavailable.

Before formal qualification, publish the exact contract manifest, implementation
identity, independent checker freeze and reviewed adoption receipt. Qualify
retained A/B/C/D and the 362.5/372.5 mm witnesses E/F. Every formal build starts
from an empty native scene and retains editable unbaked scene, source/settings,
raw/final motion, all attempts, bounds and receipts. Reopen every saved scene in
a fresh pinned process, clear caches and reproduce all captured native samples
without reconstruction. Confirm the disabled-collider causal response and both
authoring routes. Independent continuous/source/native and receiving-application
checks remain separate gates. Preserve all failures even if other cases pass.

The original C191/C192 expected results and failed outputs remain unchanged.
Failure of any required case leaves the new backend unqualified. Do not tune
another setting, combine candidates or expand the study on that result.
