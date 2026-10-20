# Planar reach v0.1 proposal corpus

**Status: proposed for peer review; not adopted or implemented.** This directory accompanies [OK-LANG-006](../OK-LANG-006-reusable-planar-reach-actions.md), version `0.1.0-draft.2`. The effective dependency is accepted force main `59b937d16ec0c82c9bc1395bd0c9bcc63e597261`, with complete F01–F12 and resulting-main evidence. The original `0.1.0-draft.1` source corpus and all expected values remain byte-identical. They were originally prepared on force candidate `06cf8206a8e7205f1b5f87c37c3c12dff0f65b9a`; those historical preparation reports retain that identity.

The [recovery record](draft2-recovery-20261020-14.json) identifies the executor rollback and exact recovered documents. Remaining numeric, schema, protocol and quantization work is independently reconstructed and receives fresh checks and review. An old passing result never applies merely because a new file has the same name. [Explicit amendments D14–D27](draft2-amendments.json) reconcile the accepted dependency, current/terminal identities, bounded numerical admission, complete Agent budgets, lifecycle supplements, direct stored-clock conversion and full release roles without overwriting the original input records.

The proposal supplies a reusable typed `reach_to(target, duration, branch) -> Action` capability backed by one new `reach_planar` builder. It derives a two-hinge solution from actual source sites, controls both coordinates atomically, and reports a measured goal outcome. Client entries state goals; they do not contain inverse-kinematics formulas or pre-solved joint targets.

## Reviewable inputs

| File | Purpose |
| --- | --- |
| [profile-draft2.json](profile-draft2.json) | Effective proposed bindings, distinct budget units, bounded numerical admission, diagnostics and inspection fields; original [profile.json](profile.json) preserved |
| [grammar.ebnf](grammar.ebnf) | Additions to inherited grammar; no old-parser support claim |
| [requirements-draft2.json](requirements-draft2.json) | Effective R01–R12, Q01–Q22, full protocol/recovery obligations and pending release gates; original [requirements.json](requirements.json) preserved |
| [acceptance.json](acceptance.json) | 41 exact source cases: 26 positive and 15 negative, expected samples/outcomes, action spans and complete bundle hashes |
| [libraries/reach-exterior.ok](libraries/reach-exterior.ok) | Native loft segments, marker and physically declared release payload, using inherited surface syntax |
| [libraries/reach-parts.ok](libraries/reach-parts.ok) | Typed reusable two-link arm with actual joints/sites and goal method |
| [libraries/reach-assets.ok](libraries/reach-assets.ok) | Complete bench arm, segmented character and variable keyed arm rack |
| [oracle.py](oracle.py) | Independently stated high-precision IK/FK and incoming-state equations; imports no OntoKin code |
| [author_fixtures.py](author_fixtures.py) | Reproducible source, pins, bundle identities and expected-value preparation |
| [generated-members.json](generated-members.json) | Byte/hash closure of every generated input |
| [verify_fixtures.py](verify_fixtures.py) | Portable closure/reconstruction and independent simple-case checks |
| [review-decisions.md](review-decisions.md) | Proposed decisions, preparation corrections and unresolved adoption gates |
| [sampling-bound.md](sampling-bound.md) | Conservative curved carrier/landmark and quaternion interpolation derivation |
| [repair-briefs.md](repair-briefs.md) | Reuse/repair tasks, predetermined held-outs and future direct-tool comparison |
| [author_draft2_amendments.py](author_draft2_amendments.py) | Deterministically reproduces effective profile/requirements and explicit decisions while checking six original input hashes |
| [numeric-admission.md](numeric-admission.md) and [counter units](numeric-counter-units.md) | Bounded interval/rounding-cell strategy and precise recurrence/interval/runtime counting obligations |
| [rounding-certificates.json](rounding-certificates.json) and [verifier](verify_rounding.py) | Independent proof of the unchanged 54 original coordinate bits and rounded-pair residuals; distinct from runtime implementation |
| [agent-operations.md](agent-operations.md) and [schema manifest](schema-drafts/schema-drafts-manifest.json) | Existing-operation Agent/0.6 request, response, current/terminal projection, diagnosis and recorded metadata contracts |
| [Draft 2 supplements](draft2-supplements/README.md) | Both-moving lifecycle sources, exact clocks/terminal histories, fixed protocol cases and separate nonbinary Q16 source |
| [quantization.md](quantization.md) and [pure checker](verify_quantization_contract.py) | Actual stored endpoint/time/vertex errors, enclosing phases and independently justified source/destination numerical bounds |
| [budget-counting.md](budget-counting.md) | Full Agent response, weighted source-history and whole-GLB accounting; fixed P24 N/N−1 publication probe |
| [release-contract.md](release-contract.md) | All mandatory source/Agent/native/browser/compatibility/inherited roles and actual resulting-main acceptance |
| [Combined contract review](contract-review/README.md) | Fresh combined checks, input closure and independent review for the reconstructed bytes; no runtime acceptance inference |

`reach-parts.ok.in` and `reach-assets.ok.in` are explicit authoring templates. The delivered `.ok` files contain actual SHA-256 dependency pins. Package IDs are `proposal.reach-exterior`, `proposal.reach-parts` and `proposal.reach-assets`, each at the inherited exact package version `0.1.0`. That transport identity is separate from the document's draft version; no prerelease-version extension is proposed.

Each `pNN.files.json` or `nNN.files.json` names a complete entry and its three local modules. Source-unit hashes are hashes of exact UTF-8 bytes; the program revision uses the inherited `ontokin.bundle/0.1` canonical manifest and domain separator. Proposed source uses `ontokin "0.6"` / `planar-reach-0.1`. The current parser does not implement this source version or the new enum/builder.

## Representative clients and cases

The **bench arm** includes its base, column, two independently articulated loft links and tool marker: six objects, five visible carriers. The **segmented character** has a native torso, two two-link arms, three two-link legs, a turning head and three independently keyed eyes: 20 objects, 15 visible carriers. It reaches with both arms while the head turns. These are complete source-generated exterior assemblies under a prescribed kinematic model; they do not claim balance, skin deformation, contact, acquired grasp or locomotion.

The keyed rack constructs 1, 5 or 32 independently identifiable arms. The 32-chain positive case actually creates and starts all 32 reach actions. A separate 128-action case binds many pending actions to one chain, exercising the difference between chain identity, action count and simultaneous motion.

| Cases | Predetermined obligation |
| --- | --- |
| P01–P03 | Two branches and unequal lengths with analytic endpoints |
| P04–P05 | Explicit rotated/moving base composition |
| P06–P10 | Outer/inner boundaries, branch-preserving half-turns, long principal-angle motion and closed limits |
| P11–P13 | Complete character and keyed source reuse |
| P14–P17 | Atomic pause/resume/stop, incoming release plus force, valid prefix before future failed admission |
| P18–P19 | Oblique and unequal held-out variants fixed before implementation |
| P20 | One forearm-length repair in P13's five-arm rack, unchanged siblings and pinned libraries |
| P21–P26 | Exact link/target/duration boundaries, 32 chains and 128 named actions |
| N01–N06 | One-ULP reachability rejection, singular origin, target frame/plane and selected-branch limits |
| N07–N10, N12, N14–N15 | Unsupported length/duration/type/end-site/axis and partial-claim conflict |
| N11, N13 | One over the chain/action hard maxima |

P16 moves both joint coordinates and a translating/rotating root. Its release occurs exactly at reach completion, and its expected freed sphere retains incoming position, orientation, linear velocity and angular velocity. Every linear velocity component contributes to the later force/coast positions. This distinguishes full state transfer from an accidentally stationary joint or root-only calculation.

## Reproduce preparation checks

From the repository root, using Python 3.12 (only the standard library is needed):

```bash
python3 docs/language-design/planar-reach-v0.1/verify_fixtures.py
python3 docs/language-design/planar-reach-v0.1/author_fixtures.py --output-dir /tmp/ontokin-planar-reach-prepared
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The original verifier rebuilds the generated set in an isolated temporary directory and requires identical member bytes. It separately checks exact hashes/import pins/action spans, analytic endpoints and wrapping, two-rate/root-composed release integration, repair locality and budget boundary construction. It never calls the OntoKin evaluator to choose an expectation. The fixed high-precision oracle is for this corpus; the separate bounded interval strategy establishes how numerical admission can prove or explicitly reject arbitrary supported inputs. The finite certificate is not a universal success guarantee.

Fresh contract preparation additionally runs the amendment reproduction, rounding-cell checks, exact quantization checks, lifecycle/protocol closure and schema checks. JSON Schema verification uses only the repository's pinned verification dependencies from `tools/force-agent-verification-requirements.txt`; OntoKin runtime dependencies remain standard-library-only. The combined checker records exact source hashes, commands, Python identity, raw logs and failed as well as successful attempts. The recovery inventory distinguishes exact recovered inputs from newly reconstructed expectations even where their semantic coverage or counts agree.

An optional [inherited composition probe](review_inherited_composition.py) temporarily substitutes the new profile/type/builder in memory and asks the existing compiler only to construct the ordinary asset structure. It discloses every substitution and hashes the untouched inputs before/after. This can catch invalid inherited source syntax, geometry or references. It establishes no proposed IK, atomic action, goal result or destination behavior.

The retained [preparation review](inherited-composition-review.json) passed all 26 positive entries on CPython 3.12.14 and the exact base implementation above, matching every expected object identity and preserving the inspected source hashes. Its in-memory substitutions are part of the report. It is scoped to these exact input bytes and that inherited construction check.

```bash
python3 docs/language-design/planar-reach-v0.1/review_inherited_composition.py --repo . --output /tmp/ontokin-planar-baseline-review.json
```

## Acceptance still required

These are **expected inputs**, not successful evaluations, exports or release evidence. Peer review must resolve the decision ledger, verify the complete source/expected closure and independently accept the numerical and stored-motion derivations. A separate adoption record must identify the accepted force dependency and exact input hashes. The proposed Agent/GLB schemas, actual-operation mapping, decoded-byte adversarial cases, local evidence roles and browser review criteria must be adopted before runtime implementation and final acceptance executions.

Implementation then must execute the actual source, both representative Agent authoring/repair workflows, complete inspection/protocol failure paths, independent recorded-delivery checks and inherited regressions. The full [GOAL](../../../GOAL.md) remains open; no authoring improvement or complete product acceptance is inferred from these prepared examples.
