# C272 missing components, boundaries and effort

This record serves TASK-010 (REQ-008, REQ-032, REQ-034). It follows from the
[coverage map](COVERAGE.md) and the [reconciliation](RECONCILIATION.md). Every component below
is traced to the requirement that needs it; nothing is listed that no requirement needs.

Effort estimates are agent working time on this host, including focused tests, and are
estimates only.

All new code is standard library only and lives in `docs/engineering/localized-repair-c272/`,
outside the product package (DEC-005). **Only the runner and the rebuild entry import
OntoKin**: they drive the product. Every module that computes or compares expected values
imports no product module, and a test of its imports shows this.

## Components

| ID | Component | Needed by | Exact missing property | Boundary | Estimate |
| --- | --- | --- | --- | --- | --- |
| G1 | Runner with a scripted client (`runner.py`) | REQ-010, REQ-012, REQ-013, REQ-014, REQ-020 | No program starts a case from a fresh store, drives Agent/0.2 with fixed requests, reads the accepted program back, and records every exchange as it happens. | In process `ProgramAgentService` with protocol `ontokin.agent/0.2` (DEC-005). It checks the frozen input hashes, creates a store per case, exports and retrieves the baseline, edits, submits N1, and exercises the retry and stale cases. It does not evaluate anything. | 2–3 h |
| G2 | Accepted-state record (in the runner) | REQ-015 | No record of acceptance exists that the harness derives from the bytes it actually received. | It writes C255's authority record from the service's responses and the retrieved bytes, outside the client's directory. It keeps the service's raw diagnostic beside the translated C255 form. The model fields are `not applicable to a scripted client`. | 1 h |
| G3 | Delivered-semantic reader (`semantic_observe.py`) | REQ-016 | No observation of units, frame, scene, typed parameters, primitive dimensions, appearance, placement, matter, initial velocities, the 34 sites, the follows and hinges in C255's form, the two actions or the event block. | **The owner's choice, below.** In every option it reads actual bytes, gives each field the artifact hash and a JSON pointer, refuses malformed or oversized input with a typed fault, and imports no product module. | A: 3–4 h; B: 1–2 days |
| G4 | Scoring and the per-property table (`score.py`) | REQ-010, REQ-016, REQ-017 | No step assembles the C255 observation and reports a result for each property. | It calls the unchanged C255 `evaluate` for the verdict. The per-property table localizes faults with C255's own predicates; it never sets the verdict and never fills a property from an expected value. | 1–2 h |
| G5 | Clean rebuild (`rebuild.py`) | REQ-018 | No rebuild in an empty workspace exists for fresh output. | Package-smoke procedure (DEC-007): a wheel from the candidate revision, installed alone into a clean environment outside every checkout. The rebuild runs in a new empty directory holding only `main.ok`, `hinges.ok` and the declared rebuild entry, and its bytes are compared exactly. | 2 h |
| G6 | Residual controls (`residual_controls.py`) | REQ-009 | H20: isolated changes of one ownership, one follow and one motion field are not exercised. H24: the bounds of G3's tables are not exercised. | New files only; existing observer and control files keep their bytes. The expected fields come from C255, not from an observer. | 1–2 h |
| G7 | Fault and positive controls (`controls.py`, `CONTROLS.md`) | REQ-015, REQ-019 | No end-to-end control presents the seven named faults to the workflow's checks on actual bytes. | Evaluator controls, labelled as such and never counted as cases or attempts. A table maps SCORING's other listed faults to a covering control or states that they are open. | 2–3 h |
| G8 | One documented command (`qualify.py`, `README.md`) | REQ-011 | No single entry point. | It runs G1 to G7 into a new directory outside the checkout and writes a structured result. | 1 h |

The total is about 13 to 18 hours with option A for G3, and one to two days more with option B.
The plan's later checks (driver, validation, playback, review and integration) come on top of
this.

## The owner's choice for G3 (DEC-006)

DEC-006 counts a missing observation that needs an **independent interpretation of source
expressions** as substantial. The site poses and the action declarations are examples. Its
implementation waits for the owner's answer. The fields concerned are:

- the site poses (`-self.length / 2`);
- the actions (`bend_to(45[deg], 1[s])`, `move(first, vector(world, …), 2[s])`);
- the event block (`at 0[s] sequence { … }`);
- the typed parameters (`mech.three_mounts(0.6[m])`, `length = self.finger_length` and the override);
- the rack size (`0.6[m] * real(len(self.mounts))`);
- placement, and matter (no body is declared; zero mass follows from the language default).

**Option A (recommended): read the delivered artifacts and cross-check them against decoded motion.**
- G3 reads these fields as observed claims of the delivery. The GLB supplies node properties, geometry, physical kind, material, follows, joints, gravity and coordinates. The sidecar supplies placement, initial velocities, sites, actions and events. Each comparison is with C255's independent expectations.
- Where decoded geometry and motion determine a field, G3 also checks it against them:
  - the blade size against its mesh corners;
  - the base site against the blade's −X face;
  - the pivot against the finger's centre;
  - the hinge rotation against the blade's pose relative to its finger;
  - the follow offset against the finger's pose relative to its rack;
  - the travel velocity against the rack's displacement;
  - the 45° tween in 1 s against the blade's rotation at 1 s.
- Four facts appear in no delivered artifact in C255's form: the `deg` unit of the tween target, the `world` frame of the move and of gravity, and the `sequence` mode. They are read as literal tokens from the accepted source at fixed patterns, as C256 reads keys, with byte spans. No expression is evaluated.
- Zero mass is recorded as derived from the artifact's `no_body` kind and from the absence of any body or mass declaration in the source. It is labelled as rule-derived, not as observed.
- **Limit.** Source-level meaning rests on the exact byte identity of the accepted source with the frozen endpoint, whose meaning C255 derived by hand. The delivery's semantic values are producer claims, checked independently and cross-checked against decoded motion. They are not an independent re-interpretation of the source expressions.
- Sites, actions and events reach a destination only through the sidecar, never through the GLB. That transport loss is disclosed with every result.

**Option B: build an independent finite interpreter of these source expressions.**
- It would parse this family's `.ok` tokens and evaluate the expressions used here: function call, `len`, arithmetic, unit literals, defaults, overrides, and a method returning a tween. It would derive the semantic record from source, in addition to option A's delivery check.
- It needs its own independent review. It risks growing into a second partial compiler, which the roadmap's "no broad framework" warns against.

**Option C: report these fields as incomplete.**
- C255's `evaluate` needs the complete semantic record, so it could not run. Geometry and poses would still be checked with C255's own predicates.
- REQ-016 would be reported as partly met, and REQ-010's complete applicable scoring would not exist.

No narrower study is proposed instead of the frozen C253 qualification.

## What this scope does not add

- No language feature, shape syntax, physical behavior, protocol version, transport or export target.
- No change under `ontokin/`.
- No model takes part in any run, and no record is an attempt in the sense of the frozen run plan.
- The null model and route fields of `RUN-PLAN.json` stay untouched.

## The owner's answer

On 2026-11-28 UTC the owner chose **option A** in answer to the question asked under DEC-006.
G3 is therefore built as a reader of the delivered GLB and sidecar. It compares every field
with C255's independent expectations and cross-checks the fields that decoded geometry and
motion determine. It reads four literals from the accepted source by fixed pattern and
records zero mass as rule-derived. Its limit, stated above, goes with every result. Options
B and C are not pursued.

In the implementation, G3 also reads the tween's numeric value (45) and the event time (0 s)
as source literals at the same fixed patterns, and cross-checks them against the delivered
goal and time. A site's `kind` and a hinge's `axisFrame` follow from fixed reading rules; the
semantic record lists each as derived. The first independent review found these were not
stated here (O4, O5).
