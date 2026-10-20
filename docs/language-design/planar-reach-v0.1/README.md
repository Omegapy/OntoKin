# Planar reach v0.1 proposal corpus

**Status: proposed for peer review; not adopted or implemented.** This directory accompanies [OK-LANG-006](../OK-LANG-006-reusable-planar-reach-actions.md), now version `0.1.0-draft.2`. Draft 2 corrects the SLERP proof and adds concrete interface/delivery schema drafts; the `0.1.0-draft.1` source corpus and all expected values remain byte-identical. The starting repository commit is `06cf8206a8e7205f1b5f87c37c3c12dff0f65b9a`, a published force candidate depending on [PR #17](https://github.com/Omegapy/OntoKin/pull/17). Its force release was not accepted when these inputs were prepared. Reconcile the accepted force revision before an adoption decision or runtime implementation.

The proposal supplies a reusable typed `reach_to(target, duration, branch) -> Action` capability backed by one new `reach_planar` builder. It derives a two-hinge solution from actual source sites, controls both coordinates atomically, and reports a measured goal outcome. Client entries state goals; they do not contain inverse-kinematics formulas or pre-solved joint targets.

## Reviewable inputs

| File | Purpose |
| --- | --- |
| [profile.json](profile.json) | Proposed bindings, hard bounds, diagnostic phases and inspection fields |
| [grammar.ebnf](grammar.ebnf) | Additions to inherited grammar; no old-parser support claim |
| [requirements.json](requirements.json) | R01–R09 requirements, source cases, actual-workflow obligations and pending release gates |
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

The verifier rebuilds the generated set in an isolated temporary directory and requires identical member bytes. It separately checks exact hashes/import pins/action spans, analytic endpoints and wrapping, two-rate/root-composed release integration, repair locality and budget boundary construction. It never calls the OntoKin evaluator to choose an expectation. The fixed high-precision oracle is for this corpus; it does not prove universal correct rounding.

An optional [inherited composition probe](review_inherited_composition.py) temporarily substitutes the new profile/type/builder in memory and asks the existing compiler only to construct the ordinary asset structure. It discloses every substitution and hashes the untouched inputs before/after. This can catch invalid inherited source syntax, geometry or references. It establishes no proposed IK, atomic action, goal result or destination behavior.

The retained [preparation review](inherited-composition-review.json) passed all 26 positive entries on CPython 3.12.14 and the exact base implementation above, matching every expected object identity and preserving the inspected source hashes. Its in-memory substitutions are part of the report. It is scoped to these exact input bytes and that inherited construction check.

```bash
python3 docs/language-design/planar-reach-v0.1/review_inherited_composition.py --repo . --output /tmp/ontokin-planar-baseline-review.json
```

## Acceptance still required

These are **expected inputs**, not successful evaluations, exports or release evidence. Peer review must resolve the decision ledger, verify the complete source/expected closure and independently accept the interpolation derivation. A separate adoption record must identify the accepted force dependency and exact input hashes. The final Agent/GLB engineering schemas, actual operation mapping, decoded-byte adversarial cases, local evidence roles and browser review criteria must be adopted before claiming implementation acceptance.

Implementation then must execute the actual source, both representative Agent authoring/repair workflows, complete inspection/protocol failure paths, independent recorded-delivery checks and inherited regressions. The full [GOAL](../../../GOAL.md) remains open; no authoring improvement or complete product acceptance is inferred from these prepared examples.
