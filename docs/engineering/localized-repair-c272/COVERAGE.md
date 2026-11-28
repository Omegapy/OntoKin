# C272 coverage map

This map lists every field of the observation that the unchanged
[C255 checker](../localized-repair-c255/oracle.py) expects (TASK-007, REQ-007, REQ-016). For each field
it gives the independent derivation of the expected value, where an observation can be
taken from actual bytes, the existing interface that takes it, and the state before any new
code. It was written at branch revision `539cbfe1`, whose observer files equal main
`38ee8d18`'s.

**Expected values.** Every expected value comes from C255's `expected_state` and
`semantic_state`. These were derived by hand from the frozen source bytes and the
scoring specification's equations, and were reviewed and corroborated against the
historical `expected.json` in C255. They import no product module. No caller supplies a
tolerance.

**Observation sources.** Three kinds of actual bytes exist for each case:
- the accepted source, read back through `ProgramAgentService.read_program`;
- the GLB, exported and retrieved through Agent/0.2 `export` and `artifact`;
- the semantic sidecar that the C210 route writes beside the GLB. The C272 harness builds it in
  process with the product's `build_semantic_manifest`, from the program read back through the
  service and the retrieved GLB bytes; no Agent/0.2 operation delivers it.

The sidecar and the GLB's `extras.ontokin` are **producer metadata**. Reading them gives an
observed claim of the delivery. Such a claim passes only by agreeing with the independent
expectation, never on its own word.

## Contracts read

| Contract | Revision read |
| --- | --- |
| C253 `PROTOCOL.md`, `SCORING.md`, `corpus.json`, `RUN-PLAN.json` | `38ee8d18` (SHA-256 pins as in C255 `SOURCE_PINS`) |
| C255 `CONTRACT.md`, `oracle.py` | `38ee8d18` |
| C256 `CONTRACT.md`, `reader.py` | `38ee8d18` |
| C257 `CONTRACT.md` | `38ee8d18` |
| C258 `CONTRACT.md` (limits) | `38ee8d18` |
| C267 and C268 `README.md`; C266 and C267 entry points | `38ee8d18` |
| C269 `AUDIT.md`; C271 `OWNER-DECISION-20261128.md`; C260 `CONTROL-PLAN.md` rows H16, H20, H22 and H24 | `38ee8d18` |
| C210 `CONTRACT.md`; `tools/build_semantic_export_demo.py` (service flow) | `38ee8d18` |

## Reused components and their limits

| Component | Interface used | Limit that its contract records |
| --- | --- | --- |
| Agent/0.2 service | `ProgramAgentService(store).handle(request)`, `accepted_revision`, `read_program` | The service under test. Its responses are observations, and its `status` is not the case result. |
| C255 checker | `load_corpus`, `expected_state`, `evaluate` | It checks inert records. `componentPass` is record consistency only; caller records are not authenticated by it. |
| C256 reader | `associate_glb(raw, source_files, name)` | A finite GLB profile for the two frozen source closures. It gives geometry, poses and the identity/definition join, and no semantic values. |
| C257 ownership | `compare_ownership(source_files, raw)` | Immediate ownership only; no transform parenting, revision, atomicity or rebuild. |
| C258 follows | `compare_follows(source_files, raw)` | Follow declarations only; no site or world behavior. |
| C266/C267 hinges | `compare_hinges(source_files, raw)` (binds through C266) | Finite declaration agreement; no world alignment, accepted revision, atomicity or rebuild equivalence. |
| C268 endpoint reader | **not used for fresh output** | It admits the original historical bytes only, and its boundary is kept. |

## Field map

Status keys:
- **covered**: an observation of actual bytes and an independent comparison exist and only need connecting.
- **claim**: read from producer metadata in the delivered artifact, compared with the independent expectation, and not yet implemented.
- **missing**: no existing observation.

| Observation field | Expected value (independent) | Observation from actual bytes | Existing interface | State |
| --- | --- | --- | --- | --- |
| `schema`, `attemptId`, `caseId`, `layer` | fixed by C255 | written by the runner; `layer` = `delivery` | none (runner) | missing: runner |
| `decision` | must equal `authority.decision` | the service's actual `edit` response | none | missing: accepted-state record |
| `semantic.units` | `UNITS` | sidecar `/coordinates` (length, time, angle, mass) | none | missing |
| `semantic.frame` | `FRAME` | GLB `/extras/ontokin/coordinates` (handedness, up); sidecar `/coordinates/source_rotation_order`; node `pose_frame` | none | missing |
| `semantic.scene` | id, duration 2 s, gravity 0 in world | GLB `/extras/ontokin/gravity_m_per_s2`; sidecar `/scene/duration_seconds`; scene key from source tokens (as C256 reads them); gravity frame only in source | partly C256 key reading | missing |
| `semantic.objects[].id`, `path`, `definitionId` | `object_record` | GLB node extras joined to source keys | C256 `associate_glb` | covered |
| `semantic.objects[].owner` | `object_record` | GLB node `owner` and source containment | C257 `compare_ownership` | covered (connect) |
| `semantic.objects[].parameters` | typed resolved parameters | GLB node `/extras/ontokin/properties` | none | missing |
| `semantic.objects[].primitive` | box sizes, sphere radius (1e-12 m) | GLB node `/extras/ontokin/geometry`; corroborated by decoded mesh corners | none | missing (geometry_check covers the mesh, not this field) |
| `semantic.objects[].appearance` | RGBA | GLB material `baseColorFactor` of the node's mesh primitive; node `appearance_linear_rgba` | none | missing |
| `semantic.objects[].placement` | declared world pose for the racks, undeclared otherwise | sidecar `/objects/i/placement` (`authored`, frame, pose) | none | missing |
| `semantic.objects[].matter` | `no_body`, own and aggregate mass 0 | GLB node `/extras/ontokin/physical/kind`; **no artifact carries a mass value** | none | missing: the masses need a source or rule basis |
| `semantic.objects[].initial*Velocity` | zero vectors | sidecar `/objects/i/motion/initial_velocity_m_per_s`, `initial_omega_rad_per_s` | none | missing |
| `semantic.sites` (34) | 16 authored (pivot, base at −L/2) and 18 system origins | sidecar `/sites`; **the GLB carries no site table** | none | missing: needs the sidecar or a source interpretation of the site poses |
| `semantic.follows` (8) | `semantic_state` follows | GLB `/extras/ontokin/follows` | C258 (agreement only, its own schema) | missing: mapping to the C255 record; C258 is an extra agreement check |
| `semantic.hinges` (8) | `semantic_state` hinges | GLB `/extras/ontokin/joints` | C267 (agreement only, its own schema) | missing: mapping to the C255 record; C267 is an extra agreement check |
| `semantic.actions` (2) | tween 45 deg 1 s; move 0.2 m/s in world 2 s | sidecar `/actions` (goal in radians, no unit or frame field); literal `45[deg]` and `world` only in source; **the GLB carries no actions** | none | missing: needs the sidecar plus source literals, or a source interpretation |
| `semantic.events` | one `sequence` block at 0 s | sidecar `/events` (no mode field); the `sequence` keyword is only in source; **the GLB carries no events** | none | missing: as actions |
| `geometry` (18 meshes) | box corners from half-extents, 482-point sphere envelope | GLB POSITION and index accessors | C256 `associate_glb` | covered |
| `poses` (126) | `pose_for` equations, 0.001 m, 0.001 rad, 1e-6 s | GLB animation channels, sampled at seven times | C256 `associate_glb` | covered |
| `provenance` | equals the hashes of the retained bytes | runner hashes of the bytes received; origins from C256 | none | missing: accepted-state record |
| `rebuild.*` | the same predicates as final | a second observation of the rebuilt artifact | as above | missing: clean rebuild |
| authority `start`, `candidate`, `retained` | frozen source bytes and program revisions | service `read_program` and retrieved artifacts | none | missing: runner and accepted-state record |
| authority `decision` | `staged-before-accepted-replacement`, N1 incompatible dimension | service response and diagnostic (`OKL-E-UNIT`, phase `type`) | none | missing: runner |
| authority `rebuild` | equal bytes, clean, declared inputs, byte-exact | rebuild workspace listing and bytes | none | missing: clean rebuild |

## Consequences

- Geometry, poses, identities and owners have trustworthy observers, which need only connecting.
- Follows and hinges have agreement checks between source and GLB. Their C255 records still need a mapping from the GLB metadata.
- Most remaining semantic fields are present in the delivered GLB or sidecar as producer claims. Five facts appear in no delivered artifact in the form that C255 records: action angle units, action frame, event mode, gravity frame and mass. They are source literals or rules.
- Sites, actions and events travel only in the sidecar and never in the GLB. That is a transport loss to disclose with every result.
- [GAPS.md](GAPS.md) records the boundary and effort of each missing component.
