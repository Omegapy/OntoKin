# C222 independent observation-correspondence review

**Decision: approved for the selected CPU-only integration.** The reviewed
implementation supplies the finite observation schema and exact corner
correspondence required by R00. No implementation blocker remains.

The approved author commit is
`6e02cef9e78b4b1ee51d9bf3eae50fb9e0968a8d`. The main public and internal controls
ran at `526a20805a8011223bacb0556c6d125c4a2cd43c`; the checker and contract are
byte-identical in the final commit. Its only later change corrects the author
duplicate-triangle control so that the mutation reaches correspondence while
preserving referenced vertices. The reviewer inspected that complete delta and
ran an independent focused public control on the final commit.

Checker SHA-256:
`1eab170204d8f02b5d281f7e67d7f649040a1c525884fcc17eadfed6c765b6b9`.
Exact source, file hashes, tree identity and executed outcomes are recorded in
[REVIEW-SUMMARY.json](evidence/REVIEW-SUMMARY.json).

## Independent fixture and mapping oracle

The reviewer decoded the retained GLB header, JSON/BIN chunks and little-endian
POSITION, NORMAL and index arrays directly. The generator imports no C221/C222
helper and performs no source evaluation. It independently checked the frozen
GLB, part-map and C214 payload hashes, then checked every instanced source
corner's vertex index, winding and binary32 position bytes against C214.

This accounts for 18 parts, 7,800 triangles and 23,400 corners through **70,200
exact C214 assertions**. The original fixture has no duplicate cyclic
position-triangle keys. The synthetic target indices apply the predeclared
front-face reversal before any checker result is observed.

For result checking, the reviewer constructed an independent oriented-corner
lookup from those raw bytes. This joins each returned raw corner with its
expected source mesh, primitive, triangle, corner and vertex. It does not call
the checker's correspondence routine to calculate an expected answer.

- Fixture generator — `agent-results/observation-review/independent_fixture.py`
- Synthetic observation — `agent-results/observation-review/independent-observation.json`
- Fixture identities — `agent-results/observation-review/independent-fixture-metadata.json`

## Executed controls

**49 of 49 public CLI controls passed.** Nine positive observations checked
every one of their 23,400 returned mapping rows: **210,600 independently checked
rows** in total. They cover the original fixture, arbitrary duplicate display
names, changed finite normals, signed zero, reordered parts, reindexed
vertices, fully split vertices, reordered triangles with cyclic corner order,
and an explicitly unattested producer label. Each result retains false native
acceptance, mapping attestation, normal/material/pose comparison and target
authorization flags.

Negative controls cover swapped, missing, duplicate and extra identities;
wrong source path, mesh, primitive and material assignment; wrong declared and
actual units/bases; wrong raw and declared winding; incomplete/extra/duplicate
triangles and surfaces; a position perturbation of `1e-14` with original normals;
invalid indices/vectors and unused vertices; stale source/artifact claims;
extra fields and asserted acceptance; malformed/truncated/duplicate-key/nonfinite
JSON; and modified immutable GLB bytes. The modified-input case fails at
authority admission. Coordinate declarations fail structurally, while raw
winding and exact-position mismatches fail at correspondence.

**10 of 10 isolated correspondence controls passed**, together with **six
static conditions**. These exercise duplicate position candidates with
different normals, candidate-order and vertex-index independence, ambiguous
corner rotations, one fixed winding reversal, duplicate/missing triangles and
normal-assisted matching refusal. Internal seams provide no admission evidence.

One additional focused public control passed at the final commit. It duplicates
a shared-vertex sphere triangle while keeping every vertex referenced and
requires the specific `DUPLICATE_CORRESPONDENCE` result. This supplements the
original box mutation, whose unused vertex correctly caused an earlier
structural refusal.

- Public controls and exact outcomes — `agent-results/observation-review/controls-01/SUMMARY.json`
- Full baseline map/report — `agent-results/observation-review/controls-01/baseline-stdout.json`
- Independent public-control source — `agent-results/observation-review/independent_controls.py`
- Internal controls and static checks — `agent-results/observation-review/internal-controls-01.json`
- Internal-control source — `agent-results/observation-review/internal_controls.py`
- Focused duplicate result — `agent-results/observation-review/focused-duplicate-control.json`
- Focused-control source — `agent-results/observation-review/focused_duplicate_control.py`
- Retained setup and harness observations — `agent-results/observation-review/HARNESS-NOTES.md`

## Scope and remaining limitations

Every public invocation performs fresh C221 immutable admission. The checker
uses the complete declared node/primitive identities and exact local positions;
display names and normal values cannot select a correspondence. Signed zero is
the only subsequent numeric canonicalization. Python JSON numeric decoding is
explicitly disclosed. Complete raw/source corner mappings and distinct
admission, structure and correspondence results are retained.

The checker and tests are isolated additions. Existing C221 source, authority
documents, product runtime, exporter, native prototypes and historical evidence
remain unchanged by the author commits. Package-dependent controls stay outside
broad product-test discovery.

These observations are synthetic CPU evidence. Consistently forged labels and
arrays cannot establish an actual Godot loader association. Godot runtime
behavior, normal/material fidelity, poses, persistence, process protocol,
settings, rendering and build-lineage gates remain pending. The original Blender
strict-normal failure and failed broad regression retain their meanings.

This review started no native target or version probe, evaluated no OntoKin
source, and performed no export, native import, render or native scene write.
It does not authorize a target start or advance R01–R08. Root integration,
navigation/tracker publication, final-main checks and verified handoff saving
remain the integrator's responsibility.

## Evidence location

This repository copy uses explicit handoff-relative paths for the full independent evidence. The unchanged original report and all listed artifacts are preserved in the C222 handoff and its [durable recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-bcb515965e088191a18515226adf1ae7_2ab2a24d43748191957f9bcc356b59de&account_id=personal). The local evidence summary above records exact byte identities.
