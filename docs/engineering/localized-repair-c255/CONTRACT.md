# C255 offline observation contract

C255 checks **inert records**, independently of the OntoKin parser, model,
evaluator, exporter and route scaffolds. It performs no source build, artifact
extraction, revision promotion, native launch or model trial. A true
`componentPass` says the supplied records and bytes are consistent with this
one frozen family. `realTrialSuccess` is always null, `executionAllowed` and
`artifactReaderQualified` are always false. Caller records are not authenticated
facts. A later independently qualified reader and external revision harness
must establish their origin before any trial score is possible.

The [C253 scoring specification](../localized-repair-c253/SCORING.md),
[corpus](../localized-repair-c253/corpus.json) and
[protocol](../localized-repair-c253/PROTOCOL.md) remain unchanged. The module
pins their complete raw SHA-256 identities, the run plan, and the existing
[finite mesh contract](../OK-ENG-002-3d-scene-animation-export-and-visual-validation.md).
It verifies all 14 corpus file bindings. Exact before, after and invalid bytes
remain the source authority. The historical expected JSON only corroborates
independently derived identity, dimension and pose answers.

## API

`load_corpus(repo)` returns a frozen `Corpus` after checking the authority and
source bytes. `expected_state(corpus, case_id, phase="final")` returns independent
semantic expectations and 126 poses; it supports phases `start` and `final`.
`evaluate(corpus, case_id, observation, authority)` returns a component result.
Cases are `V1`, `V2`, and `N1`; N1's final expected semantics remain 0.65 m.
No API accepts caller-defined tolerances.

`classify_attempt(case_id, admitted, started, outcome, component_pass=False)`
is a separate inert denominator control. Started V1/V2 cases stay in the valid
denominator; started N1 cases stay in the separate negative denominator.
Missing output, timeout, crash, infrastructure incident, abstention and budget
exhaustion never pass or remove an attempted case. An unavailable route before
start has no attempt denominator. No real trial score is created.

## Separate caller byte authority

The authority argument uses schema `ontokin.c255.inert-authority/0.1`. Its
exact keys are `schema`, `attemptId`, `caseId`, `start`, `candidate`, `retained`,
`rebuild`, and `decision`. `attemptId` is a nonempty opaque string. No route
label is accepted by the checker.

`start` and `retained` each have exactly:

- `acceptedRevision`: a nonempty external accepted-record identity.
- `programRevision`: the frozen content-derived program identity for the bytes.
- `sourceFiles`: `main.ok` and `hinges.ok`, each mapped to actual Python `bytes`.
- `artifacts`: nonempty relative artifact filenames mapped to actual `bytes`.

`candidate` has `candidateId`, `parentAcceptedRevision`, `sourceFiles`, and
`artifacts`. The parent must equal the starting accepted revision. Candidate
source must be the exact frozen endpoint (or exact kg candidate for N1).
Extra source/dependency files are rejected. Valid retained source and artifacts
must equal candidate bytes, with a new accepted revision. N1 retains every
starting identity, source byte, dependency byte and artifact byte, and its
candidate artifact map is empty.

`decision` has `status`, `candidateId`, `parentAcceptedRevision`,
`acceptedRevision`, `boundary`, `invalidEverAccepted`, and `diagnostic`.
The boundary is exactly `staged-before-accepted-replacement`;
`invalidEverAccepted` must be Boolean false. Valid cases require `accepted`
and a null diagnostic. N1 requires `rejected` and a diagnostic with exact
keys `code`, `expectedDimension`, `receivedDimension`, `mechanism`, `message`.
Its code is `incompatible-dimension`, dimensions are `length` and `mass`,
and the nonempty message is retained. Mechanisms `compiler`,
`script_unit_validator` and `author_refusal` remain distinct. Harness-only
rejection cannot earn the route-rejection predicate.

`rebuild` has `sourceFiles`, `artifacts`, `cleanWorkspace`, `declaredInputs`,
and `determinism`. Its source and artifact bytes must equal retained bytes;
`cleanWorkspace` is Boolean true, `declaredInputs` is exactly the sorted
list `["hinges.ok", "main.ok"]`, and `determinism` is `byte-exact`. These
are inert observations, not proof a clean rebuild was run. Other native
serialization/normalization policies need a separately reviewed extension.
The component currently checks the bound OntoKin source closure; direct-route
source decoders and equivalent native seeds remain unqualified.

For the CLI only, each byte-map value is `{"encoding":"hex","data":"..."}`
with lowercase hex. The checker decodes this transport into the actual bytes
before hashing or comparing. It never accepts a hash-only claim as retained
source or artifact authority.

## Observation schema

The observation uses schema `ontokin.c255.observation/0.1`, with exact keys
`schema`, `attemptId`, `caseId`, `layer`, `semantic`, `geometry`, `poses`,
`provenance`, `rebuild`, and `decision`. Attempt/case/decision must match the
separate caller records. `layer` is `reference` or `delivery`.

`semantic` has exact keys `units`, `frame`, `scene`, `objects`, `sites`,
`follows`, `hinges`, `actions`, and `events`. The canonical records are fully
specified by the independent `semantic_state` formulas in the module. They
include the complete stable key lists from raw authored `@` keys, definition
keys, owner keys, typed resolved parameters, appearances, primitive dimensions,
authored placement, zero matter and initial velocities, 34 origin/authored
sites, eight separate follows, eight hinges, two actions, and the ordered event
block. An origin site uses its occurrence key plus `@system`, `origin`, with interface
`rigid.origin`; authored site keys append `pivot` or `base`. The scene keeps
its two authored module/scene keys without a fabricated third segment. Lists keyed by `id` are order-independent. Keys,
units, frames, memberships, exact zero mass, actions and event values are
exact. Only source primitive dimensions, scalar length parameters and the
selected blade base X coordinate use the original 1e-12 m limit. Full keys
must be unique; display paths cannot substitute for them.

`geometry` is an order-independent list of 18 records, each with `id`,
`vertices_m`, `triangles`, and `origin`. Vertices are local raw coordinate
triples; triangle indices are integer triples. Every vertex is used. Actual
finite triangles must be nondegenerate, unique, outward, closed (two incident
faces per edge), and have Euler characteristic two. Coincident seam/pole
vertices are joined only by a fixed 12-decimal coordinate key; this joins
sub-picometre residue and is not a delivery tolerance or a source edit.
Boxes cover all eight independently derived corners, all six faces, and 12
triangles. Duplicated face vertices and permuted triangle/index order are
accepted. Spheres retain 482 distinct positions and 960 triangles from the
32-longitude/16-latitude contract, radial vertex and six-axis envelope checks.
This establishes a finite mesh envelope, not exact curved surfaces, normals,
identical triangulation order or arbitrary native tessellation support.
Local mesh coordinates use the unchanged 0.001 m delivery position limit;
source primitive dimensions retain 1e-12 m independently.

`poses` is an order-independent list of exactly 126 records. Each has `id`,
`time_s`, `side`, `position_m`, `rotation_wxyz`, `scale`, `matrix`, and `origin`.
The full identity and one of the seven requested times identify a unique slot.
`side` is `after`, scale is exactly `[1,1,1]`, and `matrix` is the raw 16-number
row-major local-to-world transform with translation at indices 3, 7, 11. Its
homogeneous last row is exactly `[0,0,0,1]`.

Reference poses use 1e-9 m component position and 1e-9 rad orientation limits,
with exact requested timestamps. Delivery poses use 0.001 m, 0.001 rad and
1e-6 s. Bounds are inclusive with no added epsilon. Quaternion comparison is
sign-invariant and uses a stable chord formula at small angles. Raw nonzero
quaternion norms, matrix column norms and orthogonality have fixed structural
residual limits of 1e-12 for reference records and 1e-6 for delivery records;
the latter accommodates binary32 representation. Material scale/shear or a
reflection fails before any normalization. Raw/decomposed consistency uses
that structural residual bound, and raw translation and raw matrix orientation are independently checked
against the original position and angle limits. After raw rigidity checks, a
bounded 3×3 polar factor removes already-admitted encoding residual solely
for raw orientation measurement; this prevents a tiny uniform residual from
biasing the measured angle. It does not repair a rejected matrix or widen the
angle bound. These structural bounds do not relax
source, pose or mesh tolerances. The poses certify only the seven samples.

`provenance` has `acceptedRevision`, `programRevision`, `sourceHashes`,
`artifactHashes`, and `semanticOrigin`. Hash maps must equal the hashes of
caller-supplied actual bytes. The semantic graph's origin and each geometry
and pose record's `origin` have `artifact`, `sha256`, `location`, and
`programRevision`. Each origin binds every field in that record to a named
artifact's actual hash and a nonblank concrete native path/buffer reference without control characters.
The program identity must match retained source. These references are checked
for consistency only; resolving them against native artifacts is a later
reader's obligation. An author's origin label cannot create authenticity.

`rebuild` has only `semantic`, `geometry`, `poses`, and `provenance`, in the same
shapes. Rebuilt observations face the complete original predicates; no changed
field is retrospectively waived. Legitimate accepted-record identities and
artifact hashes may change between valid cases when their actual bytes and
all matching references change together. Stable semantic keys do not change.

## Remaining qualification

This component does not implement a general language parser, native reader,
revision coordinator, trial runner, model/environment pinning, baseline
qualification or statistical comparison. It does not verify that a caller is
outside author control, that an artifact origin was actually traversed, that
no intermediate invalid state occurred, or that a claimed clean workspace was
clean. The future external harness must measure and protect these facts.
Passing inert controls qualifies only the stated component boundary. The
existing public family remains ineligible for an advantage claim.
